# runner / cognitive_memory.py
# Multi - layer cognitive memory system with GCP persistence
# Implements working, short - term, long - term, and episodic memory with automatic persistence

import uuid
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import math
import logging
from .k8s_native_gcp_client import get_k8s_gcp_client


class MemoryType(Enum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"


class ImportanceLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class MemoryItem:
    """Individual memory item with persistence and decay properties"""
    id: str
    content: str
    memory_type: str
    importance: float
    created_at: datetime.datetime
    last_accessed: datetime.datetime
    decay_rate: float
    associations: List[str]
    metadata: Dict[str, Any]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage"""
        return {
                    'id': self.id,
                    'content': self.content,
                    'memory_type': self.memory_type,
                    'importance': self.importance,
                    'created_at': self.created_at,
                    'last_accessed': self.last_accessed,
                    'decay_rate': self.decay_rate,
                    'associations': self.associations,
                'metadata': self.metadata,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create MemoryItem from dictionary"""
        return cls(
                    id=data['id'],
                    content=data['content'],
                    memory_type=data['memory_type'],
                    importance=data['importance'],
                    created_at=data['created_at'],
                    last_accessed=data['last_accessed'],
                    decay_rate=data['decay_rate'],
                    associations=data.get('associations', []),
                metadata=data.get('metadata', {}),
            tags=data.get('tags', [])
        )
    
    def calculate_current_strength(self) -> float:
        """Calculate current memory strength based on time and decay"""
        hours_since_creation = (datetime.datetime.utcnow() - self.created_at).total_seconds() / 3600
        hours_since_access = (datetime.datetime.utcnow() - self.last_accessed).total_seconds() / 3600
        
        # Base decay formula: strength = importance * e^(-decay_rate * time_since_access)
        base_strength = self.importance * math.exp(-self.decay_rate * hours_since_access)
        
        # Boost for recent creation
        recency_boost = 1.0 if hours_since_creation < 1 else 1.0 / math.log(hours_since_creation + 1)
        
        return min(base_strength * recency_boost, self.importance)


class CognitiveMemory:
    """
    Human - like multi - layer memory system with GCP persistence.
    Handles working memory (7±2 items), short - term, long - term, and episodic memory.
    """
    
    def __init__(self, gcp_client, logger: logging.Logger = None):
        self.gcp_client = gcp_client
        self.logger = logger or logging.getLogger(__name__)
        
        # Memory configuration
        self.working_memory_limit = 7  # Miller's Rule: 7±2 items
        self.short_term_memory_limit = 50
        self.decay_rates = {
            MemoryType.WORKING: 0.5,      # Fast decay (hours)
            MemoryType.SHORT_TERM: 0.1,   # Medium decay
            MemoryType.LONG_TERM: 0.01,   # Slow decay
            MemoryType.EPISODIC: 0.05     # Episode - dependent decay
        }
        
        # In - memory caches for performance
        self._working_memory_cache: List[MemoryItem] = []
        self._memory_associations: Dict[str, List[str]] = {}
        
        # State tracking
        self._last_cleanup = datetime.datetime.utcnow()
        self._memory_loaded = False
        
        # Auto - initialize from GCP
        self._load_memory_state()
    
    def _load_memory_state(self):
        """Load memory state from GCP on startup"""
        try:
            # Try to load from latest snapshot first
            snapshot = self.gcp_client.load_latest_memory_snapshot()
            if snapshot:
                self._restore_from_snapshot(snapshot)
                self.logger.info("Memory state restored from snapshot")
            else:
                # Load working memory from Firestore
                self._load_working_memory()
                self.logger.info("Memory state loaded from Firestore")
            
            self._memory_loaded = True
        except Exception as e:
            self.logger.error(f"Failed to load memory state: {e}")
            self._memory_loaded = False
    
    def _restore_from_snapshot(self, snapshot):
        """Restore memory state from snapshot"""
        # Restore working memory cache
        self._working_memory_cache = [
            MemoryItem.from_dict(item) for item in snapshot.working_memory
        ]
        
        # Restore recent short - term memories to cache if needed
        recent_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        for item_data in snapshot.short_term_memory:
            item = MemoryItem.from_dict(item_data)
            if item.last_accessed > recent_threshold:
                # Keep recently accessed items in working memory
                if len(self._working_memory_cache) < self.working_memory_limit:
                    self._working_memory_cache.append(item)
    
    def _load_working_memory(self):
        """Load working memory from Firestore"""
        working_memories = self.gcp_client.query_memory_collection(
                    'working_memory',
                order_by='last_accessed',
            limit=self.working_memory_limit
        )
        
        self._working_memory_cache = [
            MemoryItem.from_dict(mem) for mem in working_memories
        ]
    
    def store_memory(self, content: str, memory_type: MemoryType = MemoryType.WORKING,
                         importance: ImportanceLevel = ImportanceLevel.MEDIUM,
                     tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Store new memory item with automatic persistence"""
        memory_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        
        memory_item = MemoryItem(
                    id=memory_id,
                    content=content,
                    memory_type=memory_type.value,
                    importance=importance.value,
                    created_at=now,
                    last_accessed=now,
                    decay_rate=self.decay_rates[memory_type],
                    associations=[],
                metadata=metadata or {},
            tags=tags or []
        )
        
        # Store to appropriate location
        if memory_type == MemoryType.WORKING:
            self._add_to_working_memory(memory_item)
        else:
            # Store directly to Firestore for non - working memory
            collection_name = f"{memory_type.value}_memory"
            self.gcp_client.store_memory_item(
                        collection_name, 
                        memory_id, 
                    memory_item.to_dict(),
                ttl_hours=self._get_ttl_hours(memory_type)
            )
        
        self.logger.debug(f"Stored {memory_type.value} memory: {memory_id}")
        return memory_id
    
    def _add_to_working_memory(self, memory_item: MemoryItem):
        """Add item to working memory with overflow handling"""
        # Add to cache
        self._working_memory_cache.append(memory_item)
        
        # Handle overflow (Miller's Rule: 7±2 items)
        if len(self._working_memory_cache) > self.working_memory_limit:
            # Move oldest / least important items to short - term memory
            self._consolidate_working_memory()
        
        # Persist to Firestore
        self.gcp_client.store_memory_item(
                    'working_memory',
                    memory_item.id,
                memory_item.to_dict(),
            ttl_hours=1  # Working memory TTL
        )
    
    def _consolidate_working_memory(self):
        """Move items from working to short - term memory"""
        while len(self._working_memory_cache) > self.working_memory_limit:
            # Find least important / oldest item
            candidates = [
                (i, item) for i, item in enumerate(self._working_memory_cache)
                if item.calculate_current_strength() < 2.0  # Below medium importance
            ]
            
            if candidates:
                # Sort by strength (weakest first)
                candidates.sort(key=lambda x: x[1].calculate_current_strength())
                idx, item_to_move = candidates[0]
            else:
                # If all items are important, move oldest
                idx = min(range(len(self._working_memory_cache)),
                         key=lambda i: self._working_memory_cache[i].last_accessed)
                item_to_move = self._working_memory_cache[idx]
            
            # Move to short - term memory
            item_to_move.memory_type = MemoryType.SHORT_TERM.value
            self.gcp_client.store_memory_item(
                        'short_term_memory',
                        item_to_move.id,
                    item_to_move.to_dict(),
                ttl_hours=self._get_ttl_hours(MemoryType.SHORT_TERM)
            )
            
            # Remove from working memory
            self._working_memory_cache.pop(idx)
            self.gcp_client.delete_memory_item('working_memory', item_to_move.id)
            
            self.logger.debug(f"Moved memory {item_to_move.id} to short - term")
    
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve memory by ID from any layer"""
        # Check working memory cache first
        for item in self._working_memory_cache:
            if item.id == memory_id:
                item.last_accessed = datetime.datetime.utcnow()
                self._update_memory_access(item)
                return item
        
        # Search other memory layers
        for memory_type in ['short_term_memory', 'long_term_memory', 'episodic_memory']:
            memory_data = self.gcp_client.get_memory_item(memory_type, memory_id)
            if memory_data:
                memory_item = MemoryItem.from_dict(memory_data)
                
                # Update access time
                memory_item.last_accessed = datetime.datetime.utcnow()
                self.gcp_client.update_memory_item(
                            memory_type, 
                        memory_id, 
                    {'last_accessed': memory_item.last_accessed}
                )
                
                # Promote to working memory if important
                if memory_item.calculate_current_strength() > 3.0:
                    self._promote_to_working_memory(memory_item, memory_type)
                
                return memory_item
        
        return None
    
    def _promote_to_working_memory(self, memory_item: MemoryItem, source_collection: str):
        """Promote memory item to working memory"""
        memory_item.memory_type = MemoryType.WORKING.value
        self._add_to_working_memory(memory_item)
        
        # Remove from source collection
        self.gcp_client.delete_memory_item(source_collection, memory_item.id)
        
        self.logger.debug(f"Promoted memory {memory_item.id} to working memory")
    
    def search_memories(self, query: str, memory_types: List[MemoryType] = None,
                       tags: List[str] = None, limit: int = 10) -> List[MemoryItem]:
        """Search memories by content, tags, or metadata"""
        if memory_types is None:
            memory_types = [MemoryType.WORKING, MemoryType.SHORT_TERM, MemoryType.LONG_TERM]
        
        results = []
        
        # Search working memory cache
        if MemoryType.WORKING in memory_types:
            for item in self._working_memory_cache:
                if self._matches_query(item, query, tags):
                    results.append(item)
        
        # Search Firestore collections
        for memory_type in memory_types:
            if memory_type == MemoryType.WORKING:
                continue  # Already searched cache
            
            collection_name = f"{memory_type.value}_memory"
            
            # Build filters
            filters = []
            if tags:
                filters.append(('tags', 'array_contains_any', tags))
            
            memories_data = self.gcp_client.query_memory_collection(
                        collection_name,
                        filters=filters,
                    order_by='importance',
                limit=limit
            )
            
            for memory_data in memories_data:
                memory_item = MemoryItem.from_dict(memory_data)
                if self._matches_query(memory_item, query, tags):
                    results.append(memory_item)
        
        # Sort by relevance and current strength
        results.sort(key=lambda x: x.calculate_current_strength(), reverse=True)
        return results[:limit]
    
    def _matches_query(self, memory_item: MemoryItem, query: str, tags: List[str] = None) -> bool:
        """Check if memory item matches search criteria"""
        # Text search in content
        content_match = query.lower() in memory_item.content.lower() if query else True
        
        # Tag search
        tag_match = True
        if tags:
            tag_match = any(tag in memory_item.tags for tag in tags)
        
        return content_match and tag_match
    
    def create_memory_association(self, memory_id1: str, memory_id2: str, strength: float = 1.0):
        """Create association between two memories"""
        # Update in - memory associations
        if memory_id1 not in self._memory_associations:
            self._memory_associations[memory_id1] = []
        if memory_id2 not in self._memory_associations:
            self._memory_associations[memory_id2] = []
        
        self._memory_associations[memory_id1].append(memory_id2)
        self._memory_associations[memory_id2].append(memory_id1)
        
        # Update memories in Firestore
        for memory_id in [memory_id1, memory_id2]:
            other_id = memory_id2 if memory_id == memory_id1 else memory_id1
            
            # Find memory in any collection and update associations
            for collection in ['working_memory', 'short_term_memory', 'long_term_memory', 'episodic_memory']:
                memory_data = self.gcp_client.get_memory_item(collection, memory_id)
                if memory_data:
                    associations = memory_data.get('associations', [])
                    if other_id not in associations:
                        associations.append(other_id)
                        self.gcp_client.update_memory_item(
                            collection, memory_id, {'associations': associations}
                        )
                    break
    
    def get_associated_memories(self, memory_id: str) -> List[MemoryItem]:
        """Get memories associated with given memory"""
        associations = self._memory_associations.get(memory_id, [])
        
        # Also check Firestore for persistent associations
        memory = self.retrieve_memory(memory_id)
        if memory:
            associations.extend(memory.associations)
        
        # Remove duplicates and retrieve associated memories
        unique_associations = list(set(associations))
        associated_memories = []
        
        for assoc_id in unique_associations:
            assoc_memory = self.retrieve_memory(assoc_id)
            if assoc_memory:
                associated_memories.append(assoc_memory)
        
        return associated_memories
    
    def create_episodic_memory(self, event_type: str, details: Dict[str, Any],
                              importance: ImportanceLevel = ImportanceLevel.MEDIUM) -> str:
        """Create episodic memory for significant events"""
        episode_content = f"{event_type}: {json.dumps(details, default=str)}"
        
        memory_id = self.store_memory(
                    content=episode_content,
                    memory_type=MemoryType.EPISODIC,
                    importance=importance,
                tags=[event_type, 'episode'],
            metadata={
                        'event_type': event_type,
                    'event_details': details,
                'is_episodic': True
            }
        )
        
        self.logger.info(f"Created episodic memory: {event_type}")
        return memory_id
    
    def consolidate_memories(self):
        """Periodic memory consolidation and cleanup"""
        current_time = datetime.datetime.utcnow()
        
        # Skip if recent consolidation
        if (current_time - self._last_cleanup).total_seconds() < 3600:  # 1 hour
            return
        
        self.logger.info("Starting memory consolidation")
        
        # 1. Clean up expired memories
        self.gcp_client.cleanup_expired_memories()
        
        # 2. Promote important short - term memories to long - term
        self._promote_important_memories()
        
        # 3. Decay memory strengths
        self._apply_memory_decay()
        
        # 4. Create memory snapshot
        self._create_memory_snapshot()
        
        self._last_cleanup = current_time
        self.logger.info("Memory consolidation completed")
    
    def _promote_important_memories(self):
        """Promote important short - term memories to long - term storage"""
        short_term_memories = self.gcp_client.query_memory_collection(
                    'short_term_memory',
                order_by='importance',
            limit=100
        )
        
        for memory_data in short_term_memories:
            memory_item = MemoryItem.from_dict(memory_data)
            
            # Promote if high importance and frequently accessed
            if (memory_item.importance >= ImportanceLevel.HIGH.value and
                memory_item.calculate_current_strength() > 3.0):
                
                # Move to long - term memory
                memory_item.memory_type = MemoryType.LONG_TERM.value
                self.gcp_client.store_memory_item(
                            'long_term_memory',
                        memory_item.id,
                    memory_item.to_dict()
                )
                
                # Remove from short - term
                self.gcp_client.delete_memory_item('short_term_memory', memory_item.id)
                
                self.logger.debug(f"Promoted memory {memory_item.id} to long - term")
    
    def _apply_memory_decay(self):
        """Apply decay to all memories based on time and access patterns"""
        for collection in ['working_memory', 'short_term_memory']:
            memories = self.gcp_client.query_memory_collection(collection, limit=1000)
            
            for memory_data in memories:
                memory_item = MemoryItem.from_dict(memory_data)
                current_strength = memory_item.calculate_current_strength()
                
                # If strength falls too low, delete memory
                if current_strength < 0.5:
                    self.gcp_client.delete_memory_item(collection, memory_item.id)
                    
                    # Remove from working memory cache if present
                    self._working_memory_cache = [
                        item for item in self._working_memory_cache 
                        if item.id != memory_item.id
                    ]
                    
                    self.logger.debug(f"Decayed memory {memory_item.id}")
    
    def _create_memory_snapshot(self):
        """Create periodic memory snapshot for disaster recovery"""
        try:
            # Collect current memory state
            working_memory = [item.to_dict() for item in self._working_memory_cache]
            
            short_term_data = self.gcp_client.query_memory_collection(
                'short_term_memory', limit=50
            )
            
            # Get current cognitive state (will be implemented in cognitive_system.py)
            cognitive_state = {'state': 'unknown', 'timestamp': datetime.datetime.utcnow()}
            
            # Get recent thoughts (will be implemented in thought_journal.py)
            recent_thoughts = []
            
            # Get performance metrics (will be implemented in metacognition.py)
            performance_metrics = {}
            
            snapshot = {
                'timestamp': datetime.datetime.utcnow(),
                'working_memory': working_memory,
                'short_term_memory': short_term_data,
                'cognitive_state': cognitive_state,
                'recent_thoughts': recent_thoughts,
                'performance_metrics': performance_metrics
            }
            
            self.gcp_client.store_memory_snapshot(snapshot)
        except Exception as e:
            self.logger.error(f"Failed to create memory snapshot: {e}")
    
    def _get_ttl_hours(self, memory_type: MemoryType) -> Optional[int]:
        """Get TTL hours for memory type"""
        ttl_config = {
                MemoryType.WORKING: 1,
            MemoryType.SHORT_TERM: 168,  # 7 days
            MemoryType.LONG_TERM: None,  # No TTL
            MemoryType.EPISODIC: None    # No TTL
        }
        return ttl_config.get(memory_type)
    
    def _update_memory_access(self, memory_item: MemoryItem):
        """Update memory access time in Firestore"""
        collection_name = f"{memory_item.memory_type}_memory"
        self.gcp_client.update_memory_item(
                    collection_name,
                memory_item.id,
            {'last_accessed': memory_item.last_accessed}
        )
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory system summary"""
        stats = self.gcp_client.get_memory_stats()
        
        return {
                    'working_memory_count': len(self._working_memory_cache),
                    'working_memory_limit': self.working_memory_limit,
                    'firestore_stats': stats,
                    'memory_loaded': self._memory_loaded,
                'last_cleanup': self._last_cleanup,
            'total_associations': len(self._memory_associations)
        }
    
    def emergency_memory_reset(self):
        """Emergency reset of all memory systems"""
        self.logger.warning("Performing emergency memory reset")
        
        # Clear caches
        self._working_memory_cache.clear()
        self._memory_associations.clear()
        
        # Clear Firestore collections
        for collection in ['working_memory', 'short_term_memory']:
            memories = self.gcp_client.query_memory_collection(collection, limit=1000)
            for memory_data in memories:
                self.gcp_client.delete_memory_item(collection, memory_data['id'])
        
        self._memory_loaded = False
        self.logger.warning("Emergency memory reset completed")
