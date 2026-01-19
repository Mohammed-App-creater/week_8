# Telegram Medical Channel Scraper

This project scrapes public Telegram channels for medical and pharmaceutical products, preserving messages and images in a raw format for downstream processing.

## Project Structure

```
/
├── src/
│   └── scraper.py       # Main scraping script
├── data/
│   ├── raw/
│   │   ├── telegram_messages/  # JSON files grouped by date/channel
│   │   └── images/             # Images grouped by channel
├── logs/
│   └── scraper.log      # Application logs
├── requirements.txt     # Python dependencies
├── .env                 # API credentials (not committed)
└── README.md            # This file
```

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment**:
    Create a `.env` file in the root directory with your Telegram API credentials:
    ```env
    TELEGRAM_API_ID=your_api_id
    TELEGRAM_API_HASH=your_api_hash
    ```
    *Note: You can get these from [my.telegram.org](https://my.telegram.org).*

## Usage

Run the scraper using Python:

```bash
python src/scraper.py
```

**First Run**: The first time you run this, it will prompt you to enter your phone number and the code you receive on Telegram to authenticate and create a session file.

## Output

- **Messages**: Saved as `data/raw/telegram_messages/YYYY-MM-DD/{channel_name}.json`.
- **Images**: Saved in `data/raw/images/{channel_name}/{message_id}.jpg`.
- **Logs**: Execution logs are stored in `logs/scraper.log`.

## Configuration

You can add more channels to scrape by modifying the `CHANNELS_TO_SCRAPE` list in `src/scraper.py`.
