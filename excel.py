from openpyxl import load_workbook

# TODO: this is currently just a working template.
# This still needs to be implemented to follow the main.py flow in parallel.

songListFile = "song-list.xlsx"
wb = load_workbook(filename=songListFile)
ws = wb.active  # ws == worksheet
ws.append(["new song", "new artist", "new genre"])
wb.save(songListFile)

print(f"Updated local excel spreadsheet: {songListFile}")
