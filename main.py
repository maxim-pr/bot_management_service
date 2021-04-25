import uvicorn

from loader import app
from routers import auth_router, bots_router

from config import IP, PORT

app.include_router(auth_router)
app.include_router(bots_router)


if __name__ == "__main__":
    uvicorn.run(app, host=IP, port=PORT)
