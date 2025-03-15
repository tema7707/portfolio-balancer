# Portfolio Rebalancer

[📽️ Demo 📽️](https://www.loom.com/share/233cd4b529da44cfa6241e0c150bea51?sid=26bd43ce-f576-4db9-b8f8-8bd93aa14b3e) 

[Market-Fetcher Agent](https://app.near.ai/agents/temazzz.near/market-fetcher/latest) 

[Portfolio-Manager Agent](https://app.near.ai/agents/temazzz.near/portfolio-manager/latest)

## Overview
Portfolio Rebalancer is an AI-driven system designed to help cryptocurrency investors manage and optimize their portfolios. The system consists of two AI agents: `market-fetcher` and `portfolio-manager`, as well as an automated trading script, `auto-trader.py`. Together, they provide real-time market analysis, trading strategy recommendations, and automated portfolio rebalancing.

## System Architecture

The system is built with a modular architecture consisting of three main components:

1. **Market-Fetcher Agent**: Provides real-time market data and analysis
2. **Portfolio-Manager Agent**: Analyzes portfolio and recommends trades
3. **Auto-Trader Script**: Automates the execution of recommended trades

These components work together to create a complete portfolio management solution:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Market-Fetcher │    │ Portfolio-Manager│    │   Auto-Trader   │
│      Agent      │───▶│      Agent       │───▶│     Script      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Market Data   │    │Portfolio Analysis│    │  Trade Execution│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Features

### Market-Fetcher Agent
The `market-fetcher` agent fetches and analyzes real-time cryptocurrency market data. It provides comprehensive insights into token prices, market capitalization, trading volume, order book details, and more to help you make informed investment decisions.

#### Technical Implementation:
The agent is built on the NEAR AI platform using a Llama v3p1 70B model and implements several specialized functions:

- `get_top_coins()`: Retrieves top cryptocurrencies by market cap
- `search_token()`: Searches for specific tokens and their market data
- `get_order_book()`: Analyzes order book depth for specific tokens
- `get_historical_data()`: Retrieves historical price data with various timeframes
- `fetch_comprehensive_data()`: Combines multiple data sources for in-depth analysis
- `analyze_market_sentiment()`: Evaluates market sentiment for specific tokens

The agent uses the CoinGecko API to fetch real-time market data and performs custom analysis to provide actionable insights.

#### Capabilities:
- Real-time price tracking for any cryptocurrency
- Market capitalization analysis
- Trading volume monitoring
- Order book depth analysis
- Price change tracking (24h, 7d)
- Token information and use cases
- Comparative analysis between tokens

#### Example Query & Response:
**User:**
```
Yo! I have $100 and want to know some info about IMX and SOL. I want to decide in which token to invest my money.
```

**Market-Fetcher Response:**
```
Hello!
You're interested in investing $100 in either IMX or SOL. I'll give you an overview of both tokens, including their current market data, trading information, and order book details.

IMX (Immutable)
- Current price: $0.5551
- Market capitalization: $981,881,127
- 24-hour trading volume: $28,415,577
- 24-hour price change: +7.40%
- 7-day price change: -6.96%

IMX is the native token of the Immutable X platform, a decentralized, community-driven marketplace for NFTs. The token is used for governance, staking, and as a medium of exchange within the platform.

SOL (Solana)
- Current price: $135.27
- Market capitalization: $44,649,193,819
- 24-hour trading volume: $1,489,703,528
- 24-hour price change: +0.00%
- 7-day price change: +13.51%

SOL is the native token of the Solana blockchain, a fast, decentralized, and scalable platform for building blockchain applications. The token is used for governance, staking, and as a medium of exchange within the platform.

Order Book Details:
For IMX:
- Best bid: $0.55
- Best ask: $0.56
- Spread: 0.01 (1.82%)
- Total bid value: $68,251.80
- Total ask value: $31,169.00

For SOL:
- Best bid: $135.27
- Best ask: $135.28
- Spread: 0.01 (0.01%)
- Total bid value: $1,475,961.90
- Total ask value: $735,937.20

Additional Information:
Both IMX and SOL have a relatively high market capitalization, indicating an established presence in the cryptocurrency market. However, SOL has a significantly higher market capitalization and 24-hour trading volume, indicating more liquidity and trading activity.

IMX has a higher 24-hour price change, indicating more volatility in its price. However, SOL has a higher 7-day price change, indicating a stronger upward trend in its price.

Please keep in mind that this information is subject to change and might not reflect the current market situation. Always do your own research and consider multiple sources before making any investment decisions.
```

You can try it here: [Market-Fetcher Agent](https://app.near.ai/agents/temazzz.near/market-fetcher/latest)

### Portfolio-Manager Agent
The `portfolio-manager` agent connects to an OKX account to analyze portfolio allocations, fetch real-time market data, and suggest optimal trading strategies based on user prompts. It leverages the market-fetcher agent to gather market intelligence and combines it with your portfolio data to provide personalized recommendations.

#### Technical Implementation:
The agent is built on the NEAR AI platform using a Llama v3p1 70B model and implements several specialized functions:

- `get_okx_signature()`: Generates authentication signatures for OKX API
- `get_account_balance()`: Retrieves current portfolio holdings from OKX
- `get_account_balance_in_usd()`: Converts all holdings to USD value
- `call_market_fetcher()`: Integrates with the market-fetcher agent for market data
- `analyze_portfolio()`: Performs comprehensive portfolio analysis
- `generate_trade_recommendation()`: Creates actionable trade recommendations

The agent uses secure API authentication with HMAC-SHA256 signatures to interact with the OKX exchange API and implements error handling for API rate limits and connection issues.

#### Capabilities:
- Portfolio analysis and allocation review
- Market trend identification
- Risk assessment
- Trading strategy development
- Rebalancing recommendations
- Automated trade suggestions

#### Setup:
To use the `portfolio-manager` agent, you must configure your system environment variables with OKX API credentials:
```
export OKX_API_KEY=your_api_key
export OKX_API_SECRET=your_api_secret
export OKX_API_PASSPHRASE=your_api_passphrase
```

#### Example Queries:
1. **User:** "Rebalance my portfolio, I want to invest in AI tokens."
2. **User:** "I want to invest in a coin with potential x100."

**Response Example:**
```
{
  "action": "BUY",
  "coin": "NEAR",
  "amount_usd": 10000.0
}
```

You can try it here: [Portfolio-Manager Agent](https://app.near.ai/agents/temazzz.near/portfolio-manager/latest)

### Auto-Trader Script
The `auto-trader.py` script automates the portfolio rebalancing process by executing the `portfolio-manager` agent at regular intervals. This allows for hands-free, continuous portfolio optimization according to the user's investment strategy.

#### Technical Implementation:
The script is implemented in Python and consists of three main classes:

1. **OKXClient**: Handles all OKX API interactions with secure authentication
   - Implements signature generation with HMAC-SHA256
   - Provides methods for account balance retrieval and order placement
   - Handles API rate limiting and error recovery

2. **PortfolioExecutor**: Manages the interaction with the portfolio-manager agent
   - Sends queries to the agent and parses responses
   - Validates trade recommendations
   - Prepares orders for execution

3. **AutoTrader**: Orchestrates the entire automated trading process
   - Runs on a configurable interval
   - Handles graceful shutdown with signal handlers
   - Implements logging and error handling
   - Provides simulation mode for testing without actual trades

#### How It Works:
- The script runs at a specified interval (N minutes).
- It calls the `portfolio-manager` agent to analyze and rebalance the portfolio.
- If a trade is recommended, it executes the trade on OKX.
- It maintains a log of all trades and portfolio changes.
- It implements error handling and retry mechanisms for API failures.

#### Features:
- Scheduled portfolio analysis
- Automated trade execution
- Strategy persistence
- Risk management controls
- Performance tracking
- Simulation mode for testing

## Tools and Technologies

### Market-Fetcher Tools:
- Real-time cryptocurrency API integration (CoinGecko)
- Technical analysis algorithms
- Order book analysis
- Market sentiment analysis
- Historical data comparison
- NEAR AI platform with Llama v3p1 70B model

### Portfolio-Manager Tools:
- OKX API integration with HMAC-SHA256 authentication
- Portfolio optimization algorithms
- Risk assessment models
- Market trend analysis
- Trading strategy formulation
- NEAR AI platform with Llama v3p1 70B model

## Installation & Usage
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/portfolio-rebalancer.git
   cd portfolio-rebalancer
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up your environment variables for OKX API:
   ```sh
   export OKX_API_KEY=your_api_key
   export OKX_API_SECRET=your_api_secret
   export OKX_API_PASSPHRASE=your_api_passphrase
   ```
4. Run the auto-trader script:
   ```sh
   python auto-trader.py --query "Rebalance my portfolio with focus on AI tokens" --interval 60 --simulate
   ```

## Configuration
You can customize the auto-trader behavior by modifying the command-line arguments:
- `--query`: The strategy prompt to send to the portfolio-manager agent
- `--interval`: Time between portfolio checks (in minutes)
- `--simulate`: Run in simulation mode without executing actual trades
- `--agent-path`: Custom path to the portfolio-manager agent

Additional configuration options can be set in the script:
- `MAX_TRADE_SIZE`: Maximum size of any single trade (in USD)
- `RISK_TOLERANCE`: Level of risk tolerance (low, medium, high)
- `STRATEGY`: Investment strategy to follow (growth, income, balanced)

## Security Considerations
- API keys are stored as environment variables for security
- The system never exposes your private keys
- All API communications use encrypted connections with HMAC-SHA256 signatures
- Trading limits can be set to prevent excessive losses
- Simulation mode allows testing without financial risk

## Notes
- Always perform due diligence before executing trades.
- Ensure API keys are securely stored and never shared.
- The market conditions can change rapidly, and AI-based recommendations should be used with caution.
- This tool is designed to assist with investment decisions, not to replace human judgment.

## License
This project is licensed under the MIT License.

## Disclaimer
Cryptocurrency investments are subject to market risks. Past performance is not indicative of future results. This software is provided for educational and informational purposes only and is not financial advice.

