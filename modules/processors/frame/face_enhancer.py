from typing import Any, List, Callable
import cv2
import threading
import gfpgan
import os
import importlib
import torch

import modules.globals
import modules.processors.frame.core
from modules.core import update_status
from modules.face_analyser import get_one_face
from modules.typing import Frame, Face
import platform
import torch
from modules.utilities import (
    conditional_download,
    is_image,
    is_video,
)

FACE_ENHANCER = None
THREAD_SEMAPHORE = threading.Semaphore()
THREAD_LOCK = threading.Lock()
NAME = "DLC.FACE-ENHANCER"

abs_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(abs_dir))), "models"
)


def pre_check() -> bool:
    download_directory_path = models_dir
    conditional_download(
        download_directory_path,
        [
            "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"
        ],
    )
    return True


def pre_start() -> bool:
    if not is_image(modules.globals.target_path) and not is_video(
        modules.globals.target_path
    ):
        update_status("Select an image or video for target path.", NAME)
        return False
    return True


def get_face_enhancer() -> Any:
    global FACE_ENHANCER

    with THREAD_LOCK:
        if FACE_ENHANCER is None:
            model_path = os.path.join(models_dir, "GFPGANv1.4.pth")
            
            try:
                match platform.system():
                    case "Darwin":  # Mac OS
                        if torch.backends.mps.is_available():
                            mps_device = torch.device("mps")
                            FACE_ENHANCER = gfpgan.GFPGANer(
                                model_path=model_path, upscale=1, device=mps_device
                            )  # type: ignore[attr-defined]
                        else:
                            FACE_ENHANCER = gfpgan.GFPGANer(
                                model_path=model_path, upscale=1
                            )  # type: ignore[attr-defined]
                    case _:  # Other OS
                        FACE_ENHANCER = gfpgan.GFPGANer(
                            model_path=model_path, upscale=1
                        )  # type: ignore[attr-defined]
            except Exception as e:
                update_status(f"Error initializing GFPGAN model: {e}", NAME)
                raise e

    return FACE_ENHANCER


def enhance_face(temp_frame: Frame) -> Frame:
    with THREAD_SEMAPHORE:
        try:
            _, _, temp_frame = get_face_enhancer().enhance(temp_frame, paste_back=True)
        except Exception as e:
            update_status(f"Error enhancing face: {e}", NAME)
            raise e
    return temp_frame


def process_frame(source_face: Face, temp_frame: Frame) -> Frame:
    target_face = get_one_face(temp_frame)
    if target_face:
        temp_frame = enhance_face(temp_frame)
    return temp_frame


def process_frames(
    source_path: str, temp_frame_paths: List[str], progress: Any = None
) -> None:
    update_status(f"Starting frame processing for {len(temp_frame_paths)} frames.", NAME)
    for temp_frame_path in temp_frame_paths:
        update_status(f"Processing frame: {temp_frame_path}", NAME)
        temp_frame = cv2.imread(temp_frame_path)
        if temp_frame is None:
            update_status(f"Warning: Could not read frame {temp_frame_path}", NAME)
            if progress: progress.update(1)
            continue

        try:
            result = process_frame(None, temp_frame)
            cv2.imwrite(temp_frame_path, result)
            update_status(f"Successfully processed frame: {temp_frame_path}", NAME)
        except Exception as exception:
            update_status(f"Error processing frame {os.path.basename(temp_frame_path)}: {exception}", NAME)
        finally:
            if progress:
                progress.update(1)


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    target_frame = cv2.imread(target_path)
    result = process_frame(None, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, temp_frame_paths: List[str], progress: Any = None) -> None:
    update_status(f"Processing video with {len(temp_frame_paths)} frames.", NAME)
    try:
        process_frames(source_path, temp_frame_paths, progress)
    except Exception as e:
        update_status(f"Error during video processing: {e}", NAME)


def process_frame_v2(temp_frame: Frame) -> Frame:
    target_face = get_one_face(temp_frame)
    if target_face:
        temp_frame = enhance_face(temp_frame)
    return temp_frame
