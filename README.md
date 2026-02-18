# Reddit AI Auto-Replier

An intelligent Reddit bot that monitors subreddits or specific users and generates contextual replies using LLM APIs (OpenAI, Anthropic Claude, or local models via Ollama).

## Features

- **AI-Powered Replies** — Generates context-aware responses using GPT-4, Claude, or local LLMs via Ollama
- **Dual Monitoring Modes** — Track specific users or monitor entire subreddits by keyword
- **Multi-Account Rotation** — Distribute replies across multiple Reddit accounts to respect rate limits
- **Customizable Prompts** — Define system prompts and reply templates per subreddit or topic
- **Rate Limit Handling** — Exponential backoff with configurable retry logic
- **Duplicate Prevention** — Tracks replied comments to avoid double-posting
- **Persistent State** — Saves last run timestamp to resume without reprocessing old comments

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Reddit API     │────▶│  Comment Monitor  │────▶│  Reply Filter   │
│  (PRAW)         │     │  (User/Subreddit) │     │  (Keyword/Time) │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Reddit Post    │◀────│  Account Rotator  │◀────│  LLM Generator  │
│  (Rate Limited) │     │  (Multi-Account)  │     │  (GPT/Claude/   │
└─────────────────┘     └──────────────────┘     │   Ollama)       │
                                                  └─────────────────┘
```

## Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/miao0044/reddit-AI-replier.git
cd reddit-AI-replier
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Reddit API credentials and LLM API key:

```env
# Reddit credentials (create app at https://www.reddit.com/prefs/apps)
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# LLM provider: "openai", "anthropic", or "ollama"
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3
```

### 3. Customize the System Prompt

Edit `prompts/default.txt` to define how the AI should respond:

```
You are a helpful and knowledgeable Reddit user. Reply to the following 
comment naturally and conversationally. Keep responses concise (2-4 sentences) 
and relevant to the topic. Do not mention that you are an AI or bot.
```

### 4. Run

```bash
# Monitor a specific user's new comments
python reddit_bot.py --mode user --target USERNAME

# Monitor a subreddit for keyword matches
python reddit_bot.py --mode subreddit --target SUBREDDIT --keywords "python,machine learning"

# Continuous monitoring with 60-second intervals
python reddit_bot.py --mode subreddit --target learnpython --loop --interval 60
```

## Configuration

| Parameter | Env Variable | CLI Flag | Default | Description |
|-----------|-------------|----------|---------|-------------|
| Reddit Username | `REDDIT_USERNAME` | — | — | Reddit account username |
| LLM Provider | `LLM_PROVIDER` | `--llm` | `openai` | AI backend: openai, anthropic, ollama |
| Monitor Mode | — | `--mode` | `user` | `user` or `subreddit` |
| Target | — | `--target` | — | Username or subreddit name |
| Keywords | — | `--keywords` | — | Comma-separated filter keywords |
| Sleep Duration | `SLEEP_DURATION` | `--interval` | `30` | Seconds between checks |
| Reply Delay | `REPLY_DELAY` | `--delay` | `10` | Seconds between replies |
| Max Replies | `MAX_REPLIES` | `--max` | `10` | Max replies per run |
| Loop Mode | — | `--loop` | `false` | Continuous monitoring |

## Project Structure

```
reddit-AI-replier/
├── reddit_bot.py          # Main bot entry point with CLI
├── config.py              # Configuration loader (env + CLI)
├── llm_client.py          # Unified LLM interface (OpenAI/Claude/Ollama)
├── monitor.py             # Comment monitoring & filtering
├── replier.py             # Reply posting with account rotation
├── state.py               # Persistent state management
├── prompts/
│   └── default.txt        # Default system prompt
├── requirements.txt
├── .env.example           # Template for environment variables
├── .gitignore
└── LICENSE
```

## Supported LLM Providers

| Provider | Model | Local/Cloud | Setup |
|----------|-------|-------------|-------|
| OpenAI | GPT-4o, GPT-4o-mini | Cloud | Set `OPENAI_API_KEY` |
| Anthropic | Claude Sonnet 4.5 | Cloud | Set `ANTHROPIC_API_KEY` |
| Ollama | Llama 3, Mistral, etc. | Local | Install [Ollama](https://ollama.ai), pull model |

## How It Works

1. **Monitor** — PRAW streams new comments from target user or subreddit
2. **Filter** — Comments are checked against keyword filters, time window, and duplicate list
3. **Generate** — Matching comments are sent to the LLM with the system prompt + comment context
4. **Reply** — Generated responses are posted via account rotation with rate limit handling
5. **Persist** — Replied comment IDs and timestamps are saved to prevent duplicates

## Rate Limiting & Safety

- Configurable delay between replies (default: 10s)
- Exponential backoff on Reddit API rate limits (up to 3 retries)
- Multi-account rotation distributes load
- Max replies per run cap prevents spam
- Duplicate tracking across sessions

## License

MIT License — see [LICENSE](LICENSE) for details.
