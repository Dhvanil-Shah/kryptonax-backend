# from fastapi import FastAPI, HTTPException, Body, Depends, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# import requests
# import pymongo
# from datetime import datetime, timedelta
# import yfinance as yf
# from ai import get_sentiment 
# from typing import List
# import google.generativeai as genai
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

# # --- AI / LLM CONFIG (Google Gemini) ---
# SYSTEM_PROMPT = """You are an intelligent financial AI assistant for Kryptonax platform.
# You have expertise in:
# - Company news analysis and market sentiment
# - Board member profiles and their expertise
# - Company history and capability assessment
# - Stock market trends and technical analysis
# - Cryptocurrency and commodities markets

# Provide accurate, concise, and professional financial insights.
# When discussing companies, mention relevant sectors, market cap, recent news highlights, and sentiment.
# Always cite data-driven insights when available."""

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
# gemini_model = None

# def resolve_gemini_model_name(preferred: str) -> str:
#     preferred = (preferred or "").strip()
#     candidates = []
#     if preferred:
#         candidates.append(preferred)
#         if preferred.startswith("models/"):
#             candidates.append(preferred.replace("models/", "", 1))
#         else:
#             candidates.append(f"models/{preferred}")

#     try:
#         models = list(genai.list_models())
#         available = {m.name for m in models}

#         for name in candidates:
#             if name in available:
#                 return name

#         priority = [
#             "models/gemini-1.5-flash",
#             "models/gemini-1.5-pro",
#             "models/gemini-1.5-flash-latest",
#             "models/gemini-1.5-pro-latest",
#             "models/gemini-pro",
#         ]
#         for name in priority:
#             if name in available:
#                 return name

#         for m in models:
#             if "generateContent" in getattr(m, "supported_generation_methods", []):
#                 return m.name
#     except Exception as e:
#         print(f"⚠️ Gemini model discovery failed: {e}")

#     return preferred or "gemini-1.5-flash"

# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)
#     resolved_model = resolve_gemini_model_name(GEMINI_MODEL)
#     print(f"✅ Gemini model resolved: {resolved_model}")
#     gemini_model = genai.GenerativeModel(
#         model_name=resolved_model,
#         system_instruction=SYSTEM_PROMPT
#     )

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

# class ChatMessage(BaseModel):
#     role: str  # "user" or "bot"
#     message: str

# class ChatRequest(BaseModel):
#     user_message: str
#     ticker: str = None  # Optional company ticker for context
#     history: List[ChatMessage] = []  # Previous messages for context

# class ChatResponse(BaseModel):
#     response: str
#     role: str = "bot"
#     history: List[ChatMessage] = []

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
# def get_general_news(category: str = "all"):
#     """Return general trending news. Optional `category` filters: all, gold, stocks, mutual_fund, crypto, real_estate."""
#     # Try cached
#     cached = list(news_collection.find({"ticker": "GENERAL_TRENDING"}, {"_id": 0}).sort("publishedAt", -1))
#     need_refresh = False
#     if not cached:
#         need_refresh = True
#     else:
#         try:
#             if (datetime.now() - cached[0]["fetched_at"]).seconds > 21600:
#                 need_refresh = True
#         except:
#             need_refresh = True

#     if need_refresh:
#         try:
#             q = "stock market OR economy OR crypto OR gold OR mutual fund OR real estate"
#             url = f"https://newsapi.org/v2/everything?q={q}&apiKey={API_KEY}&language=en&sortBy=publishedAt&pageSize=60"
#             articles = requests.get(url).json().get("articles", [])
#             if articles:
#                 # annotate and cache
#                 news_collection.delete_many({"ticker": "GENERAL_TRENDING"})
#                 enriched = []
#                 for a in articles:
#                     a["ticker"] = "GENERAL_TRENDING"
#                     a["fetched_at"] = datetime.utcnow()
#                     a["sentiment"] = get_sentiment(a.get("title", "")[:200])
#                     a_cat = None
#                     txt = ((a.get("title") or "") + " " + (a.get("description") or "")).lower()
#                     if "gold" in txt:
#                         a_cat = "gold"
#                     elif any(x in txt for x in ["crypto", "bitcoin", "ethereum", "btc", "eth", "coin"]):
#                         a_cat = "crypto"
#                     elif any(x in txt for x in ["mutual fund", "mutual funds", "sip", "nav", "aum", "fund house", "mf "]):
#                         a_cat = "mutual_fund"
#                     elif any(x in txt for x in ["real estate", "property", "mortgage", "housing", "realty", "reit"]):
#                         a_cat = "real_estate"
#                     elif any(x in txt for x in ["stock", "shares", "ipo", "earnings", "revenue", "acquisition", "merger"]):
#                         a_cat = "stocks"
#                     else:
#                         a_cat = "all"
#                     a["category"] = a_cat

