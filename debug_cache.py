"""
Debug script to test MongoDB cache and quality score endpoint
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ MONGO_URI not found in environment")
    exit(1)

client = MongoClient(MONGO_URI)
db = client['kryptonax']
company_data_collection = db['company_data']

# Check cache for BHEL.BO
ticker = "BHEL.BO"
cached = company_data_collection.find_one({"ticker": ticker, "type": "quality_score"})

if cached:
    print(f"✅ Found cached data for {ticker}")
    print(f"Timestamp: {cached.get('timestamp')}")
    print(f"Has error: {'error' in cached.get('data', {})}")
    if 'error' in cached.get('data', {}):
        print(f"Error message: {cached['data']['error']}")
        print(f"\n🗑️ Deleting bad cache...")
        result = company_data_collection.delete_one({"ticker": ticker, "type": "quality_score"})
        print(f"Deleted {result.deleted_count} entries")
    else:
        print(f"Score: {cached.get('data', {}).get('overall_score')}")
else:
    print(f"⚠️ No cache found for {ticker}")

# List all cached tickers
print(f"\n📋 All cached quality scores:")
all_cached = company_data_collection.find({"type": "quality_score"})
for item in all_cached:
    has_error = 'error' in item.get('data', {})
    print(f"  - {item['ticker']}: {'❌ ERROR' if has_error else '✅ OK'}")
