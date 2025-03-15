# Portfolio Manager Agent

## Overview
The Portfolio Manager is an AI-powered agent designed to analyze cryptocurrency portfolios and provide intelligent trading recommendations. It connects directly to your OKX exchange account to fetch real-time portfolio data, analyze market conditions, and suggest optimal trades based on your investment goals and preferences.

## Features
- **Portfolio Analysis**: Comprehensive analysis of your current cryptocurrency holdings
- **Market Intelligence**: Integration with the market-fetcher agent for real-time market data
- **Trading Recommendations**: Actionable trade suggestions based on your investment strategy
- **Risk Assessment**: Evaluation of portfolio risk and diversification
- **Automated Rebalancing**: Suggestions for portfolio rebalancing to maintain optimal allocations
- **Strategy Implementation**: Support for various investment strategies (growth, value, momentum)

## Technical Implementation
The agent is built on the NEAR AI platform using a Llama v3p1 70B model and implements several specialized functions:

- `get_okx_signature()`: Generates authentication signatures for OKX API
- `get_account_balance()`: Retrieves current portfolio holdings from OKX
- `get_account_balance_in_usd()`: Converts all holdings to USD value
- `call_market_fetcher()`: Integrates with the market-fetcher agent for market data
- `analyze_portfolio()`: Performs comprehensive portfolio analysis
- `generate_trade_recommendation()`: Creates actionable trade recommendations

The agent uses secure API authentication with HMAC-SHA256 signatures to interact with the OKX exchange API and implements error handling for API rate limits and connection issues.

## Prerequisites
- OKX exchange account
- API credentials with trading permissions
- Environment variables for API authentication

## Setup
1. **Set up OKX API credentials**:
   - Log in to your OKX account
   - Navigate to API Management
   - Create a new API key with read and trading permissions
   - Note your API key, secret, and passphrase

2. **Configure environment variables**:
   ```sh
   export OKX_API_KEY=your_api_key
   export OKX_API_SECRET=your_api_secret
   export OKX_API_PASSPHRASE=your_api_passphrase
   ```

3. **Run the agent locally**:
   ```sh
   nearai agent interactive ./portfolio-manager/0.0.1 --local
   ```

## Usage Examples

### Example 1: Portfolio Rebalancing
**User Query**:
```
Rebalance my portfolio, I want to invest in AI tokens.
```

**Agent Response**:
```json
{
   "action": "BUY",
   "coin": "FET",
   "amount_usd": 5000.0,
   "reasoning": "FET is a leading AI-focused token with strong fundamentals and recent positive momentum. Adding this position will increase your exposure to the AI sector while maintaining a balanced risk profile."
}
```

### Example 2: High-Growth Investment
**User Query**:
```
I want to invest in a coin with potential x100.
```

**Agent Response**:
```json
{
   "action": "BUY",
   "coin": "NEAR",
   "amount_usd": 10000.0,
   "reasoning": "NEAR has strong technological fundamentals, growing ecosystem adoption, and significant institutional backing. While all high-growth investments carry substantial risk, NEAR presents the most favorable risk-reward profile among the analyzed options."
}
```

## Integration with Auto-Trader
The portfolio-manager agent can be integrated with the auto-trader script for automated execution of trading recommendations:

```sh
python auto-trader.py --query "Rebalance my portfolio with focus on AI tokens" --interval 60
```

## Security Considerations
- API keys are stored as environment variables for security
- The agent never exposes your private keys
- All API communications use encrypted connections with HMAC-SHA256 signatures
- Trading limits can be set to prevent excessive losses

## Notes
- Always perform due diligence before executing trades
- The agent provides recommendations, but the final decision is yours
- Market conditions can change rapidly, and all investments carry risk
- Start with small trade sizes until you're comfortable with the agent's recommendations

## Try It Online
You can try the portfolio-manager agent online at [NEAR AI Platform](https://app.near.ai/agents/temazzz.near/portfolio-manager/latest)
