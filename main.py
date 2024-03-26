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


# Parse command line arguments
args = parse_args(sys.argv[1:])

# Check if all required arguments are provided
required_args = ["client_id", "client_secret", "redirect_uri"]
for arg in required_args:
    if arg not in args:
        print(f"Error: {arg} is not provided.")
        sys.exit(1)

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

results = sp.current_user_saved_tracks(limit=10)

last_10_songs = []
for idx, item in enumerate(results["items"]):
    track = item["track"]
    print(idx, track["artists"][0]["name"], " – ", track["name"])
    last_10_songs.append(item)

last_10_songs.reverse()

# Use the credentials file to authenticate
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet (replace 'Your_Sheet_Name' with your actual sheet name)
sheet = client.open("Spotify Saved Tracks").sheet1

# Get the values of the 'Title' column starting from row 4
title_column_values = sheet.col_values(2)[
    3:
]  # replace 1 with the index of your 'Title' column

# Find the last non-empty cell in the column
last_song_added = next(
    (title for title in reversed(title_column_values) if title), None
)


# Get the index of the last song added in the last 10 songs retrieved
index = next(
    (
        index
        for (index, d) in enumerate(last_10_songs)
        if d["track"]["name"] == last_song_added
    ),
    None,
)

if index == None or index == 9:  # 9 implies all 10 are already in the spreadsheet.
    print("All 10 most recently liked songs are already in the spreadsheet.")
else:
    # Append the remaining songs to the Google Sheet
    for song in last_10_songs[index + 1 :]:
        row = [
            song["track"]["name"],
            song["track"]["artists"][0]["name"],
            song["track"]["album"]["name"],
        ]
        sheet.append_row(row)

# http://localhost/?code=AQDVfWBbBP8a194BBLfSsLFNfPjlWbA3L0_OrKXQo7PJc7RjkvfkXooxpveGGc0_gZ8EsP0IaULMT8Q9rJPgTtqCwwcXP2KoZfZN5DJcIMCxtFR_C3qQ4LCMImPoys_uxp_N8lxsZwryfOLGhcHomXkBzKVf5xv6rehxXxtl6XgpwxWsLlEJ
# Bearer AQDVfWBbBP8a194BBLfSsLFNfPjlWbA3L0_OrKXQo7PJc7RjkvfkXooxpveGGc0_gZ8EsP0IaULMT8Q9rJPgTtqCwwcXP2KoZfZN5DJcIMCxtFR_C3qQ4LCMImPoys_uxp_N8lxsZwryfOLGhcHomXkBzKVf5xv6rehxXxtl6XgpwxWsLlEJ
