#!/usr/local/bin/python3
# coding: utf-8

# ytdlbot - new.py
# 8/14/21 14:37
#

__author__ = "Benny <benny.think@gmail.com>"

import logging
import os
import re
import threading
import time
import typing
from io import BytesIO
from typing import Any

import psutil
import pyrogram.errors
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, enums, filters, types

from config import (
    APP_HASH,
    APP_ID,
    AUTHORIZED_USER,
    BOT_TOKEN,
    ENABLE_ARIA2,
    ENABLE_FFMPEG,
    M3U8_SUPPORT,
    ENABLE_VIP,
    OWNER,
    PROVIDER_TOKEN,
    TOKEN_PRICE,
    UPTIME_URL,
    BotText,
)
from database.model import (
    credit_account,
    get_format_settings,
    get_free_quota,
    get_paid_quota,
    get_quality_settings,
    get_vcodec_settings,
    init_user,
    reset_free,
    set_user_settings,
)
from engine import direct_entrance, youtube_entrance, special_download_entrance
from utils import extract_url_and_name, sizeof_fmt, timeof_fmt

localize_filetype=dict(document="Файл", video="Видео", audio="Аудио")
localize_vcodec={"vcodec-auto": "АВТО", "vcodec-vp9": "VP9 (рекомендовано)", "vcodec-av01": "AV1 (самый сжатый, но требовательный)" ,"vcodec-avc1": "AVC1 (H.264)"}

logging.info("Authorized users are %s", AUTHORIZED_USER)
logging.getLogger("apscheduler.executors.default").propagate = False

def search_ytb(kw: str):
    num_results = 10
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': True,
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_result = ydl.extract_info(f'ytsearch{num_results}:{kw}', download=False)

    index=0
    text = ""

    if search_result and 'entries' in search_result:
        for entry in search_result['entries']:
            if not entry:
                continue

            # Получаем полную информацию о видео
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl_full:
                try:
                    video_info = ydl_full.extract_info(
                        entry['url'],
                        download=False
                    )

                    index += 1
                    title = video_info.get('title', 'Нет названия')
                    url = video_info.get('webpage_url', 'Нет ссылки')
                    description = video_info.get('description', 'Нет описания')[:40] + '...'
                    text += f"<b>{index}. {title}</b>\n{url}\n<i>{description}</i>\n\n"
                except Exception as e:
                    print(f'Ошибка при обработке видео: {e}')

    return text


def create_app(name: str, workers: int = 64) -> Client:
    return Client(
        name,
        APP_ID,
        APP_HASH,
        bot_token=BOT_TOKEN,
        workers=workers,
        # max_concurrent_transmissions=max(1, WORKERS // 2),
        # https://github.com/pyrogram/pyrogram/issues/1225#issuecomment-1446595489
    )


app = create_app("main")


def private_use(func):
    def wrapper(client: Client, message: types.Message):
        chat_id = getattr(message.from_user, "id", None)

        # message type check
        if message.chat.type != enums.ChatType.PRIVATE and not getattr(message, "text", "").lower().startswith("/ytdl"):
            logging.debug("%s, it's annoying me...🙄️ ", message.text)
            return

        # authorized users check
        if AUTHORIZED_USER:
            users = [int(i) for i in AUTHORIZED_USER.split(",")]
        else:
            users = []

        if users and chat_id and chat_id not in users:
            message.reply_text("BotText.private", quote=True)
            return

        return func(client, message)

    return wrapper


@app.on_message(filters.command(["start"]))
def start_handler(client: Client, message: types.Message):
    from_id = message.chat.id
    init_user(from_id)
    logging.info("%s welcome to youtube-dl bot!", message.from_user.id)
    client.send_chat_action(from_id, enums.ChatAction.TYPING)
    free, paid = get_free_quota(from_id), get_paid_quota(from_id)
    client.send_message(
        from_id,
        BotText.start, # + f"You have {free} free and {paid} paid quota.",
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["help"]))
def help_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    client.send_message(chat_id, BotText.help, disable_web_page_preview=True)


@app.on_message(filters.command(["about"]))
def about_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    client.send_message(chat_id, BotText.about)


@app.on_message(filters.command(["ping"]))
def ping_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)

    def send_message_and_measure_ping():
        start_time = int(round(time.time() * 1000))
        reply: types.Message | typing.Any = client.send_message(chat_id, "Пинг...")

        end_time = int(round(time.time() * 1000))
        ping_time = int(round(end_time - start_time))
        message_sent = True
        if message_sent:
            message.reply_text(f"Ping: {ping_time:.2f} ms", quote=True)
        time.sleep(0.5)
        client.edit_message_text(chat_id=reply.chat.id, message_id=reply.id, text="Понг!")
        time.sleep(1)
        client.delete_messages(chat_id=reply.chat.id, message_ids=reply.id)

    thread = threading.Thread(target=send_message_and_measure_ping)
    thread.start()


