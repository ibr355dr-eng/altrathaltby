# التراث الطبي — altrathaltby.com

موقع ثابت يُبنى بـ `python3 build.py` من مجلد `site/` إلى `docs/`، وتنشره GitHub Pages من `docs/` في الفرع `main`.

## البنية

| المسار | المحتوى |
|---|---|
| `site/config.json` | اسم الموقع، والنطاق، والمؤلف، وأقسام البحوث |
| `site/research/<slug>/` | بحث منشور: `meta.json` و`index.html` وما معه من صور وملفات |
| `site/mizaj/questions.json` | أسئلة اختبار المزاج ونقاط كل جواب |
| `site/mizaj/sources.json` | نصوص المصادر (القانون ج١، الموجز) بأرقام الصفحات |
| `site/static/` | التنسيق، وكود الاختبار، والأيقونات (`tools/make_icons.py`) |

## نشر بحث

1. أنشئ `site/research/<slug>/meta.json`:

```json
{
  "title": "إنضاج السوداء عند ابن سينا",
  "category": "akhlat",
  "summary": "سطران يظهران في البطاقة ونتائج البحث.",
  "date": "2026-11-05",
  "keywords": ["السوداء", "الإنضاج", "ابن سينا"],
  "mode": "standalone",
  "access": "free"
}
```

- `category`: أحد الأقسام في `config.json`.
- `mode`: `body` إذا كان `index.html` جزءاً يوضع في قالب الموقع، و`standalone` إذا كان صفحة كاملة بتصميمها.
- `access`: `free` أو `paid`. في المدفوع لا يُنشر إلا ما قبل `<!--more-->`، ومعه زر الدفع (`pay_url`).
- `draft: true` يمنع نشره.

2. `python3 build.py`، ثم `git add -A && git commit -m "نشر: …" && git push`.

خريطة الموقع وRSS والبطاقات والأقسام تتحدث تلقائياً.

## النطاق

سجلات Namecheap (Advanced DNS): أربعة سجلات A لـ `@` إلى `185.199.108.153` و`.109` و`.110` و`.111`، وCNAME لـ `www` إلى `ibr355dr-eng.github.io.`.

## معاينة محلية

```bash
python3 build.py && cd docs && python3 -m http.server 8080
```
