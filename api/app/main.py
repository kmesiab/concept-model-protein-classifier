"""
FastAPI application for protein disorder classification.

Provides REST API endpoints for fast, accurate protein disorder prediction.
Based on validated classifier with 84.52% accuracy.
"""

import time
import os
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib

from .models import (
    ClassifyRequest,
    ClassifyResponse,
    ClassificationResult,
    FeatureValues,
    HealthResponse,
    ErrorResponse,
)
from .classifier import classify_batch
from .auth import api_key_manager
from .rate_limiter import get_rate_limiter
from .utils import parse_fasta, validate_amino_acid_sequence


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Version
API_VERSION = "1.0.0"

# Application start time for uptime tracking
START_TIME = datetime.now(timezone.utc)

# Create FastAPI app
app = FastAPI(
    title="Protein Disorder Classification API",
    description="""
    Fast and accurate protein disorder prediction API.
    
    ## Features
    - **High Accuracy**: 84.52% accuracy based on extensive validation
    - **Fast**: Threshold-based classification, no ML inference overhead
    - **Batch Processing**: Process up to 50 sequences per request (free tier)
    - **Multiple Input Formats**: JSON or FASTA
    
    ## Authentication
    All endpoints require an API key passed in the `X-API-Key` header.
    
    ## Rate Limits (Free Tier)
    - 1,000 sequences per day
    - 100 requests per minute
    - Up to 50 sequences per batch
    """,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
# Configure allowed origins from environment variable for production security
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(
    ","
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    # Log the full error server-side for debugging
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Return a generic error message to clients to avoid leaking internal details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "code": "INTERNAL_ERROR",
        },
    )


def verify_api_key(api_key: Optional[str]) -> dict:
    """
    Verify API key and return metadata.

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    metadata = api_key_manager.validate_api_key(api_key)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return metadata


def check_rate_limit(api_key: str, metadata: dict, num_sequences: int):
    """
    Check rate limits for the request.

    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Hash the API key for rate limiting
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Get rate limiter
    limiter = get_rate_limiter()

    # Check limits
    allowed, error_msg = limiter.check_rate_limit(
        api_key_hash, metadata["rate_limit_per_minute"], metadata["daily_limit"], num_sequences
    )

    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_msg)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return {
        "message": "Protein Disorder Classification API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"], summary="Health check endpoint")
async def health_check():
    """
    Check if the API is running and healthy.

    Returns service status and uptime information.
    """
    uptime = (datetime.now(timezone.utc) - START_TIME).total_seconds()

    return HealthResponse(status="healthy", version=API_VERSION, uptime_seconds=round(uptime, 2))


