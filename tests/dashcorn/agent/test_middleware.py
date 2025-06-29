import pytest
import asyncio
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Scope, Receive, Send

from dashcorn.agent.middleware import MetricsMiddleware, X_REQUEST_ID

from unittest.mock import MagicMock, patch
from types import SimpleNamespace

@pytest.fixture
def fake_app():
    async def app(scope, receive, send):
        pass
    return app

@pytest.mark.asyncio
async def test_dispatch_adds_request_id_and_sends_metrics(fake_app):
    # Arrange
    middleware = MetricsMiddleware(fake_app, enable_request_id=True)

    # Patch dependencies
    middleware._metrics_sender = MagicMock()
    middleware._normalize_path = lambda path: "/normalized"
    
    # Simulate request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/hello",
        "headers": [],
        "query_string": b"",
    }
    receive = lambda: {"type": "http.request"}
    send = lambda msg: None

    request = Request(scope, receive)

    # Simulated response from downstream app
    async def call_next(req):
        assert X_REQUEST_ID in req.scope
        return Response("OK", status_code=200)

    # Act
    response = await middleware.dispatch(request, call_next)

    # Assert
    assert response.status_code == 200
    assert X_REQUEST_ID in response.headers
    assert middleware._metrics_sender.send.called

    sent_payload = middleware._metrics_sender.send.call_args[0][0]
    assert sent_payload["type"] == "http"
    assert sent_payload["method"] == "GET"
    assert sent_payload["status"] == 200
    assert sent_payload["path"] == "/normalized"
    assert "request_id" in sent_payload
    assert "duration" in sent_payload
    assert "time" in sent_payload


@pytest.mark.asyncio
async def test_dispatch_without_request_id():
    # Arrange
    async def fake_app(scope, receive, send):
        pass

    middleware = MetricsMiddleware(fake_app, enable_request_id=False)

    middleware._metrics_sender = MagicMock()
    middleware._normalize_path = lambda path: "/normalized"

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/upload",
        "headers": [],
        "query_string": b"",
    }
    receive = lambda: {"type": "http.request"}
    request = Request(scope, receive)

    async def call_next(req):
        assert X_REQUEST_ID not in req.scope
        return Response("Upload complete", status_code=201)

    # Act
    response = await middleware.dispatch(request, call_next)

    # Assert
    assert response.status_code == 201
    assert X_REQUEST_ID not in response.headers

    middleware._metrics_sender.send.assert_called_once()
    payload = middleware._metrics_sender.send.call_args[0][0]
    assert payload["method"] == "POST"
    assert payload["status"] == 201
    assert "request_id" not in payload  # request_id shouldn't be included


@pytest.mark.asyncio
async def test_dispatch_with_exception_in_call_next():
    # Arrange
    async def fake_app(scope, receive, send):
        pass

    middleware = MetricsMiddleware(fake_app, enable_request_id=True)
    middleware._metrics_sender = MagicMock()
    middleware._normalize_path = lambda path: "/normalized"

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/error",
        "headers": [],
        "query_string": b"",
    }
    receive = lambda: {"type": "http.request"}
    request = Request(scope, receive)

    async def call_next(req):
        raise ValueError("something went wrong")

    # Act & Assert
    with pytest.raises(ValueError):
        await middleware.dispatch(request, call_next)

    # Đảm bảo metrics vẫn được gửi
    middleware._metrics_sender.send.assert_called_once()
    payload = middleware._metrics_sender.send.call_args[0][0]

    assert payload["method"] == "GET"
    assert payload["status"] == 500
    assert payload["path"] == "/normalized"
    assert "request_id" in payload