#                     # simple entity inference
#                     entity = ""
#                     if a_cat == "stocks":
#                         if any(x in txt for x in ["bank", "hdfc", "icici", "sbi", "banking"]): entity = "Sector: Banking"
#                         elif any(x in txt for x in ["oil", "energy", "exxon", "bp", "chevron"]): entity = "Sector: Energy"
#                         elif any(x in txt for x in ["tech", "software", "microsoft", "apple", "google", "tcs", "infosys"]): entity = "Sector: Technology"
#                         elif any(x in txt for x in ["auto", "tesla", "ford", "gm"]): entity = "Sector: Automotive"
#                     if a_cat == "mutual_fund":
#                         if any(x in txt for x in ["equity", "large cap", "large-cap"]): entity = "Fund Type: Equity / Large Cap"
#                         elif any(x in txt for x in ["debt", "bond"]): entity = "Fund Type: Debt"
#                         elif "hybrid" in txt: entity = "Fund Type: Hybrid"
#                         elif "sip" in txt: entity = "Fund Feature: SIP"
#                     a["entity_info"] = entity

#                     enriched.append(a)

#                 if enriched:
#                     # insert enriched with fetched_at as datetime
#                     for doc in enriched:
#                         news_collection.insert_one(doc)
#                     cached = enriched
#         except Exception as e:
#             print("Error fetching general news:", e)

#     # If category requested, filter cached
#     if category and category != "all":
#         try:
#             return [a for a in cached if a.get("category") == category]
#         except:
#             return cached

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
# def get_global_trending(region: str = "all"):
#     """Return trending movers. Optional `region` param: all, india, us"""
#     pools = {
#         "all": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "AMD", "BTC-USD", "GC=F"],
#         "india": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
#         "us": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "AMD", "META", "NFLX"]
#     }
#     tickers = pools.get(region.lower(), pools["all"])
#     data = []
#     for t in tickers:
#         try:
#             i = yf.Ticker(t).fast_info
#             change = ((i.last_price - i.previous_close)/i.previous_close)*100
#             data.append({"ticker": t, "change": round(change, 2), "price": round(i.last_price, 2)})
#         except Exception:
#             continue
#     return sorted(data, key=lambda x: abs(x['change']), reverse=True)

# # ==========================================
# #          AI CHATBOT ENDPOINT
# # ==========================================

# @app.post("/chat", response_model=ChatResponse)
# def chat_with_bot(request: ChatRequest):
#     """
#     AI Chatbot endpoint for discussing company news, history, board members, capabilities.
#     Accepts user message and optional ticker for context.
#     Uses Google Gemini API to generate intelligent financial insights.
#     """
#     if not gemini_model:
#         raise HTTPException(status_code=500, detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
    
#     try:
#         # Build conversation history for context (Gemini format)
#         messages = []
        
#         # Add conversation history if provided
#         if request.history:
#             for msg in request.history[-10:]:  # Keep last 10 messages for context window
#                 role = "user" if msg.role == "user" else "model"
#                 messages.append({
#                     "role": role,
#                     "parts": [msg.message]
#                 })
        
#         # Fetch relevant context if ticker is provided
#         context = ""
#         if request.ticker:
#             try:
#                 ticker_obj = yf.Ticker(request.ticker)
#                 info = ticker_obj.info
#                 company_name = info.get("longName", request.ticker)
#                 sector = info.get("sector", "N/A")
#                 market_cap = info.get("marketCap", "N/A")
#                 pe_ratio = info.get("trailingPE", "N/A")
                
#                 # Fetch recent news for this ticker
#                 recent_news = news_collection.find_one({"ticker": request.ticker}) or {}
#                 recent_articles = recent_news.get("articles", [])[:3]
                
#                 context = f"\nContext: Company={company_name}, Sector={sector}, MarketCap={market_cap}, P/E={pe_ratio}\n"
#                 if recent_articles:
#                     context += "Recent News:\n"
#                     for article in recent_articles:
#                         context += f"- {article.get('title', 'No title')}\n"
                
#                 # Add sentiment analysis if available
#                 sentiment_data = news_collection.find_one({"ticker": request.ticker, "sentiment": {"$exists": True}})
#                 if sentiment_data:
#                     sentiment = sentiment_data.get("sentiment", {})
#                     context += f"Market Sentiment: Positive={sentiment.get('positive', 0):.1%}, Negative={sentiment.get('negative', 0):.1%}\n"
#             except Exception as e:
#                 context = f"\n(Note: Unable to fetch detailed context for {request.ticker}: {str(e)})\n"
        
#         # Prepare user message with context
#         user_message = request.user_message
#         if context:
#             user_message = user_message + context
        
#         # Add current user message to conversation
#         messages.append({
#             "role": "user",
#             "parts": [user_message]
#         })
        
#         # Call Gemini API
#         response = gemini_model.generate_content(
#             messages,
#             generation_config={
#                 "temperature": 0.7,
#                 "max_output_tokens": 500
#             }
#         )
        
#         bot_response = response.text if hasattr(response, "text") else ""
        
#         # Build updated history
#         updated_history = list(request.history) if request.history else []
#         updated_history.append(ChatMessage(role="user", message=request.user_message))
#         updated_history.append(ChatMessage(role="bot", message=bot_response))
        
