"""
Unified LLM client supporting OpenAI, Anthropic Claude, and Ollama backends.
Generates contextual replies based on Reddit comment content.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Multi-provider LLM client for generating Reddit replies."""

    def __init__(self, provider: str, **kwargs):
        self.provider = provider
        self._client = None
        self._model = None

        if provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=kwargs.get("api_key"))
            self._model = kwargs.get("model", "gpt-4o-mini")

        elif provider == "anthropic":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=kwargs.get("api_key"))
            self._model = kwargs.get("model", "claude-sonnet-4-20250514")

        elif provider == "ollama":
            import requests
            self._base_url = kwargs.get("base_url", "http://localhost:11434")
            self._model = kwargs.get("model", "llama3")
            # Verify Ollama is running
            try:
                resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
                resp.raise_for_status()
                logger.info(f"Connected to Ollama at {self._base_url}")
            except Exception as e:
                raise ConnectionError(f"Cannot connect to Ollama at {self._base_url}: {e}")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        logger.info(f"LLM client initialized: {provider} ({self._model})")

    def generate_reply(self, comment_body: str, subreddit: str,
                       system_prompt: str, parent_context: Optional[str] = None) -> str:
        """
        Generate a contextual reply to a Reddit comment.

        Args:
            comment_body: The comment text to reply to
            subreddit: Subreddit name for context
            system_prompt: System instructions for the LLM
            parent_context: Optional parent post/comment for additional context

        Returns:
            Generated reply text
        """
        user_message = self._build_user_message(comment_body, subreddit, parent_context)

        try:
            if self.provider == "openai":
                return self._generate_openai(system_prompt, user_message)
            elif self.provider == "anthropic":
                return self._generate_anthropic(system_prompt, user_message)
            elif self.provider == "ollama":
                return self._generate_ollama(system_prompt, user_message)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def _build_user_message(self, comment_body: str, subreddit: str,
                            parent_context: Optional[str] = None) -> str:
        parts = [f"Subreddit: r/{subreddit}"]
        if parent_context:
            parts.append(f"Parent context: {parent_context}")
        parts.append(f"Comment to reply to: {comment_body}")
        return "\n\n".join(parts)

    def _generate_openai(self, system_prompt: str, user_message: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()

    def _generate_anthropic(self, system_prompt: str, user_message: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=300,
        )
        return response.content[0].text.strip()

    def _generate_ollama(self, system_prompt: str, user_message: str) -> str:
        import requests
        response = requests.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
