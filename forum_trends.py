#!/usr/bin/env python3
"""Scraper de tendencias en foros de inversion (Reddit) para detectar
que empresas/tickers se mencionan mas, como punto de partida para
investigar posibles inversiones.

Usa el endpoint JSON publico de Reddit (no requiere API key) y cuenta
menciones de tickers tipo $AAPL o palabras en mayusculas de 2-5 letras,
filtrando palabras comunes en ingles/espanol que generan falsos positivos.

Uso:
    python forum_trends.py
    python forum_trends.py --subreddits wallstreetbets stocks investing
    python forum_trends.py --time week --limit 100 --top 15
"""

from __future__ import annotations

import argparse
import re
import time
import urllib.request
import urllib.error
from collections import Counter
from dataclasses import dataclass, field

DEFAULT_SUBREDDITS = [
    "wallstreetbets",
    "stocks",
    "investing",
    "StockMarket",
    "SecurityAnalysis",
]

# Palabras en mayusculas que coinciden con el patron de un ticker pero no lo son.
TICKER_BLOCKLIST = {
    "A", "I", "THE", "FOR", "AND", "YOU", "ARE", "ALL", "NOT", "BUT",
    "CEO", "CFO", "IPO", "ETF", "USA", "USD", "EUR", "GDP", "FED",
    "EPS", "YOY", "IMO", "DD", "ATH", "ATL", "EOD", "EOW", "YTD",
    "FOMO", "FUD", "LOL", "WSB", "SEC", "FDA", "FOMC", "OTM", "ITM",
    "NYSE", "LLC", "INC", "NEW", "OLD", "NOW", "ONE", "TWO", "WHY",
    "HOW", "WHO", "YES", "NO", "OK", "PE", "ROI", "ROE", "P",
}

USER_AGENT = "forum-trends-research-bot/1.0 (educational investment research tool)"
TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b")


@dataclass
class Mention:
    count: int = 0
    sample_titles: list = field(default_factory=list)
    score: int = 0


def fetch_subreddit_posts(subreddit: str, time_filter: str, limit: int) -> list[dict]:
    """Descarga posts 'top' de un subreddit via el JSON publico de Reddit."""
    url = (
        f"https://www.reddit.com/r/{subreddit}/top.json"
        f"?t={time_filter}&limit={min(limit, 100)}"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"  [!] No se pudo leer r/{subreddit}: {exc}")
        return []

    import json

    payload = json.loads(data)
    children = payload.get("data", {}).get("children", [])
    posts = []
    for child in children:
        post = child.get("data", {})
        posts.append(
            {
                "title": post.get("title", ""),
                "selftext": post.get("selftext", "")[:500],
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "url": "https://reddit.com" + post.get("permalink", ""),
                "subreddit": subreddit,
            }
        )
    return posts


def extract_tickers(text: str) -> set[str]:
    found = set()
    for cashtag, bare in TICKER_PATTERN.findall(text):
        ticker = cashtag or bare
        if cashtag:
            found.add(ticker)
        elif bare not in TICKER_BLOCKLIST:
            found.add(bare)
    return found


def analyze(subreddits: list[str], time_filter: str, limit: int) -> Counter[str]:
    mentions: dict[str, Mention] = {}

    for subreddit in subreddits:
        print(f"-> Descargando r/{subreddit} (top/{time_filter}, limit={limit})...")
        posts = fetch_subreddit_posts(subreddit, time_filter, limit)
        for post in posts:
            text = f"{post['title']} {post['selftext']}"
            tickers = extract_tickers(text)
            for ticker in tickers:
                entry = mentions.setdefault(ticker, Mention())
                entry.count += 1
                entry.score += post["score"]
                if len(entry.sample_titles) < 3:
                    entry.sample_titles.append(f"[{post['subreddit']}] {post['title']}")
        time.sleep(1)  # cortesia hacia la API publica de Reddit

    return mentions


def print_report(mentions: dict[str, Mention], top_n: int) -> None:
    ranked = sorted(mentions.items(), key=lambda kv: (kv[1].count, kv[1].score), reverse=True)

    print("\n=== Tickers/empresas mas mencionados ===")
    print(f"{'Ticker':<8} {'Menciones':<10} {'Score total':<12}")
    print("-" * 32)
    for ticker, data in ranked[:top_n]:
        print(f"{ticker:<8} {data.count:<10} {data.score:<12}")

    print("\n=== Detalle de ejemplos ===")
    for ticker, data in ranked[:top_n]:
        print(f"\n${ticker} ({data.count} menciones, score acumulado {data.score})")
        for title in data.sample_titles:
            print(f"  - {title}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analiza tendencias de tickers en subreddits de inversion."
    )
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=DEFAULT_SUBREDDITS,
        help="Lista de subreddits a analizar (sin 'r/').",
    )
    parser.add_argument(
        "--time",
        default="day",
        choices=["hour", "day", "week", "month", "year", "all"],
        help="Rango temporal para los posts 'top' (default: day).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Numero de posts a revisar por subreddit (max 100, default: 50).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Cuantos tickers mostrar en el reporte (default: 10).",
    )
    args = parser.parse_args()

    mentions = analyze(args.subreddits, args.time, args.limit)
    if not mentions:
        print("No se encontraron menciones de tickers. Revisa conectividad o subreddits.")
        return
    print_report(mentions, args.top)

    print(
        "\nNota: esto es una senal de interes/popularidad en foros, NO una "
        "recomendacion de inversion. Verifica fundamentales antes de decidir."
    )


if __name__ == "__main__":
    main()
