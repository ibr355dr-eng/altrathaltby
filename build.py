#!/usr/bin/env python3
"""يبني موقع التراث الطبي إلى docs/، وتنشره GitHub Actions عند كل تعديل.

    python3 build.py          (يحتاج: pip install markdown pyyaml)

المحتوى يُحرَّر من Pages CMS (app.pagescms.org) أو يدوياً:
    content/settings.json       اسم الموقع ووصفه ووسائل التواصل
    content/categories/*.md     التصنيفات (name, slug, description, order)
    content/research/*.md       البحوث (title, slug, category, summary, date, cover,
                                html_file, access, pay_url, draft) والنص تحت الترويسة
    media/                      الصور والملفات المرفوعة
"""
import html, json, re, shutil
from datetime import date
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
CONTENT, SITE, OUT = ROOT / "content", ROOT / "site", ROOT / "docs"
CFG = json.loads((CONTENT / "settings.json").read_text(encoding="utf-8"))
DOMAIN = "https://altrathaltby.com"
TODAY = date.today().isoformat()
ESC = html.escape
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
MORE = re.compile(r"<!--more-->|<p>\s*\[\[المزيد\]\]\s*</p>")

LOGO = ('<svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" stroke-width="2.4"/>'
        '<circle cx="50" cy="50" r="41" fill="none" stroke="currentColor" stroke-width="1"/>'
        '<path d="M61 17 45 50" stroke="currentColor" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M24 47h52c0 16-11 26-26 26S24 63 24 47z" fill="currentColor"/>'
        '<path d="M28 47h44" stroke="var(--paper,#faf8f3)" stroke-width="1.6"/><rect x="38" y="73" width="24" height="5.5" fill="currentColor"/></svg>')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;600;700&display=swap" rel="stylesheet">')

THEME_JS = ("<script>(function(){try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}catch(e){}})();"
            "function toggleTheme(){var d=document.documentElement,c=d.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'),n=c==='dark'?'light':'dark';"
            "d.dataset.theme=n;try{localStorage.setItem('theme',n)}catch(e){}}</script>")

NAV = [("/", "الرئيسية"), ("/mizaj/", "اختبار المزاج"), ("/about/", "عن الموقع")]

CONTACTS = [("email", "البريد"), ("whatsapp", "واتساب"), ("x", "إكس"), ("instagram", "إنستغرام"), ("tiktok", "تيك توك"),
            ("telegram", "تيليجرام"), ("youtube", "يوتيوب"), ("snapchat", "سناب شات")]


def ar(s):
    return str(s).translate(AR)


def ar_date(iso):
    y, m, d = str(iso).split("-")
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    return f"{ar(int(d))} {months[int(m) - 1]} {ar(y)}م"


def front(path):
    """يقرأ ملف Markdown بترويسة YAML ويعيد (الحقول، النص)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def contact_links():
    out = []
    for key, label in CONTACTS:
        v = (CFG.get(key) or "").strip()
        if not v:
            continue
        if key == "email":
            out.append((label, f"mailto:{v}", v))
        elif key == "whatsapp":
            out.append((label, f"https://wa.me/{v}", "+" + v))
        else:
            out.append((label, v, re.sub(r"^https?://(www\.)?", "", v).rstrip("/")))
    return out


# ---------- القالب ----------
def head(title, desc, path, og_type="website", jsonld=None, image=None):
    url = DOMAIN + path
    full = title if title == CFG["name"] else f"{title} | {CFG['name']}"
    img = DOMAIN + (image or "/og.png")
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ESC(full)}</title>
<meta name="description" content="{ESC(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#7b2d26">
<meta property="og:site_name" content="{ESC(CFG['name'])}">
<meta property="og:locale" content="ar_AR">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{ESC(title)}">
<meta property="og:description" content="{ESC(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{ESC(CFG['name'])}" href="/feed.xml">
{FONTS}
<link rel="stylesheet" href="/static/style.css?v={TODAY}">
{THEME_JS}{ld}"""


