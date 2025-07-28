# src/local_scanner.py

import os
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen import MutagenError
from thefuzz import fuzz
from excel import update_excel_row
from unidecode import unidecode
from tqdm import tqdm

# List of audio file extensions to scan
AUDIO_EXTENSIONS = ['.mp3', '.flac', '.m4a', '.ogg', '.wav']

def clean_filename(filename):
    """Cleans a filename to extract potential artist and title."""
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Transliterate to ASCII to handle non-standard characters
    name = unidecode(name)
    # Common separators
    separators = [' - ', ' – ', ' _ ']
    for sep in separators:
        if sep in name:
            parts = name.split(sep, 1)
            return parts[0].strip(), parts[1].strip() # Artist, Title
    # If no separator, assume the whole name is the title
    return None, name.strip()

def get_audio_metadata(filepath):
    """Extracts metadata (artist and title) from an audio file."""
    try:
        if filepath.endswith('.mp3'):
            audio = MP3(filepath, ID3=EasyID3)
            artist = audio.get('artist', [None])[0]
            title = audio.get('title', [None])[0]
            return artist, title
        # Add handlers for other file types (flac, m4a) if needed
    except (MutagenError, Exception) as e:
        # print(f"Could not read metadata for {filepath}: {e}")
        pass
    return None, None

def find_match_in_sheet(local_artist, local_title, sheet_songs):
    """Finds the best match for a local song in the sheet data using fuzzy matching."""
    best_match = None
    highest_score = 0

    if not local_title:
        return None, 0, -1

    for i, song in enumerate(sheet_songs):
        sheet_title = song.get('Title')
        sheet_artist = song.get('Artist')

        if not sheet_title or not sheet_artist:
            continue

        # Calculate similarity
        title_score = fuzz.ratio(local_title.lower(), sheet_title.lower())
        artist_score = fuzz.ratio(local_artist.lower(), sheet_artist.lower()) if local_artist else 50

        score = (title_score * 0.7) + (artist_score * 0.3)

        if score > highest_score:
            highest_score = score
            best_match = (i, song)
    
    if best_match:
        return best_match[1], highest_score, best_match[0]
    
    return None, 0, -1


def _scan_files(scan_path, songs_to_find, sheet_songs):
    matches_to_update = []
    normalized_scan_path = os.path.normpath(scan_path)

    # Build a set of unique artist names to look for
    target_artists = set(song.get('Artist', '').strip() for song in songs_to_find if song.get('Artist'))

    # Map normalized artist names to original for fuzzy matching
    normalized_artist_map = {unidecode(artist).lower(): artist for artist in target_artists}

    # Find candidate artist folders
    artist_folders = []
    for entry in os.scandir(normalized_scan_path):
        if entry.is_dir():
            folder_name = unidecode(entry.name).lower()
            for norm_artist, orig_artist in normalized_artist_map.items():
                if fuzz.ratio(folder_name, norm_artist) > 80:
                    artist_folders.append((entry.path, orig_artist))
                    break

    # Only scan files in matched artist folders
    print(f"Found {len(artist_folders)} likely artist folders to scan:")
    # Build a map of artist to their songs to find
    artist_to_songs = {}
    for song in songs_to_find:
        artist = song.get('Artist', '').strip()
        if artist:
            artist_to_songs.setdefault(artist, []).append(song)

    total_files = 0
    for folder_path, _ in artist_folders:
        for _, _, files in os.walk(folder_path):
            total_files += sum(1 for file in files if any(file.endswith(ext) for ext in AUDIO_EXTENSIONS))
    print(f"Found {total_files} audio files in likely artist folders. Starting scan...")

    with tqdm(total=len(artist_folders), desc="Artist folders", unit="artist", ncols=80) as artist_pbar:
        with tqdm(total=total_files, desc="Scanning local files", unit="file", ncols=100, leave=False) as file_pbar:
            for folder_path, artist in artist_folders:
                # Only consider songs for this artist
                songs_needed = artist_to_songs.get(artist, [])
                if not songs_needed:
                    artist_pbar.update(1)
                    continue
                found_titles = set()
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if not any(file.endswith(ext) for ext in AUDIO_EXTENSIONS):
                            continue

                        filepath = os.path.join(root, file)
                        file_artist, title = get_audio_metadata(filepath)

                        if not title:
                            file_artist, title = clean_filename(file)

                        # Use the artist from the folder if metadata is missing
                        if not file_artist:
                            file_artist = artist

                        if not title or title in found_titles:
                            file_pbar.update(1)
                            continue

                        # Only try to match against songs for this artist
                        matched_song, score, song_index = find_match_in_sheet(file_artist, title, songs_needed)

                        if score > 85:
                            file_pbar.write(f"Match found! (Score: {int(score)}%) - File: '{file}' matched to Sheet: '{matched_song.get('Title')}' by '{matched_song.get('Artist')}'")
                            original_index = sheet_songs.index(matched_song)
                            matches_to_update.append((original_index, matched_song))
                            found_titles.add(title)
                            # Remove from both songs_needed and songs_to_find
                            songs_needed.pop(song_index)
                            songs_to_find.remove(matched_song)
                            # If all songs for this artist found, break
                            if not songs_needed:
                                break
                        file_pbar.update(1)
                    if not songs_needed:
                        break
                artist_pbar.update(1)
    return matches_to_update

