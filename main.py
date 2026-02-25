import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import threading
import os
import subprocess
import platform
import shutil

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 다운로더")
        self.root.geometry("600x600")
        self.root.resizable(True, True)
        
        # 변수
        self.url_var = tk.StringVar()
        self.formats = []
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.open_folder_var = tk.BooleanVar(value=True)  # 기본값: 폴더 열기
        self.default_quality_index = 0  # 기본 선택 인덱스
        self.js_runtimes = self._detect_js_runtime()

        self.setup_ui()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 제목
        title_label = ttk.Label(main_frame, text="YouTube 비디오 다운로더", 
                               font=("맑은 고딕", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # URL 입력 섹션
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(1, weight=1)
        
        url_label = ttk.Label(url_frame, text="YouTube URL:")
        url_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        url_entry = tk.Entry(url_frame, textvariable=self.url_var, width=45,
                            bg="#FFF9C4", relief=tk.SOLID, bd=1,
                            font=("맑은 고딕", 9),
                            insertbackground="black")
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        url_entry.bind('<Return>', lambda e: self.fetch_info())  # Enter 키로 정보 가져오기
        url_entry.bind('<FocusIn>', lambda e: url_entry.config(bg="white"))  # 포커스 시 흰색
        url_entry.bind('<FocusOut>', lambda e: url_entry.config(bg="#FFF9C4"))  # 포커스 해제 시 연한 노란색
        
        fetch_btn = ttk.Button(url_frame, text="정보 가져오기", 
                              command=self.fetch_info, width=15)
        fetch_btn.grid(row=0, column=2, padx=(5, 5))
        
        reset_btn = ttk.Button(url_frame, text="초기화", 
                              command=self.reset_all, width=12)
        reset_btn.grid(row=0, column=3, padx=(0, 0))
        
        # 비디오 정보 (더 컴팩트하게)
        info_frame = ttk.LabelFrame(main_frame, text="비디오 정보", padding="8")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        
        self.info_text = tk.Text(info_frame, height=4, width=70, 
                                state='disabled', wrap=tk.WORD, font=("맑은 고딕", 9))
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 화질 선택 (더 컴팩트하게)
        quality_frame = ttk.LabelFrame(main_frame, text="화질 선택", padding="8")
        quality_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        quality_frame.columnconfigure(0, weight=1)
        quality_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        listbox_frame = ttk.Frame(quality_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        self.quality_listbox = tk.Listbox(listbox_frame, height=6, font=("맑은 고딕", 9))
        self.quality_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, 
                                 command=self.quality_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.quality_listbox.config(yscrollcommand=scrollbar.set)
        
        # 옵션 및 다운로드 섹션 (한 줄에 배치)
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # 저장 경로
        path_label = ttk.Label(options_frame, text="저장 경로:")
        path_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.path_label = ttk.Label(options_frame, text=self.download_path, 
                                    relief=tk.SUNKEN, width=40, anchor=tk.W)
        self.path_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        browse_btn = ttk.Button(options_frame, text="찾아보기", 
                               command=self.browse_folder, width=12)
        browse_btn.grid(row=0, column=2, padx=(5, 15))
        
        # 다운로드 후 폴더 열기 옵션
        open_folder_check = ttk.Checkbutton(options_frame, 
                                           text="다운로드 완료 후 폴더 열기",
                                           variable=self.open_folder_var)
        open_folder_check.grid(row=0, column=3, padx=(0, 10))
        
        # 진행 상황 및 다운로드 버튼 (한 줄에)
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        action_frame.columnconfigure(0, weight=1)
        
        # 진행 상황
        progress_frame = ttk.Frame(action_frame)
        progress_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="대기 중...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, 
                                  font=("맑은 고딕", 9))
        progress_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 3))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', 
                                           length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 다운로드 버튼 (더 크고 눈에 띄게 - 색상 적용)
        download_btn = tk.Button(action_frame, text="다운로드", 
                                 command=self.download_video, 
                                 width=20, height=2,
                                 bg="#81C784", fg="white",
                                 font=("맑은 고딕", 14, "bold"),
                                 relief=tk.RAISED, bd=2,
                                 cursor="hand2",
                                 activebackground="#66BB6A",
                                 activeforeground="white")
        download_btn.grid(row=0, column=1, rowspan=2, sticky=(tk.N, tk.S), padx=(10, 0))
        
    def _detect_js_runtime(self):
        for runtime in ('deno', 'node', 'bun'):
            if shutil.which(runtime):
                return runtime
        return None

    def _base_ydl_opts(self):
        opts = {}
        if self.js_runtimes:
            opts['js_runtimes'] = self.js_runtimes
        return opts

    def fetch_info(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("경고", "YouTube URL을 입력하세요.")
            return
            
        self.progress_var.set("정보를 가져오는 중...")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self._fetch_info_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _fetch_info_thread(self, url):
        try:
            ydl_opts = {
                **self._base_ydl_opts(),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 정보 표시
                self.info_text.config(state='normal')
                self.info_text.delete(1.0, tk.END)
                info_str = f"제목: {info.get('title', 'N/A')}\n"
                info_str += f"업로더: {info.get('uploader', 'N/A')}\n"
                info_str += f"길이: {info.get('duration', 0) // 60}분 {info.get('duration', 0) % 60}초\n"
                info_str += f"조회수: {info.get('view_count', 'N/A'):,}\n"
                self.info_text.insert(1.0, info_str)
                self.info_text.config(state='disabled')
                
                # 포맷 정보 수집
                self.formats = []
                self.quality_listbox.delete(0, tk.END)
                
                formats = info.get('formats', [])
                
                # 비디오+오디오 포맷 추출
                video_audio_formats = []
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        height = f.get('height', 0)
                        if height:
                            video_audio_formats.append(f)
                
                # 비디오 전용 포맷 (높은 화질)
                video_only_formats = []
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                        height = f.get('height', 0)
                        if height:
                            video_only_formats.append(f)
                
                # 오디오 전용 포맷
                audio_only_formats = []
                for f in formats:
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        audio_only_formats.append(f)
                
                # 포맷 정렬 (화질 높은 순)
                video_audio_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                video_only_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                audio_only_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
                
                # 간단한 옵션 추가
                simple_options = [
                    {'id': 'best', 'desc': '최고 화질 + 최고 음질 (권장)', 'format': 'bestvideo+bestaudio[acodec=opus]/bestvideo+bestaudio/best'},
                    {'id': '1080p', 'desc': '1080p (Full HD) + 최고 음질', 'format': 'bestvideo[height<=1080]+bestaudio[acodec=opus]/bestvideo[height<=1080]+bestaudio/best[height<=1080]'},
                    {'id': '720p', 'desc': '720p (HD) + 최고 음질', 'format': 'bestvideo[height<=720]+bestaudio[acodec=opus]/bestvideo[height<=720]+bestaudio/best[height<=720]'},
                    {'id': '480p', 'desc': '480p (SD) + 최고 음질', 'format': 'bestvideo[height<=480]+bestaudio[acodec=opus]/bestvideo[height<=480]+bestaudio/best[height<=480]'},
                    {'id': 'audio', 'desc': '오디오만 (최고 품질 - Opus/AAC)', 'format': 'bestaudio[acodec=opus]/bestaudio[ext=m4a]/bestaudio'},
                ]
                
                self.quality_listbox.insert(tk.END, "=== 간편 선택 (권장) ===")
                header_count = 1  # 헤더 개수 추적
                for idx, opt in enumerate(simple_options):
                    self.quality_listbox.insert(tk.END, opt['desc'])
                    self.formats.append(opt)
                    if opt['id'] == 'best':
                        # 최고 화질 + 최고 음질이 첫 번째 옵션 (헤더 다음)
                        self.default_quality_index = header_count + idx
                
                self.quality_listbox.insert(tk.END, "")
                header_count += len(simple_options) + 1
                self.quality_listbox.insert(tk.END, "=== 고급 선택 ===")
                header_count += 1
                
                # 비디오+오디오 (권장)
                if video_audio_formats:
                    self.quality_listbox.insert(tk.END, "--- 비디오+오디오 ---")
                    header_count += 1
                    for f in video_audio_formats[:5]:  # 상위 5개만
                        format_str = self._format_string(f)
                        self.quality_listbox.insert(tk.END, format_str)
                        self.formats.append(f)
                
                # 비디오 전용 (최고 화질)
                if video_only_formats:
                    self.quality_listbox.insert(tk.END, "--- 비디오 전용 ---")
                    header_count += 1
                    for f in video_only_formats[:5]:  # 상위 5개만
                        format_str = self._format_string(f)
                        self.quality_listbox.insert(tk.END, format_str)
                        self.formats.append(f)
                
                # 오디오 전용
                if audio_only_formats:
                    self.quality_listbox.insert(tk.END, "--- 오디오 전용 ---")
                    header_count += 1
                    for f in audio_only_formats[:3]:  # 상위 3개만
                        format_str = self._format_string(f, audio_only=True)
                        self.quality_listbox.insert(tk.END, format_str)
                        self.formats.append(f)
                
                # 기본 선택값 설정 (최고 화질 + 최고 음질)
                if self.default_quality_index > 0:
                    self.quality_listbox.selection_set(self.default_quality_index)
                    self.quality_listbox.see(self.default_quality_index)
                
                self.progress_var.set("준비 완료!")
                self.progress_bar.stop()
                
        except Exception as e:
            self.progress_bar.stop()
            self.progress_var.set("오류 발생!")
            messagebox.showerror("오류", f"정보를 가져오는 중 오류가 발생했습니다:\n{str(e)}")
    
    def _format_string(self, f, audio_only=False):
        if audio_only:
            abr = f.get('abr', 0)
            ext = f.get('ext', 'unknown')
            format_id = f.get('format_id', 'unknown')
            return f"[{format_id}] {ext} - {abr:.0f}kbps"
        else:
            height = f.get('height', 0)
            fps = f.get('fps', 0)
            ext = f.get('ext', 'unknown')
            vcodec = f.get('vcodec', 'unknown')[:20]
            format_id = f.get('format_id', 'unknown')
            
            has_audio = f.get('acodec') != 'none'
            audio_str = " 🔊" if has_audio else " (오디오 없음)"
            
            return f"[{format_id}] {height}p {fps}fps - {ext} ({vcodec}){audio_str}"
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.path_label.config(text=folder)
    
    def download_video(self):
        selection = self.quality_listbox.curselection()
        
        # 선택이 없으면 기본값(최고 화질) 사용
        if not selection:
            if self.default_quality_index > 0:
                selection = (self.default_quality_index,)
            else:
                messagebox.showwarning("경고", "화질을 선택하세요.")
                return
        
        # 헤더 선택 확인
        selected_text = self.quality_listbox.get(selection[0])
        if (selected_text.startswith("===") or selected_text.startswith("---") or 
            selected_text.strip() == ""):
            # 헤더를 선택했으면 기본값 사용
            if self.default_quality_index > 0:
                selection = (self.default_quality_index,)
                selected_text = self.quality_listbox.get(selection[0])
            else:
                messagebox.showwarning("경고", "유효한 화질을 선택하세요.")
                return
        
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("경고", "YouTube URL을 입력하세요.")
            return
        
        # 실제 포맷 인덱스 계산 (헤더 제외)
        format_index = 0
        for i in range(selection[0]):
            text = self.quality_listbox.get(i)
            if not (text.startswith("===") or text.startswith("---") or text.strip() == ""):
                format_index += 1
        
        if format_index >= len(self.formats):
            messagebox.showerror("오류", "잘못된 선택입니다.")
            return
        
        selected_format = self.formats[format_index]
        
        self.progress_var.set("다운로드 중...")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self._download_thread, 
                                 args=(url, selected_format))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, url, format_info):
        try:
            # 기본 옵션
            ydl_opts = {
                **self._base_ydl_opts(),
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': False,
                'no_warnings': False,
            }
            
            # 간편 선택 옵션인지 확인 (딕셔너리에 'id' 키가 있으면 간편 선택)
            if 'id' in format_info:
                # 간편 선택 옵션
                ydl_opts['format'] = format_info['format']
                if format_info['id'] != 'audio':
                    ydl_opts['merge_output_format'] = 'mp4'
            else:
                # 고급 선택 (기존 포맷 ID 사용)
                format_id = format_info.get('format_id')
                
                # 비디오 전용인 경우 오디오 병합
                if format_info.get('acodec') == 'none':
                    # 최고 품질 오디오 우선 선택 (Opus > M4A > 기타)
                    ydl_opts['format'] = f'{format_id}+bestaudio[acodec=opus]/{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/best'
                    ydl_opts['merge_output_format'] = 'mp4'
                else:
                    # 비디오+오디오가 이미 있는 경우, fallback 추가
                    ydl_opts['format'] = f'{format_id}/bestvideo+bestaudio/best'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.progress_bar.stop()
            self.progress_var.set("다운로드 완료!")
            
            # 폴더 열기 옵션이 선택되어 있으면 폴더 열기
            if self.open_folder_var.get():
                self.open_download_folder()
            
            messagebox.showinfo("완료", f"다운로드가 완료되었습니다!\n저장 위치: {self.download_path}")
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_var.set("오류 발생!")
            messagebox.showerror("오류", f"다운로드 중 오류가 발생했습니다:\n{str(e)}")
    
    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            self.progress_var.set(f"다운로드 중... {d.get('_percent_str', 'N/A')}")
        elif d['status'] == 'finished':
            self.progress_var.set("파일 처리 중...")
    
    def reset_all(self):
        """모든 입력과 정보를 초기화"""
        # URL 초기화
        self.url_var.set("")
        
        # 비디오 정보 초기화
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')
        
        # 화질 선택 리스트 초기화
        self.quality_listbox.delete(0, tk.END)
        self.formats = []
        self.default_quality_index = 0
        
        # 진행 상황 초기화
        self.progress_var.set("대기 중...")
        if self.progress_bar.cget('mode') == 'indeterminate':
            self.progress_bar.stop()
    
    def open_download_folder(self):
        """다운로드 폴더 열기"""
        try:
            if platform.system() == 'Windows':
                os.startfile(self.download_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', self.download_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', self.download_path])
        except Exception as e:
            print(f"폴더 열기 오류: {e}")

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
