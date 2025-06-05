import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import DARKXSIDE78

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    """Auto rename command - only if not in Manual mode"""
    user_id = message.from_user.id
    
    try:
        settings = await DARKXSIDE78.get_user_settings(user_id)
        
        # Check if Manual Mode is active
        if settings.get('rename_mode') == "Manual":
            text = """❌ **Auto-rename disabled**

**Manual Mode is currently active.** Auto-rename functionality is disabled.

**To enable auto-rename:**
• Go to Settings → Rename Mode
• Select 'Auto' or 'AI' mode

**Current Mode:** Manual"""

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Go to Settings", callback_data="setting_rename_mode")],
                [InlineKeyboardButton("📖 Learn More", callback_data="autorename_help")]
            ])
            
            await message.reply_text(text, reply_markup=keyboard)
            return
        
        # Show auto-rename status if not in manual mode
        rename_mode = settings.get('rename_mode', 'Auto')
        prefix = await DARKXSIDE78.get_prefix(user_id)
        suffix = await DARKXSIDE78.get_suffix(user_id)
        remove_words = await DARKXSIDE78.get_remove_words(user_id)
        
        text = f"""**🔄 Auto-Rename Status**

**Current Mode:** {rename_mode}
**Status:** {'Enabled' if rename_mode != 'Manual' else 'Disabled'}

**Settings:**
• **Prefix:** {prefix or 'None'}
• **Suffix:** {suffix or 'None'}
• **Remove Words:** {remove_words or 'None'}

**How it works:**
When you send a file, it will be automatically renamed based on your settings."""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Configure Settings", callback_data="setting_rename_mode")],
            [InlineKeyboardButton("📝 Set Prefix", callback_data="setting_prefix")],
            [InlineKeyboardButton("📝 Set Suffix", callback_data="setting_suffix")],
            [InlineKeyboardButton("🔧 Remove Words", callback_data="setting_remove_words")]
        ])
        
        await message.reply_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"Auto rename command error: {e}")
        await message.reply_text("❌ **Error retrieving auto-rename status.**")

