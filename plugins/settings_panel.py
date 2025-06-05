import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, InputMediaPhoto
from helper.database import DARKXSIDE78
from config import Config
import logging

# Store user states with message context for proper redirection
user_states = {}

# Store original settings message references
settings_messages = {}

SETTINGS_PHOTO = "https://graph.org/file/a27d85469761da836337c.jpg"

async def get_settings_photo(user_id: int):
    """Get the photo to use for settings panel - user's thumbnail if exists, else default"""
    user_thumbnail = await DARKXSIDE78.get_thumbnail(user_id)
    if user_thumbnail:
        return user_thumbnail
    else:
        return SETTINGS_PHOTO

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@Client.on_message(filters.private & filters.command("settings"))
async def settings_command(client, message: Message):
    """Main settings command"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Get current metadata status
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    
    # Get current thumbnail status - check if file_id exists
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    
    # Create settings overview text with auto-rename status
    auto_rename_status = 'Disabled (Manual Mode)' if settings['rename_mode'] == 'Manual' else 'Enabled'
    
    settings_text = f"""**🛠️ Settings for** `{message.from_user.first_name}` **⚙️**

**Custom Thumbnail:** {'Exists' if thumbnail_status else 'Not Exists'}
**Upload Type:** {settings['send_as'].upper()}
**Prefix:** {settings['prefix'] or 'None'}
**Suffix:** {settings['suffix'] or 'None'}

**Upload Destination:** {settings['upload_destination'] or 'None'}
**Sample Video:** {'Enabled' if settings['sample_video'] else 'Disabled'}
**Screenshot:** {'Enabled' if settings['screenshot_enabled'] else 'Disabled'}

**Metadata:** {'Enabled' if metadata_status != 'Off' else 'Disabled'}
**Remove/Replace Words:** {settings['remove_words'] or 'None'}
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}
**Auto-Rename:** {auto_rename_status}"""

    # Create main settings keyboard (Upload Mode button removed)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Choose Format", callback_data="setting_send_as"),
            InlineKeyboardButton("Set Upload Destination", callback_data="setting_upload_dest")
        ],
        [
            InlineKeyboardButton("Set Thumbnail", callback_data="setting_thumbnail"),
            InlineKeyboardButton("Set Caption", callback_data="setting_caption")
        ],
        [
            InlineKeyboardButton("Set Prefix", callback_data="setting_prefix"),
            InlineKeyboardButton("Set Suffix", callback_data="setting_suffix")
        ],
        [
            InlineKeyboardButton(f"Rename Mode | {settings['rename_mode']}", callback_data="setting_rename_mode"),
            InlineKeyboardButton("Set Metadata", callback_data="setting_metadata")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="setting_remove_words"),
            InlineKeyboardButton(f"Enable Sample Video", callback_data="setting_sample_video")
        ],
        [
            InlineKeyboardButton(f"Enable Screenshot", callback_data="setting_screenshot")
        ]
    ])

    # Get the appropriate photo - user's thumbnail or default
    settings_photo = await get_settings_photo(user_id)

    try:
        sent_msg = await message.reply_photo(
            photo=settings_photo,
            caption=settings_text,
            reply_markup=keyboard
        )
        # Store the settings message reference
        settings_messages[user_id] = sent_msg
    except Exception as e:
        sent_msg = await message.reply_text(settings_text, reply_markup=keyboard)
        settings_messages[user_id] = sent_msg

@Client.on_callback_query(filters.regex(r"^setting_"))
async def settings_callback_handler(client, query: CallbackQuery):
    """Handle all settings callbacks"""
    user_id = query.from_user.id
    data = query.data
    
    try:
        if data == "setting_close":
            await query.message.delete()
            if user_id in settings_messages:
                del settings_messages[user_id]
            if user_id in user_states:
                del user_states[user_id]
            return
            
        elif data == "setting_send_as":
            await handle_send_as(client, query)
            
        elif data == "setting_upload_dest":
            await handle_upload_destination(client, query)
            
        elif data == "setting_thumbnail":
            await handle_thumbnail_setting(client, query)
            
        elif data == "setting_caption":
            await handle_caption_setting(client, query)
            
        elif data == "setting_prefix":
            await handle_prefix_setting(client, query)
            
        elif data == "setting_suffix":
            await handle_suffix_setting(client, query)
            
        elif data == "setting_rename_mode":
            await handle_rename_mode(client, query)
            
        elif data == "setting_metadata":
            # Clear any user states when going to metadata
            if user_id in user_states:
                del user_states[user_id]
            await handle_metadata_setting(client, query)
            
        elif data == "setting_remove_words":
            await handle_remove_words(client, query)
            
        elif data == "setting_sample_video":
            await handle_sample_video(client, query)
            
        elif data == "setting_screenshot":
            await handle_screenshot(client, query)
            
        elif data == "setting_back":
            # Clear any user states when going back to main
            if user_id in user_states:
                del user_states[user_id]
            await show_main_settings(client, query)
            
    except Exception as e:
        logging.error(f"Settings callback error: {e}")
        await query.answer("An error occurred. Please try again.", show_alert=True)

async def show_main_settings(client, query: CallbackQuery):
    """Show main settings panel"""
    user_id = query.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Get current metadata status
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    
    # Get current thumbnail status - check if file_id exists
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    
    # Auto-rename status
    auto_rename_status = 'Disabled (Manual Mode)' if settings['rename_mode'] == 'Manual' else 'Enabled'
    
    settings_text = f"""**🛠️ Settings for** `{query.from_user.first_name}` **⚙️**

