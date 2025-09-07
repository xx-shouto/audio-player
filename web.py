import os
from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import threading
import yt_dlp

app = FastAPI()
templates = Jinja2Templates(directory="templates")
MUSIC_DIR = "music"
PLAYLIST_DIR = "playlists"
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(PLAYLIST_DIR, exist_ok=True)

download_status = {"title": "", "progress": 0}

@app.get("/")
async def index(request: Request):
    playlists = [f for f in os.listdir(PLAYLIST_DIR) if f.endswith(".txt")]
    return templates.TemplateResponse("index.html", {"request": request, "status": download_status, "playlists": playlists})

@app.post("/upload")
async def upload(file: UploadFile):
    path = os.path.join(MUSIC_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return RedirectResponse("/", status_code=302)

@app.post("/youtube")
async def youtube(url: str = Form(...)):
    def progress_hook(d):
        if d["status"] == "downloading":
            info = d.get("info_dict", {})
            download_status["title"] = info.get("title", "Downloading...")
        elif d["status"] == "finished":
            download_status["title"] = f'{info.get("title", "Done")} Completed'

    def download():
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{MUSIC_DIR}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "postprocessors": [{"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": "192"}],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    threading.Thread(target=download, daemon=True).start()
    return RedirectResponse("/", status_code=302)

@app.post("/playlist_create")
async def playlist_create(name: str = Form(...)):
    path = os.path.join(PLAYLIST_DIR, f"{name}.txt")
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").close()
    return RedirectResponse("/", status_code=302)

@app.post("/playlist_add_song")
async def playlist_add_song(playlist: str = Form(...), filename: str = Form(...)):
    path = os.path.join(PLAYLIST_DIR, playlist)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{filename}\n")
    return RedirectResponse("/", status_code=302)

def run_web():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
