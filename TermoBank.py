import telebot
from telebot import types


bot = telebot.TeleBot('6139444297:AAFDWVDvefVvSuFTv2Z384yqgaYpd3hRFMc')
admin_chat_ids = ['835522862', '1766628578', '1569906096']  # Add all the admin chat IDs here

@bot.message_handler(commands=['start'])
def send_button(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup()
    markup.row('Техпідтримка')
    markup.row('Взяти кредит', 'Інформація про взятя кредиту')
    markup.row('Інформація про банк')
    bot.send_message(chat_id, 'Доброго дня вас вітає TermoBank виберіть дію як хочите виконати😀:', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'Взяти кредит':
        chat_id = message.chat.id
        name = message.chat.first_name  # отримуємо ім'я користувача, який натиснув кнопку
        # Створюємо нову клавіатуру з можливістю скасування запиту
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('Скасувати', callback_data='cancel_credit_request'))
        # Надсилаємо повідомлення користувачеві з клавіатурою
        bot.send_message(chat_id,
                         f'{name}, ви натиснули кнопку "Взяти кредит". Бажаєте надіслати запит на отримання кредиту адміністратору? якщо так то напишіть про це в чаті',
                         reply_markup=markup)
        bot.register_next_step_handler(message, send_credit_request_to_admin)
    elif message.text == 'Інформація про взятя кредиту':
        chat_id = message.chat.id
        bot.send_message(chat_id, f'Інформація по взятя кредиту😶. Мінімальна суму кредиу 100 максимальна 750.🤑'f'Процент на кредит в день 2% наприклад якщо ви взяли кредит на 750 грн то в день + 15 грн💸')
    elif message.text == 'Інформація про банк':
        chat_id = message.chat.id
        bot.send_message(chat_id, 'TermoBank - це сучасний банк, який надає широкий спектр послуг з обслуговування фізичних та юридичних осіб.')
    elif message.text == 'Техпідтримка':
        chat_id = message.chat.id
        bot.send_message(chat_id, 'Будь ласка, опишіть свою проблему:')
        bot.register_next_step_handler(message, reply_to_credit_request)


def reply_to_credit_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Ваш запит на кредит отримано. Адміністратор незабаром перегляне його.")

def reply_to_credit_request(message):
    text = f'Користувач {message.chat.id} написав:\n\n{message.text} @{message.chat.username}'
    for chat_id in admin_chat_ids:
        bot.send_message(admin_chat_ids[0], text)

def send_credit_request_to_admin(message):
    chat_id = message.chat.id
    text = f'Користувач {chat_id} написав:\n\n{message.text} @{message.chat.username}'
    for admin_chat_id in admin_chat_ids:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('Прийняти', callback_data=f'approve_credit_request_{chat_id}'),
                   types.InlineKeyboardButton('Відхилити', callback_data=f'reject_credit_request_{chat_id}'))
        bot.send_message(admin_chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_credit_request_'))
def approve_credit_request(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, f'Ваш запит на кредит схвалено. Дякуємо, що користуєтесь нашими послугами! Chat id: {chat_id}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_credit_request_'))
def reject_credit_request(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, f'На жаль, ваш запит на кредит було відхилено. Спробуйте звернутися до нас ще раз пізніше. Chat id: {chat_id}')


bot.infinity_polling()