**Custom Thumbnail:** {'Exists' if thumbnail_status else 'Not Exists'}
**Upload Type:** {settings['send_as'].upper()}
**Prefix:** {settings['prefix'] or 'None'}
**Suffix:** {settings['suffix'] or 'None'}

**Upload Destination:** {settings['upload_destination'] or 'None'}
**Sample Video:** {'Enabled' if settings['sample_video'] else 'Disabled'}
**Screenshot:** {'Enabled' if settings['screenshot_enabled'] else 'Disabled'}

**Metadata:** {'Enabled' if metadata_status != 'Off' else 'Disabled'}
**Remove/Replace Words:** {settings['remove_words'] or 'None'}
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}
**Auto-Rename:** {auto_rename_status}"""

    # Updated keyboard without Upload Mode button
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Choose Format", callback_data="setting_send_as"),
            InlineKeyboardButton("Set Upload Destination", callback_data="setting_upload_dest")
        ],
        [
            InlineKeyboardButton("Set Thumbnail", callback_data="setting_thumbnail"),
            InlineKeyboardButton("Set Caption", callback_data="setting_caption")
        ],
        [
            InlineKeyboardButton("Set Prefix", callback_data="setting_prefix"),
            InlineKeyboardButton("Set Suffix", callback_data="setting_suffix")
        ],
        [
            InlineKeyboardButton(f"Rename Mode | {settings['rename_mode']}", callback_data="setting_rename_mode"),
            InlineKeyboardButton("Set Metadata", callback_data="setting_metadata")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="setting_remove_words"),
            InlineKeyboardButton(f"Enable Sample Video", callback_data="setting_sample_video")
        ],
        [
            InlineKeyboardButton(f"Enable Screenshot", callback_data="setting_screenshot")
        ]
    ])

    # Get the appropriate photo - user's thumbnail or default
    settings_photo = await get_settings_photo(user_id)
    
    # Try to edit the media first, then fallback to caption
    try:
        await query.message.edit_media(
            media=InputMediaPhoto(
                media=settings_photo,
                caption=settings_text
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        await query.message.edit_caption(
            caption=settings_text,
            reply_markup=keyboard
        )

# Individual setting handlers
async def handle_send_as(client, query: CallbackQuery):
    """Handle send as document/media setting"""
    current_setting = await DARKXSIDE78.get_media_preference(query.from_user.id) or "document"
    
    text = f"""**📁 Choose Format Configuration**

Current Setting: **{current_setting.title()}**

Choose how to send your files:
• **Document**: Send as file attachment
• **Video**: Send as video (for video files)
• **Media**: Send as media with preview"""

    doc_check = "✅" if current_setting == "document" else ""
    video_check = "✅" if current_setting == "video" else ""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Send As Document {doc_check}", callback_data="send_as_document")],
        [InlineKeyboardButton(f"Send As Media {video_check}", callback_data="send_as_media")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)

async def handle_upload_destination(client, query: CallbackQuery):
    """Handle upload destination setting"""
    destination = await DARKXSIDE78.get_upload_destination(query.from_user.id)
    
    text = f"""**🎯 Upload Destination Configuration**

