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
        # Използваме новия актуален и супер бърз модел на Llama
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
            model="llama-3.1-8b-instant",  # Новият поддържан модел
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
