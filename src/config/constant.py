#!/usr/local/bin/python3
# coding: utf-8

# ytdlbot - constant.py
# 8/16/21 16:59
#

__author__ = "Benny <benny.think@gmail.com>"

import typing

from pyrogram import Client, types


class BotText:

    start = """✨ Добро пожаловать в бота для загрузки музыки и видео! Пропишите /help чтобы узнать подробнее."""

    help = """
🎬 <b>Добро пожаловать в бота для загрузки видео/аудио/файлов!</b> 🎧

Просто отправь мне ссылку на видео или аудио! Поддерживается много сервисов через мощный движок yt-dlp, например:
→ YouTube
→ Rutube
→ VK Видео
→ Яндекс.Музыка
📋 <b>Полный список:</b> [поддерживаемые сайты](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

⚡ <b>Особенности загрузки видео:</b>
→ По умолчанию разрешение Full HD
→ Ролики с русской аудиодорожкой (при наличии)
→ Большие ролики загружаются в более низком разрешении (работает не для всех сервисов)
→ Загружаются в VP9 кодеке (при наличии), отличный баланс сжатия и производительности
→ В файлы встраивается миниатюра и метаданные о ролике (например, эпизоды, описание и так далее)
→ Для загрузки музыки рекомендуем выбрать аудио-режим в /settings, иначе будут возникать проблемы
→ В данный момент не поддерживается загрузка плейлистов и трансляций.

⚙️ <b>Настройка бота:</b>
Настрой бота через /settings:
→ Качество видео (1080p/720p/480p)
→ Режим отправки (видео/аудио/файл)

📦 <b>Дополнительные возможности:</b>
→ /direct — загрузка файлов напрямую
→ /about — информация о разработчиках
→ Напишите любой текст и бот найдёт 10 видео из YouTube

🚨 <b>Важно знать:</b>
1. При спаме или атаках — моментальная блокировка!
2. Если бот не отвечает, попробуйте резервные версии от официального разработчика (они отличаются от этой версии, учтите):
   EU🇪🇺: @benny_2ytdlbot
   SG🇸🇬: @benny_ytdlbot

💬 <b>По вопросам и предложениям:</b>
@katze_942 | @katze_chat
    """

    about = """
Оригинальный разработчик данного бота - @BennyThink:
github.com/tgbot-collection/ytdlbot

Я, @katze_942, сделал форк со своими улучшениями:
github.com/Katze-942/ytdlbot

    """

    settings = """
— Пожалуйста, выберите предпочтительный формат и качество видео для вашего видео.
→ <b>Высокое (High):</b> 1080P
→ <b>Среднее (Medium):</b> 720P
→ <b>Низкое (Low):</b> 480P

Если вы решите отправить видео в виде файла, вы не сможете просматривать видео напрямую в Telegram клиенте (потребуется сторонний видеоплеер)

<b>— Ваши параметры:</b>
Качество видео: <b>{}</b>
Тип отправки: <b>{}</b>
    """


class Types:
    Message = typing.Union[types.Message, typing.Coroutine]
    Client = Client
