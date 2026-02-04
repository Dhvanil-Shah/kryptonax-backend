"""
Keep-Alive Script for Render Free Tier
Pings the server every 10 minutes to prevent cold starts
"""
import requests
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_URL = "https://kryptonax-backend.onrender.com/health"
PING_INTERVAL = 600  # 10 minutes (Render sleeps after 15 min inactivity)

def ping_server():
    """Send a ping to keep the server alive"""
    try:
        response = requests.get(SERVER_URL, timeout=10)
        if response.status_code == 200:
            logger.info(f"✓ Ping successful at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            logger.warning(f"⚠ Ping returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Ping failed: {str(e)}")
        return False

def main():
    """Main keep-alive loop"""
    logger.info("🚀 Keep-Alive service started")
    logger.info(f"📍 Target: {SERVER_URL}")
    logger.info(f"⏱️  Interval: {PING_INTERVAL} seconds")
    
    while True:
        ping_server()
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    main()
