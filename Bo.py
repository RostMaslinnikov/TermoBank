import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, InputMediaPhoto
from aiogram.filters import Command
import asyncio
import re
import pandas as pd
from datetime import datetime
import openpyxl

# Налаштування
API_TOKEN = '7532377672:AAFwPmjQOIAVZIj0CX6KSYqz8knI0YrGLRo'
CHANNEL_ID = -1002625040947
EXCEL_FILE = r"C:\Users\rost4\OneDrive\Документи\Нова папка (4)\user_stats.xlsx"

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота і диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ініціалізація глобальних змінних
message_mapping = {}
media_groups = {}
user_stats = {}
username_to_id = {}

# Функції для клавіатури
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="+ дроп 💳")],
            [KeyboardButton(text="Статистика 📈")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад 🔙")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Функції для роботи з Excel
def load_data_from_excel():
    try:
        df = pd.read_excel(EXCEL_FILE)
        global user_stats, username_to_id
        
        for _, row in df.iterrows():
            user_id = row['user_id']
            username = row['username']
            user_stats[user_id] = {
                'total_users': row['total_users'],
                'failed_users': row['failed_users'],
                'processing_users': row['processing_users'],
                'paid_users': row['paid_users'],
                'rate': row.get('rate', 900)  # Додаємо поле ставки
            }
            if username:
                username_to_id[username.lower()] = user_id
    except FileNotFoundError:
        save_data_to_excel()

def save_data_to_excel():
    try:
        data = []
        for user_id, stats in user_stats.items():
            username = next((k for k, v in username_to_id.items() if v == user_id), None)
            data.append({
                'user_id': user_id,
                'username': username,
                'total_users': stats['total_users'],
                'failed_users': stats['failed_users'],
                'processing_users': stats['processing_users'],
                'paid_users': stats['paid_users'],
                'rate': stats.get('rate', 900),  
                'last_updated': datetime.now()
            })
        
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']
            for column in worksheet.columns:
                worksheet.column_dimensions[column[0].column_letter].width = 20
            for row in worksheet.rows:
                worksheet.row_dimensions[row[0].row].height = 26
                
        logging.info(f"Дані успішно збережено в {EXCEL_FILE}")
    except Exception as e:
        logging.error(f"Помилка при збереженні даних: {e}")
        logging.exception("Повний стек помилки:")

def init_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {
            'total_users': 0,    
            'failed_users': 0,   
            'processing_users': 0,
            'paid_users': 0,
            'rate': 900  
        }
        save_data_to_excel()


def get_stats_by_username(username):
    user_id = username_to_id.get(username.lower())
    if user_id and user_id in user_stats:
        return user_stats[user_id]
    return None

# Хендлери команд
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Вас вітає CryptoWhale цей бот буде на заміні каналу статистика тобто все тоже саме ви будете кидати сюда",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text and message.text.startswith('@'))
async def handle_username_stats(message: Message):
    try:
        # Розбиваємо повідомлення на частини
        parts = message.text.strip().lower().split()
        username = parts[0].strip('@')
        
        # Якщо це команда зміни ставки і повідомлення з каналу
        if len(parts) == 3 and parts[1] == "ставка" and message.chat.id == CHANNEL_ID:
            try:
                new_rate = int(parts[2])
                user_id = username_to_id.get(username)
                
                if user_id and user_id in user_stats:
                    old_rate = user_stats[user_id].get('rate', 900)
                    user_stats[user_id]['rate'] = new_rate
                    save_data_to_excel()
                    
                    notification_text = (
                        f"Ваша ставка була змінена!\n"
                        f"Стара ставка: {old_rate} грн\n"
                        f"Нова ставка: {new_rate} грн"
                    )
                    await bot.send_message(chat_id=user_id, text=notification_text)
                    await message.reply(f"Ставка для @{username} успішно оновлена до {new_rate} грн")
                else:
                    await message.reply(f"Користувача @{username} не знайдено в базі даних")
                return
            except ValueError:
                await message.reply("Неправильний формат ставки. Використовуйте числове значення")
                return
        
        # Якщо це звичайний запит статистики
        stats = get_stats_by_username(username)
        if stats:
            stats_message = (
                f"Статистика користувача @{username} 📈\n"
                f"Загальна кількість людей які були приведені 🧾: {stats['total_users']}\n"
                f"Скільки людей слилося📉: {stats['failed_users']}\n"
                f"Скільки людей в обробці зараз⌚: {stats['processing_users']}\n"
                f"Скільки людям виплачено💳: {stats['paid_users']}\n"
                f"Ставка 💸: {stats.get('rate', 900)} грн"
            )
        else:
            stats_message = f"Статистика для користувача @{username} не знайдена"
        
        await message.reply(stats_message)
        
    except Exception as e:
        logging.error(f"Помилка при обробці команди: {str(e)}")
        await message.reply("Сталася помилка при обробці команди")

#Кнопка дроп
@dp.message(F.text == "+ дроп 💳")
async def handle_drop(message: Message):
    await message.answer(
        "Відправте 4 фото:\n1. Скріншот паспорта з дії (2 скріншоти)\n2. Скріншот з гаманця\n3. Скріншот з банку\n\nТа підпис у форматі: @username (сума)",
        reply_markup=get_back_keyboard()
    )
#Кнопка статистка
@dp.message(F.text == "Статистика 📈")
async def handle_statistics(message: Message):
    user_id = message.from_user.id
    init_user_stats(user_id)
    stats = user_stats[user_id]
    
    stats_message = (
        "Ваша статистика 📈\n"
        f"Загальна кількість людей яких ви привели 🧾: {stats['total_users']}\n"
        f"Скільки людей слилося📉: {stats['failed_users']}\n"
        f"Скільки людей в обробці зараз⌚: {stats['processing_users']}\n"
        f"Скільки людям виплачено💳: {stats['paid_users']}\n"
        f"Ваша ставка 💸: {stats.get('rate', 900)} грн"
    )
    
    await message.answer(stats_message, reply_markup=get_back_keyboard())


@dp.message(F.text == "Назад 🔙")
async def handle_back(message: Message):
    await message.answer(
        "Головне меню🧑‍💻",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.media_group_id)
async def handle_album(message: types.Message):
    try:
        if message.from_user.username:
            username_to_id[message.from_user.username.lower()] = message.from_user.id
            
        group_id = message.media_group_id
        
        if group_id not in media_groups:
            media_groups[group_id] = {
                'photos': [],
                'caption': None,
                'processed': False,
                'target_username': None
            }
        
        if message.photo:
            media_groups[group_id]['photos'].append(message.photo[-1])
            if message.caption:
                username_match = re.search(r'@(\w+)', message.caption)
                if username_match:
                    media_groups[group_id]['target_username'] = username_match.group(1)
                sender_info = f"Від: @{message.from_user.username}" if message.from_user.username else f"Від: {message.from_user.first_name}"
                media_groups[group_id]['caption'] = f"{message.caption}\n{sender_info}"

        if len(media_groups[group_id]['photos']) == 4 and not media_groups[group_id]['processed']:
            caption = media_groups[group_id]['caption']
            
            if not caption or '@' not in caption:
                await message.answer("Неправильний формат підпису. Додайте підпис у форматі: @username (сума)")
                return

            media = []
            for i, photo in enumerate(media_groups[group_id]['photos']):
                media.append(InputMediaPhoto(
                    media=photo.file_id,
                    caption=caption if i == 3 else None
                ))

            sent_messages = await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            
            for sent_msg in sent_messages:
                message_mapping[sent_msg.message_id] = {
                    'original_message_id': message.message_id,
                    'from_user': message.from_user,
                    'target_username': media_groups[group_id]['target_username']
                }

            await message.answer("Фото успішно відправлені!", reply_markup=get_main_keyboard())
            media_groups[group_id]['processed'] = True

            await asyncio.sleep(10)
            if group_id in media_groups:
                del media_groups[group_id]

    except Exception as e:
        logging.error(f"Помилка при обробці альбому: {str(e)}")
        await message.answer("Сталася помилка при обробці фото. Спробуйте ще раз.")

@dp.message(F.photo)
async def handle_single_photo(message: types.Message):
    if not message.media_group_id:
        await message.answer("Будь ласка, відправте всі 4 фото разом однією групою")

@dp.message(lambda message: message.chat.id == CHANNEL_ID and message.text and "ставка" in message.text.lower())
async def handle_rate_change(message: Message):
    try:
        # Шукаємо username та нову ставку
        match = re.search(r'@(\w+)\s+ставка\s+(\d+)', message.text.lower())
        if match:
            username, new_rate = match.groups()
            new_rate = int(new_rate)
            
            user_id = username_to_id.get(username.lower())
            if user_id and user_id in user_stats:
                old_rate = user_stats[user_id].get('rate', 900)
                user_stats[user_id]['rate'] = new_rate
                save_data_to_excel()
                
                # Відправляємо повідомлення користувачу про зміну ставки
                notification_text = (
                    f"Ваша ставка була змінена!\n"
                    f"Стара ставка: {old_rate} грн\n"
                    f"Нова ставка: {new_rate} грн"
                )
                await bot.send_message(chat_id=user_id, text=notification_text)
                await message.reply(f"Ставка для @{username} успішно оновлена до {new_rate} грн")
            else:
                await message.reply("Користувача не знайдено в базі даних")
    except Exception as e:
        logging.error(f"Помилка при зміні ставки: {str(e)}")
        await message.reply("Помилка при зміні ставки. Використовуйте формат: @username ставка 1000")


@dp.message_reaction()
async def handle_reaction(reaction: types.MessageReactionUpdated):
    try:
        message_info = message_mapping.get(reaction.message_id)
        if message_info and hasattr(reaction, 'new_reaction') and reaction.new_reaction:
            original_message_id = message_info['original_message_id']
            from_user = message_info['from_user']
            target_username = message_info.get('target_username', '')
            
            if from_user.username:
                username_to_id[from_user.username.lower()] = from_user.id
            
            init_user_stats(from_user.id)
            
            reaction_emoji = None
            for react in reaction.new_reaction:
                if hasattr(react, 'emoji'):
                    reaction_emoji = react.emoji
                    break
                elif hasattr(react, 'emoticon'):
                    reaction_emoji = react.emoticon
                    break
            
            if not reaction_emoji:
                reaction_emoji = str(reaction.new_reaction[0])
            
            logging.info(f"Отримано реакцію: {reaction_emoji}")
            
            if any(emoji in str(reaction_emoji) for emoji in ["🤡", "🤝", "🔥"]):
                if "🤡" in str(reaction_emoji):
                    notification_text = f"@{from_user.username}, @{target_username} слився 🤡"
                    user_stats[from_user.id]['failed_users'] += 1
                elif "🤝" in str(reaction_emoji):
                    notification_text = f"@{from_user.username}, @{target_username} взяли карту очікуй 🤝"
                    user_stats[from_user.id]['processing_users'] += 1
                elif "🔥" in str(reaction_emoji):
                    notification_text = f"@{from_user.username}, @{target_username} оплачено 🔥"
                    user_stats[from_user.id]['paid_users'] += 1
                    if user_stats[from_user.id]['processing_users'] > 0:
                        user_stats[from_user.id]['processing_users'] -= 1
                
                user_stats[from_user.id]['total_users'] += 1
                save_data_to_excel()
                
                await bot.send_message(
                    chat_id=from_user.id,
                    text=notification_text
                )
                
                try:
                    await bot.set_message_reaction(
                        chat_id=reaction.chat.id,
                        message_id=original_message_id,
                        reaction=[types.ReactionEmoji(emoji=str(reaction_emoji))]
                    )
                except Exception as e:
                    logging.error(f"Помилка при встановленні реакції: {str(e)}")

    except Exception as e:
        logging.error(f"Помилка при обробці реакції: {str(e)}")
        logging.exception("Повний стек помилки:")

async def main():
    try:
        logging.info("Завантаження даних з Excel...")
        load_data_from_excel()
        logging.info("Бот запущений та готовий до роботи...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Критична помилка при запуску бота: {e}")
        import traceback
        logging.error("Повний стек помилки:")
        logging.error(traceback.format_exc())



if __name__ == '__main__':
    asyncio.run(main())
