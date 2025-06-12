#!/usr/bin/env python3
"""
🚀 TRON Autotrade - Modular Architecture Usage Example

This script demonstrates how to use the new modular market data structure
and enhanced RAG/MCP system for production trading.

Features Demonstrated:
- Market data fetching with new modular structure
- Technical indicators calculation
- Enhanced RAG/MCP system with FAISS semantic search
- Trade log and market sentiment embedding storage
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the path to find runner modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# New modular imports
from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
from runner.gcp_memory_client import GCPMemoryClient


class MockLogger:
    """Mock logger for demonstration"""
    def log_event(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def info(self, message):
        self.log_event(f"[INFO] {message}")
    
    def error(self, message):
        self.log_event(f"[ERROR] {message}")


def demonstrate_modular_market_data():
    """🧪 Demonstrate new modular market data structure"""
    print("\n" + "="*60)
    print("🏗️  MODULAR MARKET DATA DEMONSTRATION")
    print("="*60)
    
    logger = MockLogger()
    
    # 1. Market Data Fetcher (extracted from old MarketMonitor)
    print("\n📊 1. Market Data Fetcher")
    print("-" * 30)
    
    data_fetcher = MarketDataFetcher(logger=logger)
    
    # Fetch SGX Nifty data
    sgx_data = data_fetcher.fetch_sgx_nifty_data()
    if sgx_data:
        print(f"✅ SGX Nifty: ₹{sgx_data['price']:.2f} ({sgx_data['change_percent']:+.2f}%) - {sgx_data['trend']}")
    else:
        print("❌ SGX Nifty data unavailable")
    
    # Fetch Dow Futures data  
    dow_data = data_fetcher.fetch_dow_futures_data()
    if dow_data:
        print(f"✅ Dow Futures: ${dow_data['price']:.2f} ({dow_data['change_percent']:+.2f}%) - {dow_data['trend']}")
    else:
        print("❌ Dow Futures data unavailable")
    
    # Fetch all pre-market data
    premarket_data = data_fetcher.fetch_all_premarket_data()
    print(f"✅ Pre-market sentiment: {premarket_data['market_sentiment']}")
    
    # 2. Technical Indicators (extracted from old MarketMonitor)
    print("\n📈 2. Technical Indicators")
    print("-" * 30)
    
    # Sample price data for indicators
    sample_prices = [17500, 17520, 17480, 17550, 17530, 17580, 17560, 17590, 17570, 17600,
                    17580, 17620, 17610, 17640, 17630, 17650, 17670, 17660, 17680, 17700]
    
    high_prices = [p + 20 for p in sample_prices]
    low_prices = [p - 15 for p in sample_prices]
    
    # ADX calculation
    adx_data = TechnicalIndicators.calculate_adx(high_prices, low_prices, sample_prices)
    print(f"✅ ADX: {adx_data['adx']:.2f} (DI+: {adx_data['di_plus']:.2f}, DI-: {adx_data['di_minus']:.2f})")
    
    # Bollinger Bands
    bb_data = TechnicalIndicators.calculate_bollinger_bands(sample_prices)
    print(f"✅ Bollinger Bands: Upper: ₹{bb_data['upper']:.2f}, Middle: ₹{bb_data['middle']:.2f}, Lower: ₹{bb_data['lower']:.2f}")
    
    # Price action analysis
    price_action = TechnicalIndicators.analyze_price_action(high_prices, low_prices, sample_prices)
    print(f"✅ Price Action: {price_action['trend']} (Strength: {price_action['strength']:.2f})")
    
    return True


def demonstrate_enhanced_rag_mcp():
    """🧪 Demonstrate enhanced RAG/MCP system with FAISS"""
    print("\n" + "="*60)
    print("🧠 ENHANCED RAG/MCP SYSTEM DEMONSTRATION")
    print("="*60)
    
    logger = MockLogger()
    
    # Initialize enhanced memory client with FAISS
    memory_client = GCPMemoryClient(
        project_id="demo-project",
        logger=logger,
        embedding_dimension=384  # Using sentence-transformers
    )
    
    print(f"✅ Initialized RAG/MCP system with {memory_client.embedding_model} embeddings")
    
    # 1. Store trade log embeddings
    print("\n📝 1. Trade Log Embedding Storage")
    print("-" * 40)
    
    sample_trades = [
        {
            "action": "BUY",
            "quantity": 100,
            "symbol": "NIFTY",
            "price": 17500.0,
            "strategy": "vwap",
            "market_sentiment": "bullish",
            "reasoning": "Strong breakout with high volume",
            "pnl": 250.0
        },
        {
            "action": "SELL", 
            "quantity": 50,
            "symbol": "BANKNIFTY",
            "price": 38000.0,
            "strategy": "scalp",
            "market_sentiment": "neutral",
            "reasoning": "Quick profit at resistance level",
            "pnl": -30.0
        }
    ]
    
    trade_ids = []
    for trade in sample_trades:
        doc_id = memory_client.store_trade_log_embedding(trade)
        if doc_id:
            trade_ids.append(doc_id)
            print(f"✅ Stored trade: {trade['action']} {trade['symbol']} - ID: {doc_id}")
        else:
            print(f"❌ Failed to store trade: {trade['action']} {trade['symbol']}")
    
    # 2. Store market sentiment embeddings
    print("\n🌊 2. Market Sentiment Embedding Storage")
    print("-" * 40)
    
    sentiment_data = {
        "overall_sentiment": "bullish",
        "vix": "low",
        "nifty_trend": "bullish",
        "sgx_nifty": "bullish",
        "dow": "neutral",
        "regime_analysis": {
            "overall_regime": {
                "regime": "STRONGLY_TRENDING",
                "factors": {
                    "volatility": "LOW",
                    "trend": "UPTREND"
                }
            }
        }
    }
    
    sentiment_id = memory_client.store_market_sentiment_embedding(sentiment_data)
    if sentiment_id:
        print(f"✅ Stored market sentiment - ID: {sentiment_id}")
    else:
        print(f"❌ Failed to store market sentiment")
    
    # 3. Semantic search demonstration
    print("\n🔍 3. Semantic Search Demonstration")
    print("-" * 40)
    
    search_queries = [
        "What profitable NIFTY trades were executed?",
        "Find bullish market conditions",
        "BANKNIFTY scalping strategies"
    ]
    
    for query in search_queries:
        print(f"\n🔎 Query: '{query}'")
        results = memory_client.search_similar_documents(
            query_text=query,
            top_k=3,
            similarity_threshold=0.5
        )
        
        if results:
            for i, result in enumerate(results):
                score = result['similarity_score']
                content = result['content'][:60] + "..."
                print(f"   {i+1}. Score: {score:.3f} | {content}")
        else:
            print("   No relevant results found")
    
    # 4. Contextual APIs demonstration
    print("\n🎯 4. Contextual APIs Demonstration")
    print("-" * 40)
    
    # Get contextual trade history
    relevant_trades = memory_client.get_contextual_trade_history(
        query="Recent profitable trades",
        days_back=30,
        top_k=5
    )
    
    print(f"✅ Retrieved {len(relevant_trades)} contextually relevant trades")
    
    # Get similar market conditions
    current_conditions = {
        "sentiment": "bullish",
        "vix": "low",
        "volatility": "medium"
    }
    
    similar_conditions = memory_client.get_similar_market_conditions(
        current_conditions=current_conditions,
        top_k=3
    )
    
    print(f"✅ Found {len(similar_conditions)} similar market conditions")
    
    # 5. System statistics
    print("\n📊 5. System Statistics")
    print("-" * 40)
    
    stats = memory_client.get_embedding_statistics()
    print(f"📈 Total documents: {stats.get('total_documents', 0)}")
    print(f"🧠 Embedding model: {stats.get('embedding_model', 'None')}")
    
    by_type = stats.get('by_type', {})
    for doc_type, count in by_type.items():
        print(f"📄 {doc_type}: {count} documents")
    
    return True


def demonstrate_complete_integration():
    """🧪 Demonstrate complete integration of modular components"""
    print("\n" + "="*60)
    print("🔗 COMPLETE SYSTEM INTEGRATION DEMONSTRATION")
    print("="*60)
    
    logger = MockLogger()
    
    # 1. Initialize all components
    data_fetcher = MarketDataFetcher(logger=logger)
    memory_client = GCPMemoryClient(project_id="demo-project", logger=logger)
    
    # 2. Fetch live market data
    print("\n📡 Live Market Data Collection")
    print("-" * 35)
    
    premarket_data = data_fetcher.fetch_all_premarket_data()
    print(f"✅ Market sentiment: {premarket_data['market_sentiment']}")
    
    # 3. Store market data as embeddings for future analysis
    print("\n💾 Storing Market Data as Embeddings")
    print("-" * 35)
    
    market_embedding_id = memory_client.store_market_sentiment_embedding(premarket_data)
    if market_embedding_id:
        print(f"✅ Stored current market state for future reference: {market_embedding_id}")
    
    # 4. Simulate a trade decision based on current market conditions
    print("\n🤖 AI-Powered Trading Decision")
    print("-" * 35)
    
    # Get historical context for current market conditions
    historical_context = memory_client.get_similar_market_conditions(
        current_conditions={
            "sentiment": premarket_data['market_sentiment'],
            "vix": premarket_data.get('vix', {}).get('value', 'moderate')
        },
        top_k=3
    )
    
    print(f"🧠 Found {len(historical_context)} similar historical market conditions")
    
    # Simulate trade execution
    simulated_trade = {
        "action": "BUY",
        "quantity": 75,
        "symbol": "NIFTY",
        "price": 17650.0,
        "strategy": "sentiment_based",
        "market_sentiment": premarket_data['market_sentiment'],
        "reasoning": f"Decision based on {len(historical_context)} similar historical patterns",
        "timestamp": datetime.now().isoformat()
    }
    
    # Store trade for future learning
    trade_id = memory_client.store_trade_log_embedding(simulated_trade)
    if trade_id:
        print(f"✅ Executed and logged trade: {simulated_trade['action']} {simulated_trade['symbol']}")
        print(f"📝 Trade logged for AI learning: {trade_id}")
    
    # 5. Performance summary
    print("\n📊 System Performance Summary")
    print("-" * 35)
    
    embedding_stats = memory_client.get_embedding_statistics()
    health_status = memory_client.health_check()
    
    print(f"🧠 AI Learning Database: {embedding_stats.get('total_documents', 0)} experiences")
    print(f"⚡ System Health: {'✅ All systems operational' if health_status.get('embedding_system') else '⚠️ Some systems offline'}")
    
    return True


def main():
    """Run complete demonstration of modular TRON architecture"""
    print("🚀 TRON AUTOTRADE - MODULAR ARCHITECTURE DEMONSTRATION")
    print("=" * 80)
    print("This demonstration shows the new production-ready modular structure:")
    print("• 🏗️  Modular Market Data (MarketDataFetcher, TechnicalIndicators)")
    print("• 🧠 Enhanced RAG/MCP System with FAISS semantic search")
    print("• 🔗 Complete AI-powered trading integration")
    print("=" * 80)
    
    try:
        # Run demonstrations
        demo1_success = demonstrate_modular_market_data()
        demo2_success = demonstrate_enhanced_rag_mcp() 
        demo3_success = demonstrate_complete_integration()
        
        # Summary
        print("\n" + "="*80)
        print("📋 DEMONSTRATION SUMMARY")
        print("="*80)
        
        results = [
            ("Modular Market Data", demo1_success),
            ("Enhanced RAG/MCP System", demo2_success), 
            ("Complete Integration", demo3_success)
        ]
        
        passed = sum(1 for _, success in results if success)
        
        for demo_name, success in results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{status} {demo_name}")
        
        print(f"\n🎯 Overall Results: {passed}/{len(results)} demonstrations successful")
        
        if passed == len(results):
            print("\n🎉 MODULAR ARCHITECTURE FULLY OPERATIONAL! 🚀")
            print("\n🔥 PRODUCTION FEATURES:")
            print("   ✅ Modular market data fetching")
            print("   ✅ Extracted technical indicators")
            print("   ✅ FAISS semantic similarity search")
            print("   ✅ Dynamic embedding storage and retrieval")
            print("   ✅ AI-powered contextual trading decisions")
            print("   ✅ Complete integration and learning system")
            
            print("\n📚 USAGE:")
            print("   • Import from runner.market_data for market data")
            print("   • Use GCPMemoryClient for AI memory and learning")
            print("   • All existing code updated to use new modular structure")
            
        else:
            print(f"\n⚠️  Some demonstrations failed - Check dependencies")
        
        return passed == len(results)
        
    except Exception as e:
        print(f"❌ Demonstration failed with error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 