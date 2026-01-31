# from fastapi import FastAPI, HTTPException, Body, Depends, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# import requests
# import pymongo
# from datetime import datetime, timedelta
# import yfinance as yf
# from ai import get_sentiment 
# from typing import List
# from passlib.context import CryptContext
# from jose import JWTError, jwt
# from pydantic import BaseModel
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import random
# import string
# import os
# from dotenv import load_dotenv

# # 1. LOAD ENVIRONMENT VARIABLES
# load_dotenv()

# # --- CONFIGURATION ---
# API_KEY = "9f07c51e4e2145569ccba561e4e0d81a" 
# SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
# ALGORITHM = "HS256"

# # ⚠️ SECURITY WARNING: Move this to your .env file in production!
# MONGO_URI = "mongodb+srv://admin:(!#Krypton1!#)@cluster0.snwbrpt.mongodb.net/?appName=Cluster0"

# # --- EMAIL CONFIG (Titan/GoDaddy) ---
# SMTP_SERVER = os.getenv("MAIL_SERVER", "smtp.titan.email")
# SMTP_PORT = int(os.getenv("MAIL_PORT", 587))
# SMTP_USERNAME = os.getenv("MAIL_USERNAME", "kryptonaxofficial@kryptonax.com")
# SMTP_PASSWORD = os.getenv("MAIL_PASSWORD", "(!#Kryptonaxofficial1!#)")
# SMTP_FROM = os.getenv("MAIL_FROM", "kryptonaxofficial@kryptonax.com")

# # --- SETUP ---
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# client = pymongo.MongoClient(MONGO_URI)
# db = client["kryptonax"]
# users_collection = db["users"]
# subscriptions_collection = db["subscriptions"]
# news_collection = db["news_articles"]
# fav_collection = db["favorites"]

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# # --- MODELS ---
# class UserRegister(BaseModel):
#     username: str
#     password: str
#     first_name: str
#     last_name: str
#     mobile: str

# class UserCreate(BaseModel):
#     username: str
#     password: str
#     first_name: str
#     last_name: str
#     mobile: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str
#     user_name: str

# class ForgotPasswordRequest(BaseModel):
#     username: str

# class ResetPasswordRequest(BaseModel):
#     username: str
#     otp: str
#     new_password: str

# # --- HELPERS ---
# def get_password_hash(password): 
#     return pwd_context.hash(password)

# def verify_password(plain, hashed): 
#     return pwd_context.verify(plain, hashed)

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     to_encode.update({"exp": datetime.utcnow() + timedelta(days=7)})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def generate_otp():
#     return ''.join(random.choices(string.digits, k=6))

# # --- CURRENT USER HELPER (Optional Auth) ---
# def get_current_user(token: str = Depends(oauth2_scheme)):
#     # If no token provided, return guest user
#     if not token:
#         return {"username": "guest", "is_guest": True}
    
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             return {"username": "guest", "is_guest": True}
#     except JWTError:
#         return {"username": "guest", "is_guest": True}
    
#     user = users_collection.find_one({"username": username})
#     if user is None:
#         return {"username": "guest", "is_guest": True}
#     return user

# # --- EMAIL FUNCTIONS ---
# def send_email_otp(to_email, otp):
#     print(f"📧 Attempting to send OTP email to {to_email}...")
#     try:
#         msg = MIMEMultipart()
#         msg['From'] = SMTP_FROM
#         msg['To'] = to_email
#         msg['Subject'] = "Kryptonax Password Reset OTP"

#         body = f"""
#         <html>
#             <body style="font-family: Arial, sans-serif; color: #333;">
#                 <h2 style="color: #2962ff;">Kryptonax Security</h2>
#                 <p>You requested to reset your password.</p>
#                 <p>Your One-Time Password (OTP) is:</p>
#                 <h1 style="background-color: #f4f4f4; padding: 10px; display: inline-block; letter-spacing: 5px; color: #000;">{otp}</h1>
#                 <p>This code is valid for 10 minutes.</p>
#             </body>
#         </html>
#         """
#         msg.attach(MIMEText(body, 'html'))

#         print(f"🔌 Connecting to SMTP {SMTP_SERVER}:{SMTP_PORT} (SSL, timeout=30s)...")
#         server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
#         print(f"🔐 Authenticating with {SMTP_USERNAME}...")
#         server.login(SMTP_USERNAME, SMTP_PASSWORD)
#         print(f"📤 Sending message...")
#         server.send_message(msg)
#         server.quit()

