from textual.app import App
from textual.widgets import Static, ListView, ListItem
from textual.screen import Screen
from textual.containers import Horizontal
import asyncio
import os
from player import MusicPlayer
from web import download_status  # WebUIと共有するグローバル変数

MUSIC_DIR = "music"

# ------------------------
# ListItem に文字列を保持するクラス
# ------------------------
class StringListItem(ListItem):
    def __init__(self, text: str):
        super().__init__(Static(text))
        self.item_name = text

# ------------------------
# サイドバー生成関数（各スクリーン用に独立）
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
# Screens
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
        self.set_interval(0.5, self.update_download_status)
        # プレイヤーの終了コールバックをセット
        self.app.player.on_end_callback = self.on_track_end

    async def on_track_end(self):
        # 曲終了時に次の曲を再生
        current_index = self.list_view.index
        next_index = (current_index + 1) % len(self.list_view.children)
        self.list_view.index = next_index
        next_song = self.list_view.children[next_index].item_name
        self.app.player.load_track(os.path.join(MUSIC_DIR, next_song))
        self.app.player.play()

        
    def load_playlist(self):
        files = os.listdir(MUSIC_DIR)
        files.sort()
        self.list_view.clear()
        for f in files:
            self.list_view.append(StringListItem(f))
        if self.list_view.children:
            self.list_view.index = 0

    async def update_download_status(self):
        status = download_status.get("status", "idle")
        title = download_status.get("title", "")

        if status == "downloading":
            if not any(title in item.item_name for item in self.list_view.children):
                self.list_view.append(StringListItem(f"{title} Downloading…"))
            else:
                for item in self.list_view.children:
                    if title in item.item_name:
                        item.query_one(Static).update(f"{title} Downloading…")
                        item.item_name = f"{title} Downloading…"
        elif status == "complete":
            for item in self.list_view.children:
                if title in item.item_name:
                    item.query_one(Static).update(f"{title} Download Complete!")
                    item.item_name = f"{title} Download Complete!"
            await asyncio.sleep(3)
            for item in self.list_view.children:
                if title in item.item_name:
                    item.query_one(Static).update(title)
                    item.item_name = title
            download_status["status"] = "idle"

    async def on_key(self, event):
        key = event.key

        # 曲選択 → アクションリスト
        if self.focused is self.list_view and key == "enter":
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

        # 左矢印でフォーカス遷移
        if key == "left":
            if self.focused is self.action_list:
                self.set_focus(self.list_view)
            elif self.focused is self.list_view:
                self.set_focus(self.sidebar)

        # 右矢印で曲リストに戻す
        elif key == "right" and self.list_view.children:
            self.set_focus(self.list_view)

        # rキーで曲リスト再読み込み
        elif key == "r":
            self.load_playlist()

# ------------------------
# PlaylistSongsScreen（プレイリスト曲表示）
# ------------------------
class PlaylistSongsScreen(Screen):
    def __init__(self, playlist_name: str):
        super().__init__()
        self.playlist_name = playlist_name

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
        self.list_view.clear()
        self.list_view.append(StringListItem(f"Song1 ({self.playlist_name})"))
        self.list_view.append(StringListItem(f"Song2 ({self.playlist_name})"))
        self.list_view.index = 0
        self.set_focus(self.list_view)

    async def on_key(self, event):
        key = event.key

        if self.focused is self.list_view and key == "enter":
            self.action_list.visible = True
            self.set_focus(self.action_list)

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

        # 左矢印でフォーカス遷移
        if key == "left":
            if self.focused is self.action_list:
                self.set_focus(self.list_view)
            elif self.focused is self.list_view:
                self.set_focus(self.sidebar)

        elif key == "right" and self.list_view.children:
            self.set_focus(self.list_view)

# ------------------------
# 他のスクリーン
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

    async def on_key(self, event):
        if event.key == "enter" and self.focused is self.playlist_list:
            playlist_name = self.playlist_list.children[self.playlist_list.index].item_name
            await self.app.push_screen(PlaylistSongsScreen(playlist_name))

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
        # プレイヤー初期化
        self.player = MusicPlayer()
        # 最初に HomeScreen を表示
        self.push_screen(HomeScreen())

if __name__ == "__main__":
    app = SidebarApp()
    app.run()
