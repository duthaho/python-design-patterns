"""
This demonstrates:
- Building a client with Builder pattern
- Making HTTP requests
- Using middleware
"""

import logging
import sys

# Add src to path for examples to work
sys.path.insert(0, "src")

from http_client import HTTPClient
from http_client.middlewares.logging import LoggingMiddleware

# Configure logging to see middleware output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def example_basic_request():
    """Example: Basic HTTP request without middleware"""
    print("\n=== Example 1: Basic Request ===")

    client = HTTPClient()

    try:
        # Make a GET request to JSONPlaceholder (free fake API)
        response = client.get("https://jsonplaceholder.typicode.com/posts/1")

        print(f"Status: {response.status_code}")
        print(f"Success: {response.is_success()}")
        print(f"Response time: {response.elapsed_ms:.2f}ms")
        print(f"Body: {response.json()}")
    finally:
        client.close()


def example_with_builder():
    """Example: Using Builder pattern"""
    print("\n=== Example 2: Builder Pattern ===")

    # Build client with configuration
    client = (
        HTTPClient.builder().base_url("https://jsonplaceholder.typicode.com").timeout(10.0).build()
    )

    with client:  # Using context manager
        # Now we can use relative paths
        response = client.get("/users/1")
        print(f"User: {response.json()}")


def example_with_middleware():
    """Example: Using middleware"""
    print("\n=== Example 3: With Logging Middleware ===")

    client = (
        HTTPClient.builder()
        .base_url("https://jsonplaceholder.typicode.com")
        .add_middleware(LoggingMiddleware())
        .build()
    )

    with client:
        # Request and response will be logged
        response = client.get("/posts/1")
        print(f"Post title: {response.json()['title']}")


def example_post_request():
    """Example: POST request with JSON"""
    print("\n=== Example 4: POST Request ===")

    client = (
        HTTPClient.builder()
        .base_url("https://jsonplaceholder.typicode.com")
        .add_middleware(LoggingMiddleware())
        .build()
    )

    with client:
        new_post = {"title": "My New Post", "body": "This is the content", "userId": 1}

        response = client.post("/posts", json=new_post)
        print(f"Created post ID: {response.json()['id']}")
        print(f"Status: {response.status_code}")


def example_all_methods():
    """Example: Demonstrating all HTTP methods"""
    print("\n=== Example 5: All HTTP Methods ===")

    client = HTTPClient.builder().base_url("https://jsonplaceholder.typicode.com").build()

    with client:
        # GET
        print("GET:", client.get("/posts/1").status_code)

        # POST
        print("POST:", client.post("/posts", json={"title": "Test"}).status_code)

        # PUT
        print("PUT:", client.put("/posts/1", json={"title": "Updated"}).status_code)

        # DELETE
        print("DELETE:", client.delete("/posts/1").status_code)


if __name__ == "__main__":
    # Run all examples
    example_basic_request()
    example_with_builder()
    example_with_middleware()
    example_post_request()
    example_all_methods()

    print("\n✅ All examples completed!")
