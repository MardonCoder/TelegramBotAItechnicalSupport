
# AI-Q&A Telegram Bot

A simple Telegram bot that answers user questions in Russian by looking up relevant sections from a “manual” (text file) and then sending the context‑aware prompt to OpenAI’s GPT-4o-mini model. It also tracks usage statistics (token counts and cost) in a local SQLite database.

## Features

- Loads a “manual” (plain‑text guide) and splits it into chunks  
- Precomputes embeddings for each chunk and uses cosine similarity to find the most relevant context for each incoming question  
- Caches repeated questions to save cost  
- Tracks total input/output tokens and cost in a local SQLite database (`stats.db`)  
- Periodically cleans up stats older than 30 days  
- Exposes `/stats` and `/clean` commands via Telegram  
- Configured entirely via environment variables

## Prerequisites

- Python 3.10+  
- A Telegram Bot token (via [@BotFather](https://t.me/BotFather))  
- An OpenAI API key  
- `git`

## Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/ai-qa-telegram-bot.git
   cd ai-qa-telegram-bot
Create & activate a virtual environment

python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate.bat   # Windows
Install dependencies

pip install -r requirements.txt
Configure environment

Copy the example files:

cp config.py.example config.py
cp .env.example .env
Open config.py (or edit your .env) and fill in your tokens:

AI_TOKEN      = "sk-..."
TG_BOT_TOKEN  = "123456789:ABC..."
Or in .env:

OPENAI_TOKEN=sk-...
TG_TOKEN=123456789:ABC...
Prepare your manual

Place your text guide in data/manual.txt.

(Optional) Create an example version in data/manual_example.txt and add the real file to .gitignore.

Usage
Run the bot:

python telegram_bot.py
Once it’s running, open your Telegram client, find your bot by its username, and start a chat:

/start or /help – Welcome message

/stats – Show total messages answered, total tokens used, and total cost

/clean – Delete stats older than 30 days

Just type any question in Russian, and the bot will reply with an answer based on your manual.

Project Structure
.
├── config.py.example    # template for your config.py
├── telegram_bot.py      # entry point for the Telegram bot
├── chat.py              # AIbot class: embedding, context lookup, chat completions
├── load_manual.py       # loads data/manual.txt
├── stats_db.py          # StatsDB class: SQLite storage & cleanup
├── data/
│   ├── manual.txt       # your private manual (ignored)
│   └── stats.db         # local SQLite database (ignored)
├── requirements.txt     # all Python dependencies
├── .gitignore
└── README.md
.gitignore Review
Your .gitignore looks solid. A few minor notes:

# Environment & secrets
*.env          # ignores .env and any file ending .env
config.py      # ensures your real config isn’t committed

# Data & DB
*.db           # ignores any .db file
data/          # ignores the entire data folder (so you can remove data/stats.db)

# Python artifacts
__pycache__/
*.py[cod]
venv/          # virtual environment

# Optional extras you might consider:
# .vscode/     # if you use VS Code
# .idea/       # if you use PyCharm
# .pytest_cache/
Redundancy: You have both *.db and data/stats.db. You can keep either; with data/ in place, you don’t need the specific data/stats.db line.

Coverage: This will also ignore any accidental SQLite files elsewhere in the project, which is usually what you want.

With this README and .gitignore, newcomers can clone, configure, and run your bot without ever seeing your real tokens or private data.
