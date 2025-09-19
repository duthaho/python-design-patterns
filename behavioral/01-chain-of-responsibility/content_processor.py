import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    MIXED = "mixed"


class ProcessingStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"
    WARNING = "warning"


@dataclass
class ProcessingResult:
    status: ProcessingStatus
    processor_name: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __str__(self):
        return f"ProcessingResult({self.status.value}, {self.processor_name}, {self.reason})"


@dataclass
class Content:
    """Represents content to be processed"""

    content_id: str
    content_type: ContentType
    text: Optional[str] = None
    image_data: Optional[bytes] = None
    video_data: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Processing context - gets populated as content flows through pipeline
    processing_context: Dict[str, Any] = field(default_factory=dict)
    processing_history: List[ProcessingResult] = field(default_factory=list)

    # User and request info
    user_id: str = "anonymous"
    source_platform: str = "web"

    def add_result(self, result: ProcessingResult):
        """Add processing result to history"""
        self.processing_history.append(result)

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of all processing steps"""
        return {
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "user_id": self.user_id,
            "source_platform": self.source_platform,
            "processing_steps": [
                {
                    "processor": r.processor_name,
                    "status": r.status.value,
                    "reason": r.reason,
                    "time_ms": r.processing_time_ms,
                    "metadata": r.metadata,
                }
                for r in self.processing_history
            ],
            "final_status": (
                self.processing_history[-1].status.value
                if self.processing_history
                else "not_processed"
            ),
            "total_processing_time_ms": sum(
                r.processing_time_ms for r in self.processing_history
            ),
            "processing_context": self.processing_context,
        }

    def __str__(self):
        return f"Content({self.content_id}, {self.content_type.value})"


class CircuitBreaker:
    """Circuit breaker pattern for failing processors"""

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class ContentProcessor(ABC):
    """Abstract base class for content processors"""

    def __init__(
        self,
        name: Optional[str] = None,
        parallel_capable: bool = False,
        retry_enabled: bool = True,
        max_retries: int = 3,
        use_circuit_breaker: bool = True,
    ):
        self.name = name or self.__class__.__name__
        self.parallel_capable = parallel_capable
        self.retry_enabled = retry_enabled
        self.max_retries = max_retries
        self._next: Optional[ContentProcessor] = None
        self.logger = logging.getLogger(f"processor.{self.name}")

        # Circuit breaker for reliability
        self.circuit_breaker = CircuitBreaker() if use_circuit_breaker else None

        # Metrics tracking
        self.total_processed = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_processing_time = 0.0
        self.skip_count = 0

    def set_next(self, processor: "ContentProcessor") -> "ContentProcessor":
        """Set the next processor in the chain"""
        self._next = processor
        return processor

    @abstractmethod
    def can_process(self, content: Content) -> bool:
        """Check if this processor can handle the given content type"""
        pass

    @abstractmethod
    def _process_content(self, content: Content) -> ProcessingResult:
        """The actual processing logic - implement in subclasses"""
        pass

    def process(self, content: Content) -> ProcessingResult:
        """Main processing method with retry logic, timing, and error handling"""
        # Check if processor can handle this content
        if not self.can_process(content):
            result = ProcessingResult(
                status=ProcessingStatus.SKIPPED,
                processor_name=self.name,
                reason=f"cannot_process_{content.content_type.value}",
            )
            content.add_result(result)
            self.skip_count += 1
            self.logger.debug(
                f"Skipping {content} - cannot process {content.content_type}"
            )
            return self._forward(content)

        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_execute():
            result = ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="circuit_breaker_open",
            )
            content.add_result(result)
            self.failure_count += 1
            self.logger.error(
                f"Circuit breaker open for {self.name}, failing {content}"
            )
            return result

        # Processing with retry logic
        attempt = 0
        last_result = None

        while attempt <= self.max_retries:
            attempt += 1
            start_time = time.time()

            try:
                self.logger.debug(
                    f"Processing {content} with {self.name} (attempt {attempt})"
                )
                result = self._process_content(content)
                result.processing_time_ms = (time.time() - start_time) * 1000
                content.add_result(result)
                last_result = result

                # Update metrics
                self.total_processed += 1
                self.total_processing_time += result.processing_time_ms

                if result.status == ProcessingStatus.SUCCESS:
                    self.success_count += 1
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    self.logger.info(f"✅ {self.name} successfully processed {content}")
                    break
                elif result.status == ProcessingStatus.WARNING:
                    self.success_count += 1  # Warnings are still successful
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    self.logger.warning(
                        f"⚠️ {self.name} warning for {content}: {result.reason}"
                    )
                    break
                else:
                    self.failure_count += 1
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure()

                    if not self.retry_enabled or attempt > self.max_retries:
                        self.logger.error(
                            f"❌ {self.name} failed {content} after {attempt} attempts: {result.reason}"
                        )
                        return result
                    else:
                        self.logger.warning(
                            f"🔄 {self.name} retry {attempt}/{self.max_retries} for {content}: {result.reason}"
                        )

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                result = ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    processor_name=self.name,
                    reason=f"exception: {str(e)}",
                    processing_time_ms=processing_time,
                )
                content.add_result(result)
                last_result = result

                self.total_processed += 1
                self.failure_count += 1
                self.total_processing_time += processing_time

                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()

                self.logger.error(
                    f"💥 {self.name} exception on attempt {attempt} for {content}: {str(e)}"
                )

                if not self.retry_enabled or attempt > self.max_retries:
                    return result

        return self._forward(content)

    def _forward(self, content: Content) -> ProcessingResult:
        """Forward to next processor or complete chain"""
        if self._next:
            return self._next.process(content)

        # End of chain - determine final status
        if content.processing_history:
            final_status = content.processing_history[-1].status
            if final_status in [ProcessingStatus.SUCCESS, ProcessingStatus.WARNING]:
                return ProcessingResult(
                    status=ProcessingStatus.SUCCESS,
                    processor_name="ChainCompleted",
                    reason="processing_chain_completed",
                )

        return ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            processor_name="ChainCompleted",
            reason="end_of_chain",
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics"""
        avg_time = (
            (self.total_processing_time / self.total_processed)
            if self.total_processed > 0
            else 0.0
        )

        success_rate = (
            (self.success_count / self.total_processed)
            if self.total_processed > 0
            else 0.0
        )

        return {
            "processor_name": self.name,
            "total_processed": self.total_processed,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "skip_count": self.skip_count,
            "success_rate": success_rate,
            "average_processing_time_ms": avg_time,
            "circuit_breaker_state": (
                self.circuit_breaker.state if self.circuit_breaker else "disabled"
            ),
            "parallel_capable": self.parallel_capable,
        }