#         return ChatResponse(
#             response=bot_response,
#             role="bot",
#             history=updated_history
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Chat error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


# if __name__ == "__main__":
#     # Use this guarded runner on Windows to avoid multiprocessing/reload recursion
#     import uvicorn
#     uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI, HTTPException, Body, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import requests
import pymongo
from datetime import datetime, timedelta
import yfinance as yf
from ai import get_sentiment 
from typing import List, Dict
import google.generativeai as genai
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
import time

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()

# ===== CACHING TO AVOID RATE LIMITS =====
company_cache: Dict[str, Dict] = {}
CACHE_TTL = 3600  # Cache for 1 hour to reduce Yahoo Finance API calls

# --- CONFIGURATION ---
API_KEY = "9f07c51e4e2145569ccba561e4e0d81a" 
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

# --- AI / LLM CONFIG (Google Gemini) ---
SYSTEM_PROMPT = """You are an intelligent financial AI assistant for Kryptonax platform.
You have expertise in:
- Company news analysis and market sentiment
- Board member profiles and their expertise
- Company history and capability assessment
- Stock market trends and technical analysis
- Cryptocurrency and commodities markets

Provide accurate, concise, and professional financial insights.
When discussing companies, mention relevant sectors, market cap, recent news highlights, and sentiment.
Always cite data-driven insights when available."""

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
gemini_model = None

def resolve_gemini_model_name(preferred: str) -> str:
    preferred = (preferred or "").strip()
    candidates = []
    if preferred:
        candidates.append(preferred)
        if preferred.startswith("models/"):
            candidates.append(preferred.replace("models/", "", 1))
        else:
            candidates.append(f"models/{preferred}")

    try:
        models = list(genai.list_models())
        available = {m.name for m in models}

        for name in candidates:
            if name in available:
                return name

        priority = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro-latest",
            "models/gemini-pro",
        ]
        for name in priority:
            if name in available:
                return name

        for m in models:
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                return m.name
    except Exception as e:
        print(f"⚠️ Gemini model discovery failed: {e}")

    return preferred or "gemini-1.5-flash"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    resolved_model = resolve_gemini_model_name(GEMINI_MODEL)
    print(f"✅ Gemini model resolved: {resolved_model}")
    gemini_model = genai.GenerativeModel(
        model_name=resolved_model,
        system_instruction=SYSTEM_PROMPT
    )

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

class ChatMessage(BaseModel):
    role: str  # "user" or "bot"
    message: str

class ChatRequest(BaseModel):
    user_message: str
    ticker: str = None  # Optional company ticker for context
    history: List[ChatMessage] = []  # Previous messages for context

