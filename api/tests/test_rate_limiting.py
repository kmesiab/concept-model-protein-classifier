"""
Tests for atomic rate limiting functionality.
"""

import concurrent.futures
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import DEMO_API_KEY
from app.main import app
from app.rate_limiter import RateLimiter


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def headers():
    """Create headers with demo API key."""
    return {"X-API-Key": DEMO_API_KEY}


@pytest.fixture
def rate_limiter():
    """Create a rate limiter instance for testing with isolated Redis state."""
    rate_limiter_instance = RateLimiter()
    try:
        # Provide the rate limiter to the test.
        yield rate_limiter_instance
    finally:
        # Ensure Redis state created by this test does not affect other tests.
        if getattr(rate_limiter_instance, "redis_available", False):
            redis_client = getattr(rate_limiter_instance, "redis", None)
            if redis_client is not None:
                # Only remove keys created by this test suite (prefixed with "test:").
                for key in redis_client.scan_iter("test:*"):
                    redis_client.delete(key)


class TestAtomicRateLimiting:
    """Tests for atomic rate limiting operations."""

    def test_redis_atomic_increment(self, rate_limiter):
        """Test that Redis operations are atomic using Lua script."""
        if not rate_limiter.redis_available:
            pytest.skip("Redis not available")

        api_key_hash = "test_hash_atomic"
        max_requests = 5
        ttl = 60
        test_key = f"test:atomic:{api_key_hash}"

        try:
            # Make requests up to the limit
            for i in range(max_requests):
                allowed, error_msg, error_details = rate_limiter._check_counter(
                    test_key, max_requests, ttl, "test requests"
                )
                assert allowed is True
                assert error_msg is None
                assert error_details is None

            # Next request should fail
            allowed, error_msg, error_details = rate_limiter._check_counter(
                test_key, max_requests, ttl, "test requests"
            )
            assert allowed is False
            assert error_msg is not None
            assert error_details is not None
            assert error_details["error_code"] == "ERR_RATE_LIMIT_EXCEEDED"
            assert error_details["retry_after"] > 0
            assert error_details["limit"] == max_requests
            assert error_details["current"] == max_requests
        finally:
            # Cleanup: delete test key
            if rate_limiter.redis_available and hasattr(rate_limiter, "redis_client"):
                rate_limiter.redis_client.delete(test_key)

    def test_concurrent_requests_no_bypass(self, rate_limiter):
        """Test that concurrent requests cannot bypass rate limits."""
        if not rate_limiter.redis_available:
            pytest.skip("Redis not available")

        api_key_hash = "test_hash_concurrent"
        max_requests = 10
        ttl = 60
        num_threads = 20
        test_key = f"test:concurrent:{api_key_hash}"

        try:

            def make_request():
                """Make a single rate limit check."""
                allowed, _, _ = rate_limiter._check_counter(
                    test_key, max_requests, ttl, "test requests"
                )
                return allowed

            # Execute concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(make_request) for _ in range(num_threads)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # Count how many were allowed
            allowed_count = sum(1 for r in results if r)

            # Should be exactly max_requests, not more (proving atomicity)
            assert allowed_count == max_requests
        finally:
            # Cleanup: delete test key
            if rate_limiter.redis_available and hasattr(rate_limiter, "redis_client"):
                rate_limiter.redis_client.delete(test_key)

    def test_concurrent_sequence_quota(self, rate_limiter):
        """Test atomic sequence quota with concurrent requests."""
        if not rate_limiter.redis_available:
            pytest.skip("Redis not available")

        api_key_hash = "test_hash_sequences"
        max_sequences = 20
        ttl = 86400
        num_threads = 10
        sequences_per_request = 3
        test_key = f"test:sequences:{api_key_hash}"

        try:

            def make_request():
                """Make a single quota check with multiple sequences."""
                allowed, _, _ = rate_limiter._check_counter(
                    test_key,
                    max_sequences,
                    ttl,
                    "test sequences",
                    increment=sequences_per_request,
                )
                return allowed

            # Execute concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(make_request) for _ in range(num_threads)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # Count allowed requests
            allowed_count = sum(1 for r in results if r)

            # Should allow floor(max_sequences / sequences_per_request) requests
            # 20 / 3 = 6 requests (18 sequences), 7th request would need 21 sequences
            assert allowed_count == 6
        finally:
            # Cleanup: delete test key
            if rate_limiter.redis_available and hasattr(rate_limiter, "redis_client"):
                rate_limiter.redis_client.delete(test_key)

    def test_error_response_structure(self, rate_limiter):
        """Test that error responses contain all required fields."""
        if not rate_limiter.redis_available:
            pytest.skip("Redis not available")

        api_key_hash = "test_hash_error"
        max_requests = 1
        ttl = 60
        test_key = f"test:error:{api_key_hash}"

        try:
            # Use up the limit
            rate_limiter._check_counter(test_key, max_requests, ttl, "test")

            # Next request should return error with all fields
            allowed, error_msg, error_details = rate_limiter._check_counter(
                test_key,
                max_requests,
                ttl,
                "test requests",
                error_code="ERR_RATE_LIMIT_EXCEEDED",
            )

            assert allowed is False
            assert error_msg == "Rate limit exceeded: 1 test requests"
            assert error_details is not None
            assert "error_code" in error_details
            assert "retry_after" in error_details
            assert "limit" in error_details
            assert "current" in error_details
            assert error_details["error_code"] == "ERR_RATE_LIMIT_EXCEEDED"
            assert error_details["retry_after"] > 0
            assert error_details["limit"] == max_requests
        finally:
            # Cleanup: delete test key
            if rate_limiter.redis_available and hasattr(rate_limiter, "redis_client"):
                rate_limiter.redis_client.delete(test_key)

    def test_quota_exceeded_error_code(self, rate_limiter):
        """Test that daily quota uses ERR_QUOTA_EXCEEDED error code."""
        if not rate_limiter.redis_available:
            pytest.skip("Redis not available")

        api_key_hash = "test_hash_quota"
        max_sequences = 5
        ttl = 86400
        test_key = f"test:quota:{api_key_hash}"

        try:
            # Use up the quota
            for _ in range(max_sequences):
                rate_limiter._check_counter(
                    test_key,
                    max_sequences,
                    ttl,
                    "sequences",
                    error_code="ERR_QUOTA_EXCEEDED",
                )

            # Next request should return quota exceeded error
            allowed, error_msg, error_details = rate_limiter._check_counter(
                test_key,
                max_sequences,
                ttl,
                "sequences per day",
                error_code="ERR_QUOTA_EXCEEDED",
            )

            assert allowed is False
            assert error_details["error_code"] == "ERR_QUOTA_EXCEEDED"
        finally:
            # Cleanup: delete test key
            if rate_limiter.redis_available and hasattr(rate_limiter, "redis_client"):
                rate_limiter.redis_client.delete(test_key)


