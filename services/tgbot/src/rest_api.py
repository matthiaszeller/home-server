import asyncio
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer
from src.models import io as mio
from starlette import status

from common.config import PathRegistry as PR
from common.config import ServiceRegistry as SR

from .access_control import AccessControlManager
from .exceptions import TaskNotFoundError, UnauthorizedAccessError

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def run_fastapi_app(
    shared_queue: asyncio.Queue, ac_manager: AccessControlManager
):
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=SR.SERVICE_TGBOT_PORT,
        loop="asyncio",
        log_level="info",
        ssl_keyfile=PR.get_config_file("secrets/key.pem"),
        ssl_certfile=PR.get_config_file("secrets/certificate.pem"),
        reload=True,
    )
    server = uvicorn.Server(config)
    app.state.message_queue = shared_queue
    app.state.ac_manager = ac_manager
    await server.serve()


def get_access_control_manager() -> AccessControlManager:
    return app.state.ac_manager


def get_message_queue() -> asyncio.Queue:
    return app.state.message_queue


def token_is_registered(ac_manager: AccessControlManager, token: str):
    return ac_manager.is_token_registered(token)


def get_current_token(token: Annotated[str, Depends(oauth2_scheme)]):
    ac_manager = get_access_control_manager()
    if not token_is_registered(ac_manager, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unregistered token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token  # Token is valid and registered, return it for potential further use


@app.get("/ping")
async def ping():
    return {"status": "ok"}


@app.post("/enqueue_task")
async def enqueue_command(
    task: mio.TgbotTask,
    fastpi_response: Response,
    token: Annotated[str, Depends(get_current_token)],
    message_queue: Annotated[asyncio.Queue, Depends(get_message_queue)],
) -> mio.ApiResponse:
    # prepare response data
    future = asyncio.Future()
    # send message to the queue
    msg_in_queue = mio.MessageInQueue(task=task, api_token=token)
    await message_queue.put((msg_in_queue, future))
    # wait for the response
    try:
        task_response: mio.TaskResponse = await asyncio.wait_for(future, timeout=5)
        response = mio.ApiResponse(
            status="success", task=task_response, status_code=200
        )
    except asyncio.TimeoutError:
        response = mio.ApiResponse(
            status="error", error="Command timeout", status_code=500
        )
    except TaskNotFoundError as e:
        response = mio.ApiResponse(status="error", error=str(e), status_code=404)
    except UnauthorizedAccessError as e:
        response = mio.ApiResponse(status="error", error=str(e), status_code=403)
    except Exception as e:
        response = mio.ApiResponse(status="error", error=str(e), status_code=500)

    fastpi_response.status_code = response.status_code
    return response
