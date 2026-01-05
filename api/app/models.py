"""
Pydantic models for request and response validation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class SequenceInput(BaseModel):
    """Single sequence input for classification."""

    id: str = Field(..., description="Unique identifier for the sequence")
    sequence: str = Field(..., description="Protein sequence (amino acid string)")

    @validator("sequence")
    def sequence_not_empty(cls, v):
        """Validate that sequence is not empty."""
        if not v or not v.strip():
            raise ValueError("Sequence cannot be empty")
        return v.strip()


class ClassifyRequest(BaseModel):
    """Request model for classification endpoint."""

    sequences: List[SequenceInput] = Field(
        ..., description="List of protein sequences to classify", min_length=1, max_length=50
    )
    threshold: Optional[int] = Field(
        5,
        description="Number of conditions that must be met for 'structured' classification",
        ge=1,
        le=7,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sequences": [
                    {"id": "protein1", "sequence": "MKVLWAASLLLLASAARA"},
                    {"id": "protein2", "sequence": "MALWMRLLPLLALLALWGPDPAAAF"},
                ],
                "threshold": 5,
            }
        }


class FeatureValues(BaseModel):
    """Computed feature values for a sequence."""

    hydro_norm_avg: float = Field(..., description="Average normalized hydrophobicity")
    flex_norm_avg: float = Field(..., description="Average normalized flexibility")
    h_bond_potential_avg: float = Field(..., description="Average hydrogen bonding potential")
    abs_net_charge_prop: float = Field(..., description="Absolute net charge proportion")
    shannon_entropy: float = Field(..., description="Sequence Shannon entropy")
    freq_proline: float = Field(..., description="Proline frequency")
    freq_bulky_hydrophobics: float = Field(..., description="Bulky hydrophobic residue frequency")


class ClassificationResult(BaseModel):
    """Classification result for a single sequence."""

    id: str = Field(..., description="Sequence identifier")
    sequence: str = Field(..., description="Protein sequence (truncated if >100 chars)")
    classification: str = Field(..., description="Classification: 'structured' or 'disordered'")
    confidence: float = Field(..., description="Confidence score (0.5-1.0)", ge=0.0, le=1.0)
    conditions_met: int = Field(..., description="Number of conditions met", ge=0, le=7)
    threshold: int = Field(..., description="Threshold used for classification", ge=1, le=7)
    features: FeatureValues = Field(..., description="Computed feature values")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if classification failed")


class ClassifyResponse(BaseModel):
    """Response model for classification endpoint."""

    results: List[ClassificationResult] = Field(..., description="Classification results")
    total_sequences: int = Field(..., description="Total number of sequences processed")
    total_time_ms: float = Field(..., description="Total processing time in milliseconds")
    api_version: str = Field(..., description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "id": "protein1",
                        "sequence": "MKVLWAASLLLLASAARA",
                        "classification": "structured",
                        "confidence": 0.92,
                        "conditions_met": 5,
                        "threshold": 5,
                        "features": {
                            "hydro_norm_avg": 0.6234,
                            "flex_norm_avg": 0.7123,
                            "h_bond_potential_avg": 1.234,
                            "abs_net_charge_prop": 0.056,
                            "shannon_entropy": 2.987,
                            "freq_proline": 0.055,
                            "freq_bulky_hydrophobics": 0.389,
                        },
                        "processing_time_ms": 3.2,
                    }
                ],
                "total_sequences": 1,
                "total_time_ms": 3.2,
                "api_version": "1.0.0",
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {"status": "healthy", "version": "1.0.0", "uptime_seconds": 12345.67}
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid request",
                "detail": "Sequence cannot be empty",
                "code": "VALIDATION_ERROR",
            }
        }
