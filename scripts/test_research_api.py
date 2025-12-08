#!/usr/bin/env python3
"""
Test script for Research Agent API endpoints
Run this to verify all endpoints are working correctly
"""
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

BASE_URL = "http://localhost:8000"

def print_test(name):
    """Print test name"""
    print(f"\n{BLUE}Testing: {name}{RESET}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")

def test_health():
    """Test health check endpoint"""
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is {data['status']}")
            print_info(f"Database: {data['services']['database']}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_info("Make sure FastAPI is running: ./start-dev.sh")
        return False

def test_available_symbols():
    """Test get available symbols endpoint"""
    print_test("Get Available Symbols")
    try:
        response = requests.get(f"{BASE_URL}/api/research/symbols")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {data['count']} symbols")
            for symbol in data['symbols'][:3]:  # Show first 3
                print(f"  - {symbol['symbol']}: {', '.join(symbol['timeframes'])}")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_market_stats():
    """Test market statistics endpoint"""
    print_test("Get Market Statistics")
    try:
        payload = {
            "symbol": "BTCUSDT",
            "timeframe": "1h"
        }
        response = requests.post(
            f"{BASE_URL}/api/research/stats",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print_success("Statistics retrieved successfully")
            print(f"  Symbol: {stats['symbol']} ({stats['timeframe']})")
            print(f"  Candles: {stats['candle_count']:,}")
            print(f"  Avg Price: ${stats['avg_price']:,.2f}")
            print(f"  Volatility: {stats['volatility_pct']:.2f}%")
            print(f"  Price Change: {stats['price_change_pct']:+.2f}%")
            return True
        elif response.status_code == 404:
            print_error("No data found for BTCUSDT 1h")
            print_info("Fetch some data first: Check frontend or API docs")
            return False
        else:
            print_error(f"Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_save_insight():
    """Test save insight endpoint"""
    print_test("Save Research Insight")
    try:
        payload = {
            "query_text": "Test query from automated test",
            "insight_type": "general",
            "insight_summary": "This is a test insight to verify API functionality",
            "insight_detail": {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "source": "test_research_api.py"
            },
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "metadata": {
                "automated_test": True
            }
        }

        response = requests.post(
            f"{BASE_URL}/api/research/insights",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Insight saved with ID: {data['insight_id']}")
            return data['insight_id']
        else:
            print_error(f"Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_get_insights():
    """Test get insights endpoint"""
    print_test("Get Research Insights")
    try:
        response = requests.get(f"{BASE_URL}/api/research/insights?limit=5")

        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data['count']} insights")
            if data['count'] > 0:
                for insight in data['insights'][:3]:  # Show first 3
                    print(f"  #{insight['id']}: {insight['insight_type']} - {insight['insight_summary'][:50]}...")
            else:
                print_info("No insights found yet")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_query_history():
    """Test query history endpoint"""
    print_test("Get Query History")
    try:
        response = requests.get(f"{BASE_URL}/api/research/queries?limit=5")

        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data['count']} queries")
            if data['count'] > 0:
                for query in data['queries'][:3]:  # Show first 3
                    print(f"  #{query['id']}: {query['query_type']} - {query['query_text'][:50]}...")
            else:
                print_info("No queries found yet")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_log_query():
    """Test log query endpoint"""
    print_test("Log Research Query")
    try:
        payload = {
            "query": "Test query for validation",
            "query_type": "analysis"
        }

        response = requests.post(
            f"{BASE_URL}/api/research/query",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Query logged with ID: {data['query_id']}")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Research Agent API Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    results = {
        "Health Check": test_health(),
        "Available Symbols": test_available_symbols(),
        "Market Statistics": test_market_stats(),
        "Save Insight": test_save_insight() is not None,
        "Get Insights": test_get_insights(),
        "Log Query": test_log_query(),
        "Query History": test_query_history()
    }

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<40} {status}")

    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"{GREEN}All tests passed! ✓{RESET}")
        print(f"\n{GREEN}Research Agent API is working correctly!{RESET}")
        print(f"{GREEN}You can now use LangFlow or N8N workflow.{RESET}\n")
        return 0
    else:
        print(f"{RED}Some tests failed. Check the errors above.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
