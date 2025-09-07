import asyncio
import os
import pygame
from textual.app import App
from textual.widgets import Static, ListView, ListItem
from textual.screen import Screen
from textual.containers import Horizontal

MUSIC_DIR = "music"

# ------------------------
# MusicPlayer
# ------------------------
class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_track = None
        self.on_end_callback = None
        self._paused = False

    def load_track(self, path: str):
        self.current_track = path
        pygame.mixer.music.load(path)
        self._paused = False

    def play(self):
        if self.current_track:
            if self._paused:
                pygame.mixer.music.unpause()
                self._paused = False
            else:
                pygame.mixer.music.play()
            asyncio.create_task(self._monitor_end())

    def pause(self):
        pygame.mixer.music.pause()
        self._paused = True

    def stop(self):
        pygame.mixer.music.stop()
        self._paused = False

    def is_playing(self):
        return pygame.mixer.music.get_busy()

    async def _monitor_end(self):
        while self.is_playing() or self._paused:
            await asyncio.sleep(0.5)
        if not self._paused and self.on_end_callback:
            await self.on_end_callback()


# ------------------------
# ListItem
# ------------------------
class StringListItem(ListItem):
    def __init__(self, text: str):
        super().__init__(Static(text))
        self.item_name = text


# ------------------------
# サイドバー
# ------------------------
def create_sidebar():
    sidebar = ListView(
        StringListItem("Home"),
        StringListItem("Settings"),
        StringListItem("Playlists"),
        StringListItem("Exit"),
    )
    sidebar.index = 0
    return sidebar


# ------------------------
# HomeScreen
# ------------------------
class HomeScreen(Screen):
    def compose(self):
        with Horizontal():
            self.sidebar = create_sidebar()
            yield self.sidebar

            self.list_view = ListView()
            yield self.list_view

            self.action_list = ListView(
                StringListItem("Play"),
                StringListItem("Pause"),
                StringListItem("Next"),
                StringListItem("Prev"),
            )
            self.action_list.visible = False
            yield self.action_list

    def on_mount(self):
        self.load_playlist()
        self.set_focus(self.list_view)
        self.app.player.on_end_callback = self.on_track_end

    def load_playlist(self):
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        files.sort()
        self.list_view.clear()
        for f in files:
            self.list_view.append(StringListItem(f))
        if self.list_view.children:
            self.list_view.index = 0

    async def on_track_end(self):
        if not self.list_view.children:
            return
        current_index = self.list_view.index
        next_index = (current_index + 1) % len(self.list_view.children)
        self.list_view.index = next_index
        next_song = self.list_view.children[next_index].item_name
        self.app.player.load_track(os.path.join(MUSIC_DIR, next_song))
        self.app.player.play()

    async def on_key(self, event):
        key = event.key

        # サイドバー選択
        if self.focused is self.sidebar and key == "enter":
            choice = self.sidebar.children[self.sidebar.index].item_name
            if choice == "Settings":
                await self.app.push_screen(SettingsScreen())
            elif choice == "Playlists":
                await self.app.push_screen(PlaylistListScreen())
            elif choice == "Exit":
                await self.app.push_screen(ExitConfirmScreen())
            elif choice == "Home":
                # 自分自身を再度 push
                await self.app.push_screen(HomeScreen())

        # 曲リスト → アクションリスト
        elif self.focused is self.list_view and key == "enter":
            self.action_list.visible = True
            self.set_focus(self.action_list)

        # アクションリスト操作
        elif self.focused is self.action_list and key == "enter":
            action = self.action_list.children[self.action_list.index].item_name
            current_index = self.list_view.index
            song_name = self.list_view.children[current_index].item_name
            song_path = os.path.join(MUSIC_DIR, song_name)

            if action == "Play":
                self.app.player.load_track(song_path)
                self.app.player.play()
            elif action == "Pause":
                self.app.player.pause()
            elif action == "Next":
                next_index = (current_index + 1) % len(self.list_view.children)
                self.list_view.index = next_index
                next_song = self.list_view.children[next_index].item_name
                self.app.player.load_track(os.path.join(MUSIC_DIR, next_song))
                self.app.player.play()
            elif action == "Prev":
                prev_index = (current_index - 1) % len(self.list_view.children)
                self.list_view.index = prev_index
                prev_song = self.list_view.children[prev_index].item_name
                self.app.player.load_track(os.path.join(MUSIC_DIR, prev_song))
                self.app.player.play()

        # 左右キーでフォーカス移動
        if key == "left":
            if self.focused is self.action_list:
                self.set_focus(self.list_view)
            elif self.focused is self.list_view:
                self.set_focus(self.sidebar)
        elif key == "right":
            if self.focused is self.sidebar:
                self.set_focus(self.list_view)

        elif key == "r":
            self.load_playlist()


