import pandas as pd
import os
import re
import requests
from bs4 import BeautifulSoup

from time import sleep

GYO_LIST = [
    "agyo",
    "kagyo",
    "sagyo",
    "tagyo",
    "nagyo",
    "hagyo",
    "magyo",
    "yagyo",
    "ragyo",
    "wagyo",
]
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "../data/song_list_from_erogamescape.csv"
)


# HH:MM:SSの形式の文字列を秒数に変換する
def convert_playtime_to_second(playtime: str) -> int:
    # 3:58 -> 238
    pattern = r"(\d+):(\d+):(\d+)"
    match = re.match(pattern, playtime)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3))
        return hour * 3600 + minute * 60 + second
    else:
        return None


def get_song_info_from_erogamescape(row) -> tuple:
    row_td_list = row.find_all("td")
    song_detail_page_url = row_td_list[0].find("a").get("href", None)
    if song_detail_page_url is None:
        return [None, None, None]
    playtime = get_playtime_from_erogamescape(song_detail_page_url)
    song_title = row_td_list[0].text.strip()
    artist = (
        row_td_list[1]
        .text.strip()
        .replace(" ", "")
        .replace("\r\n", "")
        .replace("/", " & ")
    )
    return song_title, artist, playtime


def get_playtime_from_erogamescape(song_detail_page_url: str) -> int:
    song_detail_page_url = f"https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/{song_detail_page_url}"

    song_detail_soup = BeautifulSoup(
        requests.get(song_detail_page_url).text,
        "html.parser",
    )
    playtime = convert_playtime_to_second(
        song_detail_soup.find(id="playtime").find("td").text
    )
    return playtime


def get_song_list_from_erogamescape():
    info_list = []
    for gyo in GYO_LIST:
        table = BeautifulSoup(
            requests.get(
                f"https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/musiclist.php?mode=aiueo&limit=oped&gyou={gyo}#form"
            ).text,
            "html.parser",
        ).find(id="musiclist")
        for i, row in enumerate(table.find_all("tr")[1:]):
            song_title, artist, playtime = get_song_info_from_erogamescape(row)
            if song_title is None:
                continue
            info_list.append([song_title, artist, playtime])
            sleep(1)
            if i == 10:
                break
    df = pd.DataFrame(info_list, columns=["title", "artist", "playtime"])
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    get_song_list_from_erogamescape()