def masthead(active):
    links = "".join(f'<a href="{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    return (f'<a class="skip" href="#main">تخطَّ إلى المحتوى</a><header class="masthead"><div class="wrap">'
            f'<a class="brand" href="/">{LOGO}<span><b>{CFG["name"]}</b><small>{CFG["tagline"]}</small></span></a>'
            f'<nav class="nav" aria-label="الرئيسية">{links}<button class="theme" onclick="toggleTheme()" aria-label="الوضع الليلي">◐</button></nav></div></header>')


def foot():
    links = " ".join(f'<a href="{u}">{l}</a>' for l, u, _ in contact_links())
    return (f'<footer class="foot"><div class="wrap"><span>{CFG["name"]} © {ar(date.today().year)}م</span>'
            f'<nav aria-label="التواصل">{links}<a href="/sitemap.xml">خريطة الموقع</a></nav></div></footer>')


def page(title, desc, path, body, active="", **kw):
    return (f'<!doctype html><html lang="ar" dir="rtl"><head>{head(title, desc, path, **kw)}</head>'
            f'<body>{masthead(active)}<main id="main">{body}</main>{foot()}</body></html>')


def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def org():
    return {"@type": "Organization", "name": CFG["name"], "url": DOMAIN + "/", "logo": DOMAIN + "/icon-512.png"}


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(items)]}


# ---------- المحتوى ----------
def load_categories():
    cats = []
    for f in sorted((CONTENT / "categories").glob("*.md")):
        fm, _ = front(f)
        if not fm.get("name"):
            continue
        cats.append({"slug": str(fm.get("slug") or f.stem).strip(), "name": fm["name"], "desc": fm.get("description") or "",
                     "order": float(fm.get("order") or 99), "file": f})
    cats.sort(key=lambda c: (c["order"], c["name"]))
    return cats


def resolve_cat(value, cats):
    v = str(value or "").strip()
    for c in cats:
        if v in (c["slug"], c["name"], str(c["file"].relative_to(ROOT)), c["file"].stem):
            return c
    return None


def load_research(cats):
    items = []
    for f in sorted((CONTENT / "research").glob("*.md")):
        fm, body = front(f)
        if not fm.get("title") or fm.get("draft"):
            continue
        cat = resolve_cat(fm.get("category"), cats)
        if not cat:
            raise SystemExit(f"{f.name}: التصنيف «{fm.get('category')}» غير موجود")
        items.append({"slug": str(fm.get("slug") or f.stem).strip(), "title": fm["title"], "cat": cat,
                      "summary": (fm.get("summary") or "").strip(), "date": str(fm.get("date") or TODAY)[:10],
                      "cover": fm.get("cover") or "", "html_file": fm.get("html_file") or "",
                      "paid": fm.get("access") == "paid", "pay_url": fm.get("pay_url") or "",
                      "keywords": fm.get("keywords") or [], "body": markdown.markdown(body, extensions=["tables", "extra", "sane_lists"])})
    items.sort(key=lambda m: m["date"], reverse=True)
    return items


def entry(m, show_cat=True):
    cat = f'<span class="label"><a href="/category/{m["cat"]["slug"]}/">{m["cat"]["name"]}</a></span>' if show_cat else ""
    paid = '<span class="paid">مدفوع</span>' if m["paid"] else ""
    img = f'<img src="{ESC(m["cover"])}" alt="" loading="lazy">' if m["cover"] else ""
    q = ESC(" ".join([m["title"], m["summary"], m["cat"]["name"]] + list(m["keywords"])))
    return (f'<li class="entry" data-q="{q}"><div>{cat}<h3><a href="/research/{m["slug"]}/">{ESC(m["title"])}</a>{paid}</h3>'
            f'<p>{ESC(m["summary"])}</p><div class="meta">{ar_date(m["date"])}</div></div>{img}</li>')


def entries(items, show_cat=True):
    if not items:
        return '<p class="none">لم يُنشر في هذا القسم بحث بعد.</p>'
    return f'<ul class="entries">{"".join(entry(m, show_cat) for m in items)}</ul>'


def paywall(m):
    btn = f'<a class="btn" href="{ESC(m["pay_url"])}">أكمل قراءة البحث</a>' if m["pay_url"] else '<p class="muted">يتاح قريباً.</p>'
    return f'<div class="paywall"><h3>بقية البحث للمشتركين</h3>{btn}</div>'


