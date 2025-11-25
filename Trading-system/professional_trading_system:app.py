from flask import Flask, render_template, jsonify, request
import random
from datetime import datetime, timedelta, date
import json
import sqlite3

from market_data.api_connector import MarketAPI
from main_trading_system import CONFIG

app = Flask(__name__)


# --- Helpers ---
def get_db_connection():
    conn = sqlite3.connect('trading_system.db')
    conn.row_factory = sqlite3.Row
    return conn


def serialize_row(row):
    return {key: row[key] for key in row.keys()}


def fallback_symbols():
    symbols = CONFIG.get('symbols', ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
    return [{'symbol': s, 'name': s, 'timeframe': CONFIG.get('timeframe', '1h')} for s in symbols]


market_api = MarketAPI(CONFIG.get('exchange', 'binance'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/terminal')
def terminal():
    return render_template('terminal.html')


@app.route('/api/market-data/<path:symbol>')
def get_market_data(symbol):
    timeframe = request.args.get('timeframe', CONFIG.get('timeframe', '1h'))
    df = market_api.get_ohlcv(symbol, timeframe=timeframe, limit=150)

    if df.empty:
        return jsonify([])

    data = [
        {
            'time': row.timestamp.isoformat(),
            'open': float(row.open),
            'high': float(row.high),
            'low': float(row.low),
            'close': float(row.close),
            'volume': float(row.volume),
        }
        for row in df.itertuples()
    ]
    return jsonify(data)


@app.route('/api/portfolio-data')
def get_portfolio_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    cursor.execute(
        """
        SELECT COUNT(*) as total_trades,
               SUM(CASE WHEN signal_type = 'LONG' THEN 1 ELSE 0 END) as long_trades,
               SUM(CASE WHEN signal_type = 'SHORT' THEN 1 ELSE 0 END) as short_trades
        FROM signals
        WHERE date(timestamp) = ?
        """,
        (today,),
    )
    trade_stats = cursor.fetchone() or {'total_trades': 0, 'long_trades': 0, 'short_trades': 0}

    cursor.execute(
        """
        SELECT * FROM trades
        WHERE date(timestamp) = ?
        ORDER BY timestamp DESC
        LIMIT 50
        """,
        (today,),
    )
    todays_trades = [serialize_row(row) for row in cursor.fetchall()]

    # Balance simulated from risk manager baseline with today's PnL approximation
    base_capital = CONFIG.get('base_capital', 10000)
    realized_pnl = sum((trade.get('profit_potential') or 0) for trade in todays_trades)

    portfolio = {
        'balance': base_capital + realized_pnl,
        'daily_pnl': realized_pnl,
        'win_rate': 0,
        'total_trades': trade_stats['total_trades'] if isinstance(trade_stats, dict) else trade_stats[0],
        'balance_history': [
            {'timestamp': (datetime.now() - timedelta(days=i)).isoformat(), 'balance': base_capital}
            for i in range(30)
        ],
        'positions': get_open_positions(conn),
        'trades': todays_trades,
    }

    conn.close()
    return jsonify(portfolio)


def get_open_positions(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT symbol, signal_type, entry_price, stop_loss, take_profit, position_size, risk_amount, timeframe, timestamp
        FROM trades
        WHERE status = 'OPEN'
        ORDER BY timestamp DESC
        LIMIT 20
        """
    )
    rows = cursor.fetchall()
    positions = []
    for row in rows:
        data = serialize_row(row)
        positions.append(
            {
                'symbol': data.get('symbol'),
                'type': data.get('signal_type'),
                'size': data.get('position_size'),
                'pnl': 0,
                'entry': data.get('entry_price'),
                'timeframe': data.get('timeframe'),
                'opened_at': data.get('timestamp'),
            }
        )
    return positions


@app.route('/api/real-time-data')
def get_real_time_data():
    symbols = fallback_symbols()
    symbol = symbols[0]['symbol']
    try:
        ticker = market_api.get_ticker(symbol)
        return jsonify(
            {
                'timestamp': datetime.now().isoformat(),
                'price': ticker.get('last') or ticker.get('close'),
                'volume': ticker.get('baseVolume'),
                'change': ticker.get('percentage'),
                'high': ticker.get('high'),
                'low': ticker.get('low'),
            }
        )
    except Exception:
        return jsonify(
            {
                'timestamp': datetime.now().isoformat(),
                'price': 0,
                'volume': 0,
                'change': 0,
                'high': 0,
                'low': 0,
            }
        )


@app.route('/api/signals')
def get_signals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 50"
    )
    signals = [serialize_row(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(signals)


@app.route('/api/trades')
def get_trades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 50"
    )
    trades = [serialize_row(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(trades)


@app.route('/api/symbols')
def get_symbols():
    symbols = fallback_symbols()
    enriched_symbols = []

    for symbol in symbols:
        try:
            ticker = market_api.get_ticker(symbol['symbol'])
            enriched_symbols.append(
                {
                    'symbol': symbol['symbol'],
                    'name': symbol.get('name', symbol['symbol']),
                    'price': ticker.get('last') or ticker.get('close'),
                    'change': ticker.get('percentage') or 0,
                    'timeframe': symbol.get('timeframe', CONFIG.get('timeframe', '1h')),
                }
            )
        except Exception:
            enriched_symbols.append({**symbol, 'price': 0, 'change': 0})

    return jsonify(enriched_symbols)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)