
from fastapi import FastAPI

app = FastAPI(
    title="LightShift-PatchCore API",
    description="Industrial Anomaly Detection",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "LightShift-PatchCore API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": False
    }