#         print(f"✅ OTP email successfully sent to {to_email}")
#         return True
#     except smtplib.SMTPAuthenticationError as e:
#         print(f"❌ SMTP AUTH FAILED: Invalid credentials. Error: {e}")
#         print(f"   Username: {SMTP_USERNAME}")
#         print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
#         return False
#     except TimeoutError as e:
#         print(f"❌ TIMEOUT: Cannot reach {SMTP_SERVER}:{SMTP_PORT}. Check MAIL_SERVER in .env")
#         print(f"   GoDaddy Standard Email: smtpout.secureserver.net (port 465)")
#         print(f"   Verify credentials are correct")
#         return False
#     except smtplib.SMTPException as e:
#         print(f"❌ SMTP ERROR: {e}")
#         return False
#     except Exception as e:
#         print(f"❌ EMAIL FAILED: {type(e).__name__}: {e}")
#         import traceback
#         traceback.print_exc()
#         return False

# def send_welcome_email(email_to: str, ticker: str):
#     html = f"""
#     <h3>Kryptonax Alert</h3>
#     <p>You are now subscribed to updates for: <b>{ticker}</b></p>
#     <p>We will notify you on significant market movement via email.</p>
#     """
#     try:
#         msg = MIMEMultipart()
#         msg['From'] = SMTP_FROM
#         msg['To'] = email_to
#         msg['Subject'] = f"Alert Subscribed: {ticker}"
#         msg.attach(MIMEText(html, 'html'))
        
#         print(f"🔌 Connecting to SMTP {SMTP_SERVER}:{SMTP_PORT} (SSL, timeout=30s)...")
#         server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
#         print(f"🔐 Authenticating with {SMTP_USERNAME}...")
#         server.login(SMTP_USERNAME, SMTP_PASSWORD)
#         print(f"📤 Sending message...")
#         server.send_message(msg)
#         server.quit()
        
#         print(f"✅ Welcome email sent to {email_to} for {ticker}")
#         return True
#     except smtplib.SMTPAuthenticationError as e:
#         print(f"❌ SMTP AUTH FAILED: Invalid credentials. Error: {e}")
#         print(f"   Username: {SMTP_USERNAME}")
#         print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
#         return False
#     except TimeoutError as e:
#         print(f"❌ TIMEOUT: Cannot reach {SMTP_SERVER}:{SMTP_PORT}. Check MAIL_SERVER in .env")
#         print(f"   GoDaddy Standard Email: smtpout.secureserver.net (port 465)")
#         print(f"   Verify credentials are correct")
#         return False
#     except smtplib.SMTPException as e:
#         print(f"❌ SMTP ERROR: {e}")
#         return False
#     except Exception as e:
#         print(f"❌ Welcome email error: {type(e).__name__}: {e}")
#         import traceback
#         traceback.print_exc()
#         return False
# def send_sms_otp_simulated(mobile, otp):
#     print("\n" + "="*40)
#     print(f"📱 SMS SIMULATION TO: {mobile}")
#     print(f"🔑 OTP MESSAGE: Your Kryptonax code is: [{otp}]")
#     print("="*40 + "\n")

# # ==========================================
# #               ENDPOINTS
# # ==========================================

# @app.get("/")
# def home():
#     return {"message": "Kryptonax API Live"}

# # --- AUTH ENDPOINTS ---

# @app.post("/register")
# def register(user: UserRegister):
#     clean_username = user.username.lower().strip()
#     if users_collection.find_one({"username": clean_username}):
#         raise HTTPException(status_code=400, detail="Email already registered")
#     users_collection.insert_one({
#         "username": clean_username,
#         "password": get_password_hash(user.password),
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "mobile": user.mobile
#     })
#     return {"message": "User created successfully"}

# @app.post("/token", response_model=Token)
# def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     clean_username = form_data.username.lower().strip()
#     user = users_collection.find_one({"username": clean_username})
#     if not user or not verify_password(form_data.password, user["password"]):
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
    
#     token = create_access_token(data={"sub": user["username"]})
#     user_name = user.get("first_name", "User")
#     return {
#         "access_token": token, 
#         "token_type": "bearer", 
#         "user_name": user_name
#     }

# # --- FORGOT PASSWORD FLOW ---

