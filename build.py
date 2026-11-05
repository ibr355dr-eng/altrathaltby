#!/usr/bin/env python3
"""يبني موقع التراث الطبي من مجلد site/ إلى docs/ (الذي تنشره GitHub Pages).

    python3 build.py

البحوث: site/research/<slug>/meta.json + index.html (وأي ملفات معها).
    mode = "body"        → index.html جزء يوضع داخل قالب الموقع.
    mode = "standalone"  → index.html صفحة كاملة، يُحقن فيها رأس SEO وشريط الموقع.
    access = "paid"      → لا يُنشر إلا ما قبل <!--more--> ومعه صندوق الاشتراك.
"""
import html, json, re, shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "site", ROOT / "docs"
CFG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
DOMAIN = CFG["domain"]
TODAY = date.today().isoformat()
ESC = html.escape
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="none" stroke="currentColor" stroke-width="2.5" opacity=".35"/>'
        '<path d="M32 32V6A26 26 0 0 1 58 32Z" fill="#a8323a"/><path d="M32 32H58A26 26 0 0 1 32 58Z" fill="#b7831b"/>'
        '<path d="M32 32V58A26 26 0 0 1 6 32Z" fill="#4b3c5a"/><path d="M32 32H6A26 26 0 0 1 32 6Z" fill="#3f6f8c"/>'
        '<circle cx="32" cy="32" r="9" fill="var(--surface,#fffdf8)"/></svg>')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;600;700&display=swap" rel="stylesheet">')

THEME_JS = ("<script>(function(){try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}catch(e){}})();"
            "function toggleTheme(){var d=document.documentElement,c=d.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'),n=c==='dark'?'light':'dark';"
            "d.dataset.theme=n;try{localStorage.setItem('theme',n)}catch(e){}}</script>")

NAV = [("/", "الرئيسية"), ("/mizaj/", "اختبار المزاج"), ("/about/", "عن الموقع")]


def ar(s):
    return str(s).translate(AR)


def ar_date(iso):
    y, m, d = iso.split("-")
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    return f"{ar(int(d))} {months[int(m) - 1]} {ar(y)}م"