class ContentSanitizer(ContentProcessor):
    """Removes dangerous HTML, scripts, and normalizes content"""

    def __init__(self):
        super().__init__(name="ContentSanitizer", parallel_capable=True)
        self.dangerous_patterns = [
            "<script",
            "</script>",
            "javascript:",
            "onclick=",
            "onerror=",
            "<iframe",
            "<object",
            "<embed",
            "onload=",
            "onmouseover=",
            "eval(",
            "document.cookie",
            "window.location",
        ]

    def can_process(self, content: Content) -> bool:
        return content.text is not None

    def _process_content(self, content: Content) -> ProcessingResult:
        """Sanitize content by removing dangerous patterns"""
        original_text = content.text or ""
        sanitized_text = original_text
        removed_patterns = []

        for pattern in self.dangerous_patterns:
            if pattern in sanitized_text:
                removed_patterns.append(pattern)
                sanitized_text = sanitized_text.replace(pattern, "[REMOVED]")

        content.text = sanitized_text
        content.processing_context["sanitized"] = True
        content.processing_context["removed_patterns"] = removed_patterns

        status = (
            ProcessingStatus.WARNING if removed_patterns else ProcessingStatus.SUCCESS
        )
        reason = (
            f"removed_dangerous_content: {removed_patterns}"
            if removed_patterns
            else "content_clean"
        )

        return ProcessingResult(
            status=status,
            processor_name=self.name,
            reason=reason,
            metadata={
                "original_length": len(original_text),
                "sanitized_length": len(sanitized_text),
                "removed_patterns": removed_patterns,
            },
        )


