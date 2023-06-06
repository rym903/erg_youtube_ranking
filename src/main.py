import pandas as pd
import re
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build, Resource

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# 動画の再生時間(PT3M58S)を秒に変換する
def convert_duration(duration: str) -> int:
    # PT3M58S -> 3:58 -> 238
    pattern = r"PT(\d+)M(\d+)S"
    match = re.match(pattern, duration)
    if match:
        minute = int(match.group(1))
        second = int(match.group(2))
        return minute * 60 + second
    else:
        return None


# 動画の再生時間と再生回数を取得する
def get_video_duration_and_viewcount(video_id: str, youtube_api: Resource) -> tuple:
    video_response = (
        youtube_api.videos()
        .list(part="contentDetails,statistics", id=video_id)
        .execute()
    )
    duration = video_response["items"][0]["contentDetails"]["duration"]
    viewcount = video_response["items"][0]["statistics"]["viewCount"]
    return convert_duration(duration), viewcount


# 各曲のYouTubeの再生回数を取得する
def get_view_count(row: pd.Series, youtube_api: Resource) -> int:
    # 曲名とアーティスト名を取得
    song_name = row["name"]
    artist_name = row["artist"]
    playtime = row["playtime"]
    view_count_sum = 0

    # YouTube Data APIを使用して、曲名とアーティスト名を検索 (再生時間でもフィルタリングできる)
    search_response = (
        youtube_api.search()
        .list(
            part="snippet",
            q=f"{song_name} {artist_name}",
            order="viewCount",
            type="video",
            maxResults=5,
        )
        .execute()
    )

    for item in search_response["items"]:
        videoId = item["id"]["videoId"]
        video_duration, view_count = get_video_duration_and_viewcount(
            videoId, youtube_api
        )
        if playtime - 10 <= video_duration <= playtime + 10:
            view_count_sum += int(view_count)

    return view_count_sum


def join_view_count_on_youtube():
    input_file = "song_list_sample.csv"
    output_file = "song_list_sample_with_view_count.csv"
    youtube_api = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # input_fileへの絶対パス
    input_path = os.path.join(os.path.dirname(__file__), f"../input_data/{input_file}")
    song_df = pd.read_csv(input_path, header=0)

    # 1行ごとに処理を行う
    song_df["view_count"] = song_df.apply(get_view_count, args=(youtube_api,), axis=1)

    # output_fileへの絶対パス
    output_path = os.path.join(
        os.path.dirname(__file__), f"../output_data/{output_file}"
    )
    song_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    join_view_count_on_youtube()
