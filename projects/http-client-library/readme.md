# HTTP Client Library

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-253%20passed-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](htmlcov/index.html)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A production-ready HTTP client library built to demonstrate design patterns in Python. Features authentication, retry logic, caching, rate limiting, and comprehensive middleware support.

**🎓 Built as a learning project to master 6+ design patterns through practical implementation.**

---

## ✨ Features

### 🔐 Authentication
- **Bearer Token** authentication
- **Basic Auth** (username/password)
- **API Key** authentication (header or query parameter)
- Easily extensible with custom auth strategies

### 🔄 Retry Logic
- **Exponential backoff** strategy
- **Jittered backoff** to prevent thundering herd
- Configurable max retries and delays
- Intelligent error classification (retryable vs non-retryable)

### 💾 Caching
- **In-memory cache** with TTL support
- **Redis cache** for distributed caching
- Automatic cache key generation
- Thread-safe operations

### 🚦 Rate Limiting
- **Token bucket** algorithm
- Per-second rate limiting
- Burst capacity support
- Per-endpoint or global limits

### 🔧 Middleware System
- Extensible middleware pipeline
- Request/response interceptors
- Easy to add custom middleware
- Middleware execute in configurable order

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/duthaho/http-client-library.git
cd http-client-library

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .
```

### Basic Usage

```python
from http_client import HTTPClient

# Simple GET request
client = HTTPClient()
response = client.get("https://api.github.com/users/octocat")
print(response.json())
```

### With Builder Pattern

```python
from http_client import HTTPClient
from http_client.auth.bearer import BearerTokenAuth
from http_client.retry.exponential import ExponentialBackoff
from http_client.cache.memory import MemoryCache

# Build configured client
client = HTTPClient.builder() \
    .base_url("https://api.github.com") \
    .timeout(10.0) \
    .with_auth(BearerTokenAuth("ghp_your_token")) \
    .with_retry(ExponentialBackoff(max_retries=3)) \
    .with_cache(MemoryCache(default_ttl=300)) \
    .with_rate_limit(rate=10, capacity=20) \
    .build()

# Make requests - automatically authenticated, retried, cached, and rate-limited!
response = client.get("/users/octocat")
```

---

## 📚 Documentation

### Authentication

#### Bearer Token
```python
from http_client.auth.bearer import BearerTokenAuth

client = HTTPClient.builder() \
    .with_auth(BearerTokenAuth("your-token-here")) \
    .build()
```

#### Basic Authentication
```python
from http_client.auth.basic import BasicAuth

client = HTTPClient.builder() \
    .with_auth(BasicAuth("username", "password")) \
    .build()
```

#### API Key
```python
from http_client.auth.api_key import APIKeyAuth

# API key in header
client = HTTPClient.builder() \
    .with_auth(APIKeyAuth("secret123", location="header", param_name="X-API-Key")) \
    .build()

# API key in query parameter
client = HTTPClient.builder() \
    .with_auth(APIKeyAuth("secret123", location="query", param_name="api_key")) \
    .build()
```

### Retry Strategies

#### Exponential Backoff
```python
from http_client.retry.exponential import ExponentialBackoff

# Retry up to 3 times with exponential delays: 1s, 2s, 4s
retry = ExponentialBackoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0
)

client = HTTPClient.builder() \
    .with_retry(retry) \
    .build()
```

#### Jittered Backoff
```python
from http_client.retry.jittered import JitteredBackoff

# Add randomness to prevent synchronized retries
retry = JitteredBackoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    jitter_factor=0.3  # ±30% randomness
)

client = HTTPClient.builder() \
    .with_retry(retry) \
    .build()
```

### Caching

#### Memory Cache
```python
from http_client.cache.memory import MemoryCache

# In-memory cache with 5-minute TTL
cache = MemoryCache(default_ttl=300, max_size=1000)

client = HTTPClient.builder() \
    .with_cache(cache) \
    .build()

# First call hits API
response = client.get("/users/octocat")

# Second call returns from cache (instant!)
response = client.get("/users/octocat")
```

#### Redis Cache
```python
from http_client.cache.redis import RedisCache

# Distributed cache with Redis
cache = RedisCache(
    host="localhost",
    port=6379,
    default_ttl=600
)

client = HTTPClient.builder() \
    .with_cache(cache) \
    .build()
```

### Rate Limiting

```python
# Limit to 10 requests per second with burst of 20
client = HTTPClient.builder() \
    .with_rate_limit(rate=10, capacity=20) \
    .build()

# Automatically throttled
for i in range(100):
    response = client.get(f"/api/data?page={i}")
```

### Custom Middleware

```python
from http_client.middleware import Middleware
from http_client.models import Request, Response

class CustomHeaderMiddleware(Middleware):
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
    
    def process_request(self, request: Request) -> Request:
        request.headers.update(self.headers)
        return request
    
    def process_response(self, response: Response) -> Response:
        return response

# Use custom middleware
client = HTTPClient.builder() \
    .add_middleware(CustomHeaderMiddleware({'User-Agent': 'MyApp/1.0'})) \
    .build()
