import telebot
import AI_requests
import Database
import creds

Database.create_table()
token = creds.get_bot_token()
bot = telebot.TeleBot(token=token)

MAX_STT_BLOCKS = 200
MAX_GPT_TOKENS = 2000
MAX_TTS_SYMBOLS = 20000
MAX_USERS = 5

start_text = '''Привет!
Я универсальный бот-помошник'''
help_text = '''
Простой бот-помощник.
/start - Приветстивие и описание
/help - Список команд
/debug - Режим отладки
/tts - преобразование текста в речь
/stt - преобразование речи в текст
/gpt - генеративная нейросеть
/stt_gpt - генеративная нейросеть с распознованием речи
/gpt_tts - генеративная нейросеть с озвучкой ответа
/stt_gpt_tts - генеративная нейросеть с распознованием речи и озвучкой ответа'''
debug_mode = False


def user_in_list(id):
    return id in Database.collect_users_data('user_id')


def stt_allowed(id):
    return MAX_STT_BLOCKS > Database.collect_user_data(id, 'stt_blocks')


def tts_allowed(id):
    return MAX_TTS_SYMBOLS > Database.collect_user_data(id, 'tts_symbols')


def gpt_allowed(id):
    return MAX_GPT_TOKENS > Database.collect_user_data(id, 'gpt_tokens')


def tts_res(id, content_type, text):
    global debug_mode
    if tts_allowed(id):
        if content_type == 'text':
            if len(text) <= MAX_TTS_SYMBOLS // 10:
                s, r = AI_requests.tts(text)
                if s:
                    sym = Database.collect_user_data(id, 'tts_symbols')
                    sym += len(text)
                    Database.update_data(id, 'tts_symbols', sym)
                    return 't0', r
                else:
                    if debug_mode:
                        return 't1', r
                    else:
                        return 't1', 'Возникла ошибка! работаем над устранением.'
            else:
                return 't2', f'Превышено количество блоков в одном сообщении ' \
                             f'({len(text)}/' \
                             f'{MAX_TTS_SYMBOLS // 10})'
        else:
            return 't3', f'Тип сообщения не соответствует принимаемому типу модели'
    else:
        return 't4', 'Не осталось символов'