def head(title, desc, path, og_type="website", jsonld=None, extra=""):
    url = DOMAIN + path
    full = title if title == CFG["name"] else f"{title} | {CFG['name']}"
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ESC(full)}</title>
<meta name="description" content="{ESC(desc)}">
<link rel="canonical" href="{url}">
<meta name="author" content="{ESC(CFG['author'])}">
<meta name="theme-color" content="#7a4b1f">
<meta property="og:site_name" content="{ESC(CFG['name'])}">
<meta property="og:locale" content="ar_AR">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{ESC(title)}">
<meta property="og:description" content="{ESC(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@alturathaltibb">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{ESC(CFG['name'])}" href="/feed.xml">
{FONTS}
<link rel="stylesheet" href="/static/style.css?v={TODAY}">
{THEME_JS}{ld}{extra}"""


def header(active):
    links = "".join(f'<a href="{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    return (f'<a class="skip" href="#main">تخطَّ إلى المحتوى</a><header class="site-h"><div class="wrap">'
            f'<a class="brand" href="/">{LOGO}<span>{CFG["name"]}</span></a><nav class="nav" aria-label="الرئيسية">{links}</nav>'
            f'<button class="theme-btn" onclick="toggleTheme()" aria-label="تبديل الوضع الليلي">◐</button></div></header>')


def footer():
    return (f'<footer class="site-f"><div class="wrap"><span>إعداد: {CFG["author"]} — {CFG["name"]} ‎© {ar(date.today().year)}م</span>'
            f'<span><a href="{CFG["social"]["x"]}" rel="me">إكس</a> · <a href="{CFG["social"]["tiktok"]}" rel="me">تيك توك</a> · '
            f'<a href="mailto:{CFG["email"]}">راسلنا</a> · <a href="/sitemap.xml">خريطة الموقع</a></span></div></footer>')


def page(title, desc, path, body, active="", **kw):
    return (f'<!doctype html><html lang="ar" dir="rtl"><head>{head(title, desc, path, **kw)}</head>'
            f'<body>{header(active)}<main id="main">{body}</main>{footer()}</body></html>')


def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------- البحوث ----------
def load_research():
    items = []
    for d in sorted((SRC / "research").iterdir()) if (SRC / "research").exists() else []:
        if not (d / "meta.json").exists():
            continue
        m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        if m.get("draft"):
            continue
        m["slug"] = d.name
        m["dir"] = d
        m.setdefault("access", "free")
        m.setdefault("mode", "body")
        m.setdefault("updated", m["date"])
        items.append(m)
    items.sort(key=lambda m: m["date"], reverse=True)
    return items


def card(m):
    paid = '<span class="tag paid">مدفوع</span> ' if m["access"] == "paid" else ""
    return (f'<a class="card" href="/research/{m["slug"]}/" data-q="{ESC(m["title"] + " " + m["summary"] + " " + " ".join(m.get("keywords", [])))}">'
            f'<h3>{ESC(m["title"])}</h3><p>{ESC(m["summary"])}</p><span class="meta">{paid}{ar_date(m["date"])}</span></a>')


def article_ld(m, url):
    return {"@context": "https://schema.org", "@type": "ScholarlyArticle", "headline": m["title"], "description": m["summary"],
            "inLanguage": "ar", "datePublished": m["date"], "dateModified": m["updated"], "url": url,
            "author": {"@type": "Person", "name": CFG["author"]}, "publisher": {"@type": "Organization", "name": CFG["name"], "url": DOMAIN},
            "keywords": ", ".join(m.get("keywords", [])), "isAccessibleForFree": m["access"] == "free", "image": DOMAIN + "/og.png"}


def paywall_box(m):
    link = m.get("pay_url")
    btn = f'<a class="btn" href="{ESC(link)}">أكمل قراءة البحث</a>' if link else '<span class="tag">يتاح قريباً</span>'
    return f'<div class="paywall"><h3>بقية البحث للمشتركين</h3><p>هذا ما يُعرض مجاناً من البحث.</p>{btn}</div>'


def build_research(m, cats):
    path = f"/research/{m['slug']}/"
    raw = (m["dir"] / "index.html").read_text(encoding="utf-8")
    paid = m["access"] == "paid"
    if paid:
        if "<!--more-->" not in raw:
            raise SystemExit(f"{m['slug']}: بحث مدفوع بلا علامة <!--more-->")
        raw = raw.split("<!--more-->")[0]
    ld = [article_ld(m, DOMAIN + path), crumbs_ld([("الرئيسية", "/"), (cats[m["category"]]["name"], f"/category/{m['category']}/"), (m["title"], path)])]
    if m["mode"] == "standalone":
        h = head(m["title"], m["summary"], path, og_type="article", jsonld=ld)
        h = re.sub(r'<link rel="stylesheet" href="/static/style.css[^"]*">', "", h)
        raw = re.sub(r"<title>.*?</title>", "", raw, flags=re.S)
        raw = re.sub(r'<meta[^>]+(charset|name="viewport"|name="description")[^>]*>', "", raw)
        raw = re.sub(r"<head>", "<head>" + h, raw, count=1)
        bar = (f'<div style="font-family:Amiri,serif;background:#7a4b1f;color:#fff;padding:6px 16px;display:flex;gap:16px;align-items:center;direction:rtl">'
               f'<a href="/" style="color:#fff;text-decoration:none;font-weight:700">{CFG["name"]}</a>'
               f'<a href="/category/{m["category"]}/" style="color:#fff">{cats[m["category"]]["name"]}</a></div>')
        raw = re.sub(r"(<body[^>]*>)", r"\1" + bar, raw, count=1)
        if paid:
            raw += paywall_box(m) + "</body></html>"
        out = raw
    else:
        body = (f'<article class="article"><div class="wrap"><p class="crumbs"><a href="/">الرئيسية</a> ‹ '
                f'<a href="/category/{m["category"]}/">{cats[m["category"]]["name"]}</a></p>'
                f'<h1>{ESC(m["title"])}</h1><p class="byline">إعداد: {CFG["author"]} · {ar_date(m["date"])}</p>'
                f'<div class="prose">{raw}{paywall_box(m) if paid else ""}</div></div></article>')
        out = page(m["title"], m["summary"], path, body, og_type="article", jsonld=ld)
    write(f"research/{m['slug']}/index.html", out)
    for f in m["dir"].rglob("*"):
        if f.is_file() and f.name not in ("meta.json", "index.html") and not (paid and f.name.startswith("full")):
            dst = OUT / "research" / m["slug"] / f.relative_to(m["dir"])
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
    return path


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(items)]}


# ---------- الصفحات ----------
def build_home(research, cats):
    secs = []
    for c in CFG["categories"]:
        rs = [m for m in research if m["category"] == c["slug"]]
        inner = f'<div class="grid">{"".join(card(m) for m in rs)}</div>' if rs else '<p class="empty">بحوث هذا القسم قيد الإعداد، وتُنشر هنا تباعاً.</p>'
        secs.append(f'<section class="cat" id="{c["slug"]}"><div class="cat-h"><h2><a href="/category/{c["slug"]}/" style="color:inherit;text-decoration:none">{c["name"]}</a></h2>'
                    f'<span class="count">{ar(len(rs))} {"بحث" if len(rs) != 2 else "بحثان"}</span></div><p class="cat-desc">{c["desc"]}</p>{inner}</section>')
    body = f"""<div class="wrap"><section class="hero"><h1>{CFG['name']}</h1><p class="byline">إعداد: {CFG['author']}</p>
