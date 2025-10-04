from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, upload, questions, attempts
import os

app = FastAPI(title="Concurse AI API", version="0.2.0")

origins = os.getenv("ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(questions.router, prefix="/questions", tags=["questions"])
app.include_router(attempts.router, prefix="/attempts", tags=["attempts"])