# @app.on_message(filters.command(["buy"]))
# def buy(client: Client, message: types.Message):
#     markup = types.InlineKeyboardMarkup(
#         [
#             [  # First row
#                 types.InlineKeyboardButton("10-$1", callback_data="buy-10-1"),
#                 types.InlineKeyboardButton("20-$2", callback_data="buy-20-2"),
#                 types.InlineKeyboardButton("40-$3.5", callback_data="buy-40-3.5"),
#             ],
#             [  # second row
#                 types.InlineKeyboardButton("50-$4", callback_data="buy-50-4"),
#                 types.InlineKeyboardButton("75-$6", callback_data="buy-75-6"),
#                 types.InlineKeyboardButton("100-$8", callback_data="buy-100-8"),
#             ],
#         ]
#     )
#     message.reply_text("Please choose the amount you want to buy.", reply_markup=markup)
#
#
# @app.on_callback_query(filters.regex(r"buy.*"))
# def send_invoice(client: Client, callback_query: types.CallbackQuery):
#     chat_id = callback_query.message.chat.id
#     data = callback_query.data
#     _, count, price = data.split("-")
#     price = int(float(price) * 100)
#     client.send_invoice(
#         chat_id,
#         f"{count} permanent download quota",
#         "Please make a payment via Stripe",
#         f"{count}",
#         "USD",
#         [types.LabeledPrice(label="VIP", amount=price)],
#         provider_token=os.getenv("PROVIDER_TOKEN"),
#         protect_content=True,
#         start_parameter="no-forward-placeholder",
#     )
#
#
# @app.on_pre_checkout_query()
# def pre_checkout(client: Client, query: types.PreCheckoutQuery):
#     client.answer_pre_checkout_query(query.id, ok=True)
# #
#
# @app.on_message(filters.successful_payment)
# def successful_payment(client: Client, message: types.Message):
#     who = message.chat.id
#     amount = message.successful_payment.total_amount  # in cents
#     quota = int(message.successful_payment.invoice_payload)
#     ch = message.successful_payment.provider_payment_charge_id
#     free, paid = credit_account(who, amount, quota, ch)
#     if paid > 0:
#         message.reply_text(f"Payment successful! You now have {free} free and {paid} paid quota.")
#     else:
#         message.reply_text("Something went wrong. Please contact the admin.")
#     message.delete()


@app.on_message(filters.command(["stats"]))
def stats_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    cpu_usage = psutil.cpu_percent()
    total, used, free, disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()
    memory = psutil.virtual_memory()
    boot_time = psutil.boot_time()

    owner_stats = (
        "\n\n⌬─────「 Статистика 」─────⌬\n\n"
        f"<b>╭🖥️ **Использование ЦП »**</b>  __{cpu_usage}%__\n"
        f"<b>├💾 **RAM »**</b>  __{memory.percent}%__\n"
        f"<b>╰🗃️ **Использование диска »**</b>  __{disk}%__\n\n"
        f"<b>╭📤Выгрузка:</b> {sizeof_fmt(psutil.net_io_counters().bytes_sent)}\n"
        f"<b>╰📥Загрузка:</b> {sizeof_fmt(psutil.net_io_counters().bytes_recv)}\n\n\n"
        f"<b>Общая память:</b> {sizeof_fmt(memory.total)}\n"
        f"<b>Свободная память:</b> {sizeof_fmt(memory.available)}\n"
        f"<b>Используемая память:</b> {sizeof_fmt(memory.used)}\n"
        f"<b>Размер подкачки:</b> {sizeof_fmt(swap.total)} | <b>Используемая подкачка:</b> {swap.percent}%\n\n"
        f"<b>Физическая память:</b> {sizeof_fmt(total)}\n"
        f"<b>Используется:</b> {sizeof_fmt(used)} | <b>Свободно:</b> {sizeof_fmt(free)}\n\n"
        f"<b>Количество физических ЦП ядер:</b> {psutil.cpu_count(logical=False)}\n"
        f"<b>Общее количество ЦП ядер:</b> {psutil.cpu_count(logical=True)}\n\n"
        f"<b>🤖Время работы бота:</b> {timeof_fmt(time.time() - botStartTime)}\n"
        f"<b>⏲️Время работы системы:</b> {timeof_fmt(time.time() - boot_time)}\n"
    )

    user_stats = (
        "\n\n⌬─────「 Статистика 」─────⌬\n\n"
        f"<b>╭🖥️ **Использование ЦП »**</b>  __{cpu_usage}%__\n"
        f"<b>├💾 **RAM »**</b>  __{memory.percent}%__\n"
        f"<b>╰🗃️ **Использование диска »**</b>  __{disk}%__\n\n"
        f"<b>╭📤Выгрузка:</b> {sizeof_fmt(psutil.net_io_counters().bytes_sent)}\n"
        f"<b>╰📥Загрузка:</b> {sizeof_fmt(psutil.net_io_counters().bytes_recv)}\n\n\n"
        f"<b>Общая память:</b> {sizeof_fmt(memory.total)}\n"
        f"<b>Свободная память:</b> {sizeof_fmt(memory.available)}\n"
        f"<b>Используемая память:</b> {sizeof_fmt(memory.used)}\n"
        f"<b>Размер подкачки:</b> {sizeof_fmt(swap.total)} | <b>Используемая подкачка:</b> {swap.percent}%\n\n"
        f"<b>Физическая память:</b> {sizeof_fmt(total)}\n"
        f"<b>Используется:</b> {sizeof_fmt(used)} | <b>Свободно:</b> {sizeof_fmt(free)}\n\n"
        f"<b>Количество физических ЦП ядер:</b> {psutil.cpu_count(logical=False)}\n"
        f"<b>Общее количество ЦП ядер:</b> {psutil.cpu_count(logical=True)}\n\n"
        f"<b>🤖Время работы бота:</b> {timeof_fmt(time.time() - botStartTime)}\n"
        f"<b>⏲️Время работы системы:</b> {timeof_fmt(time.time() - boot_time)}\n"
    )

    if message.from_user.id in OWNER:
        message.reply_text(owner_stats, quote=True)
    else:
        message.reply_text(user_stats, quote=True)