<p class="lead">{CFG['tagline']}: بحوث وملخصات موثّقة من كتب الأطباء المتقدمين، كل نقلٍ فيها بكتابه وصفحته.</p>
<form class="search" role="search" onsubmit="return false"><input id="q" type="search" placeholder="ابحث في البحوث…" aria-label="ابحث في البحوث"></form></section>
<div class="feature"><div><h2>اختبار المزاج</h2><p>أجب عن أسئلة مأخوذة من «أجناس الدلائل العشرة» عند ابن سينا وابن النفيس، واعرف نسبة كل خلط فيك: الدموي، والصفراوي، والبلغمي، والسوداوي.</p>
<a class="btn" href="/mizaj/">ابدأ الاختبار</a></div>{LOGO}</div>
{''.join(secs)}</div>
<script>(function(){{var n=function(s){{return s.replace(/[\\u064B-\\u0652\\u0640]/g,'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه')}};
document.getElementById('q').addEventListener('input',function(e){{var v=n(e.target.value.trim());document.querySelectorAll('.card[data-q]').forEach(function(c){{c.classList.toggle('hidden',v&&n(c.dataset.q).indexOf(v)<0)}})}})}})();</script>"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": CFG["name"], "url": DOMAIN + "/", "inLanguage": "ar", "description": CFG["description"],
           "author": {"@type": "Person", "name": CFG["author"]}},
          {"@context": "https://schema.org", "@type": "Organization", "name": CFG["name"], "url": DOMAIN + "/", "logo": DOMAIN + "/icon-512.png",
           "email": CFG["email"], "sameAs": list(CFG["social"].values())}]
    write("index.html", page(CFG["name"], CFG["description"], "/", body, "/", jsonld=ld))


