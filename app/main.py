from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models
from .routers import users, products, stats, admin, alerts, history, categories,external_data

app = FastAPI(title="FoodWaste Zero API")

# ======================================
# 🔥 CORS - DOIT ÊTRE DÉCLARÉ EN PREMIER
# ======================================
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://foodwaste-zero.info",
    "https://www.foodwaste-zero.info",
    "https://foodwaste-frontend.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================
# 🔥 Création des tables
# ======================================
Base.metadata.create_all(bind=engine)

# ======================================
# 🔥 Routes API
# ======================================
app.include_router(users.router)
app.include_router(products.router)
app.include_router(stats.router)
app.include_router(admin.router)
app.include_router(alerts.router)
app.include_router(history.router)
app.include_router(categories.router)
app.include_router(external_data.router)



@app.get("/")
def root():
    return {"service": "fwz-api", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

