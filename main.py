"""
Auto Rename Bot - Main Entry Point

This is the main entry point for the Telegram Auto Rename Bot.
The bot provides automatic file renaming capabilities with premium features,
metadata support, and admin management.

Features:
- Auto-rename files with custom templates
- Premium user management with token system
- File metadata modification
- Thumbnail and caption support
- Sequence processing for multiple files
- Force subscription system
- Admin controls

Author: DARKXSIDE78
"""

import logging
import os
import sys
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_config():
    """Validate required configuration variables"""
    required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'DB_URL']
    missing_vars = []
    
    for var in required_vars:
        if not getattr(Config, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set the required environment variables and restart the bot.")
        sys.exit(1)
    
    # Check if admins are configured
    if not Config.ADMIN:
        logger.warning("No admin users configured. Some features may not work properly.")
    
    # Check database connection
    if not Config.DB_URL:
        logger.error("Database URL not configured!")
        sys.exit(1)
    
    logger.info("Configuration validated successfully!")

def main():
    """Main function to start the bot"""
    try:
        # Validate configuration
        check_config()
        
        # Create necessary directories
        os.makedirs("downloads", exist_ok=True)
        os.makedirs("Metadata", exist_ok=True)
        
        logger.info("Starting Auto Rename Bot...")
        logger.info(f"Bot configured for {'webhook' if Config.WEBHOOK else 'polling'} mode")
        
        # Import and start the bot
        from bot import Bot
        
        # Start the bot
        bot = Bot()
        logger.info("Bot instance created successfully")
        
        # Run the bot
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
      