def build_categories(research):
    for c in CFG["categories"]:
        rs = [m for m in research if m["category"] == c["slug"]]
        path = f"/category/{c['slug']}/"
        inner = f'<div class="grid">{"".join(card(m) for m in rs)}</div>' if rs else '<p class="empty">بحوث هذا القسم قيد الإعداد، وتُنشر هنا تباعاً.</p>'
        body = f'<div class="wrap article"><p class="crumbs"><a href="/">الرئيسية</a></p><h1>{c["name"]}</h1><p class="lead">{c["desc"]}</p>{inner}</div>'
        write(f"category/{c['slug']}/index.html", page(c["name"], c["desc"], path, body,
              jsonld=[crumbs_ld([("الرئيسية", "/"), (c["name"], path)])]))


def build_mizaj(research):
    qs = json.loads((SRC / "mizaj/questions.json").read_text(encoding="utf-8"))
    srcs = json.loads((SRC / "mizaj/sources.json").read_text(encoding="utf-8"))
    short = {"qanun": "القانون ج١", "mujaz": "الموجز"}
    data = {"humors": qs["humors"], "basics": qs["basics"], "questions": qs["questions"], "related": qs["related"],
            "src": {p["id"]: {"short": short[p["book"]], "page": p["page"]} for p in srcs["passages"]},
            "pub": {m["slug"]: {"title": m["title"], "summary": m["summary"]} for m in research}}
    n = len(qs["questions"])
    body = f"""<div class="wrap mz"><h1>اختبار المزاج</h1>
<p class="lead">تقدير لمزاجك الغالب (الدموي، الصفراوي، البلغمي، السوداوي) مبنيّ على «علامات الأمزجة عشرة أجناس» في «الموجز» لابن النفيس و«القانون» لابن سينا، وعلى علامات غلبة الأخلاط. كل سؤال معه مصدره، ونصوص المصادر كاملة في <a href="/mizaj/sources/">صفحة المصادر</a>.</p>
<div id="mz-app">
<section id="mz-intro" class="panel"><form id="mz-basics">
<h2>البيانات الأساسية</h2>
<div class="field"><label class="lbl" for="mz-name">الاسم <small>(اختياري، لا يُحفظ)</small></label><input id="mz-name" type="text" autocomplete="given-name"></div>
<fieldset class="field"><legend>الجنس</legend><div class="opts" id="mz-sex"></div></fieldset>
<div class="field"><label class="lbl" for="mz-age">العمر بالسنوات</label><input id="mz-age" type="number" min="1" max="120" inputmode="numeric" required></div>
<fieldset class="field"><legend>طبيعة البلد الذي تسكنه</legend><div class="opts" id="mz-land"></div></fieldset>
<p class="qsrc">يدخل الجنس والسن والبلد في الحساب لأن ابن النفيس قال: «وقد يدلّ على كل ذلك السنّ والبلد والفصل والتدبير المتقدّم» (<a href="/mizaj/sources/#mujaz-48">الموجز ص٤٨</a>). ثم {ar(n)} سؤالاً.</p>
<button class="btn" id="mz-start" type="submit" disabled>ابدأ الأسئلة</button></form></section>
<section id="mz-q" class="panel hidden" aria-live="polite"><div class="qmeta"><span id="mz-qnum"></span><span id="mz-genus"></span></div>
<div class="progress"><i id="mz-bar"></i></div><h2 id="mz-qt" tabindex="-1"></h2>
<div class="opts" id="mz-opts" role="radiogroup"></div><p class="qsrc" id="mz-qsrc"></p>
<div class="row" style="margin-top:16px"><button class="btn" id="mz-next" disabled>التالي</button><button class="btn ghost" id="mz-prev">السابق</button></div></section>
<section id="mz-result" class="panel hidden"><h2 id="mz-who" tabindex="-1">نتيجتك</h2>
<div class="bars" id="mz-bars"></div><p class="verdict" id="mz-verdict"></p><p id="mz-qual"></p>
<div id="mz-desc"></div>
<details><summary><b>لماذا هذه النتيجة؟</b> (كل علامة ومصدرها)</summary><ul class="why" id="mz-why"></ul>
<p class="qsrc">طريقة الحساب: لكل خلط نقطة أساس، وكل علامة تزيد خلطها: العلامة الدالة على خلط بعينه نقطتان له، والعلامة الدالة على كيفية (حرارة، برودة، رطوبة، يبوسة) نقطة لكل خلط من الخلطين اللذين فيهما تلك الكيفية، ثم تُقسم نقاط كل خلط على المجموع.</p></details>
<div id="mz-rel-wrap" class="hidden"><h3 style="margin-top:20px">بحوث ذات صلة</h3><div class="grid" id="mz-rel"></div></div>
<div class="row noprint" style="margin-top:20px"><button class="btn" id="mz-share">شارك النتيجة</button><button class="btn ghost" id="mz-print">اطبع</button><button class="btn ghost" id="mz-again">أعد الاختبار</button></div></section>
</div></div>
<script>window.MZ={json.dumps(data, ensure_ascii=False)};</script><script src="/static/mizaj.js?v={TODAY}" defer></script>"""
    ld = [{"@context": "https://schema.org", "@type": "Quiz", "name": "اختبار المزاج في الطب العربي القديم", "inLanguage": "ar", "url": DOMAIN + "/mizaj/",
           "about": ["المزاج", "الأخلاط الأربعة", "طب الأخلاط"], "educationalUse": "self assessment",
           "author": {"@type": "Person", "name": CFG["author"]},
           "citation": [srcs["books"][b]["title"] for b in srcs["books"]]},
          crumbs_ld([("الرئيسية", "/"), ("اختبار المزاج", "/mizaj/")])]
    desc = "اختبار المزاج: اعرف نسبة الدموي والصفراوي والبلغمي والسوداوي فيك، بأسئلة من علامات الأمزجة في القانون لابن سينا والموجز لابن النفيس."
    write("mizaj/index.html", page("اختبار المزاج: دموي أم صفراوي أم بلغمي أم سوداوي؟", desc, "/mizaj/", body, "/mizaj/", jsonld=ld))

    cards = []
    for p in srcs["passages"]:
        b = srcs["books"][p["book"]]
        paras = "".join(f"<p>{ESC(t)}</p>" for t in p["text"])
        cards.append(f'<article class="src-card" id="{p["id"]}"><h2>{ESC(p["heading"])}</h2>'
                     f'<p class="bk">«{b["title"]}» — {b["author"]}. {b["edition"]}. <b>ص{p["page"]}</b>.</p>{paras}</article>')
    body = (f'<div class="wrap article"><p class="crumbs"><a href="/">الرئيسية</a> ‹ <a href="/mizaj/">اختبار المزاج</a></p>'
            f'<h1>مصادر اختبار المزاج</h1><p class="lead">نصوص علامات الأمزجة وغلبة الأخلاط كما في الطبعتين المذكورتين، وما بين المعقوفين [ ] زيادة للإيضاح، والنقاط … حذفٌ من النص.</p>'
            f'<div class="prose">{"".join(cards)}</div><p><a class="btn" href="/mizaj/">ارجع إلى الاختبار</a></p></div>')
    write("mizaj/sources/index.html", page("مصادر اختبار المزاج من القانون والموجز",
          "نصوص علامات الأمزجة العشرة وعلامات غلبة الدم والصفراء والبلغم والسوداء من القانون لابن سينا والموجز لابن النفيس، بأرقام الصفحات.",
          "/mizaj/sources/", body, jsonld=[crumbs_ld([("الرئيسية", "/"), ("اختبار المزاج", "/mizaj/"), ("المصادر", "/mizaj/sources/")])]))


