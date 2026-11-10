"""지도 이미지에서 '걸을 수 있는 통로' 마스크 생성 -> walk.npy, walk_preview.png

사용: python3 tools/mask.py events/<행사폴더>
- event.json 의 walk 설정: seed([x,y] 통로 위의 한 점), min/max/sat(통로 색 범위)
- walk_preview.png 를 열어 초록색이 통로를 제대로 덮는지 확인하세요
필요: pip install numpy scipy pillow
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ev = Path(sys.argv[1])
cfg = json.loads((ev/'event.json').read_text())['walk']
lo, hi, sat = cfg.get('min', 212), cfg.get('max', 246), cfg.get('sat', 10)
raw = Image.open(ev/'map.jpg').convert('RGB')
im = np.asarray(raw).astype(int)
mx, mn = im.max(2), im.min(2)
floor = (mx-mn < sat) & (mn >= lo) & (mx <= hi)
floor = ndi.binary_closing(floor, iterations=1)
lab, _ = ndi.label(floor)
sx, sy = cfg['seed']
walk = lab == lab[sy, sx]
holes = ndi.binary_fill_holes(walk) & ~walk       # 글자/아이콘 구멍 메우기
hl, hn = ndi.label(holes)
for i, s in enumerate(ndi.sum(holes, hl, range(1, hn+1)), 1):
    if s < 400:
        walk[hl == i] = True
np.save(ev/'walk.npy', walk)
prev = np.asarray(raw).copy()
prev[walk] = (prev[walk]*0.4 + np.array([0, 200, 80])*0.6).astype(np.uint8)
Image.fromarray(prev).save(ev/'walk_preview.png')
print('walk cells:', int(walk.sum()), '→ walk_preview.png 확인')