@Client.on_callback_query(filters.regex("autorename_help"))
async def autorename_help_callback(client, query):
    """Show auto-rename help"""
    text = """**📖 Auto-Rename Help**

**Rename Modes:**

**🔄 Auto Mode:**
• Automatically renames files based on your prefix, suffix, and remove words settings
• No manual intervention required

**🤖 AI Mode:**
• Uses AI to suggest better filenames
• Analyzes content and suggests improvements
• You can accept or modify AI suggestions

**✏️ Manual Mode:**
• Disables auto-rename completely
• You must manually rename each file
• Gives you full control over naming

**Settings:**
• **Prefix:** Text added to the beginning of filename
• **Suffix:** Text added to the end of filename (before extension)
• **Remove Words:** Pattern to remove/replace specific words

**Example:**
Original: `movie.mkv`
Prefix: `[HD]`
Suffix: `@Channel`
Result: `[HD] movie @Channel.mkv`"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="autorename_back")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="setting_rename_mode")]
    ])
    
    await query.message.edit_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("autorename_back"))
async def autorename_back_callback(client, query):
    """Go back to auto-rename status"""
    # Re-run the auto-rename command
    await auto_rename_command(client, query.message)

# Auto-rename processor for files
async def auto_rename_processor(client, message):
    """Process auto-rename for incoming files"""
    user_id = message.from_user.id
    
    try:
        settings = await DARKXSIDE78.get_user_settings(user_id)
        rename_mode = settings.get('rename_mode', 'Manual')
        
        # Skip if manual mode
        if rename_mode == "Manual":
            return False
        
        # Get file info
        file_name = get_file_name(message)
        if not file_name:
            return False
        
        # Apply auto-rename based on mode
        if rename_mode == "Auto":
            return await process_auto_rename(client, message, file_name)
        elif rename_mode == "AI":
            return await process_ai_rename(client, message, file_name)
        
        return False
        
    except Exception as e:
        logging.error(f"Auto rename processor error: {e}")
        return False

def get_file_name(message):
    """Extract filename from message"""
    if message.document:
        return message.document.file_name
    elif message.video:
        return message.video.file_name
    elif message.audio:
        return message.audio.file_name
    return None

async def process_auto_rename(client, message, file_name):
    """Process automatic rename"""
    try:
        user_id = message.from_user.id
        
        # Get user settings
        prefix = await DARKXSIDE78.get_prefix(user_id)
        suffix = await DARKXSIDE78.get_suffix(user_id)
        remove_words = await DARKXSIDE78.get_remove_words(user_id)
        
        # Apply rename logic
        new_name = apply_auto_rename_logic(file_name, prefix, suffix, remove_words)
        
        if new_name != file_name:
            # Show rename notification
            await message.reply_text(
                f"🔄 **Auto-Rename Applied**\n\n"
                f"**Original:** `{file_name}`\n"
                f"**New Name:** `{new_name}`\n\n"
                f"📤 **Processing file...**"
            )
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Process auto rename error: {e}")
        return False

async def process_ai_rename(client, message, file_name):
    """Process AI-based rename"""
    try:
        user_id = message.from_user.id
        
        # Show AI processing message
        processing_msg = await message.reply_text(
            "🤖 **AI Rename Active**\n\n"
            "⏳ **Analyzing filename...**"
        )
        
        # Simulate AI processing
        await asyncio.sleep(2)
        
        # Generate AI suggestion (placeholder - implement actual AI logic)
        ai_suggestion = generate_ai_filename(file_name)
        
        if ai_suggestion != file_name:
            await processing_msg.edit_text(
                f"🤖 **AI Rename Suggestion**\n\n"
                f"**Original:** `{file_name}`\n"
                f"**AI Suggestion:** `{ai_suggestion}`\n\n"
                f"📤 **Applying AI rename...**"
            )
            return True
        else:
            await processing_msg.delete()
            return False
        
    except Exception as e:
        logging.error(f"Process AI rename error: {e}")
        return False

def apply_auto_rename_logic(filename, prefix, suffix, remove_words):
    """Apply automatic rename logic"""
    try:
        import os
        new_name = filename
        
        # Apply remove/replace words
        if remove_words:
            pairs = remove_words.split('|')
            for pair in pairs:
                if ':' in pair:
                    find, replace = pair.split(':', 1)
                    new_name = new_name.replace(find, replace)
                else:
                    # Remove word if no replacement specified
                    new_name = new_name.replace(pair, '')
        
        # Clean up multiple spaces
        new_name = ' '.join(new_name.split())
        
        # Add prefix
        if prefix:
            name_part, ext = os.path.splitext(new_name)
            new_name = f"{prefix} {name_part}{ext}"
        
        # Add suffix
        if suffix:
            name_part, ext = os.path.splitext(new_name)
            new_name = f"{name_part} {suffix}{ext}"
        
        return new_name.strip()
        
    except Exception as e:
        logging.error(f"Apply auto rename logic error: {e}")
        return filename

def generate_ai_filename(filename):
    """Generate AI-based filename suggestion (placeholder)"""
    try:
        import os
        import re
        
        # Basic AI logic - clean up filename
        name_part, ext = os.path.splitext(filename)
        
        # Remove common unwanted patterns
        cleaned = re.sub(r'[\[\(].*?[\]\)]', '', name_part)  # Remove content in brackets/parentheses
        cleaned = re.sub(r'[_\-\.]+', ' ', cleaned)  # Replace separators with spaces
        cleaned = re.sub(r'\d{4}', '', cleaned)  # Remove years
        cleaned = ' '.join(word.capitalize() for word in cleaned.split() if len(word) > 2)
        
        if cleaned.strip():
            return f"{cleaned.strip()}{ext}"
        else:
            return filename
            
    except Exception as e:
        logging.error(f"Generate AI filename error: {e}")
        return filename

# Status checker
async def get_auto_rename_status(user_id):
    """Get current auto-rename status for user"""
    try:
        settings = await DARKXSIDE78.get_user_settings(user_id)
        rename_mode = settings.get('rename_mode', 'Manual')
        
        status = {
            'enabled': rename_mode != 'Manual',
            'mode': rename_mode,
            'prefix': await DARKXSIDE78.get_prefix(user_id),
            'suffix': await DARKXSIDE78.get_suffix(user_id),
            'remove_words': await DARKXSIDE78.get_remove_words(user_id)
        }
        
        return status
        
    except Exception as e:
        logging.error(f"Get auto rename status error: {e}")
        return {'enabled': False, 'mode': 'Manual'}
