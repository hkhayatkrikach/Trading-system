// Aplicación Principal Profesional
class ProfessionalTradingSystem {
    constructor() {
        this.data = {
            portfolio: null,
            market: {},
            symbols: [],
            realTime: null
        };
        this.charts = new Map();
        this.init();
    }

    async init() {
        await this.loadInitialData();
        this.setupUI();
        this.startRealTimeUpdates();
        this.setupEventListeners();
    }

    async loadInitialData() {
        try {
            // Cargar datos del portfolio
            const portfolioResponse = await fetch('/api/portfolio-data');
            this.data.portfolio = await portfolioResponse.json();
            
            // Cargar símbolos
            const symbolsResponse = await fetch('/api/symbols');
            this.data.symbols = await symbolsResponse.json();
            
            // Cargar datos de mercado para cada símbolo
            for (const symbol of this.data.symbols) {
                const marketResponse = await fetch(`/api/market-data/${symbol.symbol}`);
                this.data.market[symbol.symbol] = await marketResponse.json();
            }
            
            this.updateUI();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    setupUI() {
        this.updatePortfolioDisplay();
        this.updateMarketDisplay();
        this.updateTradesDisplay();
        this.updatePositionsDisplay();
    }

    updatePortfolioDisplay() {
        if (!this.data.portfolio) return;

        // Actualizar balance
        const balanceElements = document.querySelectorAll('.balance-amount');
        balanceElements.forEach(element => {
            element.textContent = `$${this.data.portfolio.balance?.toFixed(2) || '10,000.00'}`;
        });

        // Actualizar estadísticas
        const stats = [
            { selector: '.stat-value.balance', value: `$${this.data.portfolio.balance?.toFixed(2) || '10,000.00'}` },
            { selector: '.stat-value.pnl', value: `$${this.data.portfolio.daily_pnl?.toFixed(2) || '0.00'}` },
            { selector: '.stat-value.win-rate', value: `${this.data.portfolio.win_rate || 0}%` }
        ];

        stats.forEach(stat => {
            const elements = document.querySelectorAll(stat.selector);
            elements.forEach(element => {
                element.textContent = stat.value;
            });
        });
    }

    updateMarketDisplay() {
        if (!this.data.symbols) return;

        const marketContainer = document.querySelector('.market-tickers');
        if (!marketContainer) return;

        marketContainer.innerHTML = '';
        
        this.data.symbols.slice(0, 5).forEach(symbol => {
            const tickerElement = document.createElement('div');
            tickerElement.className = 'ticker-item';
            tickerElement.innerHTML = `
                <div class="ticker-symbol">${symbol.symbol}</div>
                <div class="ticker-name">${symbol.name}</div>
                <div class="ticker-price">$${symbol.price?.toFixed(2) || '0.00'}</div>
                <div class="ticker-change ${symbol.change >= 0 ? 'positive' : 'negative'}">
                    ${symbol.change >= 0 ? '+' : ''}${symbol.change?.toFixed(2) || '0.00'}%
                </div>
            `;
            marketContainer.appendChild(tickerElement);
        });
    }

    updateTradesDisplay() {
        if (!this.data.portfolio?.trades) return;

        const tradesContainer = document.querySelector('.trades-list');
        if (!tradesContainer) return;

        tradesContainer.innerHTML = '';
        
        this.data.portfolio.trades.forEach(trade => {
            const tradeElement = document.createElement('div');
            tradeElement.className = 'trade-item';
            tradeElement.innerHTML = `
                <div class="trade-symbol">${trade.symbol}</div>
                <div class="trade-type ${trade.type.toLowerCase()}">${trade.type}</div>
                <div class="trade-time">${trade.time}</div>
                <div class="trade-pnl ${trade.pnl >= 0 ? 'positive' : 'negative'}">
                    ${trade.pnl >= 0 ? '+' : ''}$${trade.pnl?.toFixed(2) || '0.00'}
                </div>
            `;
            tradesContainer.appendChild(tradeElement);
        });
    }

    updatePositionsDisplay() {
        if (!this.data.portfolio?.positions) return;

        const positionsContainer = document.querySelector('.positions-list');
        if (!positionsContainer) return;

        positionsContainer.innerHTML = '';
        
        this.data.portfolio.positions.forEach(position => {
            const positionElement = document.createElement('div');
            positionElement.className = 'position-item';
            positionElement.innerHTML = `
                <div class="position-symbol">${position.symbol}</div>
                <div class="position-type ${position.type.toLowerCase()}">${position.type}</div>
                <div class="position-size">${position.size?.toFixed(4) || '0.0000'}</div>
                <div class="position-pnl ${position.pnl >= 0 ? 'positive' : 'negative'}">
                    ${position.pnl >= 0 ? '+' : ''}$${position.pnl?.toFixed(2) || '0.00'}
                </div>
            `;
            positionsContainer.appendChild(positionElement);
        });
    }

    setupEventListeners() {
        // Navegación
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remover active de todos
                document.querySelectorAll('.nav-item').forEach(nav => {
                    nav.classList.remove('active');
                });
                
                // Agregar active al actual
                item.classList.add('active');
                
                // Navegar
                const href = item.getAttribute('href');
                window.location.href = href;
            });
        });

        // Botones de acción
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                const href = button.getAttribute('href');
                if (href) {
                    window.location.href = href;
                }
            });
        });

        // Efectos de hover
        document.querySelectorAll('.hover-glow').forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.style.transform = 'translateY(-2px)';
                element.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.3)';
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transform = 'translateY(0)';
                element.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.16)';
            });
        });
    }

    startRealTimeUpdates() {
        // Actualizar datos cada 30 segundos
        setInterval(async () => {
            await this.loadInitialData();
        }, 30000);

        // Actualizar datos en tiempo real cada 5 segundos
        setInterval(async () => {
            try {
                const response = await fetch('/api/real-time-data');
                this.data.realTime = await response.json();
                this.updateRealTimeData();
            } catch (error) {
                console.error('Error updating real-time ', error);
            }
        }, 5000);
    }

    updateRealTimeData() {
        if (!this.data.realTime) return;

        // Actualizar precio en tiempo real
        const priceElements = document.querySelectorAll('.real-time-price');
        priceElements.forEach(element => {
            element.textContent = `$${this.data.realTime.price?.toFixed(2) || '0.00'}`;
        });

        // Actualizar cambio en tiempo real
        const changeElements = document.querySelectorAll('.real-time-change');
        changeElements.forEach(element => {
            const change = this.data.realTime.change || 0;
            element.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            element.className = `real-time-change ${change >= 0 ? 'positive' : 'negative'}`;
        });
    }

    // Mostrar notificación
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animación de entrada
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Remover después de 3 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Actualizar gráfico
    updateChart(symbol, newData) {
        if (this.charts.has(symbol)) {
            const chart = this.charts.get(symbol);
            // Actualizar gráfico con nuevos datos
            // (Implementación específica según la biblioteca de gráficos)
        }
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.tradingSystem = new ProfessionalTradingSystem();
});