def free_part(body):
    parts = MORE.split(body, maxsplit=1)
    if len(parts) == 2:
        return parts[0]
    paras = re.findall(r"<(?:p|h\d|ul|ol|table|blockquote)[\s>].*?</(?:p|h\d|ul|ol|table|blockquote)>", body, re.S)
    return "".join(paras[:3])


def build_research(m):
    path = f"/research/{m['slug']}/"
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": m["title"], "description": m["summary"], "inLanguage": "ar",
           "datePublished": m["date"], "url": DOMAIN + path, "author": org(), "publisher": org(),
           "isAccessibleForFree": not m["paid"], "image": DOMAIN + (m["cover"] or "/og.png")},
          crumbs_ld([("الرئيسية", "/"), (m["cat"]["name"], f"/category/{m['cat']['slug']}/"), (m["title"], path)])]
    hf = m["html_file"]
    if hf.endswith(".html") and not m["paid"]:
        # صفحة جاهزة: تُعرض كما هي، ويُحقن فيها رأس الموقع وشريط علوي
        raw = (ROOT / hf.lstrip("/")).read_text(encoding="utf-8")
        h = head(m["title"], m["summary"], path, og_type="article", jsonld=ld, image=m["cover"] or None)
        h = re.sub(r'<link rel="stylesheet" href="/static/style\.css[^"]*">', "", h)
        raw = re.sub(r"<title>.*?</title>", "", raw, flags=re.S)
        raw = re.sub(r'<meta[^>]+(charset|name="viewport"|name="description")[^>]*>', "", raw)
        raw = re.sub(r"<head[^>]*>", lambda x: x.group(0) + h, raw, count=1)
        bar = (f'<div style="font-family:Amiri,serif;background:#7b2d26;color:#fff;padding:8px 16px;display:flex;gap:18px;align-items:center;direction:rtl;font-size:17px">'
               f'<a href="/" style="color:#fff;text-decoration:none;font-weight:700">{CFG["name"]}</a>'
               f'<a href="/category/{m["cat"]["slug"]}/" style="color:#fff;opacity:.85">{m["cat"]["name"]}</a></div>')
        write(f"research/{m['slug']}/index.html", re.sub(r"(<body[^>]*>)", lambda x: x.group(1) + bar, raw, count=1))
        return path
    body = m["body"]
    if hf.endswith(".pdf") and not m["paid"]:
        body += f'<p><a class="btn line" href="{ESC(hf)}">تنزيل البحث (PDF)</a></p><iframe class="embed" src="{ESC(hf)}" title="{ESC(m["title"])}"></iframe>'
    if m["paid"]:
        body = free_part(body) + paywall(m)
    cover = f'<img class="cover" src="{ESC(m["cover"])}" alt="">' if m["cover"] else ""
    html_ = (f'<article class="wrap page"><p class="crumbs"><a href="/">الرئيسية</a> ‹ <a href="/category/{m["cat"]["slug"]}/">{m["cat"]["name"]}</a></p>'
             f'<header class="page-h prose"><h1>{ESC(m["title"])}</h1><p>{ar_date(m["date"])}</p></header>'
             f'<div class="prose">{cover}{body}</div></article>')
    write(f"research/{m['slug']}/index.html", page(m["title"], m["summary"], path, html_, og_type="article", jsonld=ld, image=m["cover"] or None))
    return path


