from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
import motor.motor_asyncio
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime
import os
from dotenv import load_dotenv
import yfinance as yf
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"
MONGO_URI = os.getenv("MONGO_URI")

# Email Config
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

# --- DATABASE ---
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.kryptonax
users_collection = db.users

# --- MODELS ---
class UserRegister(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    mobile: str  # We keep this for record, but won't use it for SMS

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str

# --- AUTH UTILS ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    user = await users_collection.find_one({"username": username})
    if user is None: raise HTTPException(status_code=401)
    return user

# --- NOTIFICATIONS (EMAIL ONLY) ---
async def send_welcome_email(email_to: str, ticker: str):
    html = f"""
    <h3>Kryptonax Alert</h3>
    <p>You are now subscribed to updates for: <b>{ticker}</b></p>
    <p>We will notify you on significant market movement via email.</p>
    """
    try:
        message = MessageSchema(
            subject=f"Alert Subscribed: {ticker}",
            recipients=[email_to],
            body=html,
            subtype="html"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        print(f"Email Error: {e}")

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Kryptonax API Live"}

@app.post("/register")
async def register(user: UserRegister):
    existing = await users_collection.find_one({"username": user.username})
    if existing: raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user.password)
    await users_collection.insert_one(user_dict)
    return {"message": "User created"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = jwt.encode({"sub": user["username"]}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user_name": user.get("first_name", "User")}

@app.post("/subscribe/{ticker}")
async def subscribe(ticker: str, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"username": current_user["username"]},
        {"$addToSet": {"subscriptions": ticker}}
    )
    # Trigger Email Notification Only
    await send_welcome_email(current_user["username"], ticker)
        
    return {"status": "subscribed", "ticker": ticker}

# --- DATA ENDPOINTS ---
@app.get("/quote/{ticker}")
async def get_quote(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty: raise ValueError("No data")
        price = data['Close'].iloc[-1]
        prev = stock.info.get('previousClose', price)
        return {"symbol": ticker, "price": round(price, 2), "change": round(price-prev, 2), "percent": round((price-prev)/prev*100, 2), "currency": "USD"}
    except:
        return {"symbol": ticker, "price": 0, "change": 0, "percent": 0}

@app.get("/news/general")
async def general_news():
    return [
        {"title": "Tech Stocks Rally to New Highs", "sentiment": "positive", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Stocks hit record highs as AI adoption accelerates..."},
        {"title": "Inflation Data Shows Cooling Trend", "sentiment": "positive", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Consumer prices rose less than expected..."},
        {"title": "Oil Prices Volatile Amid Geopolitical Tension", "sentiment": "negative", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Energy sector faces uncertainty..."},
        {"title": "Crypto Markets Stabilize After Correction", "sentiment": "neutral", "publishedAt": datetime.now().isoformat(), "url": "#", "description": "Bitcoin holds steady at support levels..."}
    ]

@app.get("/trending")
async def trending():
    return [
        {"ticker": "NVDA", "change": 2.5},
        {"ticker": "TSLA", "change": -1.2},
        {"ticker": "BTC-USD", "change": 4.8},
        {"ticker": "AAPL", "change": 0.5}
    ]

@app.get("/history/{ticker}")
async def history(ticker: str, period: str = "1mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        data = [{"date": d.strftime('%Y-%m-%d'), "price": round(r['Close'], 2)} for d, r in hist.iterrows()]
        return {"currency": "USD", "data": data}
    except:
        return {"currency": "USD", "data": []}

@app.post("/api/quotes")
async def batch_quotes(tickers: List[str]):
    res = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            data = stock.history(period="1d")
            if not data.empty:
                p = data['Close'].iloc[-1]
                prev = stock.info.get('previousClose', p)
                change = ((p - prev) / prev) * 100
                res[t] = {"price": round(p, 2), "percent": round(change, 2), "color": "#00e676" if change >= 0 else "#ff1744"}
        except: continue
    return res
@app.post("/subscribe/{ticker}")
async def subscribe(ticker: str, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"username": current_user["username"]},
        {"$addToSet": {"subscriptions": ticker}}
    )
    # Trigger Email Notification Only
    await send_welcome_email(current_user["username"], ticker)
        
    return {"status": "subscribed", "ticker": ticker}
# FORCE UPDATE: TITAN EMAIL CONFIG