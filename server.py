import os
import sys
import json
import asyncio
import time
import subprocess
import webbrowser
from typing import Dict, Any, Optional

import yt_dlp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

import ffmpeg_helper
import license_manager

# Ensure FFmpeg is present & added to PATH
ffmpeg_dir = ffmpeg_helper.setup_ffmpeg_env()

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(PROJECT_DIR, "downloads")
STATIC_DIR = os.path.join(BUNDLE_DIR, "static")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = FastAPI(title="MediaDownloader PRO")

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class InfoRequest(BaseModel):
    url: str

class LicenseRequest(BaseModel):
    key: str

def format_bytes(size: float) -> str:
    if not size:
        return "Bilinmiyor"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def format_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return "00:00"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

@app.get("/")
def read_root():
    with open(os.path.join(PROJECT_DIR, "static", "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/license/status")
def get_license_status():
    return license_manager.get_credit_info()

@app.post("/api/license/activate")
def activate_license(req: LicenseRequest):
    success, message = license_manager.activate(req.key)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "ok", "message": message}

@app.post("/api/info")
def get_video_info(req: InfoRequest):
    # License & credit check
    credit_info = license_manager.get_credit_info()
    activated = credit_info["activated"]
    remaining = credit_info["free_credits_remaining"]
    
    if not activated and remaining <= 0:
        raise HTTPException(status_code=403, detail="10 Ücretsiz indirme hakkınız bitti! Lütfen sınırsız kullanım için lisans anahtarınızı girin veya satın alın.")

    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Geçerli bir URL giriniz.")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb', 'tv_embedded'],
                'player_skip': ['configs', 'webpage']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Video bilgileri alınamadı: {str(e)}")

    if not info:
        raise HTTPException(status_code=404, detail="Video bulunamadı.")

    # Process formats
    raw_formats = info.get('formats', [])
    
    # Categorize resolutions available
    available_heights = set()
    formats_list = []
    
    for f in raw_formats:
        height = f.get('height')
        if height and f.get('vcodec') != 'none':
            available_heights.add(height)
            
        ext = f.get('ext', '')
        filesize = f.get('filesize') or f.get('filesize_approx')
        
        # Build clean format representation
        formats_list.append({
            'format_id': f.get('format_id'),
            'ext': ext,
            'resolution': f.get('resolution') or (f"{f.get('width')}x{f.get('height')}" if f.get('height') else 'N/A'),
            'height': height,
            'fps': f.get('fps'),
            'filesize': filesize,
            'filesize_str': format_bytes(filesize) if filesize else "Bilinmiyor",
            'vcodec': f.get('vcodec'),
            'acodec': f.get('acodec'),
            'tbr': f.get('tbr'),
            'format_note': f.get('format_note', '')
        })

    sorted_heights = sorted(list(available_heights), reverse=True)
    
    # Preset Options for easy user selection
    presets = [
        {
            "id": "best",
            "title": "En Yüksek Kalite",
            "desc": "Mevcut en iyi video ve ses kalitesi (Otomatik)",
            "icon": "sparkles",
            "tag": "Önerilen",
            "type": "video"
        }
    ]

    for h in sorted_heights:
        label = "4K Ultra HD" if h >= 2160 else ("2K QHD" if h >= 1440 else ("Full HD" if h >= 1080 else ("HD" if h >= 720 else f"{h}p")))
        presets.append({
            "id": f"res_{h}",
            "title": f"{h}p - {label}",
            "desc": f"Maksimum {h}p çözünürlük + En iyi ses",
            "icon": "video",
            "tag": "MP4",
            "type": "video",
            "height": h
        })

    # Audio presets
    presets.append({
        "id": "audio_mp3",
        "title": "Sadece Ses (MP3)",
        "desc": "Yüksek kaliteli MP3 ses dosyası (320 kbps)",
        "icon": "music",
        "tag": "MP3",
        "type": "audio"
    })
    presets.append({
        "id": "audio_m4a",
        "title": "Sadece Ses (M4A)",
        "desc": "Orijinal M4A/AAC ses akışı",
        "icon": "music",
        "tag": "M4A",
        "type": "audio"
    })

    view_count = info.get('view_count')
    view_count_str = f"{view_count:,}".replace(',', '.') + " izlenme" if view_count else None

    return {
        "title": info.get('title'),
        "thumbnail": info.get('thumbnail'),
        "duration": info.get('duration'),
        "duration_str": format_duration(info.get('duration')),
        "uploader": info.get('uploader') or info.get('channel'),
        "view_count_str": view_count_str,
        "url": url,
        "presets": presets,
        "raw_formats": formats_list
    }

