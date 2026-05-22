import os
import sys
import telebot
import requests
import threading
from flask import Flask
import google.generativeai as genai  # Новата библиотека на Google

# Инициализиране на Flask (уеб сървър за Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "Ботът е онлайн и работи с Google Gemini мозък! 🍏🧠", 200

# Вземане на токените от Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("ГРЕШКА: Липсват API ключове в Render!", file=sys.stderr)
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Конфигуриране на Google Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Функция за времето във Франкфурт
def get_weather_data(city="Frankfurt"):
    try:
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
    bot.reply_to(message, "Здравей! Аз съм супер бърз AI бот, задвижван от Google Gemini! Вече говоря перфектен български. ⚡🤖")

# 1. ОБРАБОТЧИК: Бърза реакция при "Добро утро"
@bot.message_handler(func=lambda message: message.text and "добро утро" in message.text.lower())
def reply_good_morning(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        morning_reply = "Добро утро! ☕ Желая ти прекрасен, успешен и много усмихнат ден! С какво мога да помогна днес? ☀️"
        bot.reply_to(message, morning_reply)
    except Exception as e:
        print(f"Грешка при поздрава: {e}")

# 2. ОСНОВЕН ОБРАБОТЧИК: Големият изкуствен интелект на Google
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot_username = bot.get_me().username
        is_group = message.chat.type in ['group', 'supergroup']
        
        # Защита за групи (активира се само при таг или Reply)
        if is_group:
            has_mention = message.text and f"@{bot_username}" in message.text
            is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.username == bot_username
            if not (has_mention or is_reply_to_bot):
                return

        bot.send_chat_action(message.chat.id, 'typing')
        user_text = message.text.replace(f"@{bot_username}", "").strip() if message.text else ""

        # Инструкции за характера и езика
        system_content = (
            "Ти си интелигентен, свободен и изключително полезен AI асистент.\n"
            "ГОВОРИ ВИНАГИ НА ПЕРФЕКТЕН БЪЛГАРСКИ ЕЗИК. Използвай естествен изказ, "
            "правилна граматика и избягвай буквални преводи от английски."
        )
        
        # Проверка за времето
        if "време" in user_text.lower() or "времето" in user_text.lower():
            real_weather = get_weather_data()
            system_content += f"\n\nВАЖНО: Използвай следните реални данни, за да отговориш на въпроса за времето:\n{real_weather}"

        # Стартиране на модела на Google с вградените системни инструкции
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_content
        )
        
        # Генериране на отговор
        response_api = model.generate_content(user_text)
        response = response_api.text
        
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

# Пускане на бот процеса при първата уеб заявка от Render
@app.before_request
def start_bot_polling():
    if not hasattr(app, 'bot_started'):
        print("Стартиране на Telegram инстанцията...")
        threading.Thread(target=bot.infinity_polling, daemon=True).start()
        app.bot_started = True

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
