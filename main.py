from fastapi import FastAPI
from pydantic import BaseModel
from vectorstore import get_relevant_docs

app = FastAPI()

class Query(BaseModel):
    query: str

@app.post("/ask")
def ask(q: Query):
    query = q.query.lower()
    docs = get_relevant_docs(q.query)
    context = " ".join(docs)
    
    out_of_scope_words = ["pm", "prime minister", "president", "cricket", "movie", "weather", "who is"]
    if any(word in query for word in out_of_scope_words):
        return {"answer": "I can only answer questions about Zepto policies right now."}
    
    if "delivery fee" in query or "149" in query or "delivery" in query:
        for doc in docs:
            if "delivery fee" in doc.lower():
                return {"answer": f"Based on the retrieved context: {doc}"}
    
    if "return" in query:
        for doc in docs:
            if "return" in doc.lower():
                return {"answer": f"Based on the retrieved context: {doc}"}
    
    return {"answer": f"Based on the retrieved context: {context}"}

@app.get("/")
def home():
    return {"message": "Zepto Support Assistant Running"}