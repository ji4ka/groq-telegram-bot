import os
import threading
import telebot
from flask import Flask
from groq import Groq

app = Flask(__name__)

@app.route('/')
def home():
    return "Ботът работи стабилно през Groq!"

# Вземаме токените от настройките на Render
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(func=lambda message: True)
def reply_to_message(message):
    try:
        # Използваме големия 70B модел + System съобщение за перфектен български
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ти си интелигентен, любезен и полезен ИИ асистент. Отговаряш винаги на перфектен, граматически правилен, чист и напълно естествен български език. Отговаряш директно и точно на въпроса на потребителя, без излишни монолози, развалени фрази, диалекти или русизми."
                },
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
            model="llama-3.3-70b-versatile",  # Много по-интелигентен модел
        )
        response = chat_completion.choices[0].message.content
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

def run_bot():
    print("Стартиране на Telegram инстанцията през Groq...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Полингът спря: {e}")

if __name__ == "__main__":
    # Безопасно стартиране в отделна нишка
    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
