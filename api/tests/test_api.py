"""
Tests for the FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.app.main import app
from api.app.auth import DEMO_API_KEY


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def headers():
    """Create headers with demo API key."""
    return {"X-API-Key": DEMO_API_KEY}


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'uptime_seconds' in data
        assert data['uptime_seconds'] >= 0
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert 'message' in data
        assert 'version' in data


class TestClassifyEndpoint:
    """Tests for the classification endpoint."""
    
    def test_classify_single_sequence(self, client, headers):
        """Test classification of a single sequence."""
        request_data = {
            "sequences": [
                {
                    "id": "test1",
                    "sequence": "MKVLWAASLLLLASAARA"
                }
            ]
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_sequences'] == 1
        assert len(data['results']) == 1
        
        result = data['results'][0]
        assert result['id'] == 'test1'
        assert result['classification'] in ['structured', 'disordered']
        assert 0.5 <= result['confidence'] <= 1.0
        assert 0 <= result['conditions_met'] <= 7
        assert result['threshold'] == 4
        assert 'features' in result
        assert 'processing_time_ms' in result
    
    def test_classify_multiple_sequences(self, client, headers):
        """Test classification of multiple sequences."""
        request_data = {
            "sequences": [
                {"id": "seq1", "sequence": "MKVLWAASLLLLASAARA"},
                {"id": "seq2", "sequence": "MALWMRLLPLLALLALWGPDPAAAF"},
                {"id": "seq3", "sequence": "ACDEFGHIKLMNPQRSTVWY"}
            ]
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_sequences'] == 3
        assert len(data['results']) == 3
        assert all('classification' in r for r in data['results'])
    
    def test_classify_with_custom_threshold(self, client, headers):
        """Test classification with custom threshold."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": "MKVLWAASLLLLASAARA"}
            ],
            "threshold": 5
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['results'][0]['threshold'] == 5
    
    def test_missing_api_key(self, client):
        """Test request without API key."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": "MKVLWAASLLLLASAARA"}
            ]
        }
        
        response = client.post("/api/v1/classify", json=request_data)
        assert response.status_code == 401
    
    def test_invalid_api_key(self, client):
        """Test request with invalid API key."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": "MKVLWAASLLLLASAARA"}
            ]
        }
        
        invalid_headers = {"X-API-Key": "invalid_key_12345"}
        response = client.post("/api/v1/classify", json=request_data, headers=invalid_headers)
        assert response.status_code == 401
    
    def test_empty_sequence(self, client, headers):
        """Test with empty sequence."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": ""}
            ]
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_threshold(self, client, headers):
        """Test with invalid threshold."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": "MKVLWAASLLLLASAARA"}
            ],
            "threshold": 10  # Out of range
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_too_many_sequences(self, client, headers):
        """Test with too many sequences (exceeds batch limit)."""
        # Create 51 sequences (free tier limit is 50)
        sequences = [{"id": f"seq{i}", "sequence": "ACDEFG"} for i in range(51)]
        request_data = {"sequences": sequences}
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 400
        assert "exceeds limit" in response.json()['detail'].lower()
    
    def test_feature_values(self, client, headers):
        """Test that all feature values are returned."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": "ACDEFGHIKLMNPQRSTVWY"}
            ]
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 200
        
        features = response.json()['results'][0]['features']
        expected_features = [
            'hydro_norm_avg',
            'flex_norm_avg',
            'h_bond_potential_avg',
            'abs_net_charge_prop',
            'shannon_entropy',
            'freq_proline',
            'freq_bulky_hydrophobics'
        ]
        
        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], (int, float))


class TestClassifyFastaEndpoint:
    """Tests for the FASTA classification endpoint."""
    
    def test_classify_fasta_single(self, client, headers):
        """Test FASTA classification with single sequence."""
        fasta_data = ">test1\nMKVLWAASLLLLASAARA"
        
        response = client.post(
            "/api/v1/classify/fasta",
            data=fasta_data,
            headers={**headers, "Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_sequences'] == 1
        assert data['results'][0]['id'] == 'test1'
    
    def test_classify_fasta_multiple(self, client, headers):
        """Test FASTA classification with multiple sequences."""
        fasta_data = """
>protein1
MKVLWAASLLLLASAARA
>protein2
MALWMRLLPLLALLALWGPDPAAAF
>protein3
ACDEFGHIKLMNPQRSTVWY
"""
        
        response = client.post(
            "/api/v1/classify/fasta",
            data=fasta_data,
            headers={**headers, "Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_sequences'] == 3
        assert len(data['results']) == 3
    
    def test_classify_fasta_multiline(self, client, headers):
        """Test FASTA with multiline sequences."""
        fasta_data = """>test1
MKVLWAASLLLL
LASAARA
>test2
MALWMRLLPLL
ALLALWGPDPAAAF"""
        
        response = client.post(
            "/api/v1/classify/fasta",
            data=fasta_data,
            headers={**headers, "Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_sequences'] == 2
    
    def test_classify_fasta_with_threshold(self, client, headers):
        """Test FASTA classification with custom threshold."""
        fasta_data = ">test1\nMKVLWAASLLLLASAARA"
        
        response = client.post(
            "/api/v1/classify/fasta?threshold=5",
            data=fasta_data,
            headers={**headers, "Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['results'][0]['threshold'] == 5
    
    def test_classify_fasta_invalid(self, client, headers):
        """Test with invalid FASTA format."""
        # No header, just sequence
        fasta_data = "MKVLWAASLLLLASAARA"
        
        response = client.post(
            "/api/v1/classify/fasta",
            data=fasta_data,
            headers={**headers, "Content-Type": "text/plain"}
        )
        assert response.status_code == 400
        assert "FASTA" in response.json()['detail']
    
    def test_classify_fasta_empty(self, client, headers):
        """Test with empty FASTA input."""
        response = client.post(
            "/api/v1/classify/fasta",
            data="",
            headers={**headers, "Content-Type": "text/plain"}
        )
        assert response.status_code == 400


class TestPerformance:
    """Performance tests for the API."""
    
    def test_batch_processing_speed(self, client, headers):
        """Test that batch processing is fast."""
        import time
        
        # Create 50 sequences (max batch size for free tier)
        sequences = [
            {"id": f"seq{i}", "sequence": "ACDEFGHIKLMNPQRSTVWY"*2}
            for i in range(50)
        ]
        request_data = {"sequences": sequences}
        
        start_time = time.time()
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        
        # Should process 50 sequences in less than 2 seconds
        assert elapsed_time < 2.0
        
        # Check reported processing time
        data = response.json()
        assert data['total_time_ms'] < 2000
    
    def test_single_sequence_speed(self, client, headers):
        """Test single sequence classification speed."""
        request_data = {
            "sequences": [
                {"id": "test1", "sequence": "ACDEFGHIKLMNPQRSTVWY"*5}
            ]
        }
        
        response = client.post("/api/v1/classify", json=request_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Single sequence should be very fast
        assert data['results'][0]['processing_time_ms'] < 50


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert 'openapi' in schema
        assert 'info' in schema
        assert 'paths' in schema
    
    def test_swagger_ui(self, client):
        """Test that Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc(self, client):
        """Test that ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
