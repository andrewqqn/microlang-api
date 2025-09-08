from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Add this after creating your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://165.22.155.118:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    # For now, just echo the message back
    return {"message": f"You said: {request.message}"}
