import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


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


def parseSpotifySongUrl(song):
    spotifyUrlTemplate = "https://open.spotify.com/track/"
    urlValue = song["track"]["uri"].split(":")[2]
    return "".join([spotifyUrlTemplate, urlValue])


def getCurrentDatetime():
    now = datetime.now()
    date_added = now.strftime(
        "%B %d, %Y at %I:%M%p"
    )  # Format date as "January 29, 2024 at 01:05PM"
    return date_added


def main():
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
