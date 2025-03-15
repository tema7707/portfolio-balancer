from nearai.agents.environment import Environment
from enum import Enum
import requests
import json
import os
import time
import hmac
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

class ThreadMode(Enum):
    SAME = "same"
    FORK = "fork"
    CHILD = "child"

class RunMode(Enum):
    SIMPLE = "simple"
    WITH_CALLBACK = "with_callback"

def run(env: Environment):
    # Get OKX API credentials from environment variables
    api_key = os.environ.get("OKX_API_KEY", "")
    api_secret = os.environ.get("OKX_API_SECRET", "")
    api_passphrase = os.environ.get("OKX_API_PASSPHRASE", "")
    
    # Set flag for demo account
    is_demo_account = True  # Set to True for OKX demo trading account
    
    # Check if API credentials are available
    missing_credentials = []
    if not api_key:
        missing_credentials.append("OKX_API_KEY")
    if not api_secret:
        missing_credentials.append("OKX_API_SECRET")
    if not api_passphrase:
        missing_credentials.append("OKX_API_PASSPHRASE")
    
    if missing_credentials:
        error_message = f"Error: Missing OKX API credentials: {', '.join(missing_credentials)}. Please set these environment variables."
        env.add_agent_log(error_message)
        env.add_reply(f"I couldn't find all the required OKX API credentials. The following environment variables are missing: {', '.join(missing_credentials)}.\n\nPlease ensure you've set all three required credentials (API key, secret, and passphrase) with the correct environment variable names.")
        env.request_user_input()
        return
    
    # Log credential presence (not actual values)
    env.add_agent_log(f"API credentials found - Key: {'✓' if api_key else '✗'}, Secret: {'✓' if api_secret else '✗'}, Passphrase: {'✓' if api_passphrase else '✗'}")
    env.add_agent_log(f"Using {'DEMO' if is_demo_account else 'LIVE'} trading account")
    
    # Register custom tools for portfolio management
    tool_registry = env.get_tool_registry()
    
    def get_okx_signature(timestamp, method, request_path, body=''):
        """
        Generate OKX API signature for authentication
        """
        if str(body) == '{}' or str(body) == 'None':
            body = ''
        
        # Construct the message string exactly as OKX expects
        message = timestamp + method + request_path + (body if body else '')
        
        # Log the pre-signature message for debugging (without exposing the secret)
        env.add_agent_log(f"Generating signature for: [{timestamp}] [{method}] [{request_path}]")
        
        try:
            mac = hmac.new(
                bytes(api_secret, encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod=hashlib.sha256
            )
            
            d = mac.digest()
            signature = base64.b64encode(d).decode('utf-8')
            return signature
        except Exception as e:
            env.add_agent_log(f"Error generating signature: {str(e)}")
            raise
    
    def test_api_connection() -> Dict[str, Any]:
        """
        Test the OKX API connection with a simple public endpoint
        
        Returns:
            A dictionary with the test result
        """
        try:
            # Determine the base URL based on whether it's a demo account
            base_url = "https://www.okx.com" if not is_demo_account else "https://www.okx.com"
            
            # Try a public endpoint first (no authentication required)
            public_url = f"{base_url}/api/v5/public/time"
            public_response = requests.get(public_url)
            
            if public_response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Failed to connect to OKX public API: {public_response.status_code}",
                    "is_connected": False
                }
            
            # Now try a private endpoint that requires authentication
            endpoint = "/api/v5/account/config"  # Simple endpoint that just returns account config
            
            # Prepare request headers with authentication
            timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
            signature = get_okx_signature(timestamp, "GET", endpoint)
            
            headers = {
                "OK-ACCESS-KEY": api_key,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": api_passphrase,
                "Content-Type": "application/json"
            }
            
            # For demo accounts, add the demo flag
            if is_demo_account:
                headers["x-simulated-trading"] = "1"
            
            # Log headers (without exposing sensitive data)
            env.add_agent_log(f"Request headers: API Key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}, Timestamp: {timestamp}, Demo: {is_demo_account}")
            
            # Make request to OKX API
            url = base_url + endpoint
            response = requests.get(url, headers=headers)
            
            # Log the response status and content for debugging
            env.add_agent_log(f"API test response: Status {response.status_code}, Content: {response.text[:100]}...")
            
            if response.status_code != 200:
                error_message = f"API authentication failed: {response.status_code}"
                if response.status_code == 401:
                    error_message += " - Unauthorized. Please check your API credentials."
                elif response.status_code == 400:
                    error_message += " - Bad request. Possibly malformed signature."
                
                return {
                    "status": "error",
                    "message": error_message,
                    "is_connected": False,
                    "response": response.text
                }
            
            return {
                "status": "success",
                "message": "Successfully connected to OKX API",
                "is_connected": True
            }
            
        except Exception as e:
            env.add_agent_log(f"Error testing API connection: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception during API connection test: {str(e)}",
                "is_connected": False
            }
    
    def get_account_balance() -> Dict[str, Any]:
        """
        Get account balance from OKX exchange using API key
        
        Returns:
            A dictionary with account balance information
        """
        try:
            # First test the API connection
            connection_test = test_api_connection()
            
            if connection_test.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"API connection test failed: {connection_test.get('message')}",
                    "balances": {}
                }
            
            # Determine the base URL based on whether it's a demo account
            base_url = "https://www.okx.com" if not is_demo_account else "https://www.okx.com"
            endpoint = "/api/v5/account/balance"
            
            # Prepare request headers with authentication
            timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
            signature = get_okx_signature(timestamp, "GET", endpoint)
            
            headers = {
                "OK-ACCESS-KEY": api_key,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": api_passphrase,
                "Content-Type": "application/json"
            }
            
            # For demo accounts, add the demo flag
            if is_demo_account:
                headers["x-simulated-trading"] = "1"
            
            # Make request to OKX API
            url = base_url + endpoint
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                env.add_agent_log(f"Error fetching account balance: {response.status_code}, {response.text}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch account balance: {response.status_code}. Response: {response.text[:200]}",
                    "balances": {}
                }
            
            data = response.json()
            
            if data.get("code") != "0":
                env.add_agent_log(f"OKX API error: {data.get('msg')}")
                return {
                    "status": "error",
                    "message": f"OKX API error: {data.get('msg')}",
                    "balances": {}
                }
            
            # Process account balance data
            balances = {}
            for account in data.get("data", []):
                for detail in account.get("details", []):
                    currency = detail.get("ccy", "").upper()
                    avail_bal = float(detail.get("availBal", 0))
                    
                    # Only include non-zero balances
                    if avail_bal > 0:
                        balances[currency] = avail_bal
            
            return {
                "status": "success",
                "message": "Account balance retrieved successfully",
                "balances": balances
            }
            
        except Exception as e:
            env.add_agent_log(f"Error in get_account_balance: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "balances": {}
            }
    
    def fetch_single_coin_price(coin: str) -> Dict[str, Any]:
        """
        Fetch the current price of a single coin from OKX
        
        Args:
            coin: The coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            A dictionary with price information
        """
        try:
            coin = coin.upper()
            
            # For stablecoins, assume 1:1 USD value
            stablecoins = ["USDT", "USDC", "DAI", "BUSD", "USDP", "GUSD", "USDK", "HUSD"]
            if coin in stablecoins:
                return {
                    "status": "success",
                    "message": f"Using 1:1 USD value for stablecoin {coin}",
                    "price": 1.0
                }
            
            # Determine the base URL based on whether it's a demo account
            base_url = "https://www.okx.com" if not is_demo_account else "https://www.okx.com"
            url = f"{base_url}/api/v5/market/ticker"
            params = {"instId": f"{coin}-USDT"}
            
            # For demo accounts, add the demo flag to headers
            headers = {}
            if is_demo_account:
                headers["x-simulated-trading"] = "1"
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                env.add_agent_log(f"Error fetching price for {coin}: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch price: {response.status_code}",
                    "price": 0
                }
            
            data = response.json()
            
            if data.get("code") != "0":
                env.add_agent_log(f"OKX API error for {coin}: {data.get('msg')}")
                
                # Try alternative pairs if USDT pair fails
                alternative_pairs = ["USD", "USDC", "DAI", "BUSD"]
                for quote in alternative_pairs:
                    if quote == "USDT":  # Skip USDT as we already tried it
                        continue
                        
                    alt_params = {"instId": f"{coin}-{quote}"}
                    alt_response = requests.get(url, params=alt_params, headers=headers)
                    
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        if alt_data.get("code") == "0" and alt_data.get("data"):
                            price = float(alt_data["data"][0].get("last", 0))
                            return {
                                "status": "success",
                                "message": f"Price for {coin} retrieved from alternative pair {coin}-{quote}",
                                "price": price
                            }
                
                # If all alternatives fail, return error
                return {
                    "status": "error",
                    "message": f"OKX API error: {data.get('msg')}",
                    "price": 0
                }
            
            ticker_data = data.get("data", [])
            if not ticker_data:
                return {
                    "status": "error",
                    "message": f"No price data found for {coin}",
                    "price": 0
                }
            
            price = float(ticker_data[0].get("last", 0))
            
            return {
                "status": "success",
                "message": f"Price for {coin} retrieved successfully",
                "price": price
            }
            
        except Exception as e:
            env.add_agent_log(f"Error fetching price for {coin}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "price": 0
            }
    
    def get_account_balance_in_usd() -> Dict[str, Any]:
        """
        Get account balance with clear USD values for each asset
        
        Returns:
            A dictionary with account balance information in USD and a formatted USD summary
        """
        try:
            # First get the account balance
            balance_result = get_account_balance()
            
            if balance_result.get("status") != "success":
                return balance_result
            
            balances = balance_result.get("balances", {})
            
            if not balances:
                return {
                    "status": "error",
                    "message": "No assets found in account or couldn't retrieve balance",
                    "balances": {},
                    "usd_values": {},
                    "total_usd_value": 0
                }
            
            # Get the list of currencies in the account
            currencies = list(balances.keys())
            
            # Define a list of known stablecoins
            stablecoins = ["USDT", "USDC", "DAI", "BUSD", "USDP", "GUSD", "USDK", "HUSD"]
            non_stablecoins = [c for c in currencies if c not in stablecoins]
            
            # Process all balances
            usd_values = {}
            total_usd_value = 0
            
            # Handle stablecoins (assume 1:1 with USD)
            for stablecoin in stablecoins:
                if stablecoin in balances:
                    amount = balances[stablecoin]
                    usd_values[stablecoin] = amount
                    total_usd_value += amount
            
            # Process non-stablecoin currencies
            errors = []
            if non_stablecoins:
                for coin in non_stablecoins:
                    try:
                        coin_data = fetch_single_coin_price(coin)
                        if coin_data.get("status") == "success":
                            price = coin_data.get("price", 0)
                            amount = balances[coin]
                            usd_value = amount * price
                            usd_values[coin] = usd_value
                            total_usd_value += usd_value
                        else:
                            error_msg = f"Could not get price for {coin}: {coin_data.get('message')}"
                            errors.append(error_msg)
                            env.add_agent_log(error_msg)
                    except Exception as e:
                        error_msg = f"Exception getting price for {coin}: {str(e)}"
                        errors.append(error_msg)
                        env.add_agent_log(error_msg)
            
            # Create a formatted USD summary string
            usd_summary = []
            for coin, usd_value in sorted(usd_values.items(), key=lambda x: x[1], reverse=True):
                usd_summary.append(f"{coin}: ${usd_value:.2f}")
            
            # Make the summary string
            if usd_summary:
                formatted_summary = "\n".join(usd_summary)
                total_line = f"\nTotal Portfolio Value: ${total_usd_value:.2f}"
                formatted_summary += total_line
            else:
                formatted_summary = "No portfolio data available"
            
            # Determine the status based on errors
            status = "success"
            message = "Account balance in USD retrieved successfully"
            
            if errors and usd_values:
                status = "partial_success"
                message = f"Retrieved partial portfolio data. Errors with some coins: {'; '.join(errors)}"
            elif errors and not usd_values:
                status = "error"
                message = f"Failed to get any valid price data: {'; '.join(errors)}"
            
            return {
                "status": status,
                "message": message,
                "balances": balances,
                "usd_values": usd_values,
                "total_usd_value": total_usd_value,
                "usd_summary": formatted_summary,
                "errors": errors if errors else []
            }
            
        except Exception as e:
            env.add_agent_log(f"Error in get_account_balance_in_usd: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception getting balance in USD: {str(e)}",
                "balances": {},
                "usd_values": {},
                "total_usd_value": 0,
                "usd_summary": "Error retrieving portfolio data"
            }
    
    def call_market_fetcher(query: str) -> str:
        """
        Call the market-fetcher agent to get market data
        
        Args:
            query: The query to send to the market-fetcher agent
            
        Returns:
            The response from the market-fetcher agent
        """
        try:
            # Call the market-fetcher agent
            thread_id = env.run_agent(
                "temazzz.near/market-fetcher/0.1.3/", 
                query=query,
                thread_mode=ThreadMode.FORK.value
            )
            
            env.add_agent_log(f"Market fetcher called with thread ID: {thread_id}")
            
            # Since we can't access thread info directly, we'll return a simple message
            return f"Called market-fetcher with query: '{query}'. Results will be used for analysis."
            
        except Exception as e:
            env.add_agent_log(f"Error calling market-fetcher: {str(e)}")
            return f"Error calling market-fetcher: {str(e)}"
    
    def get_coin_analysis(coin: str) -> Dict[str, Any]:
        """
        Get comprehensive analysis of a specific coin by calling market-fetcher
        
        Args:
            coin: The coin symbol to analyze (e.g., "BTC", "ETH")
            
        Returns:
            Dictionary with coin analysis information
        """
        try:
            # Build a specific query for the market fetcher
            query = f"Provide detailed analysis for {coin} including: current price, market cap, 24h trading volume, price movement, technical indicators, and market sentiment"
            
            # Call the market-fetcher agent
            thread_id = env.run_agent(
                "temazzz.near/market-fetcher/0.1.3/", 
                query=query,
                thread_mode=ThreadMode.FORK.value
            )
            
            env.add_agent_log(f"Market fetcher called for {coin} analysis with thread ID: {thread_id}")
            
            # Create structured response since we can't access thread info directly
            return {
                "status": "success",
                "message": f"Detailed analysis for {coin} has been requested",
                "thread_id": thread_id,
                "analysis_type": "coin_specific",
                "coin": coin
            }
            
        except Exception as e:
            env.add_agent_log(f"Error getting {coin} analysis: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception getting {coin} analysis: {str(e)}",
                "coin": coin
            }
    
    def compare_coins(coins: List[str]) -> Dict[str, Any]:
        """
        Compare multiple coins by calling market-fetcher
        
        Args:
            coins: List of coin symbols to compare (e.g., ["BTC", "ETH", "SOL"])
            
        Returns:
            Dictionary with coin comparison information
        """
        try:
            if not coins or len(coins) < 2:
                return {
                    "status": "error",
                    "message": "At least two coins required for comparison",
                    "coins": coins
                }
            
            # Format coin list for query
            coins_str = ", ".join(coins)
            
            # Build a specific query for the market fetcher
            query = f"Compare the following coins: {coins_str}. Include price comparison, market cap, trading volume, price movement, technical indicators, fundamentals, and which has better short and long-term potential"
            
            # Call the market-fetcher agent
            thread_id = env.run_agent(
                "temazzz.near/market-fetcher/0.1.3/", 
                query=query,
                thread_mode=ThreadMode.FORK.value
            )
            
            env.add_agent_log(f"Market fetcher called for coin comparison with thread ID: {thread_id}")
            
            # Create structured response since we can't access thread info directly
            return {
                "status": "success",
                "message": f"Comparison for {coins_str} has been requested",
                "thread_id": thread_id,
                "analysis_type": "coin_comparison",
                "coins": coins
            }
            
        except Exception as e:
            env.add_agent_log(f"Error comparing coins {coins}: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception comparing coins: {str(e)}",
                "coins": coins
            }
    
    def identify_trading_opportunities() -> Dict[str, Any]:
        """
        Identify potential trading opportunities in the market by calling market-fetcher
        
        Returns:
            Dictionary with trading opportunity information
        """
        try:
            # Build a specific query for the market fetcher
            query = "Identify top 5 trading opportunities in the current market. Include coins with favorable technical indicators, positive news, and growth potential. For each opportunity, provide the coin symbol, current price, target price, and rationale"
            
            # Call the market-fetcher agent
            thread_id = env.run_agent(
                "temazzz.near/market-fetcher/0.1.3/", 
                query=query,
                thread_mode=ThreadMode.FORK.value
            )
            
            env.add_agent_log(f"Market fetcher called for trading opportunities with thread ID: {thread_id}")
            
            # Create structured response since we can't access thread info directly
            return {
                "status": "success",
                "message": "Trading opportunities have been requested",
                "thread_id": thread_id,
                "analysis_type": "trading_opportunities"
            }
            
        except Exception as e:
            env.add_agent_log(f"Error identifying trading opportunities: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception identifying trading opportunities: {str(e)}"
            }
    
    def analyze_portfolio() -> Dict[str, Any]:
        """
        Analyze portfolio to identify potential trading opportunities
        
        Returns:
            A dictionary with portfolio analysis
        """
        try:
            # Get account balance in USD
            balance_result = get_account_balance_in_usd()
            
            if balance_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Failed to analyze portfolio: {balance_result.get('message')}",
                    "analysis": None
                }
            
            balances = balance_result.get("balances", {})
            usd_values = balance_result.get("usd_values", {})
            total_usd_value = balance_result.get("total_usd_value", 0)
            
            if not balances:
                return {
                    "status": "error",
                    "message": "No assets found in portfolio or couldn't retrieve balance",
                    "analysis": None
                }
            
            # Calculate portfolio allocation percentages
            allocation = {}
            for coin, usd_value in usd_values.items():
                percentage = (usd_value / total_usd_value * 100) if total_usd_value > 0 else 0
                allocation[coin] = {
                    "amount": balances.get(coin, 0),
                    "usd_value": usd_value,
                    "percentage": percentage
                }
            
            # Get market sentiment for top coins in portfolio (simulate this since we can't get actual thread info)
            portfolio_coins = [coin for coin in balances.keys() if coin not in ["USDT", "USDC", "DAI", "BUSD"]]
            sentiments = {}
            
            for coin in portfolio_coins:
                # Skip if USD value is very small (less than $10)
                if usd_values.get(coin, 0) < 10:
                    continue
                    
                # Call market-fetcher but don't rely on getting the results back
                call_market_fetcher(f"Analyze market sentiment for {coin}")
                
                # Since we can't get the actual sentiment, we'll use price data as a proxy
                coin_price = fetch_single_coin_price(coin)
                # This is simplified logic - in a real scenario we'd get actual sentiment from market-fetcher
                if coin_price.get("status") == "success":
                    # This is just a placeholder since we can't get real sentiment
                    sentiments[coin] = "neutral"
            
            # Generate portfolio overview
            portfolio_overview = []
            for coin, data in allocation.items():
                overview_item = {
                    "coin": coin,
                    "amount": data["amount"],
                    "usd_value": data["usd_value"],
                    "percentage": data["percentage"],
                    "sentiment": sentiments.get(coin, "unknown") if coin in portfolio_coins else "stablecoin"
                }
                portfolio_overview.append(overview_item)
            
            # Sort portfolio overview by USD value (descending)
            portfolio_overview.sort(key=lambda x: x["usd_value"], reverse=True)
            
            # Generate simplified trading recommendations based on allocation
            recommendations = []
            
            return {
                "status": "success",
                "message": "Portfolio analysis completed successfully",
                "analysis": {
                    "portfolio_overview": portfolio_overview,
                    "allocation": allocation,
                    "total_usd_value": total_usd_value,
                    "recommendations": recommendations
                }
            }
            
        except Exception as e:
            env.add_agent_log(f"Error analyzing portfolio: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception analyzing portfolio: {str(e)}",
                "analysis": None
            }
    
    def generate_trade_recommendation() -> Dict[str, Any]:
        """
        Generate a single high-confidence trade recommendation
        
        Returns:
            A dictionary with a trade recommendation
        """
        try:
            # Analyze portfolio
            analysis_result = analyze_portfolio()
            
            if analysis_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Failed to generate recommendation: {analysis_result.get('message')}",
                    "recommendation": None
                }
            
            analysis = analysis_result.get("analysis", {})
            recommendations = analysis.get("recommendations", [])
            
            if not recommendations:
                return {
                    "status": "success",
                    "message": "No trade recommendations at this time",
                    "recommendation": None
                }
            
            # Get the highest priority recommendation
            # For now, we'll just take the first one, but this could be improved
            recommendation = recommendations[0]
            
            # Validate USDT balance for buy orders
            if recommendation["action"] == "buy":
                balances = get_account_balance().get("balances", {})
                usdt_balance = balances.get("USDT", 0)
                usd_amount = recommendation.get("usd_amount", 0)
                
                if usd_amount > usdt_balance:
                    # Adjust the buy amount to match available USDT
                    recommendation["usd_amount"] = usdt_balance * 0.95  # Leave 5% for fees
                    
                    # Recalculate coin amount
                    coin_data = fetch_single_coin_price(recommendation["coin"])
                    if coin_data.get("status") == "success":
                        price = coin_data.get("price", 0)
                        if price > 0:
                            recommendation["amount"] = recommendation["usd_amount"] / price
            
            return {
                "status": "success",
                "message": "Trade recommendation generated successfully",
                "recommendation": recommendation
            }
            
        except Exception as e:
            env.add_agent_log(f"Error generating trade recommendation: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "recommendation": None
            }
    
    def get_portfolio_actions() -> Dict[str, Any]:
        """
        Generate concrete buy/sell actions for the portfolio in JSON format
        
        Returns:
            A dictionary with specific sell and buy actions in JSON format
        """
        try:
            # First analyze the portfolio to get current allocation
            balance_result = get_account_balance_in_usd()
            
            if balance_result.get("status") != "success" and balance_result.get("status") != "partial_success":
                return {
                    "status": "error",
                    "message": f"Failed to generate portfolio actions: {balance_result.get('message')}",
                    "actions": None
                }
            
            balances = balance_result.get("balances", {})
            usd_values = balance_result.get("usd_values", {})
            total_usd_value = balance_result.get("total_usd_value", 0)
            
            if not balances or not usd_values:
                return {
                    "status": "error",
                    "message": "No assets found in portfolio or couldn't retrieve balance",
                    "actions": None
                }
            
            # Calculate current allocation percentages
            allocation = {}
            for coin, usd_value in usd_values.items():
                percentage = (usd_value / total_usd_value * 100) if total_usd_value > 0 else 0
                allocation[coin] = {
                    "amount": balances.get(coin, 0),
                    "usd_value": usd_value,
                    "percentage": percentage
                }
            
            # Determine ideal allocation based on portfolio size and diversification
            # This is a simplified example - could be more sophisticated in production
            ideal_allocation = {}
            
            # For a basic portfolio, we might recommend:
            # - 40% in major assets (BTC, ETH)
            # - 30% in medium cap alts 
            # - 20% in smaller promising projects
            # - 10% in stablecoins for buying opportunities
            if total_usd_value > 0:
                # Define asset categories (simplified)
                major_assets = ["BTC", "ETH"]
                medium_assets = ["SOL", "BNB", "XRP", "ADA", "DOT", "AVAX", "MATIC", "LINK"]
                stablecoins = ["USDT", "USDC", "DAI", "BUSD", "USDP", "GUSD", "USDK", "HUSD"]
                
                # Get current assets by category
                current_major = {coin: data for coin, data in allocation.items() if coin in major_assets}
                current_medium = {coin: data for coin, data in allocation.items() if coin in medium_assets}
                current_stables = {coin: data for coin, data in allocation.items() if coin in stablecoins}
                current_others = {coin: data for coin, data in allocation.items() 
                                if coin not in major_assets and coin not in medium_assets and coin not in stablecoins}
                
                # Calculate current allocation by category
                major_percent = sum(data["percentage"] for data in current_major.values())
                medium_percent = sum(data["percentage"] for data in current_medium.values())
                stables_percent = sum(data["percentage"] for data in current_stables.values())
                others_percent = sum(data["percentage"] for data in current_others.values())
                
                # Determine rebalancing needs
                sell_actions = []
                buy_actions = []
                
                # Simplified algorithm for portfolio recommendations:
                # 1. Check if stablecoin percentage is below target (10%)
                if stables_percent < 10:
                    # Need to increase stablecoin position - sell some assets
                    shortage = 10 - stables_percent
                    
                    # If we have excess in other categories, sell from there
                    if others_percent > 20:
                        # Sell from other assets (sort by value descending)
                        excess = others_percent - 20
                        to_sell_pct = min(excess, shortage)
                        sell_value = total_usd_value * (to_sell_pct / 100)
                        
                        # Find assets to sell (starting with largest holdings)
                        others_sorted = sorted(current_others.items(), key=lambda x: x[1]["usd_value"], reverse=True)
                        for coin, data in others_sorted:
                            if sell_value <= 0:
                                break
                                
                            # Sell up to 50% of the position
                            coin_sell_value = min(data["usd_value"] * 0.5, sell_value)
                            if coin_sell_value > 10:  # Only if worth more than $10
                                # Calculate amount in native token
                                coin_price = data["usd_value"] / data["amount"]
                                sell_amount = coin_sell_value / coin_price if coin_price > 0 else 0
                                
                                if sell_amount > 0:
                                    sell_actions.append({
                                        "action": "sell",
                                        "coin": coin,
                                        "amount": sell_amount,
                                        "usd_value": coin_sell_value,
                                        "reason": f"Rebalancing: Reducing {coin} exposure to increase stablecoin position"
                                    })
                                    sell_value -= coin_sell_value
                
                # 2. Check if major asset percentage is below target (40%)
                usdt_balance = balances.get("USDT", 0)
                if major_percent < 40 and usdt_balance > 0:
                    # Need to increase major asset position
                    shortage = 40 - major_percent
                    to_buy_value = min(usdt_balance * 0.8, total_usd_value * (shortage / 100))
                    
                    if to_buy_value > 10:  # Only if worth more than $10
                        # Distribute between BTC and ETH
                        for coin in major_assets:
                            if coin in current_major:
                                # If we already have this asset, allocation portion of remaining funds
                                coin_data = fetch_single_coin_price(coin)
                                if coin_data.get("status") == "success":
                                    price = coin_data.get("price", 0)
                                    if price > 0:
                                        # Allocate funds to this major asset
                                        coin_buy_value = to_buy_value / len(major_assets)
                                        buy_amount = coin_buy_value / price
                                        
                                        if buy_amount > 0:
                                            buy_actions.append({
                                                "action": "buy",
                                                "coin": coin,
                                                "amount": buy_amount,
                                                "usd_value": coin_buy_value,
                                                "reason": f"Rebalancing: Increasing {coin} exposure toward target allocation"
                                            })
                
                # If no specific actions were generated, suggest some based on portfolio composition
                if not sell_actions and not buy_actions:
                    # If we have a very unbalanced portfolio, suggest rebalancing
                    if major_percent < 20 and usdt_balance > 100:
                        # Suggest buying some BTC or ETH
                        buy_value = min(usdt_balance * 0.5, 200)  # Use up to 50% of USDT, max $200
                        
                        # Pick the major asset with lower allocation
                        target_major = "BTC" if "BTC" not in current_major or (
                            "ETH" in current_major and current_major.get("BTC", {}).get("usd_value", 0) < 
                            current_major.get("ETH", {}).get("usd_value", 0)) else "ETH"
                        
                        coin_data = fetch_single_coin_price(target_major)
                        if coin_data.get("status") == "success":
                            price = coin_data.get("price", 0)
                            if price > 0:
                                buy_amount = buy_value / price
                                buy_actions.append({
                                    "action": "buy",
                                    "coin": target_major,
                                    "amount": buy_amount,
                                    "usd_value": buy_value,
                                    "reason": f"Portfolio is underweight in major assets. Adding {target_major} to improve stability."
                                })
                    
                    # If we have too many small positions, suggest consolidating
                    small_positions = [coin for coin, data in allocation.items() 
                                    if data["usd_value"] < total_usd_value * 0.02 and coin not in stablecoins]
                    
                    if len(small_positions) > 5:  # Too many small positions
                        # Recommend selling smallest positions
                        small_sorted = sorted([(coin, allocation[coin]) for coin in small_positions], 
                                            key=lambda x: x[1]["usd_value"])
                        
                        # Sell up to 3 of the smallest positions
                        for coin, data in small_sorted[:3]:
                            if data["usd_value"] > 10:  # Only if worth more than $10
                                sell_actions.append({
                                    "action": "sell",
                                    "coin": coin,
                                    "amount": data["amount"],  # Sell entire position
                                    "usd_value": data["usd_value"],
                                    "reason": f"Portfolio optimization: Consolidating small {coin} position to reduce fragmentation"
                                })
            
            # Format the response as a clean JSON-ready structure
            actions = {
                "sell": [],
                "buy": []
            }
            
            # Format sell actions
            for action in sell_actions:
                actions["sell"].append({
                    "coin": action["coin"],
                    "amount": round(action["amount"], 8),
                    "estimated_value_usd": round(action["usd_value"], 2)
                })
            
            # Format buy actions
            for action in buy_actions:
                actions["buy"].append({
                    "coin": action["coin"],
                    "amount": round(action["amount"], 8),
                    "cost_usdt": round(action["usd_value"], 2)
                })
            
            # Create a simple formatted string representation
            actions_summary = json.dumps(actions, indent=2)
            
            return {
                "status": "success",
                "message": "Portfolio actions generated successfully",
                "actions": actions,
                "actions_json": actions_summary
            }
            
        except Exception as e:
            env.add_agent_log(f"Error generating portfolio actions: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception generating portfolio actions: {str(e)}",
                "actions": None
            }

    
    # Test API connection first
    api_test_result = test_api_connection()
    env.add_agent_log(f"API test result: {api_test_result}")
    
    # Register the tools
    tool_registry.register_tool(get_account_balance)
    tool_registry.register_tool(get_account_balance_in_usd)
    tool_registry.register_tool(call_market_fetcher)
    tool_registry.register_tool(analyze_portfolio)
    tool_registry.register_tool(generate_trade_recommendation)
    tool_registry.register_tool(get_portfolio_actions)
    tool_registry.register_tool(get_coin_analysis)
    tool_registry.register_tool(compare_coins)
    tool_registry.register_tool(identify_trading_opportunities)
    
    # System prompt for the portfolio manager agent
    system_prompt = {
        "role": "system", 
        "content": """You are a cryptocurrency portfolio manager that analyzes user portfolios and provides trade recommendations.

You have several tools at your disposal:

1. get_account_balance - Gets the current account balance from OKX
2. get_account_balance_in_usd - Gets the account balance with USD values
3. call_market_fetcher - Calls the market-fetcher agent to get market data
4. get_coin_analysis - Get detailed analysis for a specific coin
5. get_market_overview - Get overall market conditions and sentiment
6. compare_coins - Compare multiple coins on various metrics
7. identify_trading_opportunities - Find potential trading opportunities
8. get_coin_news - Get latest news and developments for a specific coin
9. analyze_portfolio - Analyzes the portfolio and identifies potential trading opportunities
10. generate_trade_recommendation - Generates a single high-confidence trade recommendation
11. get_portfolio_actions - Generate concrete buy/sell actions for the portfolio

How to handle user requests:
- For portfolio overview: Call get_account_balance_in_usd
- For market analysis: Use the specialized market fetcher tools
- For trading recommendations: Call analyze_portfolio or generate_trade_recommendation
- For specific coin information: Use get_coin_analysis or get_coin_news
- For comparing investment options: Use compare_coins
- For market opportunities outside current portfolio: Use identify_trading_opportunities

Important:
1. Always verify that there is sufficient USDT balance before recommending buy actions
2. Provide clear explanations for your recommendations
3. Include both token amounts and USD values in your responses
4. Be cautious with recommendations and explain the risks

Remember that users may make financial decisions based on your information, so accuracy and clarity are essential. Always include appropriate disclaimers in your responses.

"""
    }
    
    # Get user messages
    user_messages = env.list_messages()
    answers_count = 0
    
    # If this is the first run with no messages, add a welcome message
    if not user_messages:
        # Add API status to welcome message
        api_status = ""
        if api_test_result.get("status") != "success":
            api_status = """
            ⚠️ **API Connection Status: Failed**
            
            I couldn't connect to your OKX account with the provided API credentials.
            
            To use your account data, please check:
            1. Your API key, secret, and passphrase are correctly set as environment variables
            2. Your API key has the necessary permissions (read access)
            3. The API key is active and not restricted by IP
            
            Error details: """ + api_test_result.get("message", "Unknown error")
        else:
            api_status = """
            ✅ **API Connection Status: Success**
            
            Successfully connected to your OKX account.
            """
        
        welcome_message = f"""
        Welcome to your Crypto Portfolio Manager!
        
        I can help you analyze your portfolio and provide trading recommendations based on market data.
        
        {api_status}
        
        You can ask me for:
        - "Show me my current portfolio"
        - "What's the USD value of my holdings?"
        - "Analyze my portfolio"
        - "Give me a trade recommendation"
        - "What's the market sentiment for coins in my portfolio?"
        
        What would you like to know about your crypto portfolio today?
        """
        env.add_reply(welcome_message)
        env.request_user_input()
        return
    
    # Process the user's request using tools
    all_tools = tool_registry.get_all_tool_definitions()

    need_to_use_more_tools = True
    history = [system_prompt] + user_messages
    while need_to_use_more_tools and answers_count < 10:
        response = env.completions_and_run_tools(
            history,
            tools=all_tools
        )
        # Handle tool calls response
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            history.append({"role": "assistant", "content": "Function called: " + tool_call.function.name + " Function result: " + str(env.list_messages()[-1])})
            answers_count += 1
        else:
            history.append({"role": "assistant", "content": "No tool calls found"})

        need_to_use_more_tools = env.completion(
            [system_prompt] + user_messages + [{"role": "assistant", "content": response.choices[0].message.content}, 
            {"role": "assistant", "content": f"""
             You are a helpful assistant with access to tools for managing crypto portfolios. 
Now, you can only respond with "yes" or "no". 

- Respond "yes" if you need to call additional tools.  
- Respond "no" if no more tools are needed.  

Available tools:  
{all_tools}  

Chat history:  
{history}  

Should you call more tools? Reply only with "yes" or "no".  

Expected Output:  
- If "yes", return: {{"need_tool": "yes", "tool": "tool_name"}}  
- If "no", return: {{"need_tool": "no"}}  
the format is very important. it should be valid python code, valid json.
             """}]
        )
        answer = eval(need_to_use_more_tools.split("<|end_header_id|>")[1].replace("```json", "").replace("```", ""))
        need_to_use_more_tools = answer["need_tool"].lower().strip() == "yes"
        if need_to_use_more_tools:
            tool_name = answer["tool"]
            history.append({"role": "user", "content": "Call the tool " + tool_name})

    # Get the final response from the model
    final_message = env.completion(
        [system_prompt] + user_messages + [
            {"role": "assistant", "content": "Generate a final response based on the function calling information: " + str(env.list_messages()[-answers_count:]) + 
            """
            VERY IMPORTANT INSTRUCTIONS:
            1. If there were ANY errors in API authentication or data retrieval, explain the errors clearly and don't show any portfolio data.
            2. If you see error messages containing '401', 'unauthorized', or 'API connection test failed', explain that the API credentials are invalid.
            3. DO NOT display any portfolio data unless it was successfully retrieved from the actual OKX API.
            4. If data couldn't be retrieved, suggest solutions to fix the API credential issues.
            5. Use a formal, professional tone and be honest about errors encountered.

            In the final message, you should deside what I should do with my portfolio based on the information provided.
            Here what I want to get:
            {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "action": {
                "type": "string",
                "enum": ["BUY", "SELL"],
                "description": "Indicates whether the action is to buy or sell the cryptocurrency."
                },
                "coin": {
                "type": "string",
                "description": "The ticker symbol of the cryptocurrency (e.g., BTC, ETH, USDT)."
                },
                "amount_usd": {
                "type": "number",
                "minimum": 0,
                "description": "The amount in USD to be used for buying or selling the cryptocurrency."
                }
            },
            "required": ["action", "coin", "amount_usd"],
            "additionalProperties": false
            }
            So please use as many function calling as you like just to get the best result that contains all the information that I need and make the final desision.
            """
            }
        ]
    ).split("<|end_header_id|>")[1]
    env.add_reply(final_message)

    system_prompt = {
    "role": "system", 
    "content": """You are a helpful assistant that should write a final response based on the provided information.
    You only can write a JSONs. It should be valid json. And use this schema:
    {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
        "type": "string",
        "enum": ["BUY", "SELL"],
        "description": "Indicates whether the action is to buy or sell the cryptocurrency."
        },
        "coin": {
        "type": "string",
        "description": "The ticker symbol of the cryptocurrency (e.g., BTC, ETH, USDT)."
        },
        "amount_usd": {
        "type": "number",
        "minimum": 0,
        "description": "The amount in USD to be used for buying or selling the cryptocurrency."
        }
    },
    "required": ["action", "coin", "amount_usd"],
    "additionalProperties": false
    }
    Analyze all information from the provided dialoge and funcion calling to write a valid json with final desision what to do!
    Don't use function calling in your response. 
    Just provide a valid json with the final desision.
    My life depends on it.
    """
    }

    # Update the final message generation to include JSON output when appropriate
    final_message = env.completion(
        [system_prompt] + user_messages + [
            {"role": "assistant", "content": "Generate a final response based on the function calling information: " + str(env.list_messages()[-answers_count:]) + "FINAL MESSAGE: " + final_message,
            }
        ]
    ).split("<|end_header_id|>")[1]
    final_message = "Final desision:" + final_message
    env.add_reply(final_message)
    # Request user input for the next interaction
    env.request_user_input()

run(env)
