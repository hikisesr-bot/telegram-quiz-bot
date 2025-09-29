import logging
import io
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from quiz_generator_logic import generate_zip_file, UNIT_PLANS # Import the generator logic

# --- Configuration ---
# Your provided Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8238741478:AAGcEOXGOg5MwqlskMaobrH7VJN0OJnz_6Q"

# Subject configuration for keyboard (keys must match the logic file)
SUBJECTS = {
    'psychology': 'Psychology',
    'medical_subjects': 'Medical Subjects',
    'business': 'Business',
    'geek_mythology': 'Geek Mythology',
}

LEVELS = {
    'undergraduate': 'Undergraduate',
    'advanced': 'Advanced'
}

# State management for multi-step conversation
# {user_id: {'count': int, 'subjects': [str], 'message_id': int}}
USER_STATE = {} 

# Set up logging for the bot (important for 24/7 monitoring)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message on /start."""
    await update.message.reply_text(
        "👋 Welcome to Dudai's Academy AURA Engine Bot!\n\n"
        "Use the command `/gen [number]` to start generating unique study files (1-30).\n"
        "Example: `/gen 15`"
    )

async def handle_gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /gen command and prompts for subjects."""
    
    try:
        if not context.args:
            await update.message.reply_text("Please specify the number of files (1-30). Example: `/gen 15`")
            return
            
        count = int(context.args[0])
        if not 1 <= count <= 30:
            await update.message.reply_text("The number of files must be between 1 and 30.")
            return

    except ValueError:
        await update.message.reply_text("Invalid input. Please use a number (1-30). Example: `/gen 10`")
        return

    user_id = update.effective_user.id
    
    # 1. Store count and initialize state
    USER_STATE[user_id] = {'count': count, 'subjects': []}

    # 2. Create subject selection keyboard
    keyboard = []
    for key, name in SUBJECTS.items():
        # Callback data format: 'subject_select|{key}'
        keyboard.append([InlineKeyboardButton(name, callback_data=f"subject_select|{key}")])
    
    # Add confirmation button
    keyboard.append([InlineKeyboardButton("✅ Confirm Subjects & Select Level", callback_data="subject_confirm")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 3. Send initial message and store its ID for future edits
    message = await update.message.reply_text(
        f"You wish to generate **{count}** files.\n\n"
        "**Step 1:** Select one or more subjects:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    USER_STATE[user_id]['message_id'] = message.message_id


async def subject_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles subject selection and confirmation."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in USER_STATE:
        await query.edit_message_text("Session expired or command incomplete. Please start over with `/gen [number]`")
        return
        
    data = query.data.split('|')
    current_subjects = USER_STATE[user_id]['subjects']

    if data[0] == 'subject_select':
        # Toggle subject selection
        subject_key = data[1]
        
        if subject_key in current_subjects:
            current_subjects.remove(subject_key)
        else:
            current_subjects.append(subject_key)
            
        # Update button text to reflect selection
        keyboard = []
        for key, name in SUBJECTS.items():
            emoji = "✅" if key in current_subjects else ""
            keyboard.append([InlineKeyboardButton(f"{emoji} {name}", callback_data=f"subject_select|{key}")])
        
        keyboard.append([InlineKeyboardButton("✅ Confirm Subjects & Select Level", callback_data="subject_confirm")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        count = USER_STATE[user_id]['count']
        
        await query.edit_message_text(
            f"You wish to generate **{count}** files.\n\n"
            f"**Step 1:** Select one or more subjects:\n"
            f"Selected: {', '.join([SUBJECTS[s] for s in current_subjects]) or 'None'}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif query.data == 'subject_confirm':
        # Move to Level selection
        if not current_subjects:
            await query.answer("Please select at least one subject before confirming.", show_alert=True)
            return
            
        # Create level selection keyboard
        keyboard = []
        for key, name in LEVELS.items():
            # Callback data format: 'level_select|{key}'
            keyboard.append([InlineKeyboardButton(name, callback_data=f"level_select|{key}")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        selected_names = [SUBJECTS[s] for s in current_subjects]
        
        await query.edit_message_text(
            f"**Subjects Confirmed:** {', '.join(selected_names)}\n\n"
            "**Step 2:** Select the difficulty level:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def level_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles level selection and initiates file generation."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in USER_STATE:
        await query.edit_message_text("Session expired. Please start over with `/gen [number]`")
        return
        
    data = query.data.split('|')
    level = data[1] # 'undergraduate' or 'advanced'
    
    state = USER_STATE[user_id]
    count = state['count']
    selected_subjects = state['subjects']
    
    # 1. Show loading screen / status update
    await query.edit_message_text(
        f"**Step 3: Generating...** ⏳\n\n"
        f"Creating **{count}** unique documents for {', '.join([SUBJECTS[s] for s in selected_subjects])} at the **{LEVELS[level]}** level.\n"
        "Please wait, this can take a few moments for a large batch...",
        parse_mode='Markdown'
    )
    
    try:
        # Fetch user details for the mention/filename
        user = query.from_user
        username = user.username if user.username else None
        
        # --- CORE GENERATION CALL (Runs synchronously in this worker) ---
        zip_bytes = generate_zip_file(count, selected_subjects, level, user.id, username)
        # --- END CORE GENERATION CALL ---
        
        zip_filename = f"DudaisAcademy_Packets_{count}x_{level}.zip"
        
        # 2. Send the file
        zip_file = io.BytesIO(zip_bytes)
        zip_file.name = zip_filename
        
        # Mention the user who requested the file (Feature #6)
        user_mention = f"@{user.username}" if user.username else user.first_name
        caption = (
            f"✅ **Generation Complete!**\n\n"
            f"Your **{count}** unique study packets ({LEVELS[level]} level) are ready, {user_mention}."
        )
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=zip_file,
            caption=caption,
            parse_mode='Markdown'
        )

        # 3. Final confirmation/cleanup message
        await query.edit_message_text(f"Generation successful! The ZIP file has been sent to the chat.")

    except Exception as e:
        logger.error("Error during file generation or sending: %s", e)
        # Send an error message back to the user
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ An unexpected error occurred during file generation. Please try again. Technical error: {str(e)[:100]}..."
        )
        
    finally:
        # 4. Clean up state
        if user_id in USER_STATE:
            del USER_STATE[user_id]


def main() -> None:
    """Start the bot using long-polling (suitable for 24/7 worker process)."""
    
    # The Application builder handles the setup and long-polling (24/7 running)
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", handle_gen_command))
    
    # Register callback handlers for inline keyboard clicks
    application.add_handler(CallbackQueryHandler(subject_callback_handler, pattern="^subject_"))
    application.add_handler(CallbackQueryHandler(level_callback_handler, pattern="^level_select"))


    logger.info("Bot is starting and running 24/7...")
    # This call keeps the worker process running indefinitely
    application.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    # Check if a token is set before running
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("ERROR: Please set the TELEGRAM_BOT_TOKEN in telegram_bot.py.")
    else:
        main()
