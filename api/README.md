# Protein Disorder Classification API

Fast and accurate REST API for protein disorder prediction. Built on a validated classifier with **84.52% accuracy**.

## 🚀 Features

- **High Accuracy**: 84.52% accuracy validated through rigorous testing
- **Blazingly Fast**: Threshold-based classification with no ML inference overhead
- **Batch Processing**: Process up to 50 sequences per request (free tier)
- **Multiple Formats**: Accepts both JSON and FASTA input
- **Rate Limiting**: Redis-backed distributed rate limiting
- **Auto Documentation**: Interactive OpenAPI/Swagger documentation
- **Production Ready**: Docker containerized with health checks

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [API Usage](#-api-usage)
- [Client Examples](#-client-examples)
- [Rate Limits](#-rate-limits)
- [Deployment](#-deployment)
- [Development](#️-development)
- [Testing](#-testing)

## 🏁 Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.12+ and Redis

### Using Docker (Recommended)

```bash
cd api
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Using Python Directly

```bash
cd api

# Install dependencies
pip install -r requirements.txt

# Start Redis (in separate terminal)
redis-server

# Run the API
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verify Installation

```bash
curl http://localhost:8000/health
```

## 📖 API Usage

### Authentication

The API uses two types of authentication:

1. **API Key Authentication** (for classification endpoints)
   - Used with `X-API-Key` header
   - Long-lived credentials for protein classification
   - Created via the API key management portal

2. **JWT Bearer Token Authentication** (for API key management)
   - Used with `Authorization: Bearer` header
   - Short-lived access tokens (1 hour)
   - Obtained through magic link authentication

### Get Your First API Key

#### Step 1: Request Magic Link

A demo API key is automatically created when the server starts. Check the server logs for:

```text
Demo API Key created: pk_...
```

For production use, register using magic link authentication:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your.email@example.com"}'
```

#### Step 2: Verify Token and Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_FROM_EMAIL"}'
```

Response includes `access_token` and `refresh_token`.

#### Step 3: Create API Key

```bash
curl -X POST http://localhost:8000/api/v1/api-keys/register \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"label": "Production API"}'
```

**⚠️ Save the API key immediately - it's only shown once!**

### Manage Your API Keys

See **[api/examples/api_key_management.md](examples/api_key_management.md)** for comprehensive examples of:

- Listing all your API keys
- Rotating API keys (recommended every 90 days)
- Revoking compromised keys
- Refreshing access tokens

### Endpoint: `/api/v1/classify` (JSON)

Classify protein sequences using JSON format.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "sequences": [
      {
        "id": "protein1",
        "sequence": "MKVLWAASLLLLASAARA"
      },
      {
        "id": "protein2",
        "sequence": "MALWMRLLPLLALLALWGPDPAAAF"
      }
    ],
    "threshold": 5
  }'
```

**Response:**

```json
{
  "results": [
    {
      "id": "protein1",
      "sequence": "MKVLWAASLLLLASAARA",
      "classification": "structured",
      "confidence": 0.85,
      "conditions_met": 5,
      "threshold": 5,
      "features": {
        "hydro_norm_avg": 0.6234,
        "flex_norm_avg": 0.7123,
        "h_bond_potential_avg": 1.234,
        "abs_net_charge_prop": 0.056,
        "shannon_entropy": 2.987,
        "freq_proline": 0.055,
        "freq_bulky_hydrophobics": 0.389
      },
      "processing_time_ms": 3.2
    }
  ],
  "total_sequences": 2,
  "total_time_ms": 6.5,
  "api_version": "1.0.0"
}
```

### Endpoint: `/api/v1/classify/fasta` (FASTA)

Classify protein sequences using FASTA format.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/classify/fasta?threshold=5 \
  -H "Content-Type: text/plain" \
  -H "X-API-Key: YOUR_API_KEY" \
  --data-binary @- << 'EOF'
>protein1
MKVLWAASLLLLASAARA
>protein2
MALWMRLLPLLALLALWGPDPAAAF
EOF
```

**Response:** Same JSON format as above.

## 💻 Client Examples

### Python

```python
import requests

API_URL = "http://localhost:8000/api/v1/classify"
API_KEY = "your_api_key_here"

def classify_proteins(sequences):
    """Classify protein sequences."""
    payload = {
        "sequences": [
            {"id": seq_id, "sequence": seq}
            for seq_id, seq in sequences
        ]
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()

# Example usage
sequences = [
    ("protein1", "MKVLWAASLLLLASAARA"),
    ("protein2", "MALWMRLLPLLALLALWGPDPAAAF")
]

results = classify_proteins(sequences)

for result in results['results']:
    print(f"{result['id']}: {result['classification']} "
          f"(confidence: {result['confidence']}, "
          f"conditions: {result['conditions_met']}/{result['threshold']})")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000/api/v1/classify';
const API_KEY = 'your_api_key_here';

async function classifyProteins(sequences) {
  const payload = {
    sequences: sequences.map(([id, sequence]) => ({ id, sequence }))
  };
  
  const response = await axios.post(API_URL, payload, {
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    }
  });
  
  return response.data;
}

// Example usage
const sequences = [
  ['protein1', 'MKVLWAASLLLLASAARA'],
  ['protein2', 'MALWMRLLPLLALLALWGPDPAAAF']
];

classifyProteins(sequences)
  .then(results => {
    results.results.forEach(result => {
      console.log(`${result.id}: ${result.classification} ` +
                  `(confidence: ${result.confidence}, ` +
                  `conditions: ${result.conditions_met}/${result.threshold})`);
    });
  })
  .catch(error => console.error('Error:', error.message));
```

### cURL with FASTA file

```bash
# Classify sequences from a FASTA file
curl -X POST http://localhost:8000/api/v1/classify/fasta \
  -H "Content-Type: text/plain" \
  -H "X-API-Key: YOUR_API_KEY" \
  --data-binary @sequences.fasta
```

## 📊 Rate Limits

### Free Tier

- **Daily Limit**: 1,000 sequences per day
- **Rate Limit**: 100 requests per minute
- **Batch Size**: Up to 50 sequences per request
- **No credit card required**

### Premium Tier (Future)

- **Daily Limit**: 100,000+ sequences per day
- **Rate Limit**: 1,000 requests per minute
- **Batch Size**: Up to 500 sequences per request
- **Priority processing**
- **Usage analytics dashboard**

### Rate Limit Headers

Rate limit information is included in response headers:

```text
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build and run
cd api
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop
docker-compose down
```

### Environment Variables

Create a `.env` file in the `api` directory:

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Custom thresholds
CLASSIFICATION_THRESHOLD=5
```

### Kubernetes Deployment

(See `k8s/` directory for Kubernetes manifests - to be added)

## 🛠️ Development

### Setup Development Environment

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # To be created
```

### Run in Development Mode

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Interactive Documentation

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/openapi.json>

## 🧪 Testing

### Run All Tests

```bash
cd api
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test Suites

```bash
# Test classifier only
pytest tests/test_classifier.py -v

# Test API endpoints only
pytest tests/test_api.py -v

# Test utilities only
pytest tests/test_utils.py -v
```

### Performance Benchmarking

```bash
# Run performance tests
pytest tests/test_api.py::TestPerformance -v
```

## 👨‍💼 Admin Endpoints

### Audit Log Query API

**Endpoint: `GET /admin/audit-logs`**

Query API usage audit logs for compliance monitoring, troubleshooting, and usage tracking.

**Authentication Required:**
- JWT access token in `Authorization: ******` header
- Admin-level access (all authenticated users currently have admin access)

**Query Parameters:**
- `start_time` (required): ISO 8601 timestamp - Start of query window
- `end_time` (required): ISO 8601 timestamp - End of query window
- `api_key` (optional): Filter by specific API key ID
- `status` (optional): Filter by `success` or `error`
- `limit` (optional): Results per page (default: 100, max: 1000)
- `next_token` (optional): For pagination

**Example Request:**

```bash
curl -X GET "http://localhost:8000/admin/audit-logs?start_time=2024-01-01T00:00:00Z&end_time=2024-01-02T00:00:00Z&status=success&limit=50" \
  -H "Authorization: ******"
```

**Example Response:**

```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "api_key": "****1234",
      "sequence_length": 0,
      "processing_time_ms": 45.5,
      "status": "success",
      "error_code": null,
      "ip_address": "192.168.1.0/24"
    }
  ],
  "total": 1,
  "next_token": null
}
```

**Security & Privacy:**
- API keys masked (only last 4 characters visible)
- IP addresses masked for privacy (first 3 octets only)
- No sequence content ever exposed
- 30-day retention window (older records not available)
- Audit log access is itself logged for security
- Rate limited to 10 queries/minute per admin

**Use Cases:**
- Monitor API usage patterns
- Troubleshoot API errors
- Compliance reporting and auditing
- Usage tracking for billing/analytics

## 📐 Classification Method

The classifier uses a threshold-based approach with 7 biophysical features:

1. **Hydrophobicity** - Normalized average (Kyte-Doolittle scale)
2. **Flexibility** - Normalized average flexibility
3. **H-bond Potential** - Hydrogen bonding capacity
4. **Net Charge** - Absolute net charge proportion
5. **Shannon Entropy** - Sequence complexity
6. **Proline Frequency** - Proline content
7. **Bulky Hydrophobics** - Frequency of W, C, F, Y, I, V, L

### Classification Logic

1. Compute all 7 features from the sequence
2. Count how many features meet the "structured" condition
3. If count >= threshold (default: 5), classify as **structured**
4. Otherwise, classify as **disordered**

### Confidence Scoring

- Confidence increases with distance from threshold
- Range: 0.5 to 1.0
- Higher confidence when all or no conditions are met
- Lower confidence near the threshold boundary

## 📊 Validation Results

- **Accuracy**: 84.52%
- **Dataset**: PDB (folded) + DisProt (disordered)
- **Validation**: Independent test set
- **Speed**: ~3ms per sequence (single-threaded)

See the main repository README and `docs/VALIDATION.md` for detailed validation results.

## 🔒 Security

### API Key Security

- **API key authentication** required for all classification endpoints
- **JWT Bearer token authentication** required for API key management
- **Magic link authentication** - Passwordless, email-based login (15-minute TTL, single-use)
- **Access tokens** - 1-hour lifetime for API key management operations
- **Refresh tokens** - 30-day lifetime to obtain new access tokens
- **Rate limiting** to prevent abuse
- **Input validation** on all endpoints
- **Non-root user** in Docker container
- **CORS configuration** for production deployment

### Best Practices

1. **Never commit API keys to version control** - Use environment variables
2. **Rotate API keys regularly** - Every 90 days recommended
3. **Use different keys for different environments** - Dev, staging, production
4. **Monitor key usage** - Check the `/api/v1/api-keys/list` endpoint
5. **Revoke immediately if compromised** - Use `/api/v1/api-keys/revoke`
6. **Store refresh tokens securely** - They're valid for 30 days

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is part of the Concept Model Protein Classifier repository.

## 🙏 Acknowledgments

- Based on the Concept Model framework
- Validated using PDB and DisProt datasets
- Built with FastAPI, Redis, and modern Python tools

## 📧 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with ❤️ for protein science**
