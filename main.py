import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Define a function to parse command line arguments
def parse_args(args):
    arg_dict = {}
    for arg in args:
        key, value = arg.split("=")
        arg_dict[key] = value
    return arg_dict


# Check if all required arguments are provided
def validate_args(args):
    required_args = ["client_id", "client_secret", "redirect_uri", "credentials_file"]
    for arg in required_args:
        if arg not in args:
            print(f"Error: {arg} is not provided.")
            sys.exit(1)


def authenticate_spotify(args):
    # Assign command line arguments to variables
    scope = "user-library-read"
    client_id = args["client_id"]
    client_secret = args["client_secret"]
    redirect_uri = args["redirect_uri"]

    # Setup Spotify object...
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
    )
    return sp


def get_spotify_songs(sp, top=10):
    results = sp.current_user_saved_tracks(limit=top)
    songs = []
    for idx, item in enumerate(results["items"]):
        track = item["track"]
        print(idx, track["artists"][0]["name"], " – ", track["name"])
        songs.append(item)

    songs.reverse()
    return songs


def authenticate_google_sheets(credentials_file):
    # Use the credentials file to authenticate
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    return client


def append_songs_to_google_sheets(songs, sheets_client):
    # Open the Google Sheet (replace 'Your_Sheet_Name' with your actual sheet name)
    sheet = sheets_client.open("Spotify Saved Tracks").sheet1

    # Get the values of the 'Title' column starting from row 4
    title_column_values = sheet.col_values(2)[
        3:
    ]  # replace 1 with the index of your 'Title' column

    # Find the last non-empty cell in the column
    last_song_added = next(
        (title for title in reversed(title_column_values) if title), None
    )

    # Get the index of the last song added in the last n number of songs retrieved
    index = next(
        (
            index
            for (index, d) in enumerate(songs)
            if d["track"]["name"] == last_song_added
        ),
        None,
    )

    max_song_index = len(songs) - 1
    if (
        index == None or index == max_song_index
    ):  # 1 song less than the total number of songs means they all are already in the spreadsheet.
        print(
            f"All {len(songs)} most recently liked songs are already in the spreadsheet."
        )
    else:
        # Append the remaining songs to the Google Sheet
        for song in songs[index + 1 :]:
            row = [
                song["track"]["name"],
                song["track"]["artists"][0]["name"],
                song["track"]["album"]["name"],
            ]
            sheet.append_row(row)


def main():
    # Parse command line arguments
    args = parse_args(sys.argv[1:])
    # app exits if this validation fails.
    validate_args(args)

    authenticate_spotify(args)
    songs = get_spotify_songs(args["top"])

    sheets_client = authenticate_google_sheets(
        credentials_file=args["credentials_file"]
    )
    append_songs_to_google_sheets(songs, sheets_client)