class ProfanityFilter(ContentProcessor):
    """Detects and handles inappropriate language"""

    def __init__(self, action: str = "flag"):  # flag, censor, reject
        super().__init__(name="ProfanityFilter", parallel_capable=True)
        self.action = action
        self.profanity_words = [
            "badword1",
            "badword2",
            "inappropriate",
            "spam",
            "hate",
            "offensive",
            "toxic",
            "abusive",
        ]

    def can_process(self, content: Content) -> bool:
        return content.text is not None

    def _process_content(self, content: Content) -> ProcessingResult:
        """Check for profanity and handle according to action setting"""
        text = (content.text or "").lower()
        found_profanity = [word for word in self.profanity_words if word in text]

        if not found_profanity:
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                processor_name=self.name,
                reason="no_profanity_detected",
            )

        content.processing_context["profanity_detected"] = found_profanity

        if self.action == "flag":
            content.processing_context["profanity_flagged"] = True
            return ProcessingResult(
                status=ProcessingStatus.WARNING,
                processor_name=self.name,
                reason="profanity_flagged",
                metadata={"words": found_profanity, "action": "flagged"},
            )
        elif self.action == "censor":
            censored_text = content.text or ""
            for word in found_profanity:
                censored_text = censored_text.replace(word, "*" * len(word))
            content.text = censored_text
            content.processing_context["profanity_censored"] = found_profanity
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                processor_name=self.name,
                reason="profanity_censored",
                metadata={"words": found_profanity, "action": "censored"},
            )
        elif self.action == "reject":
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="profanity_rejected",
                metadata={"words": found_profanity, "action": "rejected"},
            )

        return ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            processor_name=self.name,
            reason="unknown_action",
        )


class SpamDetector(ContentProcessor):
    """ML-based spam detection (simplified simulation)"""

    def __init__(self, threshold: float = 0.7):
        super().__init__(name="SpamDetector", parallel_capable=True)
        self.threshold = threshold
        self.spam_indicators = [
            "buy now",
            "click here",
            "limited time",
            "free offer",
            "act now",
            "guaranteed",
            "no risk",
            "100% free",
            "urgent",
            "expires today",
            "make money fast",
            "work from home",
            "lose weight fast",
        ]

    def can_process(self, content: Content) -> bool:
        return content.text is not None

    def _process_content(self, content: Content) -> ProcessingResult:
        """Detect spam using simulated ML scoring"""
        text = (content.text or "").lower()

        # Count spam indicators
        matches = [phrase for phrase in self.spam_indicators if phrase in text]
        score = len(matches) / len(self.spam_indicators) if self.spam_indicators else 0

        # Additional heuristics
        if len(text) > 0:
            caps_ratio = sum(1 for c in content.text or "" if c.isupper()) / len(
                content.text or "X"
            )
            exclamation_count = text.count("!")
            if caps_ratio > 0.5:  # More than 50% caps
                score += 0.2
            if exclamation_count > 3:  # More than 3 exclamation marks
                score += 0.1

        score = min(score, 1.0)  # Cap at 1.0
        content.processing_context["spam_score"] = score
        content.processing_context["spam_indicators"] = matches

        if score >= self.threshold:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="spam_detected",
                metadata={
                    "spam_score": score,
                    "threshold": self.threshold,
                    "indicators": matches,
                },
            )
        elif score >= self.threshold * 0.8:  # Warning threshold
            return ProcessingResult(
                status=ProcessingStatus.WARNING,
                processor_name=self.name,
                reason="potential_spam",
                metadata={
                    "spam_score": score,
                    "threshold": self.threshold,
                    "indicators": matches,
                },
            )

        return ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            processor_name=self.name,
            reason="not_spam",
            metadata={"spam_score": score},
        )


class ImageProcessor(ContentProcessor):
    """Handles image uploads, thumbnails, NSFW detection"""

    def __init__(self):
        super().__init__(name="ImageProcessor", parallel_capable=False)
        self.supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    def can_process(self, content: Content) -> bool:
        return (
            content.content_type in {ContentType.IMAGE, ContentType.MIXED}
            and content.image_data is not None
        )

    def _process_content(self, content: Content) -> ProcessingResult:
        """Process images - create thumbnails, check NSFW"""
        if not content.image_data:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="no_image_data",
            )

        # Simulate image processing
        image_size = len(content.image_data)

        # Simulate format detection
        if image_size < 100:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="image_too_small",
            )

        # Simulate NSFW detection (based on content size for demo)
        nsfw_score = min((image_size % 100) / 100, 0.9)  # Simulate ML score

        # Simulate thumbnail generation
        thumbnail_size = min(image_size // 4, 50000)  # Simulate compression

        metadata = {
            "original_size_bytes": image_size,
            "thumbnail_size_bytes": thumbnail_size,
            "nsfw_score": nsfw_score,
            "format": "jpeg",  # Simulated
            "dimensions": "1024x768",  # Simulated
        }

        # Store processing results
        content.processing_context.update(
            {
                "image_processed": True,
                "thumbnail_url": f"https://cdn.example.com/{content.content_id}/thumb.jpg",
                "nsfw_score": nsfw_score,
                "image_metadata": metadata,
            }
        )

        # Check NSFW threshold
        if nsfw_score > 0.8:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="nsfw_content_detected",
                metadata=metadata,
            )
        elif nsfw_score > 0.6:
            return ProcessingResult(
                status=ProcessingStatus.WARNING,
                processor_name=self.name,
                reason="potentially_nsfw",
                metadata=metadata,
            )

        return ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            processor_name=self.name,
            reason="image_processed",
            metadata=metadata,
        )


