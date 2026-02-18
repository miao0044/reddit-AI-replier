"""
Reply posting module with multi-account rotation and rate limit handling.
"""

import time
import logging
import praw
import prawcore

logger = logging.getLogger(__name__)


class Replier:
    """Posts replies to Reddit comments with account rotation and rate limiting."""

    def __init__(self, reddit_instances: list[praw.Reddit], reply_delay: int = 10):
        self.instances = reddit_instances
        self.reply_delay = reply_delay
        self._current_index = 0

    def post_reply(self, comment: praw.models.Comment, reply_text: str) -> bool:
        """
        Post a reply to a comment, rotating through available accounts.

        Returns True if reply was posted successfully, False otherwise.
        """
        instance = self._next_instance()
        username = self._get_username(instance)

        try:
            comment.reply(reply_text)
            logger.info(f"✓ Replied to comment {comment.id} via u/{username}")
            time.sleep(self.reply_delay)
            return True

        except prawcore.exceptions.Forbidden as e:
            logger.warning(f"Permission denied for u/{username} on comment {comment.id}: {e}")
            return False

        except praw.exceptions.RedditAPIException as e:
            return self._handle_rate_limit(e, comment, reply_text, username)

        except Exception as e:
            logger.error(f"Unexpected error replying to {comment.id}: {e}")
            return False

    def _handle_rate_limit(self, exception, comment, reply_text: str,
                           username: str, max_retries: int = 3) -> bool:
        """Handle Reddit API rate limits with exponential backoff."""
        for attempt in range(max_retries):
            for item in exception.items:
                if item.error_type == "RATELIMIT":
                    wait_time = self._parse_wait_time(item.message)
                    logger.warning(
                        f"Rate limited on u/{username}. "
                        f"Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    try:
                        comment.reply(reply_text)
                        return True
                    except praw.exceptions.RedditAPIException:
                        continue
        logger.error(f"Failed to reply to {comment.id} after {max_retries} retries")
        return False

    def _next_instance(self) -> praw.Reddit:
        """Round-robin account selection."""
        instance = self.instances[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.instances)
        return instance

    @staticmethod
    def _get_username(instance: praw.Reddit) -> str:
        try:
            return str(instance.user.me())
        except Exception:
            return "unknown"

    @staticmethod
    def _parse_wait_time(message: str) -> int:
        """Extract wait time from Reddit rate limit message."""
        import re
        match = re.search(r"(\d+)\s*(minute|second)", message.lower())
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            return value * 60 if "minute" in unit else value
        return 60  # Default fallback
