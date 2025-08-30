from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/add")
async def add(a: int = 0, b: int = 0):
    return {"sum": a + b}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, log_level="debug")