class TestRateLimitingEndpoints:
    """Tests for rate limiting on API endpoints."""

    def test_rate_limit_exceeded_response(self, client, headers):
        """Test that rate limit exceeded returns proper 429 response."""
        # Mock the rate limiter to always fail
        with patch("app.main.get_rate_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.check_rate_limit.return_value = (
                False,
                "Rate limit exceeded: 100 requests per minute",
                {
                    "error_code": "ERR_RATE_LIMIT_EXCEEDED",
                    "retry_after": 45,
                    "limit": 100,
                    "current": 100,
                },
            )
            mock_get_limiter.return_value = mock_limiter

            request_data = {"sequences": [{"id": "test1", "sequence": "MKVLWAASLLLLASAARA"}]}

            response = client.post("/api/v1/classify", json=request_data, headers=headers)

            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], dict)
            assert data["detail"]["code"] in ["ERR_RATE_LIMIT_EXCEEDED", "ERR_QUOTA_EXCEEDED"]
            assert "retry_after" in data["detail"]
            assert "limit" in data["detail"]
            assert "current" in data["detail"]

    def test_quota_exceeded_response(self, client, headers):
        """Test that quota exceeded returns proper 429 response."""
        # Mock the rate limiter to return quota exceeded
        with patch("app.main.get_rate_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.check_rate_limit.return_value = (
                False,
                "Rate limit exceeded: 1000 sequences per day",
                {
                    "error_code": "ERR_QUOTA_EXCEEDED",
                    "retry_after": 3600,
                    "limit": 1000,
                    "current": 1000,
                },
            )
            mock_get_limiter.return_value = mock_limiter

            request_data = {"sequences": [{"id": "test1", "sequence": "MKVLWAASLLLLASAARA"}]}

            response = client.post("/api/v1/classify", json=request_data, headers=headers)

            assert response.status_code == 429
            data = response.json()
            assert data["detail"]["code"] == "ERR_QUOTA_EXCEEDED"
            assert data["detail"]["retry_after"] > 0

    def test_fasta_endpoint_rate_limiting(self, client, headers):
        """Test that FASTA endpoint also enforces rate limits."""
        # Mock the rate limiter to fail
        with patch("app.main.get_rate_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_limiter.check_rate_limit.return_value = (
                False,
                "Rate limit exceeded: 100 requests per minute",
                {
                    "error_code": "ERR_RATE_LIMIT_EXCEEDED",
                    "retry_after": 30,
                    "limit": 100,
                    "current": 100,
                },
            )
            mock_get_limiter.return_value = mock_limiter

            fasta_data = ">test1\nMKVLWAASLLLLASAARA"

            response = client.post(
                "/api/v1/classify/fasta",
                data=fasta_data,
                headers={**headers, "Content-Type": "text/plain"},
            )

            assert response.status_code == 429
            data = response.json()
            assert data["detail"]["code"] == "ERR_RATE_LIMIT_EXCEEDED"


