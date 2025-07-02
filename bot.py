import requests
import feedparser
import sqlite3
from keep_alive import keep_alive

# Telegram Configuração
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

# Feeds RSS
RSS_FEEDS = [
    "https://br.investing.com/rss/news_285.rss",
    "https://www.reuters.com/rssFeed/topNews",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

# Palavras-chave
KEYWORDS = [
    "Copom", "Selic", "Payroll", "Fed", "inflação", "PIB",
    "IPCA", "ETF", "Bitcoin", "volatilidade", "circuit breaker"
]

# Banco de dados
conn = sqlite3.connect('news.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS sent_news (link TEXT)')
conn.commit()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    r = requests.post(url, data=payload)
    print(f"Mensagem enviada. Status: {r.status_code}")

def check_and_send():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            published = entry.published if "published" in entry else "Sem data"

            if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                c.execute('SELECT 1 FROM sent_news WHERE link = ?', (link,))
                if c.fetchone():
                    continue

                message = (
                    f"🚨 <b>Notícia Relevante</b>\n\n"
                    f"<b>Título:</b> {title}\n"
                    f"<b>Fonte:</b> {feed.feed.title}\n"
                    f"<b>Data:</b> {published}\n\n"
                    f"<a href='{link}'>🔗 Leia mais</a>"
                )

                send_telegram(message)
                c.execute('INSERT INTO sent_news (link) VALUES (?)', (link,))
                conn.commit()

if __name__ == "__main__":
    keep_alive()
    check_and_send()
