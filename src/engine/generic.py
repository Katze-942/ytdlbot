#!/usr/bin/env python3
# coding: utf-8

# ytdlbot - generic.py

import logging
import os
from pathlib import Path

import yt_dlp

from config import AUDIO_FORMAT
from utils import is_youtube
from database.model import get_format_settings, get_quality_settings
from engine.base import BaseDownloader


def match_filter(info_dict):
    if info_dict.get("is_live"):
        raise NotImplementedError("⏏️ Я не могу загружать трансляции. Пожалуйста, дождитесь окончания стрима")
    return None  # Allow download for non-live videos


class YoutubeDownload(BaseDownloader):
    @staticmethod
    def get_format(m):
        return [
            # Видео, которые по длине не больше двух часов в основном
            f"bestvideo[vcodec^=vp][height<={m}][filesize<1.5G]+(bestaudio[language=ru][filesize<0.5G]/bestaudio[filesize<0.5G])",
            f"bestvideo[height<={m}][filesize<1.5G]+(bestaudio[language=ru][filesize<0.5G]/bestaudio[filesize<0.5G])",

            # Очень длинные видео
            f"bestvideo[vcodec^=vp][height<={m}][filesize<1G]+(bestaudio[language=ru][filesize<1G]/bestaudio[filesize<1G])",
            f"bestvideo[height<={m}][filesize<1G]+(bestaudio[language=ru][filesize<1G]/bestaudio[filesize<1G])",

            # Видео, у которых нет чётких размеров
            f"(bestvideo[height<={m}]/bestvideo)+(bestaudio[language=ru]/bestaudio)",

            # Просто видео или просто аудио
            f"(bestvideo[height<={m}]/bestvideo)/(bestaudio[language=ru]/bestaudio)",

            "best"
        ]

    def _setup_formats(self) -> list | None:
        # if not is_youtube(self._url):
        #     return [None]

        quality, format_ = get_quality_settings(self._chat_id), get_format_settings(self._chat_id)
        # quality: high, medium, low, custom
        # format: audio, video, document
        formats = []
        defaults = [
            # webm , vp9 and av01 are not streamable on telegram, so we'll extract only mp4
            "bestvideo[ext=mp4][vcodec!*=av01][vcodec!*=vp09]+bestaudio[ext=m4a]/bestvideo+bestaudio",
            "bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/best[vcodec^=avc]/best",
            None,
        ]
        audio = AUDIO_FORMAT or "m4a"
        audioformats = [f"bestaudio[ext={audio}][language=ru]/bestaudio[ext={audio}]", "bestaudio[ext=m4a][language=ru]/bestaudio[ext=m4a]", "bestaudio[language=ru]/bestaudio", "best"]
        maps = {
            "high-audio": audioformats,
            "high-video": self.get_format(1080),
            "high-document": self.get_format(1080),
            "medium-audio": audioformats,  # no mediumaudio :-(
            "medium-video": self.get_format(720),
            "medium-document": self.get_format(720),
            "low-audio": audioformats,
            "low-video": self.get_format(480),
            "low-document": self.get_format(480),
            "custom-audio": "",
            "custom-video": "",
            "custom-document": "",
        }

        if quality == "custom":
            pass
            # TODO not supported yet
            # get format from ytdlp, send inlinekeyboard button to user so they can choose
            # another callback will be triggered to download the video
            # available_options = {
            #     "480P": "best[height<=480]",
            #     "720P": "best[height<=720]",
            #     "1080P": "best[height<=1080]",
            # }
            # markup, temp_row = [], []
            # for quality, data in available_options.items():
            #     temp_row.append(types.InlineKeyboardButton(quality, callback_data=data))
            #     if len(temp_row) == 3:  # Add a row every 3 buttons
            #         markup.append(temp_row)
            #         temp_row = []
            # # Add any remaining buttons as the last row
            # if temp_row:
            #     markup.append(temp_row)
            # self._bot_msg.edit_text("Choose the format", reply_markup=types.InlineKeyboardMarkup(markup))
            # return None

        formats.extend(maps[f"{quality}-{format_}"])
        return formats

    def _download(self, formats) -> list:
        output = Path(self._tempdir.name, "%(title).70s.%(ext)s").as_posix()
        ydl_opts = {
            "verbose": True,
            "progress_hooks": [lambda d: self.download_hook(d)],
            "outtmpl": output,
            "restrictfilenames": False,
            "quiet": True,
            "match_filter": match_filter,
            "embedthumbnail": True,
            "writethumbnail": True,
            "cookies": "firefox",
            "format": '/'.join(formats)
        }

        if self._url.startswith("https://drive.google.com"):
            formats = ["source"] + formats

        if get_format_settings(self._chat_id) == "audio":
            ydl_opts["postprocessors"] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0'
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            }]
        else:
            if get_format_settings(self._chat_id) == "video":
                ydl_opts["merge_output_format"] = "mp4"

            ydl_opts["postprocessors"] = [{
                'key': 'FFmpegMetadata',
                'add_metadata': True
            },
            {
                'key': 'EmbedThumbnail'
            }]

        # setup cookies for youtube only
        if is_youtube(self._url):
            # use cookies from browser firstly
            if browsers := os.getenv("BROWSERS"):
                ydl_opts["cookiesfrombrowser"] = browsers.split(",")
            if os.path.isfile("youtube-cookies.txt") and os.path.getsize("youtube-cookies.txt") > 100:
                ydl_opts["cookiefile"] = "youtube-cookies.txt"
            # try add extract_args if present
            if potoken := os.getenv("POTOKEN"):
                ydl_opts["extractor_args"] = {"youtube": ["player-client=web,default", f"po_token=web+{potoken}"]}
                # for new version? https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide
                # ydl_opts["extractor_args"] = {
                #     "youtube": [f"po_token=web.player+{potoken}", f"po_token=web.gvs+{potoken}"]
                # }

        files = None
        logging.info("yt-dlp options: %s", ydl_opts)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self._url])
        files = list(Path(self._tempdir.name).glob("*"))
        return files

    def _start(self, formats=None):
        # start download and upload, no cache hit
        # user can choose format by clicking on the button(custom config)
        default_formats = self._setup_formats()
        if formats is not None:
            # formats according to user choice
            default_formats = formats + self._setup_formats()
        self._download(default_formats)
        self._upload()
