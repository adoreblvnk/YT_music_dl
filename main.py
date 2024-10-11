import re
from pathlib import Path

import yt_dlp
from mutagen.id3 import TALB, TIT2, TPE1
from mutagen.mp3 import MP3

FOLDER: str = "music"
URLS: list[str] = None

YDL_OPTS = {
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
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
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

    # standardising title string
    title = new_file.split(" - ")[1]
    # remove | <channel>, eg Artist - Song | Pressplay
    title = re.sub(r"\|.*", "", title)
    # remove (.*?), eg Artist - Song (Official Music Video)
    title = re.sub(r"\((official|music).*?\)", "", title, flags=re.IGNORECASE)
    # remove #.*?, eg Artist - Song #Album
    title = re.sub(r"#\w*", "", title)
    # remove [.*], eg Artist - Song [S2.E1]
    title = re.sub(r"\[.*\]", "", title)
    # use w/ (not W/) for with, eg Artist - Song W/ Artist
    title = re.sub(r"(w|W)/.*", "", title)
    title = title.strip()

    # standardising artist list
    artist_list = new_file.split(" - ")[0].split(", ")
    # remove duplicate artists that appear in title
    artist_list = [i for i in artist_list if i not in title]

    # creating artist string
    artist_str = " x ".join(artist_list)
    # use x (not X) to separate artists, eg Artist X Artist - Song
    artist_str = re.sub(r" X ", " x ", artist_str)
    artist_str = artist_str.strip()

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
