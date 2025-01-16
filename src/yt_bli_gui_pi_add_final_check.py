import os
import subprocess
import threading
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time

def validate_url(url):
    youtube_url_pattern = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    bilibili_url_pattern = r'^(https?\:\/\/)?(www\.bilibili\.com\/video\/BV[0-9A-Za-z]+)'
    return re.match(youtube_url_pattern, url) or re.match(bilibili_url_pattern, url)

def determine_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "bilibili.com" in url:
        return "Bilibili"
    return None

def sanitize_url(url):
    # 对 URL 进行清理，只保留基础部分
    if "?" in url:
        url = url.split("?")[0]
    return url

def select_cookie_file():
    file_path = filedialog.askopenfilename(filetypes=[("Cookie files", "*.txt")])
    if file_path:
        entry_cookie.delete(0, tk.END)
        entry_cookie.insert(0, file_path)

def select_download_path():
    path = filedialog.askdirectory()
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)

def parse_progress(line):
    match = re.search(r"(\d+(\.\d+)?)%", line)
    if match:
        return float(match.group(1))
    return None

def start_download():
    thread = threading.Thread(target=download_videos)
    thread.start()

def retry_download(command, log_file, retry_limit=3):
    attempt = 0
    while attempt < retry_limit:
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                log_file.write(line)
                log_text.insert(tk.END, line)
                log_text.see(tk.END)
            process.wait()
            if process.returncode == 0:
                return True
            else:
                attempt += 1
                log_text.insert(tk.END, f"Retrying download... Attempt {attempt}/{retry_limit}\n")
                time.sleep(5)  # Wait before retrying
        except Exception as e:
            log_text.insert(tk.END, f"Error during retry attempt {attempt}: {e}\n")
            attempt += 1
    return False

def download_videos():
    global log_text
    video_url = entry_url.get().strip()
    cookie_file = entry_cookie.get().strip()
    download_path = entry_path.get().strip()
    download_entire_playlist = playlist_var.get()
    playlist_end = entry_playlist_end.get().strip()

    if not video_url:
        messagebox.showerror("Error", "Please provide a video URL.")
        return

    if not validate_url(video_url):
        messagebox.showerror("Error", "Invalid video URL.")
        return

    log_text.insert(tk.END, f"URL input received: {video_url}\n")

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    log_file_path = os.path.join(download_path, "download_log.txt")
    platform = determine_platform(video_url)

    if platform == "YouTube":
        command = [
            "yt-dlp",
            "--cookies", cookie_file,
            "-f", "bestvideo[height<=1080]+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(download_path, "%(title)s.%(ext)s"),
            video_url
        ]
        if download_entire_playlist:
            command.append("--yes-playlist")
    elif platform == "Bilibili":
        command = [
            "yt-dlp",
            "--cookies", cookie_file,
            "-f", "bv[height<=1080]+ba/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(download_path, "%(title)s.%(ext)s"),
            "--all-subs",
            video_url
        ]
        if playlist_end and playlist_end != "-1":
            command.extend(["--playlist-end", playlist_end])
    else:
        log_text.insert(tk.END, f"Unsupported platform for URL: {video_url}\n")
        return

    log_text.insert(tk.END, f"Generated command: {' '.join(command)}\n")
    try:
        with open(log_file_path, "a") as log_file:
            success = retry_download(command, log_file)
            if success:
                log_text.insert(tk.END, f"Download completed for {video_url}\n")
            else:
                log_text.insert(tk.END, f"Download failed for {video_url} after multiple attempts\n")
    except Exception as e:
        log_text.insert(tk.END, f"Error during download: {e}\n")

def clear_logs():
    log_text.delete("1.0", tk.END)
    progress_bar["value"] = 0

# GUI Setup
root = tk.Tk()
root.title("Video Downloader (YouTube & Bilibili)")

# URL Input
tk.Label(root, text="Video URL:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_url = tk.Entry(root, width=50)
entry_url.grid(row=0, column=1, padx=5, pady=5)

# Playlist Checkbox
playlist_var = tk.BooleanVar()
playlist_checkbox = tk.Checkbutton(root, text="Download entire playlist", variable=playlist_var)
playlist_checkbox.grid(row=0, column=2, padx=5, pady=5)

# Playlist End Input
tk.Label(root, text="Playlist End:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_playlist_end = tk.Entry(root, width=50)
entry_playlist_end.insert(0, "-1")
entry_playlist_end.grid(row=1, column=1, padx=5, pady=5)

# Cookie File Input
tk.Label(root, text="Cookie File:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_cookie = tk.Entry(root, width=50)
entry_cookie.grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_cookie_file).grid(row=2, column=2, padx=5, pady=5)

# Download Path Input
tk.Label(root, text="Download Path:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=3, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_download_path).grid(row=3, column=2, padx=5, pady=5)

# Progress Bar
progress_label = tk.Label(root, text="Progress:")
progress_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=4, column=1, columnspan=2, padx=5, pady=5)

# Log Output
log_text = tk.Text(root, height=15, width=70, state="normal")
log_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

# Download Button
download_button = tk.Button(root, text="Start Download", command=start_download, bg="green", fg="white")
download_button.grid(row=6, column=1, pady=10)

# Clear Button
clear_button = tk.Button(root, text="Clear", command=clear_logs, bg="red", fg="white")
clear_button.grid(row=6, column=2, pady=10)

# Run the application
root.mainloop()
