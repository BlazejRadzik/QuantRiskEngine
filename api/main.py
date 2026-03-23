from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="QuantRisk Engine API")

app.include_router(router, prefix="/v1")

@app.get("/")
def read_root():
    return {"status": "QuantRisk Engine is Online"}
