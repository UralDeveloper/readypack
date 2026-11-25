#!/usr/bin/env python3
"""Сборка макета Ready Pack в нескольких вариантах дизайна.

  python3 build.py            — собрать все варианты
  python3 build.py v3         — собрать только v3 (+ общие ассеты)

Источник страницы: themes/<v>/src/<файл>, если есть, иначе общий src/<файл>
(так же для партиалов _header.html, _footer.html, _icons.html).
Стили: css/site.css + css/pages.css (база v1) + themes/<v>/theme.css (если есть).
Выход: docs/<v>/<slug>.html, общие ассеты в docs/assets/ (img, fonts, css).
"""
import pathlib, re, shutil, sys

root = pathlib.Path(__file__).parent
src = root / "src"
docs = root / "docs"

VARIANTS = [
    ("v1", "Bento", "Светлые bento-плитки, крупный продукт в центре"),
    ("v2", "Clean", "Белый фон, тонкая крупная типографика, тёмные блоки с синим свечением"),
    ("v3", "Grid", "Тёплый светлый фон с инженерной сеткой, огромный жирный заголовок"),
    ("v4", "Gradient", "Пастельный градиент в фирменных цветах, стеклянная рамка, широкий капс"),
    ("v5", "Mono", "Монохромный серый, гигантский контурный логотип, стеклянные карточки"),
]
PAGES = [("index", "Главная"), ("catalog-palletizers", "Каталог"), ("series-pp-pz-cn", "Серия"),
         ("case-uvelka", "Кейс"), ("podbor", "Подбор")]


def ready():
    """Варианты, у которых есть тема (v1 — база). Только они попадают в сборку и переключатель."""
    return [x for x in VARIANTS if x[0] == "v1" or (root / "themes" / x[0] / "theme.css").exists()]


def sync_assets():
    """Копирует img/, fonts/, css/ в docs/assets/ (только изменённые файлы)."""
    for d in ("img", "fonts", "css"):
        for f in (root / d).rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                out = docs / "assets" / f.relative_to(root)
                if not out.exists() or out.stat().st_mtime < f.stat().st_mtime or out.stat().st_size != f.stat().st_size:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, out)


def pick(v, name):
    p = root / "themes" / v / "src" / name
    return (p if p.exists() else src / name).read_text(encoding="utf-8")


def fix_paths(html):
    # img/... и css/... в исходниках -> общие ассеты
    html = re.sub(r'(["\'`(])img/', r'\1../assets/img/', html)
    html = re.sub(r'(["\'(])fonts/', r'\1../assets/fonts/', html)
    return html


def switcher(v, slug):
    vs = "".join(
        f'<a href="../{k}/{slug}.html" data-v="{k}" title="{n} — {d}"{" class=on aria-current=true" if k == v else ""}>{k[1:]}</a>'
        for k, n, d in ready())
    ps = "".join(
        f'<a href="{s}.html"{" class=on aria-current=page" if s == slug else ""}>{l}</a>' for s, l in PAGES)
    name = next(n for k, n, _ in VARIANTS if k == v)
    return (f'<nav class="rp-mk" aria-label="Переключатель макета">'
            f'<span class="rp-mk__g"><b>Вариант</b>{vs}<i>{name}</i></span>'
            f'<span class="rp-mk__g rp-mk__p">{ps}</span>'
            f'<a class="rp-mk__all" href="../index.html" title="Все варианты">⌂</a></nav>'
            '<script>document.querySelectorAll(".rp-mk [data-v]").forEach(a=>a.addEventListener("click",e=>{'
            'const y=Math.round(scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight)*1000);'
            'sessionStorage.setItem("rp-y",y);}));'
            '(()=>{const y=sessionStorage.getItem("rp-y");if(y!==null){sessionStorage.removeItem("rp-y");'
            'addEventListener("load",()=>scrollTo(0,(document.documentElement.scrollHeight-innerHeight)*y/1000));}})();</script>')


def build(v):
    out = docs / v
    out.mkdir(parents=True, exist_ok=True)
    theme = root / "themes" / v / "theme.css"
    if theme.exists():
        shutil.copy2(theme, out / "theme.css")
    head_extra = (root / "themes" / v / "head.html")
    head_extra = head_extra.read_text(encoding="utf-8") if head_extra.exists() else ""
    part = {n: pick(v, f"_{n}.html") for n in ("icons", "header", "footer")}
    for slug, label in PAGES:
        raw = pick(v, f"{slug}.html")
        meta = dict(re.findall(r"<!--\s*(\w+):\s*(.*?)\s*-->", "\n".join(raw.split("\n")[:6])))
        body = re.sub(r"^(<!--.*?-->\s*)+", "", raw, flags=re.S)
        header = part["header"]
        if meta.get("nav"):
            header = header.replace(f'data-nav="{meta["nav"]}"', f'data-nav="{meta["nav"]}" class="is-active" aria-current="page"')
        html = f"""<!doctype html>
<html lang="ru" data-variant="{v}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{meta.get('title', 'Ready Pack')}</title>
<meta name="description" content="{meta.get('desc', '')}">
<meta name="robots" content="noindex">
<link rel="preload" href="fonts/onest-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="css/site.css">
<link rel="stylesheet" href="css/pages.css">
{'<link rel="stylesheet" href="theme.css">' if theme.exists() else ''}
<link rel="stylesheet" href="css/mk.css">
{head_extra}
</head>
<body class="page-{slug} theme-{v}">
{part['icons']}
{header}
<main>
{body}
</main>
{part['footer']}
{switcher(v, slug)}
</body>
</html>
"""
        html = html.replace('href="css/', 'href="../assets/css/')
        (out / f"{slug}.html").write_text(fix_paths(html), encoding="utf-8")
    print("built", v)


def chooser():
    cards = "".join(
        f'<a class="v" href="{k}/index.html"><img src="assets/thumbs/{k}.webp" alt="" onerror="this.remove()">'
        f'<span><b>{k.upper()} · {n}</b><small>{d}</small></span></a>' for k, n, d in ready())
    (docs / "index.html").write_text(f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Ready Pack — варианты дизайна</title>
<link rel="stylesheet" href="assets/css/chooser.css"></head>
<body><main><header><img src="assets/img/logo.svg" alt="Ready Pack" height="40">
<h1>Варианты дизайна нового сайта</h1>
<p>Вариантов: {len(ready())}, в каждом 5 страниц: главная, каталог, карточка серии, кейс, подбор. Внизу каждой страницы есть переключатель: вариант меняется, а страница остаётся та же.</p></header>
<div class="grid">{cards}</div></main></body></html>
""", encoding="utf-8")


if __name__ == "__main__":
    want = sys.argv[1:] or [k for k, _, _ in ready()]
    for k, _, _ in VARIANTS:  # убрать собранные копии вариантов без темы
        if k not in [r[0] for r in ready()] and (docs / k).exists():
            shutil.rmtree(docs / k)
    docs.mkdir(exist_ok=True)
    sync_assets()
    (docs / ".nojekyll").touch()
    chooser()
    for v in want:
        build(v)