@app.on_message(filters.command(["settings"]))
def settings_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("Отправлять файл", callback_data="document"),
                types.InlineKeyboardButton("Отправлять видео", callback_data="video"),
                types.InlineKeyboardButton("Отправлять аудио", callback_data="audio"),
            ],
            [
                types.InlineKeyboardButton(
                    "Кодек AVC1 (H.264)", callback_data="vcodec-avc1"
                ),
                types.InlineKeyboardButton("Кодек VP9 (рекомендуется)", callback_data="vcodec-vp9"),
                types.InlineKeyboardButton(
                    "Кодек АВТО", callback_data="vcodec-auto"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    "Кодек AV1 (сжатый, требовательный к ресурсам)", callback_data="vcodec-av01"
                ),
            ],
            [
                types.InlineKeyboardButton("Качество 1440p", callback_data="1440p"),
                types.InlineKeyboardButton("Качество 1080p", callback_data="1080p"),
                types.InlineKeyboardButton("Качество 720p", callback_data="720p"),
            ],
            [
                types.InlineKeyboardButton("Качество 480p", callback_data="480p"),
                types.InlineKeyboardButton("Качество 240p", callback_data="240p"),
            ],
        ]
    )

    quality = get_quality_settings(chat_id)
    send_type = get_format_settings(chat_id)
    vcodec = get_vcodec_settings(chat_id)

    localize_send_type = localize_filetype.get(send_type, send_type)
    localize_vcodec_local = localize_vcodec.get(vcodec, vcodec)

    client.send_message(
        chat_id,
        BotText.settings.format(quality, localize_send_type, localize_vcodec_local),
        reply_markup=markup,
    )


