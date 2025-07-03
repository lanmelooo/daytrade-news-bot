import requests
import feedparser
import sqlite3
from keep_alive import keep_alive
from datetime import datetime
import pytz
import time
from urllib.parse import urlparse, urlunparse
import os

# Timezone
tz = pytz.timezone('America/Sao_Paulo')

# Telegram Configuração
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

# Feeds RSS
RSS_FEEDS = [
    "https://br.investing.com/rss/news_285.rss",
    "https://www.reuters.com/rssFeed/topNews",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

# Palavras-chave
KEYWORDS = [
    "Copom", "Selic", "Payroll", "Fed", "inflação", "PIB",
    "IPCA", "ETF", "Bitcoin", "volatilidade", "circuit breaker",
    "commodities", "petróleo", "dólar", "S&P", "índice", "bovespa"
]

# Banco de dados
conn = sqlite3.connect('news.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS sent_news (link TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS sent_titles (title TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS daily_summary (title TEXT, link TEXT)')
conn.commit()

def normalize_link(link):
    parts = urlparse(link)
    return urlunparse((parts.scheme, parts.netloc, parts.path, '', '', ''))

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload)
    print(f"✅ Mensagem enviada. Status: {r.status_code}")

def check_and_send():
    print("🔍 Iniciando verificação de notícias...")
    for feed_url in RSS_FEEDS:
        print(f"🔗 Buscando feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.strip()
            link = normalize_link(entry.link)
            published = entry.published if "published" in entry else "Sem data"

            # Verificar duplicados por link
            c.execute('SELECT 1 FROM sent_news WHERE link = ?', (link,))
            if c.fetchone():
                print(f"⚠️ Notícia já enviada (link): {title}")
                continue

            # Verificar duplicados por título
            c.execute('SELECT 1 FROM sent_titles WHERE title = ?', (title,))
            if c.fetchone():
                print(f"⚠️ Notícia já enviada (título): {title}")
                continue

            message = (
                f"🚨 <b>NOTÍCIA IMPORTANTE</b>\n\n"
                f"<b>Título:</b> {title}\n"
                f"<b>Fonte:</b> {feed.feed.title}\n"
                f"<b>Data:</b> {published}\n\n"
                f"<a href='{link}'>🔗 Leia mais</a>"
            )

            print(f"✉️ Enviando notícia: {title}")
            send_telegram(message)

            # Registrar no banco
            c.execute('INSERT INTO sent_news (link) VALUES (?)', (link,))
            c.execute('INSERT INTO sent_titles (title) VALUES (?)', (title,))
            c.execute('INSERT INTO daily_summary (title, link) VALUES (?, ?)', (title, link))
            conn.commit()
    print("✅ Verificação de notícias concluída.")

def send_daily_summary():
    print("📊 Gerando resumo diário...")
    c.execute('SELECT title, link FROM daily_summary')
    rows = c.fetchall()

    if rows:
        text = "📊 <b>Resumo das notícias do dia:</b>\n\n"
        for title, link in rows:
            text += f"🔹 <a href='{link}'>{title}</a>\n"
        send_telegram(text)
        c.execute('DELETE FROM daily_summary')
        conn.commit()
        print("✅ Resumo enviado e banco limpo.")
    else:
        send_telegram("📊 Hoje não houve notícias relevantes para o resumo.")
        print("⚠️ Nenhuma notícia para o resumo.")

def main_loop():
    print("🚀 Bot iniciado com sucesso.")
    while True:
        try:
            now = datetime.now(tz)
            hour = now.hour
            minute = now.minute
            print(f"⏰ {now.strftime('%Y-%m-%d %H:%M')} - Loop ativo.")

            # Mensagem de Bom Dia
            if hour == 5 and minute == 50:
                print("🌅 Enviando mensagem de Bom Dia.")
                send_telegram(
                    "☀️ <b>Bom dia!</b>\n\n"
                    "Vamos começar pelo calendário dos eventos econômicos do dia:\n"
                    "🔗 https://br.investing.com/economic-calendar/"
                )

            # Aviso Mercado vai abrir
            if hour == 8 and minute == 50:
                print("⏰ Enviando aviso de abertura de mercado.")
                send_telegram(
                    "⏰ <b>O mercado vai abrir em 10 minutos!</b>\n\n"
                    "Vale a pena revisar os eventos econômicos:\n"
                    "🔗 https://br.investing.com/economic-calendar/"
                )

            # Resumo diário
            if hour == 19 and minute == 0:
                print("📈 Enviando resumo diário.")
                send_daily_summary()

            # Das 6h às 19h, verificar notícias
            if 6 <= hour < 19:
                check_and_send()

        except Exception as e:
            print(f"❌ Erro no loop principal: {e}")

        time.sleep(60)

if __name__ == "__main__":
    keep_alive()
    main_loop()