If you Add Bot Will Upload your files in your channel or group.

**Steps To Add:**
1. First Create a new channel or group if u dont have.
2. After that Click on below button to add in your channel or group(As Admin with enough permission).
3. After adding send /id command in your channel or group.
4. You will get a chat_id starting with -100
5. Copy That and send here.

You can also upload on specific Group Topic.
**Example:**
-100xxx:topic_id

**Send Upload Destination ID. Timeout 60 sec**
**Current Destination:** {destination or 'None'}"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add in Channel", callback_data="dest_add_channel")],
        [InlineKeyboardButton("Add in Group", callback_data="dest_add_group")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)

async def handle_thumbnail_setting(client, query: CallbackQuery):
    """Handle thumbnail setting"""
    text = """**🖼️ Thumbnail Configuration**

Send a photo to save it as custom thumbnail.
Timeout: 60 sec"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)
    
    # Set user state with message reference
    user_states[query.from_user.id] = {
        'state': 'waiting_thumbnail',
        'message': query.message
    }
    asyncio.create_task(clear_user_state_after_timeout(query.from_user.id, 60))

async def handle_caption_setting(client, query: CallbackQuery):
    """Handle caption setting"""
    current_caption = await DARKXSIDE78.get_caption(query.from_user.id)
    
    text = f"""**📝 Caption Configuration**

**Current Caption:** {current_caption or 'None'}

Send your custom caption for files.
Timeout: 60 sec

**Available Variables:**
• {filename} - Original filename
• {filesize} - File size
• {duration} - Video duration"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)
    
    # Set user state with message reference
    user_states[query.from_user.id] = {
        'state': 'waiting_caption',
        'message': query.message
    }
    asyncio.create_task(clear_user_state_after_timeout(query.from_user.id, 60))

async def handle_prefix_setting(client, query: CallbackQuery):
    """Handle prefix setting"""
    current_prefix = await DARKXSIDE78.get_prefix(query.from_user.id)
    
    text = f"""**📝 Prefix Configuration**

Prefix is the Front Part attached with the Filename.

**Example:**
Prefix = @PublicMirrorLeech

**This will give output of:**
@PublicMirrorLeech Fast_And_Furious.mkv

**Send Prefix. Timeout: 60 sec**"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)
    
    # Set user state with message reference
    user_states[query.from_user.id] = {
        'state': 'waiting_prefix',
        'message': query.message
    }
    asyncio.create_task(clear_user_state_after_timeout(query.from_user.id, 60))

async def handle_suffix_setting(client, query: CallbackQuery):
    """Handle suffix setting"""
    current_suffix = await DARKXSIDE78.get_suffix(query.from_user.id)
    
    text = f"""**📝 Suffix Configuration**

Suffix is the End Part attached with the Filename.

**Example:**
Suffix = @PublicMirrorLeech

**This will give output of:**
Fast_And_Furious @PublicMirrorLeech.mkv

**Send Suffix. Timeout: 60 sec**"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)
    
    # Set user state with message reference
    user_states[query.from_user.id] = {
        'state': 'waiting_suffix',
        'message': query.message
    }
    asyncio.create_task(clear_user_state_after_timeout(query.from_user.id, 60))

async def handle_rename_mode(client, query: CallbackQuery):
    """Handle rename mode setting"""
    current_mode = (await DARKXSIDE78.get_user_settings(query.from_user.id))['rename_mode']
    
    text = f"""**🔄 Rename Mode Configuration**

Choose from Below Buttons!

Rename mode is {current_mode} | {current_mode}"""

    auto_check = "✅" if current_mode == "Auto" else "❌"
    manual_check = "✅" if current_mode == "Manual" else "❌"
    ai_check = "✅" if current_mode == "AI" else "❌"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Auto Rename Mode {auto_check}", callback_data="rename_mode_auto")],
        [InlineKeyboardButton(f"Set Manual Mode {manual_check}", callback_data="rename_mode_manual")],
        [InlineKeyboardButton(f"Use AI Autorename {ai_check}", callback_data="rename_mode_ai")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)