```

---

## 🏗️ Architecture

### Design Patterns Implemented

| Pattern | Component | Purpose |
|---------|-----------|---------|
| **Builder** | HTTPClientBuilder | Fluent API for client configuration |
| **Chain of Responsibility** | Middleware Pipeline | Request/response processing chain |
| **Strategy** | Auth Strategies | Interchangeable authentication methods |
| **Strategy** | Retry Strategies | Interchangeable retry algorithms |
| **Decorator** | Retry Wrapper | Wrap execution with retry logic |
| **Adapter** | RedisCache | Adapt Redis API to Cache interface |
| **Proxy** | CacheMiddleware | Intercept requests for caching |

### Project Structure

```
http-client-library/
├── src/http_client/
│   ├── __init__.py
│   ├── client.py              # HTTPClient + Builder
│   ├── middleware.py          # Middleware base classes
│   ├── models.py              # Request/Response models
│   ├── exceptions.py          # Custom exceptions
│   │
│   ├── auth/                  # Authentication strategies
│   │   ├── base.py
│   │   ├── bearer.py
│   │   ├── basic.py
│   │   └── api_key.py
│   │
│   ├── retry/                 # Retry strategies
│   │   ├── base.py
│   │   ├── exponential.py
│   │   └── jittered.py
│   │
│   ├── cache/                 # Cache implementations
│   │   ├── base.py
│   │   ├── memory.py
│   │   └── redis.py
│   │
│   ├── rate_limit/            # Rate limiting
│   │   └── token_bucket.py
│   │
│   └── middlewares/           # Concrete middlewares
│       ├── logging.py
│       ├── auth.py
│       ├── cache.py
│       └── rate_limit.py
│
├── tests/                     # Comprehensive test suite
├── examples/                  # Usage examples
└── docs/                      # Documentation
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=http_client --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_client.py -v

# Run tests by marker
pytest tests/ -m "not integration" -v
```

### Test Coverage

```
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
http_client/__init__.py                  15      0   100%
http_client/client.py                    89      3    97%
http_client/middleware.py                45      0   100%
http_client/models.py                    35      0   100%
http_client/auth/bearer.py               18      0   100%
http_client/auth/basic.py                21      0   100%
http_client/auth/api_key.py              25      0   100%
http_client/retry/exponential.py         20      0   100%
http_client/retry/jittered.py            22      0   100%
http_client/cache/memory.py              65      2    97%
http_client/cache/redis.py               48      5    90%
http_client/rate_limit/token_bucket.py   45      1    98%
---------------------------------------------------------
TOTAL                                   448     11    95%
```

### Test Statistics

- **Total Tests:** 253
- **Pass Rate:** 100%
- **Coverage:** 95%+
- **Average Runtime:** < 3 seconds

---

## 📖 Examples

Check the `examples/` directory for complete working examples:

- `basic_usage.py` - Simple HTTP requests
- `with_auth.py` - Authentication examples
- `with_retry.py` - Retry logic examples
- `with_cache.py` - Caching examples
- `advanced.py` - All features combined

---

## 🎓 Learning Resources

This project was built to learn design patterns. Here are the patterns demonstrated:

### Phase 1: Foundation
- **Builder Pattern** - Clean object construction
- **Chain of Responsibility** - Middleware pipeline

### Phase 2: Authentication & Retry
- **Strategy Pattern** - Interchangeable algorithms
- **Decorator Pattern** - Wrapping with additional behavior
- **Dependency Injection** - Strategy into middleware

### Phase 3: Caching & Rate Limiting
- **Adapter Pattern** - Adapting external APIs
- **Proxy Pattern** - Intercepting requests
- **State Pattern** - Managing state over time

### Documentation
- `docs/architecture.md` - Architecture decisions
- `docs/patterns.md` - Pattern explanations
- `docs/api_reference.md` - API documentation

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linters
make lint

# Format code
make format

# Run tests
make test
```

### Code Quality

```bash
# Format with black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

---

## 🤝 Contributing

Contributions are welcome! This is a learning project, so improvements to code quality, documentation, and examples are appreciated.

### Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`make test`)
6. Format code (`make format`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built as a learning project to master design patterns
- Inspired by industry-standard HTTP clients like `requests`, `httpx`, and `aiohttp`
- Design pattern implementations follow Gang of Four principles
- Architecture influenced by professional API client libraries

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/duthaho/http-client-library/issues)
- **Discussions:** [GitHub Discussions](https://github.com/duthaho/http-client-library/discussions)
- **Documentation:** [docs/](docs/)

---

## 🗺️ Roadmap

### Completed ✅
- [x] Core HTTP client with Builder pattern
- [x] Middleware pipeline system
- [x] Authentication strategies (Bearer, Basic, API Key)
- [x] Retry logic with exponential and jittered backoff
- [x] Memory and Redis caching
- [x] Token bucket rate limiting
- [x] Comprehensive test suite (253 tests)

### Future Enhancements 🚀
- [ ] Circuit breaker pattern
- [ ] Request/response hooks (Observer pattern)
- [ ] Async support with asyncio
- [ ] Connection pooling optimization
- [ ] Metrics and observability
- [ ] OAuth2 authentication flow
- [ ] Request signing (HMAC, AWS Signature)
- [ ] Compression support (gzip, deflate)
- [ ] Streaming response support
- [ ] WebSocket support

---

## 💡 Why This Project?

This HTTP client library was built as a **comprehensive learning project** to:

1. **Master Design Patterns** - Apply 6+ patterns in real-world context
2. **Practice TDD** - Write tests alongside implementation
3. **Learn Architecture** - Make design decisions and trade-offs
4. **Build Production Code** - Focus on quality, testing, documentation
5. **Understand HTTP** - Deep dive into HTTP clients, auth, caching

**Result:** A fully functional, well-tested, production-ready HTTP client library that demonstrates professional software engineering practices.

---

## 📊 Project Stats

- **Lines of Code:** ~3,500
- **Test Coverage:** 95%+
- **Design Patterns:** 7
- **Tests:** 253
- **Documentation:** Complete
- **Development Time:** 30+ hours
- **Python Version:** 3.9+

---

## 🌟 Star History

If you found this project helpful for learning design patterns, consider giving it a star! ⭐

---

**Built with ❤️ to learn and demonstrate design patterns in Python**

[⬆ Back to top](#http-client-library)