@app.on_message(filters.command(["direct"]))
def direct_download(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    message_text = message.text
    url, new_name = extract_url_and_name(message_text)
    logging.info("Direct download using aria2/requests start %s", url)
    if url is None or not re.findall(r"^https?://", url.lower()):
        message.reply_text("Укажи корректную ссылку!", quote=True)
        return
    bot_msg = message.reply_text("Запрос принят, обрабатываю...", quote=True)
    try:
        direct_entrance(client, bot_msg, url)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
        bot_msg.delete()
        return


@app.on_message(filters.command(["spdl"]))
def spdl_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    message_text = message.text
    url, new_name = extract_url_and_name(message_text)
    logging.info("spdl start %s", url)
    if url is None or not re.findall(r"^https?://", url.lower()):
        message.reply_text("Произошла какая-то ошибка, проверьте URL.", quote=True)
        return
    bot_msg = message.reply_text("Запрос принят, обрабатываю....", quote=True)
    try:
        special_download_entrance(client, bot_msg, url)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
        bot_msg.delete()
        return


@app.on_message(filters.command(["ytdl"]) & filters.group)
def ytdl_handler(client: Client, message: types.Message):
    # for group only
    init_user(message.from_user.id)
    client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    message_text = message.text
    url, new_name = extract_url_and_name(message_text)
    logging.info("ytdl start %s", url)
    if url is None or not re.findall(r"^https?://", url.lower()):
        message.reply_text("Check your URL.", quote=True)
        return

    bot_msg = message.reply_text("Group download request received.", quote=True)
    try:
        youtube_entrance(client, bot_msg, url)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
        bot_msg.delete()
        return


def check_link(url: str):
    ytdl = yt_dlp.YoutubeDL()
    if re.findall(r"^https://www\.youtube\.com/channel/", url) or "list" in url:
        # TODO maybe using ytdl.extract_info
        raise ValueError("📛 Загрузка плейлистов отключена!")

    if not M3U8_SUPPORT and (re.findall(r"m3u8|\.m3u8|\.m3u$", url.lower())):
        return "m3u8 links are disabled."


@app.on_message(filters.incoming & filters.text)
@private_use
def download_handler(client: Client, message: types.Message):
    chat_id = message.from_user.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    url = message.text
    logging.info("start %s", url)

    try:
       # if not re.findall(r"^https?://", url.lower()):
       #     reply = message.reply_text("🔎 Ищу ролики на YouTube...", quote=True)
       #     text = search_ytb(url)
       #     client.edit_message_text(chat_id=reply.chat.id, message_id=reply.id, text=text, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
       #     return
       #  else:
       check_link(url)
       # raise pyrogram.errors.exceptions.FloodWait(10)
       bot_msg: types.Message | Any = message.reply_text("▶️ Загружаю...\nМогут наблюдаться проблемы с AV1 кодеком.", quote=True)
       client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
       youtube_entrance(client, bot_msg, url)
    except pyrogram.errors.Flood as e:
        f = BytesIO()
        f.write(str(e).encode())
        f.write(b"Your job will be done soon. Just wait!")
        f.name = "Please wait.txt"
        message.reply_document(f, caption=f"Пожалуйста, подожди {e} секунд...", quote=True)
        f.close()
        client.send_message(OWNER, f"Пожалуйста, подожди {e} секунд...")
        time.sleep(e.value)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
    except Exception as e:
        logging.error("Download failed", exc_info=True)
        message.reply_text(f"❌ Произошла ошибка!: {e}", quote=True)


@app.on_callback_query(filters.regex(r"document|video|audio"))
def format_callback(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    logging.info("Setting %s file type to %s", chat_id, data)
    callback_query.answer(
        f"Вы установили тип отправки: {localize_filetype.get(callback_query.data, callback_query.data)}"
    )
    set_user_settings(chat_id, "format", data)


@app.on_callback_query(filters.regex(r"1440p|1080p|720p|480p|240p"))
def quality_callback(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    logging.info("Setting %s download quality to %s", chat_id, data)
    callback_query.answer(f"Вы установили качество видео: {callback_query.data}")
    set_user_settings(chat_id, "quality", data)


@app.on_callback_query(filters.regex(r"vcodec-vp9|vcodec-avc1|vcodec-av01|vcodec-auto"))
def vcodec_callback(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    logging.info("Setting %s download vcodec to %s", chat_id, data)
    callback_query.answer(f"Вы установили кодек: {localize_vcodec.get(callback_query.data, callback_query.data)}")
    set_user_settings(chat_id, "vcodec", data)

async def uptime_push():
    loop = asyncio.get_running_loop()
    while True:
        await loop.run_in_executor(None, requests.post, UPTIME_URL)
        await asyncio.sleep(55)

async def main():
    asyncio.create_task(uptime_push())
    botStartTime = time.time()
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_free, "cron", hour=0, minute=0)
    scheduler.start()
    banner = f"""
▌ ▌         ▀▛▘     ▌       ▛▀▖              ▜            ▌
▝▞  ▞▀▖ ▌ ▌  ▌  ▌ ▌ ▛▀▖ ▞▀▖ ▌ ▌ ▞▀▖ ▌  ▌ ▛▀▖ ▐  ▞▀▖ ▝▀▖ ▞▀▌
 ▌  ▌ ▌ ▌ ▌  ▌  ▌ ▌ ▌ ▌ ▛▀  ▌ ▌ ▌ ▌ ▐▐▐  ▌ ▌ ▐  ▌ ▌ ▞▀▌ ▌ ▌
 ▘  ▝▀  ▝▀▘  ▘  ▝▀▘ ▀▀  ▝▀▘ ▀▀  ▝▀   ▘▘  ▘ ▘  ▘ ▝▀  ▝▀▘ ▝▀▘

By @BennyThink, VIP Mode: {ENABLE_VIP}
    """
    print(banner)
    app.run()
    await asyncio.Future()



if __name__ == "__main__":
    main()
