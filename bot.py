import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    Message,
    ReplyKeyboardRemove,
    ForceReply
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.enums import ParseMode

# Konfiguratsiya
class Config:
    CHANNEL_USERNAME = "ajoyib_kino_kodlari1"
    CHANNEL_LINK = f"https://t.me/ajoyib_kino_kodlari1"
    CHANNEL_ID = -1002341118048
    
    SECRET_CHANNEL_USERNAME = "maxfiy_kino_kanal"
    SECRET_CHANNEL_LINK = f"https://t.me/maxfiy_kino_kanal"
    SECRET_CHANNEL_ID = -1002537276349
    
    BOT_TOKEN = "7808158374:AAGMY8mkb0HVi--N2aJyRrPxrjotI6rnm7k"
    ADMIN_IDS = [7871012050, 7183540853]

# Botni ishga tushirish
bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()  # Endi faqat Dispatcher() deb chaqiramiz

# Ma'lumotlar bazasi (vaqtincha)
user_data = set()
movies_db = {}
current_movie_id = 1

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obunani tekshirish funksiyasi
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(Config.CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Obunani tekshirishda xato: {e}")
        return False

async def ask_for_subscription(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Kanalga o'tish", url=Config.CHANNEL_LINK)
    builder.button(text="✅ Obuna bo'ldim", callback_data="check_subscription")
    builder.adjust(1)

    await message.answer(
        "🤖 Botdan to'liq foydalanish uchun quyidagi kanalga obuna bo'ling:\n"
        f"{Config.CHANNEL_LINK}\n\n"
        "Obuna bo'lgach, '✅ Obuna bo'ldim' tugmasini bosing.",
        reply_markup=builder.as_markup(),
        disable_web_page_preview=True
    )

@dp.callback_query(F.data == "check_subscription")
async def verify_subscription(query: types.CallbackQuery):
    if await check_subscription(query.from_user.id):
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Xabarni o'chirishda xato: {e}")
        
        await query.answer("✅ Obuna tasdiqlandi!", show_alert=True)
        await start_cmd(query.message)
    else:
        await query.answer("❌ Obuna tasdiqlanmadi!", show_alert=True)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user = message.from_user
    user_data.add(user.id)
    
    if not await check_subscription(user.id):
        await ask_for_subscription(message)
        return
    
    builder = ReplyKeyboardBuilder()
    builder.button(text="📞 Adminga murojaat")
    
    await message.answer(
        f"👋 Salom, {user.full_name}!\n\n"
        "🎥 Yuklamoqchi bo'lgan kinoyingizni kodini yuboring: ",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

# Admin paneli
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz!")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino qo'shish")],
            [KeyboardButton(text="❌ Kino o'chirish")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Reklama yuborish")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True,
    )

    await message.answer("👋 Admin paneliga xush kelibsiz!", reply_markup=keyboard)

import random
import string
from datetime import datetime

# Kino qo'shish funksiyalari
@dp.message(F.text == "🎬 Kino qo'shish")
async def start_adding_movie(message: Message):
    """Kino qo'shish jarayonini boshlash"""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("❌ Sizda bunday huquq yo'q!")
        return
    
    await message.answer(
        "🎥 Kino qo'shish uchun quyidagilardan birini yuboring:\n\n"
        "• Video fayl\n"
        "• Document (video fayl)\n\n"
        "📝 <b>Eslatma:</b>\n"
        "1. Kino avtomatik ravishda maxfiy kanalga joylanadi\n"
        "2. Har bir kino uchun maxsus kod generatsiya qilinadi\n"
        "3. Agar sarlavha ko'rsatmasangiz, kino nomi avtomatik yaratiladi",
        reply_markup=ReplyKeyboardRemove()
    )

def generate_movie_code():
    """6 xonali tasodifiy kino kodi generatsiya qilish"""
    return ''.join(random.choices(string.digits, k=6))

@dp.message(F.from_user.id.in_(Config.ADMIN_IDS) & (F.video | F.document))
async def handle_new_movie(message: Message):
    """Yangi kino qabul qilish va saqlash"""
    try:
        # Fayl ma'lumotlarini olish
        if message.video:
            file = message.video
            file_type = "video"
        else:
            file = message.document
            file_type = "document"
        
        # Sarlavha va kod generatsiyasi
        caption = message.caption or f"🎬 Kino {datetime.now().strftime('%d.%m.%Y')}"
        movie_code = generate_movie_code()
        
        # Kino kanalga yuborish
        if file_type == "video":
            sent_msg = await bot.send_video(
                chat_id=Config.SECRET_CHANNEL_ID,
                video=file.file_id,
                caption=f"{caption}\n\n🔐 Kino kodi: <code>{movie_code}</code>"
            )
        else:
            sent_msg = await bot.send_document(
                chat_id=Config.SECRET_CHANNEL_ID,
                document=file.file_id,
                caption=f"{caption}\n\n🔐 Kino kodi: <code>{movie_code}</code>"
            )
        
        # Ma'lumotlarni bazaga saqlash
        movies_db[movie_code] = {
            "file_id": file.file_id,
            "file_type": file_type,
            "caption": caption,
            "message_id": sent_msg.message_id,
            "date_added": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "added_by": message.from_user.id
        }
        
        # Adminga javob
        await message.answer(
            f"🎉 <b>Kino muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📌 Nomi: {caption}\n"
            f"🔢 Kodi: <code>{movie_code}</code>\n"
            f"📆 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🔗 Kanaldagi post: https://t.me/{Config.SECRET_CHANNEL_USERNAME}/{sent_msg.message_id}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="➕ Yana kino qo'shish")],
                    [KeyboardButton(text="🏠 Bosh menyu")]
                ],
                resize_keyboard=True
            ),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Kino qo'shishda xato: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Kino qo'shishda xatolik yuz berdi!\n\n"
            "Iltimos, quyidagilarni tekshiring:\n"
            "1. Fayl hajmi (20MB dan oshmasligi kerak)\n"
            "2. Internet aloqasi\n"
            "3. Fayl formati (MP4, MKV va h.k.)\n\n"
            "Qayta urunib ko'ring yoki texnik yordamga murojaat qiling.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
                resize_keyboard=True
            )
        )


