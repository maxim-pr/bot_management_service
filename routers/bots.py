from aiohttp import ClientSession
from fastapi import Depends, HTTPException, status, Body

from loader import bots_router, db
from schemas import User, Bot, Bots
from services import run_bot, stop_bot
from .auth import get_current_user


@bots_router.on_event("startup")
async def startup():
    async for user in db.get_users():
        for bot in user["bots"]:
            await run_bot(str(user["_id"]), bot["bot_token"])


@bots_router.on_event("shutdown")
async def startup():
    async for user in db.get_users():
        for bot in user["bots"]:
            await stop_bot(str(user["_id"]), bot["bot_token"])


@bots_router.get("/",
                 response_model=Bots,
                 description="Get bots")
async def get_bots(current_user: User = Depends(get_current_user)):
    bots = await db.get_user_bots(current_user.user_id)
    return bots


@bots_router.post("/",
                  response_model=Bots,
                  description="Add bot. Maximum number of bots that user can have is 5",
                  response_description="Returns user's bots after update")
async def add_bot(*,
                  current_user: User = Depends(get_current_user),
                  bot: Bot):
    bots = await _add_bot(current_user.user_id, bot)

    # start the bot
    await run_bot(current_user.user_id, bot.bot_token)

    # return all the user's bots
    return bots


@bots_router.delete("/",
                    response_model=Bots,
                    description="Delete bot",
                    response_description="Returns user's bots after deletion")
async def delete_bot(current_user: User = Depends(get_current_user),
                     bot_token: str = Body(..., embed=True)):
    current_bots = await db.get_user_bots(current_user.user_id)

    try:
        bots = await db.delete_bot(current_user.user_id, bot_token)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.args[0]
        )

    await stop_bot(current_user.user_id, bot_token)
    return bots


async def _add_bot(user_id: str, bot: Bot) -> Bots:
    # check bot token for validity (i.e. if such bot exists)
    bot_api_url = f"https://api.telegram.org/bot{bot.bot_token}/"
    session = ClientSession()
    response = await session.post(bot_api_url + "getUpdates")
    json_response = await response.json()
    if not json_response.get("ok"):
        await session.close()
        if json_response.get("error_code") == 409:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This bot token is already registered"
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bot token"
        )
    await session.close()

    # check current number of user's bots
    # (number of bots per user cannot exceed 5)
    current_bots = await db.get_user_bots(user_id)
    if len(current_bots.bots) == 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot add more than 5 bots"
        )

    try:
        bots = await db.add_bot(user_id, bot)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.args[0]
        )

    return bots