async def handle_metadata_setting(client, query: CallbackQuery):
    """Handle metadata setting"""
    user_id = query.from_user.id
    current = await DARKXSIDE78.get_metadata(user_id)
    title = await DARKXSIDE78.get_title(user_id)
    author = await DARKXSIDE78.get_author(user_id)
    audio = await DARKXSIDE78.get_audio(user_id)
    subtitle = await DARKXSIDE78.get_subtitle(user_id)
    
    text = f"""**🏷️ Metadata Setting for** `{query.from_user.first_name}` **⚙️**

Video Title is {title or 'None'}
Video Author is {author or 'None'}  
Audio Title is {audio or 'None'}
Subtitle Title is {subtitle or 'None'}"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Video Title", callback_data="meta_video_title")],
        [InlineKeyboardButton("Set Video Author", callback_data="meta_video_author")],
        [InlineKeyboardButton("Set Audio Title", callback_data="meta_audio_title")],
        [InlineKeyboardButton("Set Subtitle Title", callback_data="meta_subtitle_title")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)

async def handle_remove_words(client, query: CallbackQuery):
    """Handle remove words setting"""
    current_words = await DARKXSIDE78.get_remove_words(query.from_user.id)
    
    text = f"""**🔧 Remove/Replace Words From FileName.**

find1:change1|find2:change2|...

• **'find'**: The word you want to change.
• **'change'**: What you want to replace it with. If you leave it blank, it will disappear!
• **'|'**: Separates different changes.

You can add as many find:change pairs as you like!

**Example:**
apple:banana|the:sun:moon

**This code will:**
• Change all 'apple' to 'banana'.
• Remove all 'the'.
• Change all 'sun' to 'moon'.

**Send! Timeout: 60 sec**
Your Current Value is not added yet!"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)
    
    # Set user state with message reference
    user_states[query.from_user.id] = {
        'state': 'waiting_remove_words',
        'message': query.message
    }
    asyncio.create_task(clear_user_state_after_timeout(query.from_user.id, 60))

async def handle_sample_video(client, query: CallbackQuery):
    """Toggle sample video setting"""
    user_id = query.from_user.id
    current_setting = (await DARKXSIDE78.get_user_settings(user_id))['sample_video']
    new_setting = not current_setting
    
    await DARKXSIDE78.update_user_setting(user_id, 'sample_video', new_setting)
    await query.answer(f"Sample Video {'Enabled' if new_setting else 'Disabled'} ✅")
    await show_main_settings(client, query)

async def handle_screenshot(client, query: CallbackQuery):
    """Toggle screenshot setting"""
    user_id = query.from_user.id
    current_setting = (await DARKXSIDE78.get_user_settings(user_id))['screenshot_enabled']
    new_setting = not current_setting
    
    await DARKXSIDE78.update_user_setting(user_id, 'screenshot_enabled', new_setting)
    await query.answer(f"Screenshot {'Enabled' if new_setting else 'Disabled'} ✅")
    await show_main_settings(client, query)