def build_about():
    body = f"""<div class="wrap article"><h1>عن الموقع</h1><div class="prose">
<p>«{CFG['name']}» مرجع لبحوث الطب العربي القديم وطب الأخلاط، من إعداد {CFG['author']}.</p>
<h2>منهج البحوث</h2><p>كل معلومة في البحوث منسوبة إلى قائلها باسمه، ومعزوّة إلى كتابها وصفحتها من الطبعة المذكورة، ومن مصادرها: «القانون في الطب» لابن سينا، و«الموجز في الطب» لابن النفيس، و«الجامع لمفردات الأدوية والأغذية» لابن البيطار، و«تذكرة أولي الألباب» لداود الأنطاكي، وغيرها.</p>
<h2>اختبار المزاج</h2><p><a href="/mizaj/">اختبار المزاج</a> مبنيّ على علامات الأمزجة العشرة وعلامات غلبة الأخلاط، ومصادره كلها في <a href="/mizaj/sources/">صفحة المصادر</a>. ولا يُرسل الاختبار شيئاً من إجاباتك إلى أي خادم؛ الحساب كله في متصفحك.</p>
<h2>التواصل</h2><p>البريد: <a href="mailto:{CFG['email']}">{CFG['email']}</a> · <a href="{CFG['social']['x']}">إكس</a> · <a href="{CFG['social']['tiktok']}">تيك توك</a></p>
</div></div>"""
    write("about/index.html", page("عن الموقع", f"عن موقع {CFG['name']} ومنهج بحوثه ومصادره.", "/about/", body, "/about/"))


