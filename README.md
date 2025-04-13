# ytdlbot

Это форк бота для загрузки видео, файлов и музыки. Он создан для личного пользования, поэтому некоторые функции могут работать не так, как надо. Вот полный список изменений:
- Перевод на русский язык (неполный)
- Другое оформление различных текстов (используются эмодзи)
- **Переработана система миниатюр:**
  - Миниатюра (обложка) берётся из сервиса, а не из первого кадра ролика
  - Миниатюра встраивается напрямую в файл, а не только при предпросмотре ролика
  - Миниатюра встраивается и в аудиофайлы
- **Изменил правила, по которым выбирается формат для загрузки:**
  - По возможности выбираются видео с VP9-кодеком, так как его поддержка наиболее распространена по сравнению с AVC1
  - Если есть русская аудиодорожка, то ролик загружается с ней
  - Выбираются форматы, которые будут весить меньше 2 гигабайт (если сервис поддерживает). Это значит, что большие ролики могут загрузиться в более низком разрешении, чем установлено в `/settings`
  - Ролики загружаются в наиболее оптимальном контейнере, а не принудительно в mp4 (который чаще всего весил больше остальных)
  - Если не удаётся получить никаких данных, то загружается ролик «как есть»
  - Музыка будет загружаться либо в AUDIO_FORMAT, либо в m4a, либо в любом доступном формате. Ранее использовался строгий формат, что мешало загрузке с многих сервисов
- По умолчанию включено отображение дебаг-информации от yt-dlp
- Используются Firefox cookies для корректной работы некоторых сервисов, например, Яндекс.Музыки
- Преобразование аудио, встраивание миниатюр и генерация видео в mp4-контейнере теперь выполняются yt-dlp на этапе постобработки
- У всех файлов теперь присутствуют встроенные метаданные (например, эпизоды в видео, описание, заголовок и т.д.)
- Отключил команды `/buy`, так как они не нужны
- Команда `/stats` показывает одинаковую информацию для создателя и остальных пользователей
- Вернул функцию поиска роликов

