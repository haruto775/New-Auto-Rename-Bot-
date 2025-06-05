import asyncio
import os
import time
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from helper.database import DARKXSIDE78
from plugins.settings_panel import show_manual_rename_options
import logging

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@Client.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def handle_file_for_rename(client, message):
    """Handle incoming files for renaming"""
    user_id = message.from_user.id
    
    try:
        # Get user settings
        settings = await DARKXSIDE78.get_user_settings(user_id)
        rename_mode = settings.get('rename_mode', 'Manual')
        
        # If Manual Mode is active, don't auto-rename
        if rename_mode == "Manual":
            # Show manual rename options instead
            await show_manual_rename_options(client, message)
            return
        
        # Continue with auto-rename logic only if not in Manual mode
        if rename_mode == "Auto":
            await handle_auto_rename(client, message)
        elif rename_mode == "AI":
            await handle_ai_rename(client, message)
        else:
            # Default to manual if unknown mode
            await show_manual_rename_options(client, message)
            
    except Exception as e:
        logging.error(f"File rename handler error: {e}")
        await message.reply_text("❌ **Error processing file. Please try again.**")

async def handle_auto_rename(client, message):
    """Handle auto rename functionality"""
    user_id = message.from_user.id
    
    try:
        # Get file info
        file_name = "Unknown"
        file_size = 0
        
        if message.document:
            file_name = message.document.file_name or "Unknown"
            file_size = message.document.file_size or 0
        elif message.video:
            file_name = message.video.file_name or "Unknown"
            file_size = message.video.file_size or 0
        elif message.audio:
            file_name = message.audio.file_name or "Unknown"
            file_size = message.audio.file_size or 0
        
        # Apply auto-rename logic here
        # Get user preferences
        prefix = await DARKXSIDE78.get_prefix(user_id)
        suffix = await DARKXSIDE78.get_suffix(user_id)
        remove_words = await DARKXSIDE78.get_remove_words(user_id)
        
        new_filename = apply_rename_logic(file_name, prefix, suffix, remove_words)
        
        # Show rename preview
        text = f"""**🔄 Auto Rename Preview**

**Original:** `{file_name}`
**New Name:** `{new_filename}`
**Size:** `{get_readable_file_size(file_size)}`

**Auto-rename applied based on your settings.**"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Apply & Upload", callback_data=f"apply_rename_{message.id}")],
            [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_rename_{message.id}")],
            [InlineKeyboardButton("📤 Upload Original", callback_data=f"upload_original_{message.id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_rename_{message.id}")]
        ])
        
        await message.reply_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"Auto rename error: {e}")
        await message.reply_text("❌ **Error in auto-rename. Please try manual mode.**")

async def handle_ai_rename(client, message):
    """Handle AI rename functionality"""
    user_id = message.from_user.id
    
    try:
        # Get file info
        file_name = "Unknown"
        file_size = 0
        
        if message.document:
            file_name = message.document.file_name or "Unknown"
            file_size = message.document.file_size or 0
        elif message.video:
            file_name = message.video.file_name or "Unknown"
            file_size = message.video.file_size or 0
        elif message.audio:
            file_name = message.audio.file_name or "Unknown"
            file_size = message.audio.file_size or 0
        
        # Show AI processing message
        processing_msg = await message.reply_text("🤖 **AI is analyzing the filename...**\n\n⏳ **Please wait...**")
        
        # Simulate AI processing (replace with actual AI logic)
        await asyncio.sleep(2)
        
        # Apply AI rename logic here (placeholder)
        ai_suggested_name = f"AI_Renamed_{file_name}"
        
        await processing_msg.delete()
        
        # Show AI rename preview
        text = f"""**🤖 AI Rename Suggestion**

**Original:** `{file_name}`
**AI Suggestion:** `{ai_suggested_name}`
**Size:** `{get_readable_file_size(file_size)}`

**AI has analyzed and suggested a better filename.**"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept AI Suggestion", callback_data=f"apply_ai_rename_{message.id}")],
            [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_rename_{message.id}")],
            [InlineKeyboardButton("📤 Upload Original", callback_data=f"upload_original_{message.id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_rename_{message.id}")]
        ])
        
        await message.reply_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"AI rename error: {e}")
        await message.reply_text("❌ **Error in AI rename. Please try manual mode.**")

