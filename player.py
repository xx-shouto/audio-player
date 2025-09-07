import vlc
import os

MUSIC_DIR = "music"

class MusicPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.playlist = os.listdir(MUSIC_DIR)
        self.index = 0

    def load_track(self, track_path):
        media = self.instance.media_new(track_path)
        self.player.set_media(media)

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def next(self):
        if not self.playlist:
            return
        self.index = (self.index + 1) % len(self.playlist)
        self.load_track(os.path.join(MUSIC_DIR, self.playlist[self.index]))
        self.play()

    def prev(self):
        if not self.playlist:
            return
        self.index = (self.index - 1 + len(self.playlist)) % len(self.playlist)
        self.load_track(os.path.join(MUSIC_DIR, self.playlist[self.index]))
        self.play()
