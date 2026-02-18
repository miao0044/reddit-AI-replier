"""
Configuration loader for Reddit AI Replier.
Loads settings from environment variables (.env file) and CLI arguments.
"""

import os
import argparse
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RedditAccount:
    """Reddit account credentials."""
    username: str
    password: str
    client_id: str
    client_secret: str
    user_agent: str = "reddit-ai-replier/1.0"


@dataclass
class Config:
    """Application configuration."""
    # Reddit
    accounts: list[RedditAccount] = field(default_factory=list)
    # LLM
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Monitoring
    mode: str = "user"  # "user" or "subreddit"
    target: str = ""
    keywords: list[str] = field(default_factory=list)

    # Behavior
    sleep_duration: int = 30
    reply_delay: int = 10
    max_replies: int = 10
    loop: bool = False
    prompt_file: str = "prompts/default.txt"

    @classmethod
    def from_env_and_args(cls) -> "Config":
        """Load config from environment variables, then override with CLI args."""
        config = cls()

        # Load Reddit accounts from env
        username = os.getenv("REDDIT_USERNAME")
        if username:
            config.accounts.append(RedditAccount(
                username=username,
                password=os.getenv("REDDIT_PASSWORD", ""),
                client_id=os.getenv("REDDIT_CLIENT_ID", ""),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
                user_agent=os.getenv("REDDIT_USER_AGENT", "reddit-ai-replier/1.0"),
            ))

        # Load additional accounts (REDDIT_USERNAME_2, etc.)
        for i in range(2, 6):
            alt_user = os.getenv(f"REDDIT_USERNAME_{i}")
            if alt_user:
                config.accounts.append(RedditAccount(
                    username=alt_user,
                    password=os.getenv(f"REDDIT_PASSWORD_{i}", ""),
                    client_id=os.getenv(f"REDDIT_CLIENT_ID_{i}", ""),
                    client_secret=os.getenv(f"REDDIT_CLIENT_SECRET_{i}", ""),
                    user_agent=os.getenv(f"REDDIT_USER_AGENT_{i}", f"reddit-ai-replier/1.0-{i}"),
                ))

        # LLM settings
        config.llm_provider = os.getenv("LLM_PROVIDER", "openai")
        config.openai_api_key = os.getenv("OPENAI_API_KEY")
        config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        config.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        config.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

        # Behavior
        config.sleep_duration = int(os.getenv("SLEEP_DURATION", "30"))
        config.reply_delay = int(os.getenv("REPLY_DELAY", "10"))
        config.max_replies = int(os.getenv("MAX_REPLIES", "10"))

        # CLI overrides
        args = cls._parse_args()
        if args.mode:
            config.mode = args.mode
        if args.target:
            config.target = args.target
        if args.keywords:
            config.keywords = [k.strip() for k in args.keywords.split(",")]
        if args.llm:
            config.llm_provider = args.llm
        if args.interval:
            config.sleep_duration = args.interval
        if args.delay:
            config.reply_delay = args.delay
        if args.max:
            config.max_replies = args.max
        if args.prompt:
            config.prompt_file = args.prompt
        config.loop = args.loop

        return config

    @staticmethod
    def _parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Reddit AI Auto-Replier")
        parser.add_argument("--mode", choices=["user", "subreddit"], help="Monitoring mode")
        parser.add_argument("--target", help="Target username or subreddit")
        parser.add_argument("--keywords", help="Comma-separated keywords to filter")
        parser.add_argument("--llm", choices=["openai", "anthropic", "ollama"], help="LLM provider")
        parser.add_argument("--interval", type=int, help="Seconds between monitoring cycles")
        parser.add_argument("--delay", type=int, help="Seconds between replies")
        parser.add_argument("--max", type=int, help="Max replies per run")
        parser.add_argument("--loop", action="store_true", help="Run continuously")
        parser.add_argument("--prompt", help="Path to custom prompt file")
        return parser.parse_args()
