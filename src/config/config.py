#!/usr/local/bin/python3
# coding: utf-8

# ytdlbot - config.py
# 8/28/21 15:01
#

__author__ = "Benny <benny.think@gmail.com>"

import os


def get_env(name: str, default=None):
    val = os.getenv(name)
    # treat unset or empty ("VAR=") env vars as absent -> use default
    if val is None or val == "":
        return default
    if isinstance(val, str):
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        if val.isdigit() and name != "AUTHORIZED_USER":
            return int(val)
    return val


# general settings
WORKERS: int = get_env("WORKERS", 100)
APP_ID: int = get_env("APP_ID")
APP_HASH = get_env("APP_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")
OWNER = [int(i) for i in str(get_env("OWNER", "")).split(",") if i.strip().isdigit()]
YT_DLP_PROXY = get_env("YT_DLP_PROXY", "")

# db settings
AUTHORIZED_USER: str = get_env("AUTHORIZED_USER", "")
DB_DSN = get_env("DB_DSN")
REDIS_HOST = get_env("REDIS_HOST")

AUDIO_FORMAT = get_env("AUDIO_FORMAT", "m4a")
M3U8_SUPPORT = get_env("M3U8_SUPPORT")
ENABLE_ARIA2 = get_env("ENABLE_ARIA2")

# For advance users
# Please do not change, if you don't know what these are.
TG_NORMAL_MAX_SIZE = 2000 * 1024 * 1024
CAPTION_URL_LENGTH_LIMIT = 150

# This will set the value for the tmpfile path(engine path). If not, will return None and use system’s default path.
# Please ensure that the directory exists and you have necessary permissions to write to it.
TMPFILE_PATH = get_env("TMPFILE_PATH", "/tmp/ytdlbot")
