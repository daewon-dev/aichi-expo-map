"""map.jpg -> 통로 마스크(걸을 수 있는 영역). 결과: walk.npy, walk_preview.png"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
im=np.asarray(Image.open('map.jpg').convert('RGB')).astype(int)
mx,mn=im.max(2),im.min(2)
gray=(mx-mn<10)&(mn>=212)&(mx<=246)        # 연한 회색 바닥
gray=ndi.binary_closing(gray,iterations=1)
lab,n=ndi.label(gray)
seed=lab[330,500]
walk=lab==seed
# 텍스트/아이콘 구멍 메우기(작은 구멍만)
holes=ndi.binary_fill_holes(walk)&~walk
hl,hn=ndi.label(holes)
sizes=ndi.sum(holes,hl,range(1,hn+1))
for i,s in enumerate(sizes,1):
    if s<400: walk[hl==i]=True
np.save('walk.npy',walk)
print(walk.sum(), walk.shape)
prev=np.asarray(Image.open('map.jpg').convert('RGB')).copy()
prev[walk]=(prev[walk]*0.4+np.array([0,200,80])*0.6).astype(np.uint8)
Image.fromarray(prev).save('walk_preview.png')
