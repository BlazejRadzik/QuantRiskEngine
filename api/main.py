from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="QuantRisk Pro API",
    description="Enterprise Risk Management Engine",
    version="2.0"
)

# Podpięcie ścieżek z routes.py
app.include_router(router)

@app.get("/")
def health_check():
    return {"status": "System Operational", "service": "QuantRisk Engine API"}