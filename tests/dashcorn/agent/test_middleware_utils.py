import pytest
from starlette.requests import Request
from starlette.routing import Route
from starlette.datastructures import URL
from dashcorn.agent.middleware import get_route_path

class DummyReceive:
    async def __call__(self):
        return {"type": "http.request"}

def make_request(scope_overrides=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/hello/world",
        "headers": [],
        "query_string": b"",
    }
    if scope_overrides:
        scope.update(scope_overrides)
    return Request(scope, DummyReceive())

def test_get_route_path_with_route():
    request = make_request({
        "route": Route("/hello/world", endpoint=lambda x: x)
    })
    result = get_route_path(request)
    assert result == "/hello/world"

def test_get_route_path_without_route_fallback_url():
    request = make_request()
    result = get_route_path(request)
    assert result == "?"

def test_get_route_path_without_route_with_normalize():
    request = make_request()
    result = get_route_path(request, normalize=lambda path: path.upper())
    assert result == "/HELLO/WORLD"

def test_get_route_path_safe_check_false_with_route():
    request = make_request({
        "route": Route("/test-path", endpoint=lambda x: x)
    })
    result = get_route_path(request, safe_check=False)
    assert result == "/test-path"

def test_get_route_path_safe_check_false_without_route():
    request = make_request()
    result = get_route_path(request, safe_check=False)
    assert result == "/hello/world"
