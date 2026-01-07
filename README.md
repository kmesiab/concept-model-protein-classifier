# Protein Disorder Classification API

**Production-ready REST API for fast, accurate protein disorder prediction**

[![API Status](https://img.shields.io/badge/status-production-success)](https://kmesiab.github.io/concept-model-protein-classifier/)
[![Accuracy](https://img.shields.io/badge/accuracy-84.52%25-blue)](https://kmesiab.github.io/concept-model-protein-classifier/methodology.html)
[![Performance](https://img.shields.io/badge/speed-%3C50ms-green)](https://kmesiab.github.io/concept-model-protein-classifier/)

Integrate protein disorder prediction into your bioinformatics workflows with our validated, high-performance API. Built on a pure biophysics approach—no machine learning overhead, just fast, interpretable results.

---

## 🎯 What Is This?

A commercial REST API service that predicts whether protein sequences are **structured** (folded) or **disordered** (intrinsically unstructured). Perfect for developers building:

- 🧬 **Bioinformatics pipelines** - Protein analysis workflows
- 🔬 **Drug discovery tools** - Identifying disordered regions for targeting
- 📊 **Protein databases** - Automated annotation at scale
- 🧪 **Research platforms** - Academic and commercial applications

**Free tier available** with generous limits. No credit card required.

---

## ⚡ Quick Start

### 1. Register and Get Your API Key

Our self-service portal uses passwordless magic link authentication:

```bash
# Step 1: Request magic link
curl -X POST https://api.proteinclassifier.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your.email@example.com"}'

# Step 2: Verify token from email
curl -X POST https://api.proteinclassifier.com/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_FROM_EMAIL"}'
# Returns: access_token, refresh_token

# Step 3: Create API key
curl -X POST https://api.proteinclassifier.com/api/v1/api-keys/register \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"label": "My API Key"}'
# Returns: api_key (save this - only shown once!)
```

**[📖 Full Authentication Guide →](https://kmesiab.github.io/concept-model-protein-classifier/getting-started.html)**

### 2. Make Your First Request

```bash
curl -X POST https://api.proteinclassifier.com/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "sequences": [
      {
        "id": "example_protein",
        "sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL"
      }
    ]
  }'
```

**Response:**

```json
{
  "results": [
    {
      "id": "example_protein",
      "classification": "structured",
      "confidence": 0.92,
      "conditions_met": 6,
      "processing_time_ms": 3.8
    }
  ]
}
```

---

## 🔑 API Key Management

### Self-Service Portal

Manage your API keys through our secure, self-service portal:

#### Authentication Flow

1. **Magic Link Login** - Passwordless email-based authentication
2. **JWT Tokens** - Access tokens (1h) and refresh tokens (30d)
3. **API Key Operations** - Create, list, rotate, and revoke keys

#### Quick Reference

```bash
# List your API keys
curl -X GET https://api.proteinclassifier.com/api/v1/api-keys/list \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Rotate an API key (creates new, revokes old)
curl -X POST https://api.proteinclassifier.com/api/v1/api-keys/rotate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key_id": "key_xyz789"}'

# Revoke an API key
curl -X POST https://api.proteinclassifier.com/api/v1/api-keys/revoke \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key_id": "key_xyz789"}'
```

#### Security Best Practices

- 🔒 Never commit API keys to version control
- 🔄 Rotate keys every 90 days (recommended)
- 🎯 Use different keys for dev/staging/production
- 👁️ Monitor key usage via the list endpoint
- ⚡ Revoke immediately if compromised

**[📖 Complete API Key Management Guide →](api/examples/api_key_management.md)**

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **⚡ Lightning Fast** | <50ms per sequence • 12,750 sequences/second throughput |
| **🎯 Validated Accuracy** | 84.52% accuracy on independent test sets |
| **📦 Bulk Processing** | Up to 50 sequences per request (free tier) |
| **🔌 Multiple Formats** | JSON and FASTA input support |
| **🐳 Easy Integration** | RESTful API with OpenAPI/Swagger docs |
| **🔒 Enterprise Ready** | Rate limiting, authentication, Docker containerized |
| **💰 Free Tier** | 1,000 sequences/day at no cost |

---

## 💼 Use Cases

### Academic Research

Perfect for proteomics studies requiring disorder prediction at scale. Free tier supports most research workflows.

### Drug Discovery

Identify intrinsically disordered regions (IDRs) as potential therapeutic targets. Premium tier supports high-throughput screening.

### Bioinformatics Pipelines

Integrate disorder prediction into your analysis workflows via simple REST calls. No model training or ML infrastructure required.

### Protein Database Annotation

Annotate large protein databases with disorder predictions. Bulk processing and premium tiers handle millions of sequences.

---

## 📊 Performance

Our classifier delivers **production-grade performance** with transparent validation:

| Metric | Value |
|--------|-------|
| **Accuracy** | 84.52% |
| **Processing Speed** | <50ms per sequence |
| **Throughput** | 12,750 sequences/second |
| **Batch Support** | 50 sequences/request (free tier) |
| **Test Coverage** | 91.38% |

**[📈 View Complete Validation Results](https://kmesiab.github.io/concept-model-protein-classifier/methodology.html)**

### Why Our Approach Works

- **Pure Biophysics**: No ML training overhead—predictions based on validated biophysical features
- **Interpretable**: Results include feature values and thresholds met
- **Fast**: Threshold-based classification requires minimal compute
- **Validated**: Rigorous testing on independent datasets (PDB, DisProt, MobiDB)

---

## 💳 Pricing & Tiers

### Free Tier (Available Now)

Perfect for research, development, and small-scale applications.

- ✅ **1,000 sequences/day**
- ✅ **100 requests/minute**
- ✅ **50 sequences per request**
- ✅ **No credit card required**
- ✅ **Interactive API documentation**

### Premium Tier (Coming Soon)

For production workloads and commercial applications.

- 🚀 **100,000+ sequences/day**
- 🚀 **1,000 requests/minute**
- 🚀 **500 sequences per request**
- 🚀 **Priority processing**
- 🚀 **SLA guarantee**
- 🚀 **Usage analytics dashboard**

**[Request Early Access to Premium Tier →](https://kmesiab.github.io/concept-model-protein-classifier/getting-started.html)**

---

## 📚 Documentation

### API Documentation

- **[Complete API Reference](api/README.md)** - Endpoints, authentication, examples
- **[Interactive Swagger Docs](https://api.proteinclassifier.com/docs)** - Try the API in your browser
- **[Getting Started Guide](https://kmesiab.github.io/concept-model-protein-classifier/getting-started.html)** - Step-by-step integration

### Scientific Validation

- **[Methodology](https://kmesiab.github.io/concept-model-protein-classifier/methodology.html)** - How the classifier works
- **[Validation Results](docs/VALIDATION.md)** - Comprehensive testing and benchmarks
- **[Performance Comparison](https://kmesiab.github.io/concept-model-protein-classifier/comparison.html)** - How we stack up

### Developer Resources

- **[Python Examples](api/README.md#-client-examples)** - Python client code
- **[JavaScript Examples](api/README.md#-client-examples)** - Node.js integration
- **[FASTA Support](api/examples/curl_examples.md)** - Working with FASTA files
- **[Error Handling](https://kmesiab.github.io/concept-model-protein-classifier/api-docs.html#error-handling)** - Debugging and troubleshooting

---

## 🛠️ SDKs (Coming Soon)

Official client libraries to simplify integration:

- 🐍 **Python SDK** - Pythonic interface with async support
- 📦 **Node.js SDK** - JavaScript/TypeScript package
- 🦀 **Rust SDK** - High-performance native client
- ☕ **Java SDK** - Enterprise Java integration

**[Sign up for SDK early access →](https://kmesiab.github.io/concept-model-protein-classifier/getting-started.html)**

---

## 🚀 Deployment Options

### Cloud API (Recommended)

Access our hosted API with zero infrastructure management.

```bash
# Just use our API endpoint
curl https://api.proteinclassifier.com/api/v1/classify \
  -H "X-API-Key: YOUR_KEY" \
  -d @your_sequences.json
```

### Self-Hosted (Docker)

Deploy on your own infrastructure for complete control.

```bash
git clone https://github.com/kmesiab/concept-model-protein-classifier.git
cd concept-model-protein-classifier/api
docker-compose up -d
```

**[View API Deployment Guide →](api/README.md#-deployment)**

### AWS ECS Fargate (Production)

Deploy to AWS with Terraform infrastructure and GitHub Actions CI/CD.

```bash
cd terraform
terraform init
terraform apply
```

**[View AWS Deployment Guide →](docs/AWS_DEPLOYMENT.md)**

**[View Environment Configuration Guide →](docs/DEPLOYMENT.md)**

---

## 🤝 Community & Support

### Get Help

- 💬 **[GitHub Discussions](https://github.com/kmesiab/concept-model-protein-classifier/discussions)** - Ask questions, share use cases
- 🐛 **[Report Issues](https://github.com/kmesiab/concept-model-protein-classifier/issues)** - Bug reports and feature requests
- 📧 **Email Support** - Premium tier includes priority email support

### Contributing

We welcome contributions! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines.

### Security

Found a vulnerability? See our **[Security Policy](SECURITY.md)** for responsible disclosure.

---

## 📖 Citation & Research

This API is built on a validated biophysics-based approach. If you use this service in your research, please cite:

```bibtex
@software{protein_disorder_classifier,
  title = {Protein Disorder Classification API},
  author = {Mesiab, Kevin},
  year = {2024},
  url = {https://github.com/kmesiab/concept-model-protein-classifier},
  note = {Validated accuracy: 84.52\%}
}
```

**[Read the Methodology →](https://kmesiab.github.io/concept-model-protein-classifier/methodology.html)**

---

## 📜 License

**Note**: This is a commercial API service with a free tier for academic and non-commercial use. Contact us for commercial licensing arrangements.

---

## 🌟 Why Choose Our API?

✅ **Proven Accuracy** - 84.52% validated on independent datasets  
✅ **Production Ready** - Used in research and commercial applications  
✅ **Fast & Scalable** - Handle millions of sequences with ease  
✅ **Transparent** - Open methodology and validation results  
✅ **Developer Friendly** - RESTful API with comprehensive docs  
✅ **Free Tier** - No cost for research and development  

**[Get Started in 5 Minutes →](https://kmesiab.github.io/concept-model-protein-classifier/getting-started.html)**

---

Built with ❤️ for the bioinformatics community
