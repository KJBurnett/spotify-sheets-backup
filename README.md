# Spotify Sheets Backup

This Python script is a multi-purpose tool to manage your music library between Spotify, Google Sheets, and a local Excel file. It allows you to:
-   Retrieve your most recently liked songs from Spotify and append them to a Google Sheet and a local Excel backup.
-   Scan a local directory of music files and cross-reference it with your Google Sheet, marking songs you've downloaded.
-   Keep a local Excel file perfectly in sync with your master Google Sheet.

# Prerequisites

Before running the script, make sure you have the following:

1.  **Spotify Developer Account:**
    *   Create a Spotify Developer account and register your app to obtain the necessary credentials (client ID, client secret, and redirect URI).
    *   Set up your Spotify app with the `user-library-read` scope.
2.  **Google Service Account Credentials:**
    *   Create a service account in the Google Cloud Console and enable the Google Sheets API.
    *   Download the JSON credentials file for your service account.
3.  **Google Sheet:**
    *   Create a Google Sheet named "Music Saved Tracks".
    *   Share this sheet with the `client_email` found in your Google service account credentials JSON file.
    *   The sheet must have a header row with at least the following columns: `Title`, `Artist`, `Acquirement`, `Triaged`.

# Installation

1.  Clone this repository and navigate to the project directory.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

# Configuration

For ease of use, you can create a `config.json` file in the root of the project to store your credentials and default options. The script will automatically load this file, but any command-line arguments you provide will override the values in the file.

**Example `config.json`:**
```json
{
    "args": [
        "client_id=YOUR_SPOTIFY_CLIENT_ID",
        "client_secret=YOUR_SPOTIFY_CLIENT_SECRET",
        "redirect_uri=http://localhost:9000",
        "credentials_file=path/to/your/google/credentials.json",
        "top=20"
    ]
}
```

# Usage

The script is now controlled by flags to perform different actions.

### Backing Up Recent Spotify Tracks

This command fetches the 20 most recently liked songs from Spotify and appends any new ones to your Google Sheet and the local `song-list.xlsx` file.

```bash
python main.py --backup-tracks --top 20
```

### Scanning Your Local Music Library

This feature scans a local folder of music to see which songs from your spreadsheet you already have downloaded.

**Dry Run (Scan Mode):**
This command will scan the specified path and show you which songs it found and would mark as "acquired" and "triaged", without actually changing any data.

```bash
python main.py --scan-local --scan-path "D:\Your\Music\Folder"
```

**Live Update (Update Mode):**
By adding `--mode update`, the script will perform the scan and then update both the Google Sheet and the local Excel file with the results.

```bash
python main.py --scan-local --scan-path "D:\Your\Music\Folder" --mode update
```

### Synchronizing the Local Excel File

If your local `song-list.xlsx` gets out of sync or you want to create it for the first time, you can use the `--reset-excel` flag. This will completely overwrite the local file with the current data from your Google Sheet.

```bash
python main.py --reset-excel
```

### Combining Operations

You can combine flags to perform multiple actions in one go. For example, to back up new tracks and then immediately scan your local library:

```bash
python main.py --backup-tracks --scan-local --scan-path "D:\Your\Music\Folder"
```

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

