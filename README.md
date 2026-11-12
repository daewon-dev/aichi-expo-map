# EXPO 부스 검색 지도

행사 지도 이미지 + 업체 목록으로 **부스 검색 / 위치 이동 / 길찾기**가 되는 단일 HTML(`index.html`)을 만든다.
행사마다 `events/<행사>/` 폴더만 새로 만들면 코드는 그대로 쓴다.

```
events/2026-aichi/
  map.jpg            지도 이미지
  exhibitors.txt     행사 사이트 업체 목록을 붙여넣은 텍스트 (아래 형식)
  exhibitors.json    ↑를 변환한 오브젝트 배열 (직접 고쳐도 됨)
  coords.json        부스 번호별 지도 위 좌표 (OCR 결과)
  walk.npy           걸을 수 있는 통로 마스크 (길찾기용)
  event.json         제목, 홀(색·번호 앞자리), 통로 인식 설정, 좌표 수동 보정
src/template.html    화면 코드 (행사와 무관)
tools/               변환 도구
```

## 새 행사 만들기

필요: macOS + Xcode 커맨드라인 도구(OCR용), `pip install numpy scipy pillow`

1. `events/<새행사>/` 폴더를 만들고 `map.jpg`, `exhibitors.txt`를 넣는다.
2. `event.json`을 2026 것을 복사해 수정한다 (제목, 홀 id/색/번호 앞자리, `walk.seed`).
3. 순서대로 실행:
   ```bash
   python3 tools/import_list.py events/<새행사>   # txt -> exhibitors.json
   python3 tools/ocr_coords.py  events/<새행사>   # 지도에서 번호 위치 찾기
   python3 tools/mask.py        events/<새행사>   # 통로 마스크 (walk_preview.png 확인!)
   python3 tools/build.py       events/<새행사>   # -> index.html
   ```
4. `ocr_coords.py`가 "못 찾은 번호"를 알려 주면 `event.json`의 `coordOverrides`에 `"번호": [x, y]`로 추가하고 다시 build.
5. `walk_preview.png`에서 초록색이 통로를 덮는지 확인한다. 어긋나면 `event.json`의 `walk.min/max/sat/seed`를 조정.

업체만 바뀌고 지도가 같다면 `exhibitors.txt` 수정 → `import_list.py` → `build.py`만 하면 된다.

## exhibitors.txt 형식

```
321<TAB>업체명
・입점 브랜드 1
・입점 브랜드 2
부가 설명 줄 (・ 없으면 notes)
@@group<TAB>그룹 이름     ← 이후 부스들에 그룹 표시, '@@group' 만 쓰면 해제
```

## 화면 언어 (한국어 / 일본어)

화면의 버튼·안내 문구는 `src/template.html` 맨 위의 `I18N` 표에 있고, 목록 위쪽 `日本語 / 한국어` 버튼으로 전환한다
(선택은 브라우저에 저장, 처음엔 기기 언어를 따른다). 제목은 `event.json`의 `title.ko` / `title.ja`.
업체명과 브랜드명은 번역하지 않고 원문 그대로 보인다.

## 기능 메모

- **방문 ✓ / 메모 / ★ 즐겨찾기**: 부스를 선택하면 목록 위 카드에서 설정. 모두 브라우저(localStorage)에 저장되어 기기·브라우저별로 따로 보관된다.
- **즐겨찾기 순회**: 길찾기 → 출발지 선택 → `★ 즐겨찾기 N곳 순회`. 가까운 곳부터 + 2-opt 로 방문 순서를 계산해 번호와 경로로 표시. 순회 중 ✓ 를 누르면 그 부스에서부터 다시 계산.
- **구매 기록(가계부) / 기념 사진 / 내 기록**: 부스 카드의 `💴 · 📷` 줄을 열어 품목·금액을 직접 적고 사진을 찍어 둔다(부스당 5장, 가로 1280px JPEG로 줄여 IndexedDB 에 저장). 칩 줄의 `📒 기록`에서 합계·원화 환산(100엔당 환율 직접 입력)·텍스트 복사·사진 공유. 서버 없이 기기 안에만 저장되므로 내보내기로 따로 남겨 둘 것.
- **오프라인**: build 가 `sw.js`, `manifest.webmanifest`, 아이콘을 함께 만든다. 처음 한 번 인터넷으로 열면 이후 오프라인에서도 열린다.
  캐시 우선이라 새 버전은 **한 번 더 열어야** 반영된다 (앱을 완전히 종료했다 다시 켜면 확실).

## 배포

GitHub Pages가 저장소 루트의 `index.html`을 서비스한다. build 후 `git push`.
