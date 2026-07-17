"""
Order placement orchestration.

Sits between the CLI and the API client: validates input, logs the
request summary, calls the client, and formats the response for
display. Keeping this separate from cli.py means the same logic could
be reused by a future UI or test suite.
"""

import logging

from .client import BinanceAPIError, BinanceFuturesTestnetClient
from .validators import ValidationError, validate_order_params

logger = logging.getLogger("trading_bot")


class OrderResult:
    """Simple container describing the outcome of an order attempt."""

    def __init__(self, success: bool, message: str, data: dict = None):
        self.success = success
        self.message = message
        self.data = data or {}


def place_order(client: BinanceFuturesTestnetClient, symbol, side, order_type,
                 quantity, price=None) -> OrderResult:
    """
    Validate parameters, place the order via the client, and return an
    OrderResult describing success/failure. Never raises — all errors
    are caught and returned as a failed OrderResult so the CLI layer
    can print a clean message and exit with the right status code.
    """
    try:
        params = validate_order_params(symbol, side, order_type, quantity, price)
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc)
        return OrderResult(success=False, message=f"Validation error: {exc}")

    logger.info(
        "Order request | symbol=%s side=%s type=%s quantity=%s price=%s",
        params["symbol"], params["side"], params["order_type"],
        params["quantity"], params["price"],
    )

    try:
        response = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
        )
    except BinanceAPIError as exc:
        logger.error("Order failed (API error): %s", exc)
        return OrderResult(
            success=False,
            message=f"Order rejected by Binance API (status {exc.status_code}): {exc.payload}",
        )
    except Exception as exc:  # network errors, timeouts, etc.
        logger.error("Order failed (unexpected/network error): %s", exc)
        return OrderResult(success=False, message=f"Order failed due to network/unexpected error: {exc}")

    logger.info(
        "Order response | orderId=%s status=%s executedQty=%s avgPrice=%s",
        response.get("orderId"), response.get("status"),
        response.get("executedQty"), response.get("avgPrice"),
    )

    return OrderResult(success=True, message="Order placed successfully.", data=response)
