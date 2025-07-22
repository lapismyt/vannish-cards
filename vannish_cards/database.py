from datetime import datetime

from sqlalchemy import Engine
from sqlmodel import BigInteger, Column, Field, Session, SQLModel, select, update

from .data_types import (
    BackgroundEnum,
    BaseColorEnum,
    RarityEnum,
)


class SavedUser(SQLModel, table=True):
    user_id: int = Field(sa_column=Column(BigInteger(), primary_key=True, autoincrement=False))
    username: str | None = Field(default=None)
    cards_count: int = Field(default=0)
    last_card: datetime = Field(default=datetime(2000, 1, 1, 0, 0, 0))


class SavedCard(SQLModel, table=True):
    card_id: BigInteger | None = Field(default=None, primary_key=True)
    user_id: BigInteger = Field(index=True)
    nickname: str
    number: int | None = Field(default=None, unique=True)
    rarity: RarityEnum
    base_color: BaseColorEnum
    background: BackgroundEnum


def prepare_database(engine: Engine):
    SQLModel.metadata.create_all(engine)


def get_user_by_id(session: Session, user_id: int) -> SavedUser | None:
    return session.exec(
        select(SavedUser).where(SavedUser.user_id == user_id)
    ).one_or_none()


def get_user_by_username(session: Session, username: str) -> SavedUser | None:
    return session.exec(
        select(SavedUser).where(SavedUser.username == username)
    ).one_or_none()


def update_username(session: Session, user_id: int, new_username: str | None):
    session.exec(
        update(SavedUser)
        .where(SavedUser.user_id == user_id)  # type: ignore
        .values(username=new_username)
    )
    session.commit()


def get_last_number_card(session: Session) -> SavedCard | None:
    return session.exec(
        select(SavedCard).order_by(SavedCard.number.desc()).limit(1)  # type: ignore
    ).first()


def add_card(session: Session, card: SavedCard):
    session.add(card)
    session.commit()


def get_user_cards(session: Session, user_id: int) -> list[SavedCard]:
    return list(
        session.exec(select(SavedCard).where(SavedCard.user_id == user_id)).all()
    )


def add_user(session: Session, user: SavedUser):
    session.add(user)
    session.commit()


def get_card_by_number(session: Session, card_number: int) -> SavedCard | None:
    return session.exec(
        select(SavedCard).where(SavedCard.number == card_number)
    ).one_or_none()


def update_last_card_time(session: Session, user_id: int):
    statement = (
        update(SavedUser)
        .where(SavedUser.user_id == user_id)  # type: ignore
        .values(last_card=datetime.now())
    )
    session.exec(statement)  # type: ignore
    session.commit()
