from fastapi import FastAPI
from api.routes import router as risk_router

app = FastAPI(
    title="Quant Risk Management Engine",
    description="professional api for financial risk modeling and stochastic simulations",
    version="1.0.0"
)

# register application routes
app.include_router(risk_router, prefix="/v1")

@app.get("/")
async def health_check():
    """
    returns the operational status of the engine.
    """
    return {
        "status": "ready",
        "service": "quant-risk-engine",
        "api_version": "1.0.0"
    }