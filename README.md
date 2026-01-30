# cwrubacktest - CQ's In-House Backtesting Framework

A comprehensive, modular backtesting framework designed for quantitative trading strategy development and analysis. Built by CWRU Quants, this framework provides a robust foundation for strategy research, portfolio construction, and performance analysis.

## 🚀 Features

- **Modular Architecture**: Clean separation of concerns with pluggable components
- **Multiple Asset Classes**: Support for equities and other financial instruments
- **Flexible Data Handling**: CSV data sources with extensible data handler interface
- **Alpha Models**: Built-in signal generation models with custom model support
- **Portfolio Construction**: Advanced portfolio optimization and order sizing
- **Risk Management**: Configurable risk models and constraints
- **Performance Analytics**: Comprehensive statistics and tearsheet generation
- **Simulation Engine**: Event-driven simulation with realistic trading mechanics
- **Transaction Costs**: Customizable fee models and transaction cost analysis

## 📊 Core Components

### Alpha Models
- **FixedSignalsAlphaModel**: Static signal allocation
- **SingleSignalAlphaModel**: Single asset signal generation
- Custom alpha model interface for strategy development

### Portfolio Construction
- **Fixed Weight Optimizer**: Simple allocation strategies
- **Order Sizing**: Dollar-weighted and leveraged order sizing
- **Cash Buffer Management**: Configurable cash reserves

### Data Handling
- **CSV Data Sources**: Daily bar data from CSV files
- **Backtest Data Handler**: Unified data access layer
- Extensible for additional data sources

### Execution & Trading
- **Simulated Broker**: Realistic order execution simulation
- **Market Orders**: Basic execution algorithms
- **Rebalancing**: Configurable rebalancing frequencies

### Performance Analysis
- **Tearsheet Statistics**: Comprehensive performance reporting
- **Performance Metrics**: Sharpe ratio, CAGR, drawdown analysis
- **Benchmark Comparison**: Strategy vs benchmark analysis

## 🛠️ Installation

### Prerequisites
- Python 3.12 or higher
- pandas
- numpy
- pytz
- matplotlib (for plotting)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cwrubacktest
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .
   source bin/activate  # On Linux/Mac
   # or
   # Activate.ps1  # On Windows
   ```

3. **Install the package**:
   ```bash
   pip install -e .
   ```

## 🚀 Quick Start

### Basic Example

Here's a simple 60/40 equity/bond strategy compared to a buy-and-hold S&P 500 benchmark:

```python
import pandas as pd
import pytz
from cwrubacktest.alpha_models.fixed_signals import FixedSignalsAlphaModel
from cwrubacktest.asset.equity import Equity
from cwrubacktest.asset.universe.static import StaticUniverse
from cwrubacktest.data_handler.data_handler import BacktestDataHandler
from cwrubacktest.data_handler.csv_handler import CSVDailyBarDataSource
from cwrubacktest.statistics.tearsheet import TearsheetStatistics
from cwrubacktest.backtest.backtest import BacktestTradingSession
from cwrubacktest.trading_strats.rebalance import RebalancePeriod

# Define backtest parameters
start_dt = pd.Timestamp('2025-02-12 14:30:00', tz=pytz.UTC)
end_dt = pd.Timestamp('2025-03-13 23:59:00', tz=pytz.UTC)

# Set up universe and data
strategy_symbols = ['SPY', 'TLT']
strategy_assets = ['EQ:%s' % symbol for symbol in strategy_symbols]
strategy_universe = StaticUniverse(strategy_assets)

# Configure data source
csv_dir = "/path/to/your/data/"
data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=strategy_symbols)
data_handler = BacktestDataHandler(strategy_universe, data_sources=[data_source])

# Create strategy (60% SPY, 40% TLT)
strategy_alpha_model = FixedSignalsAlphaModel({'EQ:SPY': 0.6, 'EQ:TLT': 0.4})
strategy_backtest = BacktestTradingSession(
    start_dt,
    end_dt,
    strategy_universe,
    strategy_alpha_model,
    rebalance_pd=RebalancePeriod.DAILY,
    long_only=True,
    cash_buffer_percentage=0.01,
    data_handler=data_handler
)

