bot.send_chat_action(message.chat.id, 'typing')
        user_text = message.text.replace(f"@{bot_username}", "").strip() if message.text else ""

        # СТРИКТНИ ИНСТРУКЦИИ ЗА ПЕРФЕКТЕН БЪЛГАРСКИ ЕЗИК
        system_content = (
            "Ти си интелигентен AI асистент с перфектен изказ на български език.\n"
            "ПРАВИЛА ЗА ЕЗИКА:\n"
            "1. Говори на ПЕРФЕКТЕН, ЕСТЕСТВЕН български език. Избягвай буквален превод от английски.\n"
            "2. Внимавай за граматически грешки, падежни форми, правилно използване на пълен/кратък член и предлози.\n"
            "3. Преди да изпратиш отговора, провери наум дали звучи правилно за роден български говорител."
        )
        
        # Проверка за времето
        if "време" in user_text.lower() or "времето" in user_text.lower():
            real_weather = get_weather_data()
            system_content += f"\n\nВАЖНО: Използвай следните реални данни, за да отговориш на въпроса за времето:\n{real_weather}"

        # Извикване на Groq с мощния модел на OpenAI с отворен код
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_text}
            ],
            model="openai/gpt-oss-120b",  # <--- Слагаме 120-милиардния модел
        )