# Kino o'chirish funksiyalari
@dp.message(F.text == "❌ Kino o'chirish")
async def start_removing_movie(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    if not movies_db:
        await message.answer("⚠️ Hozircha hech qanday kino mavjud emas!")
        return
    
    movies_list = "\n".join([f"{id}: {data['caption']}" for id, data in movies_db.items()])
    
    await message.answer(
        f"🗑 O'chirish uchun kino raqamini yuboring:\n\n"
        f"{movies_list}\n\n"
        "❗ Eslatma: Kino kanaldan ham o'chib ketadi!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )

@dp.message(F.from_user.id.in_(Config.ADMIN_IDS) & F.text.regexp(r'^\d+$'))
async def remove_movie(message: Message):
    movie_id = message.text.strip()
    
    if movie_id not in movies_db:
        await message.answer("❌ Bunday raqamdagi kino topilmadi!")
        return
    
    try:
        await bot.delete_message(Config.SECRET_CHANNEL_ID, movies_db[movie_id]["message_id"])
        del movies_db[movie_id]
        
        await message.answer(
            f"✅ Kino #{movie_id} muvaffaqiyatli o'chirildi!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🏠 Admin panel")]],
                resize_keyboard=True
            )
        )
        
    except Exception as e:
        logger.error(f"Kino o'chirishda xato: {e}")
        await message.answer("❌ Kino o'chirishda xatolik yuz berdi. Iltimos, qayta urunib ko'ring.")

# Foydalanuvchilarga kinolarni yuborish
@dp.message(F.text.regexp(r'^\d+$') & ~F.from_user.id.in_(Config.ADMIN_IDS))
async def send_movie_to_user(message: Message):
    movie_id = message.text.strip()
    
    if not await check_subscription(message.from_user.id):
        await ask_for_subscription(message)
        return
    
    if movie_id not in movies_db:
        await message.answer("❌ Bunday raqamdagi kino topilmadi!")
        return
    
    movie = movies_db[movie_id]
    
    try:
        if movie["file_type"] == "video":
            await message.answer_video(movie["file_id"], caption=movie["caption"])
        else:
            await message.answer_document(movie["file_id"], caption=movie["caption"])
    except Exception as e:
        logger.error(f"Kino yuborishda xato: {e}")
        await message.answer("❌ Kino yuborishda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")

