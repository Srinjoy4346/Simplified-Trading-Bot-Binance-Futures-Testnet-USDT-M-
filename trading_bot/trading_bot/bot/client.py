"""
Thin wrapper around the Binance Futures Testnet REST API.

Uses direct HTTP calls (requests) with HMAC-SHA256 request signing,
so it has no dependency on the python-binance package version.

Docs: https://binance-docs.github.io/apidocs/testnet/en/
Base URL for USDT-M Futures Testnet: https://testnet.binancefuture.com
"""

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot")


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Binance API error [{status_code}]: {payload}")


class BinanceFuturesTestnetClient:
    """
    Minimal client for placing orders on Binance USDT-M Futures Testnet.

    Handles request signing, sending, and translating HTTP/network errors
    into BinanceAPIError / requests exceptions that the caller can handle.
    """

    BASE_URL = "https://testnet.binancefuture.com"
    ORDER_ENDPOINT = "/fapi/v1/order"
    RECV_WINDOW = 5000

    def __init__(self, api_key: str, api_secret: str, timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must both be provided.")
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params: dict) -> str:
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret, query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _signed_params(self, params: dict) -> dict:
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = self.RECV_WINDOW
        params["signature"] = self._sign(params)
        return params

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                     price: float = None, time_in_force: str = "GTC") -> dict:
        """
        Place a MARKET or LIMIT order on Futures Testnet.

        Returns the parsed JSON response from Binance on success.
        Raises BinanceAPIError on API-level errors (4xx/5xx with error body),
        or requests.exceptions.RequestException on network failures.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        url = self.BASE_URL + self.ORDER_ENDPOINT
        signed_params = self._signed_params(params)

        # Log outgoing request (never log the secret; API key + signature are
        # test-only credentials so logging them at DEBUG level is acceptable
        # for local debugging of this testnet-only tool).
        logger.debug("REQUEST POST %s | params=%s", url, {**params})

        try:
            response = self.session.post(url, params=signed_params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("Network error while calling Binance API: %s", exc)
            raise

        logger.debug("RESPONSE status=%s body=%s", response.status_code, response.text)

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}

        if response.status_code != 200:
            logger.error("Binance API returned error status=%s payload=%s",
                         response.status_code, payload)
            raise BinanceAPIError(response.status_code, payload)

        return payload
