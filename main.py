from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from openai import OpenAI
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

app = FastAPI()

load_dotenv()

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
    conversation_id: str = "default"

def init_db():
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_conversation_history(conversation_id: str):
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM conversation_turns
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def save_conversation_turn(conversation_id: str, role: str, content: str):
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversation_turns (conversation_id, role, content)
        VALUES (?, ?, ?)
    ''', (conversation_id, role, content))
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Get conversation history
        history = get_conversation_history(request.conversation_id)

        # Format history for Gemini
        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        # Add the new user message
        contents.append(types.Content(role="user", parts=[types.Part(text=request.message)]))

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=contents
        )

        output = response.text if response else "Sorry, no response generated."

        # Save the user message and bot response
        save_conversation_turn(request.conversation_id, "user", request.message)
        save_conversation_turn(request.conversation_id, "assistant", output)

        return {"message": output}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}

@app.delete("/wipe_db")
def wipe_db():
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM conversation_turns')
    conn.commit()
    conn.close()
    return {"message": "Database wiped"}
