"""
Comment monitoring module.
Supports tracking specific users or monitoring subreddits by keyword.
"""

import logging
from typing import Generator
import praw

logger = logging.getLogger(__name__)


class CommentMonitor:
    """Monitors Reddit for new comments matching specified criteria."""

    def __init__(self, reddit: praw.Reddit):
        self.reddit = reddit

    def get_user_comments(self, username: str,
                          since: float) -> Generator[praw.models.Comment, None, None]:
        """
        Fetch new comments from a specific user since a given timestamp.

        Args:
            username: Reddit username to monitor
            since: Unix timestamp — only return comments newer than this
        """
        redditor = self.reddit.redditor(username)
        count = 0
        for comment in redditor.comments.new(limit=100):
            if comment.created_utc > since:
                count += 1
                yield comment
            else:
                break
        logger.info(f"Found {count} new comments from u/{username}")

    def get_subreddit_comments(self, subreddit_name: str, since: float,
                               keywords: list[str] | None = None
                               ) -> Generator[praw.models.Comment, None, None]:
        """
        Fetch new comments from a subreddit, optionally filtered by keywords.

        Args:
            subreddit_name: Subreddit to monitor (without r/ prefix)
            since: Unix timestamp — only return comments newer than this
            keywords: Optional list of keywords to match (case-insensitive)
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        count = 0
        for comment in subreddit.comments(limit=100):
            if comment.created_utc <= since:
                continue
            if keywords and not self._matches_keywords(comment.body, keywords):
                continue
            count += 1
            yield comment
        logger.info(
            f"Found {count} matching comments in r/{subreddit_name}"
            + (f" (keywords: {keywords})" if keywords else "")
        )

    @staticmethod
    def _matches_keywords(text: str, keywords: list[str]) -> bool:
        """Check if text contains any of the specified keywords (case-insensitive)."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
