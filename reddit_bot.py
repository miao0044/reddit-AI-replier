#!/usr/bin/env python3
"""
Reddit AI Auto-Replier
Monitors Reddit comments and generates contextual AI-powered replies.
"""

import sys
import time
import logging
import praw
import prawcore
from pathlib import Path

from config import Config, RedditAccount
from llm_client import LLMClient
from monitor import CommentMonitor
from replier import Replier
from state import State

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("reddit-ai-replier")


def create_reddit_instance(account: RedditAccount) -> praw.Reddit:
    """Create an authenticated Reddit instance."""
    try:
        instance = praw.Reddit(
            username=account.username,
            password=account.password,
            client_id=account.client_id,
            client_secret=account.client_secret,
            user_agent=account.user_agent,
        )
        # Verify login
        _ = instance.user.me()
        logger.info(f"Authenticated as u/{account.username}")
        return instance
    except prawcore.exceptions.ResponseException as e:
        logger.error(f"Login failed for u/{account.username}: {e}")
        raise


def load_prompt(filepath: str) -> str:
    """Load system prompt from file."""
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"Prompt file not found: {filepath}, using default")
        return (
            "You are a helpful Reddit user. Reply naturally and concisely "
            "(2-4 sentences). Stay on topic. Do not reveal you are a bot."
        )
    return path.read_text(encoding="utf-8").strip()


def run_once(config: Config, monitor: CommentMonitor, replier: Replier,
             llm: LLMClient, state: State, system_prompt: str) -> int:
    """
    Execute one monitoring + reply cycle. Returns number of replies posted.
    """
    # Fetch comments based on mode
    if config.mode == "user":
        comments = list(monitor.get_user_comments(config.target, state.last_run_time))
    else:
        comments = list(monitor.get_subreddit_comments(
            config.target, state.last_run_time, config.keywords or None
        ))

    replies_posted = 0
    for comment in comments:
        if replies_posted >= config.max_replies:
            logger.info(f"Reached max replies ({config.max_replies}), stopping")
            break

        if state.is_replied(comment.id):
            logger.debug(f"Skipping already-replied comment {comment.id}")
            continue

        try:
            # Get parent context if available
            parent_context = None
            if hasattr(comment, "submission"):
                parent_context = comment.submission.title

            # Generate AI reply
            reply_text = llm.generate_reply(
                comment_body=comment.body,
                subreddit=str(comment.subreddit),
                system_prompt=system_prompt,
                parent_context=parent_context,
            )
            logger.info(f"Generated reply for {comment.id}: {reply_text[:80]}...")

            # Post reply
            if replier.post_reply(comment, reply_text):
                state.mark_replied(comment.id)
                replies_posted += 1

        except Exception as e:
            logger.error(f"Failed to process comment {comment.id}: {e}")
            continue

    state.update_run_time()
    return replies_posted


def main():
    config = Config.from_env_and_args()

    if not config.accounts:
        logger.error("No Reddit accounts configured. Set REDDIT_USERNAME in .env")
        sys.exit(1)
    if not config.target:
        logger.error("No target specified. Use --target USERNAME or --target SUBREDDIT")
        sys.exit(1)

    # Initialize components
    reddit_instances = []
    for account in config.accounts:
        try:
            reddit_instances.append(create_reddit_instance(account))
        except Exception:
            continue

    if not reddit_instances:
        logger.error("No Reddit accounts authenticated successfully")
        sys.exit(1)

    llm_kwargs = {"api_key": config.openai_api_key}
    if config.llm_provider == "anthropic":
        llm_kwargs = {"api_key": config.anthropic_api_key}
    elif config.llm_provider == "ollama":
        llm_kwargs = {"base_url": config.ollama_base_url, "model": config.ollama_model}

    monitor = CommentMonitor(reddit_instances[0])
    replier = Replier(reddit_instances, reply_delay=config.reply_delay)
    llm = LLMClient(config.llm_provider, **llm_kwargs)
    state = State()
    system_prompt = load_prompt(config.prompt_file)

    logger.info(f"Bot started | mode={config.mode} | target={config.target} | llm={config.llm_provider}")

    # Run loop
    try:
        while True:
            count = run_once(config, monitor, replier, llm, state, system_prompt)
            logger.info(f"Cycle complete: {count} replies posted")
            if not config.loop:
                break
            logger.info(f"Sleeping {config.sleep_duration}s before next cycle...")
            time.sleep(config.sleep_duration)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()
