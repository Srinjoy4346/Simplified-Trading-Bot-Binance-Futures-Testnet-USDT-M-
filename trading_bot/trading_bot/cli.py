#!/usr/bin/env python3
"""
CLI entry point for the Simplified Binance Futures Testnet Trading Bot.

Usage examples:

    # Market order
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit order
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000

Credentials are read from environment variables BINANCE_API_KEY and
BINANCE_API_SECRET (see README.md for setup), so they are never typed
on the command line or hard-coded in source.
"""

import argparse
import os
import sys

from bot.client import BinanceFuturesTestnetClient
from bot.logging_config import setup_logging
from bot.orders import place_order

logger = setup_logging()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance USDT-M Futures Testnet."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
                         help="Order side")
    parser.add_argument("--type", required=True, dest="order_type",
                         choices=["MARKET", "LIMIT", "market", "limit"],
                         help="Order type")
    parser.add_argument("--quantity", required=True, help="Order quantity (base asset units)")
    parser.add_argument("--price", required=False, default=None,
                         help="Limit price (required for LIMIT orders)")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("ERROR: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables "
              "(see README.md).", file=sys.stderr)
        return 1

    # Print the order request summary before doing anything network-related.
    print("=" * 50)
    print("ORDER REQUEST SUMMARY")
    print("=" * 50)
    print(f"  Symbol:     {args.symbol.upper()}")
    print(f"  Side:       {args.side.upper()}")
    print(f"  Type:       {args.order_type.upper()}")
    print(f"  Quantity:   {args.quantity}")
    print(f"  Price:      {args.price if args.price else 'N/A (market order)'}")
    print("=" * 50)

    try:
        client = BinanceFuturesTestnetClient(api_key=api_key, api_secret=api_secret)
    except ValueError as exc:
        logger.error("Client init failed: %s", exc)
        print(f"FAILURE: {exc}")
        return 1

    result = place_order(
        client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )

    print()
    if result.success:
        data = result.data
        print("ORDER RESPONSE")
        print("-" * 50)
        print(f"  Order ID:      {data.get('orderId')}")
        print(f"  Status:        {data.get('status')}")
        print(f"  Executed Qty:  {data.get('executedQty')}")
        print(f"  Avg Price:     {data.get('avgPrice', 'N/A')}")
        print("-" * 50)
        print(f"SUCCESS: {result.message}")
        return 0
    else:
        print(f"FAILURE: {result.message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
