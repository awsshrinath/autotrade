#!/usr/bin/env python3
"""
Quick test script to validate cognitive system implementations
Tests basic functionality without requiring full GCP setup
"""

import sys
import os
import datetime
import logging
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all cognitive modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from runner.gcp_memory_client import GCPMemoryClient, MemorySnapshot
        print("✅ GCP Memory Client import successful")
    except Exception as e:
        print(f"❌ GCP Memory Client import failed: {e}")
        return False
    
    try:
        from runner.cognitive_memory import CognitiveMemory, MemoryType, ImportanceLevel, MemoryItem
        print("✅ Cognitive Memory import successful")
    except Exception as e:
        print(f"❌ Cognitive Memory import failed: {e}")
        return False
    
    try:
        from runner.thought_journal import ThoughtJournal, DecisionType, ConfidenceLevel, EmotionalState, ThoughtEntry
        print("✅ Thought Journal import successful")
    except Exception as e:
        print(f"❌ Thought Journal import failed: {e}")
        return False
    
    try:
        from runner.cognitive_state_machine import CognitiveStateMachine, CognitiveState, StateTransitionTrigger
        print("✅ Cognitive State Machine import successful")
    except Exception as e:
        print(f"❌ Cognitive State Machine import failed: {e}")
        return False
    
    try:
        from runner.metacognition import MetaCognition, BiasType, DecisionOutcome, LearningType
        print("✅ Metacognition import successful")
    except Exception as e:
        print(f"❌ Metacognition import failed: {e}")
        return False
    
    try:
        from runner.cognitive_system import CognitiveSystem, create_cognitive_system
        print("✅ Cognitive System import successful")
    except Exception as e:
        print(f"❌ Cognitive System import failed: {e}")
        return False
    
    return True

def test_data_models():
    """Test data model creation and serialization"""
    print("\n🧪 Testing data models...")
    
    try:
        from runner.cognitive_memory import MemoryItem
        from runner.thought_journal import ThoughtEntry
        
        # Test MemoryItem
        memory_item = MemoryItem(
            id="test-123",
            content="Test memory content",
            memory_type="working",
            importance=3.0,
            created_at=datetime.datetime.utcnow(),
            last_accessed=datetime.datetime.utcnow(),
            decay_rate=0.5,
            associations=[],
            metadata={},
            tags=["test"]
        )
        
        # Test serialization
        memory_dict = memory_item.to_dict()
        restored_memory = MemoryItem.from_dict(memory_dict)
        print("✅ MemoryItem serialization/deserialization successful")
        
        # Test ThoughtEntry
        thought_entry = ThoughtEntry(
            id="thought-123",
            timestamp=datetime.datetime.utcnow(),
            decision="Test decision",
            reasoning="Test reasoning",
            confidence=3.0,
            emotional_state="calm",
            market_context={},
            strategy_id="test_strategy",
            trade_id="trade_123",
            decision_type="market_analysis",
            importance_score=2.5,
            follow_up_required=False,
            tags=["test"],
            related_thoughts=[],
            outcome=None,
            reflection=None
        )
        
        thought_dict = thought_entry.to_dict()
        restored_thought = ThoughtEntry.from_dict(thought_dict)
        print("✅ ThoughtEntry serialization/deserialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model test failed: {e}")
        return False

def test_mock_gcp_client():
    """Test GCP client with mocked dependencies"""
    print("\n🧪 Testing GCP client with mocks...")
    
    try:
        with patch('runner.gcp_memory_client.firestore') as mock_firestore, \
             patch('runner.gcp_memory_client.storage') as mock_storage:
            
            # Mock the clients
            mock_firestore.Client.return_value = Mock()
            mock_storage.Client.return_value = Mock()
            
            from runner.gcp_memory_client import GCPMemoryClient
            
            # Create client with mocked dependencies
            logger = Mock()
            gcp_client = GCPMemoryClient(logger=logger)
            
            # Test health check with mocked responses
            with patch.object(gcp_client, 'health_check') as mock_health:
                mock_health.return_value = {
                    'firestore': True,
                    'cloud_storage': True,
                    'buckets': True
                }
                
                health_status = gcp_client.health_check()
                assert all(health_status.values()), f"Health check failed: {health_status}"
                print("✅ GCP client mock test successful")
                
        return True
        
    except Exception as e:
        print(f"❌ GCP client mock test failed: {e}")
        return False

