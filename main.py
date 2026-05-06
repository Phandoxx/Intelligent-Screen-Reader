from ultralytics import YOLO
from pathlib import Path
import tkinter as tk
from PIL import Image
import pytesseract
import pyautogui
from gtts import gTTS
import pyttsx3
import os
import threading
from playsound3 import playsound

# Sets Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def speak_text(text, use_gtts):
    if not text.strip():
        return

    def run_speech():
        if use_gtts:
            try:
                tts = gTTS(text=text, lang='en')
                tts.save("speech.mp3")
                playsound("speech.mp3")
            except Exception as e:
                print(f"gTTS Error: {e}")
        else:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()

    # Run in a thread so the ui doesn't freeze
    threading.Thread(target=run_speech, daemon=True).start()

def clean_files():
    BASE_DIR = Path(__file__).parent
    ss_path = BASE_DIR / "screenshot" / "ss.jpg"
    ss_path.parent.mkdir(parents=True, exist_ok=True)

    text_path = BASE_DIR / "screenshot" / "text.jpg"
    text_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        os.remove("speech.mp3")
        os.remove(ss_path)
        os.remove(text_path)
    finally:
        print("files cleaned")

class SnippingTool:
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
            img = pyautogui.screenshot(region=(x1, y1, width, height))
            self.callback(img)
        else:
            root.deiconify() # Bring back if user just clicked without dragging

def runobjectrecognition():
    root.withdraw() # Hide ui while selecting (stops it getting in the way)

    def process_yolo(img):
        BASE_DIR = Path(__file__).parent
        img_path = BASE_DIR / "screenshot" / "ss.jpg"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        
        img.save(img_path)
        print(f"Image saved. Running YOLO on {img_path}...")
        
        model = YOLO("yolov8x.pt")
        results = model(str(img_path))
        # results.show()
        
        root.deiconify() # Show ui again
        clean_files()

    SnippingTool(process_yolo)

def runtextrecognition(use_gtts):
    root.withdraw() # Hide ui while selecting

    def process_ocr(img):
        BASE_DIR = Path(__file__).parent
        img_path = BASE_DIR / "screenshot" / "text.jpg"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        
        img.save(img_path)
        print(f"Image saved. Running OCR on {img_path}...")

        text = pytesseract.image_to_string(Image.open(img_path))
        print("--- OCR RESULT ---")
        print(text)
        speak_text(text, use_gtts)
        
        root.deiconify() # Show ui again
        clean_files()

    SnippingTool(process_ocr)

# Main UI Setup

root = tk.Tk()
root.title("Intelligent Screen Reader")
root.geometry("300x300")

use_gtts_var = tk.BooleanVar(value=False)

tk.Button(root, text="Start Object Recognition", width=25, command=runobjectrecognition).pack(pady=5)
tk.Button(root, text="Start Text Recognition", width=25, command=lambda: runtextrecognition(use_gtts_var.get())).pack(pady=5)
tk.Button(root, text="Stop", width=25, command=root.destroy).pack(pady=5)

tk.Checkbutton(root, text="Use High Quality Voice, non-local (gTTS)", variable=use_gtts_var).pack(pady=5)

root.bind("<F8>", lambda event: runtextrecognition(use_gtts_var.get()))
root.bind("<F9>", lambda event: runobjectrecognition())
root.bind("<F10>", lambda event: root.destroy())

root.mainloop()