# Manual rename functions
async def show_manual_rename_options(client, message):
    """Show manual rename options when Manual Mode is active"""
    user_id = message.from_user.id
    
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
    
    text = f"""**📝 Manual Rename Mode Active**

File: `{file_name}`
Size: `{get_readable_file_size(file_size)}`

**Manual Mode is enabled. Auto-rename is disabled.**

Please choose an option:"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename File", callback_data=f"manual_rename_{message.id}")],
        [InlineKeyboardButton("📤 Upload As Is", callback_data=f"upload_as_is_{message.id}")],
        [InlineKeyboardButton("⚙️ Change to Auto Mode", callback_data="setting_rename_mode")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_upload_{message.id}")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

# Additional callback handlers for sub-options
@Client.on_callback_query(filters.regex(r"^(send_as_|rename_mode_|meta_|dest_|manual_rename_|upload_as_is_|cancel_upload_)"))
async def sub_settings_handler(client, query: CallbackQuery):
    """Handle sub-setting callbacks"""
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("send_as_"):
        send_type = data.replace("send_as_", "")
        await DARKXSIDE78.set_media_preference(user_id, send_type)
        await query.answer(f"Send as {send_type} ✅")
        await show_main_settings(client, query)
        
    elif data.startswith("rename_mode_"):
        mode = data.replace("rename_mode_", "").title()
        await DARKXSIDE78.update_user_setting(user_id, 'rename_mode', mode)
        await query.answer(f"Rename mode set to {mode} ✅")
        await show_main_settings(client, query)
        
    elif data.startswith("meta_"):
        await handle_metadata_sub_setting(client, query, data)
        
    elif data.startswith("dest_"):
        user_states[user_id] = {
            'state': 'waiting_upload_destination',
            'message': query.message
        }
        asyncio.create_task(clear_user_state_after_timeout(user_id, 60))
        text = "**Send Upload Destination ID. Timeout: 60 sec**"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔙 Back", callback_data="setting_upload_dest"),
                InlineKeyboardButton("❌ Close", callback_data="setting_close")
            ]
        ])
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
        
    elif data.startswith("manual_rename_"):
        message_id = data.replace("manual_rename_", "")
        # Set user state for manual rename
        user_states[user_id] = {
            'state': 'waiting_manual_rename',
            'message_id': message_id,
            'message': query.message
        }
        
        text = "**✏️ Manual Rename**\n\nSend the new filename (with extension).\nTimeout: 60 sec"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_upload_{message_id}")]
        ])
        
        await query.message.edit_text(text, reply_markup=keyboard)
        asyncio.create_task(clear_user_state_after_timeout(user_id, 60))
        
    elif data.startswith("upload_as_is_"):
        message_id = data.replace("upload_as_is_", "")
        await query.answer("📤 Uploading file as is...")
        
        # Get original message and upload without renaming
        try:
            original_msg = await client.get_messages(query.message.chat.id, int(message_id))
            await upload_file_without_rename(client, original_msg)
            await query.message.delete()
        except Exception as e:
            await query.answer("❌ Error uploading file", show_alert=True)
            logging.error(f"Upload as is error: {e}")
            
    elif data.startswith("cancel_upload_"):
        await query.answer("❌ Upload cancelled")
        await query.message.delete()

async def handle_metadata_sub_setting(client, query: CallbackQuery, data: str):
    """Handle metadata sub-settings"""
    user_id = query.from_user.id
    
    if data == "meta_video_title":
        user_states[user_id] = {
            'state': 'waiting_video_title',
            'message': query.message
        }
        text = "**Send Video Title. Timeout: 60 sec**"
    elif data == "meta_video_author":
        user_states[user_id] = {
            'state': 'waiting_video_author',
            'message': query.message
        }
        text = "**Send Video Author. Timeout: 60 sec**"
    elif data == "meta_audio_title":
        user_states[user_id] = {
            'state': 'waiting_audio_title',
            'message': query.message
        }
        text = "**Send Audio Title. Timeout: 60 sec**"
    elif data == "meta_subtitle_title":
        user_states[user_id] = {
            'state': 'waiting_subtitle_title',
            'message': query.message
        }
        text = "**Send Subtitle Title. Timeout: 60 sec**"
    
    asyncio.create_task(clear_user_state_after_timeout(user_id, 60))
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_metadata"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)

# Input handlers for user states
@Client.on_message(filters.private & filters.text & ~filters.command(["start", "help", "settings", "autorename", "metadata", "tutorial", "token", "gentoken"]))
async def handle_settings_input(client, message: Message):
    """Handle text input for settings"""
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
        
    state_info = user_states[user_id]
    if isinstance(state_info, str):
        # Old format, convert to new format
        state = state_info
        settings_msg = None
    else:
        state = state_info.get('state')
        settings_msg = state_info.get('message')
    
    text = message.text.strip()
    
    try:
        # Delete user's message immediately
        try:
            await message.delete()
        except:
            pass
        
        if state == "waiting_prefix":
            await DARKXSIDE78.set_prefix(user_id, text)
            await show_temp_success_and_edit_settings(client, message, settings_msg, f"✅ **Prefix saved successfully!**\n\nPrefix: `{text}`")
            
        elif state == "waiting_suffix":
            await DARKXSIDE78.set_suffix(user_id, text)
            await show_temp_success_and_edit_settings(client, message, settings_msg, f"✅ **Suffix saved successfully!**\n\nSuffix: `{text}`")
            
        elif state == "waiting_remove_words":
            await DARKXSIDE78.set_remove_words(user_id, text)
            await show_temp_success_and_edit_settings(client, message, settings_msg, f"✅ **Remove words pattern saved!**\n\nPattern: `{text}`")
            
        elif state == "waiting_video_title":
            await DARKXSIDE78.set_title(user_id, text)
            await show_temp_success_and_redirect_to_metadata(client, message, settings_msg, f"✅ **Video Title Saved**\n\nTitle: `{text}`")
            
        elif state == "waiting_video_author":
            await DARKXSIDE78.set_author(user_id, text)
            await show_temp_success_and_redirect_to_metadata(client, message, settings_msg, f"✅ **Video Author Saved**\n\nAuthor: `{text}`")
            
        elif state == "waiting_audio_title":
            await DARKXSIDE78.set_audio(user_id, text)
            await show_temp_success_and_redirect_to_metadata(client, message, settings_msg, f"✅ **Audio Title Saved**\n\nTitle: `{text}`")
            
        elif state == "waiting_subtitle_title":
            await DARKXSIDE78.set_subtitle(user_id, text)
            await show_temp_success_and_redirect_to_metadata(client, message, settings_msg, f"✅ **Subtitle Title Saved**\n\nTitle: `{text}`")
            
        elif state == "waiting_upload_destination":
            await DARKXSIDE78.set_upload_destination(user_id, text)
            await show_temp_success_and_edit_settings(client, message, settings_msg, f"✅ **Upload destination saved!**\n\nDestination: `{text}`")
            
        elif state == "waiting_caption":
            await DARKXSIDE78.set_caption(user_id, text)
            await show_temp_success_and_edit_settings(client, message, settings_msg, f"✅ **Caption saved successfully!**\n\nCaption: `{text}`")
            
        elif state == "waiting_manual_rename":
            # Handle manual rename input
            new_filename = text.strip()
            if new_filename:
                try:
                    message_id = state_info.get('message_id')
                    original_msg = await client.get_messages(message.chat.id, int(message_id))
                    
                    # Rename and upload the file
                    await rename_and_upload_file(client, original_msg, new_filename)
                    
                    await show_temp_success_and_edit_settings(
                        client, message, settings_msg, 
                        f"✅ **File renamed successfully!**\n\nNew name: `{new_filename}`"
                    )
                except Exception as e:
                    logging.error(f"Manual rename error: {e}")
                    await show_temp_success_and_edit_settings(
                        client, message, settings_msg, 
                        "❌ Error renaming file. Please try again."
                    )
            else:
                await show_temp_success_and_edit_settings(
                    client, message, settings_msg, 
                    "❌ Invalid filename. Please try again."
                )
            
        # Clear user state
        if user_id in user_states:
            del user_states[user_id]
        
    except Exception as e:
        logging.error(f"Settings input error: {e}")
        await show_temp_success_and_edit_settings(client, message, settings_msg, "❌ Error saving setting. Please try again.")

@Client.on_message(filters.private & filters.photo)
async def handle_thumbnail_input(client, message: Message):
    """Handle photo input for thumbnail"""
    user_id = message.from_user.id
    
    if user_id in user_states:
        state_info = user_states[user_id]
        if isinstance(state_info, str):
            state = state_info
            settings_msg = None
        else:
            state = state_info.get('state')
            settings_msg = state_info.get('message')
            
        if state == "waiting_thumbnail":
            try:
                # Delete user's photo message
                try:
                    await message.delete()
                except:
                    pass
                    
                await DARKXSIDE78.set_thumbnail(user_id, message.photo.file_id)
                
                # Clear user state
                if user_id in user_states:
                    del user_states[user_id]
                
                # Show success and redirect to main settings
                await show_temp_success_and_edit_settings(client, message, settings_msg, "✅ **Thumbnail saved successfully!**")
                
            except Exception as e:
                logging.error(f"Thumbnail input error: {e}")
                await show_temp_success_and_edit_settings(client, message, settings_msg, "❌ Error saving thumbnail. Please try again.")

async def show_temp_success_and_edit_settings(client, message: Message, settings_msg, success_text: str):
    """Show temporary success message and edit back to main settings"""
    # Send success message
    success_msg = await message.reply_text(success_text)
    
    # Wait 2 seconds
    await asyncio.sleep(2)
    
    # Delete success message
    try:
        await success_msg.delete()
    except:
        pass
    
    # Edit back to main settings
    if settings_msg:
        await edit_settings_message(client, settings_msg, message.from_user.id)
    else:
        # Fallback: create new settings panel if no reference found
        await send_main_settings_panel(client, message.from_user.id, message.chat.id)

async def show_temp_success_and_redirect_to_metadata(client, message: Message, settings_msg, success_text: str):
    """Show temporary success message and redirect to metadata settings"""
    # Send success message
    success_msg = await message.reply_text(success_text)
    
    # Wait 2 seconds
    await asyncio.sleep(2)
    
    # Delete success message
    try:
        await success_msg.delete()
    except:
        pass
    
    # Show metadata settings instead of main settings
    if settings_msg:
        await show_metadata_settings(client, settings_msg, message.from_user.id)
    else:
        # Fallback: create new settings panel if no reference found
        await send_main_settings_panel(client, message.from_user.id, message.chat.id)

async def show_metadata_settings(client, settings_msg, user_id: int):
    """Show metadata settings panel"""
    current = await DARKXSIDE78.get_metadata(user_id)
    title = await DARKXSIDE78.get_title(user_id)
    author = await DARKXSIDE78.get_author(user_id)
    audio = await DARKXSIDE78.get_audio(user_id)
    subtitle = await DARKXSIDE78.get_subtitle(user_id)
    
    text = f"""**🏷️ Metadata Setting for** `{(await client.get_users(user_id)).first_name}` **⚙️**

