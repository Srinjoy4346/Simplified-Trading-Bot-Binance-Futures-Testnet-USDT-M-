# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI app that places MARKET and LIMIT orders on
Binance USDT-M Futures **Testnet**, with input validation, logging, and
clean error handling.

## Project structure

```
trading_bot/
  bot/
    __init__.py
    client.py         # Binance REST API client (signing, requests, error mapping)
    orders.py         # Order placement orchestration (validate -> call -> format)
    validators.py      # Input validation rules
    logging_config.py  # Rotating file + console logging setup
  cli.py               # CLI entry point (argparse)
  logs/
    trading_bot.log     # Created at runtime
  requirements.txt
  README.md
```

## 1. Setup

### 1.1 Create a Binance Futures Testnet account & API key
1. Go to https://testnet.binancefuture.com and log in with a GitHub account.
2. Once logged in, go to **API Key** (usually in the account/settings menu)
   and generate a new API Key + Secret for the testnet.
3. (Optional) Use the testnet faucet/"Reset Balance" feature to top up your
   test USDT balance so you have funds to trade with.

### 1.2 Install dependencies
Requires Python 3.8+.

```bash
cd trading_bot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3 Set your API credentials as environment variables
Credentials are **never** passed on the command line or hard-coded — they're
read from environment variables so they don't end up in shell history or logs.

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```
On Windows (PowerShell):
```powershell
$env:BINANCE_API_KEY="your_testnet_api_key"
$env:BINANCE_API_SECRET="your_testnet_api_secret"
```

## 2. How to run

### Market order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit order
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000
```

### CLI arguments
| Argument      | Required        | Description                                  |
|---------------|-----------------|-----------------------------------------------|
| `--symbol`    | yes             | Futures symbol, e.g. `BTCUSDT`                |
| `--side`      | yes             | `BUY` or `SELL`                               |
| `--type`      | yes             | `MARKET` or `LIMIT`                           |
| `--quantity`  | yes             | Order quantity (base asset units)             |
| `--price`     | only for LIMIT  | Limit price                                    |

The app prints:
- an **order request summary** before sending anything
- the **order response** (orderId, status, executedQty, avgPrice) on success
- a clear **success/failure message**

All requests, responses, and errors are additionally logged to
`logs/trading_bot.log` (rotating, so it won't grow unbounded).

## 3. Error handling covered

- **Invalid input**: bad symbol format, invalid side/order type, non-numeric
  or non-positive quantity/price, missing price on a LIMIT order — all caught
  before any network call, with a clear message and non-zero exit code.
- **API errors**: any non-200 response from Binance (e.g. bad symbol,
  insufficient balance, invalid signature) is caught, logged, and reported
  without crashing.
- **Network errors**: timeouts / connection failures are caught and logged
  rather than raising an unhandled traceback.
- **Missing credentials**: if `BINANCE_API_KEY` / `BINANCE_API_SECRET` are not
  set, the app exits immediately with a clear message instead of failing on
  the first signed request.

## 4. Assumptions

- Only **MARKET** and **LIMIT** order types are required per the core spec;
  LIMIT orders default to `timeInForce=GTC` (Good-Til-Cancelled) since the
  task didn't specify a TIF policy.
- Symbols are validated with a simple pattern (`<BASE>USDT`) rather than
  querying Binance's `/fapi/v1/exchangeInfo`, to keep the app dependency-light
  and fast to run; Binance's own API still performs the authoritative
  validation (e.g. real symbol existence, lot size, tick size) and any
  rejection is surfaced to the user as an API error.
- Direct REST calls (via `requests`) are used instead of the `python-binance`
  package, to avoid pinning to a specific third-party wrapper version and to
  keep the signing logic transparent and auditable in `bot/client.py`.
- Quantity/price precision (lot size / tick size) filters are enforced by
  Binance itself on testnet; the app does not pre-round values, so orders
  with invalid precision will come back as a Binance API error (logged and
  reported cleanly).

## 5. Bonus implemented

- **Enhanced CLI UX**: upfront request summary printout, case-insensitive
  side/type input, structured tabular response output, explicit exit codes
  (0 = success, 1 = failure) for scripting/CI use.

## 6. Log files

Sample log output from a MARKET order and a LIMIT order run is included in
`logs/trading_bot.log` (see log lines timestamped for each run). Re-running
the two commands in section 2 will append fresh entries.