class TestInMemoryFallback:
    """Tests for in-memory fallback when Redis is unavailable."""

    def test_fallback_rate_limiting(self):
        """Test that in-memory fallback works when Redis is unavailable."""
        # Create rate limiter without Redis
        limiter = RateLimiter(redis_url="redis://invalid:9999")
        assert limiter.redis_available is False

        api_key_hash = "test_hash_memory"
        max_requests = 3
        ttl = 60

        # Make requests up to the limit
        for _ in range(max_requests):
            allowed, error_msg, error_details = limiter._check_counter(
                f"test:memory:{api_key_hash}", max_requests, ttl, "test requests"
            )
            assert allowed is True

        # Next request should fail
        allowed, error_msg, error_details = limiter._check_counter(
            f"test:memory:{api_key_hash}", max_requests, ttl, "test requests"
        )
        assert allowed is False
        assert error_details is not None
        assert error_details["retry_after"] > 0

    def test_fallback_ttl_expiration(self):
        """Test that in-memory fallback respects TTL."""
        limiter = RateLimiter(redis_url="redis://invalid:9999")
        assert limiter.redis_available is False

        api_key_hash = "test_hash_ttl"
        max_requests = 2
        ttl = 1  # 1 second TTL

        # Use up the limit
        for _ in range(max_requests):
            limiter._check_counter(f"test:ttl:{api_key_hash}", max_requests, ttl, "test")

        # Should fail immediately
        allowed, _, _ = limiter._check_counter(
            f"test:ttl:{api_key_hash}", max_requests, ttl, "test"
        )
        assert allowed is False

        # Wait for TTL to expire (1.1s for 1s TTL to ensure expiration)
        time.sleep(1.1)

        # Should succeed after TTL expires
        allowed, _, _ = limiter._check_counter(
            f"test:ttl:{api_key_hash}", max_requests, ttl, "test"
        )
        assert allowed is True
