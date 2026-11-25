#!/usr/bin/env python3
"""Превью вариантов для стартовой страницы: первый экран главной 1440×900 -> docs/assets/thumbs/<v>.webp"""
import asyncio, pathlib, sys
from PIL import Image
from playwright.async_api import async_playwright
docs = pathlib.Path(__file__).resolve().parent.parent / "docs"
async def main(vs):
    out = docs / "assets" / "thumbs"; out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        for v in vs:
            await pg.goto((docs / v / "index.html").as_uri()); await pg.wait_for_timeout(900)
            await pg.add_style_tag(content=".rp-mk{display:none!important}")
            png = f"/tmp/rp-shots/thumb-{v}.png"; await pg.screenshot(path=png)
            im = Image.open(png).convert("RGB"); im.resize((960, 600), Image.LANCZOS).save(out / f"{v}.webp", quality=82)
            print(v)
        await b.close()
asyncio.run(main(sys.argv[1:] or [d.name for d in sorted(docs.glob("v*"))]))
