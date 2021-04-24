import uvicorn
from fastapi import FastAPI
from app.routers import auth_router, bots_router


app = FastAPI()
app.include_router(auth_router)
app.include_router(bots_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
