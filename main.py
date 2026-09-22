import os
import asyncio
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response, RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import yfinance as yf
from data_fetcher import get_live_price, get_all_live_prices
from market_symbols import MARKET_SYMBOLS, get_all_symbols
from models import DailyModel, WeeklyModel, MonthlyModel, YearlyModel
from admin_auth import (
    init_credentials, check_credentials, change_password,
    load_announcements, save_announcements, add_announcement, delete_announcement,
    load_counter, save_counter, increment_counter
)

app = FastAPI(title="Stock Predictor")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env (KEY=VALUE) without extra dependencies
try:
    _env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(_env_path):
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                _k, _v = _k.strip(), _v.strip().strip('"').strip("'")
                if _k and _k not in os.environ:
                    os.environ[_k] = _v
except Exception:
    pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
security = HTTPBasic()

daily_model = DailyModel()
weekly_model = WeeklyModel()
monthly_model = MonthlyModel()
yearly_model = YearlyModel()

connected_clients = set()
live_prices_cache = {}

async def poll_prices():
    await asyncio.sleep(10)
    symbols = get_all_symbols()
    while True:
        try:
            prices = {}
            for sym in symbols[:30]:
                try:
                    price = get_live_price(sym)
                    if price:
                        prices[sym] = price
                except:
                    pass
            live_prices_cache.clear()
            live_prices_cache.update(prices)
            msg = json.dumps({"type": "prices", "data": prices, "time": datetime.now().isoformat()})
            dead = set()
            for ws in connected_clients:
                try:
                    await ws.send_text(msg)
                except:
                    dead.add(ws)
            connected_clients -= dead
        except:
            pass
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup():
    init_credentials()
    asyncio.create_task(poll_prices())


def verify_admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        response = Response(content="Unauthorized", status_code=401)
        response.headers["WWW-Authenticate"] = 'Basic realm="Admin"'
        return response
    path = os.path.join(BASE_DIR, "templates", "admin.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/admin/announcements")
