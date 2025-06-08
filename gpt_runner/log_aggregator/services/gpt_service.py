"""
GPT-based log summarization service.
Provides AI-powered analysis and summarization of log data using OpenAI's GPT models.
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
import structlog
from openai import AsyncOpenAI

from ..utils.config import get_config

logger = structlog.get_logger(__name__)

class GPTLogService:
    """Service for GPT-powered log analysis and summarization."""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            if not self.config.openai_api_key:
                logger.warning("OpenAI API key not configured, GPT features will be disabled")
                return
            
            self.client = AsyncOpenAI(
                api_key=self.config.openai_api_key,
                timeout=self.config.openai_timeout
            )
            
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            self.client = None

    async def test_connection(self) -> Dict[str, bool]:
        """Test connections to OpenAI."""
        results = {
            "openai": False
        }
        
        # Test OpenAI connection
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            results["openai"] = True
            logger.info("OpenAI connection test successful")
        except Exception as e:
            logger.error("OpenAI connection test failed", error=str(e))
        
        return results
    
    def _generate_cache_key(self, content: str, summary_type: str, **kwargs) -> str:
        """Generate a cache key for the given content and parameters."""
        # Create a hash of the content and parameters
        content_hash = hashlib.md5(content.encode()).hexdigest()
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"gpt_summary:{summary_type}:{content_hash}:{params_hash}"
    
    async def _get_cached_summary(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached summary if available."""
        return None
    
    async def _cache_summary(self, cache_key: str, summary_data: Dict[str, Any], ttl: int = 3600):
        """Cache the summary data."""
        pass
    
    def _chunk_text(self, text: str, max_chunk_size: int = 8000) -> List[str]:
        """
        Split text into chunks for processing.
        Tries to split on logical boundaries (lines, sentences).
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        lines = text.split('\n')
        current_chunk = ""
        
        for line in lines:
            # If adding this line would exceed the limit
            if len(current_chunk) + len(line) + 1 > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    # Line itself is too long, split it
                    while len(line) > max_chunk_size:
                        chunks.append(line[:max_chunk_size])
                        line = line[max_chunk_size:]
                    current_chunk = line
            else:
                current_chunk += "\n" + line if current_chunk else line
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info("Text chunked for processing", total_chunks=len(chunks), original_length=len(text))
        return chunks
    
    async def _summarize_chunk(self, chunk: str, summary_type: str = "general") -> str:
        """Summarize a single chunk of text."""
        try:
            # Define prompts based on summary type
            prompts = {
                "general": "Summarize the following log data, focusing on key events, errors, and important patterns:",
                "errors": "Analyze the following log data and summarize all errors, warnings, and critical issues:",
                "performance": "Analyze the following log data for performance issues, slow operations, and resource usage patterns:",
                "security": "Analyze the following log data for security-related events, authentication issues, and potential threats:",
                "trends": "Analyze the following log data and identify trends, patterns, and recurring events:"
            }
            
            prompt = prompts.get(summary_type, prompts["general"])
            
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert log analyst. Provide concise, actionable summaries."},
                    {"role": "user", "content": f"{prompt}\n\n{chunk}"}
                ],
                max_tokens=self.config.openai_max_tokens,
                temperature=self.config.openai_temperature
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info(
                "Chunk summarized",
                chunk_length=len(chunk),
                summary_length=len(summary),
                summary_type=summary_type
            )
            
            return summary
            
        except Exception as e:
            logger.error("Failed to summarize chunk", error=str(e), chunk_length=len(chunk))
            raise
    
    async def _combine_summaries(self, summaries: List[str], summary_type: str = "general") -> str:
        """Combine multiple chunk summaries into a final summary."""
        if len(summaries) == 1:
            return summaries[0]
        
        try:
            combined_text = "\n\n".join([f"Summary {i+1}:\n{summary}" for i, summary in enumerate(summaries)])
            
            prompt = f"Combine the following log summaries into a single, comprehensive summary. Remove redundancy and highlight the most important findings:\n\n{combined_text}"
            
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert log analyst. Create comprehensive, actionable summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.openai_max_tokens,
                temperature=self.config.openai_temperature
            )
            
            final_summary = response.choices[0].message.content.strip()
            
            logger.info(
                "Summaries combined",
                input_summaries=len(summaries),
                final_length=len(final_summary)
            )
            
            return final_summary
            
        except Exception as e:
            logger.error("Failed to combine summaries", error=str(e))
            raise
    
    async def summarize_logs(
        self,
        log_content: str,
        summary_type: str = "general",
        max_chunk_size: int = 8000,
        cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Summarize log content using GPT.
        
        Args:
            log_content: Raw log content to summarize
            summary_type: Type of summary (general, errors, performance, security, trends)
            max_chunk_size: Maximum size of each chunk for processing
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Dictionary with summary and metadata
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                log_content,
                summary_type,
                max_chunk_size=max_chunk_size
            )
            
            # Check cache first
            cached_result = await self._get_cached_summary(cache_key)
            if cached_result:
                return cached_result
            
            start_time = datetime.utcnow()
            
            # Chunk the content
            chunks = self._chunk_text(log_content, max_chunk_size)
            
            # Summarize each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                try:
                    summary = await self._summarize_chunk(chunk, summary_type)
                    chunk_summaries.append(summary)
                except Exception as e:
                    logger.error(f"Failed to summarize chunk {i+1}", error=str(e))
                    chunk_summaries.append(f"[Error summarizing chunk {i+1}: {str(e)}]")
            
            # Combine summaries if multiple chunks
            if len(chunk_summaries) > 1:
                final_summary = await self._combine_summaries(chunk_summaries, summary_type)
            else:
                final_summary = chunk_summaries[0] if chunk_summaries else "No content to summarize"
            
            # Prepare result
            result = {
                "summary": final_summary,
                "summary_type": summary_type,
                "metadata": {
                    "original_length": len(log_content),
                    "summary_length": len(final_summary),
                    "chunks_processed": len(chunks),
                    "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "model_used": self.config.openai_model,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Cache the result
            await self._cache_summary(cache_key, result, cache_ttl)
            
            logger.info(
                "Log summarization completed",
                summary_type=summary_type,
                original_length=len(log_content),
                summary_length=len(final_summary),
                chunks=len(chunks),
                processing_time=result["metadata"]["processing_time_seconds"]
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to summarize logs", error=str(e), summary_type=summary_type)
            raise
    
    async def analyze_log_patterns(self, log_content: str) -> Dict[str, Any]:
        """
        Analyze log content for patterns and insights.
        
        Args:
            log_content: Raw log content to analyze
            
        Returns:
            Dictionary with pattern analysis results
        """
        try:
            cache_key = self._generate_cache_key(log_content, "patterns")
            cached_result = await self._get_cached_summary(cache_key)
            if cached_result:
                return cached_result
            
            prompt = """Analyze the following log data and provide insights on:
