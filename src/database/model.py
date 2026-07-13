#!/usr/bin/env python3
# coding: utf-8
import os
from contextlib import contextmanager
from typing import Literal

from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Integer,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)  # telegram user id

    settings = relationship("Setting", back_populates="user", cascade="all, delete-orphan", uselist=False)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quality = Column(Enum("1440p", "1080p", "720p", "480p", "240p"), nullable=False, default="1080p")
    format = Column(Enum("video", "audio", "document"), nullable=False, default="video")
    vcodec = Column(
        Enum("vcodec-auto", "vcodec-vp9", "vcodec-avc1", "vcodec-av01"),
        nullable=False,
        default="vcodec-vp9",
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="settings")


def create_session():
    engine = create_engine(
        os.getenv("DB_DSN"),
        pool_size=50,
        max_overflow=100,
        pool_timeout=30,
        pool_recycle=1800,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


SessionFactory = create_session()


@contextmanager
def session_manager():
    s = SessionFactory()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_quality_settings(tgid) -> Literal["1440p", "1080p", "720p", "480p", "240p"]:
    with session_manager() as session:
        user = session.query(User).filter(User.user_id == tgid).first()
        if user and user.settings:
            return user.settings.quality

        return "1080p"


def get_format_settings(tgid) -> Literal["video", "audio", "document"]:
    with session_manager() as session:
        user = session.query(User).filter(User.user_id == tgid).first()
        if user and user.settings:
            return user.settings.format

        return "video"


def get_vcodec_settings(
    tgid,
) -> Literal["vcodec-auto", "vcodec-vp9", "vcodec-avc1", "vcodec-av01"]:
    with session_manager() as session:
        user = session.query(User).filter(User.user_id == tgid).first()
        if user and user.settings:
            return user.settings.vcodec

        return "vcodec-vp9"


def set_user_settings(tgid: int, key: str, value: str):
    # set quality or format settings
    with session_manager() as session:
        # find user first
        user = session.query(User).filter(User.user_id == tgid).first()
        # upsert
        setting = session.query(Setting).filter(Setting.user_id == user.id).first()
        if setting:
            setattr(setting, key, value)
        else:
            session.add(Setting(user_id=user.id, **{key: value}))


def init_user(uid: int):
    with session_manager() as session:
        user = session.query(User).filter(User.user_id == uid).first()
        if not user:
            session.add(User(user_id=uid))
