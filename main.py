# from fastapi import FastAPI, HTTPException, Depends, status
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Optional
# from passlib.context import CryptContext
# import motor.motor_asyncio
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from jose import JWTError, jwt
# from datetime import datetime
# import os
# from dotenv import load_dotenv
# import yfinance as yf
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# # 1. LOAD ENVIRONMENT VARIABLES
# load_dotenv()

# # --- CONFIGURATION ---
# SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
# ALGORITHM = "HS256"

# # ⚠️ SECURITY WARNING: Move this to your .env file in production!
# MONGO_URI = "mongodb+srv://admin:(!#Krypton1!#)@cluster0.snwbrpt.mongodb.net/?appName=Cluster0"

# # --- APP INITIALIZATION ---
# app = FastAPI()

# # --- CORS ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- DATABASE CONNECTION (MONGODB - ASYNC) ---
# client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
# db = client.kryptonax
# users_collection = db.users
# subscriptions_collection = db.subscriptions  # Separate collection for easier management

# # --- EMAIL CONFIGURATION ---
# conf = ConnectionConfig(
#     MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
#     MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
#     MAIL_FROM = os.getenv("MAIL_FROM"),
#     MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
#     MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
#     MAIL_STARTTLS = True,
#     MAIL_SSL_TLS = False,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )

# # --- MODELS ---
# class UserRegister(BaseModel):
#     username: str
#     password: str
#     first_name: str
#     last_name: str
#     mobile: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str
#     user_name: str

# # --- AUTH UTILS ---
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
# def get_password_hash(password): return pwd_context.hash(password)

# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None: raise HTTPException(status_code=401)
#     except JWTError:
#         raise HTTPException(status_code=401)
    
#     user = await users_collection.find_one({"username": username})
#     if user is None: raise HTTPException(status_code=401)
#     return user

# # --- NOTIFICATIONS (EMAIL ONLY) ---
# async def send_welcome_email(email_to: str, ticker: str):
#     html = f"""
#     <h3>Kryptonax Alert</h3>
#     <p>You are now subscribed to updates for: <b>{ticker}</b></p>
#     <p>We will notify you on significant market movement via email.</p>
#     """
#     try:
#         message = MessageSchema(
#             subject=f"Alert Subscribed: {ticker}",
#             recipients=[email_to],
#             body=html,
#             subtype="html"
#         )
#         fm = FastMail(conf)
#         await fm.send_message(message)
#     except Exception as e:
#         print(f"Email Error: {e}")

# # ==========================================
# #               ENDPOINTS
# # ==========================================

# @app.get("/")
# def home():
#     return {"message": "Kryptonax API Live"}

# # --- AUTH ENDPOINTS ---

# @app.post("/register")
# async def register(user: UserRegister):
#     existing = await users_collection.find_one({"username": user.username})
#     if existing: raise HTTPException(status_code=400, detail="Email already registered")
    
#     user_dict = user.dict()
#     user_dict["password"] = get_password_hash(user.password)
#     await users_collection.insert_one(user_dict)
#     return {"message": "User created"}

# @app.post("/token", response_model=Token)
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = await users_collection.find_one({"username": form_data.username})
#     if not user or not verify_password(form_data.password, user["password"]):
#         raise HTTPException(status_code=400, detail="Invalid credentials")
    
#     token = jwt.encode({"sub": user["username"]}, SECRET_KEY, algorithm=ALGORITHM)
#     # Return first name if available, otherwise "User"
#     user_name = user.get("first_name", "User")
#     return {"access_token": token, "token_type": "bearer", "user_name": user_name}

# # --- SUBSCRIBE ENDPOINTS (BELL ICON LOGIC) ---

# # 1. SUBSCRIBE (Enable Bell)
# @app.post("/subscribe/{ticker}", status_code=status.HTTP_201_CREATED)
# async def subscribe_to_ticker(ticker: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
    
#     # Check if already subscribed
#     existing = await subscriptions_collection.find_one({
#         "username": username,
#         "ticker": ticker
#     })
    