def build_404():
    body = '<div class="wrap article"><h1>الصفحة غير موجودة</h1><p>لعلّ الرابط تغيّر. <a href="/">ارجع إلى الرئيسية</a> أو جرّب <a href="/mizaj/">اختبار المزاج</a>.</p></div>'
    write("404.html", page("الصفحة غير موجودة", "الصفحة المطلوبة غير موجودة.", "/404.html", body).replace("<head>", '<head><meta name="robots" content="noindex">', 1))


def build_meta(urls, research):
    sm = "".join(f"<url><loc>{DOMAIN}{u}</loc><lastmod>{lm}</lastmod></url>" for u, lm in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    write("CNAME", DOMAIN.split("//")[1] + "\n")
    write(".nojekyll", "")
    write("site.webmanifest", json.dumps({"name": CFG["name"], "short_name": CFG["name"], "lang": "ar", "dir": "rtl", "start_url": "/",
          "display": "standalone", "background_color": "#f7f3ea", "theme_color": "#7a4b1f",
          "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                    {"src": "/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, ensure_ascii=False))
    items = "".join(f"<item><title>{ESC(m['title'])}</title><link>{DOMAIN}/research/{m['slug']}/</link><guid>{DOMAIN}/research/{m['slug']}/</guid>"
                    f"<pubDate>{date.fromisoformat(m['date']).strftime('%a, %d %b %Y')} 00:00:00 +0300</pubDate><description>{ESC(m['summary'])}</description></item>"
                    for m in research[:30])
    write("feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{ESC(CFG["name"])}</title><link>{DOMAIN}/</link>'
          f'<description>{ESC(CFG["description"])}</description><language>ar</language>{items}</channel></rss>')


def main():
    if OUT.exists():
        for p in OUT.iterdir():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "static", OUT / "static", ignore=shutil.ignore_patterns("icons"))
    for f in (SRC / "static" / "icons").glob("*"):
        shutil.copy2(f, OUT / f.name)
    cats = {c["slug"]: c for c in CFG["categories"]}
    research = load_research()
    for m in research:
        if m["category"] not in cats:
            raise SystemExit(f"{m['slug']}: تصنيف غير معروف {m['category']}")
    last = max([m["updated"] for m in research], default=TODAY)
    urls = [("/", last), ("/mizaj/", TODAY), ("/mizaj/sources/", TODAY), ("/about/", TODAY)]
    build_home(research, cats)
    build_categories(research)
    urls += [(f"/category/{c['slug']}/", last) for c in CFG["categories"]]
    build_mizaj(research)
    build_about()
    build_404()
    for m in research:
        urls.append((build_research(m, cats), m["updated"]))
    build_meta(urls, research)
    print(f"بُني الموقع: {len(research)} بحثاً، {len(urls)} رابطاً في خريطة الموقع → {OUT}")


if __name__ == "__main__":
    main()
