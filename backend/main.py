from fastapi import FastAPI
from pydantic import BaseModel

from services.bedrock_service import ask_bedrock


app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "cloudops-ai-agent"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    answer = ask_bedrock(request.message)

    return {
        "answer": answer
    }
