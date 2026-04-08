from dataclasses import dataclass


@dataclass(frozen=True)
class CreateUser:
    email: str
    password: str
    name: str


@dataclass(frozen=True)
class LoginUser:
    email: str
    password: str
