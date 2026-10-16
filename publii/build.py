#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Подготовка сайта CatCo Studio к экспорту в Publii.

Publii отдаёт файлы с абсолютными путями (/css/..., /js/..., /assets/...),
поэтому относительные пути нужно сделать корневыми, а данные data.json
встроить прямо в HTML (иначе fetch() упрётся в MIME-тип application/json,
который Publii не отдаёт для .json).
"""
import json
import os
import re
import io
import shutil
import tarfile
import zipfile
from time import mktime

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site')
OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
PKG = os.path.join(OUT_ROOT, 'catco-studio-publii')

# ---------------------------------------------------------------- распаковка
if os.path.exists(SRC):
    shutil.rmtree(SRC)
os.makedirs(SRC)
with zipfile.ZipFile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '..', 'catco-studio.zip')) as zf:
    zf.extractall(SRC)

# ------------------------------------------------- 1. data.json -> window.DATA
with open(os.path.join(SRC, 'data.json'), encoding='utf-8') as f:
    DATA_TEXT = f.read().strip()
DATA = json.loads(DATA_TEXT)  # проверка валидности

html_path = os.path.join(SRC, 'index.html')
with open(html_path, encoding='utf-8') as f:
    html = f.read()

inject = ('  <!-- Данные встроены в страницу: работают при экспорте в Publii '
          'без отдельного запроса data.json -->\n'
          '  <script id="catco-data" type="application/json">\n'
          + DATA_TEXT.replace('</', '<\\/') + '\n  </script>\n'
          '  <script>window.CATCO_DATA = JSON.parse('
          'document.getElementById("catco-data").textContent);</script>\n')

html, n = re.subn(r'(\n)(  <script src="assets/img/three\.min\.js"></script>)',
                  r'\1' + inject + r'\2', html, count=1)
assert n == 1, 'не найден маркер внедрения данных (three.min.js)'

# абсолютизация всех локальных путей ресурсов (Publii живёт на /)
for rel in sorted({m.group(1) for m in re.finditer(
        r'(?:src|href)="((?:assets|css|js|images)/[^"]+)"', html)}):
    html = html.replace('="%s"' % rel, '="/%s"' % rel)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

# ------------------------------------------------- 2. main.js: приоритет встроенных данных
js_path = os.path.join(SRC, 'js', 'main.js')
with open(js_path, encoding='utf-8') as f:
    js = f.read()

old_loader = """  function loadData() {
    return fetch('data.json')"""
new_loader = """  function loadData() {
    // Publii / статический хостинг: данные уже вшиты в страницу
    if (window.CATCO_DATA) {
      return Promise.resolve(window.CATCO_DATA);
    }
    const inline = document.getElementById('catco-data');
    if (inline) {
      try { return Promise.resolve(JSON.parse(inline.textContent)); } catch (e) {}
    }
    return fetch('/data.json')"""
assert old_loader in js, 'не найден загрузчик данных в main.js'
js = js.replace(old_loader, new_loader, 1)
js = js.replace("x.open('GET', 'data.json', true);", "x.open('GET', '/data.json', true);")

# пути к картинкам из данных делаем корневыми (Publii живёт на /)
norm_helper = """  function normalizePaths(node) {
    const abs = v => (typeof v === 'string' && /^(?!\\/|https?:|data:|mailto:|tel:)[a-z0-9_-]/i.test(v))
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

"""
marker = "  const $ = s => document.querySelector(s);"
assert marker in js, 'не найден маркер хелперов в main.js'
js = js.replace(marker, norm_helper + marker, 1)

call_old = "  loadData().then(data => {"
call_new = "  loadData().then(data => {\n    data = normalizePaths(data);"
assert call_old in js, 'не найден вызов loadData()'
js = js.replace(call_old, call_new, 1)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

# ------------------------------------------------- 3. служебные файлы пакета
readme = """CatCo Studio — пакет для Publii
================================

Состав:
  index.html   — готовая страница (данные встроены, пути абсолютные)
  css/         — стили
  js/          — скрипты (three.js + логика)
  assets/      — изображения и 3D-библиотека
  publii-import.md — инструкция по импорту

Как перенести в Publii
----------------------
СПОСОБ A. Как «внешний» сайт через Custom HTML (самый простой)
  1. Site > Settings > Advanced > «Custom theme templates / Head code» —
     подключите /css/style.css.
  2. Создайте запись (Posts > Add post), переключите редактор в режим
     HTML и вставьте содержимое <body> из index.html.
  3. В «Head code» добавьте скрипты three.min.js и main.js.
  4. Папку assets/img/gen загрузите в Media (она попадёт в /media/...).

СПОСОБ B. Полноценная статическая копия (рекомендуется)
  1. Откройте сайт локально: python3 -m http.server -d out/catco-studio-publii 8000
  2. Сохраните страницу со всеми ресурсами или используйте этот пакет как
     корень сайта при выгрузке на хостинг из Publii (Site > Export).
  3. Все картинки лежат в /assets/img/gen/, CSS — /css/style.css,
     JS — /js/main.js и /js/three.min.js.

СПОСОБ C. Выложить пакет как статический сайт рядом с Publii (самый надёжный)
  1. Распакуйте архив catco-studio-publii.zip.
  2. Загрузите папку catco-studio-publii целиком в любой каталог хостинга
     (например /publii-site/) — структура путей уже корневая: /css/, /js/,
     /assets/. Если сайт живёт не в корне домена, замените ведущий «/» на
     имя подпапки в index.html, css/style.css и js/main.js.
  3. В Publii создайте страницу-ссылку или редирект на /publii-site/index.html.

Важно
-----
* Данные (услуги, портфолио, отзывы, форматы) вшиты в index.html в тег
  <script id="catco-data" type="application/json"> — отдельный fetch к
  data.json не требуется, поэтому экспорт не «ломается» на MIME-типах.
  Копия data.json оставлена для редактирования: после правки данных
  замените содержимое тега catco-data.
* Форма заявки не отправляется на сервер: backend не подключён. При
  отправке показывается честное сообщение и черновик сохраняется в
  localStorage. Для реальной отправки включите интеграцию формы в Publii
  (Forms) или укажите endpoint в настройках.
* Изображения демонстрационные — это кейсы студии, а не клиенты-бренды.
"""
with open(os.path.join(SRC, 'publii-import.md'), 'w', encoding='utf-8') as f:
    f.write(readme)

# three.min.js кладём рядом с остальными скриптами (PUTЬ /js/three.min.js)
shutil.copy(os.path.join(SRC, 'assets', 'img', 'three.min.js'),
            os.path.join(SRC, 'js', 'three.min.js'))
html = open(html_path, encoding='utf-8').read()
html = html.replace('src="/assets/img/three.min.js"', 'src="/js/three.min.js"')
open(html_path, 'w', encoding='utf-8').write(html)

# ------------------------------------------------- 3.5 data.json c корневыми путями + сниппеты
def abs_paths(node):
    if isinstance(node, list):
        return [abs_paths(x) for x in node]
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            path_like = k in ('src', 'img', 'image', 'cover', 'avatar', 'thumb')
            rel_str = isinstance(v, str) and not v.startswith(('http', '/', 'data:'))
            out[k] = ('/' + v) if (path_like and rel_str) else abs_paths(v)
        return out
    return node


with open(os.path.join(SRC, 'data.json'), encoding='utf-8') as f:
    _data = json.load(f)
_abs_text = json.dumps(abs_paths(_data), ensure_ascii=False, indent=2)
with open(os.path.join(SRC, 'data.json'), 'w', encoding='utf-8') as f:
    f.write(_abs_text)

# встроенный в index.html блок данных приводим к тем же корневым путям
_page = open(html_path, encoding='utf-8').read()
_tag_start = _page.index('<script id="catco-data" type="application/json">\n') + len(
    '<script id="catco-data" type="application/json">\n')
_tag_end = _page.index('\n  </script>', _tag_start)
_page = _page[:_tag_start] + _abs_text.replace('</', '<\\/') + _page[_tag_end:]
open(html_path, 'w', encoding='utf-8').write(_page)

# готовые HTML-фрагменты для вставки в Publii (меню и футер темы)
snips = os.path.join(SRC, 'publii-snippets')
os.makedirs(snips, exist_ok=True)

MENU_HTML = '''<!-- Site > Menu > Add item (каждый пункт отдельно) или вставьте как есть -->
<nav class="nav-links">
  <a href="/index.html#services">Услуги</a>
  <a href="/index.html#portfolio">Портфолио</a>
  <a href="/index.html#process">Процесс</a>
  <a href="/index.html#whyus">О студии</a>
  <a href="/index.html#reviews">Отзывы</a>
  <a href="/index.html#order">Контакты</a>
</nav>
<a href="/index.html#order" class="btn btn-primary nav-cta">Обсудить проект</a>
'''
with open(os.path.join(snips, 'header-menu.html'), 'w', encoding='utf-8') as f:
    f.write(MENU_HTML)

_page = open(html_path, encoding='utf-8').read()
_footer = _page.split('<!-- ============ КОНТАКТЫ / ФУТЕР ============ -->')[1]
_footer = _footer.split('</footer>')[0] + '</footer>\n'
with open(os.path.join(snips, 'footer.html'), 'w', encoding='utf-8') as f:
    f.write('<!-- Site > Settings > Footer > Custom code -->\n' + _footer)

_head = ('<!-- Site > Settings > Head code: подключение стилей и скриптов сайта -->\n'
         '<link rel="stylesheet" href="/css/style.css">\n'
         '<script src="/js/three.min.js" defer></script>\n'
         '<script src="/js/main.js" defer></script>\n')
with open(os.path.join(snips, 'head-code.html'), 'w', encoding='utf-8') as f:
    f.write(_head)

# ------------------------------------------------- 4. сборка архивов
if os.path.exists(OUT_ROOT):
    shutil.rmtree(OUT_ROOT)
os.makedirs(PKG)


def add_tree(zf, base, arc=''):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, base)
            zf.write(full, os.path.join(arc, rel).replace('\\', '/'))


# ZIP
zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'catco-studio-publii.zip')
if os.path.exists(zip_path):
    os.remove(zip_path)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    add_tree(zf, SRC, 'catco-studio-publii')

# TAR.GZ
tar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'catco-studio-publii.tar.gz')
if os.path.exists(tar_path):
    os.remove(tar_path)
with zipfile.ZipFile(zip_path) as zin, tarfile.open(tar_path, 'w:gz') as tfout:
    for info in zin.infolist():
        raw = zin.read(info.filename)
        ti = tarfile.TarInfo(info.filename)
        ti.size = len(raw)
        ti.mtime = int(mktime(info.date_time + (0, 0, -1)))
        ti.mode = 0o755 if info.external_attr >> 16 & 0o111 else 0o644
        tfout.addfile(ti, io.BytesIO(raw))

print('ZIP:', zip_path, os.path.getsize(zip_path))
print('TARGZ:', tar_path, os.path.getsize(tar_path))