def stt_res(id, content_type, file, duration):
    global debug_mode
    if stt_allowed(id):
        if content_type == 'voice':
            if (duration // 15 + bool(duration % 15)) <= MAX_STT_BLOCKS // 10:
                s, r = AI_requests.stt(file)
                if s:
                    blocks = Database.collect_user_data(id, 'stt_blocks')
                    blocks += (duration // 15 + bool(duration % 15))
                    Database.update_data(id, 'stt_blocks', blocks)
                    return 's0', r
                else:
                    if debug_mode:
                        return 't1', r
                    else:
                        return 't1', 'Возникла ошибка! работаем над устранением.'
            else:
                return 's2', f'Превышено количество блоков в одном сообщении ' \
                             f'({(duration // 15 + bool(duration % 15))}/' \
                             f'{MAX_STT_BLOCKS // 10})'
        else:
            return 's3', f'Тип сообщения не соответствует принимаемому типу модели'
    else:
        return 's4', 'Не осталось блоков'


def gpt_res(id, content_type, text):
    global debug_mode
    if gpt_allowed(id):
        if content_type == 'text':
            if AI_requests.count_tokens(text) <= MAX_GPT_TOKENS // 10:
                s, r = AI_requests.gpt(text)
                if s:
                    tok = Database.collect_user_data(id, 'gpt_tokens')
                    tok += AI_requests.count_tokens(r)
                    Database.update_data(id, 'gpt_tokens', tok)
                    return 'g0', r
                else:
                    if debug_mode:
                        return 't1', r
                    else:
                        return 't1', 'Возникла ошибка! работаем над устранением.'
            else:
                return 'g2', f'Превышено количество блоков в одном сообщении ' \
                             f'({AI_requests.count_tokens(text)}/' \
                             f'{MAX_GPT_TOKENS // 10})'
        else:
            return 'g3', f'Тип сообщения не соответствует принимаемому типу модели'
    else:
        return 'g4', 'Не осталось токенов'


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, start_text)
    if not user_in_list(message.chat.id):
        if len(Database.collect_users_data('user_id')) < MAX_USERS:
            Database.insert_data(message.chat.id)
        else:
            bot.send_message(message.chat.id, 'Бот недоступен')


@bot.message_handler(commands=["help"])
def help_message(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=["debug"])
def help_message(message):
    global debug_mode
    if user_in_list(message.chat.id):
        if debug_mode:
            debug_mode = False
        else:
            debug_mode = True
        bot.send_message(message.chat.id, f'Режим отладки: {debug_mode}')


@bot.message_handler(commands=["tts"])
def tts_req(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, 'Введите текст, который нужно озвучить')
        bot.register_next_step_handler(message, tts)


@bot.message_handler(commands=["stt"])
def stt_req(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, 'Отправьте голосовое сообщение, которое нужно преобразовать в текст')
        bot.register_next_step_handler(message, stt)


@bot.message_handler(commands=["gpt"])
def gpt_req(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, 'Отправьте вопрос, который хотите задать')
        bot.register_next_step_handler(message, gpt)


@bot.message_handler(commands=["stt_gpt"])
def stt_gpt_req(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, 'Надиктуйте в голосовом сообщении вопрос, который хотите задать')
        bot.register_next_step_handler(message, stt_gpt)

@bot.message_handler(commands=["gpt_tts"])
def gpt_tts_req(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, 'Отправьте вопрос, который хотите задать')
        bot.register_next_step_handler(message, gpt_tts)


@bot.message_handler(commands=["stt_gpt_tts"])
def gpt_tts_req(message):
    if user_in_list(message.chat.id):
        bot.send_message(message.chat.id, 'Надиктуйте в голосовом сообщении вопрос, который хотите задать')
        bot.register_next_step_handler(message, stt_gpt_tts)


def tts(message):
    status, response = tts_res(message.chat.id, message.content_type, message.text)
    if status == 't0':
        bot.send_voice(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, 'tts: ' + response)


def stt(message):
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    status, response = stt_res(message.chat.id, message.content_type, file, message.voice.duration)
    bot.send_message(message.chat.id, response)

def gpt(message):
    status, response = gpt_res(message.chat.id, message.content_type, message.text)
    bot.send_message(message.chat.id, response)


def gpt_tts(message):
    status_1, response_1 = gpt_res(message.chat.id, message.content_type, message.text)
    if status_1 == 'g0':
        status_2, response_2 = tts_res(message.chat.id, 'text', response_1)
        if status_2 == 't0':
            bot.send_voice(message.chat.id, response_2)
        else:
            bot.send_message(message.chat.id, 'tts: ' + response_2)
    else:
        bot.send_message(message.chat.id, 'gpt: ' + response_1)

def stt_gpt(message):
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    status_1, response_1 = stt_res(message.chat.id, message.content_type, file, message.voice.duration)
    if status_1 == 's0':
        status_2, response_2 = gpt_res(message.chat.id, 'text', response_1)
        if status_2 == 'g0':
            bot.send_message(message.chat.id, response_2)
        else:
            bot.send_message(message.chat.id, 'gpt: ' + response_2)
    else:
        bot.send_message(message.chat.id, 'stt: ' + response_1)


def stt_gpt_tts(message):
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    status_1, response_1 = stt_res(message.chat.id, message.content_type, file, message.voice.duration)
    if status_1 == 's0':
        status_2, response_2 = gpt_res(message.chat.id, 'text', response_1)
        if status_2 == 'g0':
            status_3, response_3 = tts_res(message.chat.id, 'text', response_2)
            if status_3 == 't0':
                bot.send_voice(message.chat.id, response_3)
            else:
                bot.send_message(message.chat.id, 'tts: ' + response_3)
        else:
            bot.send_message(message.chat.id, 'gpt: ' + response_2)
    else:
        bot.send_message(message.chat.id, 'stt: ' + response_1)

bot.polling()
