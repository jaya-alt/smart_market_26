import os
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from app.config import TELEGRAM_BOT_TOKEN
from app.agent.agent import run_agent, clear_session, get_last_generated_files
from app.services.idempotency_service import is_duplicate


# ============================================================
# START COMMAND
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Supermarket Ops Agent!\n\n"
        "I can help you with:\n\n"
        "📦 Stock checking & receiving\n"
        "🧾 Billing (create, add/edit/remove items, finalize)\n"
        "👥 Customer Khata (credit, payments, reminders)\n"
        "📊 Daily sales & closing reports\n"
        "📈 Sales analysis PowerPoint (with real charts)\n"
        "📄 GST invoices (PDF)\n"
        "⚙️ Remembering your preferences\n\n"
        "Just talk to me naturally, e.g.:\n"
        "• What is the stock of Maggi?\n"
        "• Start a new bill\n"
        "• Show low stock products\n"
        "• Give me today's closing report\n\n"
        "Send /new to start a fresh conversation (your stock, bills, "
        "and khata are never affected by this -- only the chat memory)."
    )


# ============================================================
# CLEAR CONVERSATION
# ============================================================

async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    clear_session(user_id)

    await update.message.reply_text(
        "🧹 Conversation cleared. Your stock, bills, khata, and saved "
        "preferences are all still exactly as they were."
    )


# ============================================================
# HANDLE USER MESSAGES
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # ------------------------------------------------------
    # Idempotency guard: skip anything we've already processed
    # (e.g. Telegram redelivering an update after a restart).
    # ------------------------------------------------------

    if is_duplicate("telegram", update.update_id):
        return

    user_message = update.message.text
    user_id = str(update.effective_user.id)

    try:
        await update.message.chat.send_action(action="typing")

        response = run_agent(user_message=user_message, session_id=user_id)
        files = get_last_generated_files(user_id)

        if response:
            max_length = 4000

            for i in range(0, len(response), max_length):
                await update.message.reply_text(response[i:i + max_length])
        else:
            await update.message.reply_text("Sorry, I couldn't generate a response.")

        for file_path in files:
            path = Path(file_path)

            if not path.exists():
                continue

            with open(path, "rb") as handle:
                await update.message.reply_document(
                    document=handle,
                    filename=path.name
                )

    except Exception as e:
        print("TELEGRAM BOT ERROR:", str(e))

        await update.message.reply_text(
            "⚠️ Something went wrong while processing your request. "
            "Please try again."
        )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Telegram error: {context.error}")


# ============================================================
# MAIN FUNCTION
# ============================================================

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    print("=" * 60)
    print("SUPERMARKET OPS TELEGRAM BOT")
    print("=" * 60)

    try:
        # Check Telegram token
        if not TELEGRAM_BOT_TOKEN:
            print("ERROR: TELEGRAM_BOT_TOKEN is NOT set")
            return

        print("TELEGRAM_BOT_TOKEN found")
        print("Bot is starting...")

        # Create Telegram application
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("clear", clear_chat))
        app.add_handler(CommandHandler("new", clear_chat))

        # Normal text messages
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_message
            )
        )

        # Error handler
        app.add_error_handler(error_handler)

        print("Telegram bot is running...")
        print("Starting polling...")

        # Keep bot running and listen for Telegram updates
        app.run_polling()

    except Exception as e:
        print("=" * 60)
        print("FATAL TELEGRAM BOT ERROR")
        print("=" * 60)
        print(f"{type(e).__name__}: {e}")

        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()