from typing import Any

import fastapi.exception_handlers
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import Field

from . import model
from .auth import UserToken
from .model import (
    JoinRoomResult,
    LiveDifficulty,
    ResultUser,
    RoomInfo,
    RoomUser,
    StrictBase,
    WaitRoomStatus,
)

app = FastAPI()


# リクエストのvalidation errorをprintする
# このエラーが出たら、リクエストのModel定義が間違っている
@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(req, exc):
    print("Request validation error")
    print(f"{req.url=}\n{exc.body=}\n{exc=!s}")
    return await fastapi.exception_handlers.request_validation_exception_handler(
        req, exc
    )


# Sample API
@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


# User APIs


class UserCreateRequest(StrictBase):
    user_name: str = Field(title="ユーザー名")
    leader_card_id: int = Field(title="リーダーカードのID")


class UserCreateResponse(StrictBase):
    user_token: str


@app.post("/user/create")
def user_create(req: UserCreateRequest) -> UserCreateResponse:
    """新規ユーザー作成"""
    token = model.create_user(req.user_name, req.leader_card_id)
    return UserCreateResponse(user_token=token)


# 認証動作確認用のサンプルAPI
# ゲームアプリは使わない
@app.get("/user/me")
def user_me(token: UserToken) -> model.SafeUser:
    user = model.get_user_by_token(token)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # print(f"user_me({token=}, {user=})")
    # 開発中以外は token をログに残してはいけない。
    return user


class Empty(StrictBase):
    pass


@app.post("/user/update")
def update(req: UserCreateRequest, token: UserToken) -> Empty:
    """Update user attributes"""
    # print(req)
    model.update_user(token, req.user_name, req.leader_card_id)
    return Empty()


# Room APIs


class RoomID(StrictBase):
    room_id: int


class CreateRoomRequest(StrictBase):
    live_id: int
    select_difficulty: int  # LiveDifficulty


@app.post("/room/create")
def create(token: UserToken, req: CreateRoomRequest) -> RoomID:
    """ルーム作成リクエスト"""
    print("/room/create", req)
    room_id = model.create_room(
        token=token, live_id=req.live_id, difficulty=req.select_difficulty
    )
    return RoomID(room_id=room_id)


class RoomListRequest(StrictBase):
    live_id: int


class RoomListResponse(StrictBase):
    room_info_list: list[RoomInfo]


@app.post("/room/list", response_model=RoomListResponse)
def room_list(req: RoomListRequest) -> RoomListResponse:
    print("Room List", req)
    return RoomListResponse(room_info_list=model.get_room_list(live_id=req.live_id))


class RoomJoinRequest(StrictBase):
    room_id: int
    select_difficulty: int  # LiveDifficulty


class RoomJoinResponse(StrictBase):
    join_room_result: JoinRoomResult


@app.post("/room/join")
def room_join(token: UserToken, req: RoomJoinRequest) -> RoomJoinResponse:
    print("Room Join Request: ", req)
    response = model.join_room(
        token=token, room_id=req.room_id, difficulty=req.select_difficulty
    )
    return RoomJoinResponse(join_room_result=response)


class RoomWaitRequest(StrictBase):
    room_id: int


class RoomWaitResponse(StrictBase):
    status: int  # WaitRoomStatus
    room_user_list: list[RoomUser]


@app.post("/room/wait")
def room_wait(token: UserToken, req: RoomWaitRequest) -> RoomWaitResponse:
    print("Room Wait Request: ", req)

    res = model.room_wait(token=token, room_id=req.room_id)
    print("RESPONCE", res)
    return RoomWaitResponse(status=res[0], room_user_list=res[1])


class RoomStartRequest(StrictBase):
    room_id: int


@app.post("/room/start")
def room_start(token: UserToken, req: RoomStartRequest):
    print("Room Live Start")
    model.room_start(token=token, room_id=req.room_id)
    return {}


class RoomLiveEndRequest(StrictBase):
    room_id: int
    judge_count_list: list[int]  # 各判定数
    score: int


@app.post("/room/end")
def room_end(token: UserToken, req: RoomLiveEndRequest):
    print("Room Live End")
    model.room_end(
        token=token,
        room_id=req.room_id,
        judge_count_list=req.judge_count_list,
        score=req.score,
    )
    return {}


class RoomResultRequest(StrictBase):
    room_id: int


class RoomResultResponse(StrictBase):
    result_user_list: list[ResultUser]


@app.post("/room/result")
def room_result(token: UserToken, req: RoomResultRequest) -> RoomResultResponse:
    print("ROOM RESULT")
    res = model.room_result(token=token, room_id=req.room_id)
    return RoomResultResponse(result_user_list=res)


class RoomLeaveRequest(StrictBase):
    room_id: int


@app.post("/room/leave")
def room_leave(token: UserToken, req: RoomLeaveRequest):
    print("Leave")
    model.room_leave(token=token, room_id=req.room_id)
    return {}
