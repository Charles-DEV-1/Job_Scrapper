import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Email configuration (using your Gmail settings)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'Cesca1Mul@gmail.com'
    MAIL_PASSWORD = 'rpqg ctjg vdru zsli'
    MAIL_DEBUG = True
    MAIL_DEFAULT_SENDER = 'Cesca1Mul@gmail.com'
    
    # Who to send alerts to
    ALERT_EMAIL = 'Cesca1Mul@gmail.com'  # Send to yourself
    
    # Scraping settings
    CHECK_INTERVAL_HOURS = 2  # Check every 2 hours
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'