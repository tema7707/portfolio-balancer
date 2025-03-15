# Market Fetcher Agent

## Overview
The Market Fetcher is an AI-powered agent designed to retrieve and analyze real-time cryptocurrency market data. It provides comprehensive insights into token prices, market trends, order book details, and trading volumes to help investors make informed decisions. This agent serves as the market intelligence component of the Portfolio Rebalancer system.

## Features
- **Real-time Price Data**: Up-to-date pricing information for thousands of cryptocurrencies
- **Market Capitalization Analysis**: Insights into token market size and relative positioning
- **Trading Volume Monitoring**: Analysis of liquidity and trading activity
- **Order Book Analysis**: Depth charts and buy/sell pressure visualization
- **Price Change Tracking**: Short and long-term price movement analysis (24h, 7d)
- **Token Information**: Background on token use cases, technology, and ecosystem
- **Comparative Analysis**: Side-by-side comparison of multiple tokens

## Technical Implementation
The agent is built on the NEAR AI platform using a Llama v3p1 70B model and implements several specialized functions:

- `get_top_coins()`: Retrieves top cryptocurrencies by market cap
- `get_top_tokens_formatted()`: Returns formatted tables of top tokens
- `search_token()`: Searches for specific tokens and their market data
- `get_token_price()`: Fetches current price for a specific token
- `get_order_book()`: Analyzes order book depth for specific tokens
- `get_historical_data()`: Retrieves historical price data with various timeframes
- `analyze_market_sentiment()`: Evaluates market sentiment for specific tokens

The agent uses the CoinGecko API to fetch real-time market data and performs custom analysis to provide actionable insights.

## Prerequisites
- Internet connection for API access
- No API keys required (uses public endpoints)

## Setup
To run the agent locally:

```sh
nearai agent interactive ./market-fetcher/0.0.1 --local
```

## Usage Examples

### Example 1: Token Comparison
**User Query**:
```
I have $100 and want to know some info about IMX and SOL. I want to decide in which token to invest my money.
```

**Agent Response**:
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

### Example 2: Market Overview
**User Query**:
```
What are the top 5 cryptocurrencies by market cap right now?
```

**Agent Response**:
```
Here are the top 5 cryptocurrencies by market capitalization as of now:

1. Bitcoin (BTC)
   - Price: $67,245.32
   - Market Cap: $1,321,456,789,123
   - 24h Volume: $42,567,890,123
   - 24h Change: +2.3%

2. Ethereum (ETH)
   - Price: $3,456.78
   - Market Cap: $415,678,901,234
   - 24h Volume: $18,901,234,567
   - 24h Change: +1.5%

3. Binance Coin (BNB)
   - Price: $567.89
   - Market Cap: $87,654,321,098
   - 24h Volume: $3,456,789,012
   - 24h Change: -0.8%

4. Solana (SOL)
   - Price: $135.27
   - Market Cap: $44,649,193,819
   - 24h Volume: $1,489,703,528
   - 24h Change: +0.0%

5. XRP (XRP)
   - Price: $0.5678
   - Market Cap: $28,901,234,567
   - 24h Volume: $1,234,567,890
   - 24h Change: -1.2%

This information is based on real-time market data and may change rapidly. The cryptocurrency market is highly volatile, and these values can fluctuate significantly even within short time periods.
```

### Example 3: Technical Analysis
**User Query**:
```
Can you provide a technical analysis for ETH?
```

**Agent Response**:
```
# Technical Analysis for Ethereum (ETH)

## Current Market Data
- Current Price: $3,456.78
- 24h Trading Volume: $18,901,234,567
- Market Cap: $415,678,901,234

## Price Action Analysis
- ETH is currently trading above its 50-day moving average ($3,234.56), indicating a bullish short-term trend
- The price has formed a higher high and higher low pattern over the past 2 weeks
- Currently testing resistance at $3,500

## Key Technical Indicators
- RSI (14): 62 - Moderately bullish, not yet overbought
- MACD: Positive and above signal line, showing bullish momentum
- Bollinger Bands: Price is in the upper half, suggesting upward pressure

## Support and Resistance Levels
- Strong Support: $3,200, $3,000, $2,800
- Key Resistance: $3,500, $3,800, $4,000

## Volume Analysis
- Trading volume has increased by 15% compared to the 7-day average
- Volume profile shows strong buying interest above $3,300

## Conclusion
The technical outlook for ETH appears bullish in the short to medium term, with strong support established around $3,200. The price is approaching key resistance at $3,500, which if broken could lead to a test of the $3,800 level. However, traders should be cautious of potential rejection at the current resistance level, which could lead to a retest of support.

This analysis is based on current market conditions and should not be considered financial advice. Always conduct your own research and consider your risk tolerance before making investment decisions.
```

## Integration with Portfolio Manager
The market-fetcher agent is designed to work seamlessly with the portfolio-manager agent, providing it with the market intelligence needed to make informed trading recommendations:

```sh
# First, run the market-fetcher agent
nearai agent interactive ./market-fetcher/0.0.1 --local

# Then, in another terminal, run the portfolio-manager agent
nearai agent interactive ./portfolio-manager/0.0.1 --local
```

## Data Sources
- CoinGecko API for comprehensive market data
- Trading exchanges for order book information
- Historical price databases for trend analysis

## Notes
- All market data is provided for informational purposes only
- Cryptocurrency markets are highly volatile and past performance is not indicative of future results
- Always verify critical information from multiple sources before making investment decisions

## Try It Online
You can try the market-fetcher agent online at [NEAR AI Platform](https://app.near.ai/agents/temazzz.near/market-fetcher/latest) 