# ---------- الصفحات ----------
def build_home(research, cats):
    catlist = "".join(f'<li><a href="/category/{c["slug"]}/">{c["name"]}<span>{ar(sum(1 for m in research if m["cat"] is c))}</span></a></li>' for c in cats)
    body = f"""<div class="wrap"><section class="intro"><p>{CFG['description']}</p></section>
<div class="layout"><section><div class="sec-h"><h2>أحدث البحوث</h2><form class="search" role="search" onsubmit="return false"><input id="q" type="search" placeholder="ابحث…" aria-label="ابحث في البحوث"></form></div>
{entries(research)}</section>
<aside class="aside"><h2>التصنيفات</h2><ul class="cats">{catlist}</ul>
<div class="box"><h2>اعرف مزاجك</h2><p>دموي أم صفراوي أم بلغمي أم سوداوي؟ اثنا عشر سؤالاً قصيراً تكشف لك نسبة كل مزاج فيك.</p><a class="btn" href="/mizaj/">ابدأ الاختبار</a></div></aside></div></div>
<script>(function(){{var n=function(s){{return s.replace(/[\\u064B-\\u0652\\u0640]/g,'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه')}},q=document.getElementById('q');
q&&q.addEventListener('input',function(){{var v=n(q.value.trim());document.querySelectorAll('.entry').forEach(function(e){{e.classList.toggle('hidden',!!v&&n(e.dataset.q).indexOf(v)<0)}})}})}})();</script>"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": CFG["name"], "url": DOMAIN + "/", "inLanguage": "ar", "description": CFG["description"]},
          dict(org(), **{"@context": "https://schema.org", "sameAs": [u for l, u, _ in contact_links() if u.startswith("http") and "wa.me" not in u]})]
    write("index.html", page(CFG["name"], CFG["description"], "/", body, "/", jsonld=ld))


def build_categories(research, cats):
    for c in cats:
        path = f"/category/{c['slug']}/"
        body = (f'<div class="wrap page"><p class="crumbs"><a href="/">الرئيسية</a></p><header class="page-h"><h1>{c["name"]}</h1><p>{c["desc"]}</p></header>'
                f'{entries([m for m in research if m["cat"] is c], show_cat=False)}</div>')
        write(f"category/{c['slug']}/index.html", page(c["name"], c["desc"] or c["name"], path, body, jsonld=[crumbs_ld([("الرئيسية", "/"), (c["name"], path)])]))


def build_mizaj():
    qs = json.loads((SITE / "mizaj/questions.json").read_text(encoding="utf-8"))
    wa = (CFG.get("whatsapp") or "").strip()
    data = {"humors": qs["humors"], "basics": qs["basics"], "questions": qs["questions"], "whatsapp": wa, "waMsg": CFG.get("whatsapp_message") or ""}
    ask = (f'<div class="ask"><h3>عندك سؤال عن نتيجتك؟</h3><p>راسلنا على واتساب، وأرسل لنا نتيجتك.</p>'
           f'<a class="btn wa" id="mz-wa" href="https://wa.me/{wa}" target="_blank" rel="noopener">تواصل عبر واتساب</a></div>') if wa else ""
    n = len(qs["questions"])
    body = f"""<div class="wrap page"><div class="mz" id="mz-app">
