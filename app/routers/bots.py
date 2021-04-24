from fastapi import Depends, APIRouter, HTTPException, status, Form, BackgroundTasks

from app.db import db
from app.schemas import User, Bot, Bots
from .auth import get_current_user
from aiohttp import ClientSession
from app.services import run_bot, stop_bot

bots_router = APIRouter()


@bots_router.on_event("startup")
async def startup():
    for user_data in db.values():
        for bot_token_dict in user_data.get("bots"):
            await run_bot(User(**user_data), bot_token_dict.get("bot_token"))


@bots_router.on_event("shutdown")
async def startup():
    for user_data in db.values():
        for bot_token in user_data.get("bots"):
            await stop_bot(User(**user_data), bot_token)


@bots_router.get("/bots", response_model=Bots)
async def get_bots(current_user: User = Depends(get_current_user)):
    bots = await _get_bots(current_user.username)
    return bots


@bots_router.post("/bots", response_model=Bots)
async def add_bot(*,
                  current_user: User = Depends(get_current_user),
                  bot: Bot):
    await _add_bot(current_user.username, bot)

    # start the bot
    await run_bot(current_user, bot.bot_token)

    # return all the user's bots
    bots = await _get_bots(current_user.username)
    return bots


@bots_router.delete("/bots", response_model=Bots)
async def delete_bot(*,
                     current_user: User = Depends(get_current_user),
                     bot_token: str):
    db[current_user.username]["bots"].remove(bot_token)
    await stop_bot(current_user, bot_token)


async def _get_bots(username: str) -> Bots:
    bots = db.get(username).get("bots")
    return Bots(**{"bots": bots})


async def _add_bot(username: str, bot: Bot):
    # check bot token for validity (i.e. such bot exists)
    bot_api_url = f"https://api.telegram.org/bot{bot.bot_token}/"
    session = ClientSession()
    response = await session.post(bot_api_url + "getUpdates")
    json_response = await response.json()
    if not json_response.get("ok"):
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bot token"
        )
    await session.close()

    # check current number of user's bots
    # (number of bots per user cannot exceed 5)
    if len(db.get(username).get("bots")) == 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot add more than 5 bots"
        )

    # check bot token for duplicates in database
    # (user cannot add bot with token that was already added before)
    for user_data in db.values():
        for user_bot in user_data.get("bots"):
            if bot.bot_token == user_bot.get("bot_token"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Requested bot token is already registered"
                )

    # add bot to database
    db[username]["bots"].append(bot.dict())
