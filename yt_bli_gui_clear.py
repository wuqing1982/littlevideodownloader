import os
import subprocess
import threading
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


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
    thread = threading.Thread(target=download_video)
    thread.start()


def download_video():
    global log_text
    video_url = entry_url.get().strip()
    if not video_url or not validate_url(video_url):
        messagebox.showerror("Error", "Please provide a valid YouTube or Bilibili video URL.")
        return

    platform = determine_platform(video_url)
    cookie_file = entry_cookie.get().strip()
    download_path = entry_path.get().strip()

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    log_file_path = os.path.join(download_path, "download_log.txt")

    if platform == "YouTube":
        command = [
            "yt-dlp",
            "--cookies", cookie_file,
            "-f", "bestvideo[height<=1080]+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(download_path, "%(title)s.%(ext)s"),
            "--verbose",
            video_url
        ]
    elif platform == "Bilibili":
        command = [
            "yt-dlp",
            "--cookies", cookie_file,
            "-f", "bv[height<=1080]+ba/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(download_path, "%(title)s.%(ext)s"),
            "--verbose",
            video_url
        ]
    else:
        messagebox.showerror("Error", "Unsupported platform.")
        return

    try:
        if log_text:
            log_text.insert(tk.END, f"Generated command: {' '.join(command)}\n")
            log_text.insert(tk.END, "Starting download...\n")

        with open(log_file_path, "w") as log_file:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            for line in process.stdout:
                log_file.write(line)

                if "[download]" in line and "%" in line:
                    progress = parse_progress(line)
                    if progress is not None:
                        progress_bar["value"] = progress
                        progress_bar.update_idletasks()

                if log_text:
                    log_text.insert(tk.END, line)
                    log_text.see(tk.END)
            process.wait()

        if process.returncode == 0:
            progress_bar["value"] = 100
            messagebox.showinfo("Success", f"Video downloaded successfully to {download_path}\nLog saved at {log_file_path}")
        else:
            messagebox.showerror("Error", f"Download failed. Check the log file at {log_file_path} for details.")
    except Exception as e:
        progress_bar["value"] = 0
        messagebox.showerror("Error", f"An error occurred: {e}")


def clear_logs():
    """
    Clear the log text and reset the progress bar.
    """
    log_text.delete("1.0", tk.END)  # Clear log
    progress_bar["value"] = 0  # Reset progress bar


# GUI Setup
root = tk.Tk()
root.title("Video Downloader (YouTube & Bilibili)")

# URL Input
tk.Label(root, text="Video URL:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_url = tk.Entry(root, width=50)
entry_url.grid(row=0, column=1, padx=5, pady=5)

# Cookie File Input
tk.Label(root, text="Cookie File:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_cookie = tk.Entry(root, width=50)
entry_cookie.grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_cookie_file).grid(row=1, column=2, padx=5, pady=5)

# Download Path Input
tk.Label(root, text="Download Path:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_download_path).grid(row=2, column=2, padx=5, pady=5)

# Progress Bar
progress_label = tk.Label(root, text="Progress:")
progress_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=3, column=1, columnspan=2, padx=5, pady=5)

# Log Output
log_text = tk.Text(root, height=15, width=70, state="normal")
log_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

# Download Button
download_button = tk.Button(root, text="Start Download", command=start_download, bg="green", fg="white")
download_button.grid(row=5, column=1, pady=10)

# Clear Button
clear_button = tk.Button(root, text="Clear", command=clear_logs, bg="red", fg="white")
clear_button.grid(row=5, column=2, pady=10)

# Run the application
root.mainloop()