# @app.post("/forgot-password")
# def forgot_password(req: ForgotPasswordRequest):
#     clean_username = req.username.lower().strip()
#     user = users_collection.find_one({"username": clean_username})
    
#     if not user:
#         print(f"⚠️ Forgot Password request for non-existent user: {clean_username}")
#         return {"message": "If account exists, OTP sent."}
    
#     otp = generate_otp()
#     expiry = datetime.utcnow() + timedelta(minutes=10)
    
#     # Update DB
#     users_collection.update_one(
#         {"username": clean_username},
#         {"$set": {"otp_code": otp, "otp_expiry": expiry}}
#     )
    
#     # 1. Send SMS (Simulated)
#     if "mobile" in user:
#         send_sms_otp_simulated(user["mobile"], otp)
        
#     # 2. Send Email (Real)
#     send_email_otp(clean_username, otp)
        
#     return {"message": "OTP sent to registered email and mobile"}

# @app.post("/reset-password")
# def reset_password(req: ResetPasswordRequest):
#     clean_username = req.username.lower().strip()
#     user = users_collection.find_one({"username": clean_username})
    
#     if not user: 
#         raise HTTPException(status_code=400, detail="User not found")
    
#     # DEBUGGING: Print what is happening
#     received_otp = req.otp.strip()
#     stored_otp = user.get("otp_code")
    
#     print(f"🔍 DEBUG RESET: User={clean_username} | Stored OTP='{stored_otp}' | Input OTP='{received_otp}'")

#     if not stored_otp:
#         raise HTTPException(status_code=400, detail="No OTP request found. Request a new one.")
        
#     if stored_otp != received_otp:
#         print("❌ OTP Mismatch!")
#         raise HTTPException(status_code=400, detail="Invalid OTP")
        
#     if "otp_expiry" in user and datetime.utcnow() > user["otp_expiry"]:
#         raise HTTPException(status_code=400, detail="OTP Expired")
        
#     # Success - Reset Password
#     new_hashed = get_password_hash(req.new_password)
#     users_collection.update_one(
#         {"username": clean_username},
#         {"$set": {"password": new_hashed}, "$unset": {"otp_code": "", "otp_expiry": ""}}
#     )
#     print("✅ Password reset successful")
    
#     return {"message": "Password reset successful! Please login."}

# # --- SUBSCRIBE ENDPOINTS (BELL ICON LOGIC) ---

# # 1. SUBSCRIBE (Enable Bell)
# @app.post("/subscribe/{ticker}", status_code=status.HTTP_201_CREATED)
# def subscribe_to_ticker(ticker: str, current_user: dict = Depends(get_current_user)):
#     username = current_user.get("username", "guest")
    
#     # Check if already subscribed
#     existing = subscriptions_collection.find_one({
#         "username": username,
#         "ticker": ticker
#     })
    
#     if existing:
#         return {"message": f"Already subscribed to {ticker}"}

#     # Add subscription to DB
#     subscriptions_collection.insert_one({
#         "username": username,
#         "ticker": ticker
#     })
    
#     # Send Email Notification
#     send_welcome_email(username, ticker)
    
#     return {"message": f"Successfully subscribed to {ticker}"}

# # 2. UNSUBSCRIBE (Disable Bell)
# @app.delete("/subscribe/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
# def unsubscribe_from_ticker(ticker: str, current_user: dict = Depends(get_current_user)):
#     username = current_user.get("username", "guest")

#     # Delete subscription from DB
#     result = subscriptions_collection.delete_one({
#         "username": username,
#         "ticker": ticker
#     })

#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Subscription not found")

#     return

# # 3. GET FAVORITES (Restore Bell State on Refresh)
# @app.get("/favorites")
# def get_favorites(current_user: dict = Depends(get_current_user)):
#     username = current_user.get("username", "guest")
    
#     # Find all tickers this user is subscribed to
#     subs = list(subscriptions_collection.find({"username": username}))
    
#     # Also get watchlist favorites with live prices
#     fav_tickers = [doc["ticker"] for doc in fav_collection.find({"username": username})]
#     results = [{"ticker": sub["ticker"]} for sub in subs]
    
#     # Add watchlist favorites with live prices
#     if fav_tickers:
#         try:
#             stocks = yf.Tickers(" ".join(fav_tickers))
#             for t in fav_tickers:
#                 try:
#                     info = stocks.tickers[t].fast_info
#                     results.append({
#                         "ticker": t,
#                         "price": round(info.last_price, 2),
#                         "change": round(info.last_price - info.previous_close, 2),
#                         "percent": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2)
#                     })
#                 except:
#                     pass
#         except:
#             pass
    
