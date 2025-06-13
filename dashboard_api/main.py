from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers
from routers import system, cognitive, trade

# Initialize FastAPI app
app = FastAPI(
    title="Tron Dashboard API",
    description="Backend service for the Tron Trading Dashboard.",
    version="1.0.0",
)

# CORS Middleware to allow requests from the Next.js frontend
import os

# Get environment-specific origins
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    origins = [
        "https://tron-trading.com",
        "https://www.tron-trading.com", 
        "https://dashboard.tron-trading.com",
        "https://api.tron-trading.com",
        # Add LoadBalancer IP when known
        "http://localhost:3000",  # Keep for local testing
    ]
else:
    origins = [
        "http://localhost:3000",  # Default Next.js port
        "http://localhost:3001",  # Common alternative Next.js port
        "http://localhost:8080",  # Additional dev port
        "http://127.0.0.1:3000",
        "*",  # Allow all in development
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(cognitive.router, prefix="/api/cognitive", tags=["Cognitive"])
app.include_router(trade.router, prefix="/api/trade", tags=["Trade"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Tron Dashboard API"}

# For running the app directly during development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 