# Run the backtest
strategy_backtest.run()

# Create benchmark (100% SPY)
benchmark_assets = ['EQ:SPY']
benchmark_universe = StaticUniverse(benchmark_assets)
benchmark_alpha_model = FixedSignalsAlphaModel({'EQ:SPY': 1.0})
benchmark_backtest = BacktestTradingSession(
    start_dt,
    end_dt,
    benchmark_universe,
    benchmark_alpha_model,
    rebalance_pd=RebalancePeriod.NEVER,
    long_only=True,
    cash_buffer_percentage=0.01,
    data_handler=data_handler
)
benchmark_backtest.run()

# Generate performance tearsheet
tearsheet = TearsheetStatistics(
    strategy_equity=strategy_backtest.get_equity_curve(),
    benchmark_equity=benchmark_backtest.get_equity_curve(),
    title='60/40 US Equities/Bonds vs. Buy and Hold S&P 500'
)
tearsheet.plot_results()
```

### Data Format

The framework expects CSV files with the following format:

```csv
Date,Open,High,Low,Close,Adj Close,Volume
03/13/2025,558.49,559.11,549.68,551.42,551.42,74079406
03/12/2025,562.17,563.11,553.69,558.87,558.87,69588172
```

## 📖 Usage Guide

### 1. Setting Up Your Universe

```python
from cwrubacktest.asset.universe.static import StaticUniverse

# Define your assets
assets = ['EQ:SPY', 'EQ:QQQ', 'EQ:TLT']
universe = StaticUniverse(assets)
```

### 2. Creating Alpha Models

**Fixed Signals**:
```python
from cwrubacktest.alpha_models.fixed_signals import FixedSignalsAlphaModel

alpha_model = FixedSignalsAlphaModel({
    'EQ:SPY': 0.5,
    'EQ:TLT': 0.3,
    'EQ:QQQ': 0.2
})
```

**Custom Alpha Model**:
```python
from cwrubacktest.alpha_models.alpha_model import AlphaModel

class MyAlphaModel(AlphaModel):
    def __call__(self, dt):
        # Your custom signal logic here
        return {'EQ:SPY': signal_value}
```

### 3. Configuring Rebalancing

```python
from cwrubacktest.trading_strats.rebalance import RebalancePeriod

# Available periods
RebalancePeriod.DAILY
RebalancePeriod.WEEKLY
RebalancePeriod.MONTHLY
RebalancePeriod.NEVER
```

### 4. Running Analysis

The framework provides comprehensive performance metrics:

- **CAGR**: Compound Annual Growth Rate
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Volatility**: Standard deviation of returns
- **Beta**: Market sensitivity (vs benchmark)

## 🏗️ Architecture

```
cwrubacktest/
├── alpha_models/     # Signal generation models
├── asset/           # Asset definitions and universe management
├── backtest/        # Main backtesting orchestration
├── broker/          # Trade execution and portfolio management
├── data_handler/    # Data source interfaces and implementations
├── exchange/        # Market simulation
├── execution/       # Order execution algorithms
├── portbuild/       # Portfolio construction and optimization
├── sim/             # Simulation engine and event management
├── statistics/      # Performance analysis and reporting
├── trading_strats/  # Trading strategy implementations
└── utils/           # Utility functions and settings
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔬 Research & Development

This framework is actively used by CWRU Quants for:
- **Strategy Research**: Testing new quantitative trading ideas
- **Risk Analysis**: Understanding portfolio risk characteristics
- **Performance Attribution**: Analyzing sources of returns
- **Academic Research**: Supporting quantitative finance coursework

## 📞 Support

- **Documentation**: In-code documentation and examples
- **Issues**: GitHub Issues for bug reports and feature requests
- **Community**: CWRU Quants team collaboration

## 🎯 Roadmap

- [ ] Additional asset classes (options, futures, FX)
- [ ] Real-time data integration
- [ ] Advanced risk models
- [ ] Machine learning alpha models
- [ ] Enhanced visualization tools
- [ ] Portfolio optimization algorithms

---

**Built with ❤️ by CWRU Quants**