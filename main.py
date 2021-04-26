from loader import app
from routers import auth_router, bots_router

app.include_router(auth_router)
app.include_router(bots_router)
