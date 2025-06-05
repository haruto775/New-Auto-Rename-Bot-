import motor.motor_asyncio
import datetime
import pytz
from config import Config
import logging

class Database:
    def __init__(self, uri, database_name):
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self._client.server_info()
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e
        self.DARKXSIDE78 = self._client[database_name]
        self.col = self.DARKXSIDE78.user
        self.token_links = self.DARKXSIDE78.token_links  # Token links collection

    def new_user(self, id):
        return dict(
            _id=int(id),
            join_date=datetime.datetime.now(pytz.utc).date().isoformat(),
            file_id=None,
            caption=None,
            metadata="Off",
            metadata_code="Telegram : @DARKXSIDE78",
            format_template=None,
            rename_count=0,
            first_name="",
            username="",
            token_tasks=[],
            is_premium=False,
            premium_expiry=None,
            token=69,  # Default token value
            media_type=None,
            title='GenAnimeOfc [t.me/GenAnimeOfc]',
            author='DARKXSIDE78',
            artist='DARKXSIDE78',
            audio='[GenAnimeOfc]',
            subtitle="[GenAnimeOfc]",
            video='[GenAnimeOfc]',
            encoded_by="GenAnimeOfc [DARKXSIDE78]",
            custom_tag="[GenAnimeOfc]",
            # New settings for settings panel
            upload_mode='Telegram',
            send_as='DOCUMENT',
            upload_destination=None,
            prefix=None,
            suffix=None,
            rename_mode='Auto',
            remove_words=None,
            sample_video=False,
            screenshot_enabled=False,
            ai_autorename=False,
            manual_mode=False,
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.datetime.max.date().isoformat(),
                ban_reason=''
            )
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            # Add user's actual information
            user["first_name"] = u.first_name or "Unknown"
            user["username"] = u.username or ""
            try:
                await self.col.insert_one(user)
                logging.info(f"User {u.id} added to database")
            except Exception as e:
                logging.error(f"Error adding user {u.id} to database: {e}")

    async def is_user_exist(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return bool(user)
        except Exception as e:
            logging.error(f"Error checking if user {id} exists: {e}")
            return False

    async def total_users_count(self):
        try:
            count = await self.col.count_documents({})
            return count
        except Exception as e:
            logging.error(f"Error counting users: {e}")
            return 0

    async def get_all_users(self):
        try:
            all_users = self.col.find({})
            return all_users
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return None

    async def delete_user(self, user_id):
        try:
            await self.col.delete_many({"_id": int(user_id)})
        except Exception as e:
            logging.error(f"Error deleting user {user_id}: {e}")

    async def set_thumbnail(self, id, file_id):
        try:
            await self.col.update_one({"_id": int(id)}, {"$set": {"file_id": file_id}})
        except Exception as e:
            logging.error(f"Error setting thumbnail for user {id}: {e}")

    async def get_thumbnail(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("file_id", None) if user else None
        except Exception as e:
            logging.error(f"Error getting thumbnail for user {id}: {e}")
            return None

    async def set_caption(self, id, caption):
        try:
            await self.col.update_one({"_id": int(id)}, {"$set": {"caption": caption}})
        except Exception as e:
            logging.error(f"Error setting caption for user {id}: {e}")

    async def get_caption(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("caption", None) if user else None
        except Exception as e:
            logging.error(f"Error getting caption for user {id}: {e}")
            return None

    async def set_format_template(self, id, format_template):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"format_template": format_template}}
            )
        except Exception as e:
            logging.error(f"Error setting format template for user {id}: {e}")

    async def get_format_template(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("format_template", None) if user else None
        except Exception as e:
            logging.error(f"Error getting format template for user {id}: {e}")
            return None

    async def create_token_link(self, user_id: int, token_id: str, tokens: int):
        expiry = datetime.datetime.now(pytz.utc) + datetime.timedelta(hours=24)
        try:
            await self.token_links.update_one(
                {"_id": token_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "tokens": tokens,
                        "used": False,
                        "expiry": expiry
                    }
                },
                upsert=True
            )
            logging.info(f"Token link created for user {user_id} with token ID {token_id}.")
        except Exception as e:
            logging.error(f"Error creating token link: {e}")

    async def get_token_link(self, token_id: str):
        try:
            token_data = await self.token_links.find_one({"_id": token_id})
            return token_data
        except Exception as e:
            logging.error(f"Error fetching token link for token ID {token_id}: {e}")
            return None

    async def mark_token_used(self, token_id: str):
        try:
            await self.token_links.update_one(
                {"_id": token_id},
                {"$set": {"used": True}}
            )
            logging.info(f"Token {token_id} marked as used.")
        except Exception as e:
            logging.error(f"Error marking token as used: {e}")

    async def set_token(self, user_id, token):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"token": token}}
            )
            logging.info(f"Token updated for user {user_id}.")
        except Exception as e:
            logging.error(f"Error setting token for user {user_id}: {e}")

    async def get_token(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("token", 69) if user else 69
        except Exception as e:
            logging.error(f"Error getting token for user {user_id}: {e}")
            return 69

    async def set_media_preference(self, id, media_type):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"media_type": media_type}}
            )
        except Exception as e:
            logging.error(f"Error setting media preference for user {id}: {e}")

    async def get_media_preference(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("media_type", None) if user else None
        except Exception as e:
            logging.error(f"Error getting media preference for user {id}: {e}")
            return None

    async def set_metadata(self, id, metadata):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"metadata": metadata}}
            )
        except Exception as e:
            logging.error(f"Error setting metadata for user {id}: {e}")

    async def get_metadata(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("metadata", "Off") if user else "Off"
        except Exception as e:
            logging.error(f"Error getting metadata for user {id}: {e}")
            return "Off"

    async def set_title(self, id, title):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"title": title}}
            )
        except Exception as e:
            logging.error(f"Error setting title for user {id}: {e}")

    async def get_title(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("title", None) if user else None
        except Exception as e:
            logging.error(f"Error getting title for user {id}: {e}")
            return None

    async def set_author(self, id, author):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"author": author}}
            )
        except Exception as e:
            logging.error(f"Error setting author for user {id}: {e}")

    async def get_author(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("author", None) if user else None
        except Exception as e:
            logging.error(f"Error getting author for user {id}: {e}")
            return None

    async def set_artist(self, id, artist):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"artist": artist}}
            )
        except Exception as e:
            logging.error(f"Error setting artist for user {id}: {e}")

    async def get_artist(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("artist", None) if user else None
        except Exception as e:
            logging.error(f"Error getting artist for user {id}: {e}")
            return None

    async def set_audio(self, id, audio):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"audio": audio}}
            )
        except Exception as e:
            logging.error(f"Error setting audio for user {id}: {e}")

    async def get_audio(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("audio", None) if user else None
        except Exception as e:
            logging.error(f"Error getting audio for user {id}: {e}")
            return None

    async def set_subtitle(self, id, subtitle):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"subtitle": subtitle}}
            )
        except Exception as e:
            logging.error(f"Error setting subtitle for user {id}: {e}")

    async def get_subtitle(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("subtitle", None) if user else None
        except Exception as e:
            logging.error(f"Error getting subtitle for user {id}: {e}")
            return None

    async def set_video(self, id, video):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"video": video}}
            )
        except Exception as e:
            logging.error(f"Error setting video for user {id}: {e}")

    async def get_video(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("video", None) if user else None
        except Exception as e:
            logging.error(f"Error getting video for user {id}: {e}")
            return None

    async def set_encoded_by(self, id, encoded_by):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"encoded_by": encoded_by}}
            )
        except Exception as e:
            logging.error(f"Error setting encoded_by for user {id}: {e}")

    async def get_encoded_by(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("encoded_by", None) if user else None
        except Exception as e:
            logging.error(f"Error getting encoded_by for user {id}: {e}")
            return None

    async def set_custom_tag(self, id, custom_tag):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"custom_tag": custom_tag}}
            )
        except Exception as e:
            logging.error(f"Error setting custom_tag for user {id}: {e}")

    async def get_custom_tag(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("custom_tag", None) if user else None
        except Exception as e:
            logging.error(f"Error getting custom_tag for user {id}: {e}")
            return None

    async def set_metadata_code(self, id, metadata_code):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"metadata_code": metadata_code}}
            )
        except Exception as e:
            logging.error(f"Error setting metadata_code for user {id}: {e}")

    async def get_metadata_code(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("metadata_code", "Telegram : @DARKXSIDE78") if user else "Telegram : @DARKXSIDE78"
        except Exception as e:
            logging.error(f"Error getting metadata_code for user {id}: {e}")
            return "Telegram : @DARKXSIDE78"

    # NEW SETTINGS PANEL METHODS

    async def get_user_settings(self, user_id):
        """Get all user settings in one query"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            if not user:
                return self.new_user_settings()
            
            # Return all settings with defaults
            return {
                'upload_mode': user.get('upload_mode', 'Telegram'),
                'send_as': user.get('send_as', 'DOCUMENT'),
                'upload_destination': user.get('upload_destination', None),
                'custom_thumbnail': user.get('file_id', None),
                'prefix': user.get('prefix', None),
                'suffix': user.get('suffix', None),
                'rename_mode': user.get('rename_mode', 'Auto'),
                'remove_words': user.get('remove_words', None),
                'sample_video': user.get('sample_video', False),
                'screenshot_enabled': user.get('screenshot_enabled', False),
                'ai_autorename': user.get('ai_autorename', False),
                'manual_mode': user.get('manual_mode', False)
            }
        except Exception as e:
            logging.error(f"Error getting user settings: {e}")
            return self.new_user_settings()

    def new_user_settings(self):
        """Default settings for new users"""
        return {
            'upload_mode': 'Telegram',
            'send_as': 'DOCUMENT', 
            'upload_destination': None,
            'custom_thumbnail': None,
            'prefix': None,
            'suffix': None,
            'rename_mode': 'Auto',
            'remove_words': None,
            'sample_video': False,
            'screenshot_enabled': False,
            'ai_autorename': False,
            'manual_mode': False
        }

    async def update_user_setting(self, user_id, setting_key, value):
        """Update a specific user setting"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {setting_key: value}}
            )
            return True
        except Exception as e:
            logging.error(f"Error updating setting {setting_key}: {e}")
            return False

    async def set_prefix(self, user_id, prefix):
        """Set filename prefix"""
        return await self.update_user_setting(user_id, 'prefix', prefix)

    async def get_prefix(self, user_id):
        """Get filename prefix"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('prefix', None) if user else None
        except Exception as e:
            logging.error(f"Error getting prefix: {e}")
            return None

    async def set_suffix(self, user_id, suffix):
        """Set filename suffix"""
        return await self.update_user_setting(user_id, 'suffix', suffix)

    async def get_suffix(self, user_id):
        """Get filename suffix"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('suffix', None) if user else None
        except Exception as e:
            logging.error(f"Error getting suffix: {e}")
            return None

    async def set_upload_destination(self, user_id, destination):
        """Set upload destination channel/group"""
        return await self.update_user_setting(user_id, 'upload_destination', destination)

    async def get_upload_destination(self, user_id):
        """Get upload destination"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('upload_destination', None) if user else None
        except Exception as e:
            logging.error(f"Error getting upload destination: {e}")
            return None

    async def set_remove_words(self, user_id, words):
        """Set words to remove from filenames"""
        return await self.update_user_setting(user_id, 'remove_words', words)

    async def get_remove_words(self, user_id):
        """Get words to remove from filenames"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('remove_words', None) if user else None
        except Exception as e:
            logging.error(f"Error getting remove words: {e}")
            return None

# Create database instance
DARKXSIDE78 = Database(Config.DB_URL, Config.DB_NAME)
