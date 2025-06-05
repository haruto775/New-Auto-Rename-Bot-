import asyncio
import logging
import os
import math
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import DARKXSIDE78
from plugins.auto_rename import auto_rename_file

# Store user states for file renaming
user_rename_states = {}

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

async def clear_user_rename_state_after_timeout(user_id: int, timeout: int):
    """Clear user rename state after timeout"""
    await asyncio.sleep(timeout)
    if user_id in user_rename_states:
        del user_rename_states[user_id]

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file_for_rename(client, message: Message):
    """Handle incoming files for renaming"""
    user_id = message.from_user.id
    
    # Get user settings
    settings = await DARKXSIDE78.get_user_settings(user_id)
    rename_mode = settings.get('rename_mode', 'Manual')
    
    # If Manual Mode is active, show direct rename prompt
    if rename_mode == "Manual":
        await show_direct_manual_rename(client, message)
        return
    
    # Try auto-rename for Auto/AI modes
    auto_renamed = await auto_rename_file(client, message)
    
    # If auto-rename failed or not applicable, show manual rename
    if not auto_renamed:
        await show_direct_manual_rename(client, message)

async def show_direct_manual_rename(client, message: Message):
    """Show direct manual rename prompt"""
    user_id = message.from_user.id
    
    # Store file message for later processing
    user_rename_states[user_id] = {
        'original_message': message,
        'state': 'waiting_filename'
    }
    
    # Set timeout
    asyncio.create_task(clear_user_rename_state_after_timeout(user_id, 60))
    
    # Send direct rename prompt
    rename_msg = await message.reply_text(
        "**✏️ Manual Rename Mode ✅**\n\n"
        "Send New file name with extension.\n\n"
        "**Note:** Don't delete your original file."
    )
    
    # Store the rename message for deletion
    user_rename_states[user_id]['rename_message'] = rename_msg

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "help", "settings", "autorename", "metadata", "tutorial", "token", "gentoken", "rename", "analyze", "batchrename"]))
async def handle_manual_rename_input(client, message: Message):
    """Handle manual rename filename input"""
    user_id = message.from_user.id
    
    # Check if user is in rename state
    if user_id not in user_rename_states:
        return
    
    state_info = user_rename_states[user_id]
    if state_info.get('state') != 'waiting_filename':
        return
    
    new_filename = message.text.strip()
    
    try:
        # Delete user's filename message immediately
        try:
            await message.delete()
        except:
            pass
        
        # Delete the rename prompt message
        try:
            rename_msg = state_info.get('rename_message')
            if rename_msg:
                await rename_msg.delete()
        except:
            pass
        
        # Validate filename
        if not new_filename or any(char in new_filename for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            error_msg = await message.reply_text("❌ **Invalid filename!**\n\nFilename contains invalid characters.")
            await asyncio.sleep(3)
            await error_msg.delete()
            # Clear state
            if user_id in user_rename_states:
                del user_rename_states[user_id]
            return
        
        # Get original message
        original_msg = state_info.get('original_message')
        if not original_msg:
            if user_id in user_rename_states:
                del user_rename_states[user_id]
            return
        
        # Start rename and upload process
        success = await rename_and_upload_file_direct(client, original_msg, new_filename)
        
        # Clear state
        if user_id in user_rename_states:
            del user_rename_states[user_id]
        
    except Exception as e:
        logging.error(f"Manual rename input error: {e}")
        # Clear state on error
        if user_id in user_rename_states:
            del user_rename_states[user_id]

async def rename_and_upload_file_direct(client, message: Message, new_filename):
    """Rename and upload file directly without status messages"""
    try:
        user_id = message.from_user.id
        
        # Start downloading immediately
        file_path = await message.download()
        
        # Create new file path with new name
        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_filename)
        
        # Rename file
        os.rename(file_path, new_file_path)
        
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
            
        return True
        
    except Exception as e:
        logging.error(f"Direct rename and upload error: {e}")
        return False

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
                    # Start direct rename
                    success = await rename_and_upload_file_direct(client, replied_msg, new_filename)
                    
                    if success:
                        await message.reply_text(f"✅ **File renamed to:** `{new_filename}`")
                    else:
                        await message.reply_text("❌ **Rename failed!**")
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
            
            await message.reply_text(text)
        else:
            await message.reply_text("❌ **No file found!**\n\nReply to a document, video, or audio file.")
    else:
        await message.reply_text("❌ **No file selected!**\n\nReply to a file with `/analyze`")

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
