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

### 1. Get Your Free API Key

Visit our [Getting Started Guide](https://kmesiab.github.io/concept-model-protein-classifier/getting-started.html) to request your API key (1000 sequences/day free).

### 2. Make Your First Request

```bash
curl -X POST https://api.proteinclassifier.io/api/v1/classify \
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
- **[Interactive Swagger Docs](https://api.proteinclassifier.io/docs)** - Try the API in your browser
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
curl https://api.proteinclassifier.io/api/v1/classify \
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

**[View Deployment Guide →](api/README.md#-deployment)**

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
