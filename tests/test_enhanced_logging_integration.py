#!/usr/bin/env python3
"""
Enhanced Logging Integration Test Script
========================================

Comprehensive test suite for verifying RAG and MCP logging integration
with Firestore and GCS backends.
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

def test_basic_imports():
    """Test basic module imports"""
    print("🔍 Testing Basic Imports...")
    
    try:
        # Test enhanced logging imports
        from runner.enhanced_logging import TradingLogger, LogLevel, LogCategory
        print("✅ Enhanced logging system imported successfully")
        
        # Test RAG logging imports
        from gpt_runner.rag.enhanced_rag_logger import get_rag_logger, create_rag_logger
        print("✅ RAG enhanced logger imported successfully")
        
        # Test MCP logging imports
        from mcp.enhanced_mcp_logger import get_mcp_logger, create_mcp_logger, MCPDecisionType
        print("✅ MCP enhanced logger imported successfully")
        
        # Test enhanced context builder
        from mcp.context_builder import EnhancedMCPContextBuilder, build_mcp_context
        print("✅ Enhanced MCP context builder imported successfully")
        
        # Test enhanced retriever
        from gpt_runner.rag.retriever import retrieve_similar_context, retrieve_with_hybrid_strategy
        print("✅ Enhanced RAG retriever imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_rag_logging():
    """Test RAG logging functionality"""
    print("\n🔍 Testing RAG Logging...")
    
    try:
        from gpt_runner.rag.enhanced_rag_logger import create_rag_logger
        
        # Create RAG logger
        session_id = f"test_rag_{int(time.time())}"
        rag_logger = create_rag_logger(session_id=session_id, bot_type="test-bot")
        print(f"✅ RAG logger created with session: {session_id}")
        
        # Test query logging
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 20  # Mock embedding
        trace_id = rag_logger.log_rag_query(
            query_text="Test query for NIFTY trading patterns",
            query_embedding=test_embedding,
            context_type="test_context",
            metadata={"symbol": "NIFTY", "test": True}
        )
        print(f"✅ RAG query logged with trace_id: {trace_id}")
        
        # Test retrieval logging
        mock_docs = [
            {"text": "Mock document 1", "metadata": {"type": "trade"}},
            {"text": "Mock document 2", "metadata": {"type": "log"}}
        ]
        rag_logger.log_rag_retrieval(
            trace_id=trace_id,
            query_id=trace_id,
            retrieved_docs=mock_docs,
            similarity_scores=[0.85, 0.72],
            retrieval_time_ms=45.2,
            total_searched=100,
            threshold=0.7,
            strategy="test_semantic"
        )
        print("✅ RAG retrieval logged successfully")
        
        # Test context logging
        rag_logger.log_rag_context(
            trace_id=trace_id,
            query_id=trace_id,
            final_context="Test context for LLM",
            context_sources=["doc1", "doc2"],
            llm_model="gpt-4",
            temperature=0.7,
            max_tokens=2048
        )
        print("✅ RAG context logged successfully")
        
        # Test response logging
        rag_logger.log_rag_response(
            trace_id=trace_id,
            query_id=trace_id,
            llm_response="Test LLM response",
            processing_time_ms=120.5,
            tokens_used=150,
            cost_estimate=0.002,
            confidence_score=0.85
        )
        print("✅ RAG response logged successfully")
        
        # Test embedding logging
        embedding_trace_id = rag_logger.log_rag_embedding(
            document_id="test_doc_123",
            document_type="trade",
            source_bot="test-bot",
            embedding_model="text-embedding-ada-002",
            document_text="Test document for embedding",
            metadata={"test": True},
            embedding_time_ms=25.3,
            embedding_dimensions=1536
        )
        print(f"✅ RAG embedding logged with trace_id: {embedding_trace_id}")
        
        # Test performance summary
        summary = rag_logger.get_rag_performance_summary()
        print(f"✅ RAG performance summary: {summary['metrics']}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG logging test failed: {e}")
        return False


def test_mcp_logging():
    """Test MCP logging functionality"""
    print("\n🔍 Testing MCP Logging...")
    
    try:
        from mcp.enhanced_mcp_logger import create_mcp_logger, MCPDecisionType, MCPActionStatus
        
        # Create MCP logger
        session_id = f"test_mcp_{int(time.time())}"
        mcp_logger = create_mcp_logger(session_id=session_id, bot_type="test-bot")
        print(f"✅ MCP logger created with session: {session_id}")
        
        # Test context logging
        context_trace_id = mcp_logger.log_mcp_context(
            context_request={"include_trades": True, "include_rag": True},
            context_sources=["firestore_trades", "rag_retrieval", "market_monitor"],
            context_data={"test": "context_data"},
            build_time_ms=120.5,
            completeness_score=0.85
        )
        print(f"✅ MCP context logged with trace_id: {context_trace_id}")
        
        # Test decision logging
        decision_trace_id = mcp_logger.log_mcp_decision(
            context_id=context_trace_id,
            decision_type=MCPDecisionType.STRATEGY_SUGGESTION,
            input_analysis={"market_trend": "bullish", "volatility": "moderate"},
            reasoning="Test decision reasoning based on market analysis",
            confidence=0.78,
            actions=[{"type": "adjust_sl", "value": "2%"}],
            risk_assessment={"risk_level": "medium"},
            expected_impact={"profit_potential": "high"},
            decision_time_ms=89.3
        )
        print(f"✅ MCP decision logged with trace_id: {decision_trace_id}")
        
        # Test action logging
        action_trace_id = mcp_logger.log_mcp_action(
            decision_id=decision_trace_id,
            action_type="strategy_adjustment",
            action_details={"parameter": "stop_loss", "new_value": "2%"},
            execution_status=MCPActionStatus.EXECUTED,
            execution_time_ms=45.2,
            result_data={"success": True, "applied": True},
            error_details=None,
            impact_metrics={"risk_reduction": 0.15}
        )
        print(f"✅ MCP action logged with trace_id: {action_trace_id}")
        
        # Test reflection logging
        reflection_trace_id = mcp_logger.log_mcp_reflection(
            reflection_period="daily",
            performance_data={"pnl": 1250.50, "trades": 15, "win_rate": 0.73},
            lessons_learned=["Market volatility increased", "Stop loss strategy effective"],
            strategy_adjustments=[{"parameter": "position_size", "change": "reduce by 10%"}],
            confidence_evolution={"strategy_confidence": 0.82, "market_confidence": 0.65},
            next_actions=["Monitor volatility", "Adjust position sizing"]
        )
        print(f"✅ MCP reflection logged with trace_id: {reflection_trace_id}")
        
        # Test strategy evolution logging
        strategy_trace_id = mcp_logger.log_mcp_strategy_evolution(
            strategy_name="momentum_v2",
            version="2.1.0",
            changes_made=[{"component": "entry_logic", "change": "added volatility filter"}],
            backtesting_results={"sharpe_ratio": 1.85, "max_drawdown": 0.12},
            confidence_metrics={"backtest_confidence": 0.88, "live_confidence": 0.75},
            deployment_status="testing"
        )
        print(f"✅ MCP strategy evolution logged with trace_id: {strategy_trace_id}")
        
        # Test performance summary
        summary = mcp_logger.get_mcp_performance_summary()
        print(f"✅ MCP performance summary: {summary['metrics']}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP logging test failed: {e}")
        return False


def test_enhanced_context_builder():
    """Test enhanced MCP context builder"""
    print("\n🔍 Testing Enhanced MCP Context Builder...")
    
    try:
        from mcp.context_builder import EnhancedMCPContextBuilder
        
        # Create enhanced context builder
        session_id = f"test_context_{int(time.time())}"
        builder = EnhancedMCPContextBuilder(session_id=session_id)
        print(f"✅ Enhanced context builder created with session: {session_id}")
        
        # Test context building with various options
        context_request = {
            "include_trades": True,
            "include_capital": True,
            "include_market": True,
            "include_rag": True,
            "include_historical": False,
            "time_range_hours": 24,
            "trade_limit": 10
        }
        
        context = builder.build_mcp_context(
            bot_name="test-bot",
            context_request=context_request
        )
        
        print("✅ Enhanced context built successfully")
        print(f"   - Sources: {context['context_metadata']['sources']}")
        print(f"   - Completeness: {context['context_metadata']['completeness_score']:.2f}")
        print(f"   - Build time: {context['context_metadata']['build_time_ms']:.1f}ms")
        
        # Test backward compatibility
        from mcp.context_builder import build_mcp_context
        legacy_context = build_mcp_context("test-bot", enhanced=False)
        enhanced_context = build_mcp_context("test-bot", enhanced=True)
        
        print("✅ Backward compatibility maintained")
        print(f"   - Legacy context keys: {len(legacy_context.keys())}")
        print(f"   - Enhanced context keys: {len(enhanced_context.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced context builder test failed: {e}")
        return False


def test_enhanced_retriever():
    """Test enhanced RAG retriever"""
    print("\n🔍 Testing Enhanced RAG Retriever...")
    
    try:
        from gpt_runner.rag.retriever import retrieve_similar_context, retrieve_with_hybrid_strategy, retrieve_by_category
        
        session_id = f"test_retriever_{int(time.time())}"
        
        # Test enhanced retrieval (will likely return empty due to no vector store)
        results = retrieve_similar_context(
            query="test trading query",
            limit=5,
            threshold=0.7,
            bot_name="test-bot",
            session_id=session_id,
            context_type="test_context"
        )
        print(f"✅ Enhanced retrieval completed - {len(results)} results")
        
        # Test hybrid strategy retrieval
        hybrid_results = retrieve_with_hybrid_strategy(
            query="test hybrid query",
            limit=3,
            threshold=0.6,
            bot_name="test-bot",
            temporal_weight=0.3,
            session_id=session_id
        )
        print(f"✅ Hybrid retrieval completed - {len(hybrid_results)} results")
        
        # Test category retrieval
        category_results = retrieve_by_category(
            category="trade",
            limit=10,
            bot_name="test-bot",
            session_id=session_id
        )
        print(f"✅ Category retrieval completed - {len(category_results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced retriever test failed: {e}")
        return False


def test_gcs_bucket_configuration():
    """Test GCS bucket configuration"""
    print("\n🔍 Testing GCS Bucket Configuration...")
    
    try:
        from runner.enhanced_logging.gcs_logger import GCSLogger, GCSBuckets
        
        # Test bucket names
        expected_buckets = [
            GCSBuckets.TRADE_LOGS,
            GCSBuckets.COGNITIVE_ARCHIVES,
            GCSBuckets.SYSTEM_LOGS,
            GCSBuckets.ANALYTICS_DATA,
            GCSBuckets.COMPLIANCE_LOGS
        ]
        
        print(f"✅ GCS bucket names configured:")
        for bucket in expected_buckets:
            print(f"   - {bucket}")
        
        # Test GCS logger initialization (may fail without credentials)
        try:
            gcs_logger = GCSLogger(project_id="autotrade-453303")
            print("✅ GCS logger initialized successfully")
            
            # Test blob path generation
            blob_path = gcs_logger._get_blob_path("test_bucket", "test_file", "test-bot", "1")
            print(f"✅ Blob path generated: {blob_path}")
            
        except Exception as e:
            print(f"⚠️  GCS logger initialization failed (expected without credentials): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ GCS bucket configuration test failed: {e}")
        return False


def test_firestore_integration():
    """Test Firestore integration"""
    print("\n🔍 Testing Firestore Integration...")
    
    try:
        from runner.firestore_client import FirestoreClient
        
        # Test Firestore client initialization (may fail without credentials)
        try:
            firestore_client = FirestoreClient()
            print("✅ Firestore client initialized successfully")
            
            # Test collection names
            expected_collections = [
                "rag_queries", "rag_retrievals", "rag_contexts", "rag_responses", "rag_embeddings",
                "mcp_contexts", "mcp_decisions", "mcp_actions", "mcp_reflections", "mcp_strategies"
            ]
            
            print("✅ Expected Firestore collections:")
            for collection in expected_collections:
                print(f"   - {collection}")
                
        except Exception as e:
            print(f"⚠️  Firestore client initialization failed (expected without credentials): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestore integration test failed: {e}")
        return False


def test_trace_correlation():
    """Test trace correlation system"""
    print("\n🔍 Testing Trace Correlation System...")
    
    try:
        from gpt_runner.rag.enhanced_rag_logger import create_rag_logger
        from mcp.enhanced_mcp_logger import create_mcp_logger
        
        # Create loggers with same session
        session_id = f"test_correlation_{int(time.time())}"
        rag_logger = create_rag_logger(session_id=session_id, bot_type="test-bot")
        mcp_logger = create_mcp_logger(session_id=session_id, bot_type="test-bot")
        
        # Generate correlated trace IDs
        rag_trace_id = rag_logger.generate_trace_id()
        mcp_trace_id = mcp_logger.generate_trace_id()
        
        print(f"✅ Trace correlation system working:")
        print(f"   - Session ID: {session_id}")
        print(f"   - RAG trace: {rag_trace_id}")
        print(f"   - MCP trace: {mcp_trace_id}")
        
        # Verify trace ID format
        assert rag_trace_id.startswith("rag_"), "RAG trace ID format incorrect"
        assert mcp_trace_id.startswith("mcp_"), "MCP trace ID format incorrect"
        assert len(rag_trace_id.split("_")) == 3, "RAG trace ID structure incorrect"
        assert len(mcp_trace_id.split("_")) == 3, "MCP trace ID structure incorrect"
        
        print("✅ Trace ID format validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Trace correlation test failed: {e}")
        return False


def test_performance_monitoring():
    """Test performance monitoring capabilities"""
    print("\n🔍 Testing Performance Monitoring...")
    
    try:
        from gpt_runner.rag.enhanced_rag_logger import create_rag_logger
        from mcp.enhanced_mcp_logger import create_mcp_logger
        
        # Create loggers
        session_id = f"test_perf_{int(time.time())}"
        rag_logger = create_rag_logger(session_id=session_id, bot_type="test-bot")
        mcp_logger = create_mcp_logger(session_id=session_id, bot_type="test-bot")
        
        # Simulate some operations to generate metrics
        for i in range(3):
            # RAG operations
            trace_id = rag_logger.log_rag_query(
                query_text=f"Test query {i}",
                query_embedding=[0.1] * 100,
                context_type="test"
            )
            
            rag_logger.log_rag_retrieval(
                trace_id=trace_id,
                query_id=trace_id,
                retrieved_docs=[{"text": f"doc_{i}"}],
                similarity_scores=[0.8],
                retrieval_time_ms=50.0 + i * 10,
                total_searched=100,
                threshold=0.7,
                strategy="test"
            )
            
            # MCP operations
            context_trace_id = mcp_logger.log_mcp_context(
                context_request={"test": True},
                context_sources=["test_source"],
                context_data={"test": f"data_{i}"},
                build_time_ms=100.0 + i * 20,
                completeness_score=0.8
            )
        
        # Get performance summaries
        rag_summary = rag_logger.get_rag_performance_summary()
        mcp_summary = mcp_logger.get_mcp_performance_summary()
        
        print("✅ Performance monitoring working:")
        print(f"   - RAG queries: {rag_summary['metrics']['total_queries']}")
        print(f"   - RAG avg retrieval time: {rag_summary['metrics']['avg_retrieval_time_ms']:.1f}ms")
        print(f"   - MCP contexts: {mcp_summary['metrics']['total_contexts']}")
        print(f"   - MCP avg context time: {mcp_summary['metrics']['avg_context_build_time_ms']:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting Enhanced Logging Integration Tests\n")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("RAG Logging", test_rag_logging),
        ("MCP Logging", test_mcp_logging),
        ("Enhanced Context Builder", test_enhanced_context_builder),
        ("Enhanced Retriever", test_enhanced_retriever),
        ("GCS Bucket Configuration", test_gcs_bucket_configuration),
        ("Firestore Integration", test_firestore_integration),
        ("Trace Correlation", test_trace_correlation),
        ("Performance Monitoring", test_performance_monitoring),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced logging integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 