# ------------------------
# SettingsScreen
# ------------------------
class SettingsScreen(Screen):
    def compose(self):
        with Horizontal():
            self.sidebar = create_sidebar()
            yield self.sidebar
            self.settings_list = ListView()
            yield self.settings_list

    def on_mount(self):
        self.settings_list.clear()
        self.settings_list.append(StringListItem("Bluetooth"))
        self.settings_list.append(StringListItem("Other Setting"))
        self.set_focus(self.sidebar)

    async def on_key(self, event):
        key = event.key
        if self.focused is self.sidebar and key == "enter":
            choice = self.sidebar.children[self.sidebar.index].item_name
            if choice == "Home":
                await self.app.push_screen(HomeScreen())
            elif choice == "Playlists":
                await self.app.push_screen(PlaylistListScreen())
            elif choice == "Exit":
                await self.app.push_screen(ExitConfirmScreen())
        elif key == "right" and self.focused is self.sidebar:
            self.set_focus(self.settings_list)
        elif key == "left" and self.focused is self.settings_list:
            self.set_focus(self.sidebar)


# ------------------------
# PlaylistListScreen
# ------------------------
class PlaylistListScreen(Screen):
    def compose(self):
        with Horizontal():
            self.sidebar = create_sidebar()
            yield self.sidebar
            self.playlist_list = ListView()
            yield self.playlist_list

    def on_mount(self):
        self.playlist_list.clear()
        self.playlist_list.append(StringListItem("Favorites"))
        self.playlist_list.append(StringListItem("Chill"))
        self.set_focus(self.sidebar)

    async def on_key(self, event):
        key = event.key
        if self.focused is self.sidebar and key == "enter":
            choice = self.sidebar.children[self.sidebar.index].item_name
            if choice == "Home":
                await self.app.push_screen(HomeScreen())
            elif choice == "Settings":
                await self.app.push_screen(SettingsScreen())
            elif choice == "Exit":
                await self.app.push_screen(ExitConfirmScreen())
        elif key == "right" and self.focused is self.sidebar:
            self.set_focus(self.playlist_list)
        elif key == "left" and self.focused is self.playlist_list:
            self.set_focus(self.sidebar)
        elif self.focused is self.playlist_list and key == "enter":
            await self.app.push_screen(HomeScreen())


# ------------------------
# ExitConfirmScreen
# ------------------------
class ExitConfirmScreen(Screen):
    def compose(self):
        self.list_view = ListView(
            StringListItem("Yes"),
            StringListItem("No")
        )
        yield self.list_view

    def on_mount(self):
        self.list_view.index = 1
        self.set_focus(self.list_view)

    async def on_key(self, event):
        if event.key == "enter":
            choice = self.list_view.children[self.list_view.index].item_name
            if choice == "Yes":
                await self.app.action_quit()
            else:
                await self.app.pop_screen()


# ------------------------
# Main App
# ------------------------
class SidebarApp(App):
    CSS_PATH = "sidebar.css"
    BINDINGS = [("q", "quit", "Quit")]

    def on_mount(self):
        self.player = MusicPlayer()
        self.push_screen(HomeScreen())  # 最初の HomeScreen

if __name__ == "__main__":
    app = SidebarApp()
    app.run()
