import os
import sys
import shutil

def get_ffmpeg_dir() -> str:
    """
    Returns the absolute path to the directory containing ffmpeg.exe and ffprobe.exe.
    Works seamlessly in PyInstaller frozen exe, local development, or PATH.
    """
    # 1. Check PyInstaller _MEIPASS bundle
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        bundled_ffmpeg_dir = os.path.join(bundle_dir, "ffmpeg_bin")
        local_ffmpeg = os.path.join(bundled_ffmpeg_dir, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
        if os.path.isfile(local_ffmpeg):
            return bundled_ffmpeg_dir

    # 2. Check local workspace directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg_dir = os.path.join(current_dir, "ffmpeg_bin")
    local_ffmpeg = os.path.join(local_ffmpeg_dir, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
    if os.path.isfile(local_ffmpeg):
        return local_ffmpeg_dir

    # 3. Check alongside the executable itself
    exe_dir = os.path.dirname(sys.executable)
    exe_ffmpeg_dir = os.path.join(exe_dir, "ffmpeg_bin")
    if os.path.isfile(os.path.join(exe_ffmpeg_dir, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")):
        return exe_ffmpeg_dir

    # 4. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return os.path.dirname(sys_ffmpeg)

    return local_ffmpeg_dir

def setup_ffmpeg_env():
    """Adds the verified ffmpeg path to os.environ['PATH'] so all subprocesses inherit it."""
    f_dir = get_ffmpeg_dir()
    if f_dir and os.path.isdir(f_dir):
        current_path = os.environ.get("PATH", "")
        if f_dir not in current_path:
            os.environ["PATH"] = f_dir + os.pathsep + current_path
    return f_dir

if __name__ == "__main__":
    f_path = setup_ffmpeg_env()
    print(f"FFmpeg Directory: {f_path}")
