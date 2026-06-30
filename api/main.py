"""
main.py
FastAPI backend exposing ARIA as an API.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import ask_aria

app = FastAPI(title="ARIA API", description="Self-healing cybersecurity RAG assistant")


class QueryRequest(BaseModel):
    question: str
    mode: str = "qa"


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    scores: dict
    healing_triggered: bool
    healing_attempts: int
    strategies_used: list[str]
    passed: bool
    latency_ms: int
    mode: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result = ask_aria(request.question, mode=request.mode)
    return result