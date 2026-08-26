"""Build a compact GitHub-safe tile-reveal animation from AttendGuard screenshots."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCES = [
    ASSETS / "attendguard-landing.jpeg",
    ASSETS / "attendguard-live-session.jpeg",
    ASSETS / "attendguard-reports.jpeg",
    ASSETS / "attendguard-fraud-monitor.jpeg",
]
OUTPUT = ASSETS / "attendguard-tile-reveal.gif"

WIDTH, HEIGHT = 960, 540
COLS, ROWS = 8, 5
FRAMES = 34


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def build_collage() -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#030914")
    cells = [(0, 0, 480, 270), (480, 0, 960, 270), (0, 270, 480, 540), (480, 270, 960, 540)]
    for source, box in zip(SOURCES, cells):
        image = cover(Image.open(source).convert("RGB"), (box[2] - box[0], box[3] - box[1]))
        image = ImageEnhance.Contrast(image).enhance(1.04)
        canvas.paste(image, box[:2])
    draw = ImageDraw.Draw(canvas)
    draw.line((480, 0, 480, 540), fill="#173A59", width=5)
    draw.line((0, 270, 960, 270), fill="#173A59", width=5)
    draw.rounded_rectangle((3, 3, WIDTH - 4, HEIGHT - 4), radius=24, outline="#1597C9", width=4)
    return canvas


def ease_out_cubic(value: float) -> float:
    return 1 - (1 - value) ** 3


def build_frames(final_image: Image.Image) -> list[Image.Image]:
    tile_w = WIDTH // COLS
    tile_h = HEIGHT // ROWS
    frames: list[Image.Image] = []

    for frame_index in range(FRAMES):
        frame = Image.new("RGB", (WIDTH, HEIGHT), "#020713")
        draw = ImageDraw.Draw(frame)
        for ring in range(1, 6):
            inset = ring * 28
            draw.rounded_rectangle(
                (inset, inset // 2, WIDTH - inset, HEIGHT - inset // 2),
                radius=28,
                outline=(5, 32 + ring * 5, 55 + ring * 8),
                width=1,
            )

        for row in range(ROWS):
            for col in range(COLS):
                delay = (col * 0.72 + row * 1.15) / 13
                raw = (frame_index / (FRAMES - 10) - delay) * 1.8
                progress = ease_out_cubic(max(0.0, min(1.0, raw)))
                if progress <= 0:
                    continue

                x0, y0 = col * tile_w, row * tile_h
                x1 = WIDTH if col == COLS - 1 else x0 + tile_w
                y1 = HEIGHT if row == ROWS - 1 else y0 + tile_h
                tile = final_image.crop((x0, y0, x1, y1))

                angle = (1 - progress) * (86 if (row + col) % 2 == 0 else -86)
                scale_x = 0.08 + progress * 0.92
                scale_y = 0.45 + progress * 0.55
                scaled = tile.resize(
                    (max(2, round(tile.width * scale_x)), max(2, round(tile.height * scale_y))),
                    Image.Resampling.LANCZOS,
                ).rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

                centre_x = (x0 + x1) // 2
                centre_y = (y0 + y1) // 2
                frame.paste(scaled, (centre_x - scaled.width // 2, centre_y - scaled.height // 2))

        frames.append(frame)

    frames.extend([final_image.copy()] * 14)
    return frames


def main() -> None:
    final_image = build_collage()
    frames = build_frames(final_image)
    palette_frames = [frame.quantize(colors=192, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for frame in frames]
    palette_frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=palette_frames[1:],
        duration=70,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB)")


if __name__ == "__main__":
    main()
