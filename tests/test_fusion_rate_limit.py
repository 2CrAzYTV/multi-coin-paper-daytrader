from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.market_data import MarketData


def _settings():
    return SimpleNamespace(
        fusion_read_api_key="read-only-test-key",
        fusion_base_url="https://api.fusion.bitpanda.com",
    )


def test_retry_after_seconds_accepts_numeric_seconds():
    assert MarketData._retry_after_seconds("3") == 3.0
    assert MarketData._retry_after_seconds(None) is None


def test_get_json_retries_http_429_and_then_returns_payload():
    market = MarketData(_settings())
    market.MIN_REQUEST_INTERVAL = 0.0

    limited = MagicMock()
    limited.status_code = 429
    limited.headers = {"Retry-After": "0"}

    success = MagicMock()
    success.status_code = 200
    success.headers = {}
    success.raise_for_status.return_value = None
    success.json.return_value = [{"pair": "BTC-EUR"}]

    client = MagicMock()
    client.get.side_effect = [limited, success]
    context = MagicMock()
    context.__enter__.return_value = client
    context.__exit__.return_value = False

    with patch("httpx.Client", return_value=context), patch("app.market_data.time.sleep") as sleep:
        payload = market._get_json("/v1/pairs")

    assert payload == [{"pair": "BTC-EUR"}]
    assert client.get.call_count == 2
    sleep.assert_called_once_with(1.0)


def test_get_json_stops_after_bounded_429_retries():
    market = MarketData(_settings())
    market.MIN_REQUEST_INTERVAL = 0.0
    market.RATE_LIMIT_BACKOFF = (0.0, 0.0)

    limited = MagicMock()
    limited.status_code = 429
    limited.headers = {}

    client = MagicMock()
    client.get.return_value = limited
    context = MagicMock()
    context.__enter__.return_value = client
    context.__exit__.return_value = False

    with patch("httpx.Client", return_value=context), patch("app.market_data.time.sleep"):
        try:
            market._get_json("/v1/pairs")
        except Exception as exc:
            assert "HTTP 429 after automatic retries" in str(exc)
        else:
            raise AssertionError("Expected bounded HTTP 429 retry failure")

    assert client.get.call_count == 3
