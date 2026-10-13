/* =========================================================================
   التراث الطبي — منطق الواجهة
   لا يحتاج أي مكتبات خارجية.
   ========================================================================= */
(function () {
  'use strict';

  /* ----------------------------- عناصر الصفحة ---------------------------- */
  var el = {
    grid:        document.getElementById('grid'),
    empty:       document.getElementById('empty'),
    chips:       document.getElementById('chips'),
    search:      document.getElementById('search'),
    searchClear: document.getElementById('searchClear'),
    typeFilter:  document.getElementById('typeFilter'),
    sort:        document.getElementById('sort'),
    count:       document.getElementById('count'),
    resetAll:    document.getElementById('resetAll'),
    toolbar:     document.getElementById('toolbar'),
    themeToggle: document.getElementById('themeToggle'),
    statTotal:   document.getElementById('statTotal'),
    statCats:    document.getElementById('statCats'),
    statFeat:    document.getElementById('statFeat'),
    year:        document.getElementById('year'),
    modal:       document.getElementById('modal'),
    modalBody:   document.getElementById('modalBody'),
    modalTitle:  document.getElementById('modalTitle'),
    modalKicker: document.getElementById('modalKicker'),
    modalUrl:    document.getElementById('modalUrl'),
    modalOpen:   document.getElementById('modalOpen'),
    modalFrame:  document.getElementById('modalFrame'),
    modalLoader: document.getElementById('modalLoader'),
    modalNote:   document.getElementById('modalNote'),
    modalClose:  document.getElementById('modalClose'),
    modalHint:   document.getElementById('modalHint'),
    modalHintClose: document.getElementById('modalHintClose')
  };

  var DATA = Array.isArray(window.RESOURCES) ? window.RESOURCES.slice() : [];

  var state = { q: '', cat: '', type: '', sort: 'default' };

  /* ------------------------------ أدوات عامة ----------------------------- */

  // تطبيع الحروف العربية حتى يطابق البحث: الهمزات، التاء المربوطة، الألف المقصورة، التشكيل
  function norm(s) {
    return String(s == null ? '' : s)
      .replace(/[ً-ْٰـ]/g, '')
      .replace(/[آأإا]/g, 'ا')
      .replace(/ى/g, 'ي')
      .replace(/ة/g, 'ه')
      .replace(/ؤ/g, 'و')
      .replace(/ئ/g, 'ي')
      .toLowerCase()
      .trim();
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function host(url) {
    try { return new URL(url).hostname.replace(/^www\./, ''); }
    catch (e) { return ''; }
  }

  function num(n) {
    try { return Number(n).toLocaleString('ar-EG'); } catch (e) { return String(n); }
  }

  /* --------------------------- أيقونات الأنواع --------------------------- */
  var ICONS = {
    'مخطوط':  '<path d="M4 19V5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
    'مكتبة':  '<path d="M4 5h6v14H4zM14 5h6v14h-6z"/><path d="M4 9h6M14 9h6"/>',
    'بحث':    '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
    'مقال':   '<path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    'كتاب':   '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5A2.5 2.5 0 0 0 4 22z"/><path d="M4 19.5h16"/>',
    'ملاحظة': '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 14h7"/>',
    'موسوعة': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14 0 18M12 3c-3 3.5-3 14 0 18"/>',
    'مرئي':   '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M10.5 9.5l4.5 2.5-4.5 2.5z"/>',
    'أرشيف':  '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9M10 13h4"/>'
  };

  function typeIcon(t) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[t] || ICONS['مقال']) + '</svg>';
  }

  /* ------------------------------ التصفية -------------------------------- */
  function haystack(r) {
    if (r._hay) return r._hay;
    r._hay = norm([r.title, r.desc, r.category, r.type, r.note, r.body,
                   (r.tags || []).join(' '), host(r.url)].join(' '));
    return r._hay;
  }

  function matches(r) {
    if (state.cat && r.category !== state.cat) return false;
    if (state.type && r.type !== state.type) return false;
    if (!state.q) return true;
    var terms = state.q.split(/\s+/).filter(Boolean);
    var hay = haystack(r);
    for (var i = 0; i < terms.length; i++) {
      if (hay.indexOf(terms[i]) === -1) return false;
    }
    return true;
  }

  var collator = (function () {
    try { return new Intl.Collator('ar'); } catch (e) { return null; }
  })();

  function cmpText(a, b) {
    return collator ? collator.compare(a || '', b || '') : String(a).localeCompare(String(b));
  }

  function sortList(list) {
    var s = state.sort;
    return list.sort(function (a, b) {
      if (s === 'alpha') return cmpText(a.title, b.title);
      if (s === 'newest') return String(b.added || '').localeCompare(String(a.added || ''));
      if (s === 'category') {
        var c = cmpText(a.category, b.category);
        return c !== 0 ? c : cmpText(a.title, b.title);
      }
      // default: المميّز أولاً ثم الأحدث ثم الأبجدي
      var f = (b.featured ? 1 : 0) - (a.featured ? 1 : 0);
      if (f !== 0) return f;
      var d = String(b.added || '').localeCompare(String(a.added || ''));
      if (d !== 0) return d;
      return cmpText(a.title, b.title);
    });
  }

  /* ------------------------------- البطاقات ------------------------------ */
  function cardHTML(r, i) {
    var h = [];
    h.push('<article class="card" style="animation-delay:' + Math.min(i * 28, 400) + 'ms">');

    h.push('<div class="card-top">');
    h.push('<span class="badge badge-type">' + typeIcon(r.type) + esc(r.type || 'مصدر') + '</span>');
    if (r.category) {
      h.push('<button class="badge badge-cat" type="button" data-cat="' + esc(r.category) + '">' + esc(r.category) + '</button>');
    }
    if (r.featured) {
      h.push('<span class="badge badge-feat" title="مصدر مميّز">★ مميّز</span>');
    }
    h.push('</div>');

    h.push('<h3 class="card-title">' + esc(r.title) + '</h3>');
    if (r.desc) h.push('<p class="card-desc">' + esc(r.desc) + '</p>');
    if (r.note) h.push('<div class="card-note"><strong>ملاحظتي</strong>' + esc(r.note) + '</div>');

    if (r.tags && r.tags.length) {
      h.push('<div class="tags">');
      r.tags.forEach(function (t) {
        h.push('<button class="tag" type="button" data-tag="' + esc(t) + '">#' + esc(t) + '</button>');
      });
      h.push('</div>');
    }

    h.push('<div class="card-foot">');
    h.push('<button class="btn btn-primary" type="button" data-open="' + r._i + '">' +
           '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/></svg>' +
           (r.url ? 'فتح في نافذة' : 'قراءة الملاحظة') + '</button>');
    if (r.url) {
      h.push('<a class="btn btn-ghost" href="' + esc(r.url) + '" target="_blank" rel="noopener noreferrer" title="فتح في تبويب جديد" aria-label="فتح في تبويب جديد">' +
             '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-8.5 8.5"/><path d="M19 14v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg></a>');
      h.push('<span class="card-host">' + esc(host(r.url)) + '</span>');
    }
    h.push('</div>');

    h.push('</article>');
    return h.join('');
  }

  /* -------------------------------- العرض -------------------------------- */
  function render() {
    var list = sortList(DATA.filter(matches));

    el.grid.innerHTML = list.map(cardHTML).join('');
    el.empty.hidden = list.length !== 0;

    var total = DATA.length;
    if (list.length === total) {
      el.count.textContent = 'تُعرض كل المصادر (' + num(total) + ').';
    } else {
      el.count.textContent = 'عرض ' + num(list.length) + ' من ' + num(total) + ' مصدر.';
    }

    el.searchClear.hidden = !state.q;
    Array.prototype.forEach.call(el.chips.children, function (c) {
      c.setAttribute('aria-pressed', String(c.dataset.cat === state.cat));
    });
  }

  /* ------------------------------ بناء الأدوات --------------------------- */
  function buildFilters() {
    var cats = {}, types = {};
    DATA.forEach(function (r) {
      if (r.category) cats[r.category] = (cats[r.category] || 0) + 1;
      if (r.type) types[r.type] = (types[r.type] || 0) + 1;
    });

    var catNames = Object.keys(cats).sort(cmpText);
    var chips = ['<button class="chip" type="button" data-cat="" aria-pressed="true">الكل <b>' + num(DATA.length) + '</b></button>'];
    catNames.forEach(function (c) {
      chips.push('<button class="chip" type="button" data-cat="' + esc(c) + '" aria-pressed="false">' +
                 esc(c) + ' <b>' + num(cats[c]) + '</b></button>');
    });
    el.chips.innerHTML = chips.join('');

    Object.keys(types).sort(cmpText).forEach(function (t) {
      var o = document.createElement('option');
      o.value = t;
      o.textContent = t + ' (' + num(types[t]) + ')';
      el.typeFilter.appendChild(o);
    });

    el.statTotal.textContent = num(DATA.length);
    el.statCats.textContent  = num(catNames.length);
    el.statFeat.textContent  = num(DATA.filter(function (r) { return r.featured; }).length);
  }

  /* ------------------------------- النافذة ------------------------------- */
  var lastFocus = null, hintTimer = null, hintMuted = false;

  function showHint() {
    if (!hintMuted) el.modalHint.hidden = false;
  }

  function openModal(idx) {
    var r = DATA[idx];
    if (!r) return;

    lastFocus = document.activeElement;

    el.modalTitle.textContent  = r.title || '';
    el.modalKicker.textContent = [r.type, r.category].filter(Boolean).join(' · ');

    clearTimeout(hintTimer);
    el.modalHint.hidden = true;

    if (r.url) {
      el.modalBody.classList.remove('is-note');
      el.modalNote.hidden = true;
      el.modalUrl.textContent = r.url;
      el.modalUrl.hidden = false;
      el.modalOpen.href = r.url;
      el.modalOpen.hidden = false;
      el.modalLoader.hidden = false;
      el.modalFrame.src = r.url;
      // لا توجد طريقة موثوقة لكشف منع التضمين من داخل الصفحة،
      // فنُظهر تنبيهاً لطيفاً بعد مهلة حتى لو نجح التحميل.
      hintTimer = setTimeout(function () {
        el.modalLoader.hidden = true;
        showHint();
      }, 5000);
    } else {
      // ملاحظة نصّية بلا رابط
      el.modalBody.classList.add('is-note');
      el.modalFrame.removeAttribute('src');
      el.modalLoader.hidden = true;
      el.modalUrl.hidden = true;
      el.modalOpen.hidden = true;
      var parts = String(r.body || r.desc || '').split(/\n+/).filter(Boolean);
      el.modalNote.innerHTML =
        (r.desc && r.body ? '<h3>' + esc(r.desc) + '</h3>' : '') +
        parts.map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('');
      el.modalNote.hidden = false;
    }

    el.modal.hidden = false;
    document.body.classList.add('no-scroll');
    el.modalClose.focus({ preventScroll: true });
  }

  function closeModal() {
    clearTimeout(hintTimer);
    el.modal.hidden = true;
    el.modalFrame.removeAttribute('src');
    el.modalNote.innerHTML = '';
    document.body.classList.remove('no-scroll');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  el.modalFrame.addEventListener('load', function () {
    if (!el.modalFrame.getAttribute('src')) return;
    clearTimeout(hintTimer);
    el.modalLoader.hidden = true;
    hintTimer = setTimeout(showHint, 1400);
  });

  el.modalHintClose.addEventListener('click', function () {
    hintMuted = true;
    el.modalHint.hidden = true;
  });

  // حصر التركيز داخل النافذة ما دامت مفتوحة
  el.modal.addEventListener('keydown', function (e) {
    if (e.key !== 'Tab') return;
    var f = el.modal.querySelectorAll('a[href]:not([hidden]), button:not([hidden]):not([disabled]), iframe');
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ------------------------------- الأحداث ------------------------------- */
  var tDebounce;
  el.search.addEventListener('input', function () {
    clearTimeout(tDebounce);
    tDebounce = setTimeout(function () { state.q = norm(el.search.value); render(); }, 130);
  });

  el.searchClear.addEventListener('click', function () {
    el.search.value = ''; state.q = ''; render(); el.search.focus();
  });

  el.chips.addEventListener('click', function (e) {
    var b = e.target.closest('[data-cat]');
    if (!b) return;
    state.cat = b.dataset.cat;
    render();
  });

  el.typeFilter.addEventListener('change', function () { state.type = el.typeFilter.value; render(); });
  el.sort.addEventListener('change', function () { state.sort = el.sort.value; render(); });

  el.grid.addEventListener('click', function (e) {
    var open = e.target.closest('[data-open]');
    if (open) { openModal(Number(open.dataset.open)); return; }

    var tag = e.target.closest('[data-tag]');
    if (tag) {
      el.search.value = tag.dataset.tag;
      state.q = norm(tag.dataset.tag);
      state.cat = ''; state.type = ''; el.typeFilter.value = '';
      render();
      el.toolbar.scrollIntoView({ block: 'start' });
      return;
    }

    var cat = e.target.closest('[data-cat]');
    if (cat) {
      state.cat = cat.dataset.cat;
      render();
      el.toolbar.scrollIntoView({ block: 'start' });
    }
  });

  function resetAll() {
    state = { q: '', cat: '', type: '', sort: 'default' };
    el.search.value = ''; el.typeFilter.value = ''; el.sort.value = 'default';
    render();
  }
  el.resetAll.addEventListener('click', resetAll);

  el.modal.addEventListener('click', function (e) {
    if (e.target.closest('[data-close]')) closeModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !el.modal.hidden) { closeModal(); return; }
    // "/" لتركيز البحث
    if (e.key === '/' && document.activeElement !== el.search && el.modal.hidden) {
      e.preventDefault(); el.search.focus(); el.search.select();
    }
  });

  /* -------------------------------- السمة -------------------------------- */
  el.themeToggle.addEventListener('click', function () {
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('turath-theme', next); } catch (e) {}
  });

  /* ------------------------- ظل الشريط عند التمرير ----------------------- */
  if ('IntersectionObserver' in window) {
    var sentinel = document.createElement('div');
    sentinel.style.cssText = 'position:absolute;top:0;height:1px;width:1px';
    document.body.prepend(sentinel);
    new IntersectionObserver(function (entries) {
      el.toolbar.classList.toggle('is-stuck', !entries[0].isIntersecting);
    }).observe(sentinel);
  }

  /* ------------------------------- التشغيل ------------------------------- */
  DATA.forEach(function (r, i) { r._i = i; });
  el.year.textContent = new Date().getFullYear();
  buildFilters();
  render();

  if (!DATA.length) {
    el.grid.innerHTML =
      '<article class="card"><h3 class="card-title">لا توجد مصادر بعد</h3>' +
      '<p class="card-desc">أضف مصادرك في الملف <code>data/resources.js</code> لتظهر هنا.</p></article>';
    el.empty.hidden = true;
  }
})();
