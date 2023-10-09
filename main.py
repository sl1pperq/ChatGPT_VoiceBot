from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import openai
import uuid
import speech_recognition as sp
import torch

openai.api_key = 'OPENAI-TOKEN'
bot = telebot.TeleBot("TELEGRAM-TOKEN")

messages = [
    {
        "role": "system",
        "content": "You are a intelligent assistant."
    }
]

def GPT(message):
    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
    reply = chat.choices[0].message.content
    return reply


def MARKUP():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("👍", callback_data=f"like"), InlineKeyboardButton("👎", callback_data=f"dislike"))
    return markup

@bot.message_handler(commands=['anek', 'joke'])
def gpt_write_anek(ms):
    bot.send_message(ms.chat.id, 'Придумываю для тебя самый смешной анекдот...')
    bot.send_chat_action(ms.chat.id, action='typing')
    reply = GPT('Расскажи еще одну шутку, которая никого не оскорбит. Только шутку, без дополнительных слов.')
    bot.delete_message(ms.chat.id, ms.message_id + 1)
    bot.send_message(ms.chat.id, f'{reply}')
    messages.append({"role": "assistant", "content": reply})


@bot.message_handler(commands=['fact', 'interesting'])
def gpt_write_anek(ms):
    bot.send_message(ms.chat.id, 'Уже в поисках самого интересного факта...')
    bot.send_chat_action(ms.chat.id, action='typing')
    reply = GPT('Расскажи очень интересный факт о котором я не знал без дополнительных слов')
    bot.delete_message(ms.chat.id, ms.message_id + 1)
    bot.send_message(ms.chat.id, f'{reply}')
    messages.append({"role": "assistant", "content": reply})


@bot.callback_query_handler(func=lambda call: True)
def answer_to_feed(call):
    if call == 'like':
        bot.answer_callback_query(call.id, 'Рад, что ответ вам понравился!')
    elif call == 'dislike':
        bot.answer_callback_query(call.id, 'Мне очень жаль, что ответ вам не понравился!')


@bot.message_handler(content_types=['text'])
def gpt_main_question(ms):
    message = ms.text
    bot.send_message(ms.chat.id, 'Я уже думаю над ответом...')
    bot.send_chat_action(ms.chat.id, action='typing')
    reply = GPT(message)
    bot.delete_message(ms.chat.id, ms.message_id + 1)
    bot.send_message(ms.chat.id, f'{reply}', reply_markup=MARKUP())
    messages.append({"role": "assistant", "content": reply})


@bot.message_handler(content_types=['audio', 'voice'])
def gpt_voice_question(ms):
    device = torch.device('cpu')
    sample_rate = 48000
    language = 'ru'
    model_id = 'v3_1_ru'
    file_info = bot.get_file(ms.voice.file_id)
    down_file = bot.download_file(file_info.file_path)
    path = str(uuid.uuid4())
    with open(path + '.oga', 'wb') as file:
        file.write(down_file)
    convert_audio(path + '.oga')
    voice = sp.Recognizer()
    with sp.WavFile(path + '.oga.wav') as source:
        audio = voice.record(source)
        at = voice.recognize_google(audio, language='ru-RU')
        reply = GPT(at)
        messages.append({"role": "assistant", "content": reply})
        model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language=language, speaker=model_id)
        model.to(device)
        text = f'{reply}'
        audio = model.save_wav(text=text, speaker='baya', sample_rate=sample_rate, audio_path="audio.wav")
        with open('audio.wav', 'rb') as file:
            bot.send_voice(ms.chat.id, file)

def convert_audio(path):
    import subprocess
    src_filename = path
    dest_filename = path + '.wav'
    subprocess.run(['ffmpeg', '-i', src_filename, dest_filename])
    return dest_filename

bot.polling()