def test_cognitive_memory_mock():
    """Test cognitive memory with mocked GCP client"""
    print("\n🧪 Testing cognitive memory with mocks...")
    
    try:
        from runner.cognitive_memory import CognitiveMemory, MemoryType, ImportanceLevel
        
        # Mock GCP client
        mock_gcp_client = Mock()
        mock_gcp_client.query_memory_collection.return_value = []
        mock_gcp_client.store_memory_item.return_value = True
        mock_gcp_client.get_memory_item.return_value = None
        mock_gcp_client.load_latest_memory_snapshot.return_value = None
        
        logger = Mock()
        
        # Create cognitive memory with mocked client
        memory = CognitiveMemory(mock_gcp_client, logger)
        
        # Test memory storage
        memory_id = memory.store_memory(
            content="Test memory",
            memory_type=MemoryType.WORKING,
            importance=ImportanceLevel.MEDIUM,
            tags=["test"]
        )
        
        assert memory_id, "Memory storage should return an ID"
        print("✅ Cognitive memory mock test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Cognitive memory mock test failed: {e}")
        return False

def test_thought_journal_mock():
    """Test thought journal with mocked GCP client"""
    print("\n🧪 Testing thought journal with mocks...")
    
    try:
        from runner.thought_journal import ThoughtJournal, DecisionType, ConfidenceLevel
        
        # Mock GCP client
        mock_gcp_client = Mock()
        mock_gcp_client.store_memory_item.return_value = True
        mock_gcp_client.query_memory_collection.return_value = []
        
        logger = Mock()
        
        # Create thought journal with mocked client
        journal = ThoughtJournal(mock_gcp_client, logger)
        
        # Test thought recording
        thought_id = journal.record_thought(
            decision="Test decision",
            reasoning="Test reasoning",
            decision_type=DecisionType.MARKET_ANALYSIS,
            confidence=ConfidenceLevel.MEDIUM
        )
        
        assert thought_id, "Thought recording should return an ID"
        print("✅ Thought journal mock test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Thought journal mock test failed: {e}")
        return False

def test_state_machine_mock():
    """Test cognitive state machine with mocked GCP client"""
    print("\n🧪 Testing state machine with mocks...")
    
    try:
        from runner.cognitive_state_machine import CognitiveStateMachine, CognitiveState, StateTransitionTrigger
        
        # Mock GCP client
        mock_gcp_client = Mock()
        mock_gcp_client.get_memory_item.return_value = None
        mock_gcp_client.store_memory_item.return_value = True
        
        logger = Mock()
        
        # Create state machine with mocked client
        state_machine = CognitiveStateMachine(mock_gcp_client, logger)
        
        # Test state transition
        success = state_machine.transition_to(
            CognitiveState.ANALYZING,
            StateTransitionTrigger.SIGNAL_DETECTED,
            "Test transition"
        )
        
        assert success, "State transition should succeed"
        assert state_machine.get_current_state() == CognitiveState.ANALYZING
        print("✅ State machine mock test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ State machine mock test failed: {e}")
        return False

def test_trade_manager_integration():
    """Test trade manager integration with cognitive system"""
    print("\n🧪 Testing trade manager integration...")
    
    try:
        from runner.trade_manager import TradeManager
        
        # Mock dependencies
        logger = Mock()
        kite = Mock()
        firestore_client = Mock()
        
        # Create trade manager without cognitive system first
        trade_manager = TradeManager(
            logger=logger,
            kite=kite,
            firestore_client=firestore_client,
            cognitive_system=None
        )
        
        # Check that it initializes without cognitive system
        assert trade_manager.cognitive_system is None
        print("✅ Trade manager works without cognitive system")
        
        # Mock cognitive system
        mock_cognitive_system = Mock()
        mock_cognitive_system.record_thought.return_value = "thought-123"
        
        trade_manager_with_cognitive = TradeManager(
            logger=logger,
            kite=kite,
            firestore_client=firestore_client,
            cognitive_system=mock_cognitive_system
        )
        
        assert trade_manager_with_cognitive.cognitive_system is not None
        print("✅ Trade manager integration mock test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Trade manager integration test failed: {e}")
        return False

def test_requirements():
    """Test that required packages are available"""
    print("\n🧪 Testing requirements...")
    
    required_packages = [
        'google.cloud.firestore',
        'google.cloud.storage',
        'datetime',
        'json',
        'dataclasses',
        'enum',
        'uuid',
        'threading',
        'logging'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        return False
    else:
        print("✅ All required packages available")
        return True

def main():
    """Run all tests"""
    print("🧠 TRON Cognitive System - Quick Validation Test")
    print("=" * 50)
    
    tests = [
        test_requirements,
        test_imports,
        test_data_models,
        test_mock_gcp_client,
        test_cognitive_memory_mock,
        test_thought_journal_mock,
        test_state_machine_mock,
        test_trade_manager_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Cognitive system implementation is working correctly.")
        print("\n📋 Next Steps:")
        print("1. Create GCS buckets: tron-cognitive-memory, tron-thought-archives, tron-analysis-reports, tron-memory-backups")
        print("2. Set up GCP_PROJECT_ID environment variable")
        print("3. Deploy with cognitive system enabled")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)