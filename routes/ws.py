from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect
import logging


ws_router = APIRouter()


@ws_router.websocket("/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # await verify_token(token)
    await websocket.accept()
    try:
        while True:
            pass
    except WebSocketDisconnect:
        logging.warning(f"server[{token}] is disconnect")
    except Exception as e:
        logging.error(e)
