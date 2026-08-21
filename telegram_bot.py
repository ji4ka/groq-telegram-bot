import os
import threading
import telebot
from flask import Flask
from groq import Groq

app = Flask(__name__)

@app.route('/')
def home():
    return "Ботът работи стабилно с автоматичен избор на модел!"

# Вземаме токените от настройките на Render
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# Памет за съобщенията
conversations = {}

SYSTEM_PROMPT = (
    "Ти си интелигентен, любезен и полезен ИИ асистент. "
    "Отговаряш винаги на перфектен, граматически правилен, чист и напълно естествен български език. "
    "Отговаряш директно и точно на въпроса на потребителя, без излишни монолози, развалени фрази, диалекти или русизми."
)

def get_active_model():
    """Автоматично намира най-добрия и активен модел в акаунта."""
    try:
        models_list = client.models.list()
        active_ids = [m.id for m in models_list.data]
        
        # Списък с предпочитани модели по приоритет
        preferred_order = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768"
        ]
        
        for model_id in preferred_order:
            if model_id in active_ids:
                return model_id
        
        # Ако никой от горните не е намерен, вземаме първия изобщо наличен
        if active_ids:
            return active_ids[0]
    except Exception as e:
        print(f"Грешка при проверка на моделите: {e}")
    
    return "gemma2-9b-it"

@bot.message_handler(func=lambda message: True)
def reply_to_message(message):
    chat_id = message.chat.id
    
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    conversations[chat_id].append({"role": "user", "content": message.text})
    
    # Ограничаване на историята до последните 20 съобщения
    if len(conversations[chat_id]) > 21:
        conversations[chat_id] = [conversations[chat_id][0]] + conversations[chat_id][-20:]

    try:
        # Автоматично засичане на работещ модел
        selected_model = get_active_model()
        
        chat_completion = client.chat.completions.create(
            messages=conversations[chat_id],
            model=selected_model,
        )
        response = chat_completion.choices[0].message.content
        
        conversations[chat_id].append({"role": "assistant", "content": response})
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

def run_bot():
    print("Стартиране на Telegram инстанцията през Groq с авто-модел...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Полингът спря: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