#     return results

# # 4. Add a stock to favorites (Watchlist)
# @app.post("/favorites/{ticker}")
# def add_favorite(ticker: str, current_user: dict = Depends(get_current_user)):
#     username = current_user.get("username", "guest")
#     ticker = ticker.upper()
#     existing = fav_collection.find_one({"username": username, "ticker": ticker})
#     if existing:
#         return {"message": "Already in watchlist"}
    
#     fav_collection.insert_one({
#         "username": username,
#         "ticker": ticker,
#         "added_at": datetime.utcnow()
#     })
#     return {"message": f"Added {ticker} to watchlist"}

# # 5. Remove a stock from favorites
# @app.delete("/favorites/{ticker}")
# def remove_favorite(ticker: str, current_user: dict = Depends(get_current_user)):
#     username = current_user.get("username", "guest")
#     ticker = ticker.upper()
#     result = fav_collection.delete_one({"username": username, "ticker": ticker})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Ticker not found in watchlist")
#     return {"message": f"Removed {ticker}"}

# # --- DATA ENDPOINTS (Condensed) ---
# def fetch_from_api_and_save(ticker):
#     search_query = ticker.replace(".NS", "").replace(".BO", "")
#     mappings = { "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services", "INFY": "Infosys", "HDFCBANK": "HDFC Bank", "BTC-USD": "Bitcoin Crypto", "GC=F": "Gold Price", "SI=F": "Silver Price" }
#     if search_query in mappings: search_query = mappings[search_query]
#     try:
#         url = f"https://newsapi.org/v2/everything?q={search_query}&apiKey={API_KEY}&language=en&sortBy=publishedAt&from={(datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')}&pageSize=50"
#         data = requests.get(url).json(); articles = data.get("articles", [])
#         if articles:
#             news_collection.delete_many({"ticker": ticker})
#             for a in articles: a["ticker"] = ticker; a["fetched_at"] = datetime.now(); a["sentiment"] = get_sentiment(a.get("title", "")[:200])
#             news_collection.insert_many(articles)
#         return articles
#     except: return []

# @app.get("/news/general")
# def get_general_news():
#     cached = list(news_collection.find({"ticker": "GENERAL_TRENDING"}, {"_id": 0}).sort("publishedAt", -1))
#     if not cached or (datetime.now() - cached[0]["fetched_at"]).seconds > 21600:
#         try:
#             url = f"https://newsapi.org/v2/everything?q=stock market OR economy OR crypto&apiKey={API_KEY}&language=en&sortBy=publishedAt&pageSize=40"
#             articles = requests.get(url).json().get("articles", [])
#             if articles:
#                 news_collection.delete_many({"ticker": "GENERAL_TRENDING"})
#                 for a in articles: a["ticker"] = "GENERAL_TRENDING"; a["fetched_at"] = datetime.now(); a["sentiment"] = get_sentiment(a.get("title", "")[:200])
#                 news_collection.insert_many(articles)
#                 return articles
#         except: pass
#     return cached

# @app.get("/news/{ticker}")
# def get_news(ticker: str, period: str = "30d"): 
#     ticker = ticker.upper()
#     if news_collection.count_documents({"ticker": ticker}) < 5: fetch_from_api_and_save(ticker)
#     all_news = list(news_collection.find({"ticker": ticker}, {"_id": 0}).sort("publishedAt", -1))
#     filtered = []
#     limit = int(period.replace("d", "")) if "d" in period else 30
#     for n in all_news:
#         if (datetime.now() - datetime.strptime(n['publishedAt'][:10], '%Y-%m-%d')).days <= (2 if limit==1 else limit): filtered.append(n)
#     return filtered if filtered else all_news

# @app.get("/quote/{ticker}")
# def get_current_price(ticker: str):
#     try:
#         info = yf.Ticker(ticker.upper()).fast_info
#         return {"symbol": ticker.upper(), "price": round(info.last_price, 2), "change": round(info.last_price - info.previous_close, 2), "percent": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2), "currency": info.currency}
#     except: return {"price": 0, "change": 0, "percent": 0, "currency": "USD"}

