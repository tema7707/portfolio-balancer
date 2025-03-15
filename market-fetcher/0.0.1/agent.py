from nearai.agents.environment import Environment
import requests
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import math
import json
import time


def run(env: Environment):
    # Register custom tools for crypto data
    tool_registry = env.get_tool_registry()
    
    def get_top_coins(limit: int = 10) -> Dict[str, Any]:
        """
        Get list of top cryptocurrencies by market cap.
        
        Args:
            limit: The number of top coins to retrieve (default: 10)
            
        Returns:
            A dictionary with the top coins data including symbol, price, market cap, volume, and 24h change
        """
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False
            }
            
            # In a real implementation, you might want to handle API rate limits
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                env.add_agent_log(f"Error fetching data: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch data: {response.status_code}",
                    "coins": []
                }
            
            data = response.json()
            
            coins = []
            for coin in data:
                coins.append({
                    "symbol": coin['symbol'].upper(),
                    "name": coin['name'],
                    "price": coin['current_price'],
                    "market_cap": coin['market_cap'],
                    "volume": coin['total_volume'],
                    "change_24h": coin['price_change_percentage_24h']
                })
            
            return {
                "status": "success",
                "coins": coins,
                "count": len(coins)
            }
        except Exception as e:
            env.add_agent_log(f"Error fetching coin data: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "coins": []
            }
    
    def get_top_tokens_formatted(limit: int = 10) -> str:
        """
        Get list of top tokens by market cap in a formatted table.
        
        Args:
            limit: The number of top tokens to retrieve (default: 10)
            
        Returns:
            A formatted string with a table of top tokens
        """
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False
            }
            
            response = requests.get(url, params=params)
            data = response.json()

            answer = [f"\n{'Symbol':<8}{'Price':<15}{'Market Cap':<20}{'24h Volume':<20}{'24h Change'}"]
            answer += ["-" * 75]
            
            for coin in data:
                answer += [
                    f"{coin['symbol'].upper():<8}"
                    f"${coin['current_price']:<14,.2f}"
                    f"${coin['market_cap']:<19,.0f}"
                    f"${coin['total_volume']:<19,.0f}"
                    f"{coin['price_change_percentage_24h']:<7.2f}%"
                ]
            
            return "\n".join(answer)
        except Exception as e:
            env.add_agent_log(f"Error fetching formatted token data: {str(e)}")
            return f"Error fetching data: {str(e)}"
    
    def search_token(token: str, min_volume: float = 0) -> Dict[str, Any]:
        """
        Search for a single token and get its trading information against USDT on OKX.
        
        Args:
            token: Token symbol to search for (e.g., "BTC", "ETH", "IMX")
            min_volume: Minimum 24h trading volume in USDT
            
        Returns:
            A dictionary with token trading information
        """
        try:
            # Ensure the token is uppercase for consistency
            token = token.upper()
            
            # Get ticker data from OKX
            ticker_url = "https://www.okx.com/api/v5/market/ticker"
            ticker_params = {"instId": f"{token}-USDT"}
            ticker_response = requests.get(ticker_url, params=ticker_params)
            
            if ticker_response.status_code != 200:
                env.add_agent_log(f"Error fetching ticker for {token}-USDT: {ticker_response.status_code}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch ticker for {token}-USDT: {ticker_response.status_code}",
                    "results": {}
                }
            
            ticker_data = ticker_response.json().get("data", [])
            if not ticker_data or len(ticker_data) == 0:
                env.add_agent_log(f"No ticker data received for {token}-USDT")
                return {
                    "status": "error", 
                    "message": f"No ticker data found for {token}-USDT",
                    "results": {}
                }
            
            ticker = ticker_data[0]
            volume_24h = float(ticker.get('volCcy24h', 0))
            
            if volume_24h < min_volume:
                return {
                    "status": "error",
                    "message": f"Token {token}-USDT has insufficient volume: {volume_24h} < {min_volume}",
                    "results": {}
                }
            
            # Get instrument info for additional details
            instrument_url = "https://www.okx.com/api/v5/public/instruments"
            instrument_params = {"instType": "SPOT", "instId": f"{token}-USDT"}
            instrument_response = requests.get(instrument_url, params=instrument_params)
            
            instrument_data = {}
            if instrument_response.status_code == 200:
                instruments = instrument_response.json().get("data", [])
                if instruments and len(instruments) > 0:
                    instrument_data = instruments[0]
            
            # Combine the data
            result = {
                f"{token}-USDT": {
                    'pair_info': {
                        'base': token,
                        'quote': 'USDT',
                        'active': instrument_data.get('state', '') == 'live',
                        'type': instrument_data.get('instType', 'SPOT'),
                        'min_amount': float(instrument_data.get('minSz', '0')) if instrument_data.get('minSz') else 0
                    },
                    'ticker': {
                        'symbol': f"{token}-USDT",
                        'last': float(ticker.get('last', 0)),
                        'bid': float(ticker.get('bidPx', 0)),
                        'ask': float(ticker.get('askPx', 0)),
                        'volume': volume_24h,
                        'change_24h': float(ticker.get('change24h', 0)) * 100 if ticker.get('change24h') else 0,
                        'high_24h': float(ticker.get('high24h', 0)),
                        'low_24h': float(ticker.get('low24h', 0)),
                        'timestamp': int(ticker.get('ts', 0))
                    }
                }
            }
            
            return {
                "status": "success",
                "message": "Token data retrieved successfully",
                "results": result
            }
            
        except Exception as e:
            env.add_agent_log(f"Error searching for token {token} on OKX: {e}")
            return {
                "status": "error",
                "message": str(e),
                "results": {}
            }

    def search_tokens(tokens: Union[str, List[str]], min_volume: float = 0) -> Dict[str, Any]:
        """
        Search for multiple tokens and get their trading information.
        
        Args:
            tokens: Token symbol(s) to search for (e.g., "BTC", ["BTC", "ETH", "IMX"])
            min_volume: Minimum 24h trading volume in USDT
            
        Returns:
            A dictionary with token trading information
        """
        # Improved handling of token input
        if isinstance(tokens, str):
            # Handle case where tokens might be a string representation of a list
            if tokens.startswith('[') and tokens.endswith(']'):
                try:
                    # Try to safely parse it as a list
                    import ast
                    token_list = ast.literal_eval(tokens)
                except (ValueError, SyntaxError):
                    # If parsing fails, treat it as a single token
                    token_list = [tokens]
            else:
                # Regular string case (single token)
                token_list = [tokens]
        else:
            # Already a list
            token_list = tokens
        
        # Ensure all tokens are strings
        token_list = [str(token).strip() for token in token_list]
        
        # Log the tokens being processed
        env.add_agent_log(f"Processing tokens: {token_list}")
        
        # Process each token individually
        all_results = {}
        for token in token_list:
            token_result = search_token(token, min_volume)
            if token_result.get("status") == "success":
                all_results.update(token_result.get("results", {}))
            # Add a small delay to avoid rate limiting
            time.sleep(0.2)
        
        return {
            "status": "success" if all_results else "error",
            "message": "Token data retrieved successfully" if all_results else f"No matching tokens found for {token_list}",
            "results": all_results
        }
    
    def get_order_book(token: str, levels: int = 20) -> Dict[str, Any]:
        """
        Get detailed order book for a token trading against USDT on OKX.
        
        Args:
            token: Token symbol (e.g., "BTC", "ETH", "IMX")
            levels: Number of order book levels to return
            
        Returns:
            A dictionary with order book data
        """
        token = token.upper()
        symbol = f"{token}-USDT"
        
        try:
            # Fetch order book from OKX
            orderbook_url = "https://www.okx.com/api/v5/market/books"
            orderbook_params = {
                "instId": symbol,
                "sz": 400  # Request a deep order book
            }
            
            orderbook_response = requests.get(orderbook_url, params=orderbook_params)
            
            if orderbook_response.status_code != 200:
                env.add_agent_log(f"Error fetching order book: {orderbook_response.status_code}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch order book: {orderbook_response.status_code}",
                    "order_book": None
                }
            
            orderbook_data = orderbook_response.json().get("data", [])
            
            if not orderbook_data or len(orderbook_data) == 0:
                return {
                    "status": "error",
                    "message": f"No order book data found for {symbol}",
                    "order_book": None
                }
            
            order_book = orderbook_data[0]
            
            # Convert order book to more usable format
            bids = [[float(price), float(qty)] for price, qty, *_ in (order_book.get('bids', []))]
            asks = [[float(price), float(qty)] for price, qty, *_ in (order_book.get('asks', []))]
            
            # Auto-determine price step based on price
            first_price = bids[0][0] if bids else 0
            price_step = 0.01  # Default
            
            if first_price >= 10000:
                price_step = 100
            elif first_price >= 1000:
                price_step = 10
            elif first_price >= 100:
                price_step = 1
            elif first_price >= 10:
                price_step = 0.1
            
            # Group orders by price step
            def group_orders(orders, step, is_bid):
                grouped = {}
                for price, amount in orders:
                    group_price = (math.floor if is_bid else math.ceil)(price / step) * step
                    grouped[group_price] = grouped.get(group_price, 0) + amount
                return grouped
            
            grouped_bids = group_orders(bids, price_step, True)
            grouped_asks = group_orders(asks, price_step, False)
            
            total_bid_volume = sum(grouped_bids.values())
            total_ask_volume = sum(grouped_asks.values())
            total_volume = total_bid_volume + total_ask_volume
            
            bid_percentage = (total_bid_volume / total_volume * 100) if total_volume > 0 else 0
            ask_percentage = (total_ask_volume / total_volume * 100) if total_volume > 0 else 0
            
            # Format order book levels
            sorted_bids = sorted(grouped_bids.items(), reverse=True)[:levels]
            sorted_asks = sorted(grouped_asks.items())[:levels]
            
            bid_levels = []
            bid_cumulative = 0
            for price, amount in sorted_bids:
                bid_cumulative += amount
                total = price * amount
                bid_levels.append({
                    'price': price,
                    'amount': amount,
                    'total': total,
                    'cumulative': bid_cumulative
                })
            
            ask_levels = []
            ask_cumulative = 0
            for price, amount in sorted_asks:
                ask_cumulative += amount
                total = price * amount
                ask_levels.append({
                    'price': price,
                    'amount': amount,
                    'total': total,
                    'cumulative': ask_cumulative
                })
            
            # Calculate metrics
            best_bid = sorted_bids[0][0] if sorted_bids else None
            best_ask = sorted_asks[0][0] if sorted_asks else None
            spread = best_ask - best_bid if (best_bid and best_ask) else None
            spread_percentage = (spread / best_bid * 100) if spread and best_bid else None
            
            return {
                "status": "success",
                "order_book": {
                    'symbol': symbol,
                    'exchange': "okx",
                    'timestamp': int(order_book.get('ts', 0)),
                    'price_step': price_step,
                    'bids': bid_levels,
                    'asks': ask_levels,
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'spread': spread,
                    'spread_percentage': spread_percentage,
                    'total_bid_value': sum(price * amount for price, amount in grouped_bids.items()),
                    'total_ask_value': sum(price * amount for price, amount in grouped_asks.items()),
                    'bid_percentage': bid_percentage,
                    'ask_percentage': ask_percentage
                }
            }
            
        except Exception as e:
            env.add_agent_log(f"Error processing order book for {symbol}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "order_book": None
            }
    
    def get_historical_data(token: str, timeframe: str = "1H", limit: int = 100) -> Dict[str, Any]:
        """
        Get historical OHLCV data for a token.
        
        Args:
            token: Token symbol (e.g., "BTC", "ETH", "IMX")
            timeframe: Timeframe for candles (e.g., "1m", "1H", "1D")
            limit: Number of candles to retrieve
            
        Returns:
            A dictionary with historical price data
        """
        token = token.upper()
        symbol = f"{token}-USDT"
        
        try:
            # Fetch candles from OKX
            candles_url = "https://www.okx.com/api/v5/market/candles"
            candles_params = {
                "instId": symbol,
                "bar": timeframe,
                "limit": limit
            }
            
            candles_response = requests.get(candles_url, params=candles_params)
            
            if candles_response.status_code != 200:
                env.add_agent_log(f"Error fetching OHLCV data: {candles_response.status_code}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch OHLCV data: {candles_response.status_code}",
                    "ohlcv": None
                }
            
            candles_data = candles_response.json().get("data", [])
            
            if not candles_data:
                return {
                    "status": "error",
                    "message": f"No OHLCV data found for {symbol}",
                    "ohlcv": None
                }
            
            # Process candles
            candles = []
            for candle in candles_data:
                # OKX API returns: [ts, open, high, low, close, vol, volCcy]
                ts, open_price, high, low, close, _, volume = candle
                candles.append({
                    'timestamp': datetime.fromtimestamp(int(ts)/1000).isoformat(),
                    'open': float(open_price),
                    'high': float(high),
                    'low': float(low),
                    'close': float(close),
                    'volume': float(volume)
                })
            
            # OKX returns newest first, so reverse for chronological order
            candles.reverse()
            
            # Calculate metrics
            if len(candles) > 1:
                price_change = candles[-1]['close'] - candles[0]['open']
                price_change_pct = (price_change / candles[0]['open']) * 100
                total_volume = sum(c['volume'] for c in candles)
                avg_volume = total_volume / len(candles)
                max_price = max(c['high'] for c in candles)
                min_price = min(c['low'] for c in candles)
                volatility = sum((c['high'] - c['low']) / c['low'] for c in candles) / len(candles) * 100
            else:
                price_change = 0
                price_change_pct = 0
                total_volume = candles[0]['volume'] if candles else 0
                avg_volume = total_volume
                max_price = candles[0]['high'] if candles else 0
                min_price = candles[0]['low'] if candles else 0
                volatility = 0
            
            return {
                "status": "success",
                "ohlcv": {
                    'symbol': symbol,
                    'exchange': "okx",
                    'timeframe': timeframe,
                    'candles': candles,
                    'price_change': price_change,
                    'price_change_pct': price_change_pct,
                    'total_volume': total_volume,
                    'avg_volume': avg_volume,
                    'max_price': max_price,
                    'min_price': min_price,
                    'volatility': volatility
                }
            }
            
        except Exception as e:
            env.add_agent_log(f"Error fetching OHLCV data for {symbol}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "ohlcv": None
            }
    
    def fetch_comprehensive_data(token: str) -> Dict[str, Any]:
        """
        Fetch comprehensive market data for a token by calling multiple tools.
        
        Args:
            token: Token symbol (e.g., "BTC", "ETH", "IMX")
            
        Returns:
            A dictionary with comprehensive market data
        """
        token = token.upper()
        
        results = {}
        
        # Get basic token info from CoinGecko for market cap and other details
        try:
            url = "https://api.coingecko.com/api/v3/search"
            search_params = {"query": token}
            search_response = requests.get(url, params=search_params)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                coin_id = None
                
                # Find the coin with the exact symbol match
                for coin in search_data.get('coins', []):
                    if coin.get('symbol', '').upper() == token:
                        coin_id = coin.get('id')
                        break
                
                if coin_id:
                    # Get detailed information
                    coin_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                    coin_params = {"localization": "false", "tickers": "false", "market_data": "true", "community_data": "false", "developer_data": "false"}
                    coin_response = requests.get(coin_url, params=coin_params)
                    
                    if coin_response.status_code == 200:
                        coin_data = coin_response.json()
                        market_data = coin_data.get('market_data', {})
                        
                        results["coin_info"] = {
                            'name': coin_data.get('name', ''),
                            'symbol': token,
                            'price_usd': market_data.get('current_price', {}).get('usd', 0),
                            'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                            'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                            'change_24h': market_data.get('price_change_percentage_24h', 0),
                            'change_7d': market_data.get('price_change_percentage_7d', 0),
                            'rank': market_data.get('market_cap_rank', 0)
                        }
        except Exception as e:
            env.add_agent_log(f"Error fetching token info from CoinGecko: {e}")
        
        # Add a small delay
        time.sleep(0.2)
        
        # Get OKX trading data
        trading_info = search_token(token)
        if trading_info.get("status") == "success":
            results["trading_info"] = trading_info.get("results", {}).get(f"{token}-USDT", {})
        
        # Add a small delay
        time.sleep(0.2)
        
        # Get order book
        order_book = get_order_book(token)
        if order_book.get("status") == "success":
            results["order_book"] = order_book.get("order_book", {})
        
        # Add a small delay
        time.sleep(0.2)
        
        # Get historical data (1H timeframe)
        historical_data = get_historical_data(token)
        if historical_data.get("status") == "success":
            results["historical_data"] = historical_data.get("ohlcv", {})
        
        return {
            "status": "success" if results else "error",
            "message": "Comprehensive data retrieved successfully" if results else "Failed to fetch comprehensive data",
            "data": results
        }
    
    def analyze_market_sentiment(token: str) -> Dict[str, Any]:
        """
        Analyze market sentiment for a token based on various data points.
        
        Args:
            token: Token symbol (e.g., "BTC", "ETH", "IMX")
            
        Returns:
            A dictionary with market sentiment analysis
        """
        # Get comprehensive data first
        token_data = fetch_comprehensive_data(token)
        
        if token_data.get("status") != "success":
            return {
                "status": "error",
                "message": f"Failed to analyze sentiment: {token_data.get('message')}",
                "sentiment": None
            }
        
        data = token_data.get("data", {})
        
        sentiment = {
            "token": token.upper(),
            "overall": "neutral",
            "confidence": 0.5,
            "factors": [],
            "summary": ""
        }
        
        # Extract data
        coin_info = data.get("coin_info", {})
        trading_info = data.get("trading_info", {}).get("ticker", {})
        order_book = data.get("order_book", {})
        historical_data = data.get("historical_data", {})
        
        factors = []
        bullish_signals = 0
        bearish_signals = 0
        
        # Check price momentum
        change_24h = coin_info.get("change_24h", 0) or trading_info.get("change_24h", 0)
        if change_24h:
            if change_24h > 5:
                factors.append({"factor": "24h price change", "signal": "bullish", "value": f"{change_24h:.2f}%"})
                bullish_signals += 1
            elif change_24h < -5:
                factors.append({"factor": "24h price change", "signal": "bearish", "value": f"{change_24h:.2f}%"})
                bearish_signals += 1
            else:
                factors.append({"factor": "24h price change", "signal": "neutral", "value": f"{change_24h:.2f}%"})
        
        # Check 7d price change if available
        change_7d = coin_info.get("change_7d", 0)
        if change_7d:
            if change_7d > 10:
                factors.append({"factor": "7d price change", "signal": "bullish", "value": f"{change_7d:.2f}%"})
                bullish_signals += 1
            elif change_7d < -10:
                factors.append({"factor": "7d price change", "signal": "bearish", "value": f"{change_7d:.2f}%"})
                bearish_signals += 1
            else:
                factors.append({"factor": "7d price change", "signal": "neutral", "value": f"{change_7d:.2f}%"})
        
        # Check order book imbalance
        if order_book:
            bid_percentage = order_book.get("bid_percentage", 0)
            ask_percentage = order_book.get("ask_percentage", 0)
            
            if bid_percentage > ask_percentage * 1.5:  # 50% more buy pressure
                factors.append({"factor": "order book imbalance", "signal": "bullish", "value": f"Bid: {bid_percentage:.1f}%, Ask: {ask_percentage:.1f}%"})
                bullish_signals += 1
            elif ask_percentage > bid_percentage * 1.5:  # 50% more sell pressure
                factors.append({"factor": "order book imbalance", "signal": "bearish", "value": f"Bid: {bid_percentage:.1f}%, Ask: {ask_percentage:.1f}%"})
                bearish_signals += 1
            else:
                factors.append({"factor": "order book imbalance", "signal": "neutral", "value": f"Bid: {bid_percentage:.1f}%, Ask: {ask_percentage:.1f}%"})
        
        # Check volatility
        if historical_data and "volatility" in historical_data:
            volatility = historical_data.get("volatility", 0)
            if volatility > 3:  # High volatility
                factors.append({"factor": "volatility", "signal": "high", "value": f"{volatility:.2f}%"})
            elif volatility < 1:  # Low volatility
                factors.append({"factor": "volatility", "signal": "low", "value": f"{volatility:.2f}%"})
            else:
                factors.append({"factor": "volatility", "signal": "medium", "value": f"{volatility:.2f}%"})
        
        # Determine overall sentiment
        if bullish_signals > bearish_signals + 1:
            sentiment["overall"] = "bullish"
            sentiment["confidence"] = min(0.5 + (bullish_signals - bearish_signals) * 0.1, 0.9)
        elif bearish_signals > bullish_signals + 1:
            sentiment["overall"] = "bearish"
            sentiment["confidence"] = min(0.5 + (bearish_signals - bullish_signals) * 0.1, 0.9)
        else:
            sentiment["overall"] = "neutral"
            sentiment["confidence"] = 0.5
        
        sentiment["factors"] = factors
        
        # Generate summary
        summary_parts = []
        if sentiment["overall"] == "bullish":
            summary_parts.append(f"The market for {token.upper()} appears bullish with a confidence of {sentiment['confidence']*100:.0f}%.")
        elif sentiment["overall"] == "bearish":
            summary_parts.append(f"The market for {token.upper()} appears bearish with a confidence of {sentiment['confidence']*100:.0f}%.")
        else:
            summary_parts.append(f"The market for {token.upper()} appears neutral with mixed signals.")
        
        for factor in factors:
            if factor["signal"] in ["bullish", "bearish"]:
                summary_parts.append(f"{factor['factor'].capitalize()} is {factor['signal']} at {factor['value']}.")
        
        sentiment["summary"] = " ".join(summary_parts)
        
        return {
            "status": "success",
            "sentiment": sentiment
        }
    
    # Register the tools
    tool_registry.register_tool(get_top_coins)
    tool_registry.register_tool(get_top_tokens_formatted)
    tool_registry.register_tool(search_token)
    tool_registry.register_tool(search_tokens)
    tool_registry.register_tool(get_order_book)
    tool_registry.register_tool(get_historical_data)
    tool_registry.register_tool(fetch_comprehensive_data)
    tool_registry.register_tool(analyze_market_sentiment)
    
    # System prompt for the coin listing agent
    system_prompt = {
        "role": "system", 
        "content": """You are a cryptocurrency information agent that provides comprehensive data about cryptocurrencies.

You have several tools at your disposal:

1. get_top_coins - Returns data about the top N cryptocurrencies by market cap
2. get_top_tokens_formatted - Returns a nicely formatted table of the top N cryptocurrencies
3. search_token - Searches for a single token on OKX and returns trading information
4. search_tokens - Searches for multiple tokens on OKX and returns trading information
5. get_order_book - Gets the current order book for a specific token
6. get_historical_data - Gets historical OHLCV data for a specific token
7. fetch_comprehensive_data - Fetches comprehensive market data for a token by calling multiple data sources
8. analyze_market_sentiment - Analyzes market sentiment based on available data

How to handle user requests:
- For information about top coins: Call get_top_tokens_formatted
- For information about a single specific coin: Call search_token for basic info
- For information about multiple specific coins: Call search_tokens with a list
- For detailed market analysis: Call fetch_comprehensive_data or analyze_market_sentiment
- For technical questions about order book or historical data: Call the appropriate specific tool

Important:
1. When a user asks about multiple tokens (e.g., "Tell me about BTC, ETH, and SOL"), use search_tokens with a list of tokens
2. For any detailed token request, consider using fetch_comprehensive_data to get complete information
3. Always format data in a readable way and explain what it means
4. Provide actionable insights based on the data when possible

Remember that users may make financial decisions based on your information, so accuracy and clarity are essential. If you're uncertain, indicate your uncertainty clearly.
"""
    }
    
    # Get user messages
    user_messages = env.list_messages()
    answers_count = 0
    
    # If this is the first run with no messages, add a welcome message
    if not user_messages:
        welcome_message = """
        Welcome to the Crypto Market Analyzer! 
        
        I can provide you with detailed information about cryptocurrencies and markets.
        
        You can ask me for:
        - "Show me the top 10 coins by market cap"
        - "What are the current prices of BTC, ETH, and SOL?"
        - "Get detailed market data for NEAR"
        - "What's the order book for Bitcoin?"
        - "Analyze market sentiment for Ethereum"
        
        What would you like to know about the crypto markets today?
        """
        env.add_reply(welcome_message)
        env.request_user_input()
        return
    
    # Process the user's request using tools
    all_tools = tool_registry.get_all_tool_definitions()

    need_to_use_more_tools = True
    history = [system_prompt] + user_messages
    while need_to_use_more_tools and answers_count < 10:
        print("########################")
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
             You are a helpful assistant with access to tools for retrieving crypto market information. 
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
        answer = eval(need_to_use_more_tools.split("<|end_header_id|>")[1])
        need_to_use_more_tools = answer["need_tool"].lower().strip() == "yes"
        if need_to_use_more_tools:
            tool_name = answer["tool"]
            history.append({"role": "user", "content": "Call the tool " + tool_name})

    # Get the final response from the model
    final_message = env.completion(
        [system_prompt] + user_messages + [{"role": "assistant", "content": "Generate a final response based on the function calling information: " + str(env.list_messages()[-answers_count:]) + "Don't say Based on the provided information. Generate a full comprehensive response for the user on his question. Write very informatice. Don't recommend anything. You are not a financial advisor. You are a helpful assistant that should just retrive and provide information. Other agents will analyze the data and provide recommendations. Don't use function calling in your response."},]
    ).split("<|end_header_id|>")[1]
    env.add_reply(final_message)
    # Request user input for the next interaction
    env.request_user_input()

run(env)
