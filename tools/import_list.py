"""exhibitors.txt (행사 사이트 목록을 붙여넣은 텍스트) -> exhibitors.json (오브젝트 배열)

사용: python3 tools/import_list.py events/<행사폴더>

txt 형식:
  321<TAB>GOLDEN FOREST          ← 부스번호 + 업체명(첫 줄)
  ・PLANFORTY                    ← ・로 시작하면 입점 브랜드 목록(items)
  아웃도어 급수 시스템             ← 그 외 이어지는 줄은 부가 설명(notes)
  321<TAB>!noname  /  !guess        ← 업체명이 원문에 없거나 번호를 추정한 부스 표시 (화면에서 한/일 문구로 표시)
  @@group<TAB>그룹 이름           ← 이후 부스들에 group 값을 붙임 (@@group 만 쓰면 해제)
"""
import json, re, sys
from pathlib import Path

ev = Path(sys.argv[1])
booths, cur, group = [], None, ''
for line in (ev/'exhibitors.txt').read_text().splitlines():
    if not line.strip():
        continue
    if line.startswith('@@group'):
        group = line.split('\t', 1)[1].strip() if '\t' in line else ''
        continue
    m = re.match(r'^(\d{3})(?:[\t ]+(.*))?$', line)
    if m:
        name = (m.group(2) or '').strip()
        flag = name[1:] if name.startswith('!') else ''   # '!noname' '!guess' 같은 표시
        cur = {'n': m.group(1), 'name': '' if flag else name, 'items': [], 'notes': [], 'group': group, 'flag': flag}
        booths.append(cur)
    elif cur:
        s = line.strip()
        if s.startswith('・'):
            cur['items'].append(s[1:].strip())
        else:
            cur['notes'].append(s)
for b in booths:  # 빈 값은 JSON에서 생략
    for k in ('items', 'notes', 'group', 'flag'):
        if not b[k]:
            del b[k]
(ev/'exhibitors.json').write_text(json.dumps(booths, ensure_ascii=False, indent=1))
print(len(booths), 'booths ->', ev/'exhibitors.json')
