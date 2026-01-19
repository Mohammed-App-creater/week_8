import os
import json
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'medical_scraper_session'

CHANNELS_TO_SCRAPE = [
    'Chemed',
    'https://t.me/lobelia4cosmetics',
    'https://t.me/tikvahpharma',
    # Add more channels here
]

# Paths
DATA_DIR = os.path.join('data', 'raw')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
MESSAGES_DIR = os.path.join(DATA_DIR, 'telegram_messages')
LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'scraper.log')

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MESSAGES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramScraper:
    def __init__(self, api_id, api_hash, session_name):
        self.client = TelegramClient(session_name, api_id, api_hash)

    async def scrape_channel(self, channel_url):
        """
        Scrapes messages from a single Telegram channel.
        """
        try:
            logger.info(f"Starting scrape for channel: {channel_url}")
            entity = await self.client.get_entity(channel_url)
            channel_name = entity.username or entity.id
            channel_title = entity.title
            
            # Create channel-specific image directory
            channel_img_dir = os.path.join(IMAGES_DIR, str(channel_name))
            os.makedirs(channel_img_dir, exist_ok=True)

            today_str = datetime.now().strftime('%Y-%m-%d')
            daily_messages_dir = os.path.join(MESSAGES_DIR, today_str)
            os.makedirs(daily_messages_dir, exist_ok=True)
            
            output_file = os.path.join(daily_messages_dir, f"{channel_name}.json")
            
            messages_data = []
            
            # Strategy: Fetch last 100 messages for now (or configurable limit)
            # In a full production run, we might want to iterate deeper or check for existing IDs
            limit = 100 
            
            async for message in self.client.iter_messages(entity, limit=limit):
                try:
                    msg_data = {
                        'message_id': message.id,
                        'channel_name': str(channel_name),
                        'channel_title': channel_title,
                        'date': message.date.isoformat(),
                        'message_text': message.text,
                        'views': message.views,
                        'forwards': message.forwards,
                        'has_media': bool(message.media),
                        'image_path': None
                    }

                    if message.photo:
                        image_filename = f"{message.id}.jpg"
                        image_path = os.path.join(channel_img_dir, image_filename)
                        
                        if not os.path.exists(image_path):
                            await self.client.download_media(message, file=image_path)
                            logger.debug(f"Downloaded image: {image_path}")
                        
                        msg_data['image_path'] = image_path

                    messages_data.append(msg_data)

                except Exception as e:
                    logger.error(f"Error processing message {message.id} from {channel_name}: {e}")

            # Save to JSON
            # Upsert strategy: Read existing if exists, update with new messages
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        # Create a dict for easier lookup
                        existing_dict = {msg['message_id']: msg for msg in existing_data}
                        
                        # Update/Add new messages
                        for msg in messages_data:
                            existing_dict[msg['message_id']] = msg
                            
                        # Convert back to list
                        messages_data = list(existing_dict.values())
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode existing JSON file {output_file}. Overwriting.")

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, indent=4, ensure_ascii=False)

            logger.info(f"Successfully scraped {len(messages_data)} messages for {channel_name}")

        except Exception as e:
            logger.error(f"Failed to scrape channel {channel_url}: {e}")

    async def run(self, channels):
        await self.client.start()
        logger.info("Client started.")
        
        for channel in channels:
            await self.scrape_channel(channel)
            
        logger.info("Scraping completed for all channels.")
        
    def main(self):
        if not API_ID or not API_HASH:
            logger.critical("TELEGRAM_API_ID or TELEGRAM_API_HASH not found in environment variables.")
            return

        with self.client:
            self.client.loop.run_until_complete(self.run(CHANNELS_TO_SCRAPE))

if __name__ == '__main__':
    scraper = TelegramScraper(API_ID, API_HASH, SESSION_NAME)
    scraper.main()