class ContentEnricher(ContentProcessor):
    """Adds metadata, extracts hashtags, mentions, etc."""

    def __init__(self):
        super().__init__(name="ContentEnricher", parallel_capable=True)

    def can_process(self, content: Content) -> bool:
        return True  # Can process any content type

    def _process_content(self, content: Content) -> ProcessingResult:
        """Enrich content with metadata"""
        text = content.text or ""

        # Extract hashtags and mentions
        words = text.split()
        hashtags = [word for word in words if word.startswith("#") and len(word) > 1]
        mentions = [word for word in words if word.startswith("@") and len(word) > 1]

        # Basic text analysis
        word_count = len([word for word in words if word.strip()])
        char_count = len(text)
        sentence_count = len([s for s in text.split(".") if s.strip()])

        # Simulate sentiment analysis
        positive_words = [
            "good",
            "great",
            "awesome",
            "excellent",
            "love",
            "happy",
            "amazing",
        ]
        negative_words = [
            "bad",
            "terrible",
            "hate",
            "awful",
            "horrible",
            "sad",
            "angry",
        ]

        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())

        if positive_count > negative_count:
            sentiment_score = 0.6 + (positive_count * 0.1)
        elif negative_count > positive_count:
            sentiment_score = 0.4 - (negative_count * 0.1)
        else:
            sentiment_score = 0.5

        sentiment_score = max(0.0, min(1.0, sentiment_score))  # Clamp between 0 and 1

        # Language detection (simplified)
        language = "en"  # Simulated

        # Content categorization (simplified)
        tech_words = ["code", "programming", "software", "technology", "computer"]
        sports_words = ["game", "sport", "team", "player", "match", "score"]

        categories = []
        if any(word in text.lower() for word in tech_words):
            categories.append("technology")
        if any(word in text.lower() for word in sports_words):
            categories.append("sports")
        if hashtags:
            categories.append("social")
        if not categories:
            categories.append("general")

        enrichment_data = {
            "hashtags": hashtags,
            "mentions": mentions,
            "word_count": word_count,
            "char_count": char_count,
            "sentence_count": sentence_count,
            "sentiment_score": sentiment_score,
            "language": language,
            "categories": categories,
            "readability_score": min(
                sentence_count / max(word_count, 1) * 10, 10
            ),  # Simplified
            "engagement_prediction": sentiment_score
            * len(hashtags)
            * 0.1,  # Simplified
        }

        # Store enrichment data
        content.processing_context.update(enrichment_data)
        content.processing_context["enriched"] = True

        return ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            processor_name=self.name,
            reason="content_enriched",
            metadata=enrichment_data,
        )