[![docker image](https://github.com/tgbot-collection/ytdlbot/actions/workflows/builder.yaml/badge.svg)](https://github.com/tgbot-collection/ytdlbot/actions/workflows/builder.yaml)

**YouTube Download Bot🚀🎬⬇️**

This Telegram bot allows you to download videos from YouTube and [other supported websites](#supported-websites).

# Usage

* EU🇪🇺: [https://t.me/benny_2ytdlbot](https://t.me/benny_2ytdlbot)
* Singapore🇸🇬:[https://t.me/benny_ytdlbot](https://t.me/benny_ytdlbot)

* Join Telegram Channel https://t.me/ytdlbot0 for updates.

Just send a link directly to the bot.

# Supported websites

* YouTube
* Any websites [supported by yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

  ### Specific link downloader (Use /spdl for these links)
    * Instagram (Videos, Photos, Reels, IGTV & carousel)
    * Pixeldrain
    * KrakenFiles

# Features

1. fast download and upload.
2. No ads
3. download & upload progress bar
4. download quality selection
5. upload format: file, video, audio
6. cache mechanism - download once for the same video.
7. Supports multiple download engines (yt-dlp, aria2, requests).

> ## Limitations
> Due to limitations on servers and bandwidth, there are some restrictions on this free service.
> * Each user is limited to 1 free downloads every day.

# Screenshots

## Normal download

![](assets/1.jpeg)

## Instagram download

![](assets/instagram.png)

![](assets/2.jpeg)

# How to deploy?

This bot can be deployed on any platform that supports Python.

## Run natively on your machine

> Project use PDM to manage dependencies.

1. <details>
    <summary>Install PDM</summary>

    You can install using pip: `pip install --user pdm`
    or for detailed instructions: [Official Docs](https://pdm-project.org/en/latest/#installation)
  
   </details>

2. Install modules using PDM: `pdm install`, or the old way use `pip install -r requirements.txt`

3. <details>
    <summary>Setting up config file</summary>

    ```
    cp .env.example .env
    ```
    
    Fill the fields in `.env`. For more information, see the comments in the `.env.example` file.

    **- Required Fields**
    - `WORKERS`: Number of workers (default is 100)
    - `APP_ID`: Telegram app ID
    - `APP_HASH`: Telegram app hash
    - `BOT_TOKEN`: Your telegram bot token
    - `OWNER`: Owner ID (separate by `,`)
    - `AUTHORIZED_USER`: List of authorized users ids, (separate by `,`)
    - `DB_DSN`: Your database URL (mysql+pymysql://user:pass@mysql/dbname) or SQLite (sqlite:///db.sqlite)
    - `REDIS_HOST`: Redis host

    **- Optional Fields**
    - `ENABLE_FFMPEG`: Enable FFMPEG for video processing (True/False)
    - `AUDIO_FORMAT`: Desired audio format (e.g.:- mp3, wav)
    - `ENABLE_ARIA2`: Enable Aria2 for downloads (True/False)
    - `RCLONE_PATH`: Path to Rclone executable
    - `ENABLE_VIP`: Enable VIP features (True/False)
    - `PROVIDER_TOKEN`: Payment provider token from Stripe
    - `FREE_DOWNLOAD`: Free downloads allowed per user
    - `RATE_LIMIT`: Rate limit for requests
    - `TMPFILE_PATH`: Path for temporary/download files (ensure the directory exists and is writable)
    - `TG_NORMAL_MAX_SIZE`: Maximum size for Telegram uploads in MB
    - `CAPTION_URL_LENGTH_LIMIT`: Maximum URL length in captions
    - `POTOKEN`: Your PO Token.  [PO-Token-Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
    - `BROWSERS`: Browser to handle 'cookies from browser', i.e. firefox
  </details>

4. Activate virtual environment that created by PDM: `source .venv/bin/activate`

5. Finally run the bot: `python src/main.py`

## Docker

One line command to run the bot

```shell
docker run --env-file .env bennythink/ytdlbot
```

# Command

```
start - Let's start
about - What's this bot?
help - Help
spdl - Use to download specific link downloader links
direct - Download using aria2/requests engines
ytdl - Download video in group
settings - Set your preference
unsub - Unsubscribe from YouTube Channel
ping - Ping the Bot
stats - Server and bot stats
buy - Buy quota.
```

# Test data

<details><summary>Tap to expand</summary>

## Test video

https://www.youtube.com/watch?v=V3RtA-1b_2E

## Test Playlist

https://www.youtube.com/playlist?list=PL1Hdq7xjQCJxQnGc05gS4wzHWccvEJy0w

## Test twitter

https://twitter.com/nitori_sayaka/status/1526199729864200192
https://twitter.com/BennyThinks/status/1475836588542341124

## Test instagram

* single image: https://www.instagram.com/p/CXpxSyOrWCA/
* single video: https://www.instagram.com/p/Cah_7gnDVUW/
* reels: https://www.instagram.com/p/C0ozGsjtY0W/
* image carousel: https://www.instagram.com/p/C0ozPQ5o536/
* video and image carousel: https://www.instagram.com/p/C0ozhsVo-m8/

## Test Pixeldrain

https://pixeldrain.com/u/765ijw9i

## Test KrakenFiles

https://krakenfiles.com/view/oqmSTF0T5t/file.html

</details>

# Donation

Found this bot useful? You can donate to support the development of this bot.

## Donation Platforms

* [Buy me a coffee](https://www.buymeacoffee.com/bennythink)
* [GitHub Sponsor](https://github.com/sponsors/BennyThink)

## Stripe

You can choose to donate via Stripe.

| USD(Card, Apple Pay and Google Pay)              | CNY(Card, Apple Pay, Google Pay and Alipay)      |
|--------------------------------------------------|--------------------------------------------------|
| [USD](https://buy.stripe.com/cN203sdZB98RevC3cd) | [CNY](https://buy.stripe.com/dR67vU4p13Ox73a6oq) |
| ![](assets/USD.png)                              | ![](assets/CNY.png)                              |

## Cryptocurrency

TRX or USDT(TRC20)

![](assets/tron.png)

```
TF9peZjC2FYjU4xNMPg3uP4caYLJxtXeJS
```

# License

Apache License 2.0
