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

@Client.on_message(filters.private & filters.command("settings"))
async def settings_command(client, message: Message):
    """Main settings command"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Get current metadata status
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    
    # Get current thumbnail status - check if file_id exists
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    
    # Create settings overview text
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
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}"""

    # Create main settings keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Upload Mode | {settings['upload_mode']} ✅", callback_data="setting_upload_mode"),
        ],
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
            
        elif data == "setting_upload_mode":
            await handle_upload_mode(client, query)
            
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
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Upload Mode | {settings['upload_mode']} ✅", callback_data="setting_upload_mode"),
        ],
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
async def handle_upload_mode(client, query: CallbackQuery):
    """Handle upload mode setting"""
    text = """**📤 Upload Mode Configuration**

Select how you want to upload your files:

• **Telegram**: Upload directly to current chat
• **Channel**: Upload to a specific channel  
• **Group**: Upload to a specific group"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Telegram ✅", callback_data="upload_mode_telegram")],
        [InlineKeyboardButton("Channel", callback_data="upload_mode_channel")],
        [InlineKeyboardButton("Group", callback_data="upload_mode_group")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="setting_back"),
            InlineKeyboardButton("❌ Close", callback_data="setting_close")
        ]
    ])
    
    await query.message.edit_caption(caption=text, reply_markup=keyboard)

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
        [InlineKeyboardButton(f"Set Manual Mode", callback_data="rename_mode_manual")],
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

# Additional callback handlers for sub-options
@Client.on_callback_query(filters.regex(r"^(upload_mode_|send_as_|rename_mode_|meta_|dest_)"))
async def sub_settings_handler(client, query: CallbackQuery):
    """Handle sub-setting callbacks"""
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("upload_mode_"):
        mode = data.replace("upload_mode_", "").title()
        await DARKXSIDE78.update_user_setting(user_id, 'upload_mode', mode)
        await query.answer(f"Upload mode set to {mode} ✅")
        await show_main_settings(client, query)
        
    elif data.startswith("send_as_"):
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
                
                # Show success and edit existing settings
                await show_temp_success_and_edit_settings(client, message, settings_msg, "✅ **Thumbnail Saved Successfully ✅️**")
                
                if user_id in user_states:
                    del user_states[user_id]
            except Exception as e:
                logging.error(f"Thumbnail save error: {e}")
                await show_temp_success_and_edit_settings(client, message, settings_msg, "❌ Error saving thumbnail. Please try again.")

async def show_temp_success_and_edit_settings(client, message: Message, settings_msg, success_text: str):
    """Show temporary success message and edit existing settings panel"""
    # Send success message
    success_msg = await message.reply_text(success_text)
    
    # Wait 2 seconds
    await asyncio.sleep(2)
    
    # Delete success message
    try:
        await success_msg.delete()
    except:
        pass
    
    # Edit the original settings message instead of creating new one
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
    """Edit the existing settings message with updated content"""
    try:
        settings = await DARKXSIDE78.get_user_settings(user_id)
        
        # Get current metadata status
        metadata_status = await DARKXSIDE78.get_metadata(user_id)
        
        # Get current thumbnail status - check if file_id exists
        thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
        
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
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}"""

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"Upload Mode | {settings['upload_mode']} ✅", callback_data="setting_upload_mode"),
            ],
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
        
        # Check if we need to change the photo
        try:
            await settings_msg.edit_media(
                media=InputMediaPhoto(
                    media=settings_photo,
                    caption=settings_text
                ),
                reply_markup=keyboard
            )
        except Exception as e:
            # If edit_media fails, try edit_caption
            await settings_msg.edit_caption(
                caption=settings_text,
                reply_markup=keyboard
            )

    except Exception as e:
        logging.error(f"Error editing settings message: {e}")
        # Fallback to creating new message
        await send_main_settings_panel(client, user_id, settings_msg.chat.id)

async def send_main_settings_panel(client, user_id: int, chat_id: int):
    """Send main settings panel as new message"""
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Get current metadata status
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    
    # Get current thumbnail status - check if file_id exists
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    
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
**Rename mode:** {settings['rename_mode']} | {settings['rename_mode']}"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Upload Mode | {settings['upload_mode']} ✅", callback_data="setting_upload_mode"),
        ],
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
        await client.send_photo(
            chat_id=chat_id,
            photo=settings_photo,
            caption=settings_text,
            reply_markup=keyboard
        )
    except Exception as e:
        await client.send_message(
            chat_id=chat_id,
            text=settings_text,
            reply_markup=keyboard
        )

async def clear_user_state_after_timeout(user_id: int, timeout: int = 60):
    """Clear user state after timeout"""
    await asyncio.sleep(timeout)
    if user_id in user_states:
        del user_states[user_id]
