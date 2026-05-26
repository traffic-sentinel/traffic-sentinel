from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Traffic Sentinel",
    description="AI-Powered Traffic Monitoring System for Uganda",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "🚦 Traffic Sentinel MVP is running!",
        "status": "active",
        "version": "1.0.0",
        "purpose": "Government Systems Prototype Showcase 2026"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Traffic Sentinel"}

# TODO: Add more routes later (video upload, detection, analytics)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)