@app.post(
    "/api/v1/classify",
    response_model=ClassifyResponse,
    tags=["Classification"],
    summary="Classify protein sequences",
    responses={
        200: {"description": "Successful classification"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        401: {"description": "Invalid API key", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
    },
)
async def classify_sequences(
    request: ClassifyRequest, x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Classify protein sequences as structured or disordered.

    Accepts JSON input with a list of sequences. Each sequence is analyzed
    using 7 biophysical features and classified based on empirically-derived
    thresholds.

    **Classification Method:**
    - Computes 7 biophysical features from the sequence
    - Counts how many features meet the "structured" condition
    - Classifies as "structured" if >= 4 conditions met (default threshold)

    **Features:**
    1. Normalized hydrophobicity
    2. Normalized flexibility
    3. Hydrogen bonding potential
    4. Absolute net charge
    5. Shannon entropy
    6. Proline frequency
    7. Bulky hydrophobic frequency

    **Rate Limits (Free Tier):**
    - 1,000 sequences per day
    - 100 requests per minute
    - Max 50 sequences per request
    """
    # Verify API key
    metadata = verify_api_key(x_api_key)

    # Check batch size limit
    num_sequences = len(request.sequences)
    if num_sequences > metadata["max_batch_size"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size {num_sequences} exceeds limit of {metadata['max_batch_size']} for {metadata['tier']} tier",
        )

    # Check rate limits
    check_rate_limit(x_api_key, metadata, num_sequences)

    # Validate sequences
    for seq_input in request.sequences:
        is_valid, error = validate_amino_acid_sequence(seq_input.sequence)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sequence '{seq_input.id}': {error}",
            )

    # Start timing
    start_time = time.time()

    # Prepare sequences for classification
    sequences = [(seq.id, seq.sequence) for seq in request.sequences]

    # Classify sequences
    results = classify_batch(sequences, threshold=request.threshold)

    # Add processing times
    total_time_ms = (time.time() - start_time) * 1000
    avg_time_ms = total_time_ms / num_sequences

    classification_results = []
    for result in results:
        # Convert to response model
        classification_results.append(
            ClassificationResult(
                id=result["id"],
                sequence=result["sequence"],
                classification=result["classification"],
                confidence=result["confidence"],
                conditions_met=result["conditions_met"],
                threshold=result["threshold"],
                features=FeatureValues(**result["features"]),
                processing_time_ms=round(avg_time_ms, 2),
                error=result.get("error"),
            )
        )

    return ClassifyResponse(
        results=classification_results,
        total_sequences=num_sequences,
        total_time_ms=round(total_time_ms, 2),
        api_version=API_VERSION,
    )


@app.post(
    "/api/v1/classify/fasta",
    response_model=ClassifyResponse,
    tags=["Classification"],
    summary="Classify protein sequences from FASTA format",
    responses={
        200: {"description": "Successful classification"},
        400: {"description": "Invalid FASTA format", "model": ErrorResponse},
        401: {"description": "Invalid API key", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
    },
)
async def classify_fasta(
    request: Request, threshold: int = 4, x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Classify protein sequences from FASTA format input.

    Accepts FASTA formatted text as the request body.

    **Example FASTA input:**
    ```
    >protein1
    MKVLWAASLLLLASAARA
    >protein2
    MALWMRLLPLLALLALWGPDPAAAF
    ```

    **Rate Limits (Free Tier):**
    - 1,000 sequences per day
    - 100 requests per minute
    - Max 50 sequences per request
    """
    # Verify API key
    metadata = verify_api_key(x_api_key)

    # Read FASTA content
    fasta_content = await request.body()
    fasta_text = fasta_content.decode("utf-8")

    # Parse FASTA
    try:
        sequences = parse_fasta(fasta_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid FASTA format: {str(e)}"
        )

    # Check batch size limit
    num_sequences = len(sequences)
    if num_sequences > metadata["max_batch_size"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size {num_sequences} exceeds limit of {metadata['max_batch_size']} for {metadata['tier']} tier",
        )

    # Check rate limits
    check_rate_limit(x_api_key, metadata, num_sequences)

    # Validate sequences
    for seq_id, sequence in sequences:
        is_valid, error = validate_amino_acid_sequence(sequence)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sequence '{seq_id}': {error}",
            )

    # Start timing
    start_time = time.time()

    # Classify sequences
    results = classify_batch(sequences, threshold=threshold)

    # Add processing times
    total_time_ms = (time.time() - start_time) * 1000
    avg_time_ms = total_time_ms / num_sequences

    classification_results = []
    for result in results:
        classification_results.append(
            ClassificationResult(
                id=result["id"],
                sequence=result["sequence"],
                classification=result["classification"],
                confidence=result["confidence"],
                conditions_met=result["conditions_met"],
                threshold=result["threshold"],
                features=FeatureValues(**result["features"]),
                processing_time_ms=round(avg_time_ms, 2),
                error=result.get("error"),
            )
        )

    return ClassifyResponse(
        results=classification_results,
        total_sequences=num_sequences,
        total_time_ms=round(total_time_ms, 2),
        api_version=API_VERSION,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
