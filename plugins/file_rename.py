import asyncio
import logging
import os
import math
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import DARKXSIDE78
from plugins.auto_rename import auto_rename_file, show_manual_rename_options

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file_for_rename(client, message: Message):
    """Handle incoming files for renaming"""
    user_id = message.from_user.id
    
    # Get user settings
    settings = await DARKXSIDE78.get_user_settings(user_id)
    rename_mode = settings.get('rename_mode', 'Manual')
    
    # If Manual Mode is active, show manual options
    if rename_mode == "Manual":
        await show_manual_rename_options(client, message)
        return
    
    # Try auto-rename for Auto/AI modes
    auto_renamed = await auto_rename_file(client, message)
    
    # If auto-rename failed or not applicable, show manual options
    if not auto_renamed:
        await show_manual_rename_options(client, message)

@Client.on_message(filters.private & filters.command("rename"))
async def manual_rename_command(client, message: Message):
    """Manual rename command"""
    user_id = message.from_user.id
    
    if message.reply_to_message:
        replied_msg = message.reply_to_message
        
        if replied_msg.document or replied_msg.video or replied_msg.audio:
            # Extract new filename from command
            command_parts = message.text.split(' ', 1)
            if len(command_parts) > 1:
                new_filename = command_parts[1].strip()
                
                # Validate filename
                if new_filename and not any(char in new_filename for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
                    # Show confirmation
                    original_name = get_original_filename(replied_msg)
                    
                    text = f"""**✏️ Manual Rename Confirmation**

**Original:** `{original_name}`
**New Name:** `{new_filename}`

Confirm rename?"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_rename_{replied_msg.id}_{new_filename}")],
                        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_rename")]
                    ])
                    
                    await message.reply_text(text, reply_markup=keyboard)
                else:
                    await message.reply_text("❌ **Invalid filename!**\n\nFilename contains invalid characters.")
            else:
                await message.reply_text(
                    "❌ **No filename provided!**\n\n"
                    "Usage: `/rename new_filename.ext`\n"
                    "Reply to a file with this command."
                )
        else:
            await message.reply_text("❌ **No file found!**\n\nReply to a document, video, or audio file.")
    else:
        await message.reply_text(
            "❌ **No file selected!**\n\n"
            "Reply to a file with `/rename new_filename.ext`"
        )

def get_original_filename(message: Message):
    """Get original filename from message"""
    if message.document:
        return message.document.file_name or "Unknown"
    elif message.video:
        return message.video.file_name or "Unknown"
    elif message.audio:
        return message.audio.file_name or "Unknown"
    return "Unknown"

@Client.on_callback_query(filters.regex(r"^confirm_rename_"))
async def confirm_rename_callback(client, query):
    """Handle rename confirmation"""
    try:
        data_parts = query.data.split('_', 3)
        message_id = int(data_parts[2])
        new_filename = data_parts[3] if len(data_parts) > 3 else "renamed_file"
        
        # Get original message
        original_msg = await client.get_messages(query.message.chat.id, message_id)
        
        # Process rename
        from plugins.auto_rename import rename_and_upload_file
        success = await rename_and_upload_file(client, original_msg, new_filename)
        
        if success:
            await query.message.edit_text(
                f"✅ **File Renamed Successfully!**\n\n"
                f"**New Name:** `{new_filename}`"
            )
        else:
            await query.message.edit_text("❌ **Rename Failed!**\n\nPlease try again.")
            
    except Exception as e:
        logging.error(f"Confirm rename error: {e}")
        await query.answer("❌ Error processing rename", show_alert=True)

@Client.on_callback_query(filters.regex(r"^cancel_rename"))
async def cancel_rename_callback(client, query):
    """Handle rename cancellation"""
    await query.message.edit_text("❌ **Rename Cancelled**")

# File analysis and suggestions
async def analyze_filename(filename):
    """Analyze filename and provide suggestions"""
    suggestions = []
    
    # Check for common issues
    if len(filename) > 100:
        suggestions.append("Filename is too long")
    
    if '..' in filename:
        suggestions.append("Contains double dots")
    
    if filename.count('.') > 1:
        suggestions.append("Multiple extensions detected")
    
    # Check for unwanted patterns
    unwanted_patterns = ['720p', '1080p', 'x264', 'x265', 'HEVC', 'WEBRip', 'BDRip']
    for pattern in unwanted_patterns:
        if pattern.lower() in filename.lower():
            suggestions.append(f"Contains '{pattern}' - consider removing")
    
    return suggestions

@Client.on_message(filters.private & filters.command("analyze"))
async def analyze_file_command(client, message: Message):
    """Analyze file and provide rename suggestions"""
    if message.reply_to_message:
        replied_msg = message.reply_to_message
        
        if replied_msg.document or replied_msg.video or replied_msg.audio:
            original_name = get_original_filename(replied_msg)
            file_size = 0
            
            if replied_msg.document:
                file_size = replied_msg.document.file_size or 0
            elif replied_msg.video:
                file_size = replied_msg.video.file_size or 0
            elif replied_msg.audio:
                file_size = replied_msg.audio.file_size or 0
            
            # Analyze filename
            suggestions = await analyze_filename(original_name)
            
            text = f"""**📊 File Analysis**

**File:** `{original_name}`
**Size:** `{get_readable_file_size(file_size)}`

**Analysis Results:**"""
            
            if suggestions:
                text += "\n\n⚠️ **Issues Found:**\n"
                for i, suggestion in enumerate(suggestions, 1):
                    text += f"{i}. {suggestion}\n"
            else:
                text += "\n\n✅ **No issues found!**\nFilename looks good."
            
            # Add action buttons
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 AI Suggest", callback_data=f"ai_suggest_{replied_msg.id}")],
                [InlineKeyboardButton("✏️ Manual Rename", callback_data=f"manual_rename_{replied_msg.id}")],
                [InlineKeyboardButton("📤 Upload As Is", callback_data=f"upload_as_is_{replied_msg.id}")]
            ])
            
            await message.reply_text(text, reply_markup=keyboard)
        else:
            await message.reply_text("❌ **No file found!**\n\nReply to a document, video, or audio file.")
    else:
        await message.reply_text("❌ **No file selected!**\n\nReply to a file with `/analyze`")

@Client.on_callback_query(filters.regex(r"^ai_suggest_"))
async def ai_suggest_callback(client, query):
    """Handle AI suggestion request"""
    try:
        message_id = int(query.data.split('_')[2])
        original_msg = await client.get_messages(query.message.chat.id, message_id)
        
        # Get AI suggestion
        from plugins.auto_rename import generate_ai_filename
        original_name = get_original_filename(original_msg)
        ai_suggestion = await generate_ai_filename(original_name)
        
        if ai_suggestion and ai_suggestion != original_name:
            text = f"""🤖 **AI Suggestion**

**Original:** `{original_name}`
**AI Suggested:** `{ai_suggestion}`

Apply this suggestion?"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Apply", callback_data=f"confirm_rename_{message_id}_{ai_suggestion}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_rename")]
            ])
            
            await query.message.edit_text(text, reply_markup=keyboard)
        else:
            await query.message.edit_text(
                f"🤖 **AI Analysis Complete**\n\n"
                f"No improvements suggested for:\n`{original_name}`"
            )
            
    except Exception as e:
        logging.error(f"AI suggest error: {e}")
        await query.answer("❌ Error generating AI suggestion", show_alert=True)

# Batch rename functionality
@Client.on_message(filters.private & filters.command("batchrename"))
async def batch_rename_command(client, message: Message):
    """Batch rename command for multiple files"""
    await message.reply_text(
        "🔄 **Batch Rename Mode**\n\n"
        "Send multiple files and they will be processed according to your rename settings.\n\n"
        "Current Mode: Auto processing based on your settings"
    )

# File type specific handlers
@Client.on_message(filters.private & filters.document & filters.regex(r'\.(mp4|avi|mkv|mov|wmv|flv|webm)$'))
async def handle_video_file(client, message: Message):
    """Handle video files specifically"""
    await handle_file_for_rename(client, message)

@Client.on_message(filters.private & filters.document & filters.regex(r'\.(mp3|wav|flac|aac|ogg|m4a)$'))
async def handle_audio_file(client, message: Message):
    """Handle audio files specifically"""
    await handle_file_for_rename(client, message)

@Client.on_message(filters.private & filters.document & filters.regex(r'\.(zip|rar|7z|tar|gz)$'))
async def handle_archive_file(client, message: Message):
    """Handle archive files specifically"""
    await handle_file_for_rename(client, message)
