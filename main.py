# File: main.py

"""
This script serves as a multi-tool for managing a music library backup.
Its capabilities, controlled by command-line flags, include:
- Backing up recently liked Spotify songs to a Google Sheet and a local Excel file.
- Scanning a local music directory to cross-reference with the Google Sheet and mark songs as "acquired" and "triaged".
- Performing a full reset of the local Excel file to match the Google Sheet exactly.
"""

import os
import sys
import argparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from src.song import parseSpotifySongUrl, getCurrentDatetime
from excel import append_row_to_excel, reset_excel_from_google_sheet, update_excel_row
from src.local_scanner import scan_music_library

# Define a function to parse command line arguments
def parse_cli_args():
    """Parse command line arguments using argparse."""
    parser = argparse.ArgumentParser(description="Spotify to Google Sheets backup script.")
    
    # Spotify Credentials
    parser.add_argument("--client_id", help="Spotify client ID.")
    parser.add_argument("--client_secret", help="Spotify client secret.")
    parser.add_argument("--redirect_uri", help="Spotify redirect URI.")
    
    # Google Credentials
    parser.add_argument("--credentials_file", help="Path to Google Sheets credentials file.")

    # Operational Flags
    parser.add_argument("--backup-tracks", action="store_true", help="Run the Spotify backup process.")
    parser.add_argument("--scan-local", action="store_true", help="Scan local music files.")
    parser.add_argument("--reset-excel", action="store_true", help="Reset the local Excel file from the Google Sheet.")

    # Options
    parser.add_argument("--top", type=int, default=10, help="Number of recent songs to fetch from Spotify.")
    parser.add_argument("--scan-path", help="Path to local music library for scanning.")
    parser.add_argument("--mode", choices=['scan', 'update'], default='scan', help="Mode for scanning local files ('scan' for dry-run, 'update' to apply changes).")

    args = parser.parse_args()

    # Load from config.json if essential args are missing
    config_args = {}
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            config = json.load(file)
            # config is a dictionary with a single key "args" which is a list of strings
            for arg in config.get("args", []):
                key, value = arg.split("=", 1)
                config_args[key] = value

    # Override config with command line args
    for key, value in vars(args).items():
        if value is not None:
            config_args[key] = value
    
    # Convert back to a namespace for consistency
    final_args = argparse.Namespace(**config_args)

    return final_args

# Check if all required arguments are provided
def validate_args(args):
    required_args = ["client_id", "client_secret", "redirect_uri", "credentials_file"]
    for arg in required_args:
        if not hasattr(args, arg) or getattr(args, arg) is None:
            print(f"Error: {arg} is not provided in CLI arguments or config.json.")
            sys.exit(1)


def authenticate_spotify(args):
    # Assign command line arguments to variables
    scope = "user-library-read"
    
    # Setup Spotify object...
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=args.client_id,
            client_secret=args.client_secret,
            redirect_uri=args.redirect_uri,
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


def append_songs_to_google_sheets(songs, sheet):
    try:
        all_values = sheet.get_all_values()
        headers = all_values[3]  # Headers on row 4
        sheet_records = all_values[4:]  # Data starts on row 5

        # Create a set of existing songs for efficient lookup
        existing_songs = set()
        title_col = headers.index("Title")
        artist_col = headers.index("Artist")
        for row in sheet_records:
            if len(row) > title_col and len(row) > artist_col:
                existing_songs.add((row[title_col], row[artist_col]))

    except (ValueError, IndexError) as e:
        print(f"Error reading sheet structure: {e}")
        return

    songs_to_add = []
    for song in songs:
        song_title = song["track"]["name"]
        song_artist = song["track"]["artists"][0]["name"]
        if (song_title, song_artist) not in existing_songs:
            songs_to_add.append(song)

    if songs_to_add:
        print(f"Found {len(songs_to_add)} new songs to add.")
        for song in songs_to_add:
            # Dynamically build the row based on headers
            row_data_map = {
                "Date Added": getCurrentDatetime(),
                "Title": song["track"]["name"],
                "Artist": song["track"]["artists"][0]["name"],
                "Album": song["track"]["album"]["name"],
                "Spotify Link": parseSpotifySongUrl(song),
                "Method Added": "Auto Added",
            }
            
            # Ensure all headers are present in the final row data
            final_row_data = [row_data_map.get(header, "") for header in headers]
            
            sheet.append_row(final_row_data)
            append_row_to_excel(final_row_data)
    else:
        print(
            f"All {len(songs)} most recently liked songs are already in the spreadsheet."
        )

def run_spotify_backup(args, sheet):
    """Handles the logic for backing up Spotify tracks."""
    print("Running Spotify backup...")
    validate_args(args)
    sp = authenticate_spotify(args)
    songs = get_spotify_songs(sp, int(args.top))
    append_songs_to_google_sheets(songs, sheet)
    print("Spotify backup complete.")

from src.local_scanner import scan_music_library
def run_local_scanner(args, sheet):
    """Handles the logic for scanning local music files."""
    if not args.scan_path:
        print("Error: --scan-path is required for --scan-local.")
        sys.exit(1)
    scan_music_library(sheet, args.scan_path.strip('"'), args.mode)


def run_excel_reset(args, sheet):
    """Handles the logic for resetting the Excel file."""
    print("Resetting local Excel file from Google Sheet...")
    reset_excel_from_google_sheet(sheet)


def main():
    # Ensure working directory is the same as main.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    args = parse_cli_args()

    # Authenticate Google Sheets once if any action requires it
    sheet = None
    if args.backup_tracks or args.scan_local or args.reset_excel:
        validate_args(args) # a subset of args are needed for sheets
        sheets_client = authenticate_google_sheets(
            credentials_file=args.credentials_file
        )
        try:
            sheet = sheets_client.open("Music Saved Tracks").sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            print(
                "Error: Google Sheet 'Music Saved Tracks' not found or access denied.\n"
                "- Make sure the sheet exists in your Google Drive.\n"
                "- Make sure you have shared the sheet with your service account email (found in your credentials file)."
            )
            sys.exit(1)


    if args.backup_tracks:
        run_spotify_backup(args, sheet)
    
    if args.scan_local:
        run_local_scanner(args, sheet)

    if args.reset_excel:
        run_excel_reset(args, sheet)

    if not any([args.backup_tracks, args.scan_local, args.reset_excel]):
        print("No action specified. Use --backup-tracks, --scan-local, or --reset-excel.")
        print("Use -h or --help for more information.")


if __name__ == "__main__":
    main()
