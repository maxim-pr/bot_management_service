import uvicorn

from loader import app
from routers import auth_router, bots_router

app.include_router(auth_router)
app.include_router(bots_router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
