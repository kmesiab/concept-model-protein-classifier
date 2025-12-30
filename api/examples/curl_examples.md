# cURL Examples for Protein Disorder Classification API

This file contains various examples of using the API with cURL.

## Prerequisites

Replace `YOUR_API_KEY_HERE` with your actual API key in all examples below.

## Basic Examples

### 1. Health Check

```bash
curl -X GET http://localhost:8000/health
```

### 2. Classify Single Sequence (JSON)

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {
        "id": "test_protein",
        "sequence": "MKVLWAASLLLLASAARA"
      }
    ]
  }'
```

### 3. Classify Multiple Sequences (JSON)

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {
        "id": "protein1",
        "sequence": "ILVILVILVILVILVILVILVIL"
      },
      {
        "id": "protein2",
        "sequence": "KKEEKKEEKKEEKKEEGGPPGGPP"
      },
      {
        "id": "protein3",
        "sequence": "ACDEFGHIKLMNPQRSTVWY"
      }
    ]
  }'
```

### 4. Classify with Custom Threshold

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {
        "id": "test_protein",
        "sequence": "MKVLWAASLLLLASAARA"
      }
    ],
    "threshold": 5
  }'
```

## FASTA Examples

### 5. Classify from FASTA (Inline)

```bash
curl -X POST http://localhost:8000/api/v1/classify/fasta \
  -H "Content-Type: text/plain" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  --data-binary $'>protein1
MKVLWAASLLLLASAARA
>protein2
MALWMRLLPLLALLALWGPDPAAAF'
```

### 6. Classify from FASTA File

```bash
# Create a FASTA file
cat > sequences.fasta << 'EOF'
>albumin_fragment
MKWVTFISLLFLFSSAYSRGVFRRDAHKSEVAHRFKDLGEENFKALVL
>alpha_synuclein
MDVFMKGLSKAKEGVVAAAEKTKQGVAEAAGKTKEGVLYVGSKTKEGV
EOF

# Classify the sequences
curl -X POST http://localhost:8000/api/v1/classify/fasta \
  -H "Content-Type: text/plain" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  --data-binary @sequences.fasta
```

### 7. FASTA with Custom Threshold

```bash
curl -X POST "http://localhost:8000/api/v1/classify/fasta?threshold=5" \
  -H "Content-Type: text/plain" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  --data-binary @sequences.fasta
```

## Advanced Examples

### 8. Pretty Print JSON Output (with jq)

```bash
curl -s -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {"id": "test", "sequence": "MKVLWAASLLLLASAARA"}
    ]
  }' | jq .
```

### 9. Extract Only Classifications

```bash
curl -s -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {"id": "test1", "sequence": "ILVILVILVILVILVILVILVIL"},
      {"id": "test2", "sequence": "KKEEKKEEKKEEKKEEGGPPGGPP"}
    ]
  }' | jq '.results[] | {id, classification, confidence}'
```

### 10. Batch Processing Large File

```bash
# Process a large FASTA file in batches of 50 sequences
# (This is a simple example - in practice you'd want proper error handling)

split -l 100 large_sequences.fasta batch_

for file in batch_*; do
  echo "Processing $file..."
  curl -X POST http://localhost:8000/api/v1/classify/fasta \
    -H "Content-Type: text/plain" \
    -H "X-API-Key: YOUR_API_KEY_HERE" \
    --data-binary @$file \
    > ${file}_results.json
done
```

### 11. Measure Response Time

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {"id": "test", "sequence": "ACDEFGHIKLMNPQRSTVWY"}
    ]
  }' \
  -w "\nTime total: %{time_total}s\n" \
  -o /dev/null
```

### 12. Save Results to File

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d @input.json \
  -o results.json

echo "Results saved to results.json"
```

## Error Handling Examples

### 13. Missing API Key (401 Error)

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": [
      {"id": "test", "sequence": "MKVLWAASLLLLASAARA"}
    ]
  }'
```

### 14. Invalid API Key (401 Error)

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid_key_12345" \
  -d '{
    "sequences": [
      {"id": "test", "sequence": "MKVLWAASLLLLASAARA"}
    ]
  }'
```

### 15. Invalid Input (422 Error)

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "sequences": [
      {"id": "test", "sequence": ""}
    ]
  }'
```

## Performance Testing

### 16. Benchmark Single Sequence

```bash
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/api/v1/classify \
    -H "Content-Type: application/json" \
    -H "X-API-Key: YOUR_API_KEY_HERE" \
    -d '{
      "sequences": [
        {"id": "test", "sequence": "ACDEFGHIKLMNPQRSTVWY"}
      ]
    }' \
    -w "%{time_total}\n" \
    -o /dev/null
done | awk '{sum+=$1; count++} END {print "Average time:", sum/count, "seconds"}'
```

### 17. Test Batch Performance

```bash
# Generate 50 sequences
cat > batch.json << 'EOF'
{
  "sequences": [
EOF

for i in {1..49}; do
  echo '    {"id": "seq'$i'", "sequence": "ACDEFGHIKLMNPQRSTVWY"},' >> batch.json
done
echo '    {"id": "seq50", "sequence": "ACDEFGHIKLMNPQRSTVWY"}' >> batch.json
echo '  ]
}' >> batch.json

# Test
time curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d @batch.json
```

## API Documentation

### 18. Get OpenAPI Schema

```bash
curl -X GET http://localhost:8000/openapi.json | jq .
```

### 19. View Interactive Documentation

Open in your browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
