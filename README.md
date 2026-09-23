# Stock Predictor

AI-powered stock market prediction dashboard with real-time analysis using Machine Learning (LightGBM).

## Features

- **AI Predictions** — Daily, Weekly, Monthly, and Yearly price forecasts
- **Real-time Prices** — Live WebSocket price updates
- **Multi-language** — Arabic, French, English
- **Dark/Light Theme** — Toggle between themes
- **Admin Panel** — Manage announcements and visitor counter
- **AI Chat** — Market-aware assistant (OpenRouter free model): asks about the selected symbol, advises enter/wait/avoid
- **SEO Optimized** — Meta tags, robots.txt, sitemap.xml

## Live Demo

> [https://stockpredictor.example.com](https://stockpredictor.example.com)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/nexara93-oss/stock-predictor-ai.git
cd stock-predictor-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** On newer Python versions, you may need:
> ```bash
> pip install -r requirements.txt --break-system-packages
> ```

### 3. Install system dependency (Linux)

```bash
sudo apt update && sudo apt install -y libgomp1
```

### 4. Start the server

```bash
# Linux / Mac
bash start.sh

# Windows
start.bat
```

### 5. Open in browser

- **Main page:** http://localhost:3000

### 6. Enable the AI chat (optional, free)

1. Create a free key at [openrouter.ai](https://openrouter.ai/keys)
2. Set the environment variable (or create a `.env` file next to `main.py`):

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key
# optional, default is a free Llama model:
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

3. Restart the server — the floating **AI** button opens a chat that sees the
   selected symbol, live price and model forecasts, and answers questions like
   "should I enter now?" in Arabic, French or English.

- **Announcements** — Add/delete announcements with colors (green, red, blue, gold)
- **Visitor Counter** — Enable/disable and reset visitor count
- **Change Password** — Update admin password (min 8 characters)

## Project Structure

```
stock-predictor/
├── main.py              # FastAPI server + routes
├── models.py            # LightGBM prediction models
├── data_fetcher.py      # Yahoo Finance data fetching
├── market_symbols.py    # Stock/Crypto/Forex symbols
├── confidence.py        # Model confidence calculation
├── admin_auth.py        # Admin authentication & data
├── start.sh             # Linux launch script
├── start.bat            # Windows launch script
├── requirements.txt     # Python dependencies
├── data/                # JSON data storage
│   ├── admin_credentials.json
│   ├── announcements.json
│   └── counter.json
└── templates/
    ├── index.html       # Main dashboa
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard 
| GET | `/predict?symbol=AAPL` | Get AI predictions |
| GET | `/markets` | Get all market symbols |
| GET | `/price/{symbol}` | Get live price |
| GET | `/api/counter` | Get visitor count |
| POST | `/api/ai-chat` | AI chat (OpenRouter free model, market-aware) |
| WS | `/ws` | WebSocket for live prices |

## Tech Stack

- **Backend:** Python, FastAPI, uvicorn
- **ML:** LightGBM, scikit-learn, pandas, numpy
- **Data:** Yahoo Finance (yfinance)
- **Frontend:** Vanilla JS, Chart.js
- **Auth:** HTTP Basic Auth

## License

MIT
