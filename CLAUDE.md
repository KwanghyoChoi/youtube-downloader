# YouTube 다운로더 프로젝트

## 개요
tkinter 기반 YouTube 비디오 다운로더 GUI 앱. yt-dlp를 백엔드로 사용.

## 기술 스택
- Python 3.7+
- tkinter (GUI)
- yt-dlp (다운로드 엔진)
- ffmpeg (비디오/오디오 병합 - 외부 의존성)

## 프로젝트 구조
```
main.py       # 메인 앱 (콘솔 창 표시)
main.pyw      # 메인 앱 (콘솔 창 숨김, 배포용)
requirements.txt
```

## 주요 클래스/함수
- `YouTubeDownloader` (main.py) — 전체 앱 로직을 담당하는 단일 클래스
  - `fetch_info()` — URL에서 비디오 정보 및 포맷 목록 가져오기
  - `download_video()` — 선택한 포맷으로 다운로드 실행
  - `_base_ydl_opts()` — JS 런타임(deno/node/bun) 감지 후 기본 옵션 생성

## 코딩 컨벤션
- 한국어 UI 텍스트 및 주석 사용
- 폰트: "맑은 고딕" (Windows 한글 폰트)
- 다운로드 기본 경로: `~/Downloads`

## 실행 방법
```bash
pip install -r requirements.txt
python main.py
```

## 참고
- main.py와 main.pyw는 동일한 코드 (확장자만 다름)
- 비디오/오디오 별도 다운로드 후 ffmpeg로 mp4 병합
- yt-dlp 포맷 선택: `bestvideo+bestaudio` 패턴 사용
