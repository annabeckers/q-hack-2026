from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.auth.jwt import get_current_user
from app.infrastructure.database import async_session_factory
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.commands.user_commands import CreateUser, LoginUser
from app.application.handlers.user_handler import CreateUserHandler, LoginHandler

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    async with async_session_factory() as session:
        async with session.begin():
            repo = UserRepository(session)
            handler = CreateUserHandler(repo)
            try:
                user = await handler.handle(CreateUser(email=body.email, password=body.password, name=body.name))
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            return UserResponse(id=str(user.id), email=user.email, name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    async with async_session_factory() as session:
        repo = UserRepository(session)
        handler = LoginHandler(repo)
        try:
            token = await handler.handle(LoginUser(email=body.email, password=body.password))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(user_data: dict = Depends(get_current_user)):
    return UserResponse(id=user_data["sub"], email=user_data["email"], name="")
