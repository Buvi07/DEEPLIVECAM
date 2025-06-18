import subprocess
import modules.globals

def run_ffmpeg(args: list[str]) -> bool:
    commands = [
        "ffmpeg",
        "-hide_banner",
        "-hwaccel",
        "auto",
        "-loglevel",
        modules.globals.log_level,
    ]
    commands.extend(args)
    try:
        subprocess.check_output(commands, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as e:
        update_status(f"FFmpeg error: {e.output.decode()}", "DLC.FFMPEG")
        return False