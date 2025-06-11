from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers
from .routers import system, cognitive, trade

# Initialize FastAPI app
app = FastAPI(
    title="Tron Dashboard API",
    description="Backend service for the Tron Trading Dashboard.",
    version="1.0.0",
)

# CORS Middleware to allow requests from the Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
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