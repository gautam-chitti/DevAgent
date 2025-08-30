from fastapi import FastAPI

app = FastAPI()

@app.get("/add")
async def add(a: int = 0, b: int = 0):
    return {"result": a + b}