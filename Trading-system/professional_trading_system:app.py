from flask import Flask, render_template, jsonify
import random
from datetime import datetime, timedelta
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/terminal')
def terminal():
    return render_template('terminal.html')

@app.route('/api/market-data/<symbol>')
def get_market_data(symbol):
    data = []
    base_price = 45000 if 'BTC' in symbol else (3200 if 'ETH' in symbol else 150)
    
    for i in range(100):
        time_point = datetime.now() - timedelta(minutes=i*5)
        price_change = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + price_change)
        
        data.append({
            'time': time_point.isoformat(),
            'open': current_price - random.uniform(0, 50),
            'high': current_price + random.uniform(0, 100),
            'low': current_price - random.uniform(0, 100),
            'close': current_price,
            'volume': random.uniform(1000, 5000)
        })
        base_price = current_price
    
    return jsonify(data)

@app.route('/api/portfolio-data')
def get_portfolio_data():
    return jsonify({
        'balance': 12345.67,
        'daily_pnl': 234.56,
        'win_rate': 68,
        'total_trades': 42,
        'balance_history': [
            {'timestamp': (datetime.now() - timedelta(days=i)).isoformat(), 'balance': 10000 + i*100}
            for i in range(30)
        ],
        'positions': [
            {'symbol': 'BTC/USDT', 'type': 'LONG', 'size': 0.123, 'pnl': 45.60, 'entry': 45000},
            {'symbol': 'ETH/USDT', 'type': 'SHORT', 'size': 0.456, 'pnl': -12.30, 'entry': 3200}
        ],
        'trades': [
            {'symbol': 'BTC/USDT', 'type': 'LONG', 'pnl': 120.50, 'time': '10:30'},
            {'symbol': 'ETH/USDT', 'type': 'SHORT', 'pnl': -45.20, 'time': '11:15'},
            {'symbol': 'SOL/USDT', 'type': 'LONG', 'pnl': 23.40, 'time': '12:00'}
        ]
    })

@app.route('/api/real-time-data')
def get_real_time_data():
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'price': 45000 + random.uniform(-100, 100),
        'volume': random.uniform(1000, 5000),
        'change': random.uniform(-2, 2),
        'high': 45100,
        'low': 44900
    })

@app.route('/api/symbols')
def get_symbols():
    return jsonify([
        {'symbol': 'BTC/USDT', 'name': 'Bitcoin', 'price': 45230.45, 'change': 1.2},
        {'symbol': 'ETH/USDT', 'name': 'Ethereum', 'price': 3210.78, 'change': 0.8},
        {'symbol': 'SOL/USDT', 'name': 'Solana', 'price': 152.34, 'change': -0.3},
        {'symbol': 'AAPL', 'name': 'Apple', 'price': 178.23, 'change': 0.5},
        {'symbol': 'GOOGL', 'name': 'Google', 'price': 145.67, 'change': -0.2}
    ])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)