class ContentPublisher(ContentProcessor):
    """Final step - publishes content to appropriate channels"""

    def __init__(self):
        super().__init__(name="ContentPublisher", parallel_capable=False)
        self.channels = {
            ContentType.TEXT: ["main_feed", "search_index", "text_archive"],
            ContentType.IMAGE: ["main_feed", "image_gallery", "search_index"],
            ContentType.VIDEO: ["main_feed", "video_platform", "search_index"],
            ContentType.MIXED: ["main_feed", "search_index", "multimedia_archive"],
        }

    def can_process(self, content: Content) -> bool:
        return True  # Can publish any content type

    def _process_content(self, content: Content) -> ProcessingResult:
        """Publish content to appropriate channels"""
        channels = self.channels.get(content.content_type, ["main_feed"])

        # Check if content should be published based on processing context
        spam_score = content.processing_context.get("spam_score", 0)
        nsfw_score = content.processing_context.get("nsfw_score", 0)

        published_channels = []
        skipped_channels = []

        for channel in channels:
            # Apply channel-specific rules
            should_publish = True
            skip_reason = None

            if channel == "main_feed":
                if spam_score > 0.8:
                    should_publish = False
                    skip_reason = "high_spam_score"
                elif nsfw_score > 0.7:
                    should_publish = False
                    skip_reason = "nsfw_content"
            elif channel == "image_gallery":
                if nsfw_score > 0.5:
                    should_publish = False
                    skip_reason = "nsfw_content"

            if should_publish:
                published_channels.append(channel)
                self.logger.info(f"Published {content.content_id} to {channel}")
            else:
                skipped_channels.append({"channel": channel, "reason": skip_reason})
                self.logger.warning(
                    f"Skipped publishing {content.content_id} to {channel}: {skip_reason}"
                )

        # Store publication info
        content.processing_context.update(
            {
                "published_channels": published_channels,
                "skipped_channels": skipped_channels,
                "publication_timestamp": datetime.utcnow().isoformat(),
                "published": len(published_channels) > 0,
            }
        )

        if not published_channels:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name=self.name,
                reason="no_channels_available",
                metadata={
                    "attempted_channels": channels,
                    "skipped_channels": skipped_channels,
                },
            )

        return ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            processor_name=self.name,
            reason="content_published",
            metadata={
                "published_channels": published_channels,
                "skipped_channels": skipped_channels,
                "total_channels": len(published_channels),
            },
        )