# @app.post("/api/quotes")
# def get_batch_quotes(tickers: List[str] = Body(...)):
#     results = {}
#     if not tickers: return results
#     try:
#         stocks = yf.Tickers(" ".join(tickers))
#         for t in tickers:
#             try:
#                 i = stocks.tickers[t].fast_info
#                 results[t] = {"price": round(i.last_price, 2), "change": round(i.last_price - i.previous_close, 2), "percent": round(((i.last_price - i.previous_close) / i.previous_close)*100, 2), "color": "#00e676" if i.last_price >= i.previous_close else "#ff1744"}
#             except: results[t] = None
#     except: pass
#     return results

# @app.get("/history/{ticker}")
# def get_stock_history(ticker: str, period: str = "1mo"):
#     try:
#         stock = yf.Ticker(ticker.upper())
#         hist = stock.history(period=period, interval="1m" if period == "1d" else "15m" if period == "5d" else "1d")
#         data = [{"date": date.strftime('%H:%M') if period=="1d" else date.strftime('%Y-%m-%d'), "price": row['Close']} for date, row in hist.iterrows()]
#         return {"currency": "USD", "data": data}
#     except: return {"currency": "USD", "data": []}

# @app.get("/api/search/{query}")
# def search_tickers(query: str):
#     try:
#         r = requests.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={query}", headers={'User-Agent': 'Mozilla/5.0'}).json()
#         return [{"symbol": i['symbol'], "name": i.get('shortname', i['symbol']), "exchange": i.get('exchange', 'Unknown')} for i in r.get('quotes', []) if 'symbol' in i][:8]
#     except: return []

# @app.get("/trending")
# def get_global_trending():
#     data = []
#     for t in ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "AMD", "BTC-USD", "GC=F"]:
#         try:
#             i = yf.Ticker(t).fast_info
#             change = ((i.last_price - i.previous_close)/i.previous_close)*100
#             data.append({"ticker": t, "change": round(change, 2), "price": round(i.last_price, 2)})
#         except: continue
#     return sorted(data, key=lambda x: abs(x['change']), reverse=True)



from fastapi import FastAPI, HTTPException, Body, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import requests
import pymongo
from datetime import datetime, timedelta
import yfinance as yf
from ai import get_sentiment 
from typing import List
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import os
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()

# --- CONFIGURATION ---
API_KEY = "9f07c51e4e2145569ccba561e4e0d81a" 
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

# ⚠️ SECURITY WARNING: Move this to your .env file in production!
MONGO_URI = "mongodb+srv://admin:(!#Krypton1!#)@cluster0.snwbrpt.mongodb.net/?appName=Cluster0"

# --- EMAIL CONFIG (Titan/GoDaddy) ---
SMTP_SERVER = os.getenv("MAIL_SERVER", "smtp.titan.email")
SMTP_PORT = int(os.getenv("MAIL_PORT", 587))
SMTP_USERNAME = os.getenv("MAIL_USERNAME", "kryptonaxofficial@kryptonax.com")
SMTP_PASSWORD = os.getenv("MAIL_PASSWORD", "(!#Kryptonaxofficial1!#)")
SMTP_FROM = os.getenv("MAIL_FROM", "kryptonaxofficial@kryptonax.com")

