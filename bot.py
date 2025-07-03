import requests
import feedparser
import sqlite3
import os
import time
import datetime
from keep_alive import keep_alive

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
CATEGORY_A = [
    "tendência", "perspectiva", "projeção", "expectativa", "cenário",
    "abertura positiva", "abertura negativa", "futuros do índice",
    "futuros do dólar", "sentimento do mercado", "visão de analistas"
]

CATEGORY_B = [
    "Selic", "IPCA", "PIB", "inflação", "Fed", "Payroll", "Copom",
    "commodities", "petróleo", "ouro", "ETF", "circuit breaker",
    "volatilidade", "Bitcoin", "Ethereum", "dólar", "taxa de juros",
    "risco fiscal", "risco político", "geopolítica", "crise energética",
    "OPEP", "balança comercial", "swap cambial", "intervenção cambial",
    "decisão do FOMC", "decisão do BCE", "dívida americana", "shutdown",
    "China", "recessão", "rally", "crash", "OMC", "conflito"
]

CATEGORY_C = [
    "guerra", "ataque", "colapso", "falência", "congelamento", "default",
    "crise", "pânico", "emergência", "lockdown", "ameaça nuclear", "ataque cibernético"
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

            # Verificar duplicados
            c.execute('SELECT 1 FROM sent_news WHERE link = ?', (link,))
            if c.fetchone():
                continue

            # Categoria Extraordinária
            if any(keyword.lower() in title.lower() for keyword in CATEGORY_C):
                prefix = "⚠️ <b>ALERTA EXTRAORDINÁRIO</b>"
            # Categoria Tendência
            elif any(keyword.lower() in title.lower() for keyword in CATEGORY_A):
                prefix = "🚀 <b>ALERTA DE TENDÊNCIA</b>"
            # Categoria Geral
            elif any(keyword.lower() in title.lower() for keyword in CATEGORY_B):
                prefix = "🚨 <b>NOTÍCIA IMPORTANTE</b>"
            else:
                continue

            message = (
                f"{prefix}\n\n"
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
    while True:
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        # Mensagem das 05:50
        if hour == 5 and minute == 50:
            msg = (
                "📅 <b>Bom dia!</b>\n\n"
                "Vamos começar pelo calendário dos eventos econômicos do dia:\n"
                "🔗 <a href='https://br.investing.com/economic-calendar/'>Investing.com - Calendário Econômico</a>"
            )
            send_telegram(msg)

        # Mensagem das 08:50
        if hour == 8 and minute == 50:
            msg = (
                "⏰ <b>O mercado vai abrir em 10 minutos.</b>\n\n"
                "Vale a pena uma olhada nos eventos econômicos do dia:\n"
                "🔗 <a href='https://br.investing.com/economic-calendar/'>Investing.com - Calendário Econômico</a>"
            )
            send_telegram(msg)

        # Janela principal de operação
        if 6 <= hour < 19:
            print(f"⏰ {now.strftime('%H:%M')} – Executando checagem...")
            check_and_send()
        else:
            print(f"🌙 {now.strftime('%H:%M')} – Fora do horário monitorado.")

        time.sleep(60)  # Checa a cada 1 min para pegar certinho os horários
