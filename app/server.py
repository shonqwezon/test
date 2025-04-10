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
    add_task,
    delete_factory,
    get_factories,
    get_factory,
    get_task,
    get_tasks,
    get_user,
    get_users_by_role,
    set_factory,
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


class CreateObject(BaseModel):
    token: int
    name: str
    description: str
    lat: float
    lon: float


class CreateTask(BaseModel):
    token: int
    user_id: int
    object_id: int
    description: str


class GetSmth(BaseModel):
    token: int


class GetTask(BaseModel):
    token: int
    user_id: int = -1
    status: int


class Object(BaseModel):
    name: str
    latitude: float
    longitude: float


class UpdateTask(BaseModel):
    token: int
    task_id: int
    status: int
    note: str = ""


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
async def list_users(request: GetSmth):
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


@server.post("/object/create")
async def create_object(request: CreateObject):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        return await set_factory(request.name, request.description, request.lat, request.lon)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/objects")
async def list_objects(request: GetSmth):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        return await get_factories()
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/object/get/{object_id}")
async def list_object(request: GetSmth, object_id: int):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        return await get_factory(object_id)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/object/del/{object_id}")
async def del_object(request: GetSmth, object_id: int):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        await delete_factory(object_id)
        return JSONResponse(content={"message": "OK"}, status_code=200)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/task/create")
async def create_task(request: CreateTask):
    try:
        user = await get_user(request.token)
        if user.role != Role.OWNER:
            raise Exception("User is not OWNER")
        return await add_task(user.id, request.user_id, request.object_id, request.description)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/tasks")
async def list_tasks(request: GetTask):
    try:
        user = await get_user(request.token)
        if user.role == Role.OWNER:
            return await get_tasks(request.user_id, request.status)
        elif user.role == Role.WORKER:
            return await get_tasks(user.id, request.status)
        else:
            raise Exception("User has role USER")
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/task/get/{task_id}")
async def list_task(request: GetSmth, task_id: int):
    try:
        user = await get_user(request.token)
        if user.role == Role.USER:
            raise Exception("User has role USER")
        return await get_task(task_id)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")


@server.post("/task/update")
async def del_task(request: UpdateTask):
    try:
        user = await get_user(request.token)
        if user.role == Role.USER:
            raise Exception("User has role USER")
        return await update_task(request.task_id, request.status, request.note)
    except Exception as e:
        logger.debug(f"Token is wrong: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid")