class ChatResponse(BaseModel):
    response: str
    role: str = "bot"
    history: List[ChatMessage] = []

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
def get_general_news(category: str = "all", regions: str = "all", states: str = ""):
    """
    Return general trending news with region/state filtering.
    - category: all, gold, stocks, mutual_fund, crypto, real_estate
    - regions: comma-separated list (e.g., "india,us") or "all"
    - states: JSON string mapping regions to states
    """
    import json
    
    # Create cache key based on regions
    cache_key = f"GENERAL_TRENDING_{regions.replace(',', '_')}" if regions != "all" else "GENERAL_TRENDING"
    
    # Try cached
    cached = list(news_collection.find({"ticker": cache_key}, {"_id": 0}).sort("publishedAt", -1))
    need_refresh = False
    if not cached:
        need_refresh = True
    else:
        try:
            # Shorter cache for region-specific queries (1 hour vs 6 hours)
            cache_duration = 3600 if regions != "all" else 21600
            if (datetime.now() - cached[0]["fetched_at"]).seconds > cache_duration:
                need_refresh = True
        except:
            need_refresh = True

    if need_refresh:
        try:
            # Adjust search query based on regions
            region_keywords = ""
            if regions and regions != "all":
                region_list = regions.split(",")
                if "india" in region_list:
                    region_keywords += " (India OR Mumbai OR Delhi OR Bangalore OR NSE OR BSE OR Sensex OR Nifty OR Rupee OR RBI)"
                if "us" in region_list:
                    region_keywords += " (USA OR America OR NYSE OR NASDAQ OR 'Wall Street' OR 'Federal Reserve')"
                if "uk" in region_list:
                    region_keywords += " (UK OR Britain OR London OR LSE OR FTSE)"
                if "japan" in region_list:
                    region_keywords += " (Japan OR Tokyo OR Nikkei)"
                if "china" in region_list:
                    region_keywords += " (China OR Beijing OR Shanghai OR 'Hong Kong')"
                if "canada" in region_list:
                    region_keywords += " (Canada OR Toronto OR TSX)"
                if "germany" in region_list:
                    region_keywords += " (Germany OR Berlin OR Frankfurt OR DAX)"
                if "france" in region_list:
                    region_keywords += " (France OR Paris OR 'CAC 40')"
            
            q = f"(stock market OR economy OR crypto OR gold OR 'mutual fund' OR 'real estate'){region_keywords}"
            url = f"https://newsapi.org/v2/everything?q={q}&apiKey={API_KEY}&language=en&sortBy=publishedAt&pageSize=100"
            articles = requests.get(url).json().get("articles", [])
            
            if articles:
                # annotate and cache
                news_collection.delete_many({"ticker": cache_key})
                enriched = []
                for a in articles:
                    a["ticker"] = cache_key
                    a["fetched_at"] = datetime.utcnow()
                    a["sentiment"] = get_sentiment(a.get("title", "")[:200])
                    a_cat = None
                    txt = ((a.get("title") or "") + " " + (a.get("description") or "")).lower()
                    
                    # Categorize news
                    if "gold" in txt:
                        a_cat = "gold"
                    elif any(x in txt for x in ["crypto", "bitcoin", "ethereum", "btc", "eth", "coin"]):
                        a_cat = "crypto"
                    elif any(x in txt for x in ["mutual fund", "mutual funds", "sip", "nav", "aum", "fund house", "mf "]):
                        a_cat = "mutual_fund"
                    elif any(x in txt for x in ["real estate", "property", "mortgage", "housing", "realty", "reit"]):
                        a_cat = "real_estate"
                    elif any(x in txt for x in ["stock", "shares", "ipo", "earnings", "revenue", "acquisition", "merger"]):
                        a_cat = "stocks"
                    else:
                        a_cat = "all"
                    a["category"] = a_cat

                    # Detect region from content
                    detected_regions = []
                    if any(x in txt for x in ["india", "mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad", "pune", "ahmedabad", "surat", "nse", "bse", "sensex", "nifty", "rupee", "rbi", "sebi", "indian", "bharat", "bengaluru", "gurgaon", "noida"]):
                        detected_regions.append("india")
                    if any(x in txt for x in ["usa", "america", "american", "us ", " us.", "nyse", "nasdaq", "dow jones", "wall street", "federal reserve", "fed ", "s&p 500", "california", "new york", "texas", "florida"]):
                        detected_regions.append("us")
                    if any(x in txt for x in ["uk", "britain", "british", "london", "lse", "ftse", "england", "scotland", "wales"]):
                        detected_regions.append("uk")
                    if any(x in txt for x in ["japan", "japanese", "tokyo", "nikkei", "osaka", "yen", "boj"]):
                        detected_regions.append("japan")
                    if any(x in txt for x in ["china", "chinese", "beijing", "shanghai", "hong kong", "yuan", "pboc", "shenzhen"]):
                        detected_regions.append("china")
                    if any(x in txt for x in ["canada", "canadian", "toronto", "vancouver", "tsx", "ottawa"]):
                        detected_regions.append("canada")
                    if any(x in txt for x in ["germany", "german", "berlin", "munich", "frankfurt", "dax", "euro", "bundesbank"]):
                        detected_regions.append("germany")
                    if any(x in txt for x in ["france", "french", "paris", "cac 40", "lyon", "marseille"]):
                        detected_regions.append("france")
                    
                    a["regions"] = detected_regions if detected_regions else ["all"]

                    # simple entity inference
                    entity = ""
                    if a_cat == "stocks":
                        if any(x in txt for x in ["bank", "hdfc", "icici", "sbi", "banking"]): entity = "Sector: Banking"
                        elif any(x in txt for x in ["oil", "energy", "exxon", "bp", "chevron"]): entity = "Sector: Energy"
                        elif any(x in txt for x in ["tech", "software", "microsoft", "apple", "google", "tcs", "infosys"]): entity = "Sector: Technology"
                        elif any(x in txt for x in ["auto", "tesla", "ford", "gm"]): entity = "Sector: Automotive"
                    if a_cat == "mutual_fund":
                        if any(x in txt for x in ["equity", "large cap", "large-cap"]): entity = "Fund Type: Equity / Large Cap"
                        elif any(x in txt for x in ["debt", "bond"]): entity = "Fund Type: Debt"
                        elif "hybrid" in txt: entity = "Fund Type: Hybrid"
                        elif "sip" in txt: entity = "Fund Feature: SIP"
                    a["entity_info"] = entity

                    enriched.append(a)

                if enriched:
                    # insert enriched with fetched_at as datetime
                    for doc in enriched:
                        news_collection.insert_one(doc)
                    cached = enriched
        except Exception as e:
            print("Error fetching general news:", e)

    # Filter by category
    filtered_news = cached
    if category and category != "all":
        try:
            filtered_news = [a for a in cached if a.get("category") == category]
        except:
            filtered_news = cached
    
    # Filter by regions
    if regions and regions != "all":
        region_list = [r.strip().lower() for r in regions.split(",")]
        filtered_news = [
            a for a in filtered_news 
            if (
                # Article has detected regions that match requested regions
                any(r in a.get("regions", []) for r in region_list) 
                # OR article is marked as "all" (global/generic)
                or "all" in a.get("regions", [])
            )
        ]
        
        # If specific regions requested and we have articles, prioritize region-specific over "all"
        if filtered_news and len(region_list) > 0 and "all" not in region_list:
            # Separate region-specific from generic
            region_specific = [a for a in filtered_news if "all" not in a.get("regions", [])]
            generic = [a for a in filtered_news if "all" in a.get("regions", [])]
            
            # Prefer region-specific, but include some generic if not enough content
            if len(region_specific) >= 10:
                filtered_news = region_specific[:30]  # Limit to 30 region-specific
            else:
                filtered_news = region_specific + generic[:10]  # Mix both
    
    # Parse states filter if provided (for future enhancement)
    states_filter = {}
    if states:
        try:
            states_filter = json.loads(states)
        except:
            pass
    
    # TODO: Add state-level filtering when geographic data is available
    # For now, we return region-filtered results
    
    return filtered_news

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
def get_global_trending(regions: str = "all", states: str = ""):
    """
    Return trending movers. 
    - regions: comma-separated list (e.g., "india,us") or "all"
    - states: JSON string mapping regions to states (e.g., '{"india":["Maharashtra","Delhi"]}')
    """
    import json
    
    # Define region-specific ticker pools
    pools = {
        "all": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "AMD", "BTC-USD", "GC=F", "GOLD", "SILVER"],
        "india": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "WIPRO.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"],
        "us": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "AMD", "META", "NFLX", "JPM", "V", "WMT"],
        "uk": ["BP.L", "HSBA.L", "SHEL.L", "AZN.L", "ULVR.L", "GSK.L", "DGE.L", "RIO.L", "BARC.L"],
        "japan": ["7203.T", "6758.T", "9984.T", "6861.T", "6902.T", "8306.T", "9432.T"],  # Toyota, Sony, SoftBank, etc.
        "china": ["BABA", "BIDU", "JD", "PDD", "NIO", "XPEV", "LI"]  # ADRs for Chinese companies
    }
    
    # Parse states filter if provided
    states_filter = {}
    if states:
        try:
            states_filter = json.loads(states)
        except:
            pass
    
    # Determine which tickers to fetch
    selected_tickers = []
    if regions == "all" or not regions:
        selected_tickers = pools["all"]
    else:
        region_list = [r.strip().lower() for r in regions.split(",")]
        for region in region_list:
            if region in pools:
                selected_tickers.extend(pools[region])
    
    # Remove duplicates
    selected_tickers = list(set(selected_tickers))
    
    # Fetch data for all selected tickers
    data = []
    for t in selected_tickers:
        try:
            i = yf.Ticker(t).fast_info
            change = ((i.last_price - i.previous_close)/i.previous_close)*100
            
            # Determine region for this ticker
            ticker_region = "all"
            for region, region_tickers in pools.items():
                if t in region_tickers and region != "all":
                    ticker_region = region
                    break
            
            data.append({
                "ticker": t, 
                "change": round(change, 2), 
                "price": round(i.last_price, 2),
                "region": ticker_region
            })
        except Exception:
            continue
    
    # Note: State filtering would require more specific data sources
    # For now, we return region-filtered results
    # TODO: Integrate state-specific market indices or company headquarters data
    
    return sorted(data, key=lambda x: abs(x['change']), reverse=True)