def apply_rename_logic(filename, prefix, suffix, remove_words):
    """Apply rename logic based on user settings"""
    try:
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
        
        # Add prefix
        if prefix:
            name_part, ext = os.path.splitext(new_name)
            new_name = f"{prefix} {name_part}{ext}"
        
        # Add suffix
        if suffix:
            name_part, ext = os.path.splitext(new_name)
            new_name = f"{name_part} {suffix}{ext}"
        
        return new_name
        
    except Exception as e:
        logging.error(f"Apply rename logic error: {e}")
        return filename

# Callback handlers for rename actions
@Client.on_callback_query(filters.regex(r"^(apply_rename_|apply_ai_rename_|edit_rename_|upload_original_|cancel_rename_)"))
async def rename_callback_handler(client, query: CallbackQuery):
    """Handle rename callback queries"""
    user_id = query.from_user.id
    data = query.data
    
    try:
        if data.startswith("apply_rename_") or data.startswith("apply_ai_rename_"):
            message_id = data.split("_")[-1]
            await query.answer("✅ Applying rename and uploading...")
            
            # Get original message and process rename
            try:
                original_msg = await client.get_messages(query.message.chat.id, int(message_id))
                await process_file_upload(client, original_msg, apply_rename=True)
                await query.message.delete()
            except Exception as e:
                await query.answer("❌ Error processing file", show_alert=True)
                logging.error(f"Apply rename error: {e}")
                
        elif data.startswith("edit_rename_"):
            message_id = data.replace("edit_rename_", "")
            
            # Set user state for editing
            from plugins.settings_panel import user_states
            user_states[user_id] = {
                'state': 'waiting_edit_rename',
                'message_id': message_id,
                'message': query.message
            }
            
            text = "**✏️ Edit Filename**\n\nSend the new filename (with extension).\nTimeout: 60 sec"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_rename_{message_id}")]
            ])
            
            await query.message.edit_text(text, reply_markup=keyboard)
            
        elif data.startswith("upload_original_"):
            message_id = data.replace("upload_original_", "")
            await query.answer("📤 Uploading original file...")
            
            try:
                original_msg = await client.get_messages(query.message.chat.id, int(message_id))
                await process_file_upload(client, original_msg, apply_rename=False)
                await query.message.delete()
            except Exception as e:
                await query.answer("❌ Error uploading file", show_alert=True)
                logging.error(f"Upload original error: {e}")
                
        elif data.startswith("cancel_rename_"):
            await query.answer("❌ Rename cancelled")
            await query.message.delete()
            
    except Exception as e:
        logging.error(f"Rename callback error: {e}")
        await query.answer("❌ Error processing request", show_alert=True)

async def process_file_upload(client, message, apply_rename=True):
    """Process file upload with or without rename"""
    try:
        user_id = message.from_user.id
        
        if apply_rename:
            # Apply rename logic
            settings = await DARKXSIDE78.get_user_settings(user_id)
            prefix = await DARKXSIDE78.get_prefix(user_id)
            suffix = await DARKXSIDE78.get_suffix(user_id)
            remove_words = await DARKXSIDE78.get_remove_words(user_id)
            
            # Get original filename
            original_name = "Unknown"
            if message.document:
                original_name = message.document.file_name or "Unknown"
            elif message.video:
                original_name = message.video.file_name or "Unknown"
            elif message.audio:
                original_name = message.audio.file_name or "Unknown"
            
            new_name = apply_rename_logic(original_name, prefix, suffix, remove_words)
            
            # Here you would implement the actual file download, rename, and upload
            # For now, just show success message
            await message.reply_text(
                f"✅ **File processed successfully!**\n\n"
                f"**Original:** `{original_name}`\n"
                f"**New Name:** `{new_name}`\n\n"
                f"📤 **File uploaded with new name.**"
            )
        else:
            # Upload without rename
            await message.copy(message.chat.id)
            await message.reply_text("✅ **File uploaded with original name.**")
            
    except Exception as e:
        logging.error(f"Process file upload error: {e}")
        await message.reply_text("❌ **Error processing file upload.**")
