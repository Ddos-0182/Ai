import asyncio
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from fpdf import FPDF
import logging
import os

# Set your API keys and owner details
OPENAI_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "7694445973:AAHsBQyfItoJxHks6bOsOXmjcXCGPwVtR-8"
OWNER_USER_ID = "7083378335"

# Configure OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

user_contexts = {}

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hi! I'm your AI-powered bot. Use /help to see what I can do!")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/generate_image [description] - Create an AI-generated image\n"
        "/generate_document [type] - Generate a document (e.g., resume)"
    )

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_message = update.message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = [{"role": "system", "content": "You are a helpful assistant."}]
    user_contexts[user_id].append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model="gpt-4",  # Use "gpt-4" or "gpt-3.5-turbo"
            messages=user_contexts[user_id],
            max_tokens=200
        )
        reply = response.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def generate_image(update: Update, context: CallbackContext):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Please provide a description for the image.")
        return

    try:
        response = await client.images.generate(
            model="dall-e-3",  # Use DALL·E 3 for better images
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        image_url = response.data[0].url
        await update.message.reply_text(f"Here is your image: {image_url}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def generate_document(update: Update, context: CallbackContext):
    doc_type = " ".join(context.args)
    if not doc_type:
        await update.message.reply_text("Please specify the document type (e.g., resume).")
        return

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Generated {doc_type.title()}", ln=True, align='C')
        file_name = f"{doc_type}.pdf"
        pdf.output(file_name)

        await update.message.reply_document(document=open(file_name, "rb"))
        os.remove(file_name)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate_image", generate_image))
    application.add_handler(CommandHandler("generate_document", generate_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    try:
        asyncio.run(application.run_polling())
    except RuntimeError:  # Handle "event loop is already running"
        loop = asyncio.get_event_loop()
        loop.run_until_complete(application.run_polling())

if __name__ == "__main__":
    main()