# ==========================================
#       COMPANY DETAILS ENDPOINTS
# ==========================================

# Helper function to fetch Wikipedia photos
def get_wikipedia_photo(name: str) -> str:
    """
    Fetch professional photo from Wikipedia for a person.
    Falls back to initials avatar if not found.
    """
    try:
        # Clean the name for Wikipedia search
        search_name = name.strip().replace(' ', '_')
        
        # Try Wikipedia API
        wiki_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'titles': search_name,
            'prop': 'pageimages|extracts',
            'format': 'json',
            'pithumbsize': '500',
            'redirects': 1
        }
        
        response = requests.get(wiki_url, params=params, timeout=5)
        data = response.json()
        
        # Extract image from Wikipedia response
        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if 'thumbnail' in page_data:
                photo_url = page_data['thumbnail']['source']
                # Verify the URL is accessible
                if photo_url and photo_url.startswith('http'):
                    return photo_url
        
        # If no Wikipedia image found, try Wikidata
        return get_wikidata_photo(name)
        
    except Exception as e:
        # Silently fail and return initials avatar
        return None

def get_wikidata_photo(name: str) -> str:
    """Fetch professional photo from Wikidata as secondary source."""
    try:
        search_name = name.strip()
        
        # Wikidata API search
        wikidata_url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbsearchentities',
            'search': search_name,
            'language': 'en',
            'format': 'json'
        }
        
        response = requests.get(wikidata_url, params=params, timeout=5)
        data = response.json()
        entities = data.get('search', [])
        
        if entities:
            # Get the first entity ID
            entity_id = entities[0]['id']
            
            # Fetch entity details to get image
            entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
            entity_response = requests.get(entity_url, timeout=5)
            entity_data = entity_response.json()
            
            claims = entity_data.get('entities', {}).get(entity_id, {}).get('claims', {})
            
            # Look for image property (P18)
            if 'P18' in claims:
                image_title = claims['P18'][0]['mainsnak']['datavalue']['value']
                # Convert Wikimedia Commons image title to URL
                image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_title}?width=500"
                return image_url
    except Exception:
        pass
    
    return None