@app.websocket("/ws/download")
async def websocket_download(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()

    # License & credit check
    credit_info = license_manager.get_credit_info()
    activated = credit_info["activated"]
    remaining = credit_info["free_credits_remaining"]

    if not activated and remaining <= 0:
        await websocket.send_json({
            "status": "error",
            "message": "Ücretsiz indirme hakkınız bitti! Devam etmek için lisans anahtarınızı girin veya satın alın.",
            "code": "OUT_OF_CREDITS"
        })
        await websocket.close()
        return

    try:
        data_str = await websocket.receive_text()
        data = json.loads(data_str)
        
        url = data.get("url")
        preset_id = data.get("preset_id", "best")
        custom_format_id = data.get("custom_format_id")
        
        if not url:
            await websocket.send_json({"status": "error", "message": "URL bulunamadı."})
            await websocket.close()
            return

        # Prepare yt-dlp download parameters
        format_spec = 'bestvideo+bestaudio/best'
        postprocessors = []

        if custom_format_id:
            format_spec = custom_format_id
        elif preset_id == "best":
            format_spec = 'bestvideo+bestaudio/best'
        elif preset_id.startswith("res_"):
            height = preset_id.replace("res_", "")
            format_spec = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
        elif preset_id == "audio_mp3":
            format_spec = 'bestaudio/best'
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            })
        elif preset_id == "audio_m4a":
            format_spec = 'bestaudio[ext=m4a]/bestaudio'

        out_template = os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s")

        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                percent = (downloaded / total * 100) if total else 0
                
                msg = {
                    "status": "downloading",
                    "percent": round(percent, 1),
                    "downloaded_str": format_bytes(downloaded),
                    "total_str": format_bytes(total),
                    "speed_str": d.get('_speed_str', '---').strip(),
                    "eta_str": d.get('_eta_str', '---').strip(),
                    "filename": os.path.basename(d.get('filename', ''))
                }
                asyncio.run_coroutine_threadsafe(websocket.send_json(msg), loop)

            elif d['status'] == 'finished':
                msg = {
                    "status": "processing",
                    "message": "İndirme tamamlandı! FFmpeg ile dönüştürülüyor / birleştiriliyor...",
                    "filename": os.path.basename(d.get('filename', ''))
                }
                asyncio.run_coroutine_threadsafe(websocket.send_json(msg), loop)

        ydl_opts = {
            'format': format_spec,
            'outtmpl': out_template,
            'progress_hooks': [progress_hook],
            'ffmpeg_location': ffmpeg_dir,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'mweb', 'tv_embedded'],
                    'player_skip': ['configs', 'webpage']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            'quiet': True,
            'no_warnings': True,
        }

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        def run_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info_dict)
                if preset_id == "audio_mp3":
                    filename = os.path.splitext(filename)[0] + ".mp3"
                return filename

        # Consume 1 credit if running in free trial mode
        if not activated:
            allowed, remaining_credits = license_manager.consume_credit()
            if not allowed:
                await websocket.send_json({
                    "status": "error",
                    "message": "Ücretsiz indirme hakkınız bitti! Lütfen lisans anahtarınızı girin veya satın alın.",
                    "code": "OUT_OF_CREDITS"
                })
                await websocket.close()
                return

        await websocket.send_json({"status": "starting", "message": "İndirme başlatılıyor...", "credits": license_manager.get_credit_info()})
        
        final_filepath = await loop.run_in_executor(None, run_download)
        final_filename = os.path.basename(final_filepath)
        
        await websocket.send_json({
            "status": "completed",
            "message": "İndirme başarıyla tamamlandı!",
            "filename": final_filename,
            "filepath": final_filepath,
            "credits": license_manager.get_credit_info()
        })

    except WebSocketDisconnect:
        print("WebSocket istemcisi ayrıldı.")
    except Exception as e:
        await websocket.send_json({"status": "error", "message": f"İndirme hatası: {str(e)}"})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

@app.post("/api/open-downloads-folder")
def open_downloads_folder():
    try:
        if os.name == 'nt':
            os.startfile(DOWNLOADS_DIR)
        else:
            subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', DOWNLOADS_DIR])
        return {"status": "ok", "message": "Klasör açıldı."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads-list")
def get_downloads_list():
    try:
        files = []
        for name in os.listdir(DOWNLOADS_DIR):
            file_path = os.path.join(DOWNLOADS_DIR, name)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "name": name,
                    "size_str": format_bytes(stat.st_size),
                    "created_at": time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                })
        files.sort(key=lambda x: x['created_at'], reverse=True)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin Panel & Key Generator Routes
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

class AdminAuthRequest(BaseModel):
    password: str

class AdminGenerateRequest(BaseModel):
    password: str
    count: int = 1
    prefix: str = "PRO"
    note: str = ""

@app.get("/admin")
def serve_admin_panel():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))

@app.post("/api/admin/login")
def admin_login(req: AdminAuthRequest):
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Hatalı Yönetici Şifresi!")
    return {"status": "ok", "message": "Giriş başarılı."}

@app.post("/api/admin/generate")
def admin_generate_keys(req: AdminGenerateRequest):
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Yetkisiz erişim! Hatalı şifre.")
    keys = license_manager.generate_bulk_keys(req.count, req.prefix, req.note)
    return {"status": "ok", "count": len(keys), "keys": keys}

@app.post("/api/admin/keys")
def admin_get_keys(req: AdminAuthRequest):
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Yetkisiz erişim! Hatalı şifre.")
    keys = license_manager.get_all_generated_keys()
    return {"status": "ok", "keys": keys}

if __name__ == "__main__":
    import uvicorn
    def launch_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")
        
    import threading
    threading.Thread(target=launch_browser, daemon=True).start()
    
    print("\n=======================================================")
    print("🚀 MediaDownloader PRO Başlatılıyor...")
    print("📍 Adres: http://localhost:8000")
    print("=======================================================\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
