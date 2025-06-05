import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import DARKXSIDE78
import os
import re

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message: Message):
    """Auto rename command handler"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Check if Manual Mode is active
    if settings.get('rename_mode') == "Manual":
        await message.reply_text(
            "❌ **Auto-rename disabled**\n\n"
            "Manual Mode is currently active. Auto-rename functionality is disabled.\n\n"
            "To enable auto-rename:\n"
            "• Go to Settings → Rename Mode\n"
            "• Select 'Auto' or 'AI' mode"
        )
        return
    
    # Show auto rename options
    text = f"""**🔄 Auto Rename Configuration**

Current Mode: **{settings.get('rename_mode', 'Manual')}**

Choose auto rename options:"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI Auto Rename", callback_data="autorename_ai")],
        [InlineKeyboardButton("⚡ Quick Auto Rename", callback_data="autorename_quick")],
        [InlineKeyboardButton("⚙️ Configure Settings", callback_data="autorename_settings")],
        [InlineKeyboardButton("❌ Close", callback_data="autorename_close")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^autorename_"))
async def auto_rename_callbacks(client, query):
    """Handle auto rename callbacks"""
    data = query.data
    user_id = query.from_user.id
    
    if data == "autorename_close":
        await query.message.delete()
        
    elif data == "autorename_ai":
        # Set AI mode
        await DARKXSIDE78.update_user_setting(user_id, 'rename_mode', 'AI')
        await query.answer("AI Auto Rename Mode Enabled ✅")
        await query.message.edit_text(
            "✅ **AI Auto Rename Enabled**\n\n"
            "Now send any file and it will be automatically renamed using AI!"
        )
        
    elif data == "autorename_quick":
        # Set Auto mode
        await DARKXSIDE78.update_user_setting(user_id, 'rename_mode', 'Auto')
        await query.answer("Quick Auto Rename Mode Enabled ✅")
        await query.message.edit_text(
            "✅ **Quick Auto Rename Enabled**\n\n"
            "Now send any file and it will be automatically renamed!"
        )
        
    elif data == "autorename_settings":
        # Redirect to settings
        from plugins.settings_panel import show_main_settings
        await show_main_settings(client, query)

async def auto_rename_file(client, message: Message):
    """Auto rename file - only if not in Manual mode"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Check if Manual Mode is active
    if settings.get('rename_mode') == "Manual":
        # Don't show error message here, just return
        return False
    
    rename_mode = settings.get('rename_mode', 'Manual')
    
    if rename_mode == "Auto":
        return await handle_auto_rename(client, message)
    elif rename_mode == "AI":
        return await handle_ai_rename(client, message)
    
    return False

async def handle_auto_rename(client, message: Message):
    """Handle automatic renaming using patterns"""
    try:
        user_id = message.from_user.id
        
        # Get file info
        file_name = None
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name
        elif message.audio:
            file_name = message.audio.file_name
        
        if not file_name:
            return False
        
        # Get user settings
        prefix = await DARKXSIDE78.get_prefix(user_id) or ""
        suffix = await DARKXSIDE78.get_suffix(user_id) or ""
        remove_words = await DARKXSIDE78.get_remove_words(user_id) or ""
        
        # Process filename
        new_name = process_filename_auto(file_name, prefix, suffix, remove_words)
        
        if new_name != file_name:
            # Show auto rename result
            text = f"""**🔄 Auto Rename Applied**

**Original:** `{file_name}`
**Renamed:** `{new_name}`

Processing file..."""
            
            status_msg = await message.reply_text(text)
            
            # Apply the rename and upload
            success = await rename_and_upload_file(client, message, new_name)
            
            if success:
                await status_msg.edit_text(
                    f"✅ **File Auto Renamed & Uploaded**\n\n"
                    f"**New Name:** `{new_name}`"
                )
            else:
                await status_msg.edit_text("❌ **Auto Rename Failed**")
                
            return success
        
        return False
        
    except Exception as e:
        logging.error(f"Auto rename error: {e}")
        return False

async def handle_ai_rename(client, message: Message):
    """Handle AI-powered renaming"""
    try:
        user_id = message.from_user.id
        
        # Get file info
        file_name = None
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name
        elif message.audio:
            file_name = message.audio.file_name
        
        if not file_name:
            return False
        
        # Show AI processing message
        status_msg = await message.reply_text(
            f"🤖 **AI Analyzing File...**\n\n"
            f"Original: `{file_name}`\n\n"
            f"Please wait while AI generates a better filename..."
        )
        
        # Generate AI filename (you can integrate with OpenAI API here)
        ai_name = await generate_ai_filename(file_name)
        
        if ai_name and ai_name != file_name:
            await status_msg.edit_text(
                f"🤖 **AI Rename Suggestion**\n\n"
                f"**Original:** `{file_name}`\n"
                f"**AI Suggested:** `{ai_name}`\n\n"
                f"Processing file..."
            )
            
            # Apply AI rename
            success = await rename_and_upload_file(client, message, ai_name)
            
            if success:
                await status_msg.edit_text(
                    f"✅ **AI Rename Applied Successfully**\n\n"
                    f"**New Name:** `{ai_name}`"
                )
            else:
                await status_msg.edit_text("❌ **AI Rename Failed**")
                
            return success
        else:
            await status_msg.edit_text(
                f"🤖 **AI Analysis Complete**\n\n"
                f"No better filename suggested for:\n`{file_name}`\n\n"
                f"Uploading with original name..."
            )
            return False
        
    except Exception as e:
        logging.error(f"AI rename error: {e}")
        return False

def process_filename_auto(filename, prefix="", suffix="", remove_words=""):
    """Process filename with auto rename rules"""
    try:
        # Split filename and extension
        name, ext = os.path.splitext(filename)
        
        # Apply remove/replace words
        if remove_words:
            name = apply_remove_words(name, remove_words)
        
        # Clean up filename
        name = clean_filename(name)
        
        # Add prefix
        if prefix:
            name = f"{prefix} {name}"
        
        # Add suffix (before extension)
        if suffix:
            name = f"{name} {suffix}"
        
        # Return processed filename
        return f"{name}{ext}"
        
    except Exception as e:
        logging.error(f"Filename processing error: {e}")
        return filename

def apply_remove_words(text, remove_pattern):
    """Apply remove/replace words pattern"""
    try:
        # Split by | for multiple patterns
        patterns = remove_pattern.split('|')
        
        for pattern in patterns:
            if ':' in pattern:
                # Replace pattern (find:replace)
                find, replace = pattern.split(':', 1)
                text = text.replace(find, replace)
            else:
                # Remove pattern
                text = text.replace(pattern, '')
        
        return text
        
    except Exception as e:
        logging.error(f"Remove words error: {e}")
        return text

def clean_filename(filename):
    """Clean filename from unwanted characters"""
    try:
        # Remove extra spaces
        filename = ' '.join(filename.split())
        
        # Remove special characters but keep useful ones
        filename = re.sub(r'[^\w\s\-\.\(\)\[\]]+', '', filename)
        
        # Remove multiple dots except the last one
        parts = filename.split('.')
        if len(parts) > 1:
            name_part = '.'.join(parts[:-1])
            name_part = name_part.replace('.', ' ')
            filename = f"{name_part}.{parts[-1]}"
        
        return filename
        
    except Exception as e:
        logging.error(f"Filename cleaning error: {e}")
        return filename

async def generate_ai_filename(filename):
    """Generate AI filename (integrate with OpenAI API)"""
    try:
        # This is a placeholder - you can integrate with OpenAI API
        # For now, we'll do basic AI-like improvements
        
        name, ext = os.path.splitext(filename)
        
        # Basic AI improvements
        ai_name = name
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'\b\d{3,4}p\b',  # Remove resolution like 720p, 1080p
            r'\bx264\b', r'\bx265\b',  # Remove codec info
            r'\bHEVC\b', r'\bAVC\b',
            r'\bWEBRip\b', r'\bBDRip\b',
            r'\bWEB-DL\b', r'\bBluRay\b',
            r'\[\w+\]',  # Remove [tags]
            r'\(\w+\)',  # Remove (tags)
        ]
        
        for pattern in unwanted_patterns:
            ai_name = re.sub(pattern, '', ai_name, flags=re.IGNORECASE)
        
        # Clean up spaces
        ai_name = ' '.join(ai_name.split())
        
        # Capitalize properly
        ai_name = ai_name.title()
        
        return f"{ai_name}{ext}" if ai_name != name else None
        
    except Exception as e:
        logging.error(f"AI filename generation error: {e}")
        return None

async def rename_and_upload_file(client, message: Message, new_filename):
    """Rename and upload file with new filename"""
    try:
        user_id = message.from_user.id
        
        # Download the file
        status_msg = await message.reply_text("📥 Downloading file...")
        
        # Get file path
        file_path = await message.download()
        
        await status_msg.edit_text("🔄 Renaming file...")
        
        # Create new file path with new name
        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_filename)
        
        # Rename file
        os.rename(file_path, new_file_path)
        
        await status_msg.edit_text("📤 Uploading renamed file...")
        
        # Get user settings for upload
        settings = await DARKXSIDE78.get_user_settings(user_id)
        thumbnail = await DARKXSIDE78.get_thumbnail(user_id)
        caption = await DARKXSIDE78.get_caption(user_id)
        
        # Prepare caption
        final_caption = caption or new_filename
        
        # Upload based on file type and settings
        if message.document:
            if settings.get('send_as') == 'media' and new_filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                await client.send_video(
                    chat_id=message.chat.id,
                    video=new_file_path,
                    caption=final_caption,
                    thumb=thumbnail,
                    supports_streaming=True
                )
            else:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=new_file_path,
                    caption=final_caption,
                    thumb=thumbnail
                )
        elif message.video:
            await client.send_video(
                chat_id=message.chat.id,
                video=new_file_path,
                caption=final_caption,
                thumb=thumbnail,
                supports_streaming=True
            )
        elif message.audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=new_file_path,
                caption=final_caption,
                thumb=thumbnail
            )
        
        # Clean up
        try:
            os.remove(new_file_path)
        except:
            pass
            
        await status_msg.delete()
        return True
        
    except Exception as e:
        logging.error(f"Rename and upload error: {e}")
        return False

async def upload_file_without_rename(client, message: Message):
    """Upload file without renaming"""
    try:
        user_id = message.from_user.id
        
        # Get user settings
        settings = await DARKXSIDE78.get_user_settings(user_id)
        thumbnail = await DARKXSIDE78.get_thumbnail(user_id)
        caption = await DARKXSIDE78.get_caption(user_id)
        
        # Get original filename
        original_name = None
        if message.document:
            original_name = message.document.file_name
        elif message.video:
            original_name = message.video.file_name
        elif message.audio:
            original_name = message.audio.file_name
        
        final_caption = caption or original_name or "File"
        
        status_msg = await message.reply_text("📤 Uploading file as is...")
        
        # Upload based on file type
        if message.document:
            if settings.get('send_as') == 'media' and original_name and original_name.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                await client.send_video(
                    chat_id=message.chat.id,
                    video=message.document.file_id,
                    caption=final_caption,
                    thumb=thumbnail,
                    supports_streaming=True
                )
            else:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=message.document.file_id,
                    caption=final_caption,
                    thumb=thumbnail
                )
        elif message.video:
            await client.send_video(
                chat_id=message.chat.id,
                video=message.video.file_id,
                caption=final_caption,
                thumb=thumbnail,
                supports_streaming=True
            )
        elif message.audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=message.audio.file_id,
                caption=final_caption,
                thumb=thumbnail
            )
        
        await status_msg.delete()
        return True
        
    except Exception as e:
        logging.error(f"Upload without rename error: {e}")
        return False
