#!/usr/bin/env python3
# coding: utf-8

# ytdlbot - instagram.py

import time
import pathlib
import re

import filetype
import requests
from engine.base import BaseDownloader


class InstagramDownload(BaseDownloader):
    def extract_code(self):
        patterns = [
            # Instagram stories highlights
            r"/stories/highlights/([a-zA-Z0-9_-]+)/",
            # Posts
            r"/p/([a-zA-Z0-9_-]+)/",
            # Reels
            r"/reel/([a-zA-Z0-9_-]+)/",
            # TV
            r"/tv/([a-zA-Z0-9_-]+)/",
            # Threads post (both with @username and without)
            r"(?:https?://)?(?:www\.)?(?:threads\.net)(?:/[@\w.]+)?(?:/post)?/([\w-]+)(?:/?\?.*)?$",
        ]

        for pattern in patterns:
            match = re.search(pattern, self._url)
            if match:
                if pattern == patterns[0]:  # Check if it's the stories highlights pattern
                    # Return the URL as it is
                    return self._url
                else:
                    # Return the code part (first group)
                    return match.group(1)

        return None

    def _setup_formats(self) -> list | None:
        pass

    def _download(self, formats=None):
        try:
            resp = requests.get(f"http://instagram:15000/?url={self._url}").json()
        except Exception as e:
            self._bot_msg.edit_text(f"❌ Произошла ошибка!\n\n`{e}`")
            pass

        code = self.extract_code()
        counter = 1
        video_paths = []

        if url_results := resp.get("data"):
            for link in url_results:
                try:
                    req = requests.get(link, stream=True)
                    length = int(req.headers.get("content-length", 0) or req.headers.get("x-full-image-content-length", 0))
                    filename = f"Instagram_{code}-{counter}"
                    save_path = pathlib.Path(self._tempdir.name, filename)
                    chunk_size = 8192
                    downloaded = 0
                    start_time = time.time()

                    with open(save_path, "wb") as fp:
                        for chunk in req.iter_content(chunk_size):
                            if chunk:
                                downloaded += len(chunk)
                                fp.write(chunk)

                                elapsed_time = time.time() - start_time
                                if elapsed_time > 0:
                                    speed = downloaded / elapsed_time  # bytes per second

                                    if speed >= 1024 * 1024:  # MB/s
                                        speed_str = f"{speed / (1024 * 1024):.2f}MB/s"
                                    elif speed >= 1024:  # KB/s
                                        speed_str = f"{speed / 1024:.2f}KB/s"
                                    else:  # B/s
                                        speed_str = f"{speed:.2f}B/s"

                                    if length > 0:
                                        eta_seconds = (length - downloaded) / speed
                                        if eta_seconds >= 3600:
                                            eta_str = f"{eta_seconds / 3600:.1f}h"
                                        elif eta_seconds >= 60:
                                            eta_str = f"{eta_seconds / 60:.1f}m"
                                        else:
                                            eta_str = f"{eta_seconds:.0f}s"
                                    else:
                                        eta_str = "N/A"
                                else:
                                    speed_str = "N/A"
                                    eta_str = "N/A"

                                # dictionary for calling the download_hook
                                d = {
                                    "status": "downloading",
                                    "downloaded_bytes": downloaded,
                                    "total_bytes": length,
                                    "_speed_str": speed_str,
                                    "_eta_str": eta_str
                                }

                                self.download_hook(d)

                    if ext := filetype.guess_extension(save_path):
                        new_path = save_path.with_suffix(f".{ext}")
                        save_path.rename(new_path)
                        save_path = new_path

                    video_paths.append(save_path)
                    counter += 1

                except Exception as e:
                    self._bot_msg.edit_text(f"❌ Произошла ошибка!\n\n`{e}`")
                    return []

        return video_paths

    def _start(self):
        self._download()
        self._upload()
