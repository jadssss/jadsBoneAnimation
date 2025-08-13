import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw
import imageio

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, "render_output")
try:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Отладка: Директория OUT_DIR создана или существует")
except Exception as e:
    print(f"Отладка: Ошибка создания OUT_DIR: {e}")

executor = ThreadPoolExecutor(max_workers=4)
print("Отладка: ThreadPoolExecutor создан")


def draw_frame(positions, size=(500, 500)):
    try:
        print("Отладка: Начало draw_frame")
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
        print("Отладка: draw_frame завершён")
        return np.array(img)
    except Exception as e:
        print(f"Отладка: Ошибка в draw_frame: {e}")
        return None


async def export_animation(scene, fps, update_status_callback):
    try:
        print("Отладка: Начало export_animation")
        update_status_callback("running")
        frames = []
        for i in sorted(scene.frames.keys()):
            pos = scene.compute_abs_positions(i)
            frames.append(
                {"positions": {k: {"x": v[0], "y": v[1], "angle": v[2], "length": v[3]} for k, v in pos.items()}})
        job_id = str(uuid.uuid4())
        out_dir = os.path.join(OUT_DIR, job_id)
        os.makedirs(out_dir, exist_ok=True)
        print(f"Отладка: Директория экспорта {out_dir} создана")

        def render_single(i, f):
            print(f"Отладка: Рендеринг кадра {i}")
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
        print(f"Отладка: GIF сохранён в {gif_path}")

        mp4_path = os.path.join(out_dir, f"{job_id}.mp4")
        writer = imageio.get_writer(mp4_path, fps=fps)
        for im in imgs:
            writer.append_data(im)
        writer.close()
        print(f"Отладка: MP4 сохранён в {mp4_path}")

        update_status_callback(f"Done: GIF {gif_path}, MP4 {mp4_path}")
        print("Отладка: export_animation завершён")
    except Exception as e:
        print(f"Отладка: Ошибка в export_animation: {e}")
        update_status_callback(f"Ошибка: {e}")