def get_avatar_url(name: str) -> str:
    """Generate professional initials-based avatar URL as fallback."""
    name_parts = name.strip().split()
    if len(name_parts) >= 2:
        initials = name_parts[0][0] + name_parts[-1][0]
    else:
        initials = name_parts[0][:2] if name_parts else "U"
    return f"https://ui-avatars.com/api/?name={initials.upper()}&bold=true&background=4FACFE&color=ffffff&size=240&font-size=0.40"


# ==========================================
#     REPORT FETCHING HELPERS
# ==========================================

def get_sec_cik(ticker: str) -> str:
    """Get SEC CIK number for a ticker."""
    try:
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=exclude&count=1&search_text="
        headers = {'User-Agent': 'Kryptonax Research kryptonax@example.com'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            import re
            match = re.search(r'CIK=(\d{10})', response.text)
            if match:
                return match.group(1)
    except:
        pass
    return None

def fetch_sec_reports(ticker: str, year: int, quarter: int) -> dict:
    """Fetch reports from SEC EDGAR for US companies."""
    try:
        cik = get_sec_cik(ticker)
        if not cik:
            return None
            
        headers = {'User-Agent': 'Kryptonax Research kryptonax@example.com'}
        
        # Determine filing type based on quarter
        if quarter == 4:
            form_type = "10-K"  # Annual report
        else:
            form_type = "10-Q"  # Quarterly report
            
        # SEC EDGAR API endpoint
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            filings = data.get('filings', {}).get('recent', {})
            
            # Find matching filing
            for i, form in enumerate(filings.get('form', [])):
                if form == form_type:
                    accession = filings['accessionNumber'][i].replace('-', '')
                    filing_date = filings['filingDate'][i]
                    primary_doc = filings['primaryDocument'][i]
                    
                    # Construct document URL
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{primary_doc}"
                    return {
                        "url": doc_url,
                        "date": filing_date,
                        "source": "SEC EDGAR",
                        "available": True
                    }
    except Exception as e:
        print(f"SEC fetch error: {e}")
    return None

def fetch_yahoo_investor_relations(ticker: str) -> str:
    """Get investor relations page from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        website = info.get('website', '')
        
        if website:
            # Common investor relations URL patterns
            ir_patterns = [
                f"{website}/investor-relations",
                f"{website}/investors",
                f"{website}/en/investor-relations",
                f"{website}/ir",
            ]
            
            for ir_url in ir_patterns:
                try:
                    response = requests.head(ir_url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        return ir_url
                except:
                    continue
    except:
        pass
    return None

def fetch_company_reports_from_web(ticker: str, report_type: str) -> str:
    """Scrape company website for report PDFs."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        website = info.get('website', '')
        
        if not website:
            return None
            
        # Try investor relations page
        ir_url = fetch_yahoo_investor_relations(ticker)
        if ir_url:
            response = requests.get(ir_url, timeout=10)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for PDF links
                keywords = {
                    'annual': ['annual report', '10-k', 'annual general meeting'],
                    'quarterly': ['quarterly report', '10-q', 'q1', 'q2', 'q3', 'q4'],
                    'proxy': ['proxy statement', 'def 14a', 'agm'],
                    'esg': ['sustainability', 'esg', 'corporate responsibility']
                }
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    text = link.get_text().lower()
                    
                    if href.endswith('.pdf'):
                        for keyword in keywords.get(report_type, []):
                            if keyword in text:
                                if not href.startswith('http'):
                                    href = website + href
                                return href
    except Exception as e:
        print(f"Web scraping error: {e}")
    return None

def get_report_with_fallback(ticker: str, report_type: str, year: int, quarter: int) -> dict:
    """Multi-source report fetching with cascading fallback."""
    
    # Attempt 1: SEC EDGAR (US companies only)
    if report_type in ['results', 'quarterly', 'annual']:
        sec_report = fetch_sec_reports(ticker, year, quarter)
        if sec_report:
            return sec_report
    
    # Attempt 2: Yahoo Finance investor relations link
    ir_link = fetch_yahoo_investor_relations(ticker)
    if ir_link:
        return {
            "url": ir_link,
            "date": f"{year}-Q{quarter}",
            "source": "Investor Relations",
            "available": True
        }
    
    # Attempt 3: Company website scraping
    web_report = fetch_company_reports_from_web(ticker, report_type)
    if web_report:
        return {
            "url": web_report,
            "date": f"{year}-Q{quarter}",
            "source": "Company Website",
            "available": True
        }
    
    # Fallback: Report not available
    return {
        "url": None,
        "date": f"{year}-Q{quarter}",
        "source": "Not Available",
        "available": False
    }


# ==========================================
#     COMPANY DETAILS ENDPOINTS
# ==========================================

@app.get("/company-history/{ticker}")
def get_company_history(ticker: str):
    """Fetch company history, founding info, and key milestones."""
    # Check cache first
    cache_key = f"history_{ticker}"
    if cache_key in company_cache:
        cached_data = company_cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            print(f"✅ Returning cached data for {ticker}")
            return cached_data["data"]
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(0.5)
        
        t = yf.Ticker(ticker)
        info = t.info
        
        # Check if we got valid data
        if not info or not info.get("longName"):
            result = {
                "ticker": ticker,
                "company_name": ticker,
                "founded": "N/A",
                "sector": "N/A",
                "industry": "N/A",
                "country": "N/A",
                "website": "N/A",
                "description": "Company information not available from Yahoo Finance. This may be a new listing, a foreign ticker, or the data may not be publicly available.",
                "headquarters": "N/A",
                "employees": "N/A",
                "market_cap": "N/A",
                "beta": "N/A"
            }
        else:
            result = {
                "ticker": ticker,
                "company_name": info.get("longName", ticker),
                "founded": info.get("founded", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "country": info.get("country", "N/A"),
                "website": info.get("website", "N/A"),
                "description": info.get("longBusinessSummary", "No description available"),
                "headquarters": info.get("city", "") + ", " + info.get("state", ""),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "beta": info.get("beta", "N/A")
            }
        
        # Cache the result
        company_cache[cache_key] = {
            "data": result,
            "timestamp": time.time()
        }
        
        return result
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {str(e)}")
        # Return default data instead of raising exception
        return {
            "ticker": ticker,
            "company_name": ticker,
            "founded": "N/A",
            "sector": "N/A",
            "industry": "N/A",
            "country": "N/A",
            "website": "N/A",
            "description": f"Unable to fetch company information. The service may be temporarily unavailable. Please try again later.",
            "headquarters": "N/A",
            "employees": "N/A",
            "market_cap": "N/A",
            "beta": "N/A"
        }


@app.get("/board-members/{ticker}")
def get_board_members(ticker: str):
    """Fetch board members and leadership information with Wikipedia photos."""
    # Check cache first
    cache_key = f"board_{ticker}"
    if cache_key in company_cache:
        cached_data = company_cache[cache_key]
        if time.time() - cached_data["timestamp"] < CACHE_TTL:
            print(f"✅ Returning cached board data for {ticker}")
            return cached_data["data"]
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(0.5)
        
        t = yf.Ticker(ticker)
        info = t.info
        
        # Extract officers data from Yahoo Finance
        officers = []
        owner = None
        chairperson = None
        
        if "companyOfficers" in info and info["companyOfficers"]:
            for i, officer in enumerate(info["companyOfficers"][:12]):
                title = officer.get("title", "N/A").lower()
                name = officer.get("name", "N/A")
                
                # Try to get Wikipedia photo, fallback to initials avatar
                wiki_photo = get_wikipedia_photo(name)
                photo_url = wiki_photo if wiki_photo else get_avatar_url(name)
                
                # Identify owner and chairperson
                if i == 0 and not owner and ("founder" in title or "chairman" in title or "ceo" in title):
                    owner = {
                        "name": name,
                        "title": officer.get("title", "Founder & CEO"),
                        "pay": officer.get("totalPay", 0),
                        "photo_url": photo_url,
                        "role": "Founder & CEO"
                    }
                elif not chairperson and ("chairman" in title or "board" in title):
                    chairperson = {
                        "name": name,
                        "title": officer.get("title", "Chairperson"),
                        "pay": officer.get("totalPay", 0),
                        "photo_url": photo_url,
                        "role": "Chairperson"
                    }
                else:
                    officers.append({
                        "name": name,
                        "title": officer.get("title", "N/A"),
                        "pay": officer.get("totalPay", 0),
                        "photo_url": photo_url
                    })
        
        # If no officers found, create defaults
        if not officers:
            officers.append({
                "name": "Leadership Team",
                "title": "Management",
                "pay": 0,
                "photo_url": get_avatar_url("LT")
            })
        
        # Prepare leadership section with owner and chairperson at the top
        leadership = []
        if owner:
            leadership.append(owner)
        if chairperson:
            leadership.append(chairperson)
        
        result = {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "leadership": leadership,  # Owner and Chairperson at top
            "board_members": officers,
            "board_size": len(officers) + len(leadership)
        }
        
        # Cache the result
        company_cache[cache_key] = {
            "data": result,
            "timestamp": time.time()
        }
        
        return result
    except Exception as e:
        print(f"❌ Error fetching board for {ticker}: {str(e)}")
        # Return default data instead of raising exception
        return {
            "ticker": ticker,
            "company_name": ticker,
            "leadership": [],
            "board_members": [{
                "name": "Board Information",
                "title": "Temporarily Unavailable",
                "pay": 0,
                "photo_url": get_avatar_url("NA")
            }],
            "board_size": 0
        }


@app.get("/compendium/{ticker}")
def get_compendium(ticker: str):
    """Fetch financial reports with multi-source fallback (SEC, Yahoo, Web Scraping)."""
    try:
        current_year = 2025
        
        # Fetch reports for each quarter using multi-source approach
        quarters_data = {}
        for q in [4, 3, 2, 1]:
            quarter_key = f"Q{q}"
            report_data = get_report_with_fallback(ticker, 'quarterly', current_year, q)
            
            # Quarter dates
            quarter_months = {4: "Jan", 3: "Oct", 2: "Jul", 1: "Apr"}
            
            quarters_data[quarter_key] = {
                "url": report_data["url"] if report_data["available"] else None,
                "date": f"{quarter_months[q]} {current_year - (1 if q <= 3 else 0)}",
                "source": report_data["source"],
                "available": report_data["available"]
            }
        
        # Fetch AGM report (annual)
        agm_report = get_report_with_fallback(ticker, 'annual', current_year, 4)
        
        # Structure for different report types
        compendium = {
            "ticker": ticker,
            "reports": {
                "credit_summary": {
                    "name": "Credit Summary",
                    "description": "Credit analysis and debt assessment",
                    "quarters": quarters_data
                },
                "equity_note": {
                    "name": "Equity Note",
                    "description": "Equity valuation and stock analysis",
                    "quarters": quarters_data
                },
                "esg_compendium": {
                    "name": "ESG Compendium",
                    "description": "Environmental, Social & Governance insights",
                    "quarters": quarters_data
                },
                "results_compendium": {
                    "name": "Results Compendium",
                    "description": "Financial results and performance summary",
                    "quarters": quarters_data
                },
                "agm_report": {
                    "name": "Annual General Meeting",
                    "description": "Annual general meeting report and proxy statement",
                    "quarters": {
                        "Annual": {
                            "url": agm_report["url"] if agm_report["available"] else None,
                            "date": f"FY {current_year}",
                            "source": agm_report["source"],
                            "available": agm_report["available"]
                        }
                    }
                }
            }
        }
        return compendium
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching compendium: {str(e)}")


# ==========================================
#          AI CHATBOT ENDPOINT
# ==========================================

@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    """
    AI Chatbot endpoint for discussing company news, history, board members, capabilities.
    Accepts user message and optional ticker for context.
    Uses Google Gemini API to generate intelligent financial insights.
    """
    if not gemini_model:
        raise HTTPException(status_code=500, detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
    
    try:
        # Build conversation history for context (Gemini format)
        messages = []
        
        # Add conversation history if provided
        if request.history:
            for msg in request.history[-10:]:  # Keep last 10 messages for context window
                role = "user" if msg.role == "user" else "model"
                messages.append({
                    "role": role,
                    "parts": [msg.message]
                })
        
        # Fetch relevant context if ticker is provided
        context = ""
        if request.ticker:
            try:
                ticker_obj = yf.Ticker(request.ticker)
                info = ticker_obj.info
                company_name = info.get("longName", request.ticker)
                sector = info.get("sector", "N/A")
                market_cap = info.get("marketCap", "N/A")
                pe_ratio = info.get("trailingPE", "N/A")
                
                # Fetch recent news for this ticker
                recent_news = news_collection.find_one({"ticker": request.ticker}) or {}
                recent_articles = recent_news.get("articles", [])[:3]
                
                context = f"\nContext: Company={company_name}, Sector={sector}, MarketCap={market_cap}, P/E={pe_ratio}\n"
                if recent_articles:
                    context += "Recent News:\n"
                    for article in recent_articles:
                        context += f"- {article.get('title', 'No title')}\n"
                
                # Add sentiment analysis if available
                sentiment_data = news_collection.find_one({"ticker": request.ticker, "sentiment": {"$exists": True}})
                if sentiment_data:
                    sentiment = sentiment_data.get("sentiment", {})
                    context += f"Market Sentiment: Positive={sentiment.get('positive', 0):.1%}, Negative={sentiment.get('negative', 0):.1%}\n"
            except Exception as e:
                context = f"\n(Note: Unable to fetch detailed context for {request.ticker}: {str(e)})\n"
        
        # Prepare user message with context
        user_message = request.user_message
        if context:
            user_message = user_message + context
        
        # Add current user message to conversation
        messages.append({
            "role": "user",
            "parts": [user_message]
        })
        
        # Call Gemini API
        response = gemini_model.generate_content(
            messages,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 500
            }
        )
        
        bot_response = response.text if hasattr(response, "text") else ""
        
        # Build updated history
        updated_history = list(request.history) if request.history else []
        updated_history.append(ChatMessage(role="user", message=request.user_message))
        updated_history.append(ChatMessage(role="bot", message=bot_response))
        
        return ChatResponse(
            response=bot_response,
            role="bot",
            history=updated_history
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


if __name__ == "__main__":
    # Use this guarded runner on Windows to avoid multiprocessing/reload recursion
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)



