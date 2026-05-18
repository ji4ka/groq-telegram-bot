import os
import sys
import telebot
import requests
from flask import Flask
from groq import Groq

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route('/')
def home():
    return "Ботът е онлайн!", 200

def get_weather_data(city="Frankfurt"):
    try:
        lat, lon = 50.1109, 8.6821 
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto"
        response = requests.get(url).json()
        current = response['current']
        return f"Актуално време във Франкфурт: {current['temperature_2m']}°C (усеща се как {current['apparent_temperature']}°C)"
    except:
        return "Неуспешно извличане на времето."

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot_username = bot.get_me().username
        if message.chat.type in ['group', 'supergroup']:
            if not (f"@{bot_username}" in message.text or (message.reply_to_message and message.reply_to_message.from_user.username == bot_username)):
                return

        bot.send_chat_action(message.chat.id, 'typing')
        user_text = message.text.replace(f"@{bot_username}", "").strip()
        system_content = "Ти си полезен асистент. Отговаряй на български."
        
        if "време" in user_text.lower() or "времето" in user_text.lower():
            system_content += f"\n\nДанни: {get_weather_data()}"

        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_content}, {"role": "user", "content": user_text}],
            model="llama-3.3-70b-versatile",
        )
        bot.reply_to(message, chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Грешка при обработка: {e}")

# Функцията на Flask, която ще стартира и бота след първата заявка
@app.before_all_requests
def start_bot_polling():
    if not hasattr(app, 'bot_started'):
        import threading
        threading.Thread(target=bot.infinity_polling, daemon=True).start()
        app.bot_started = True

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
