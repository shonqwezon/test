import asyncio
import random
import secrets
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config.roles import Role
from app.config.task_status import TaskStatus
from app.db.models import User, db_init
from app.db.requests import (
    get_factory,
    get_tasks,
    get_user,
    get_users_by_role,
    set_user,
    update_task,
    update_user,
)
from app.instances import ThreadSafeKey, TimerSingleton
from app.utils import setup_logger


async def lifespan(app: FastAPI):
    await db_init()
    yield


server = FastAPI(lifespan=lifespan)

logger = setup_logger(__name__)


class AuthRequest(BaseModel):
    key: int


class CreateWorker(BaseModel):
    fullname: str
    token: int


class GetSmth(BaseModel):
    token: int


class Object(BaseModel):
    name: str
    latitude: float
    longitude: float


class Task(BaseModel):
    id: int
    admin_id: int
    object: Object
    description: str
    created: datetime


class HandledTask(BaseModel):
    token: int
    id: int
    name: str
    admin_id: int
    status: TaskStatus
    note: Optional[str] = ""


@server.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return None


# Auth user
@server.post("/auth")
async def authenticate(request: AuthRequest):
    now = datetime.now()
    minutes_today = now.hour * 60 + now.minute

    if abs(minutes_today - request.key) <= 10:
        token = secrets.randbits(63)
        await set_user(token)
        await update_user(token, {User.role: Role.OWNER})
        return {"token": token}

    if name := ThreadSafeKey.is_valid(request.key):
        user = await set_user()
        token = secrets.randbits(63)
        await update_user(
            user.id,
            {User.tg_id: token, User.fullname: name, User.role: Role.WORKER},
            False,
        )
        await TimerSingleton().stop(name)
        return {"token": token}
    else:
        logger.debug("Key is wrong")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/user/create")
async def create_user(request: CreateWorker):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        key = random.randint(100000, 999999)
        timer = TimerSingleton()
        await timer.start((key, request.fullname))
        return {"key": key}
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/users")
async def list_users(request: GetSmth, user_id: int = -1):
    print(user_id)
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        return await get_users_by_role(Role.WORKER)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/user/get/{user_id}")
async def list_user(request: GetSmth, user_id: int):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        return await get_user(user_id, False)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/user/del/{user_id}")
async def del_user(request: GetSmth, user_id: int):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        await update_user(
            user_id,
            {User.role: Role.USER},
            False,
        )
        return JSONResponse(content={"message": "OK"}, status_code=200)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


# @server.post("/get_current_tasks")
# async def get_current_tasks(request: GetTasks):
#     try:
#         user = asyncio.run_coroutine_threadsafe(get_user(request.token), loop).result()
#     except Exception:
#         raise HTTPException(status_code=401, detail="Token has expired, please log in again")
#     if user.role != Role.WORKER:
#         raise HTTPException(status_code=401, detail="Token has expired, please log in again")
#     tasks = asyncio.run_coroutine_threadsafe(get_tasks(user.id, TaskStatus.WAIT), loop).result()
#     res = []
#     for task in tasks:
#         object = asyncio.run_coroutine_threadsafe(get_factory(task.object_id), loop).result()
#         obj = Object(name=object.name, latitude=object.latitude, longitude=object.longitude)
#         res.append(
#             Task(
#                 id=task.id,
#                 admin_id=task.admin_id,
#                 object=obj,
#                 description=task.description,
#                 created=task.created,
#             )
#         )
#     return res


# @server.post("/update_assigned_task")
# async def update_assigned_task(request: HandledTask):
#     try:
#         user = asyncio.run_coroutine_threadsafe(get_user(request.token), loop).result()
#     except Exception:
#         raise HTTPException(status_code=401, detail="Token has expired, please log in again")
#     if user.role != Role.WORKER:
#         raise HTTPException(status_code=401, detail="Token has expired, please log in again")
#     try:
#         task = asyncio.run_coroutine_threadsafe(
#             update_task(request.id, request.status, request.note), loop
#         ).result()
#         admin = asyncio.run_coroutine_threadsafe(get_user(request.admin_id, False), loop).result()
#         if request.status == TaskStatus.COMPLETE:
#             asyncio.run_coroutine_threadsafe(
#                 bot.send_message(
#                     chat_id=admin.tg_id,
#                     text=messages.SEND_COMPLETE_TASK.format(
#                         request.name, user.fullname, task.description
#                     ),
#                 ),
#                 loop,
#             ).result()
#         elif request.status == TaskStatus.CANCELED:
#             asyncio.run_coroutine_threadsafe(
#                 bot.send_message(
#                     chat_id=admin.tg_id,
#                     text=messages.SEND_DENIED_TASK.format(
#                         request.name, user.fullname, request.note, task.description
#                     ),
#                 ),
#                 loop,
#             ).result()
#     except Exception:
#         return HTTPException(status_code=500)
#     else:
#         return JSONResponse(status_code=200, content={"message": "OK"})