# Qolgan funksiyalar (adminga murojaat, statistika, reklama)
@dp.message(F.text == "📞 Adminga murojaat")
async def contact_admin(message: Message):
    await message.answer(
        "✍️ Adminga xabar yuborish uchun matn, rasm, video yoki fayl yuboring.\n\n"
        "Yoki to'g'ridan-to'g'ri @admin ga yozishingiz mumkin.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(F.chat.type == "private", ~F.from_user.id.in_(Config.ADMIN_IDS))
async def user_to_admin(message: Message):
    try:
        user_info = (
            f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"📅 Sana: {message.date.strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        
        if message.text:
            caption = f"{user_info}📝 Xabar: {message.text}"
            for admin_id in Config.ADMIN_IDS:
                await bot.send_message(admin_id, caption, reply_markup=ForceReply())
        
        elif message.photo:
            caption = f"{user_info}📷 Rasm"
            for admin_id in Config.ADMIN_IDS:
                await bot.send_photo(admin_id, message.photo[-1].file_id, 
                                   caption=caption, 
                                   reply_markup=ForceReply())
        
        elif message.video:
            caption = f"{user_info}🎥 Video"
            for admin_id in Config.ADMIN_IDS:
                await bot.send_video(admin_id, message.video.file_id, 
                                   caption=caption, 
                                   reply_markup=ForceReply())
        
        elif message.document:
            caption = f"{user_info}📄 Fayl: {message.document.file_name}"
            for admin_id in Config.ADMIN_IDS:
                await bot.send_document(admin_id, message.document.file_id, 
                                      caption=caption, 
                                      reply_markup=ForceReply())
        
        await message.answer("✅ Xabaringiz adminlarga yuborildi. Javobni kuting.")
    
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")
        await message.answer("❌ Xabar yuborishda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")

@dp.message(F.reply_to_message, F.from_user.id.in_(Config.ADMIN_IDS))
async def admin_to_user(message: Message):
    try:
        original_msg = message.reply_to_message.text or message.reply_to_message.caption
        
        if original_msg and "👤 Foydalanuvchi:" in original_msg:
            user_id_line = next(line for line in original_msg.split('\n') if "🆔 ID:" in line)
            user_id = int(user_id_line.split(":")[1].strip())
            
            reply_text = (
                "📩 Admin javobi:\n\n"
                f"{message.text}\n\n"
                "💬 Savolingiz bo'lsa, yana yozishingiz mumkin."
            )
            await bot.send_message(user_id, reply_text)
            await message.answer("✅ Javob foydalanuvchiga yuborildi.")
    
    except Exception as e:
        logger.error(f"Javob yuborishda xato: {e}")
        await message.answer("❌ Javob yuborishda xatolik. Foydalanuvchi ID topilmadi.")

@dp.message(F.text == "📊 Statistika")
async def show_statistics(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz!")
        return

    total_users = len(user_data)
    total_movies = len(movies_db)
    
    await message.answer(
        f"📊 Bot statistikasi:\n\n"
        f"👤 Foydalanuvchilar soni: {total_users}\n"
        f"🎬 Kinolar soni: {total_movies}"
    )

@dp.message(F.text == "📢 Reklama yuborish")
async def ask_for_advertisement(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    await message.answer("✍️ Reklama uchun matn, rasm, video yoki fayl yuboring.")

@dp.message(F.from_user.id.in_(Config.ADMIN_IDS))
async def send_advertisement(message: Message):
    if not user_data:
        await message.answer("⚠️ Hozircha hech qanday foydalanuvchi yo'q!")
        return

    success, failed = 0, 0

    for user_id in user_data:
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.document:
                await bot.send_document(user_id, message.document.file_id, caption=message.caption)
            success += 1
        except Exception as e:
            logger.error(f"Xabar yuborilmadi (User ID: {user_id}): {e}")
            failed += 1

    await message.answer(f"✅ Reklama {success} ta foydalanuvchiga yuborildi!\n❌ Xatoliklar: {failed}")

@dp.message(F.text == "🏠 Asosiy menyu")
async def back_to_main_menu(message: types.Message):
    await start_cmd(message)

async def main():
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
