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
                   't': b.get('name', ''), 's': sub, 'g': b.get('group', '')})
print(len(booths), 'booths')

W, H = Image.open(ev/'map.jpg').size
CS = cfg.get('walk', {}).get('cell', 4)
walk = np.load(ev/'walk.npy')
gh, gw = -(-H//CS), -(-W//CS)
pad = np.zeros((gh*CS, gw*CS), bool); pad[:H, :W] = walk[:H, :W]
cells = pad.reshape(gh, CS, gw, CS).mean(axis=(1, 3)) >= 0.5
nav = {'cs': CS, 'gw': gw, 'gh': gh, 'b64': base64.b64encode(np.packbits(cells.flatten()).tobytes()).decode()}

meta = {'title': cfg['title'], 'w': W, 'h': H, 'halls': [{'id': h['id'], 'color': h['color']} for h in cfg['halls']]}
img = base64.b64encode((ev/'map.jpg').read_bytes()).decode()
html = (ROOT/'src'/'template.html').read_text()
for k, v in {'/*DATA*/[]': json.dumps(booths, ensure_ascii=False), '/*NAV*/null': json.dumps(nav),
             '/*EVENT*/{}': json.dumps(meta, ensure_ascii=False), 'IMG_B64': img, '__TITLE__': cfg['title'], '__W__': str(W), '__H__': str(H)}.items():
    html = html.replace(k, v)
out.write_text(html)
print('->', out)
