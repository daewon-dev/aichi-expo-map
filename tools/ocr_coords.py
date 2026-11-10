"""지도 이미지에서 부스 번호 위치를 OCR(macOS Vision)로 찾아 coords.json 생성

사용: python3 tools/ocr_coords.py events/<행사폴더>
- exhibitors.json 에 있는 부스번호만 찾습니다 (오인식으로 엉뚱한 번호가 섞이는 걸 방지)
- 못 찾은 번호는 출력해 주니, event.json 의 coordOverrides 에 [x, y] 로 직접 넣으면 됩니다
- macOS + Xcode 커맨드라인 도구(swiftc) 필요
"""
import json, re, statistics, subprocess, sys, tempfile
from collections import defaultdict
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
ev = Path(sys.argv[1])
want = {b['n'] for b in json.loads((ev/'exhibitors.json').read_text())}

binp = ROOT/'.bin'/'ocr'
if not binp.exists():
    binp.parent.mkdir(exist_ok=True)
    subprocess.run(['swiftc', '-O', str(ROOT/'ocr.swift'), '-o', str(binp)], check=True)

im = Image.open(ev/'map.jpg').convert('RGB')
W, H = im.size
S, TW, TH, OV = 3, 700, 450, 60   # 3배 확대, 타일 크기, 겹침
found = defaultdict(list)
with tempfile.TemporaryDirectory() as td:
    for y in range(0, H, TH-OV):
        for x in range(0, W, TW-OV):
            box = (x, y, min(x+TW, W), min(y+TH, H))
            t = im.crop(box).resize(((box[2]-box[0])*S, (box[3]-box[1])*S), Image.LANCZOS)
            tp, jp = f'{td}/t.png', f'{td}/t.json'
            t.save(tp)
            subprocess.run([str(binp), tp, jp], check=True, capture_output=True)
            for o in json.load(open(jp)):
                txt = o['t']
                d = re.sub(r'\D', '', txt)
                if len(d) < 3 or len(d) % 3 or len(d) > 12 or re.search(r'[A-Za-z]{2,}', txt):
                    continue
                k = len(d)//3   # '606 607608' 처럼 한 줄에 여러 번호가 붙어 나오면 가로로 균등 분할
                for i in range(k):
                    n = d[i*3:i*3+3]
                    if n in want:
                        found[n].append((x+(o['x']+o['w']*(i+.5)/k)/S, y+(o['y']+o['h']/2)/S))

coords = {n: [round(statistics.median(p[0] for p in v)), round(statistics.median(p[1] for p in v))] for n, v in found.items()}
(ev/'coords.json').write_text(json.dumps(coords, sort_keys=True))
miss = sorted(want-set(coords))
print(f'{len(coords)}/{len(want)} 개 위치 인식')
print('못 찾은 번호 (event.json 의 coordOverrides 에 직접 입력):', miss)
