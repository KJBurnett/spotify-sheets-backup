# File: main.py

"""
The `main` function in this script handles:
- Setting up working dir (`os.chdir(script_dir)`).
- Parsing command line arguments.
- Validating parsed args (exits if invalid).
- Authenticating Spotify access via `authenticate_spotify`.
- Fetching top songs from Spotify based on user preferences.
- Authenticating Google Sheets using OAuth2 client flow through `authenticate_google_sheets` with credentials file specified in CLI.
- Interacting w/ target spreadsheet to append fetched Spotify songs at end of given range within worksheet.
Overall purpose: Automates tracking favorite music trends across short/medium/long term directly into shared docs via bridge b/w Spotify & Google Sheets services.
"""

import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from src.song import parseSpotifySongUrl, getCurrentDatetime


# Define a function to parse command line arguments
def parse_args(args):
    arg_dict = {}
    for arg in args:
        key, value = arg.split("=")
        arg_dict[key] = value

    # Check if required arguments are missing
    required_args = ["client_id", "client_secret", "redirect_uri", "credentials_file"]
    missing_args = [arg for arg in required_args if arg not in arg_dict]

    if missing_args:
        # If any required arguments are missing, load from config.json
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                config = json.load(file)
                arg_dict.update(config)
        else:
            print(
                f"Error: {', '.join(missing_args)} are not provided and config.json is missing."
            )
            sys.exit(1)

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
    import spotipy
    import requests

    results = None
    try:
        results = sp.current_user_saved_tracks(limit=top)
    except (spotipy.oauth2.SpotifyOauthError, requests.exceptions.HTTPError) as e:
        print(
            "Spotify authentication error detected (likely due to revoked/expired token).\nAttempting to remove .cache and prompting for re-authentication..."
        )
        cache_path = ".cache"
        import os

        if os.path.exists(cache_path):
            os.remove(cache_path)
            print(
                "Removed .cache file. Please re-run the script to re-authenticate with Spotify."
            )
        else:
            print(
                "No .cache file found to remove. Please check your credentials and re-authenticate."
            )
        sys.exit(1)
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
    import gspread

    try:
        # Open the Google Sheet (replace 'Your_Sheet_Name' with your actual sheet name)
        sheet = sheets_client.open("Music Saved Tracks").sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        print(
            "Error: Google Sheet 'Music Saved Tracks' not found or access denied.\n"
            "- Make sure the sheet exists in your Google Drive.\n"
            "- Make sure you have shared the sheet with your service account email (found in your credentials file).\n"
            "- You can also change the sheet name in the script if needed."
        )

    # Get the values of the 'Title' column starting from row 4
    title_column_values = sheet.col_values(2)[
        3:
    ]  # replace 1 with the index of your 'Title' column

    # Get the values of the 'Method Added' column starting from row 4
    method_added_column_values = sheet.col_values(12)[3:]

    # Filter the titles where corresponding method added is 'Auto Added'
    song_titles_only_added_automatically = [
        title
        for title, method in zip(title_column_values, method_added_column_values)
        if method == "Auto Added"
    ]

    # Get the index of the most recent song added in the last n number of songs retrieved
    index = None
    for i in range(len(songs) - 1, -1, -1):
        song_name = songs[i]["track"]["name"]
        if song_name in song_titles_only_added_automatically:
            index = i
            break

    # If index is still None, no intersecting song was found
    if index is None:
        print("No intersecting song was found.")
    else:
        print("Index of intersecting song:", index)

    # If there are remaining songs, append them to the Google Sheet
    if index is not None and index < len(songs) - 1:
        for song in songs[index + 1 :]:
            # Construct row data for appending to the Google Sheet
            row = [
                song["track"]["name"],  # Title
                song["track"]["artists"][0]["name"],  # Artist
                song["track"]["album"]["name"],  # Album
                None,  # Art
                parseSpotifySongUrl(song),  # Link (Typically a Spotify track url)
                None,  # Aquirement Status
                None,  # Quality
                None,  # Addiional Header. Ignore.
                None,  # Triaged
                None,  # Notes
                "Auto Added",  # Method Added
                None,  # Torrent Links
                getCurrentDatetime(),  # Date Added
            ]
            sheet.append_row(row)
    else:
        print(
            f"All {len(songs)} most recently liked songs are already in the spreadsheet."
        )


def main():
    # Ensure working directory is the same as main.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Parse command line arguments
    args = parse_args(sys.argv[1:])
    # app exits if this validation fails.
    validate_args(args)

    sp = authenticate_spotify(args)
    songs = get_spotify_songs(sp, args["top"])

    sheets_client = authenticate_google_sheets(
        credentials_file=args["credentials_file"]
    )
    append_songs_to_google_sheets(songs, sheets_client)


if __name__ == "__main__":
    main()
