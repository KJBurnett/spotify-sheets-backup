# Spotify Playlist Tracker
This Python script allows you to retrieve your most recently liked songs from Spotify and append them to a Google Sheet. It uses the Spotify API and Google Sheets API for authentication and data manipulation.

# Prerequisites
Before running the script, make sure you have the following:

1. **Spotify Developer Account:**
Create a Spotify Developer account and register your app to obtain the necessary credentials (client ID, client secret, and redirect URI).
Set up your Spotify app with the appropriate permissions (e.g., user-library-read).
2. **Google Service Account Credentials:**
Create a service account in the Google Cloud Console.
Download the JSON credentials file (e.g., credentials.json) for your service account.
3. **Google Sheet:**
Create a Google Sheet where you want to store your Spotify tracks.
Note the name of the sheet (replace 'Spotify Saved Tracks' in the script with your actual sheet name).

# Usage
1. Clone this repository and navigate to the project directory.
2. Install the required Python packages:
   <br>`pip install spotipy gspread oauth2client`

4. Run the script with the necessary command line arguments:
  <br>`python spotify_playlist_tracker.py client_id=<YOUR_CLIENT_ID> client_secret=<YOUR_CLIENT_SECRET> redirect_uri=<YOUR_REDIRECT_URI>`

5. The script will retrieve your last 10 liked songs from Spotify and check if they are already in your Google Sheet. If not, it will append them to the sheet.
6. Check your Google Sheet to see the updated list of saved tracks.

# Notes
* If all 10 most recently liked songs are already in the spreadsheet, the script will inform you.
* Make sure the Google Sheet has a column named “Title” (adjust the column index in the script if needed).
