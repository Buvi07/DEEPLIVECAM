# This file is intentionally left blank to mark the directory as a Python package.
import os
import tempfile
import shutil
import cv2
from glob import glob
import subprocess
from typing import List  # Add this import
import urllib.request  # Add this import
from tqdm import tqdm  # Add this import
from modules.utilities.ffmpeg_utils import run_ffmpeg  # Update import
import modules  # Ensure the modules package is imported
from modules.utilities.status import update_status  # Import update_status

def get_temp_directory_path():
    return os.path.join(tempfile.gettempdir(), "deep_live_cam_temp")

def create_temp():
    temp_dir = get_temp_directory_path()
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def clean_temp():
    temp_dir = get_temp_directory_path()
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def extract_frames(video_path, output_dir, fps=1):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    frame_count = 0
    saved_count = 0
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps // fps)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_count += 1

        frame_count += 1

    cap.release()
    return saved_count

def get_temp_frame_paths():
    temp_dir = get_temp_directory_path()
    return sorted(glob(os.path.join(temp_dir, "*.jpg")))

def is_image(file_path):
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    return os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in image_extensions

def is_video(file_path):
    video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
    return os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in video_extensions

def resolve_relative_path(path, base_dir=None):
    if os.path.isabs(path):
        return path
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir, path))

def get_temp_output_path(target_path):
    temp_directory_path = get_temp_directory_path()
    return os.path.join(temp_directory_path, "temp.mp4")

def move_temp(target_path: str, output_path: str) -> None:
    temp_output_path = get_temp_output_path(target_path)
    if not os.path.isfile(temp_output_path):
        raise FileNotFoundError(
            f"Temporary output file not found: {temp_output_path}. "
            f"Ensure that frames were extracted and the video was created successfully."
        )
    if os.path.isfile(output_path):
        os.remove(output_path)
    shutil.move(temp_output_path, output_path)

def normalize_output_path(source_path, target_path, output_path):
    if source_path and target_path:
        source_name, _ = os.path.splitext(os.path.basename(source_path))
        target_name, target_extension = os.path.splitext(os.path.basename(target_path))
        if os.path.isdir(output_path):
            return os.path.join(
                output_path, source_name + "-" + target_name + target_extension
            )
    return output_path

def create_temp(target_path):
    temp_directory_path = get_temp_directory_path(target_path)
    os.makedirs(temp_directory_path, exist_ok=True)
    return temp_directory_path

def clean_temp(target_path):
    temp_directory_path = get_temp_directory_path(target_path)
    if os.path.exists(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    parent_directory_path = os.path.dirname(temp_directory_path)
    if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
        os.rmdir(parent_directory_path)
    return True

import glob  # Ensure glob is imported correctly

def get_temp_frame_paths(target_path: str) -> List[str]:
    temp_directory_path = get_temp_directory_path(target_path)
    return glob.glob(os.path.join(glob.escape(temp_directory_path), "*.png"))  # Fixed incorrect usage of glob

def get_temp_directory_path(target_path):
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, "temp", target_name)
def get_temp_output_path(target_path):
    temp_directory_path = get_temp_directory_path(target_path)
    return os.path.join(temp_directory_path, "temp.mp4")

def normalize_output_path(source_path, target_path, output_path):
    if source_path and target_path:
        source_name, _ = os.path.splitext(os.path.basename(source_path))
        target_name, target_extension = os.path.splitext(os.path.basename(target_path))
        if os.path.isdir(output_path):
            return os.path.join(
                output_path, source_name + "-" + target_name + target_extension
            )
    return output_path

def has_image_extension(file_path: str) -> bool:
    """Check if a file has a valid image extension."""
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    return os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in image_extensions

def detect_fps(target_path: str) -> float:
    """Detect the FPS of a video file."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        target_path,
    ]
    output = subprocess.check_output(command).decode().strip().split("/")
    try:
        numerator, denominator = map(int, output)
        return numerator / denominator
    except Exception:
        pass
    return 30.0

def create_video(target_path: str, fps: float = 30.0) -> None:
    temp_output_path = get_temp_output_path(target_path)
    temp_directory_path = get_temp_directory_path(target_path)
    update_status(f"Creating video at {temp_output_path} with FPS: {fps}", "DLC.CORE")
    result = run_ffmpeg(
        [
            "-r",
            str(fps),
            "-i",
            os.path.join(temp_directory_path, "%04d.png"),
            "-c:v",
            modules.globals.video_encoder,
            "-crf",
            str(modules.globals.video_quality),
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "colorspace=bt709:iall=bt601-6-625:fast=1",
            "-y",
            temp_output_path,
        ]
    )
    if not result:
        raise RuntimeError(f"Failed to create video at {temp_output_path}")

def restore_audio(target_path: str, output_path: str) -> None:
    """Restore audio from the original video to the processed video."""
    temp_output_path = get_temp_output_path(target_path)
    done = run_ffmpeg(
        [
            "-i",
            temp_output_path,
            "-i",
            target_path,
            "-c:v",
            "copy",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-y",
            output_path,
        ]
    )
    if not done:
        move_temp(target_path, output_path)

def conditional_download(download_directory_path: str, urls: List[str]) -> None:
    """Download files from the given URLs if they do not already exist."""
    if not os.path.exists(download_directory_path):
        os.makedirs(download_directory_path)
    for url in urls:
        download_file_path = os.path.join(
            download_directory_path, os.path.basename(url)
        )
        if not os.path.exists(download_file_path):
            request = urllib.request.urlopen(url)  # type: ignore[attr-defined]
            total = int(request.headers.get("Content-Length", 0))
            with tqdm(
                total=total,
                desc="Downloading",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as progress:
                urllib.request.urlretrieve(url, download_file_path, reporthook=lambda count, block_size, total_size: progress.update(block_size))  # type: ignore[attr-defined]

def extract_frames(target_path: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    update_status(f"Extracting frames from {target_path} to {output_dir}", "DLC.CORE")
    result = run_ffmpeg(
        [
            "-i",
            target_path,
            "-pix_fmt",
            "rgb24",
            os.path.join(output_dir, "%04d.png"),
        ]
    )
    if not result:
        raise RuntimeError(f"Failed to extract frames from {target_path}")

# Ensure all utility functions are explicitly exposed
__all__ = [
    "get_temp_directory_path",
    "create_temp",
    "clean_temp",
    "extract_frames",
    "get_temp_frame_paths",
    "is_image",
    "is_video",
    "resolve_relative_path",
    "get_temp_output_path",
    "move_temp",
    "normalize_output_path",
    "has_image_extension",
    "detect_fps",
    "create_video",
    "restore_audio",
    "conditional_download",  # Add conditional_download to the list
]