<header class="page-h"><h1>اختبار المزاج</h1><p>هل مزاجك دموي أم صفراوي أم بلغمي أم سوداوي؟ أجب عن {ar(n)} سؤالاً قصيراً، وتظهر لك نسبة كل مزاج فيك.</p></header>
<section id="mz-intro" class="step"><h2 tabindex="-1">قبل أن نبدأ</h2><form id="mz-basics">
<fieldset class="field"><legend>الجنس</legend><div class="opts row" id="mz-sex"></div></fieldset>
<div class="field"><label for="mz-age">العمر</label><input id="mz-age" type="number" min="1" max="120" inputmode="numeric" placeholder="بالسنوات"></div>
<fieldset class="field"><legend>جوّ المدينة التي تسكنها</legend><div class="opts row" id="mz-land"></div></fieldset>
<button class="btn" id="mz-start" type="submit" disabled>ابدأ</button></form></section>
<section id="mz-q" class="step hidden"><div class="qtop"><span id="mz-qnum"></span><button id="mz-prev" type="button">→ السابق</button></div>
<div class="progress"><i id="mz-bar"></i></div><h2 id="mz-qt" tabindex="-1"></h2><div class="opts" id="mz-opts" role="radiogroup" aria-labelledby="mz-qt"></div></section>
<section id="mz-result" class="step hidden"><h2 tabindex="-1" class="muted" style="font-size:20px;margin:0">مزاجك الغالب</h2>
<p class="res-name" id="mz-name"></p><p class="res-qual" id="mz-qual"></p><p id="mz-text"></p>
<div class="bars" id="mz-bars"></div>{ask}
<div class="actions"><button class="btn line" id="mz-share" type="button">شارك النتيجة</button><button class="btn line" id="mz-again" type="button">أعد الاختبار</button></div></section>
</div></div>
<script>window.MZ={json.dumps(data, ensure_ascii=False)};</script><script src="/static/mizaj.js?v={TODAY}" defer></script>"""
    ld = [{"@context": "https://schema.org", "@type": "Quiz", "name": "اختبار المزاج", "inLanguage": "ar", "url": DOMAIN + "/mizaj/",
           "about": ["المزاج", "الأخلاط الأربعة", "طب الأخلاط"], "publisher": org()}, crumbs_ld([("الرئيسية", "/"), ("اختبار المزاج", "/mizaj/")])]
    write("mizaj/index.html", page("اختبار المزاج: دموي أم صفراوي أم بلغمي أم سوداوي؟",
          "اختبار قصير يكشف مزاجك الغالب ونسبة الدموي والصفراوي والبلغمي والسوداوي فيك، على طريقة الطب العربي القديم.", "/mizaj/", body, "/mizaj/", jsonld=ld))


def build_about():
    items = "".join(f'<li><span>{l}</span><a href="{u}">{ESC(t)}</a></li>' for l, u, t in contact_links())
    body = (f'<div class="wrap page"><header class="page-h"><h1>عن الموقع</h1></header><div class="prose">'
            f'{"".join(f"<p>{ESC(p)}</p>" for p in (CFG.get("about") or "").split(chr(10)) if p.strip())}'
            f'<h2>تواصل معنا</h2><ul class="contacts">{items}</ul></div></div>')
    write("about/index.html", page("عن الموقع", f"عن {CFG['name']} ووسائل التواصل.", "/about/", body, "/about/"))


def build_404():
    body = '<div class="wrap page"><h1>الصفحة غير موجودة</h1><p>لعلّ الرابط تغيّر. <a href="/">ارجع إلى الرئيسية</a>.</p></div>'
    write("404.html", page("الصفحة غير موجودة", "الصفحة المطلوبة غير موجودة.", "/404.html", body).replace("<head>", '<head><meta name="robots" content="noindex">', 1))


def build_meta(urls, research):
    sm = "".join(f"<url><loc>{DOMAIN}{u}</loc><lastmod>{lm}</lastmod></url>" for u, lm in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    write("CNAME", DOMAIN.split("//")[1])
    write(".nojekyll", "")
    write("site.webmanifest", json.dumps({"name": CFG["name"], "short_name": CFG["name"], "lang": "ar", "dir": "rtl", "start_url": "/",
          "display": "standalone", "background_color": "#faf8f3", "theme_color": "#7b2d26",
          "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                    {"src": "/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, ensure_ascii=False))
    items = "".join(f"<item><title>{ESC(m['title'])}</title><link>{DOMAIN}/research/{m['slug']}/</link><guid>{DOMAIN}/research/{m['slug']}/</guid>"
                    f"<pubDate>{date.fromisoformat(m['date']).strftime('%a, %d %b %Y')} 00:00:00 +0300</pubDate><description>{ESC(m['summary'])}</description></item>"
                    for m in research[:30])
    write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{ESC(CFG["name"])}</title><link>{DOMAIN}/</link>'
          f'<description>{ESC(CFG["description"])}</description><language>ar</language>{items}</channel></rss>')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SITE / "static", OUT / "static", ignore=shutil.ignore_patterns("icons"))
    for f in (SITE / "static" / "icons").glob("*"):
        shutil.copy2(f, OUT / f.name)
    shutil.copytree(ROOT / "media", OUT / "media", ignore=shutil.ignore_patterns(".gitkeep"))
    cats = load_categories()
    research = load_research(cats)
    slugs = [m["slug"] for m in research]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("رابطان متشابهان لبحثين: " + ", ".join(s for s in slugs if slugs.count(s) > 1))
    last = max([m["date"] for m in research], default=TODAY)
    urls = [("/", last), ("/mizaj/", TODAY), ("/about/", TODAY)] + [(f"/category/{c['slug']}/", last) for c in cats]
    build_home(research, cats)
    build_categories(research, cats)
    build_mizaj()
    build_about()
    build_404()
    urls += [(build_research(m), m["date"]) for m in research]
    build_meta(urls, research)
    print(f"بُني الموقع: {len(research)} بحثاً، {len(cats)} تصنيفات، {len(urls)} رابطاً → {OUT}")


if __name__ == "__main__":
    main()
