"""exhibitors.txt + coords_raw.json + map.jpg -> index.html (단일 파일)"""
import json, re, base64, statistics
HERE = __import__('pathlib').Path(__file__).parent
raw = json.loads((HERE/'coords_raw.json').read_text())
coords = {k: (statistics.median(p[0] for p in v), statistics.median(p[1] for p in v)) for k, v in raw.items()}
coords.update({'112': (172, 363), '802': (1917, 281)})  # OCR 누락분 수동 보정

booths, cur, group = [], None, ''
for line in (HERE/'exhibitors.txt').read_text().splitlines():
    if not line.strip(): continue
    if line.startswith('@@group'):
        group = line.split('\t')[1] if '\t' in line else ''; continue
    m = re.match(r'^(\d{3})(?:[\t ]+(.*))?$', line)
    if m and not line.startswith('802PRODUCTS'):
        cur = {'n': m.group(1), 'lines': [m.group(2).strip()] if m.group(2) else [], 'g': group}
        booths.append(cur)
    elif cur: cur['lines'].append(line.strip())
HALL = {'1': 'C', '2': 'C', '3': 'D', '4': 'D', '5': 'E', '6': 'E', '7': 'F', '8': 'F'}
out = []
for b in booths:
    c = coords.get(b['n'])
    if not c: print('NO COORD', b['n']); continue
    ls = b['lines']
    out.append({'n': b['n'], 'h': HALL[b['n'][0]], 'x': round(c[0]), 'y': round(c[1]),
                't': ls[0] if ls else '', 's': ls[1:], 'g': b['g']})
print(len(out), 'booths')
import numpy as np
CS = 4
walk = np.load(HERE/'walk.npy')
gh, gw = -(-walk.shape[0]//CS), -(-walk.shape[1]//CS)
pad = np.zeros((gh*CS, gw*CS), bool); pad[:walk.shape[0], :walk.shape[1]] = walk
cells = pad.reshape(gh, CS, gw, CS).mean(axis=(1, 3)) >= 0.5
nav = {'cs': CS, 'gw': gw, 'gh': gh, 'b64': base64.b64encode(np.packbits(cells.flatten()).tobytes()).decode()}
img = base64.b64encode((HERE/'map.jpg').read_bytes()).decode()
html = (HERE/'template.html').read_text().replace('/*DATA*/[]', json.dumps(out, ensure_ascii=False)).replace('/*NAV*/null', json.dumps(nav)).replace('IMG_B64', img)
(HERE/'index.html').write_text(html)
