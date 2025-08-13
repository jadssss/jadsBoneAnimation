# /render.py
# Rendering management / Управление рендерингом

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw
import imageio
import logging

logger = logging.getLogger(__name__)

logger.debug('render.py run')
file_id = 'render'

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, "render_output")
try:
    os.makedirs(OUT_DIR, exist_ok=True)
    logger.info(f'OUT_DIR created or exists | {file_id}')
except Exception as e:
    logger.error(f'error creating OUT_DIR: {e} | {file_id}')

executor = ThreadPoolExecutor(max_workers=4)
logger.info(f'ThreadPoolExecutor created | {file_id}')

def draw_frame(positions, size=(500, 500)):
    try:
        logger.info(f'draw frame | {file_id}')
        img = Image.new('RGB', size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        for bid, pos in positions.items():
            x, y = pos['x'], pos['y']
            angle = pos['angle']
            length = pos['length']
            rad = np.radians(angle)
            ex = x + np.cos(rad) * length
            ey = y + np.sin(rad) * length
            draw.line((int(x), int(y), int(ex), int(ey)), fill=(0, 0, 0), width=4)
            draw.ellipse((int(x - 4), int(y - 4), int(x + 4), int(y + 4)), fill=(0, 0, 0))
        logger.debug(f'draw frame completed | {file_id}')
        return np.array(img)
    except Exception as e:
        logger.error(f'error in draw_frame: {e} | {file_id}')
        return None

async def export_animation(scene, fps, update_status_callback):
    try:
        logger.info(f'export animation | {file_id}')
        update_status_callback("running")
        frames = []
        for i in sorted(scene.frames.keys()):
            pos = scene.compute_abs_positions(i)
            frames.append(
                {"positions": {k: {"x": v[0], "y": v[1], "angle": v[2], "length": v[3]} for k, v in pos.items()}})
        job_id = str(uuid.uuid4())
        out_dir = os.path.join(OUT_DIR, job_id)
        os.makedirs(out_dir, exist_ok=True)
        logger.debug(f'export directory {out_dir} created | {file_id}')

        def render_single(i, f):
            logger.info(f'rendering frame {i} | {file_id}')
            img = draw_frame(f['positions'])
            p = os.path.join(out_dir, f"frame_{i:04d}.png")
            imageio.imwrite(p, img)
            return img, p

        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(executor, render_single, i, f) for i, f in enumerate(frames)]
        results = await asyncio.gather(*tasks)
        imgs, saved_paths = zip(*results)

        gif_path = os.path.join(out_dir, f"{job_id}.gif")
        imageio.mimsave(gif_path, imgs, fps=fps)
        logger.debug(f'GIF saved to {gif_path} | {file_id}')

        mp4_path = os.path.join(out_dir, f"{job_id}.mp4")
        writer = imageio.get_writer(mp4_path, fps=fps)
        for im in imgs:
            writer.append_data(im)
        writer.close()
        logger.debug(f'MP4 saved to {mp4_path} | {file_id}')

        update_status_callback(f"Done: GIF {gif_path}, MP4 {mp4_path}")
        logger.debug(f'export animation completed | {file_id}')
    except Exception as e:
        logger.error(f'error in export_animation: {e} | {file_id}')
        update_status_callback(f"Error: {e}")