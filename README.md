# Spotify Playlist Tracker
This Python script allows you to retrieve your most recently liked songs from Spotify and append them to a Google Sheet. It uses the Spotify API and Google Sheets API for authentication and data manipulation.

# Prerequisites
Before running the script, make sure you have the following:

1. **Spotify Developer Account:**
<br>Create a Spotify Developer account and register your app to obtain the necessary credentials (client ID, client secret, and redirect URI).
<br>Set up your Spotify app with the appropriate permissions (e.g., user-library-read).
2. **Google Service Account Credentials:**
<br>Create a service account in the Google Cloud Console.
<br>Download the JSON credentials file (e.g., credentials.json) for your service account.
3. **Google Sheet:**
<br>Create a Google Sheet where you want to store your Spotify tracks.
<br>Note the name of the sheet (replace 'Spotify Saved Tracks' in the script with your actual sheet name).

# Usage
1. Clone this repository and navigate to the project directory.
2. Install the required Python packages:
   <br>`pip install -r requirements.txt`

4. Run the script with the necessary command line arguments:
  <br>`python main.py client_id=<YOUR_CLIENT_ID> client_secret=<YOUR_CLIENT_SECRET> redirect_uri=<YOUR_REDIRECT_URI> credentials_file=<YOUR_CREDENTIALS_JSON_FROM_GOOGLE> top=10`
  <br> Note: `top` is how many most recently liked songs you should grab. This has only been tested up to 50 songs. Increase at your own risk, lol.

6. The script will retrieve your last 10 liked songs from Spotify and check if they are already in your Google Sheet. If not, it will append them to the sheet.
7. Check your Google Sheet to see the updated list of saved tracks.

# Notes
* If all 10 most recently liked songs are already in the spreadsheet, the script will inform you.
* Make sure the Google Sheet has a column named “Title” (adjust the column index in the script if needed).

----------
# Initial Setup

## 1. Spotify Developer Account Setup *(Requires Spotify Premium!)*
1. **Create a Spotify Developer Account**:
    - Go to the Spotify Developer Dashboard.
    - Log in with your existing Spotify account or create a new one.
2. **Create a New App**:
    - Click on the "Create an App" button.
    - Fill in the required details for your app (name, description, etc.).
    - Once created, you'll see your **Client ID** and **Client Secret**. Keep these safe; you'll need them later.
3. **Configure Redirect URI**:
    - In your app settings, add a redirect URI (e.g., `http://localhost:8888/callback`). This is where Spotify will redirect after authentication.
    - Make sure the redirect URI matches the one you'll use in your Python script.

## 2. Google Service Account Credentials Setup *(100% works for multiple users on the FREE TIER!)*
1. **Create a Google Cloud Project**:
    - Go to the Google Cloud Console.
    - Create a new project (or use an existing one).
2. **Enable Google Sheets API**:
    - In your project, navigate to the **APIs & Services > Library** section.
    - Search for "Google Sheets API" and enable it.
3. **Create a Service Account**:
    - In the same project, go to **APIs & Services > Credentials**.
    - Click on "Create Credentials" and select "Service Account".
    - Fill in the required details (name, role, etc.).
    - Click "Create" to generate the service account.
4. **Generate JSON Key File (credentials.json)**:
    - After creating the service account, click on it.
    - Go to the "Keys" tab and click "Add Key" > "Create new key".
    - Choose JSON format.
    - Download the `credentials.json` file.
    - Keep this file secure; it contains your service account credentials. and will be ingested by the main.py script in this project.

