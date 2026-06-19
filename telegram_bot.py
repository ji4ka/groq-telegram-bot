import os
import telebot
from groq import Groq
import threading
from Flask import Flask

App = Flask(__name__)

@app.route('/')
def home():
    Return "Ботът работи стабилно през Groq!"

# Вземаме токените от настройките на Render
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(func=lambda message: True)
def reply_to_message(message):
    Try:
        # Използваме супер бързия Llama 3 модел през Groq
        Chat_completion = client.chat.completions.create(
            Messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
            Model="llama3-8b-8192", # Бърз, стабилен и напълно безплатен
        )
        response = chat_completion.choices[0].message.content
        bot.reply_to(message, response)
    Except Exception as e:
        Bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

Def run_bot():
    Print("Стартиране на Telegram инстанцията през Groq...")
    Try:
        Bot.infinity_polling(timeout=10, long_polling_timeout=5)
    Except Exception as e:
        Print(f"Полингът спря: {e}")

If __name__ == "__main__":
    # Местим стартирането ТУК, за да нямаме Грешка 409 (Conflict)
    Threading.Thread(target=run_bot, daemon=True).start()
    
    Port = int(os.environ.get("PORT", 10000))
    App.run(host="0.0.0.0", port=port)
