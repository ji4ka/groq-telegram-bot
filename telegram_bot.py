import os
import sys
import telebot
import requests
import threading
from flask import Flask
from groq import Groq

# Инициализиране на Flask (мини уеб сървър, за да не ни изхвърля Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "Ботът е задействан и работи!", 200

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY:
    print("ГРЕШКА: Липсват API ключове в Render!", file=sys.stderr)
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

def get_weather_data(city="Frankfurt"):
    try:
        # Координати за Франкфурт
        lat, lon = 50.1109, 8.6821 
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto"
        response = requests.get(url).json()
        current = response['current']
        
        weather_report = (
            f"Актуални данни за времето във Франкфурт в момента:\n"
            f"- Температура: {current['temperature_2m']}°C (усеща се като {current['apparent_temperature']}°C)\n"
            f"- Влажност: {current['relative_humidity_2m']}%\n"
            f"- Скорост на вятъра: {current['wind_speed_10m']} км/ч\n"
        )
        return weather_report
    except Exception as e:
        return f"Неуспешно извличане на времето: {e}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Здравей! Аз съм супер бърз AI бот, задвижван от Groq. Вече знам и времето! ⚡🌤️")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot_username = bot.get_me().username
        is_group = message.chat.type in ['group', 'supergroup']
        
        if is_group:
            has_mention = message.text and f"@{bot_username}" in message.text
            is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.username == bot_username
            if not (has_mention or is_reply_to_bot):
                return

        bot.send_chat_action(message.chat.id, 'typing')
        user_text = message.text.replace(f"@{bot_username}", "").strip() if message.text else ""

        system_content = "Ти си полезен и умен асистент. Отговаряй на български език."
        
        if "време" in user_text.lower() or "времето" in user_text.lower():
            real_weather = get_weather_data()
            system_content += f"\n\nВАЖНО: Използвай следните реални данни, за да отговориш на въпроса за времето:\n{real_weather}"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_text}
            ],
            model="llama-3.3-70b-versatile",
        )
        
        response = chat_completion.choices[0].message.content
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

# Функция за пускане на бота в отделна нишка (thread)
def run_bot():
    print("Ботът е стартиран успешно и чака съобщения... 🚀")
    bot.infinity_polling()

if __name__ == "__main__":
    # Стартираме бота в бекграунда, за да може Flask да си работи на преден план
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Стартираме уеб сървъра на порта, който Render ще ни даде автоматично
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
