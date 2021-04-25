import asyncio

from aiohttp import ClientSession

# dictionary with asyncio tasks representing currently running bots
bot_tasks = dict()


async def run_bot(user_id: str, bot_token: str):
    bot_task = asyncio.get_event_loop().create_task(_process_updates(bot_token))
    if not bot_tasks.get(user_id):
        bot_tasks[user_id] = dict()
    bot_tasks[user_id][bot_token] = bot_task


async def stop_bot(user_id: str, bot_token: str):
    bot_task = bot_tasks.get(user_id).get(bot_token)
    bot_task.cancel()


async def _process_updates(bot_token: str):
    bot_api_url = f"https://api.telegram.org/bot{bot_token}/"
    session = ClientSession()

    json_body = {
        "limit": 1
    }

    # start polling telegram bot API for updates
    while True:
        try:
            response = await session.post(bot_api_url + "getUpdates", json=json_body)
            json_response = await response.json()

            # check whether there is error in response
            if not json_response.get("ok"):
                await asyncio.sleep(1)
                continue

            # check whether response has update
            if json_response.get("result"):
                update_id = json_response.get("result")[0].get("update_id")
                from_id = json_response.get("result")[0].get("message").get("from").get("id")
                # if received message is text message, send it back
                text = json_response.get("result")[0].get("message").get("text")
                if text:
                    response = await session.post(bot_api_url + "sendMessage", json={"chat_id": from_id, "text": text})
                json_body["offset"] = update_id + 1
        except asyncio.CancelledError:
            break
        await asyncio.sleep(0.1)

    await session.close()



