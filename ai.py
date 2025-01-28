import openai
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
from fpdf import FPDF
import os
import asyncio
import sys

# Set API keys and owner ID
OPENAI_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "7694445973:AAHsBQyfItoJxHks6bOsOXmjcXCGPwVtR-8"
OWNER_USER_ID = "7083378335"  # Replace with the Telegram ID of the bot owner

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# User contexts for conversations
user_contexts = {}

# Function to send logs to the bot owner
def send_log_to_owner(context: CallbackContext, log_message: str):
    try:
        context.bot.send_message(chat_id=OWNER_USER_ID, text=log_message)
    except Exception as e:
        logger.error(f"Failed to send log to owner: {e}")

# Handle image generation with DALL·E
async def generate_image(update: Update, context: CallbackContext):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a description. Example: /generate_image a sunset over the ocean")
        return

    try:
        response = openai.Image.create(
            prompt=query,
            n=1,
            size="1024x1024",
        )
        image_url = response['data'][0]['url']
        await update.message.reply_text(f"Here is your generated image: {image_url}")
        log_message = f"Image generated for user {update.message.chat_id}: {query} -> {image_url}"
        send_log_to_owner(context, log_message)
    except Exception as e:
        await update.message.reply_text(f"Error generating image: {str(e)}")
        send_log_to_owner(context, f"Error generating image for user {update.message.chat_id}: {str(e)}")

# Handle document generation
async def generate_document(update: Update, context: CallbackContext):
    doc_type = " ".join(context.args)
    if not doc_type:
        await update.message.reply_text("Please specify the document type. Example: /generate_document resume")
        return

    try:
        # Create a simple PDF using FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Generated {doc_type.title()}", ln=True, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=f"This is a sample {doc_type}. Customize this section as needed.")

        # Save PDF locally
        file_path = f"{doc_type}_generated.pdf"
        pdf.output(file_path)

        # Send the document to the user
        await update.message.reply_document(document=open(file_path, "rb"))
        os.remove(file_path)  # Cleanup after sending
        log_message = f"Document '{doc_type}' generated for user {update.message.chat_id}"
        send_log_to_owner(context, log_message)
    except Exception as e:
        await update.message.reply_text(f"Error generating document: {str(e)}")
        send_log_to_owner(context, f"Error generating document for user {update.message.chat_id}: {str(e)}")

# Handle text conversations
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_message = update.message.text

    # Maintain user-specific context
    if user_id not in user_contexts:
        user_contexts[user_id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

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

        # Send reply to user
        await update.message.reply_text(bot_reply)

        # Log the conversation
        log_message = f"User {user_id}:\n{user_message}\nBot:\n{bot_reply}"
        send_log_to_owner(context, log_message)
    except Exception as e:
        error_message = f"Error: {str(e)}"
        await update.message.reply_text(error_message)
        send_log_to_owner(context, f"Error handling message for user {user_id}: {error_message}")

# Command handlers
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
        "/generate_document [type] - Generate a document (e.g., resume, report)\n\n"
        "Type your question or command, and I'll assist!"
    )

# Main function
async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate_image", generate_image))
    application.add_handler(CommandHandler("generate_document", generate_document))

    # Message handler for text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    await application.run_polling()

# Fix for running in an environment with an already running event loop (e.g., Jupyter Notebooks)
if __name__ == "__main__":
    import sys

    if sys.platform.startswith('win') or sys.platform == "linux":
        try:
            asyncio.run(main())
        except RuntimeError:  # This catches the "already running" issue
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
    else:
        asyncio.run(main())
        
