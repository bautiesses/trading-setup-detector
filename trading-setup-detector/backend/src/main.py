import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import get_settings
from src.database import init_db
from src.auth.router import router as auth_router
from src.watchlist.router import router as watchlist_router
from src.scanner.router import router as scanner_router
from src.binance.router import router as binance_router
from src.trades.router import router as trades_router
from src.solana.router import router as solana_router

settings = get_settings()

# Build CORS origins from environment
def get_cors_origins():
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    # Add frontend URL from environment (Railway)
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)
        origins.append(frontend_url.rstrip("/"))

    # Add CORS_ORIGINS if set (comma-separated list or single URL)
    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins:
        for origin in cors_origins.split(","):
            origin = origin.strip()
            if origin and origin not in origins:
                origins.append(origin)
                origins.append(origin.rstrip("/"))

    print(f"CORS Origins configured: {origins}")  # Debug log
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models so they are registered
    from src.auth.models import User
    from src.watchlist.models import WatchlistItem
    from src.scanner.models import ScanResult, ScanExecution
    from src.trades.models import Trade
    from src.solana.models import SolanaWallet, SolanaTrade, TokenCache

    # Startup
    await init_db()
    yield
    # Shutdown
    from src.binance.client import binance_client
    await binance_client.close()


app = FastAPI(
    title="Break & Retest Scanner API",
    description="Detector de patrones Break & Retest en criptomonedas - 100% Gratis",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(scanner_router, prefix="/api/v1")
app.include_router(binance_router, prefix="/api/v1")
app.include_router(trades_router, prefix="/api/v1")
app.include_router(solana_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "Break & Retest Scanner API",
        "version": "2.0.0",
        "description": "Detector de patrones Break & Retest - 100% Gratis",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