async def api_get_announcements(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return load_announcements()


@app.post("/api/admin/announcements")
async def api_add_announcement(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    text = body.get("text", "")
    color = body.get("color", "green")
    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)
    item = add_announcement(text, color)
    return item


@app.delete("/api/admin/announcements/{ann_id}")
async def api_delete_announcement(ann_id: int, request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    delete_announcement(ann_id)
    return {"ok": True}


@app.post("/api/admin/change-password")
async def api_change_password(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    new_pw = body.get("password", "")
    if len(new_pw) < 8:
        return JSONResponse({"error": "password must be 8+ chars"}, status_code=400)
    change_password(new_pw)
    return {"ok": True}


@app.get("/api/admin/counter")
async def api_get_counter(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return load_counter()


@app.post("/api/admin/counter")
async def api_set_counter(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    if not check_credentials(credentials.username, credentials.password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    save_counter(body)
    return {"ok": True}


@app.get("/api/counter")
async def api_public_counter():
    return load_counter()


@app.get("/", response_class=HTMLResponse)
async def home(response: Response):
    increment_counter()
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        anns = load_announcements()
        counter = load_counter()
        active_anns = [a for a in anns if a.get("active", True)]
        inject = "<body>\n<script>"
        inject += f"window.__ANNOUNCEMENTS__ = {json.dumps(active_anns, ensure_ascii=False)};"
        inject += f"window.__COUNTER__ = {json.dumps(counter)};"
        inject += "</script>"
        content = content.replace("<body>", inject)
        return HTMLResponse(content=content)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    path = os.path.join(BASE_DIR, "templates", "dashboard.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/markets")
async def get_markets():
    result = {}
    for key, market in MARKET_SYMBOLS.items():
        result[key] = {"name": market["name"], "timezone": market.get("timezone", "UTC"), "symbols": market["symbols"]}
    return result

@app.get("/predict")
async def predict(symbol: str = Query("AAPL")):
    try:
        results = {}
        d = daily_model.predict(symbol)
        w = weekly_model.predict(symbol)
        m = monthly_model.predict(symbol)
        y = yearly_model.predict(symbol)
        if d:
            results["daily"] = d
        if w:
            results["weekly"] = w
        if m:
            results["monthly"] = m
        if y:
            results["yearly"] = y
        current_price = get_live_price(symbol)
        if current_price:
            results["current_price"] = round(current_price, 2)
        elif d:
            results["current_price"] = d["last_price"]
        return results
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "get_price":
                    symbol = msg.get("symbol", "AAPL")
                    price = get_live_price(symbol)
                    await websocket.send_text(json.dumps({
                        "type": "price_update",
                        "symbol": symbol,
                        "price": price,
                        "time": datetime.now().isoformat()
                    }))
                elif msg.get("type") == "subscribe":
                    symbol = msg.get("symbol")
                    while True:
                        price = get_live_price(symbol)
                        if price:
                            await websocket.send_text(json.dumps({
                                "type": "price_update",
                                "symbol": symbol,
                                "price": price
                            }))
                        await asyncio.sleep(10)
            except:
                pass
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except:
        connected_clients.discard(websocket)

@app.get("/price/{symbol}")
async def get_price(symbol: str):
    price = get_live_price(symbol)
    if price:
        return {"symbol": symbol.upper(), "price": round(price, 2)}
    return {"error": "Could not fetch price"}


@app.get("/robots.txt", response_class=Response)
async def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: https://stockpredictor.example.com/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://stockpredictor.example.com/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://stockpredictor.example.com/?lang=ar</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://stockpredictor.example.com/?lang=fr</loc>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://stockpredictor.example.com/?lang=en</loc>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    return Response(content=xml, media_type="application/xml")


def call_openrouter(messages, max_tokens=800):
    """Call a free OpenRouter model. Returns (text, error)."""
    if not OPENROUTER_API_KEY:
        return None, "missing_key"
    body = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + OPENROUTER_API_KEY,
            "HTTP-Referer": "https://stockpredictor.example.com/",
            "X-Title": "Stock Predictor",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        if choices:
            return ((choices[0].get("message") or {}).get("content") or "").strip(), None
        err = data.get("error")
        return None, (err.get("message") if isinstance(err, dict) else str(err)) or "empty response"
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8")).get("error")
            msg = (err.get("message") if isinstance(err, dict) else str(err)) if err else str(e)
        except Exception:
            msg = str(e)
        return None, msg
    except Exception as e:
        return None, str(e)


@app.post("/api/ai-chat")
async def api_ai_chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    user_msg = str(body.get("message") or "").strip()[:2000]
    symbol = str(body.get("symbol") or "AAPL").upper()[:20]
    lang = str(body.get("lang") or "ar")[:5]
    history = body.get("history") or []
    if not user_msg:
        return JSONResponse({"error": "message required"}, status_code=400)

    # Market context so the AI answers about the real selected symbol.
    # Frontend sends the already-computed forecast (fast path); otherwise compute it here.
    ctx = ["Symbol: " + symbol]
    market = str(body.get("market") or "")[:1500]
    if market:
        ctx.append("Model forecast: " + market)
    else:
        try:
            px = get_live_price(symbol)
            if px:
                ctx.append("Live price: $%.2f" % px)
        except Exception:
            pass
        try:
            for name, model in (("daily", daily_model), ("weekly", weekly_model)):
                try:
                    p = model.predict(symbol)
                except Exception:
                    p = None
                if p and p.get("predictions"):
                    preds = p["predictions"]
                    last = p.get("last_price") or preds[0]
                    chg = (preds[-1] - last) / last * 100 if last else 0
                    ctx.append("%s: last $%.2f -> target $%.2f (%+.2f%%, confidence %s%%)"
                               % (name, last, preds[-1], chg, p.get("confidence", 0)))
        except Exception:
            pass

    lang_name = {"ar": "Arabic (clear, friendly; Darija touches allowed)",
                 "fr": "French", "en": "English"}.get(lang, "Arabic")
    system = (
        "You are the Stock Predictor AI trading assistant. Answer in %s. "
        "Market context:\n%s\n"
        "Rules: be concise and practical; when asked whether to trade now, weigh the forecast, "
        "confidence and risk, give a clear stance (enter / wait / avoid) plus 2-4 bullet reasons, "
        "a suggested stop-loss mindset and position-size caution. "
        "Always add one short line: educational analysis, not financial advice." % (lang_name, "\n".join(ctx))
    )
    msgs = [{"role": "system", "content": system}]
    try:
        for h in history[-8:]:
            r, c = h.get("role"), str(h.get("content") or "")[:1500]
            if r in ("user", "assistant") and c:
                msgs.append({"role": r, "content": c})
    except Exception:
        pass
    msgs.append({"role": "user", "content": user_msg})

    text, err = call_openrouter(msgs)
    if err == "missing_key":
        return JSONResponse({"error": "AI not configured. Set OPENROUTER_API_KEY on the server."}, status_code=503)
    if err:
        return JSONResponse({"error": "AI error: " + str(err)}, status_code=502)
    return {"reply": text or "..."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
