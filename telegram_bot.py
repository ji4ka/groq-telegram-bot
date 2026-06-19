import os
import threading
import telebot
from flask import Flask
from groq import Groq

app = Flask(__name__)

@app.route('/')
def home():
    return "Ботът работи стабилно и вече помни разговорите!"

# Вземаме токените от настройките на Render
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# Речник, в който ще пазим историята на съобщенията за всеки чат поотделно
conversations = {}

SYSTEM_PROMPT = (
    "Ти си интелигентен, любезен и полезен ИИ асистент. "
    "Отговаряш винаги на перфектен, граматически правилен, чист и напълно естествен български език. "
    "Отговаряш директно и точно на въпроса на потребителя, без излишни монолози, развалени фрази, диалекти или русизми."
)

@bot.message_handler(func=lambda message: True)
def reply_to_message(message):
    chat_id = message.chat.id
    
    # Ако този потребител пише за първи път, му създаваме нова история със системната инструкция
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Добавяме новото съобщение на потребителя в неговата история
    conversations[chat_id].append({"role": "user", "content": message.text})
    
    # Ограничаваме историята до последните 20 реплики, за да не препълваме паметта
    if len(conversations[chat_id]) > 21:  # 1 системно + 20 разменени съобщения
        conversations[chat_id] = [conversations[chat_id][0]] + conversations[chat_id][-20:]

    try:
        # Подаваме цялата история на разговорите към модела
        chat_completion = client.chat.completions.create(
            messages=conversations[chat_id],
            model="llama-3.3-70b-versatile",
        )
        response = chat_completion.choices[0].message.content
        
        # Записваме и отговора на бота в историята, за да го знае при следващото съобщение
        conversations[chat_id].append({"role": "assistant", "content": response})
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

def run_bot():
    print("Стартиране на Telegram инстанцията през Groq с памет...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Полингът спря: {e}")

if __name__ == "__main__":
    # Безопасно стартиране в отделна нишка
    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