#     if existing:
#         return {"message": f"Already subscribed to {ticker}"}

#     # Add subscription to DB
#     await subscriptions_collection.insert_one({
#         "username": username,
#         "ticker": ticker
#     })
    
#     # Send Email Notification
#     await send_welcome_email(username, ticker)
    
#     return {"message": f"Successfully subscribed to {ticker}"}

# # 2. UNSUBSCRIBE (Disable Bell)
# @app.delete("/subscribe/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
# async def unsubscribe_from_ticker(ticker: str, current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]

#     # Delete subscription from DB
#     result = await subscriptions_collection.delete_one({
#         "username": username,
#         "ticker": ticker
#     })

#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Subscription not found")

#     return

# # 3. GET FAVORITES (Restore Bell State on Refresh)
# @app.get("/favorites")
# async def get_favorites(current_user: dict = Depends(get_current_user)):
#     username = current_user["username"]
#     # Find all tickers this user is subscribed to
#     cursor = subscriptions_collection.find({"username": username})
#     subs = await cursor.to_list(length=100)
#     # Return format expected by Frontend
#     return [{"ticker": sub["ticker"]} for sub in subs]

# # --- DATA ENDPOINTS ---

# @app.get("/quote/{ticker}")
# async def get_quote(ticker: str):
#     try:
#         stock = yf.Ticker(ticker)
#         data = stock.history(period="1d")
#         if data.empty: raise ValueError("No data")
#         price = data['Close'].iloc[-1]
#         prev = stock.info.get('previousClose', price)
#         return {"symbol": ticker, "price": round(price, 2), "change": round(price-prev, 2), "percent": round((price-prev)/prev*100, 2), "currency": "USD"}
#     except:
#         return {"symbol": ticker, "price": 0, "change": 0, "percent": 0}

# @app.get("/news/general")
# async def general_news():
#     return [
#         {"title": "Tech Stocks Rally to New Highs", "sentiment": "positive", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Stocks hit record highs as AI adoption accelerates..."},
#         {"title": "Inflation Data Shows Cooling Trend", "sentiment": "positive", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Consumer prices rose less than expected..."},
#         {"title": "Oil Prices Volatile Amid Geopolitical Tension", "sentiment": "negative", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Energy sector faces uncertainty..."},
#         {"title": "Crypto Markets Stabilize After Correction", "sentiment": "neutral", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Bitcoin holds steady at support levels..."}
#     ]

# @app.get("/trending")
# async def trending():
#     return [
#         {"ticker": "NVDA", "change": 2.5},
#         {"ticker": "TSLA", "change": -1.2},
#         {"ticker": "BTC-USD", "change": 4.8},
#         {"ticker": "AAPL", "change": 0.5}
#     ]

# @app.get("/history/{ticker}")
# async def history(ticker: str, period: str = "1mo"):
#     try:
#         stock = yf.Ticker(ticker)
#         hist = stock.history(period=period)
#         data = [{"date": d.strftime('%Y-%m-%d'), "price": round(r['Close'], 2)} for d, r in hist.iterrows()]
#         return {"currency": "USD", "data": data}
#     except:
#         return {"currency": "USD", "data": []}

# @app.post("/api/quotes")
# async def batch_quotes(tickers: List[str]):
#     res = {}
#     for t in tickers:
#         try:
#             stock = yf.Ticker(t)
#             data = stock.history(period="1d")
#             if not data.empty:
#                 p = data['Close'].iloc[-1]
#                 prev = stock.info.get('previousClose', p)
#                 change = ((p - prev) / prev) * 100
#                 res[t] = {"price": round(p, 2), "percent": round(change, 2), "color": "#00e676" if change >= 0 else "#ff1744"}
#         except: continue
#     return res



from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
from passlib.context import CryptContext
import motor.motor_asyncio
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import yfinance as yf
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

MONGO_URI = os.getenv("MONGO_URI")

if not SECRET_KEY or not MONGO_URI:
    raise RuntimeError("Missing required environment variables")