def _update_sheet(sheet, matches_to_update, acquirement_col_index, triaged_col_index, mode):
    if not matches_to_update:
        print("No new matches found in the local library.")
        return

    print(f"-- Scan Complete ---\nFound {len(matches_to_update)} new songs to update.")

    if mode == 'scan':
        print("[Scan Mode] The following changes would be made in 'update' mode:")
        for _, song in matches_to_update:
            print(f"  - Mark '{song['Title']}' by '{song['Artist']}' as acquired and triaged.")
    
    elif mode == 'update':
        print("[Update Mode] Applying changes to Google Sheet and Excel file...")
        for original_index, song in matches_to_update:
            try:
                row_to_update_index = original_index + 5 # Data starts on row 5
                sheet.update_cell(row_to_update_index, acquirement_col_index + 1, 'acquired')
                sheet.update_cell(row_to_update_index, triaged_col_index + 1, 'triaged')
                update_excel_row(song['Title'], song['Artist'], {'Acquirement Status': 'acquired', 'Triaged': 'triaged'})
                print(f"  - Updated '{song['Title']}'")
            except Exception as e:
                print(f"  - Failed to update '{song['Title']}'. Reason: {e}")
    
    print("Update process complete.")

def scan_music_library(sheet, scan_path, mode):
    """
    Scans a local music library, compares it with the Google Sheet,
    and updates the sheet and Excel file based on the findings.
    """
    if not os.path.exists(scan_path):
        print(f"Error: Scan path does not exist: {scan_path}")
        return

    print("Reading data from Google Sheet...")
    try:
        # Fetch all data, including headers on row 4
        all_values = sheet.get_all_values()
        headers = all_values[3] # Headers are on the 4th row (index 3)
        sheet_songs_data = all_values[4:] # Data starts on the 5th row (index 4)

        # Get column indices
        title_col_index = headers.index('Title')
        artist_col_index = headers.index('Artist')
        acquirement_col_index = headers.index('Acquirement Status')
        triaged_col_index = headers.index('Triaged')

    except (ValueError, IndexError) as e:
        print(f"Error: Could not find required columns or data in Google Sheet. Details: {e}")
        return

    # Create a list of dictionaries manually for easier processing
    sheet_songs = [dict(zip(headers, row)) for row in sheet_songs_data]

    # Filter out songs that are already acquired and triaged
    songs_to_find = [
        song for song in sheet_songs
        if 'acquired' not in str(song.get('Acquirement Status', '')).lower() and \
           'triaged' not in str(song.get('Triaged', '')).lower()
    ]
    print(f"Found {len(songs_to_find)} songs to search for locally.")

    matches_to_update = _scan_files(scan_path, songs_to_find, sheet_songs)
    _update_sheet(sheet, matches_to_update, acquirement_col_index, triaged_col_index, mode)
