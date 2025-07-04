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
    "https://br.investing.com/rss/news_285.rss",                  # Notícias economia Brasil
    "https://br.investing.com/rss/news_25.rss",                   # Calendário econômico
    "https://www.reuters.com/rssFeed/topNews",                    # Notícias globais
    "https://www.bloomberg.com/markets/rss",                      # Mercados globais
    "https://valorinveste.globo.com/rss/",                        # Brasil - Valor Investe
    "https://www.coindesk.com/arc/outboundfeeds/rss/",            # Bitcoin e cripto
    "https://www.spglobal.com/commodityinsights/en/market-insights/rss-feed",  # Commodities
    "https://www.bcb.gov.br/feeds/noticias.xml",                  # Banco Central Brasil
    "https://tradingeconomics.com/rss"                            # Indicadores globais
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
    any_news = False
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.strip()
            link = normalize_link(entry.link)
            published = entry.published if "published" in entry else "Sem data"

            c.execute('SELECT 1 FROM sent_news WHERE link = ?', (link,))
            if c.fetchone():
                continue

            c.execute('SELECT 1 FROM sent_titles WHERE title = ?', (title,))
            if c.fetchone():
                continue

            message = (
                f"🚨 <b>NOTÍCIA IMPORTANTE</b>\n\n"
                f"<b>Título:</b> {title}\n"
                f"<b>Fonte:</b> {feed.feed.title}\n"
                f"<b>Data:</b> {published}\n\n"
                f"<a href='{link}'>🔗 Leia mais</a>"
            )

            send_telegram(message)
            c.execute('INSERT INTO sent_news (link) VALUES (?)', (link,))
            c.execute('INSERT INTO sent_titles (title) VALUES (?)', (title,))
            c.execute('INSERT INTO daily_summary (title, link) VALUES (?, ?)', (title, link))
            conn.commit()
            any_news = True

    if not any_news:
        print("✅ Nenhuma notícia nova encontrada.")

def send_daily_summary():
    c.execute('SELECT title, link FROM daily_summary')
    rows = c.fetchall()

    if rows:
        text = "📊 <b>Resumo das notícias do dia:</b>\n\n"
        for title, link in rows:
            text += f"🔹 <a href='{link}'>{title}</a>\n"
        send_telegram(text)
        c.execute('DELETE FROM daily_summary')
        conn.commit()
    else:
        send_telegram("📊 Hoje não houve notícias relevantes para o resumo.")
        print("⚠️ Nenhuma notícia para o resumo.")

def check_bitcoin_volatility():
    print("🔍 Checando volatilidade do Bitcoin...")
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true")
        data = response.json()
        change = data["bitcoin"]["usd_24h_change"]
        if abs(change) >= 5:
            emoji = "📈" if change > 0 else "📉"
            send_telegram(
                f"{emoji} <b>ALERTA DE VOLATILIDADE - Bitcoin</b>\n\n"
                f"Variação nas últimas 24h: {change:.2f}%\n"
                "Fique atento aos impactos no mercado cripto e no sentimento de risco."
            )
        else:
            print(f"✅ Variação BTC: {change:.2f}%, dentro do normal.")
    except Exception as e:
        print(f"⚠️ Erro ao checar Bitcoin: {e}")

def main_loop():
    print("🚀 Bot iniciado com sucesso.")
    while True:
        try:
            now = datetime.now(tz)
            hour = now.hour
            minute = now.minute
            print(f"🔄 Loop ativo - {now.strftime('%Y-%m-%d %H:%M')}")

            # Aberturas e Fechamentos

            if hour == 4 and minute == 50:
                send_telegram(
                    "🇪🇺 <b>Abertura dos mercados europeus em 10 minutos.</b>\n\n"
                    "Atente-se a possíveis movimentos iniciais que podem impactar futuros e dólar."
                )

            if hour == 8 and minute == 50:
                send_telegram(
                    "🇧🇷 <b>O mercado brasileiro de futuros abrirá em 10 minutos.</b>\n\n"
                    "Reveja seus parâmetros e prepare seu setup de day trade."
                )

            if hour == 9 and minute == 50:
                send_telegram(
                    "🏛️ <b>Abertura do pregão de ações em 10 minutos.</b>\n\n"
                    "Liquidez aumentará no mercado à vista."
                )

            if hour == 10 and minute == 20:
                send_telegram(
                    "🇺🇸 <b>Abertura do mercado americano em 10 minutos.</b>\n\n"
                    "Prepare-se para volatilidade no índice e dólar."
                )

            if hour == 16 and minute == 50:
                send_telegram(
                    "🇪🇺 <b>Fechamento dos mercados europeus em 10 minutos.</b>\n\n"
                    "A liquidez pode reduzir. Atenção ao fluxo americano."
                )

            if hour == 18 and minute == 15:
                send_telegram(
                    "⏳ <b>Fechamento do mercado de futuros em 10 minutos.</b>\n\n"
                    "Avalie zerar suas posições e revisar resultados."
                )

            # Resumo diário
            if hour == 19 and minute == 0:
                send_daily_summary()

            # Das 6h às 19h, verificar notícias e Bitcoin
            if 6 <= hour < 19:
                check_and_send()
                check_bitcoin_volatility()

        except Exception as e:
            print(f"❌ Erro no loop principal: {e}")

        time.sleep(60)

if __name__ == "__main__":
    keep_alive()
    main_loop()
