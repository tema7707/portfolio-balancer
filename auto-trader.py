#!/usr/bin/env python3
import subprocess
import json
import re
import os
import time
import sys
import requests
import hmac
import base64
import hashlib
import signal
import datetime
import traceback
from datetime import datetime
from typing import Dict, Any

class OKXClient:
    """
    Client for interacting with the OKX API
    """
    
    def __init__(self, api_key=None, api_secret=None, passphrase=None, is_demo=True):
        """
        Initialize the OKX client
        
        Args:
            api_key: OKX API key
            api_secret: OKX API secret
            passphrase: OKX API passphrase
            is_demo: Whether to use the demo trading account
        """
        # Get API credentials from environment variables if not provided
        self.api_key = api_key or os.environ.get("OKX_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("OKX_API_SECRET", "")
        self.passphrase = passphrase or os.environ.get("OKX_API_PASSPHRASE", "")
        self.is_demo = is_demo
        
        # Base URL
        self.base_url = "https://www.okx.com"
        
        # Check if credentials are available
        self.has_credentials = bool(self.api_key and self.api_secret and self.passphrase)
    
    def _generate_signature(self, timestamp, method, request_path, body=''):
        """
        Generate OKX API signature for authentication
        """
        if str(body) == '{}' or str(body) == 'None':
            body = ''
        
        # Construct the message string exactly as OKX expects
        message = timestamp + method + request_path + (body if body else '')
        
        # Print the pre-signature message for debugging
        print(f"DEBUG - Signature message: {message}")
        
        # Create signature
        mac = hmac.new(
            bytes(self.api_secret, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod=hashlib.sha256
        )
        
        d = mac.digest()
        signature = base64.b64encode(d).decode('utf-8')
        return signature
    
    def _request(self, method, endpoint, params=None, data=None):
        """
        Make a request to the OKX API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response
        """
        if not self.has_credentials:
            return {
                "status": "error",
                "message": "API credentials not available. Please set OKX_API_KEY, OKX_API_SECRET, and OKX_API_PASSPHRASE environment variables."
            }
        
        # Prepare URL
        url = self.base_url + endpoint
        
        # Convert data to JSON string if provided
        body = json.dumps(data) if data else ''
        
        # Prepare request headers with authentication
        timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
        signature = self._generate_signature(timestamp, method, endpoint, body)
        
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
        
        # For demo accounts, add the demo flag
        if self.is_demo:
            headers["x-simulated-trading"] = "1"
        
        # Print debug info
        print(f"DEBUG - Request URL: {url}")
        print(f"DEBUG - Request headers: {headers}")
        if data:
            print(f"DEBUG - Request data: {data}")
        
        # Make request to OKX API
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported HTTP method: {method}"
                }
            
            # Print response details for debugging
            print(f"DEBUG - Response status: {response.status_code}")
            print(f"DEBUG - Response text: {response.text[:500]}")
            
            # Parse response
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if OKX API returned an error
                if response_data.get("code") != "0":
                    return {
                        "status": "error",
                        "message": f"OKX API error: {response_data.get('msg')}",
                        "data": response_data
                    }
                
                return {
                    "status": "success",
                    "data": response_data.get("data", {}),
                    "message": "Request successful"
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP error {response.status_code}: {response.text}",
                    "http_status": response.status_code
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def get_account_balance(self):
        """
        Get account balance from OKX
        
        Returns:
            Dictionary with account balance information
        """
        endpoint = "/api/v5/account/balance"
        return self._request("GET", endpoint)
    
    def place_market_order(self, coin, action, amount_usd):
        """
        Place a market order on OKX
        
        Args:
            coin: Coin symbol (e.g., "BTC")
            action: "buy" or "sell"
            amount_usd: Amount in USD to buy or sell
            
        Returns:
            Dictionary with order information
        """
        # Ensure action is lowercase
        action = action.lower()
        
        if action not in ["buy", "sell"]:
            return {
                "status": "error",
                "message": f"Invalid action: {action}. Must be 'buy' or 'sell'."
            }
        
        # Format trading pair
        trading_pair = f"{coin}-USDT"
        
        # For OKX, side is 'buy' or 'sell'
        side = action
        
        # Prepare order data - CORRECTED FORMAT
        if action == "buy":
            order_data = {
                "instId": trading_pair,
                "tdMode": "cash",
                "side": side,
                "ordType": "market",
                "sz": str(amount_usd),
                "ccy": "USDT"  # Use ccy instead of tgtCcy
            }
        else:  # for sell orders
            order_data = {
                "instId": trading_pair,
                "tdMode": "cash",
                "side": side,
                "ordType": "market",
                "sz": str(amount_usd)
            }
            
        # Place the order
        endpoint = "/api/v5/trade/order"
        result = self._request("POST", endpoint, data=order_data)
        
        if result.get("status") == "success":
            # Access the first item in the data list
            order_data = result.get("data", [])
            if order_data and isinstance(order_data, list) and len(order_data) > 0:
                order_info = order_data[0]  # Get the first order info
                return {
                    "status": "success",
                    "message": "Order placed successfully",
                    "details": {
                        "order_id": order_info.get("ordId"),
                        "client_order_id": order_info.get("clOrdId"),
                        "message": order_info.get("sMsg"),
                        "timestamp": order_info.get("ts")
                    }
                }
            else:
                return {
                    "status": "success",
                    "message": "Order placed, but no detailed information returned",
                    "details": result.get("data")
                }
        
        return result  # Return the original result if not successful


class PortfolioExecutor:
    """
    Handles interactions with the portfolio manager agent and executes trading recommendations
    """
    
    def __init__(self, agent_path: str = None, okx_client=None):
        """
        Initialize the executor with the path to the agent
        
        Args:
            agent_path: Path to the agent, defaults to temazzz.near/portfolio-manager/0.0.1
            okx_client: OKX client for executing trades
        """
        self.agent_path = agent_path or "temazzz.near/portfolio-manager/0.0.1"
        self.last_recommendation = None
        self.debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
        
        # Initialize OKX client if not provided
        self.okx_client = okx_client or OKXClient(
            is_demo=os.environ.get("OKX_DEMO", "true").lower() == "true"
        )
    
    def send_query(self, query: str) -> dict:
        """
        Send a query to the portfolio manager agent and extract the recommendation
        
        Args:
            query: The query to send to the agent
            
        Returns:
            A dictionary with the recommendation
        """
        try:
            # Format the query to specifically request a trade recommendation
            if "recommend" not in query.lower():
                enhanced_query = f"{query}. Please analyze and provide a trade recommendation."
            else:
                enhanced_query = query
                
            # Build the command to run the agent
            cmd = ["nearai", "agent", "interactive", self.agent_path, "--local"]
            
            print(f"Starting agent with command: {' '.join(cmd)}")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Wait for the agent to initialize
            output = ""
            ready_timeout = 60  # Increased timeout for initialization
            start_time = time.time()
            agent_ready = False
            
            print("Waiting for agent to initialize...")
            
            # Collect initial output until ready prompt
            while (time.time() - start_time) < ready_timeout:
                if process.poll() is not None:
                    # Process exited prematurely
                    stderr = process.stderr.read()
                    error_msg = f"Agent process exited unexpectedly. Exit code: {process.returncode}. Stderr: {stderr}"
                    print(error_msg)
                    return {"status": "error", "message": error_msg}
                
                # Check if there's output available
                line = process.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                output += line
                
                # Print initialization line
                print(f"INIT: {line.strip()}")
                
                # Check for various indicators that the agent is ready
                if ">" in line or line.strip() == ">" or line.endswith("> ") or "Type 'multiline' to enter multiline mode" in line:
                    agent_ready = True
                    print("Agent is ready to receive input.")
                    break
            
            if not agent_ready:
                error_msg = "Agent initialization timed out or failed."
                print(error_msg)
                process.terminate()
                return {"status": "error", "message": error_msg}
            
            if self.debug_mode:
                print("Initialization output:")
                print(output)
            
            # Add a short delay to ensure agent is ready for input
            time.sleep(1)
            
            # Send the query
            print(f"Sending enhanced query: {enhanced_query}")
            try:
                process.stdin.write(enhanced_query + "\n")
                process.stdin.flush()
            except BrokenPipeError as e:
                error_msg = f"Failed to send query: {str(e)}. The agent process may have terminated unexpectedly."
                print(error_msg)
                return {"status": "error", "message": error_msg}
            except Exception as e:
                error_msg = f"Error sending query: {str(e)}"
                print(error_msg)
                return {"status": "error", "message": error_msg}
            
            # Collect the full response
            print("Waiting for response. This may take several minutes...")
            full_response = ""
            json_str = None
            final_decision_marker = False
            json_collection = ""
            
            # Set a timeout for collecting the response
            response_timeout = 600  # 10 minutes timeout for response
            start_time = time.time()
            
            while (time.time() - start_time) < response_timeout:
                if process.poll() is not None:
                    # Process exited unexpectedly
                    print(f"Agent process exited with code {process.returncode}")
                    break
                
                line = process.stdout.readline()
                if not line:
                    # Check if we're already collecting JSON after the final decision marker
                    if final_decision_marker and json_collection:
                        # Check if we have a complete JSON object
                        if json_collection.count("{") == json_collection.count("}") and json_collection.strip().endswith("}"):
                            print("JSON collection appears complete, breaking...")
                            break
                    
                    time.sleep(0.1)
                    continue
                
                stripped_line = line.strip()
                print(f"RESPONSE: {stripped_line}")
                full_response += line
                
                # Look for "Final desision:" marker
                if "Final desision:" in stripped_line:
                    print("Found 'Final desision:' marker.")
                    final_decision_marker = True
                    continue
                
                # If we've found the marker, start collecting JSON
                if final_decision_marker:
                    json_collection += stripped_line
                    # Check if we have a complete JSON object
                    if "{" in json_collection and "}" in json_collection:
                        # Extract the JSON
                        json_match = re.search(r'{.*}', json_collection, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            print(f"Found JSON after 'Final desision:': {json_str}")
                            try:
                                # Validate that it parses correctly
                                parsed_json = json.loads(json_str)
                                if all(k in parsed_json for k in ["action", "coin", "amount_usd"]):
                                    print("JSON is valid, breaking...")
                                    break
                            except json.JSONDecodeError:
                                # Not complete yet, keep collecting
                                pass
                
                # If not found yet and this is a JSON line, check it
                if not json_str and not final_decision_marker:
                    # Check for JSON in the line
                    json_candidates = re.findall(r'{.*?}', stripped_line)
                    for candidate in json_candidates:
                        try:
                            parsed_json = json.loads(candidate)
                            if all(k in parsed_json for k in ["action", "coin", "amount_usd"]):
                                json_str = candidate
                                print(f"Found JSON in response: {json_str}")
                                break
                        except json.JSONDecodeError:
                            continue
                    
                    if json_str:
                        break
            
            # If we haven't found a JSON yet, scan the entire response
            if not json_str:
                print("Scanning entire response for recommendation...")
                
                # Look for the specific pattern we've seen in the example
                pattern = r'Final desision:\s*\n*\s*{\s*\n*\s*"action":\s*"([^"]+)"\s*,\s*\n*\s*"coin":\s*"([^"]+)"\s*,\s*\n*\s*"amount_usd":\s*(\d+\.?\d*)\s*\n*\s*}'
                match = re.search(pattern, full_response, re.DOTALL | re.IGNORECASE)
                
                if match:
                    action = match.group(1)
                    coin = match.group(2)
                    amount_usd = float(match.group(3))
                    
                    recommendation = {
                        "action": action,
                        "coin": coin,
                        "amount_usd": amount_usd
                    }
                    
                    json_str = json.dumps(recommendation)
                    print(f"Extracted recommendation from pattern: {json_str}")
                else:
                    # Try a more general approach
                    pattern = r'"action"\s*:\s*"([^"]+)"\s*,\s*"coin"\s*:\s*"([^"]+)"\s*,\s*"amount_usd"\s*:\s*(\d+\.?\d*)'
                    match = re.search(pattern, full_response)
                    
                    if match:
                        action = match.group(1)
                        coin = match.group(2)
                        amount_usd = float(match.group(3))
                        
                        recommendation = {
                            "action": action,
                            "coin": coin,
                            "amount_usd": amount_usd
                        }
                        
                        json_str = json.dumps(recommendation)
                        print(f"Extracted recommendation from text: {json_str}")
            
            # Try to terminate the agent process
            try:
                print("Sending exit command...")
                process.stdin.write("exit\n")
                process.stdin.flush()
            except:
                pass
            
            # Kill the process if it's still running
            if process.poll() is None:
                print("Terminating agent process...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("Process did not terminate, killing it...")
                    process.kill()
            
            if json_str:
                try:
                    recommendation = json.loads(json_str)
                    self.last_recommendation = recommendation
                    
                    if self.debug_mode:
                        print("Found JSON recommendation:")
                        print(json.dumps(recommendation, indent=2))
                    
                    return {
                        "status": "success",
                        "recommendation": recommendation,
                        "full_response": full_response
                    }
                except json.JSONDecodeError as e:
                    return {
                        "status": "error",
                        "message": f"Found JSON-like text but couldn't parse it: {str(e)}",
                        "json_str": json_str,
                        "full_response": full_response
                    }
            else:
                # Try to synthesize a recommendation from the response text
                print("No JSON found, attempting to synthesize a recommendation from response text...")
                # Look for mentions of coins with "BUY" nearby
                coins_to_check = ["BTC", "ETH", "DOGE", "SHIB", "PEPE", "DOT", "AXS", "SOL", "BNB", "XRP"]
                
                # First look for explicit buy recommendations
                for coin in coins_to_check:
                    pattern = r'(?i)(?:buy|buying|purchase)\s+(?:some)?\s*' + re.escape(coin)
                    if re.search(pattern, full_response):
                        # Look for an amount
                        amount_pattern = r'(?i)(?:amount|cost|value|worth|)\s*(?:of)?\s*(?:\$|USD)?\s*(\d+(?:\.\d+)?)'
                        amount_match = re.search(amount_pattern, full_response)
                        amount = 500.0  # Default
                        if amount_match:
                            try:
                                amount = float(amount_match.group(1))
                            except:
                                pass
                        
                        print(f"Found buy recommendation for {coin} with amount ${amount}")
                        synthesized_recommendation = {
                            "action": "BUY",
                            "coin": coin,
                            "amount_usd": amount
                        }
                        self.last_recommendation = synthesized_recommendation
                        return {
                            "status": "success",
                            "recommendation": synthesized_recommendation,
                            "full_response": full_response,
                            "note": "This recommendation was synthesized from the response text as no complete JSON was found"
                        }
                
                # If no explicit recommendations, look for coin mentions
                for coin in coins_to_check:
                    if coin in full_response:
                        print(f"Found mentioned coin: {coin}")
                        synthesized_recommendation = {
                            "action": "BUY",
                            "coin": coin,
                            "amount_usd": 500.0
                        }
                        self.last_recommendation = synthesized_recommendation
                        return {
                            "status": "success",
                            "recommendation": synthesized_recommendation,
                            "full_response": full_response,
                            "note": "This recommendation was synthesized from coin mentions as no complete JSON was found"
                        }
                
                if self.debug_mode:
                    print("No valid JSON found. Full response:")
                    print(full_response)
                
                return {
                    "status": "error",
                    "message": "No valid recommendation found in agent response",
                    "full_response": full_response
                }
        
        except Exception as e:
            error_message = f"Error interacting with agent: {str(e)}"
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": error_message
            }
    
    def execute_recommendation(self, recommendation: dict = None, simulate: bool = False) -> dict:
        """
        Execute a trading recommendation using OKX API
        
        Args:
            recommendation: The recommendation to execute, defaults to the last recommendation
            simulate: If True, only simulate the execution
            
        Returns:
            A dictionary with the execution result
        """
        recommendation = recommendation or self.last_recommendation
        
        if not recommendation:
            return {
                "status": "error",
                "message": "No recommendation to execute"
            }
        
        action = recommendation.get("action", "").upper()
        coin = recommendation.get("coin", "")
        amount_usd = recommendation.get("amount_usd", 0)
        
        if not action or not coin or amount_usd <= 0:
            return {
                "status": "error",
                "message": "Invalid recommendation format"
            }
        
        # Print execution details
        print(f"\n{'=' * 50}")
        print(f"ORDER DETAILS:")
        print(f"Action: {action}")
        print(f"Coin: {coin}")
        print(f"Amount: ${amount_usd:.2f}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # If simulating, don't actually execute the trade
        if simulate:
            print(f"Status: SIMULATED (No actual trade executed)")
            print(f"{'=' * 50}\n")
            
            return {
                "status": "success",
                "message": f"Simulated {action} order for {coin} of ${amount_usd:.2f} USD",
                "details": {
                    "action": action,
                    "coin": coin,
                    "amount_usd": amount_usd,
                    "execution_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "execution_status": "SIMULATED"
                }
            }
        
        # Check if OKX client has credentials
        if not self.okx_client.has_credentials:
            print(f"Status: FAILED (Missing API credentials)")
            print(f"{'=' * 50}\n")
            return {
                "status": "error",
                "message": "OKX API credentials not available. Please set OKX_API_KEY, OKX_API_SECRET, and OKX_API_PASSPHRASE environment variables."
            }
        
        # Execute the trade using OKX API
        try:
            print(f"Status: EXECUTING (Live trade on OKX)")
            print(f"{'=' * 50}\n")
            
            # Place the order
            result = self.okx_client.place_market_order(coin, action.lower(), amount_usd)
            
            if result.get("status") == "success":
                order_details = result.get("details", {})
                print(f"Trade executed successfully!")
                print(f"Order ID: {order_details.get('order_id', 'Unknown')}")
                
                return {
                    "status": "success",
                    "message": f"Executed {action} order for {coin} of ${amount_usd:.2f} USD",
                    "details": {
                        "action": action,
                        "coin": coin,
                        "amount_usd": amount_usd,
                        "execution_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "execution_status": "EXECUTED",
                        "order_id": order_details.get("order_id"),
                        "raw_response": order_details
                    }
                }
            else:
                print(f"Trade execution failed: {result.get('message')}")
                return {
                    "status": "error",
                    "message": f"Failed to execute {action} order for {coin}: {result.get('message')}",
                    "details": result
                }
                
        except Exception as e:
            print(f"Trade execution failed with exception: {str(e)}")
            return {
                "status": "error",
                "message": f"Exception during trade execution: {str(e)}"
            }


class AutoTrader:
    """
    Automated trading system that runs the portfolio manager on a schedule
    """
    
    def __init__(self, query, interval_minutes=5, agent_path=None, simulate=False):
        """
        Initialize the auto trader
        
        Args:
            query: The query to send to the portfolio manager
            interval_minutes: How often to run the trader in minutes
            agent_path: Path to the agent
            simulate: Whether to simulate trades or execute them
        """
        self.query = query
        self.interval_minutes = interval_minutes
        self.simulate = simulate
        self.running = False
        self.trade_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        
        # Initialize the executor
        self.okx_client = OKXClient(
            is_demo=os.environ.get("OKX_DEMO", "true").lower() == "true"
        )
        self.executor = PortfolioExecutor(agent_path, self.okx_client)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        # Check OKX credentials
        if not self.okx_client.has_credentials and not simulate:
            print("\n⚠️ OKX API credentials not available. Forcing simulation mode.")
            self.simulate = True
    
    def handle_shutdown(self, signum, frame):
        """
        Handle shutdown signals
        """
        print("\n\nReceived shutdown signal. Stopping auto trader...")
        self.running = False
    
    def run(self):
        """
        Run the auto trader in a loop
        """
        self.running = True
        self.start_time = time.time()
        
        print(f"\n{'=' * 70}")
        print(f"STARTING AUTOMATED TRADING")
        print(f"Query: {self.query}")
        print(f"Interval: {self.interval_minutes} minutes")
        print(f"Mode: {'SIMULATION' if self.simulate else 'LIVE TRADING'}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 70}\n")
        
        while self.running:
            cycle_start = time.time()
            
            try:
                self.trade_count += 1
                
                print(f"\n{'#' * 70}")
                print(f"TRADE CYCLE #{self.trade_count}")
                print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'#' * 70}\n")
                
                # Request recommendation from the agent
                print("Requesting recommendation from portfolio manager...")
                result = self.executor.send_query(self.query)
                
                if result.get("status") == "success":
                    recommendation = result.get("recommendation")
                    
                    # Check if this was a synthesized recommendation
                    if "note" in result:
                        print(f"\n⚠️ {result['note']}")
                    
                    print("\nReceived recommendation:")
                    print(json.dumps(recommendation, indent=2))
                    
                    # Execute the recommendation
                    print("\nExecuting recommendation automatically...")
                    execution_result = self.executor.execute_recommendation(recommendation, self.simulate)
                    
                    if execution_result.get("status") == "success":
                        self.success_count += 1
                        print(f"Success: {execution_result.get('message')}")
                    else:
                        self.error_count += 1
                        print(f"Error: {execution_result.get('message')}")
                else:
                    self.error_count += 1
                    print(f"\nError getting recommendation: {result.get('message')}")
            
            except Exception as e:
                self.error_count += 1
                print(f"\n{'!' * 70}")
                print(f"ERROR IN TRADE CYCLE: {str(e)}")
                print(f"Stack trace:")
                traceback.print_exc()
                print(f"{'!' * 70}\n")
                print("Error caught, continuing with next cycle after interval...")
            
            # Calculate how long the cycle took and sleep until the next cycle
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, self.interval_minutes * 60 - cycle_duration)
            
            # Print status summary
            run_time = time.time() - self.start_time
            hours = int(run_time // 3600)
            minutes = int((run_time % 3600) // 60)
            seconds = int(run_time % 60)
            
            print(f"\n{'=' * 70}")
            print(f"CYCLE SUMMARY:")
            print(f"Cycle #{self.trade_count} completed in {cycle_duration:.1f} seconds")
            print(f"Total running time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            print(f"Success rate: {self.success_count}/{self.trade_count} ({(self.success_count/self.trade_count*100) if self.trade_count > 0 else 0:.1f}%)")
            print(f"Next cycle will start in {int(sleep_time)} seconds...")
            print(f"{'=' * 70}\n")
            
            if sleep_time > 0 and self.running:
                try:
                    time.sleep(sleep_time)
                except KeyboardInterrupt:
                    print("\nSleep interrupted. Shutting down...")
                    self.running = False
        
        # Print final status when stopped
        run_time = time.time() - self.start_time
        hours = int(run_time // 3600)
        minutes = int((run_time % 3600) // 60)
        seconds = int(run_time % 60)
        
        print(f"\n{'=' * 70}")
        print(f"AUTO TRADER STOPPED")
        print(f"Total running time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"Total trade cycles: {self.trade_count}")
        print(f"Successful trades: {self.success_count}")
        print(f"Failed trades: {self.error_count}")
        print(f"Success rate: {(self.success_count/self.trade_count*100) if self.trade_count > 0 else 0:.1f}%")
        print(f"{'=' * 70}\n")



def main():
    """
    Main function to run the auto trader
    """
    # Set debug mode from environment or command line
    if "--debug" in sys.argv:
        os.environ["DEBUG_MODE"] = "true"
        sys.argv.remove("--debug")
    
    # Check for simulate flag
    simulate = False
    if "--simulate" in sys.argv:
        simulate = True
        sys.argv.remove("--simulate")
    
    # Check for interval flag
    interval_minutes = 5  # Default interval
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--interval" and i < len(sys.argv) - 1:
            try:
                interval_minutes = int(sys.argv[i + 1])
                # Remove these arguments
                sys.argv.pop(i)  # Remove --interval
                sys.argv.pop(i)  # Remove the value
                break
            except ValueError:
                print(f"Invalid interval value: {sys.argv[i + 1]}. Using default of 5 minutes.")
    
    # Check for specific agent version
    agent_path = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--agent" and i < len(sys.argv) - 1:
            agent_path = sys.argv[i + 1]
            # Remove these arguments
            sys.argv.pop(i)  # Remove --agent
            sys.argv.pop(i)  # Remove the path
            break
    
    # Set mode based on OKX credentials availability
    if not simulate and not (os.environ.get("OKX_API_KEY") and 
                              os.environ.get("OKX_API_SECRET") and 
                              os.environ.get("OKX_API_PASSPHRASE")):
        print("\\n⚠️ OKX API credentials not found in environment variables.")
        print("Running in simulation mode. For real trading, please set OKX_API_KEY, OKX_API_SECRET, and OKX_API_PASSPHRASE.\\n")
        simulate = True
    
    # Get query from command line arguments or prompt user
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("Enter your query for the portfolio manager (this will be used for all trading cycles):")
        query = input("> ")
    
    # Initialize the auto trader
    auto_trader = AutoTrader(
        query=query,
        interval_minutes=interval_minutes,
        agent_path=agent_path,
        simulate=simulate
    )
    
    print(f"\\nStarting automated trading with '{query}'")
    print(f"Will run every {interval_minutes} minutes in {'SIMULATION' if simulate else 'LIVE TRADING'} mode.")
    print("Press Ctrl+C to stop the auto trader.")
    
    # Run the auto trader
    try:
        auto_trader.run()
    except KeyboardInterrupt:
        print("\\nKeyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"\\nUnexpected error: {str(e)}")
        traceback.print_exc()
    
    print("Auto trader stopped.")


def main():
    """
    Main function to run the auto trader
    """
    # Set debug mode from environment or command line
    if "--debug" in sys.argv:
        os.environ["DEBUG_MODE"] = "true"
        sys.argv.remove("--debug")
    
    # Check for simulate flag
    simulate = False
    if "--simulate" in sys.argv:
        simulate = True
        sys.argv.remove("--simulate")
    
    # Check for interval flag
    interval_minutes = 5  # Default interval
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--interval" and i < len(sys.argv) - 1:
            try:
                interval_minutes = int(sys.argv[i + 1])
                # Remove these arguments
                sys.argv.pop(i)  # Remove --interval
                sys.argv.pop(i)  # Remove the value
                break
            except ValueError:
                print(f"Invalid interval value: {sys.argv[i + 1]}. Using default of 5 minutes.")
    
    # Check for specific agent version
    agent_path = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--agent" and i < len(sys.argv) - 1:
            agent_path = sys.argv[i + 1]
            # Remove these arguments
            sys.argv.pop(i)  # Remove --agent
            sys.argv.pop(i)  # Remove the path
            break
    
    # Set mode based on OKX credentials availability
    if not simulate and not (os.environ.get("OKX_API_KEY") and 
                              os.environ.get("OKX_API_SECRET") and 
                              os.environ.get("OKX_API_PASSPHRASE")):
        print("\n⚠️ OKX API credentials not found in environment variables.")
        print("Running in simulation mode. For real trading, please set OKX_API_KEY, OKX_API_SECRET, and OKX_API_PASSPHRASE.\n")
        simulate = True
    
    # Get query from command line arguments or prompt user
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("Enter your query for the portfolio manager (this will be used for all trading cycles):")
        query = input("> ")
    
    # Initialize the auto trader
    auto_trader = AutoTrader(
        query=query,
        interval_minutes=interval_minutes,
        agent_path=agent_path,
        simulate=simulate
    )
    
    print(f"\nStarting automated trading with '{query}'")
    print(f"Will run every {interval_minutes} minutes in {'SIMULATION' if simulate else 'LIVE TRADING'} mode.")
    print("Press Ctrl+C to stop the auto trader.")
    
    # Run the auto trader
    try:
        auto_trader.run()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        traceback.print_exc()
    
    print("Auto trader stopped.")

if __name__ == "__main__":
    main()