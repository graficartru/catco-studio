/* ============================================================
   CatCo Studio — логика сайта
   Данные рендерятся из data.json; three.js-сцена в hero.
   ============================================================ */
(function () {
  'use strict';

  let DATA = null;

  /* ---------- загрузка data.json (fetch + резервныйXHR для file://) ---------- */
  function loadData() {
    // Publii / статический хостинг: данные уже вшиты в страницу
    if (window.CATCO_DATA) {
      return Promise.resolve(window.CATCO_DATA);
    }
    const inline = document.getElementById('catco-data');
    if (inline) {
      try { return Promise.resolve(JSON.parse(inline.textContent)); } catch (e) {}
    }
    return fetch('/data.json')
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .catch(() => new Promise((res, rej) => {
        const x = new XMLHttpRequest();
        x.open('GET', '/data.json', true);
        x.onload = () => { try { res(JSON.parse(x.responseText)); } catch (e) { rej(e); } };
        x.onerror = rej;
        x.send();
      }));
  }

  function normalizePaths(node) {
    const abs = v => (typeof v === 'string' && /^(?!\/|https?:|data:|mailto:|tel:)[a-z0-9_-]/i.test(v))
      ? '/' + v : v;
    if (Array.isArray(node)) { node.forEach(normalizePaths); return node; }
    if (node && typeof node === 'object') {
      for (const k of Object.keys(node)) {
        if (/^(src|img|image|cover|avatar|thumb)$/i.test(k)) node[k] = abs(node[k]);
        else normalizePaths(node[k]);
      }
    }
    return node;
  }

  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html !== undefined) n.innerHTML = html;
    return n;
  };

  /* ============================================================
     HERO: фоновый слайдер из 3 слайдов + параллакс
     ============================================================ */
  function initHeroSlider(slides) {
    const bg = $('#heroBg'), dots = $('#heroDots');
    slides.forEach((s, i) => {
      const d = el('div', 'hero-slide' + (i === 0 ? ' active' : ''));
      d.style.backgroundImage = `url("${s.src}")`;
      bg.appendChild(d);
      const b = el('button', i === 0 ? 'active' : '');
      b.setAttribute('aria-label', 'Слайд ' + (i + 1));
      b.addEventListener('click', () => go(i));
      dots.appendChild(b);
    });
    let cur = 0, timer;
    function go(i) {
      const items = $$('.hero-slide'), ds = dots.children;
      items[cur].classList.remove('active'); ds[cur].classList.remove('active');
      // перезапуск ken-burns
      void items[i].offsetWidth;
      cur = (i + items.length) % items.length;
      items[cur].classList.add('active'); ds[cur].classList.add('active');
      restart();
    }
    function next() { go(cur + 1); }
    function restart() { clearInterval(timer); timer = setInterval(next, 6500); }
    restart();
  }

  /* параллакс hero при движении курсора */
  function initParallax() {
    const copy = $('.hero-copy'), wrap = $('#hero-canvas-wrap'), bg = $('#heroBg');
    if (!copy) return;
    let tx = 0, ty = 0, cx = 0, cy = 0;
    window.addEventListener('mousemove', e => {
      tx = (e.clientX / innerWidth - .5);
      ty = (e.clientY / innerHeight - .5);
    }, { passive: true });
    (function raf() {
      cx += (tx - cx) * .06; cy += (ty - cy) * .06;
      copy.style.transform = `translate(${cx * -14}px, ${cy * -10}px)`;
      if (bg) bg.style.transform = `translate(${cx * 22}px, ${cy * 16}px)`;
      if (wrap && wrap.firstElementChild && wrap.firstElementChild.tagName === 'CANVAS') {
        // three.js сцена сама реагирует на мышь
      }
      requestAnimationFrame(raf);
    })();
  }

  /* ============================================================
     HERO: three.js — вращающаяся hardsurface/sci-fi композиция
     ============================================================ */
  function initThreeScene() {
    const holder = $('#hero-canvas-wrap');
    if (!holder || typeof THREE === 'undefined') return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, holder.clientWidth / holder.clientHeight, .1, 100);
    camera.position.set(0, 1.2, 9);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(holder.clientWidth, holder.clientHeight);
    holder.prepend(renderer.domElement);

    // свет
    scene.add(new THREE.AmbientLight(0x334455, 1.1));
    const key = new THREE.DirectionalLight(0xffa85c, 1.6); key.position.set(5, 8, 6); scene.add(key);
    const rim = new THREE.PointLight(0x3d7bff, 1.4, 40); rim.position.set(-6, -3, -4); scene.add(rim);
    const accentL = new THREE.PointLight(0xff6a00, 2.2, 25); accentL.position.set(3, -2, 4); scene.add(accentL);

    const group = new THREE.Group(); scene.add(group);

    const metal = new THREE.MeshStandardMaterial({ color: 0x8fa2c8, metalness: .9, roughness: .28 });
    const dark = new THREE.MeshStandardMaterial({ color: 0x232838, metalness: .8, roughness: .45 });
    const acc = new THREE.MeshStandardMaterial({ color: 0xff6a00, metalness: .5, roughness: .3, emissive: 0xff3c00, emissiveIntensity: .35 });
    const wireMat = new THREE.LineBasicMaterial({ color: 0x6f8fc8, transparent: true, opacity: .55 });

    // ядро — додекаэдр «hard surface»
    const coreGeo = new THREE.DodecahedronGeometry(1.5, 0);
    const core = new THREE.Mesh(coreGeo, metal); group.add(core);
    const coreEdges = new THREE.LineSegments(new THREE.EdgesGeometry(coreGeo), new THREE.LineBasicMaterial({ color: 0xffb35c, transparent: true, opacity: .8 }));
    core.add(coreEdges);

    // внутренний светящийся узел
    const spark = new THREE.Mesh(new THREE.IcosahedronGeometry(.6, 0), acc); group.add(spark);

    // внешняя проволочная сфера-орбита
    const cage = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(3.1, 12, 8)), wireMat);
    group.add(cage);

    // кольца-торусы
    const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.6, .05, 10, 90), dark);
    ring1.rotation.x = Math.PI / 2.4; group.add(ring1);
    const ring2 = new THREE.Mesh(new THREE.TorusGeometry(3.4, .03, 10, 90), metal);
    ring2.rotation.x = -Math.PI / 3; ring2.rotation.y = .6; group.add(ring2);

    // спутники — технические детали
    const satGeos = [new THREE.BoxGeometry(.34, .34, .9), new THREE.CylinderGeometry(.18, .18, .7, 6), new THREE.OctahedronGeometry(.3)];
    const sats = [];
    for (let i = 0; i < 7; i++) {
      const m = new THREE.Mesh(satGeos[i % 3], i % 3 === 0 ? acc : metal);
      const orbitR = 2.6 + (i % 3) * .45, ang = i * (Math.PI * 2 / 7), y = Math.sin(i * 2.1) * 1.1;
      m.userData = { orbitR, ang, y, speed: .18 + (i % 4) * .07 };
      group.add(m); sats.push(m);
    }

    // частицы-звёзды вокруг
    const pGeo = new THREE.BufferGeometry();
    const N = 260, pos = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      const r = 4 + Math.random() * 5, t = Math.random() * Math.PI * 2, p = Math.acos(2 * Math.random() - 1);
      pos[i * 3] = r * Math.sin(p) * Math.cos(t);
      pos[i * 3 + 1] = r * Math.cos(p) * .6;
      pos[i * 3 + 2] = r * Math.sin(p) * Math.sin(t);
    }
    pGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pts = new THREE.Points(pGeo, new THREE.PointsMaterial({ color: 0x9db4dd, size: .035, transparent: true, opacity: .7 }));
    scene.add(pts);

    // реакция на курсор (наклон группы)
    let mx = 0, my = 0, tmx = 0, tmy = 0;
    window.addEventListener('mousemove', e => {
      tmx = (e.clientX / innerWidth - .5); tmy = (e.clientY / innerHeight - .5);
    }, { passive: true });

    const clock = new THREE.Clock();
    (function animate() {
      requestAnimationFrame(animate);
      const dt = clock.getDelta(), t = clock.elapsedTime;
      mx += (tmx - mx) * .05; my += (tmy - my) * .05;
      group.rotation.y = t * .12 + mx * .8;
      group.rotation.x = my * .5 + Math.sin(t * .3) * .06;
      core.rotation.z = t * .18; spark.rotation.y = -t * .9;
      cage.rotation.y = -t * .05;
      ring1.rotation.z = t * .22; ring2.rotation.z = -t * .16;
      sats.forEach(s => {
        s.userData.ang += dt * s.userData.speed;
        s.position.set(Math.cos(s.userData.ang) * s.userData.orbitR, s.userData.y + Math.sin(t + s.userData.ang) * .18, Math.sin(s.userData.ang) * s.userData.orbitR);
        s.rotation.x += dt; s.rotation.y += dt * .7;
      });
      pts.rotation.y = t * .02;
      camera.position.x = mx * .9; camera.position.y = 1.2 - my * .7;
      camera.lookAt(0, .3, 0);
      renderer.render(scene, camera);
    })();

    window.addEventListener('resize', () => {
      if (!holder.clientWidth) return;
      camera.aspect = holder.clientWidth / holder.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(holder.clientWidth, holder.clientHeight);
    });
  }

  /* ============================================================
     Услуги: flip-карточки
     ============================================================ */
  function renderServices(items) {
    const grid = $('#servicesGrid');
    items.forEach((s, i) => {
      const card = el('article', 'flip-card reveal d' + ((i % 4) + 1));
      card.tabIndex = 0;
      card.innerHTML = `
        <div class="flip-inner">
          <div class="flip-face flip-front">
            <img src="${s.img}" alt="Иллюстрация услуги «${s.title}»" loading="lazy">
            <span class="svc-num">${s.num}</span>
            <span class="svc-hover-hint"><span>${s.title.split(' ')[0]}</span><span>наведите →</span></span>
          </div>
          <div class="flip-face flip-back">
            <h3><em>${s.num}.</em> ${s.title}</h3>
            <p>${s.desc}</p>
            <a class="more" href="#portfolio" data-goto-cat="${catForService(s.num)}">Подробнее ↗</a>
          </div>
        </div>`;
      grid.appendChild(card);
    });
    grid.querySelectorAll('.more').forEach(a => a.addEventListener('click', () => {
      const cat = a.dataset.gotoCat;
      if (cat) setTimeout(() => setFilter(cat), 400);
    }));
    function catForService(num) {
      return { '01': 'modeling', '02': 'graphics', '03': 'vector', '04': 'print' }[num] || 'all';
    }
  }

  /* ============================================================
     Портфолио: masonry-галерея + фильтры + модалка
     ============================================================ */
  let PROJECTS = [];
  function renderPortfolio(filters, projects) {
    PROJECTS = projects;
    const fWrap = $('#filters'), g = $('#gallery');
    filters.forEach((f, i) => {
      const b = el('button', 'filter-btn' + (i === 0 ? ' active' : ''), f.label);
      b.dataset.cat = f.id;
      b.addEventListener('click', () => setFilter(f.id));
      fWrap.appendChild(b);
    });
    projects.forEach(p => {
      const w = el('figure', 'work reveal');
      w.dataset.cat = p.category;
      w.innerHTML = `
        <img src="${p.cover}" alt="${p.title} — ${p.categoryLabel}" loading="lazy">
        <span class="work-open">↗</span>
        <figcaption class="work-meta">
          <span class="cat">${p.categoryLabel} · ${p.year}</span>
          <h3>${p.title}</h3>
          <span class="work-tags">${p.tags.map(t => `<span>${t}</span>`).join('')}</span>
        </figcaption>`;
      w.addEventListener('click', () => openProject(p));
      g.appendChild(w);
    });
  }
  function setFilter(cat) {
    $$('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
    $$('.work').forEach(w => w.classList.toggle('hidden-item', cat !== 'all' && w.dataset.cat !== cat));
  }

  /* --- модалка проекта + вертикальный слайдер before/after --- */
  function openProject(p) {
    const modal = $('#projectModal'), content = $('#modalContent');
    let compareHTML = '';
    if (p.compare) {
      compareHTML = `
        <div class="vslider" id="vslider">
          <div class="vslide-img vslide-after"><img src="${p.compare.after}" alt="${p.compare.afterLabel}"></div>
          <div class="vslide-img vslide-before" id="vBefore"><img src="${p.compare.before}" alt="${p.compare.beforeLabel}"></div>
          <div class="vslider-line" id="vLine"></div>
          <span class="vlabel top">${p.compare.beforeLabel}</span>
          <span class="vlabel bottom">${p.compare.afterLabel}</span>
        </div>
        <p class="vhint">Потяните ползунок вверх или вниз, чтобы сравнить этапы разработки.</p>`;
    } else {
      compareHTML = `<img src="${p.cover}" alt="${p.title}" style="width:100%;border-radius:var(--radius-l);border:1px solid var(--line)">`;
    }
    content.innerHTML = `
      <div class="modal-head">
        <span class="cat">${p.categoryLabel} · ${p.year}</span>
        <h3>${p.title}</h3>
        <div class="work-tags">${p.tags.map(t => `<span>${t}</span>`).join('')}</div>
      </div>
      <div class="modal-body">
        <div>
          ${compareHTML}
          <div class="modal-gallery">
            ${p.gallery.map(gl => `<figure><img src="${gl.src}" alt="${gl.caption}" loading="lazy"><figcaption>${gl.caption}</figcaption></figure>`).join('')}
          </div>
        </div>
        <div class="modal-info">
          <h4>Задача</h4><p>${p.task}</p>
          <h4>Процесс разработки</h4>
          <ol>${p.process.map(s => `<li>${s}</li>`).join('')}</ol>
          <h4>Результат</h4><p>${p.result}</p>
          <div style="margin-top:30px"><a href="#order" class="btn btn-primary" id="modalOrder">Хочу такой же проект</a></div>
        </div>
      </div>`;
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    initVSlider();
    $('#modalOrder').addEventListener('click', () => closeModal());
  }
  function closeModal() {
    $('#projectModal').classList.remove('open');
    document.body.style.overflow = '';
  }
  function initVSlider() {
    const slider = $('#vslider'); if (!slider) return;
    const before = $('#vBefore'), line = $('#vLine');
    let dragging = false;
    function setY(clientY) {
      const r = slider.getBoundingClientRect();
      let pct = ((clientY - r.top) / r.height) * 100;
      pct = Math.max(4, Math.min(96, pct));
      before.style.clipPath = `inset(0 0 ${100 - pct}% 0)`;
      line.style.top = pct + '%';
    }
    slider.addEventListener('pointerdown', e => { dragging = true; slider.setPointerCapture(e.pointerId); setY(e.clientY); });
    slider.addEventListener('pointermove', e => { if (dragging) setY(e.clientY); });
    ['pointerup', 'pointercancel'].forEach(ev => slider.addEventListener(ev, () => dragging = false));
  }

  /* ============================================================
     Процесс / Почему мы / Форматы
     ============================================================ */
  function renderProcess(items) {
    const t = $('#processTrack');
    items.forEach((s, i) => {
      const n = el('div', 'step reveal d' + (i + 1));
      n.innerHTML = `<span class="step-num">${s.num}</span><div class="step-dot"></div><h3>${s.title}</h3><p>${s.desc}</p>`;
      t.appendChild(n);
    });
  }
  function renderWhy(items) {
    const g = $('#whyGrid');
    items.forEach((w, i) => {
      const n = el('div', 'why-card reveal d' + ((i % 4) + 1));
      n.innerHTML = `<span class="idx">${String(i + 1).padStart(2, '0')}</span><h3>${w.title}</h3><p>${w.desc}</p>`;
      g.appendChild(n);
    });
  }
  function renderFormats(groups, note) {
    const w = $('#formatsWrap');
    groups.forEach((gr, i) => {
      const n = el('div', 'format-group reveal d' + (i + 1));
      n.innerHTML = `<h3><i></i>${gr.group}</h3><div class="chips">${gr.items.map(f => `<span class="chip">${f}</span>`).join('')}</div>`;
      w.appendChild(n);
    });
    $('#formatsNote').textContent = note;
  }

  /* ============================================================
     Отзывы: слайдер со стрелками сверху и точками снизу
     ============================================================ */
  function renderTestimonials(items) {
    const track = $('#tTrack'), dots = $('#tDots');
    items.forEach(t => {
      const s = el('div', 't-slide');
      s.innerHTML = `<div class="t-card">
        <div class="t-avatar"><img src="${t.avatar}" alt="Фото заказчика: ${t.name}" loading="lazy"></div>
        <div><p class="t-quote">${t.text}</p><div class="t-name">${t.name}</div><div class="t-role">${t.role}</div></div>
      </div>`;
      track.appendChild(s);
    });
    items.forEach((_, i) => {
      const d = el('button', 't-dot' + (i === 0 ? ' active' : ''));
      d.setAttribute('aria-label', 'Отзыв ' + (i + 1));
      d.addEventListener('click', () => go(i));
      dots.appendChild(d);
    });
    let cur = 0, auto;
    function go(i) {
      cur = (i + items.length) % items.length;
      track.style.transform = `translateX(-${cur * 100}%)`;
      Array.from(dots.children).forEach((d, k) => d.classList.toggle('active', k === cur));
      restartAuto();
    }
    function restartAuto() { clearInterval(auto); auto = setInterval(() => go(cur + 1), 7000); }
    $('#tPrev').addEventListener('click', () => go(cur - 1));
    $('#tNext').addEventListener('click', () => go(cur + 1));
    // свайп
    let sx = null;
    track.addEventListener('touchstart', e => sx = e.touches[0].clientX, { passive: true });
    track.addEventListener('touchend', e => {
      if (sx === null) return;
      const dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 45) go(cur + (dx < 0 ? 1 : -1));
      sx = null;
    });
    restartAuto();
  }

  /* ============================================================
     Форма заявки: валидация + честный статус отправки
     ============================================================ */
  function initForm(formCfg, serviceOptions) {
    const sel = $('#fService');
    serviceOptions.forEach(o => { const op = el('option', '', o); op.value = o; sel.appendChild(op); });

    // файлы
    const dz = $('#dropzone'), input = $('#fFiles'), list = $('#fileList');
    let files = [];
    dz.addEventListener('click', () => input.click());
    dz.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') input.click(); });
    input.addEventListener('change', () => addFiles(input.files));
    ['dragover', 'dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => {
      e.preventDefault(); dz.classList.toggle('dragover', ev === 'dragover');
      if (ev === 'drop') addFiles(e.dataTransfer.files);
    }));
    function addFiles(fl) {
      for (const f of fl) {
        if (files.length >= 5) { status('warn', 'Можно прикрепить не больше 5 файлов — лишние пропущены.'); break; }
        if (f.size > 15 * 1024 * 1024) { status('warn', `Файл «${f.name}» больше 15 МБ и не добавлен.`); continue; }
        files.push(f);
      }
      drawFiles();
    }
    function drawFiles() {
      list.innerHTML = '';
      files.forEach((f, i) => {
        const tag = el('span', 'file-tag', `${f.name} <small>(${(f.size / 1024).toFixed(0)} КБ)</small>`);
        const x = el('button', '', '✕'); x.type = 'button'; x.setAttribute('aria-label', 'Убрать файл');
        x.addEventListener('click', () => { files.splice(i, 1); drawFiles(); });
        tag.appendChild(x); list.appendChild(tag);
      });
    }

    // валидация
    const rules = {
      fName: v => v.trim().length >= 2 || 'Укажите имя (минимум 2 символа).',
      fContact: v => /^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(v.trim()) || /^@[a-z0-9_.\-]{3,}$/i.test(v.trim()) || 'Нужен корректный email или ник в мессенджере (например @nickname).',
      fPhone: v => (v.match(/\d/g) || []).length >= 10 || 'Телефон должен содержать минимум 10 цифр.',
      fService: v => !!v || 'Выберите тип услуги.',
      fDesc: v => v.trim().length >= 10 || 'Опишите задачу подробнее (от 10 символов).'
    };
    function validateField(id) {
      const node = document.getElementById(id), wrap = node.closest('.field');
      const res = rules[id](node.value);
      const msg = wrap.querySelector('.err-msg');
      wrap.classList.toggle('invalid', res !== true);
      msg.textContent = res === true ? '' : res;
      return res === true;
    }
    Object.keys(rules).forEach(id => {
      const n = document.getElementById(id);
      n.addEventListener('blur', () => validateField(id));
      n.addEventListener('input', () => { if (n.closest('.field').classList.contains('invalid')) validateField(id); });
    });

    function status(type, text) {
      const s = $('#formStatus');
      s.className = 'form-status show ' + type;
      s.innerHTML = text;
    }

    $('#orderForm').addEventListener('submit', e => {
      e.preventDefault();
      const ok = Object.keys(rules).map(validateField).every(Boolean);
      if (!ok) {
        status('err', 'Проверьте выделенные поля — форма пока не отправлена.');
        const bad = $('.field.invalid');
        if (bad) bad.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }
      const payload = {
        name: $('#fName').value.trim(),
        contact: $('#fContact').value.trim(),
        phone: $('#fPhone').value.trim(),
        service: $('#fService').value,
        description: $('#fDesc').value.trim(),
        deadline: $('#fDeadline').value.trim(),
        files: files.map(f => f.name),
        createdAt: new Date().toISOString()
      };

      if (formCfg.backendConfigured && formCfg.endpoint) {
        // реальная отправка на подключённый backend/сервис форм
        const fd = new FormData();
        Object.entries(payload).forEach(([k, v]) => fd.append(k, v));
        files.forEach(f => fd.append('attachments', f));
        status('warn', 'Отправляем заявку…');
        fetch(formCfg.endpoint, { method: 'POST', body: fd })
          .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            status('ok', 'Заявка отправлена. Мы свяжемся с вами в ближайшее время.');
            reset();
          })
          .catch(() => status('err', 'Не удалось отправить заявку. Попробуйте позже или напишите нам на почту.'));
      } else {
        // backend НЕ настроен — честно сохраняем черновик локально
        try { localStorage.setItem('catco_draft', JSON.stringify(payload)); } catch (err) { /* ignore */ }
        status('warn',
          '⚠ Backend для приёма заявок ещё не подключён — реальная отправка не выполнена.<br>' +
          'Черновик заявки сохранён локально в браузере. Чтобы связаться с нами прямо сейчас, напишите на ' +
          '<a href="mailto:hello@catcostudio.design" style="color:#ffd08a;text-decoration:underline">hello@catcostudio.design</a>.');
      }
      function reset() {
        $('#orderForm').reset(); files = []; drawFiles();
        $$('.field').forEach(f => f.classList.remove('invalid'));
        $$('.err-msg').forEach(m => m.textContent = '');
      }
    });
  }

  /* ============================================================
     Разное: nav, reveal, футер, политика
     ============================================================ */
  function initNav() {
    const nav = $('#nav');
    addEventListener('scroll', () => nav.classList.toggle('scrolled', scrollY > 40), { passive: true });
    $('#burger').addEventListener('click', () => $('#navLinks').classList.toggle('open'));
    $$('#navLinks a').forEach(a => a.addEventListener('click', () => $('#navLinks').classList.remove('open')));
    // плавный якорь для кнопки "Смотреть работы"
    const tw = $('#toWorks');
    if (tw) tw.addEventListener('click', e => {
      e.preventDefault();
      $('#portfolio').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
  function initReveal() {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('visible'); io.unobserve(en.target); } });
    }, { threshold: .12 });
    setTimeout(() => $$('.reveal:not(.visible)').forEach(n => io.observe(n)), 50);
  }
  function initFooter(studio) {
    $('#year').textContent = new Date().getFullYear();
    $('#footerDesc').textContent = studio.description;
    const em = $('#footerEmail'); em.textContent = studio.email; em.href = 'mailto:' + studio.email;
    const ph = $('#footerPhone'); ph.textContent = studio.phone;
    const sl = $('#socialList');
    studio.social.forEach(s => {
      const li = el('li', '', `<a href="${s.url}" target="_blank" rel="noopener noreferrer">${s.label} ↗</a>`);
      sl.appendChild(li);
    });
    // политика
    const pp = $('#ppModal');
    $$('.pp-link').forEach(a => a.addEventListener('click', e => { e.preventDefault(); pp.classList.add('open'); }));
    $('#ppClose').addEventListener('click', () => pp.classList.remove('open'));
    pp.addEventListener('click', e => { if (e.target === pp) pp.classList.remove('open'); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') { pp.classList.remove('open'); closeModal(); }
    });
    $('#modalClose').addEventListener('click', closeModal);
    $('#projectModal').addEventListener('click', e => { if (e.target.id === 'projectModal') closeModal(); });
  }

  /* ============================================================
     Старт
     ============================================================ */
  loadData().then(data => {
    data = normalizePaths(data);
    DATA = data;
    // hero-тексты из json (синхронизируем с разметкой)
    $('#heroTitle').innerHTML = data.hero.title.replace('в цифровую форму', 'в<br><span class="grad">цифровую форму</span>');
    $('#heroSub').textContent = data.hero.subtitle;
    document.title = `${DATA.studio.name} — ${DATA.studio.tagline} · 3D-моделирование, графика, 3D-печать`;

    initHeroSlider(data.hero.slides);
    renderServices(data.services);
    renderPortfolio(data.portfolioFilters, data.projects);
    renderProcess(data.process);
    renderWhy(data.whyUs);
    renderFormats(data.formats, data.formatsNote);
    renderTestimonials(data.testimonials);
    initForm(data.form, data.serviceOptions);
    initFooter(data.studio);
    initNav();
    initParallax();
    initThreeScene();
    initReveal();
  }).catch(err => {
    console.error('Не удалось загрузить data.json:', err);
    // сайт остаётся читабельным: показываем нативный контент hero
    const st = $('#formStatus');
    if (st) { st.className = 'form-status show err'; st.textContent = 'Не удалось загрузить данные страницы (data.json). Откройте сайт через локальный сервер, например: python3 -m http.server.'; }
  });
})();
