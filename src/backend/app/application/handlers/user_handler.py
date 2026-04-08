from app.application.commands.user_commands import CreateUser, LoginUser
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.domain.entities import User
from app.domain.interfaces import AbstractUserRepository


class CreateUserHandler:
    def __init__(self, user_repo: AbstractUserRepository):
        self._user_repo = user_repo

    async def handle(self, command: CreateUser) -> User:
        existing = await self._user_repo.get_by_email(command.email)
        if existing:
            raise ValueError(f"User with email {command.email} already exists")

        user = User(
            email=command.email,
            hashed_password=hash_password(command.password),
            name=command.name,
        )
        return await self._user_repo.save(user)


class LoginHandler:
    def __init__(self, user_repo: AbstractUserRepository):
        self._user_repo = user_repo

    async def handle(self, command: LoginUser) -> str:
        user = await self._user_repo.get_by_email(command.email)
        if not user or not verify_password(command.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        return create_access_token({"sub": str(user.id), "email": user.email})