# --- SETUP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = pymongo.MongoClient(MONGO_URI)
db = client["kryptonax"]
users_collection = db["users"]
subscriptions_collection = db["subscriptions"]
news_collection = db["news_articles"]
fav_collection = db["favorites"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- MODELS ---
class UserRegister(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    mobile: str

class UserCreate(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    mobile: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    username: str
    otp: str
    new_password: str

# --- HELPERS ---
def get_password_hash(password): 
    return pwd_context.hash(password)

def verify_password(plain, hashed): 
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(days=7)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# --- CURRENT USER HELPER (Optional Auth) ---
def get_current_user(token: str = Depends(oauth2_scheme)):
    # If no token provided, return guest user
    if not token:
        return {"username": "guest", "is_guest": True}
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return {"username": "guest", "is_guest": True}
    except JWTError:
        return {"username": "guest", "is_guest": True}
    
    user = users_collection.find_one({"username": username})
    if user is None:
        return {"username": "guest", "is_guest": True}
    return user

# --- EMAIL FUNCTIONS ---
def send_email_otp(to_email, otp):
    print(f"📧 Attempting to send OTP email to {to_email}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = "Kryptonax Password Reset OTP"

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #2962ff;">Kryptonax Security</h2>
                <p>You requested to reset your password.</p>
                <p>Your One-Time Password (OTP) is:</p>
                <h1 style="background-color: #f4f4f4; padding: 10px; display: inline-block; letter-spacing: 5px; color: #000;">{otp}</h1>
                <p>This code is valid for 10 minutes.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        print(f"🔌 Connecting to SMTP {SMTP_SERVER}:{SMTP_PORT} (SSL, timeout=30s)...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
        print(f"🔐 Authenticating with {SMTP_USERNAME}...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print(f"📤 Sending message...")
        server.send_message(msg)
        server.quit()

        print(f"✅ OTP email successfully sent to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP AUTH FAILED: Invalid credentials. Error: {e}")
        print(f"   Username: {SMTP_USERNAME}")
        print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
        return False
    except TimeoutError as e:
        print(f"❌ TIMEOUT: Cannot reach {SMTP_SERVER}:{SMTP_PORT}. Check MAIL_SERVER in .env")
        print(f"   GoDaddy Standard Email: smtpout.secureserver.net (port 465)")
        print(f"   Verify credentials are correct")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ EMAIL FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_welcome_email(email_to: str, ticker: str):
    html = f"""
    <h3>Kryptonax Alert</h3>
    <p>You are now subscribed to updates for: <b>{ticker}</b></p>
    <p>We will notify you on significant market movement via email.</p>
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM
        msg['To'] = email_to
        msg['Subject'] = f"Alert Subscribed: {ticker}"
        msg.attach(MIMEText(html, 'html'))
        
        print(f"🔌 Connecting to SMTP {SMTP_SERVER}:{SMTP_PORT} (SSL, timeout=30s)...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
        print(f"🔐 Authenticating with {SMTP_USERNAME}...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print(f"📤 Sending message...")
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Welcome email sent to {email_to} for {ticker}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP AUTH FAILED: Invalid credentials. Error: {e}")
        print(f"   Username: {SMTP_USERNAME}")
        print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
        return False
    except TimeoutError as e:
        print(f"❌ TIMEOUT: Cannot reach {SMTP_SERVER}:{SMTP_PORT}. Check MAIL_SERVER in .env")
        print(f"   GoDaddy Standard Email: smtpout.secureserver.net (port 465)")
        print(f"   Verify credentials are correct")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ Welcome email error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
def send_sms_otp_simulated(mobile, otp):
    print("\n" + "="*40)
    print(f"📱 SMS SIMULATION TO: {mobile}")
    print(f"🔑 OTP MESSAGE: Your Kryptonax code is: [{otp}]")
    print("="*40 + "\n")

# ==========================================
#               ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {"message": "Kryptonax API Live"}

# --- AUTH ENDPOINTS ---

@app.post("/register")
def register(user: UserRegister):
    clean_username = user.username.lower().strip()
    if users_collection.find_one({"username": clean_username}):
        raise HTTPException(status_code=400, detail="Email already registered")
    users_collection.insert_one({
        "username": clean_username,
        "password": get_password_hash(user.password),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "mobile": user.mobile
    })
    return {"message": "User created successfully"}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    clean_username = form_data.username.lower().strip()
    user = users_collection.find_one({"username": clean_username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    token = create_access_token(data={"sub": user["username"]})
    user_name = user.get("first_name", "User")
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user_name": user_name
    }

# --- FORGOT PASSWORD FLOW ---

@app.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    clean_username = req.username.lower().strip()
    user = users_collection.find_one({"username": clean_username})
    
    if not user:
        print(f"⚠️ Forgot Password request for non-existent user: {clean_username}")
        return {"message": "If account exists, OTP sent."}
    
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Update DB
    users_collection.update_one(
        {"username": clean_username},
        {"$set": {"otp_code": otp, "otp_expiry": expiry}}
    )
    
    # 1. Send SMS (Simulated)
    if "mobile" in user:
        send_sms_otp_simulated(user["mobile"], otp)
        
    # 2. Send Email (Real)
    send_email_otp(clean_username, otp)
        
    return {"message": "OTP sent to registered email and mobile"}

@app.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    clean_username = req.username.lower().strip()
    user = users_collection.find_one({"username": clean_username})
    
    if not user: 
        raise HTTPException(status_code=400, detail="User not found")
    
    # DEBUGGING: Print what is happening
    received_otp = req.otp.strip()
    stored_otp = user.get("otp_code")
    
    print(f"🔍 DEBUG RESET: User={clean_username} | Stored OTP='{stored_otp}' | Input OTP='{received_otp}'")

    if not stored_otp:
        raise HTTPException(status_code=400, detail="No OTP request found. Request a new one.")
        
    if stored_otp != received_otp:
        print("❌ OTP Mismatch!")
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    if "otp_expiry" in user and datetime.utcnow() > user["otp_expiry"]:
        raise HTTPException(status_code=400, detail="OTP Expired")
        
    # Success - Reset Password
    new_hashed = get_password_hash(req.new_password)
    users_collection.update_one(
        {"username": clean_username},
        {"$set": {"password": new_hashed}, "$unset": {"otp_code": "", "otp_expiry": ""}}
    )
    print("✅ Password reset successful")
    
    return {"message": "Password reset successful! Please login."}

# --- SUBSCRIBE ENDPOINTS (BELL ICON LOGIC) ---

# 1. SUBSCRIBE (Enable Bell)
@app.post("/subscribe/{ticker}", status_code=status.HTTP_201_CREATED)
def subscribe_to_ticker(ticker: str, current_user: dict = Depends(get_current_user)):
    username = current_user.get("username", "guest")
    
    # Check if already subscribed
    existing = subscriptions_collection.find_one({
        "username": username,
        "ticker": ticker
    })
    
    if existing:
        return {"message": f"Already subscribed to {ticker}"}

    # Add subscription to DB
    subscriptions_collection.insert_one({
        "username": username,
        "ticker": ticker
    })
    
    # Send Email Notification
    send_welcome_email(username, ticker)
    
    return {"message": f"Successfully subscribed to {ticker}"}

# 2. UNSUBSCRIBE (Disable Bell)
@app.delete("/subscribe/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe_from_ticker(ticker: str, current_user: dict = Depends(get_current_user)):
    username = current_user.get("username", "guest")

    # Delete subscription from DB
    result = subscriptions_collection.delete_one({
        "username": username,
        "ticker": ticker
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return

# 3. GET FAVORITES (Restore Bell State on Refresh)
@app.get("/favorites")
def get_favorites(current_user: dict = Depends(get_current_user)):
    username = current_user.get("username", "guest")
    
    # Find all tickers this user is subscribed to
    subs = list(subscriptions_collection.find({"username": username}))
    
    # Also get watchlist favorites with live prices
    fav_tickers = [doc["ticker"] for doc in fav_collection.find({"username": username})]
    results = [{"ticker": sub["ticker"]} for sub in subs]
    
    # Add watchlist favorites with live prices
    if fav_tickers:
        try:
            stocks = yf.Tickers(" ".join(fav_tickers))
            for t in fav_tickers:
                try:
                    info = stocks.tickers[t].fast_info
                    results.append({
                        "ticker": t,
                        "price": round(info.last_price, 2),
                        "change": round(info.last_price - info.previous_close, 2),
                        "percent": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2)
                    })
                except:
                    pass
        except:
            pass
    
    return results

# 4. Add a stock to favorites (Watchlist)
@app.post("/favorites/{ticker}")
def add_favorite(ticker: str, current_user: dict = Depends(get_current_user)):
    username = current_user.get("username", "guest")
    ticker = ticker.upper()
    existing = fav_collection.find_one({"username": username, "ticker": ticker})
    if existing:
        return {"message": "Already in watchlist"}
    
    fav_collection.insert_one({
        "username": username,
        "ticker": ticker,
        "added_at": datetime.utcnow()
    })
    return {"message": f"Added {ticker} to watchlist"}

# 5. Remove a stock from favorites
@app.delete("/favorites/{ticker}")
def remove_favorite(ticker: str, current_user: dict = Depends(get_current_user)):
    username = current_user.get("username", "guest")
    ticker = ticker.upper()
    result = fav_collection.delete_one({"username": username, "ticker": ticker})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ticker not found in watchlist")
    return {"message": f"Removed {ticker}"}

# --- DATA ENDPOINTS (Condensed) ---
def fetch_from_api_and_save(ticker):
    search_query = ticker.replace(".NS", "").replace(".BO", "")
    mappings = { "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services", "INFY": "Infosys", "HDFCBANK": "HDFC Bank", "BTC-USD": "Bitcoin Crypto", "GC=F": "Gold Price", "SI=F": "Silver Price" }
    if search_query in mappings: search_query = mappings[search_query]
    try:
        url = f"https://newsapi.org/v2/everything?q={search_query}&apiKey={API_KEY}&language=en&sortBy=publishedAt&from={(datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')}&pageSize=50"
        data = requests.get(url).json(); articles = data.get("articles", [])
        if articles:
            news_collection.delete_many({"ticker": ticker})
            for a in articles: a["ticker"] = ticker; a["fetched_at"] = datetime.now(); a["sentiment"] = get_sentiment(a.get("title", "")[:200])
            news_collection.insert_many(articles)
        return articles
    except: return []

@app.get("/news/general")
def get_general_news():
    cached = list(news_collection.find({"ticker": "GENERAL_TRENDING"}, {"_id": 0}).sort("publishedAt", -1))
    if not cached or (datetime.now() - cached[0]["fetched_at"]).seconds > 21600:
        try:
            url = f"https://newsapi.org/v2/everything?q=stock market OR economy OR crypto&apiKey={API_KEY}&language=en&sortBy=publishedAt&pageSize=40"
            articles = requests.get(url).json().get("articles", [])
            if articles:
                news_collection.delete_many({"ticker": "GENERAL_TRENDING"})
                for a in articles: a["ticker"] = "GENERAL_TRENDING"; a["fetched_at"] = datetime.now(); a["sentiment"] = get_sentiment(a.get("title", "")[:200])
                news_collection.insert_many(articles)
                return articles
        except: pass
    return cached

@app.get("/news/{ticker}")
def get_news(ticker: str, period: str = "30d"): 
    ticker = ticker.upper()
    if news_collection.count_documents({"ticker": ticker}) < 5: fetch_from_api_and_save(ticker)
    all_news = list(news_collection.find({"ticker": ticker}, {"_id": 0}).sort("publishedAt", -1))
    filtered = []
    limit = int(period.replace("d", "")) if "d" in period else 30
    for n in all_news:
        if (datetime.now() - datetime.strptime(n['publishedAt'][:10], '%Y-%m-%d')).days <= (2 if limit==1 else limit): filtered.append(n)
    return filtered if filtered else all_news

@app.get("/quote/{ticker}")
def get_current_price(ticker: str):
    try:
        info = yf.Ticker(ticker.upper()).fast_info
        return {"symbol": ticker.upper(), "price": round(info.last_price, 2), "change": round(info.last_price - info.previous_close, 2), "percent": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2), "currency": info.currency}
    except: return {"price": 0, "change": 0, "percent": 0, "currency": "USD"}

@app.post("/api/quotes")
def get_batch_quotes(tickers: List[str] = Body(...)):
    results = {}
    if not tickers: return results
    try:
        stocks = yf.Tickers(" ".join(tickers))
        for t in tickers:
            try:
                i = stocks.tickers[t].fast_info
                results[t] = {"price": round(i.last_price, 2), "change": round(i.last_price - i.previous_close, 2), "percent": round(((i.last_price - i.previous_close) / i.previous_close)*100, 2), "color": "#00e676" if i.last_price >= i.previous_close else "#ff1744"}
            except: results[t] = None
    except: pass
    return results

@app.get("/history/{ticker}")
def get_stock_history(ticker: str, period: str = "1mo"):
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period, interval="1m" if period == "1d" else "15m" if period == "5d" else "1d")
        data = [{"date": date.strftime('%H:%M') if period=="1d" else date.strftime('%Y-%m-%d'), "price": row['Close']} for date, row in hist.iterrows()]
        return {"currency": "USD", "data": data}
    except: return {"currency": "USD", "data": []}

@app.get("/api/search/{query}")
def search_tickers(query: str):
    try:
        r = requests.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={query}", headers={'User-Agent': 'Mozilla/5.0'}).json()
        return [{"symbol": i['symbol'], "name": i.get('shortname', i['symbol']), "exchange": i.get('exchange', 'Unknown')} for i in r.get('quotes', []) if 'symbol' in i][:8]
    except: return []

@app.get("/trending")
def get_global_trending():
    data = []
    for t in ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "AMD", "BTC-USD", "GC=F"]:
        try:
            i = yf.Ticker(t).fast_info
            change = ((i.last_price - i.previous_close)/i.previous_close)*100
            data.append({"ticker": t, "change": round(change, 2), "price": round(i.last_price, 2)})
        except: continue
    return sorted(data, key=lambda x: abs(x['change']), reverse=True)