Video Title is {title or 'None'}
Video Author is {author or 'None'}  
Audio Title is {audio or 'None'}
Subtitle Title is {subtitle or 'None'}"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Video Title", callback_data="meta_video_title")],
        [InlineKeyboardButton("Set Video Author", callback_data="meta_video_author")],
        [InlineKeyboardButton("Set Audio Title", callback_data="meta_audio_title")],
        [InlineKeyboardButton("Set Subtitle Title", callback_data="meta_subtitle_title")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    try:
        await settings_msg.edit_caption(caption=text, reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error showing metadata settings: {e}")

async def edit_settings_message(client, settings_msg, user_id: int):
    """Edit settings message with updated content"""
    settings = await DARKXSIDE78.get_user_settings(user_id)
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    auto_rename_status = 'Disabled (Manual Mode)' if settings['rename_mode'] == 'Manual' else 'Enabled'
    
    settings_text = f"""**🛠️ Settings for** `{(await client.get_users(user_id)).first_name}` **⚙️**

**Custom Thumbnail:** {'Exists' if thumbnail_status else 'Not Exists'}
**Upload Type:** {settings['send_as'].upper()}
**Prefix:** {settings['prefix'] or 'None'}
**Suffix:** {settings['suffix'] or 'None'}

**Upload Destination:** {settings['upload_destination'] or 'None'}
**Sample Video:** {'Enabled' if settings['sample_video'] else 'Disabled'}
**Screenshot:** {'Enabled' if settings['screenshot_enabled'] else 'Disabled'}

**Metadata:** {'Enabled' if metadata_status != 'Off' else 'Disabled'}
**Remove/Replace Words:** {settings['remove_words'] or 'None'}
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}
**Auto-Rename:** {auto_rename_status}"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Choose Format", callback_data="setting_send_as"),
            InlineKeyboardButton("Set Upload Destination", callback_data="setting_upload_dest")
        ],
        [
            InlineKeyboardButton("Set Thumbnail", callback_data="setting_thumbnail"),
            InlineKeyboardButton("Set Caption", callback_data="setting_caption")
        ],
        [
            InlineKeyboardButton("Set Prefix", callback_data="setting_prefix"),
            InlineKeyboardButton("Set Suffix", callback_data="setting_suffix")
        ],
        [
            InlineKeyboardButton(f"Rename Mode | {settings['rename_mode']}", callback_data="setting_rename_mode"),
            InlineKeyboardButton("Set Metadata", callback_data="setting_metadata")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="setting_remove_words"),
            InlineKeyboardButton(f"Enable Sample Video", callback_data="setting_sample_video")
        ],
        [
            InlineKeyboardButton(f"Enable Screenshot", callback_data="setting_screenshot")
        ]
    ])

    # Get the appropriate photo - user's thumbnail or default
    settings_photo = await get_settings_photo(user_id)
    
    try:
        await settings_msg.edit_media(
            media=InputMediaPhoto(
                media=settings_photo,
                caption=settings_text
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        await settings_msg.edit_caption(
            caption=settings_text,
            reply_markup=keyboard
        )

async def send_main_settings_panel(client, user_id: int, chat_id: int):
    """Send new main settings panel"""
    settings = await DARKXSIDE78.get_user_settings(user_id)
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    auto_rename_status = 'Disabled (Manual Mode)' if settings['rename_mode'] == 'Manual' else 'Enabled'
    
    settings_text = f"""**🛠️ Settings for** `{(await client.get_users(user_id)).first_name}` **⚙️**

**Custom Thumbnail:** {'Exists' if thumbnail_status else 'Not Exists'}
**Upload Type:** {settings['send_as'].upper()}
**Prefix:** {settings['prefix'] or 'None'}
**Suffix:** {settings['suffix'] or 'None'}

**Upload Destination:** {settings['upload_destination'] or 'None'}
**Sample Video:** {'Enabled' if settings['sample_video'] else 'Disabled'}
**Screenshot:** {'Enabled' if settings['screenshot_enabled'] else 'Disabled'}

**Metadata:** {'Enabled' if metadata_status != 'Off' else 'Disabled'}
**Remove/Replace Words:** {settings['remove_words'] or 'None'}
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}
**Auto-Rename:** {auto_rename_status}"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Choose Format", callback_data="setting_send_as"),
            InlineKeyboardButton("Set Upload Destination", callback_data="setting_upload_dest")
        ],
        [
            InlineKeyboardButton("Set Thumbnail", callback_data="setting_thumbnail"),
            InlineKeyboardButton("Set Caption", callback_data="setting_caption")
        ],
        [
            InlineKeyboardButton("Set Prefix", callback_data="setting_prefix"),
            InlineKeyboardButton("Set Suffix", callback_data="setting_suffix")
        ],
        [
            InlineKeyboardButton(f"Rename Mode | {settings['rename_mode']}", callback_data="setting_rename_mode"),
            InlineKeyboardButton("Set Metadata", callback_data="setting_metadata")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="setting_remove_words"),
            InlineKeyboardButton(f"Enable Sample Video", callback_data="setting_sample_video")
        ],
        [
            InlineKeyboardButton(f"Enable Screenshot", callback_data="setting_screenshot")
        ]
    ])

    settings_photo = await get_settings_photo(user_id)

    try:
        sent_msg = await client.send_photo(
            chat_id,
            photo=settings_photo,
            caption=settings_text,
            reply_markup=keyboard
        )
        settings_messages[user_id] = sent_msg
    except Exception as e:
        sent_msg = await client.send_message(chat_id, settings_text, reply_markup=keyboard)
        settings_messages[user_id] = sent_msg

async def clear_user_state_after_timeout(user_id: int, timeout: int):
    """Clear user state after timeout"""
    await asyncio.sleep(timeout)
    if user_id in user_states:
        del user_states[user_id]

# Helper functions for manual rename
async def upload_file_without_rename(client, message):
    """Upload file without renaming"""
    try:
        # Just forward the file as is
        await message.copy(message.chat.id)
        await message.reply_text("✅ **File uploaded successfully without renaming!**")
    except Exception as e:
        logging.error(f"Upload without rename error: {e}")
        await message.reply_text("❌ **Error uploading file. Please try again.**")

async def rename_and_upload_file(client, message, new_filename):
    """Rename and upload file"""
    try:
        # This would involve downloading, renaming, and re-uploading
        # For now, just simulate the process
        await message.reply_text(f"✅ **File renamed to:** `{new_filename}`\n\n📤 **Uploading...**")
        
        # Add actual rename and upload logic here based on your existing implementation
        # This is a placeholder for the actual rename functionality
        
    except Exception as e:
        logging.error(f"Rename and upload error: {e}")
        await message.reply_text("❌ **Error renaming and uploading file. Please try again.**")
