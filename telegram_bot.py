import os
import telebot
from groq import Groq

# Вземане на ключовете от променливите на средата (Environment Variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Инициализиране
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Здравей! Аз съм супер бърз AI бот, задвижван от Groq. Питай ме каквото и да е! ⚡")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Показва "typing..." в Telegram
        bot.send_chat_action(message.chat.id, 'typing')

        # Изпращане на въпроса към Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ти си полезен и умен асистент. Отговаряй на български език, освен ако потребителят не поиска друго."},
                {"role": "user", "content": message.text}
            ],
            model="llama-3.3-70b-versatile", # Използваме най-мощния безплатен модел
        )

        # Връщане на отговора в Telegram
        response = chat_completion.choices[0].message.content
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"Опа, възникна грешка: {str(e)}")

print("Ботът е стартиран и очаква съобщения...")
bot.infinity_polling()