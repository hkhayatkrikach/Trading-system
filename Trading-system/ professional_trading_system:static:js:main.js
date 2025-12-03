class ProfessionalTradingSystem {
    constructor() {
        this.data = {
            portfolio: null,
            symbols: [],
            signals: [],
            trades: [],
            market: {},
            realTime: null,
        };

        this.selectedSymbol = null;
        this.selectedTimeframe = '1h';
        this.chartId = 'main-chart';
        this.chartInstance = null;

        this.init();
    }

    async init() {
        await this.loadInitialData();
        this.setupEventListeners();
        await this.refreshRealTime();
        this.startRealTimeUpdates();
    }

    /* ----------------------- Data loading ----------------------- */
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadPortfolio(),
                this.loadSymbols(),
                this.loadSignals(),
                this.loadTrades(),
            ]);

            if (!this.selectedSymbol && this.data.symbols.length) {
                this.selectedSymbol = this.data.symbols[0].symbol;
                this.selectedTimeframe = this.data.symbols[0].timeframe || '1h';
            }

            await this.loadMarketData();
            this.updateUI();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.notify('No se pudieron cargar los datos iniciales.', 'error');
        }
    }

    async loadPortfolio() {
        const response = await fetch('/api/portfolio-data');
        this.data.portfolio = await response.json();
    }

    async loadSymbols() {
        const response = await fetch('/api/symbols');
        this.data.symbols = await response.json();
    }

    async loadSignals() {
        const response = await fetch('/api/signals');
        this.data.signals = await response.json();
    }

    async loadTrades() {
        const response = await fetch('/api/trades');
        this.data.trades = await response.json();
    }

    async loadMarketData(symbol = this.selectedSymbol, timeframe = this.selectedTimeframe) {
        if (!symbol) return;
        const marketResponse = await fetch(`/api/market-data/${encodeURIComponent(symbol)}?timeframe=${timeframe}`);
        const candles = await marketResponse.json();
        this.data.market[symbol] = candles;
    }

    /* ----------------------- UI updates ----------------------- */
    updateUI() {
        this.renderHeader();
        this.renderSymbols();
        this.renderMarketTicker();
        this.renderPortfolioStats();
        this.renderSignals();
        this.renderTrades();
        this.renderPositions();
        this.renderChart();
    }

    renderHeader() {
        const balanceEls = document.querySelectorAll('.balance-amount');
        const balance = this.data.portfolio?.balance ?? 0;
        balanceEls.forEach(el => (el.textContent = `$${balance.toFixed(2)}`));

        const pnlEl = document.querySelector('.pnl-value');
        if (pnlEl) pnlEl.textContent = `$${(this.data.portfolio?.daily_pnl ?? 0).toFixed(2)}`;

        const winRateEl = document.querySelector('.win-rate');
        if (winRateEl) winRateEl.textContent = `${this.data.portfolio?.win_rate ?? 0}%`;

        document.querySelector('.selected-symbol')?.textContent = this.selectedSymbol || '—';
        document.querySelector('.selected-timeframe')?.textContent = this.selectedTimeframe;
    }

    renderSymbols() {
        const container = document.querySelector('.symbol-selector');
        if (!container) return;
        container.innerHTML = '';

        this.data.symbols.forEach(({ symbol }) => {
            const btn = document.createElement('button');
            btn.className = `symbol-button ${symbol === this.selectedSymbol ? 'active' : ''}`;
            btn.dataset.symbol = symbol;
            btn.textContent = symbol;
            btn.onclick = async () => {
                this.selectedSymbol = symbol;
                await this.loadMarketData(symbol, this.selectedTimeframe);
                this.updateUI();
            };
            container.appendChild(btn);
        });
    }

    renderMarketTicker() {
        const feed = document.querySelector('.ticker-feed');
        if (!feed) return;
        feed.innerHTML = '';

        this.data.symbols.forEach((s) => {
            const row = document.createElement('div');
            const change = s.change ?? 0;
            row.className = 'ticker-row';
            row.innerHTML = `
                <strong>${s.symbol}</strong>
                <span>${s.price ? `$${s.price.toFixed(2)}` : '—'}</span>
                <span>${s.timeframe || ''}</span>
                <span class="change ${change >= 0 ? 'positive' : 'negative'}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span>
            `;
            row.addEventListener('click', async () => {
                this.selectedSymbol = s.symbol;
                await this.loadMarketData(s.symbol, this.selectedTimeframe);
                this.updateUI();
            });
            feed.appendChild(row);
        });

        this.updateTradeStats();
    }

    updateTradeStats() {
        const totals = {
            total: this.data.portfolio?.total_trades ?? 0,
            long: this.data.portfolio?.long_trades ?? 0,
            short: this.data.portfolio?.short_trades ?? 0,
        };
        document.querySelector('.total-trades')?.textContent = totals.total;
        document.querySelector('.long-trades')?.textContent = totals.long;
        document.querySelector('.short-trades')?.textContent = totals.short;
    }

    renderPortfolioStats() {
        const pnlPercent = this.data.portfolio?.daily_pnl ?? 0;
        const pnlPill = document.querySelector('.pnl');
        if (pnlPill) {
            pnlPill.textContent = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`;
            pnlPill.classList.toggle('positive', pnlPercent >= 0);
            pnlPill.classList.toggle('negative', pnlPercent < 0);
        }
    }

    renderSignals() {
        const container = document.querySelector('.signals-list');
        if (!container) return;
        container.innerHTML = '';

        if (!this.data.signals.length) {
            container.textContent = 'No hay señales disponibles.';
            container.classList.add('empty-state');
            return;
        }
        container.classList.remove('empty-state');

        this.data.signals.slice(0, 10).forEach(signal => {
            const item = document.createElement('div');
            const type = (signal.signal_type || '').toLowerCase();
            item.className = 'list-item';
            item.innerHTML = `
                <div>
                    <strong>${signal.symbol}</strong>
                    <div class="meta">${signal.timestamp}</div>
                </div>
                <div>
                    <span class="badge ${type}">${signal.signal_type}</span>
                    <div class="meta">${signal.timeframe || ''}</div>
                </div>
                <div>
                    <div class="meta">Entrada: $${(signal.entry_price ?? 0).toFixed(2)}</div>
                    <div class="meta">SL: $${(signal.stop_loss ?? 0).toFixed(2)} · TP: $${(signal.take_profit ?? 0).toFixed(2)}</div>
                </div>
                <div class="ticker-timeframe">${symbol.timeframe || ''}</div>
            `;
            container.appendChild(item);
        });
    }

    renderTrades() {
        const container = document.querySelector('.trades-list');
        if (!container) return;
        container.innerHTML = '';

        if (!this.data.trades.length) {
            container.textContent = 'Aún no hay trades ejecutados.';
            container.classList.add('empty-state');
            return;
        }
        container.classList.remove('empty-state');

        this.data.trades.slice(0, 10).forEach(trade => {
            const pnl = trade.pnl ?? trade.profit_potential ?? 0;
            const type = (trade.signal_type || trade.type || '').toLowerCase();
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div>
                    <strong>${trade.symbol}</strong>
                    <div class="meta">${trade.timestamp}</div>
                </div>
                <div>
                    <span class="badge ${type}">${trade.signal_type || trade.type}</span>
                    <div class="meta">${trade.timeframe || ''}</div>
                </div>
                <div>
                    <div class="meta">Size: ${(trade.position_size ?? 0).toFixed(4)}</div>
                    <div class="meta ${pnl >= 0 ? 'positive' : 'negative'}">PnL: ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}</div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    renderPositions() {
        const container = document.querySelector('.positions-list');
        if (!container) return;
        container.innerHTML = '';

        const positions = this.data.portfolio?.positions || [];
        if (!positions.length) {
            container.textContent = 'Sin posiciones abiertas.';
            container.classList.add('empty-state');
            return;
        }
        container.classList.remove('empty-state');

        positions.forEach(pos => {
            const type = (pos.type || '').toLowerCase();
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div>
                    <strong>${pos.symbol}</strong>
                    <div class="meta">${pos.opened_at || ''}</div>
                </div>
                <div>
                    <span class="badge ${type}">${pos.type}</span>
                    <div class="meta">${pos.timeframe || ''}</div>
                </div>
                <div>
                    <div class="meta">Size: ${(pos.size ?? 0).toFixed(4)}</div>
                    <div class="meta ${pos.pnl >= 0 ? 'positive' : 'negative'}">PnL: ${pos.pnl >= 0 ? '+' : ''}$${(pos.pnl ?? 0).toFixed(2)}</div>
                </div>
                <div class="position-timeframe">${position.timeframe || ''}</div>
            `;
            container.appendChild(item);
        });
    }

    renderChart() {
        const data = this.data.market[this.selectedSymbol] || [];
        if (!data.length) return;

        const trace = [{
            x: data.map(d => d.time),
            open: data.map(d => d.open),
            high: data.map(d => d.high),
            low: data.map(d => d.low),
            close: data.map(d => d.close),
            type: 'candlestick',
            increasing: { line: { color: '#4ade80' } },
            decreasing: { line: { color: '#f87171' } },
        }];

        const layout = {
            margin: { l: 40, r: 10, t: 10, b: 30 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: { color: '#a5abb6' },
            yaxis: { color: '#a5abb6', side: 'right' },
            font: { color: '#f5f7fb' },
            dragmode: 'pan',
        };

        Plotly.newPlot(this.chartId, trace, layout, { displayModeBar: false, responsive: true });
        const last = data[data.length - 1];
        document.querySelector('.live-price')?.textContent = `$${(last.close ?? 0).toFixed(2)}`;
        const changeEl = document.querySelector('.live-change');
        if (changeEl) {
            const change = ((last.close - data[0].open) / data[0].open) * 100;
            changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeEl.classList.toggle('positive', change >= 0);
            changeEl.classList.toggle('negative', change < 0);
        }
    }

    /* ----------------------- Real-time updates ----------------------- */
    startRealTimeUpdates() {
        setInterval(async () => {
            await this.refreshTicker();
        }, 15000);

        setInterval(async () => {
            await this.refreshRealTime();
        }, 5000);
    }

    async refreshTicker() {
        await this.loadSymbols();
        this.renderMarketTicker();
    }

    async refreshRealTime() {
        try {
            const response = await fetch('/api/real-time-data');
            this.data.realTime = await response.json();
            this.updateRealTimeUI();
        } catch (error) {
            console.error('Error in realtime update', error);
        }
    }

    updateRealTimeUI() {
        if (!this.data.realTime) return;
        const { price, change } = this.data.realTime;
        document.querySelector('.live-price')?.textContent = `$${(price ?? 0).toFixed(2)}`;
        const changeEl = document.querySelector('.live-change');
        if (changeEl) {
            changeEl.textContent = `${change >= 0 ? '+' : ''}${(change ?? 0).toFixed(2)}%`;
            changeEl.classList.toggle('positive', change >= 0);
            changeEl.classList.toggle('negative', change < 0);
        }
    }

    /* ----------------------- Event listeners ----------------------- */
    setupEventListeners() {
        document.querySelectorAll('.timeframe-chip').forEach(btn => {
            btn.addEventListener('click', async () => {
                document.querySelectorAll('.timeframe-chip').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedTimeframe = btn.dataset.timeframe;
                await this.loadMarketData(this.selectedSymbol, this.selectedTimeframe);
                this.renderChart();
            });
        });

        document.querySelectorAll('[data-action="refresh-all"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                await this.loadInitialData();
                this.notify('Panel sincronizado');
            });
        });

        document.querySelectorAll('[data-action="refresh-market"], [data-action="refresh-chart"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                await this.loadMarketData();
                this.renderChart();
                this.notify('Mercado actualizado');
            });
        });

        document.querySelectorAll('[data-action="refresh-signals"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                await this.loadSignals();
                this.renderSignals();
                this.notify('Señales sincronizadas');
            });
        });

        document.querySelectorAll('[data-action="refresh-portfolio"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                await this.loadPortfolio();
                this.renderHeader();
                this.renderPositions();
                this.updateTradeStats();
                this.notify('Portafolio actualizado');
            });
        });

        document.querySelectorAll('[data-action="refresh-trades"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                await this.loadTrades();
                this.renderTrades();
                this.notify('Historial refrescado');
            });
        });

        document.querySelectorAll('[data-action="refresh-ticker"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                await this.refreshTicker();
                this.notify('Ticker sincronizado');
            });
        });

        document.querySelectorAll('[data-action="open-terminal"]').forEach(btn => {
            btn.addEventListener('click', () => window.location.href = '/terminal');
        });
    }

    /* ----------------------- Helpers ----------------------- */
    notify(message, type = 'info') {
        const bar = document.querySelector('.notification-bar');
        if (!bar) return;
        bar.textContent = message;
        bar.classList.remove('hidden');
        bar.classList.add('visible');
        bar.className = `notification-bar visible ${type}`;
        setTimeout(() => bar.classList.remove('visible'), 2500);
    }
}

new ProfessionalTradingSystem();
