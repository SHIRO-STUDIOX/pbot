import asyncio
import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import Config

logger = logging.getLogger("bot.handlers")
router = Router()

# Hardcoded allowed usernames for account delivery simulation
ALLOWED_USERNAMES = {"saleh_anaei", "saleh.anaei", "salehanaei", "saleh"}

# In-memory tracking of users who have already received their credentials
delivered_users = set()

def get_language_keyboard() -> types.InlineKeyboardMarkup:
    """
    Creates an inline keyboard markup for language selection.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇸 English", callback_data="lang:en")
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.adjust(2)
    return builder.as_markup()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Handles the /start command. Welcomes the user and asks to select a language.
    """
    user = message.from_user
    logger.info("User /start triggered by %s (ID: %s, Username: %s)", 
                user.full_name, user.id, user.username)
    
    welcome_text = (
        "👋 Hello! Welcome to the Purchase Delivery Bot.\n\n"
        "Please select your language to proceed:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👋 Здравствуйте! Добро пожаловать в бот доставки покупок.\n\n"
        "Пожалуйста, выберите язык, чтобы продолжить:"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_language_keyboard()
    )

@router.callback_query(F.data.startswith("lang:"))
async def process_language_selection(callback_query: types.CallbackQuery):
    """
    Handles the language selection callback and simulates purchase verification.
    """
    language = callback_query.data.split(":")[1]
    user = callback_query.from_user
    
    logger.info("User %s (ID: %s, Username: %s) selected language: %s", 
                user.full_name, user.id, user.username, language)
    
    # Text configs based on language
    if language == "en":
        checking_text = "🔍 *Checking your purchase...*\n\n_Please wait a moment while we verify your payment and retrieve your account credentials._"
        success_text = "✅ *Purchase verified successfully!* Delivering your account details below:"
        warning_text = "⚠️ *Important Notice:*\nPlease make sure to save your credentials immediately. This bot is only responsible for delivering the purchased details. The bot is temporary and may not be active or respond in the future."
        not_found_text = "❌ *Order Not Found:*\nWe could not find any active or unpaid purchases for your Telegram account."
        error_text = "❌ *Error:* Could not retrieve your account credentials. Please contact support."
        template_path = Config.DELIVERY_EN_PATH
    else:  # 'ru'
        checking_text = "🔍 *Проверка вашей покупки...*\n\n_Пожалуйста, подождите, пока мы проверим вашу оплату и получим данные вашего аккаунта._"
        success_text = "✅ *Покупка успешно подтверждена!* Ваши данные аккаунта доставлены ниже:"
        warning_text = "⚠️ *Важное примечание:*\nПожалуйста, обязательно сразу сохраните свои данные. Бот отвечает исключительно за выдачу данных о покупке. Этот бот является временным и в будущем может быть отключен или перестать отвечать."
        not_found_text = "❌ *Заказ не найден:*\nМы не смогли найти никаких активных или неоплаченных покупок для вашего аккаунта Telegram."
        error_text = "❌ *Ошибка:* Не удалось получить данные вашего аккаунта. Пожалуйста, обратитесь в поддержку."
        template_path = Config.DELIVERY_RU_PATH

    # Answer the callback query to remove loading animation in Telegram client
    await callback_query.answer()

    # Inform user about the verification status (send as a new message so previous remains)
    status_message = await callback_query.message.answer(
        text=checking_text,
        parse_mode="Markdown"
    )

    try:
        # Simulate check delay (e.g. database querying or external API checkout)
        logger.debug("Simulating verification delay of %s seconds...", Config.SIMULATION_DELAY)
        await asyncio.sleep(Config.SIMULATION_DELAY)

        # Check if the user is authorized (saleh.anaei or variants) and hasn't received it already
        username = user.username.lower() if user.username else ""
        is_allowed = username in ALLOWED_USERNAMES
        already_delivered = user.id in delivered_users

        if not is_allowed or already_delivered:
            logger.warning("Delivery rejected for user %s (ID: %s, Username: %s). Allowed: %s, Already delivered: %s",
                           user.full_name, user.id, user.username, is_allowed, already_delivered)
            await status_message.edit_text(
                text=not_found_text,
                parse_mode="Markdown"
            )
            return

        # Read delivery template
        logger.debug("Loading account details template from: %s", template_path)
        with open(template_path, "r", encoding="utf-8") as file:
            delivery_content = file.read()

        # Update status to success
        await status_message.edit_text(
            text=success_text,
            parse_mode="Markdown"
        )

        # Deliver credentials
        await callback_query.message.answer(
            text=delivery_content,
            parse_mode="Markdown"
        )

        # Deliver temporary bot warning
        await callback_query.message.answer(
            text=warning_text,
            parse_mode="Markdown"
        )
        
        # Mark as delivered
        delivered_users.add(user.id)
        logger.info("Successfully delivered purchase to user %s (ID: %s). Marked as delivered.", user.full_name, user.id)

    except FileNotFoundError:
        logger.error("Template file not found: %s", template_path)
        await status_message.edit_text(text=error_text, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Unexpected error during purchase simulation for user %s: %s", user.id, str(e))
        await status_message.edit_text(text=error_text, parse_mode="Markdown")
