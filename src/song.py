from datetime import datetime


class Song:
    def __init__(self, song):
        self.song = song

    @property
    def title(self):
        return self.song.name

    @property
    def artist(self):
        return self.song.artist

    @property
    def album(self):
        return self.song.album

    @property
    def artwork(self):
        return None

    @property
    def link(self):
        return parseSpotifySongUrl(self.song)

    @property
    def aquirement_status(self):
        return None

    @property
    def quality(self):
        return None

    @property
    def additional_header(self):
        return None

    @property
    def triaged(self):
        return None

    @property
    def notes(self):
        return None

    @property
    def method_added(self):
        return "Auto Added"

    @property
    def torrent_links(self):
        return None

    @property
    def date_added(self):
        return self.getCurrentDateTime()


def getSong(song):
    return Song(song)


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
