import asyncio
import threading
from tui import SidebarApp  # 修正
from web import app
import uvicorn

def start_web():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    # Webサーバーを別スレッドで起動
    threading.Thread(target=start_web, daemon=True).start()
    # Textual TUIをasyncで起動
    await SidebarApp().run_async()  # 修正

if __name__ == "__main__":
    asyncio.run(main())
