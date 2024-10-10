import re
from pathlib import Path

import yt_dlp
from mutagen.id3 import TALB, TIT2, TPE1
from mutagen.mp3 import MP3

FOLDER = "music"
URLS = None
URLS = []

ydl_opts = {
    "format": "mp3/bestaudio",
    # if music prepend "Artist, Artist - " else do nothing
    "outtmpl": {
        "default": f"{FOLDER}/%(artist&{{}} - |)s%(title)s.%(ext)s",
        "pl_thumbnail": "",
    },
    "ignoreerrors": True,
    "writethumbnail": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        },
        {
            "key": "FFmpegMetadata",
            "add_metadata": True,
        },
        {
            "key": "EmbedThumbnail",
            "already_have_thumbnail": False,
        },
    ],
    "postprocessor_args": {
        # square thumbnail
        "embedthumbnail+ffmpeg_o": [
            "-c:v",
            "mjpeg",
            "-vf",
            "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
        ],
    },
}

Path(FOLDER).mkdir(exist_ok=True)

if URLS is not None and len(URLS) > 0:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(URLS)

for file in Path(FOLDER).iterdir():
    # standardising filename
    new_file = Path(file).stem
    # replacing characters
    new_file = (
        new_file.replace("｜", "|")
        .replace("⧸", "/")
        .replace("？", "?")
        .replace("＊", "*")
    )
    # remove | <channel>, eg Artist - Song | Pressplay
    new_file = re.sub(r"\|.*", "", new_file)
    # remove (.*?), eg Artist - Song (Official Music Video)
    new_file = re.sub(r"\((official|music).*?\)", "", new_file, flags=re.IGNORECASE)
    # remove [.*], eg Artist - Song [S2.E1]
    new_file = re.sub(r"\[.*\]", "", new_file)

    # standardising artist string
    artist_str = new_file.split(" - ")[0]
    # use x (not X) to separate artists, eg Artist X Artist - Song
    artist_str = re.sub(r" X ", " x ", artist_str)
    # use x (not , ) to separate artists
    artist_str = re.sub(r", ", " x ", artist_str)
    artist_str = artist_str.strip()

    # standardising title string
    title = new_file.split(" - ")[1]
    # remove #.*?, eg Artist - Song #Album
    title = re.sub(r"#\w*", "", title)
    # use w/ (not W/) for with, eg Artist - Song W/ Artist
    title = re.sub(r"(w|W)/.*", "", title)
    title = title.strip()

    new_file_name = Path(f"{FOLDER}/{artist_str} - {title}.mp3")
    Path(file).rename(new_file_name)  # rename file
    print(f"{artist_str} - {title}")

    # standardising artists further for metadata
    artists = re.sub(r"\(.*?\) ", "", artist_str)  # remove parentheses & hashtags
    artists = re.sub(r"#\w* ", "", artists)

    # add audio tags
    audio = MP3(new_file_name)
    if audio.tags is None:
        audio.add_tags()
    audio.tags["TPE1"] = TPE1(text=artists)  # add artists
    audio.tags["TIT2"] = TIT2(text=title)  # add title
    audio.tags["TALB"] = TALB(text=title)  # add album name, possibly incorrect but idc
    audio.tags.pop("TXXX:description", None)  # del comments
    audio.tags.pop("TXXX:synopsis", None)
    audio.save()