1. Most frequent error types and their patterns
2. Time-based patterns (peak activity periods, recurring events)
3. Performance bottlenecks or slow operations
4. Security-related events or anomalies
5. Resource usage patterns
6. Recommendations for investigation or optimization

Provide a structured analysis with specific examples from the logs."""
            
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert log analyst. Provide detailed, actionable insights."},
                    {"role": "user", "content": f"{prompt}\n\n{log_content[:12000]}"}  # Limit to avoid token limits
                ],
                max_tokens=self.config.openai_max_tokens,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            analysis = response.choices[0].message.content.strip()
            
            result = {
                "analysis": analysis,
                "metadata": {
                    "analyzed_length": len(log_content),
                    "model_used": self.config.openai_model,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self._cache_summary(cache_key, result, 1800)  # Cache for 30 minutes
            
            logger.info("Log pattern analysis completed", analyzed_length=len(log_content))
            return result
            
        except Exception as e:
            logger.error("Failed to analyze log patterns", error=str(e))
            raise
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics and health information."""
        return {"cache_enabled": False}
    
    async def clear_cache(self, pattern: str = "gpt_summary:*") -> int:
        """Clear cached summaries matching the pattern."""
        return 0


# Global service instance
_gpt_service = None


def get_gpt_service() -> GPTLogService:
    """Get the global GPT service instance."""
    global _gpt_service
    if _gpt_service is None:
        _gpt_service = GPTLogService()
    return _gpt_service 