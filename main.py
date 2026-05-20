from ultralytics import YOLO
from pathlib import Path
import tkinter as tk
from PIL import Image
from PIL import ImageGrab
import pytesseract
import pyautogui
from gtts import gTTS
import pyttsx3
import os
import sys
import platform
import threading
from playsound3 import playsound
from tkinter import messagebox
import urllib.request

BASE_DIR = Path(__file__).parent
FLAG_PATH = BASE_DIR / ".model_installed"

# ─────────────────────────────────────────────
# Set Tesseract path based on OS
# ─────────────────────────────────────────────
OS = platform.system()

if OS == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
elif OS == "Darwin":
    # Homebrew installs tesseract here on macOS
    pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
    # Apple Silicon Homebrew path
    if not Path(pytesseract.pytesseract.tesseract_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
# Linux: tesseract is on PATH by default, no need to set

SPEECH_PATH = BASE_DIR / "speech.mp3"
SS_PATH     = BASE_DIR / "screenshot" / "ss.jpg"
TEXT_PATH   = BASE_DIR / "screenshot" / "text.jpg"
def install_model(silent):
    url = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8x.pt"
    destination = BASE_DIR / "yolov8x.pt"

    def download():
        try:
            if not destination.exists():
                if not silent:
                    messagebox.showinfo("Installing...", "Downloading yolov8x.pt...")
                urllib.request.urlretrieve(url, destination)
                if not silent:
                    messagebox.showinfo("Installing...", "Done!")
            else:
                if not silent:
                    messagebox.showinfo("Installing...", "yolov8x.pt already exists, skipping download.")
            FLAG_PATH.touch()  # only run if no exception
        except Exception as e:
            print(f"Download failed: {e}")
            if not silent:
                messagebox.showerror("Error", f"Download failed: {e}")

    threading.Thread(target=download, daemon=True).start()

def first_run_check():
    flag_exists = FLAG_PATH.exists()
    messagebox.showinfo("Debug", f"FLAG_PATH: {FLAG_PATH}\nFlag exists: {flag_exists}")
    if not flag_exists:
        messagebox.showinfo("Debug", "First run detected, installing...")
        install_model(False)
    else:
        messagebox.showinfo("Debug", "Flag found, skipping install.")


def speak_text(text, use_gtts):
    if not text.strip():
        return

    def run_speech():
        if use_gtts:
            try:
                tts = gTTS(text=text, lang='en')
                tts.save(str(SPEECH_PATH))
                playsound(str(SPEECH_PATH))
            except Exception as e:
                print(f"gTTS Error: {e}")
        else:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()

    threading.Thread(target=run_speech, daemon=True).start()

def clean_files():
    for f in [SPEECH_PATH, SS_PATH, TEXT_PATH]:
        try:
            if f.exists():
                os.remove(f)
        except Exception as e:
            print(f"Could not remove {f}: {e}")
    print("files cleaned")

class SnippingTool:
    #install_model() just used to test OS detecting
    def __init__(self, callback):
        self.callback = callback
        self.snip_surface = tk.Toplevel()
        self.snip_surface.attributes('-alpha', 0.3)
        self.snip_surface.attributes('-fullscreen', True)
        self.snip_surface.attributes("-topmost", True)
        self.snip_surface.config(cursor="cross")

        self.canvas = tk.Canvas(self.snip_surface, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=2)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        self.snip_surface.destroy()

        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        width, height = x2 - x1, y2 - y1

        if width > 0 and height > 0:
            if OS == "Windows":
                img = ImageGrab.grab(bbox=(x1, y1, x1 + width, y1 + height))
            elif OS == "Linux":
                messagebox.showinfo("Debug","Linux detected")
            elif OS == "Darwin":
                messagebox.showinfo("Debug","MacOS detected")
            self.callback(img)
        else:
            root.deiconify()

def runobjectrecognition():
    root.withdraw()

    def process_yolo(img):
        SS_PATH.parent.mkdir(parents=True, exist_ok=True)
        img.save(SS_PATH)
        print(f"Image saved. Running YOLO on {SS_PATH}...")

        model = YOLO("yolov8x.pt")
        results = model(str(SS_PATH))

        root.deiconify()
        clean_files()

    SnippingTool(process_yolo)

def runtextrecognition(use_gtts):
    root.withdraw()

    def process_ocr(img):
        TEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
        img.save(TEXT_PATH)
        print(f"Image saved. Running OCR on {TEXT_PATH}...")

        text = pytesseract.image_to_string(Image.open(TEXT_PATH))
        print("--- OCR RESULT ---")
        print(text)
        speak_text(text, use_gtts)

        root.deiconify()
        clean_files()

    SnippingTool(process_ocr)

# ─────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("Intelligent Screen Reader")
root.geometry("300x300")

use_gtts_var = tk.BooleanVar(value=False)

tk.Button(root, text="Start Object Recognition", width=25, command=runobjectrecognition).pack(pady=5)
tk.Button(root, text="Start Text Recognition",   width=25, command=lambda: runtextrecognition(use_gtts_var.get())).pack(pady=5)
tk.Button(root, text="Stop",                      width=25, command=root.destroy).pack(pady=5)
tk.Button(root, text="Install Model",                      width=25, command=lambda: install_model(False)).pack(pady=5)  #Debug button, used for testing

tk.Checkbutton(root, text="Use High Quality Voice, non-local (gTTS)", variable=use_gtts_var).pack(pady=5)

root.bind("<F8>",  lambda event: runtextrecognition(use_gtts_var.get()))
root.bind("<F9>",  lambda event: runobjectrecognition())
root.bind("<F10>", lambda event: root.destroy())


root.after(100, first_run_check)
root.mainloop()

#if OS == "Windows":
#        messagebox.showinfo("Debug","Windows")
#    elif OS == "Linux":
#        messagebox.showinfo("Debug","Linux detected")
#    elif OS == "Darwin":
#        messagebox.showinfo("Debug","MacOS detected")
