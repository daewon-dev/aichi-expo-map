"""행사 폴더 + src/template.html -> 단일 index.html

사용: python3 tools/build.py events/<행사폴더> [출력경로, 기본 ./index.html]
필요: pip install numpy pillow
"""
import base64, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ev = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT/'index.html'
cfg = json.loads((ev/'event.json').read_text())
exh = json.loads((ev/'exhibitors.json').read_text())
coords = {k: tuple(v) for k, v in json.loads((ev/'coords.json').read_text()).items()}
coords.update({k: tuple(v) for k, v in cfg.get('coordOverrides', {}).items()})

hall_of = {p: h['id'] for h in cfg['halls'] for p in h['prefixes']}
booths = []
for b in exh:
    c = coords.get(b['n'])
    if not c:
        print('위치 없음(건너뜀):', b['n']); continue
    sub = list(b.get('notes', [])) + [f'・{i}' for i in b.get('items', [])]
    booths.append({'n': b['n'], 'h': hall_of.get(b['n'][0], '?'), 'x': round(c[0]), 'y': round(c[1]),
                   't': b.get('name', ''), 's': sub, 'g': b.get('group', ''), 'f': b.get('flag', '')})
print(len(booths), 'booths')

W, H = Image.open(ev/'map.jpg').size
CS = cfg.get('walk', {}).get('cell', 4)
walk = np.load(ev/'walk.npy')
gh, gw = -(-H//CS), -(-W//CS)
pad = np.zeros((gh*CS, gw*CS), bool); pad[:H, :W] = walk[:H, :W]
cells = pad.reshape(gh, CS, gw, CS).mean(axis=(1, 3)) >= 0.5
nav = {'cs': CS, 'gw': gw, 'gh': gh, 'b64': base64.b64encode(np.packbits(cells.flatten()).tobytes()).decode()}

titles = cfg['title'] if isinstance(cfg['title'], dict) else {'ko': cfg['title']}
meta = {'title': titles, 'w': W, 'h': H, 'halls': [{'id': h['id'], 'color': h['color']} for h in cfg['halls']]}
img = base64.b64encode((ev/'map.jpg').read_bytes()).decode()
html = (ROOT/'src'/'template.html').read_text()
for k, v in {'/*DATA*/[]': json.dumps(booths, ensure_ascii=False), '/*NAV*/null': json.dumps(nav),
             '/*EVENT*/{}': json.dumps(meta, ensure_ascii=False), 'IMG_B64': img, '__TITLE__': titles.get('ko', next(iter(titles.values()))),
             '__W__': str(W), '__H__': str(H), '__THEME__': cfg.get('themeColor', '#1971ff')}.items():
    html = html.replace(k, v)
out.write_text(html)
print('->', out)

# ---- 오프라인(PWA) 파일: manifest, 아이콘, 서비스 워커 (index.html 과 같은 폴더에 생성)
import hashlib
from PIL import ImageDraw
od = out.parent
theme = cfg.get('themeColor', '#1971ff')

def icon(size):
    S = size*4                                   # 4배로 그린 뒤 줄여서 부드럽게
    im = Image.new('RGB', (S, S), theme)
    d = ImageDraw.Draw(im)
    cx, cy, r = S/2, S*0.42, S*0.22              # 지도 핀 모양
    d.polygon([(cx-r*0.93, cy+r*0.35), (cx+r*0.93, cy+r*0.35), (cx, S*0.80)], fill='white')
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill='white')
    d.ellipse([cx-r*0.42, cy-r*0.42, cx+r*0.42, cy+r*0.42], fill=theme)
    return im.resize((size, size), Image.LANCZOS)

icon(192).save(od/'icon-192.png'); icon(512).save(od/'icon-512.png'); icon(180).save(od/'apple-touch-icon.png')
(od/'manifest.webmanifest').write_text(json.dumps({
    'name': titles.get('ko', next(iter(titles.values()))), 'short_name': 'EXPO MAP', 'start_url': './', 'scope': './',
    'display': 'standalone', 'background_color': '#ffffff', 'theme_color': theme,
    'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, ensure_ascii=False, indent=1))
ver = hashlib.sha1(html.encode()).hexdigest()[:10]   # 내용이 바뀌면 캐시 이름도 바뀜 → 옛 캐시 자동 삭제
(od/'sw.js').write_text(f"""// 자동 생성 파일 (tools/build.py)
const V = 'expo-{ver}';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => e.waitUntil(
  caches.open(V).then(c => c.addAll(FILES.map(f => new Request(f, {{cache: 'reload'}})))).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())));
// 캐시 우선(오프라인에서도 열림) + 뒤에서 최신본을 받아 두기 → 새 버전은 다음 실행부터 적용
self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request, {{ignoreSearch: true}}).then(hit => {{
    const net = fetch(e.request).then(r => {{
      if (r.ok) {{ const cp = r.clone(); caches.open(V).then(c => c.put(e.request, cp)); }}
      return r;
    }}).catch(() => hit);
    return hit || net;
  }}));
}});
""")
print('PWA files ->', od)
