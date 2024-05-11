from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect
import logging

from app_redis import get_redis

ws_router = APIRouter()


@ws_router.websocket("/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # await verify_token(token)
    await websocket.accept()
    redis = await get_redis()
    try:
        while True:
            message = await redis.lpop(token)
            if message:
                logging.info(f"websocket is start to send message {message}")
                await websocket.send_text(message)
    except WebSocketDisconnect:
        logging.warning(f"server[{token}] is disconnect")
    except Exception as e:
        logging.error(e)
