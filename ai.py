import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
from fpdf import FPDF
import os
import asyncio

# Set API keys and owner ID
OPENAI_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "7694445973:AAHsBQyfItoJxHks6bOsOXmjcXCGPwVtR-8"
OWNER_USER_ID = "7083378335"  # Replace with your Telegram ID

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# User contexts for conversations
user_contexts = {}

async def generate_image(update: Update, context: CallbackContext):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a description. Example: /generate_image a sunset over the ocean")
        return

    try:
        response = openai.Image.create(prompt=query, n=1, size="1024x1024")
        image_url = response['data'][0]['url']
        await update.message.reply_text(f"Here is your generated image: {image_url}")
    except Exception as e:
        await update.message.reply_text(f"Error generating image: {str(e)}")

async def generate_document(update: Update, context: CallbackContext):
    doc_type = " ".join(context.args)
    if not doc_type:
        await update.message.reply_text("Please specify the document type. Example: /generate_document resume")
        return

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Generated {doc_type.title()}", ln=True, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=f"This is a sample {doc_type}. Customize as needed.")

        file_path = f"{doc_type}_generated.pdf"
        pdf.output(file_path)

        await update.message.reply_document(document=open(file_path, "rb"))
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"Error generating document: {str(e)}")

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_message = update.message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    user_contexts[user_id].append({"role": "user", "content": user_message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_contexts[user_id],
            max_tokens=200,
            temperature=0.7,
        )
        bot_reply = response['choices'][0]['message']['content']
        user_contexts[user_id].append({"role": "assistant", "content": bot_reply})
        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Hi! I'm your AI-powered bot. 🤖\n\n"
        "I can chat, generate images, create documents, and more.\n"
        "Use /help to see available commands!"
    )

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📋 *Help Menu*\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/generate_image [description] - Generate an AI image\n"
        "/generate_document [type] - Generate a document (e.g., resume, report)\n"
        "Type your question, and I'll assist!"
    )

async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate_image", generate_image))
    application.add_handler(CommandHandler("generate_document", generate_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ✅ This prevents "coroutine was never awaited" errors
    try:
        await application.initialize()
        await application.run_polling()
    finally:
        await application.shutdown()

# ✅ **Final Fix for Event Loop Issues**
def run_bot():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main())

if __name__ == "__main__":
    run_bot()
