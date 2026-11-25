#!/usr/bin/env python3
"""Скриншоты варианта: python3 tools/shot.py v3 [страницы,через,запятую|all] [ширины: 1440,390]
Пишет /tmp/rp-shots/<v>/<page>-<w>.png (полная страница) и нарезку <page>-<w>_<n>.png по 1400px (десктоп) / 2000px (мобайл),
мобайл дополнительно склеивается по 5 полос в <page>-<w>-sheet<k>.png. Печатает горизонтальное переполнение."""
import sys, asyncio, pathlib
from PIL import Image
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent / "docs"
PAGES = ["index", "catalog-palletizers", "series-pp-pz-cn", "case-uvelka", "podbor"]
OVF = """()=>{const W=document.documentElement.clientWidth,o=[];document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();
if(r.right>W+1&&r.width>0&&!e.closest('.rp-mk')){let p=e.parentElement,s=false;while(p){const c=getComputedStyle(p).overflowX;if(['auto','scroll','hidden','clip'].includes(c)){s=true;break}p=p.parentElement}
if(!s)o.push(e.tagName+'.'+[...e.classList].join('.')+' r='+Math.round(r.right))}});return [document.documentElement.scrollWidth,o.slice(0,8)]}"""
async def main(v, pages, widths):
    out = pathlib.Path(f"/tmp/rp-shots/{v}"); out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        for w in widths:
            mob = w < 800
            ctx = await b.new_context(viewport={"width": w, "height": 900 if not mob else 844}, is_mobile=mob, has_touch=mob)
            pg = await ctx.new_page()
            for n in pages:
                await pg.goto((ROOT / v / f"{n}.html").as_uri())
                await pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                await pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,30))}scrollTo(0,0)}")
                await pg.wait_for_timeout(700)
                sw, bad = await pg.evaluate(OVF)
                print(f"{v} {n} {w}: scrollWidth={sw}" + (f"  OVERFLOW {bad}" if sw > w or bad else ""))
                f = out / f"{n}-{w}.png"
                await pg.screenshot(path=str(f), full_page=True)
                im = Image.open(f); step = 1400 if not mob else 2000
                parts = [im.crop((0, y, im.width, min(y + step, im.height))) for y in range(0, im.height, step)]
                if not mob:
                    for i, pc in enumerate(parts): pc.save(out / f"{n}-{w}_{i}.png")
                else:
                    for k in range(0, len(parts), 5):
                        g = parts[k:k + 5]; s = Image.new("RGB", (len(g) * (w + 10), step), "white")
                        for i, pc in enumerate(g): s.paste(pc, (i * (w + 10), 0))
                        s.save(out / f"{n}-{w}-sheet{k // 5}.png")
            await ctx.close()
        await b.close()
v = sys.argv[1]
pages = PAGES if len(sys.argv) < 3 or sys.argv[2] == "all" else sys.argv[2].split(",")
widths = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "1440,390").split(",")]
asyncio.run(main(v, pages, widths))
