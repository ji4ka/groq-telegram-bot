import os
import threading
import telebot
from flask import Flask
from groq import Groq

app = Flask(__name__)

@app.route('/')
def home():
    return "Ботът работи стабилно с интелигентен филтър на моделите!"

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

conversations = {}

SYSTEM_PROMPT = (
    "Ти си интелигентен, любезен и полезен ИИ асистент. "
    "Отговаряш винаги на перфектен, граматически правилен, чист и напълно естествен български език. "
    "Отговаряш директно и точно на въпроса на потребителя, без излишни монолози, развалени фрази, диалекти или русизми."
)

def get_active_chat_model():
    """Филтрира само валидни текстови чат модели, като игнорира Whisper, Canopylabs и др."""
    try:
        models_list = client.models.list()
        
        # Ключови думи за модели, които НЕ са за текстов чат
        ignored_keywords = ['whisper', 'canopylabs', 'guard', 'vision', 'tts', 'embed', 'audio']
        
        chat_models = [
            m.id for m in models_list.data 
            if not any(keyword in m.id.lower() for keyword in ignored_keywords)
        ]
        
        # Приоритетен списък с текстови модели
        preferred_order = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768"
        ]
        
        for model_id in preferred_order:
            if model_id in chat_models:
                return model_id
        
        if chat_models:
            return chat_models[0]
    except Exception as e:
        print(f"Грешка при проверка на моделите: {e}")
    
    return "llama-3.1-8b-instant"

@bot.message_handler(func=lambda message: True)
def reply_to_message(message):
    chat_id = message.chat.id
    
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    conversations[chat_id].append({"role": "user", "content": message.text})
    
    # Ограничаваме паметта до системната инструкция + последните 10 съобщения,
    # за да не надвишаваме лимита за дължина (context limit)
    if len(conversations[chat_id]) > 11:
        conversations[chat_id] = [conversations[chat_id][0]] + conversations[chat_id][-10:]

    try:
        selected_model = get_active_chat_model()
        
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
    print("Стартиране на Telegram инстанцията...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Полингът спря: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