class ContentCache:
    """Content deduplication and caching system"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Content] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}

    def get_content_hash(self, content: Content) -> str:
        """Generate hash for content deduplication"""
        text_hash = hashlib.md5((content.text or "").encode()).hexdigest()
        image_hash = hashlib.md5(content.image_data or b"").hexdigest()
        return (
            f"{content.content_type.value}_{text_hash}_{image_hash}_{content.user_id}"
        )

    def get(self, content_hash: str) -> Optional[Content]:
        if content_hash in self.cache:
            self.access_times[content_hash] = time.time()
            return self.cache[content_hash]
        return None

    def put(self, content_hash: str, content: Content):
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest_hash = min(
                self.access_times.keys(), key=lambda k: self.access_times[k]
            )
            del self.cache[oldest_hash]
            del self.access_times[oldest_hash]

        self.cache[content_hash] = content
        self.access_times[content_hash] = time.time()


class ProcessingPipeline:
    """Manages and orchestrates the content processing pipeline"""

    def __init__(self, name: str):
        self.name = name
        self.processors: List[ContentProcessor] = []
        self.logger = logging.getLogger(f"pipeline.{name}")
        self.metrics = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0,
            "cached_hits": 0,
        }
        self.cache = ContentCache()

    def add_processor(self, processor: ContentProcessor) -> "ProcessingPipeline":
        """Add a processor to the pipeline"""
        if self.processors:
            self.processors[-1].set_next(processor)
        self.processors.append(processor)
        return self

    def create_chain_for_content_type(
        self, content_type: ContentType
    ) -> Optional[ContentProcessor]:
        """Create a processing chain optimized for specific content type"""
        if content_type == ContentType.TEXT:
            chain = ContentSanitizer()
            chain.set_next(ProfanityFilter()).set_next(SpamDetector()).set_next(
                ContentEnricher()
            ).set_next(ContentPublisher())
            return chain
        elif content_type == ContentType.IMAGE:
            chain = ContentSanitizer()
            chain.set_next(ImageProcessor()).set_next(ProfanityFilter()).set_next(
                ContentEnricher()
            ).set_next(ContentPublisher())
            return chain
        elif content_type == ContentType.VIDEO:
            chain = ContentSanitizer()
            chain.set_next(ProfanityFilter()).set_next(SpamDetector()).set_next(
                ContentEnricher()
            ).set_next(ContentPublisher())
            return chain
        elif content_type == ContentType.MIXED:
            chain = ContentSanitizer()
            chain.set_next(ImageProcessor()).set_next(ProfanityFilter()).set_next(
                SpamDetector()
            ).set_next(ContentEnricher()).set_next(ContentPublisher())
            return chain
        return None

    def process_content(self, content: Content) -> ProcessingResult:
        """Process content with caching support"""
        start_time = time.time()

        # Check cache for duplicate content
        content_hash = self.cache.get_content_hash(content)
        cached_content = self.cache.get(content_hash)

        if cached_content and cached_content.content_id != content.content_id:
            self.logger.info(
                f"Cache hit for similar content, reusing processing results"
            )
            # Copy cached processing results to new content
            content.processing_context = cached_content.processing_context.copy()
            content.processing_history = [
                ProcessingResult(
                    status=ProcessingStatus.SUCCESS,
                    processor_name="ContentCache",
                    reason="cached_result_reused",
                    metadata={"original_content_id": cached_content.content_id},
                )
            ]
            self.metrics["cached_hits"] += 1
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                processor_name="Pipeline",
                reason="cached_processing_used",
            )

        # Create appropriate processing chain
        chain = self.create_chain_for_content_type(content.content_type)
        if not chain:
            self.logger.error(
                f"No processing chain available for {content.content_type}"
            )
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processor_name="Pipeline",
                reason="no_chain_available",
            )

        # Process content through the chain
        self.logger.info(f"🚀 Starting processing pipeline for {content}")
        result = chain.process(content)

        # Cache successful processing results
        if result.status == ProcessingStatus.SUCCESS:
            self.cache.put(content_hash, content)

        # Update pipeline metrics
        processing_time = (time.time() - start_time) * 1000
        self.metrics["total_processed"] += 1
        self.metrics["total_time"] += processing_time

        if result.status == ProcessingStatus.SUCCESS:
            self.metrics["successful"] += 1
            self.logger.info(
                f"✅ Pipeline completed successfully for {content} in {processing_time:.2f}ms"
            )
        else:
            self.metrics["failed"] += 1
            self.logger.error(f"❌ Pipeline failed for {content}: {result.reason}")

        return result

    async def process_content_async(self, content: Content) -> ProcessingResult:
        """Process content asynchronously (placeholder for future async implementation)"""
        # For now, just wrap synchronous processing
        return await asyncio.get_event_loop().run_in_executor(
            None, self.process_content, content
        )

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get overall pipeline performance metrics"""
        processor_metrics = [processor.get_metrics() for processor in self.processors]

        avg_time = (
            self.metrics["total_time"] / self.metrics["total_processed"]
            if self.metrics["total_processed"] > 0
            else 0.0
        )

        success_rate = (
            self.metrics["successful"] / self.metrics["total_processed"]
            if self.metrics["total_processed"] > 0
            else 0.0
        )

        cache_hit_rate = (
            self.metrics["cached_hits"] / self.metrics["total_processed"]
            if self.metrics["total_processed"] > 0
            else 0.0
        )

        return {
            "pipeline_name": self.name,
            "total_processed": self.metrics["total_processed"],
            "successful": self.metrics["successful"],
            "failed": self.metrics["failed"],
            "success_rate": success_rate,
            "average_processing_time_ms": avg_time,
            "cache_hit_rate": cache_hit_rate,
            "cached_hits": self.metrics["cached_hits"],
            "processor_metrics": processor_metrics,
        }

    def get_processing_report(self, content: Content) -> Dict[str, Any]:
        """Generate detailed processing report for content"""
        return content.get_processing_summary()

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify processing bottlenecks"""
        bottlenecks = []
        for processor in self.processors:
            metrics = processor.get_metrics()
            if (
                metrics["average_processing_time_ms"] > 1000  # Slow processors
                or metrics["success_rate"] < 0.9
            ):  # Unreliable processors
                bottlenecks.append(
                    {
                        "processor": processor.name,
                        "issue": (
                            "slow_processing"
                            if metrics["average_processing_time_ms"] > 1000
                            else "low_success_rate"
                        ),
                        "metrics": metrics,
                    }
                )
        return bottlenecks


class PipelineBuilder:
    """Utility class for building different types of pipelines"""

    @staticmethod
    def create_standard_pipeline() -> ProcessingPipeline:
        """Create a standard content processing pipeline"""
        pipeline = ProcessingPipeline(name="StandardPipeline")
        pipeline.add_processor(ContentSanitizer())
        pipeline.add_processor(ProfanityFilter(action="flag"))
        pipeline.add_processor(SpamDetector(threshold=0.7))
        pipeline.add_processor(ImageProcessor())
        pipeline.add_processor(ContentEnricher())
        pipeline.add_processor(ContentPublisher())
        return pipeline

    @staticmethod
    def create_fast_pipeline() -> ProcessingPipeline:
        """Create a faster pipeline with fewer checks (for trusted content)"""
        pipeline = ProcessingPipeline(name="FastPipeline")
        pipeline.add_processor(ContentSanitizer())
        pipeline.add_processor(ContentEnricher())
        pipeline.add_processor(ContentPublisher())
        return pipeline

    @staticmethod
    def create_strict_pipeline() -> ProcessingPipeline:
        """Create a strict pipeline with enhanced security/moderation"""
        pipeline = ProcessingPipeline(name="StrictPipeline")
        pipeline.add_processor(ContentSanitizer())
        pipeline.add_processor(ProfanityFilter(action="reject"))
        pipeline.add_processor(SpamDetector(threshold=0.5))
        pipeline.add_processor(ImageProcessor())
        pipeline.add_processor(ContentEnricher())
        pipeline.add_processor(ContentPublisher())
        return pipeline

    @staticmethod
    def create_image_pipeline() -> ProcessingPipeline:
        """Create a pipeline optimized for image content"""
        pipeline = ProcessingPipeline(name="ImagePipeline")
        pipeline.add_processor(ContentSanitizer())
        pipeline.add_processor(ImageProcessor())
        pipeline.add_processor(ProfanityFilter(action="flag"))
        pipeline.add_processor(ContentEnricher())
        pipeline.add_processor(ContentPublisher())
        return pipeline


class PipelineHealthCheck:
    """Health monitoring system for pipelines"""

    def __init__(self, pipeline: ProcessingPipeline):
        self.pipeline = pipeline
        self.health_thresholds = {
            "success_rate": 0.95,
            "avg_processing_time": 5000,  # ms
            "cache_hit_rate": 0.1,  # Minimum expected cache hit rate
        }

    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        metrics = self.pipeline.get_pipeline_metrics()
        bottlenecks = self.pipeline.get_bottlenecks()

        health_issues = []
        warnings = []

        # Check success rate
        success_rate = metrics.get("success_rate", 0)
        if success_rate < self.health_thresholds["success_rate"]:
            health_issues.append(f"Low success rate: {success_rate:.1%}")

        # Check processing time
        avg_time = metrics.get("average_processing_time_ms", 0)
        if avg_time > self.health_thresholds["avg_processing_time"]:
            health_issues.append(f"Slow processing: {avg_time:.1f}ms average")

        # Check cache performance
        cache_hit_rate = metrics.get("cache_hit_rate", 0)
        if cache_hit_rate < self.health_thresholds["cache_hit_rate"]:
            warnings.append(f"Low cache hit rate: {cache_hit_rate:.1%}")

        # Check for circuit breaker issues
        for processor_metrics in metrics.get("processor_metrics", []):
            if processor_metrics.get("circuit_breaker_state") == "OPEN":
                health_issues.append(
                    f"Circuit breaker open: {processor_metrics['processor_name']}"
                )

        # Determine overall health status
        if health_issues:
            status = "unhealthy"
        elif warnings or bottlenecks:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "issues": health_issues,
            "warnings": warnings,
            "bottlenecks": bottlenecks,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Test framework and sample usage
def create_test_content() -> List[Content]:
    """Create comprehensive sample content for testing"""
    return [
        # Clean text content
        Content(
            content_id="test_001",
            content_type=ContentType.TEXT,
            text="Hello world! This is a test post #testing @user1 Great content here!",
            user_id="user123",
        ),
        # Content with profanity
        Content(
            content_id="test_002",
            content_type=ContentType.TEXT,
            text="This contains badword1 and inappropriate content that should be flagged",
            user_id="user456",
        ),
        # Image content
        Content(
            content_id="test_003",
            content_type=ContentType.IMAGE,
            text="Check out this amazing photo! #photography @photographer",
            image_data=b"fake_image_data_here_with_sufficient_length_to_simulate_real_image",
            user_id="user789",
        ),
        # Spam content
        Content(
            content_id="test_004",
            content_type=ContentType.TEXT,
            text="<script>alert('xss')</script>BUY NOW! Amazing deal! Limited time! Click here! FREE OFFER! Act now!",
            user_id="spammer123",
        ),
        # Mixed content
        Content(
            content_id="test_005",
            content_type=ContentType.MIXED,
            text="Mixed content with image and text #mixed @everyone",
            image_data=b"another_fake_image_with_different_content_for_variety",
            user_id="user999",
        ),
        # Duplicate content (for cache testing)
        Content(
            content_id="test_006",
            content_type=ContentType.TEXT,
            text="Hello world! This is a test post #testing @user1 Great content here!",  # Same as test_001
            user_id="user123",
        ),
        # Edge case: empty content
        Content(
            content_id="test_007",
            content_type=ContentType.TEXT,
            text="",
            user_id="edge_case_user",
        ),
        # Long content
        Content(
            content_id="test_008",
            content_type=ContentType.TEXT,
            text="This is a very long piece of content " * 50
            + "#long @verbose great excellent awesome amazing",
            user_id="verbose_user",
        ),
    ]


def run_comprehensive_test():
    """Run comprehensive testing of the pipeline system"""
    print("🧪 COMPREHENSIVE CONTENT PROCESSING PIPELINE TEST")
    print("=" * 60)

    # Test different pipeline configurations
    pipelines = {
        "Standard": PipelineBuilder.create_standard_pipeline(),
        "Fast": PipelineBuilder.create_fast_pipeline(),
        "Strict": PipelineBuilder.create_strict_pipeline(),
        "Image": PipelineBuilder.create_image_pipeline(),
    }

    test_content = create_test_content()

    for pipeline_name, pipeline in pipelines.items():
        print(f"\n🔧 Testing {pipeline_name} Pipeline")
        print("-" * 40)

        health_checker = PipelineHealthCheck(pipeline)

        for content in test_content[:4]:  # Test first 4 items for each pipeline
            print(f"\n📄 Processing {content}")
            result = pipeline.process_content(content)

            # Display results
            print(f"   Result: {result.status.value} - {result.reason}")

            # Show key processing context
            context = content.processing_context
            interesting_keys = [
                "sanitized",
                "profanity_flagged",
                "spam_score",
                "published_channels",
            ]
            context_info = {k: v for k, v in context.items() if k in interesting_keys}
            if context_info:
                print(f"   Context: {context_info}")

        # Pipeline metrics
        metrics = pipeline.get_pipeline_metrics()
        print(f"\n📊 {pipeline_name} Pipeline Metrics:")
        print(
            f"   Processed: {metrics['total_processed']}, Success Rate: {metrics['success_rate']:.1%}"
        )
        print(f"   Avg Time: {metrics['average_processing_time_ms']:.1f}ms")
        print(f"   Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")

        # Health check
        health = health_checker.check_health()
        print(f"   Health Status: {health['status'].upper()}")
        if health["issues"]:
            print(f"   Issues: {health['issues']}")
        if health["warnings"]:
            print(f"   Warnings: {health['warnings']}")

    # Test cache functionality
    print(f"\n💾 Cache Testing")
    print("-" * 40)
    standard_pipeline = pipelines["Standard"]

    # Process same content multiple times to test cache
    duplicate_content = test_content[0]  # Use first test content
    for i in range(3):
        duplicate_content.content_id = f"cache_test_{i}"
        result = standard_pipeline.process_content(duplicate_content)
        print(f"   Attempt {i+1}: {result.reason}")

    final_metrics = standard_pipeline.get_pipeline_metrics()
    print(f"   Final Cache Hit Rate: {final_metrics['cache_hit_rate']:.1%}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run comprehensive tests
    run_comprehensive_test()

    print(f"\n" + "=" * 60)
    print("🎯 INDIVIDUAL CONTENT PROCESSING DEMO")
    print("=" * 60)

    # Demo individual content processing with detailed output
    pipeline = PipelineBuilder.create_standard_pipeline()
    test_content = create_test_content()

    for content in test_content[:3]:  # Show detailed results for first 3
        print(f"\n{'='*20} Processing {content} {'='*20}")
        result = pipeline.process_content(content)

        # Show detailed processing report
        report = pipeline.get_processing_report(content)
        print(f"\n📋 Detailed Processing Report:")
        print(json.dumps(report, indent=2, default=str))

        print(f"\n🏁 Final Result: {result}")

    print(f"\n{'='*20} Pipeline Performance Summary {'='*20}")
    final_metrics = pipeline.get_pipeline_metrics()
    print(json.dumps(final_metrics, indent=2))

    # Health check
    health_check = PipelineHealthCheck(pipeline)
    health = health_check.check_health()
    print(f"\n🏥 Pipeline Health Report:")
    print(json.dumps(health, indent=2, default=str))
