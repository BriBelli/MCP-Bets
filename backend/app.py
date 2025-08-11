
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from openai_service import get_openai_completion

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
def home():
    return JSONResponse(content={"message": "Welcome to the Python-React app!"})


# New endpoint for OpenAI completion
@app.post("/api/openai")
async def openai_completion(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    result = get_openai_completion(prompt)
    if "error" in result:
        return JSONResponse(content={"error": result["error"]}, status_code=result["status_code"])
    return JSONResponse(content={"response": result["response"]}, status_code=result["status_code"])

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)