# =====================================================
# APP INITIALIZATION
# =====================================================
app = FastAPI(title="Kryptonax API")

# =====================================================
# CORS (RESTRICT IN PRODUCTION)
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kryptonax.com",
        "https://www.kryptonax.com"],  # change in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# DATABASE (MONGODB ASYNC)
# =====================================================
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.kryptonax
users_collection = db.users
subscriptions_collection = db.subscriptions

# =====================================================
# EMAIL CONFIGURATION
# =====================================================
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# =====================================================
# MODELS
# =====================================================
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    mobile: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str

# =====================================================
# AUTH UTILITIES
# =====================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# =====================================================
# EMAIL NOTIFICATION
# =====================================================
async def send_welcome_email(email_to: str, ticker: str):
    html = f"""
    <h3>Kryptonax Alert</h3>
    <p>You are now subscribed to <b>{ticker}</b></p>
    """
    message = MessageSchema(
        subject=f"Subscribed to {ticker}",
        recipients=[email_to],
        body=html,
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)

# =====================================================
# ROUTES
# =====================================================

@app.get("/")
def home():
    return {"message": "Kryptonax API Live"}

# ---------------- AUTH ----------------

@app.post("/register", status_code=201)
async def register(user: UserRegister):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = user.dict()
    user_data["password"] = get_password_hash(user.password)
    await users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_name": user.get("first_name", "User"),
    }

# ---------------- SUBSCRIPTIONS ----------------

@app.post("/subscribe/{ticker}", status_code=201)
async def subscribe(ticker: str, current_user: dict = Depends(get_current_user)):
    ticker = ticker.upper()
    email = current_user["email"]

    exists = await subscriptions_collection.find_one(
        {"email": email, "ticker": ticker}
    )
    if exists:
        return {"message": "Already subscribed"}

    await subscriptions_collection.insert_one(
        {"email": email, "ticker": ticker}
    )

    await send_welcome_email(email, ticker)
    return {"message": f"Subscribed to {ticker}"}

@app.delete("/subscribe/{ticker}", status_code=204)
async def unsubscribe(ticker: str, current_user: dict = Depends(get_current_user)):
    ticker = ticker.upper()
    email = current_user["email"]

    result = await subscriptions_collection.delete_one(
        {"email": email, "ticker": ticker}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")

@app.get("/favorites")
async def favorites(current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    subs = await subscriptions_collection.find(
        {"email": email}
    ).to_list(length=100)
    return [{"ticker": s["ticker"]} for s in subs]

# ---------------- MARKET DATA ----------------

@app.get("/quote/{ticker}")
async def quote(ticker: str):
    ticker = ticker.upper()
    stock = yf.Ticker(ticker)
    hist = stock.history(period="2d")

    if hist.empty:
        raise HTTPException(status_code=404, detail="No data")

    price = hist["Close"].iloc[-1]
    prev = hist["Close"].iloc[-2] if len(hist) > 1 else price

    return {
        "symbol": ticker,
        "price": round(price, 2),
        "change": round(price - prev, 2),
        "percent": round((price - prev) / prev * 100, 2),
        "currency": "USD",
    }

@app.get("/history/{ticker}")
async def history(ticker: str, period: str = "1mo"):
    ticker = ticker.upper()
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    data = [
        {"date": d.strftime("%Y-%m-%d"), "price": round(r["Close"], 2)}
        for d, r in hist.iterrows()
    ]
    return {"currency": "USD", "data": data}

@app.post("/api/quotes")
async def batch_quotes(tickers: List[str]):
    result = {}
    for t in tickers:
        t = t.upper()
        stock = yf.Ticker(t)
        hist = stock.history(period="2d")
        if hist.empty:
            continue

        price = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else price
        change = ((price - prev) / prev) * 100

        result[t] = {
            "price": round(price, 2),
            "percent": round(change, 2),
            "color": "#00e676" if change >= 0 else "#ff1744",
        }
    return result
