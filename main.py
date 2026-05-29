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
import subprocess, tempfile
from PIL import ImageTk
import customtkinter

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
    # rootle Silicon Homebrew path
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
            #set_display_text(f"Download failed: {e}")
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
# ─────────────────────────────────────────────
# Set Windows Snipping tool
# ─────────────────────────────────────────────
    if OS == "Windows":
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
                img = ImageGrab.grab(bbox=(x1, y1, x1 + width, y1 + height))
                self.callback(img)
            else:
                root.deiconify()
# ─────────────────────────────────────────────
# Set Linux snipping tool
# ─────────────────────────────────────────────
    elif OS == "Linux":
        SESSION_TYPE    = os.environ.get("XDG_SESSION_TYPE", "").lower()
        DESKTOP_SESSION = os.environ.get("DESKTOP_SESSION",  "").lower()

        def __init__(self, callback):
            self.callback = callback
            if SnippingTool.SESSION_TYPE == "wayland":
                self._init_wayland()
            else:
                self._init_x11()

        # ──────────────────────────────────────────────────────────────
        # WAYLAND
        # Detect desktop environment and use the rootropriate native tool:
        #   KDE Plasma  → spectacle
        #   GNOME       → gnome-screenshot
        #   wlroots     → grim + slurp  (Sway, Hyprland, etc.)
        #   Unknown     → try each in order
        # All tools open their own native region selector UI —
        # no tkinter overlay needed on Wayland.
        # ──────────────────────────────────────────────────────────────
        def _init_wayland(self):
            def _tool_exists(name):
                return subprocess.run(
                    ['which', name],
                    capture_output=True
                ).returncode == 0

            def capture():
                try:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                        tmp = f.name
                    os.unlink(tmp)

                    desktop = SnippingTool.DESKTOP_SESSION
                    captured = False

                    # ── KDE Plasma Wayland ──
                    if not captured and ('plasma' in desktop or 'kde' in desktop):
                        if _tool_exists('spectacle'):
                            result = subprocess.run(
                                ['spectacle', '-r', '-b', '-n', '-o', tmp],
                                capture_output=True, text=True
                            )
                            if result.returncode == 0 and os.path.exists(tmp):
                                captured = True
                            else:
                                raise Exception(
                                    f'spectacle failed: {result.stderr.strip()}\n\n'
                                    'Make sure spectacle is installed:\n'
                                    '  sudo apt install spectacle'
                                )
                        else:
                            raise FileNotFoundError('spectacle')

                    # ── GNOME Wayland ──
                    if not captured and 'gnome' in desktop:
                        if _tool_exists('gnome-screenshot'):
                            result = subprocess.run(
                                ['gnome-screenshot', '-a', '-f', tmp],
                                capture_output=True, text=True
                            )
                            if result.returncode == 0 and os.path.exists(tmp):
                                captured = True
                            else:
                                raise Exception(
                                    f'gnome-screenshot failed: {result.stderr.strip()}\n\n'
                                    'Make sure gnome-screenshot is installed:\n'
                                    '  sudo apt install gnome-screenshot'
                                )
                        else:
                            raise FileNotFoundError('gnome-screenshot')

                    # ── wlroots Wayland (Sway, Hyprland, etc.) ──
                    if not captured and _tool_exists('grim') and _tool_exists('slurp'):
                        slurp = subprocess.run(
                            ['slurp'],
                            capture_output=True, text=True
                        )
                        if slurp.returncode != 0:
                            # User cancelled
                            root.after(0, root.deiconify)
                            return
                        region = slurp.stdout.strip()
                        result = subprocess.run(
                            ['grim', '-g', region, tmp],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0 and os.path.exists(tmp):
                            captured = True
                        else:
                            raise Exception(f'grim failed: {result.stderr.strip()}')

                    # ── Unknown Wayland — try everything ──
                    if not captured:
                        # Try spectacle
                        if _tool_exists('spectacle'):
                            result = subprocess.run(
                                ['spectacle', '-r', '-b', '-n', '-o', tmp],
                                capture_output=True, text=True
                            )
                            if result.returncode == 0 and os.path.exists(tmp):
                                captured = True

                        # Try gnome-screenshot
                        if not captured and _tool_exists('gnome-screenshot'):
                            result = subprocess.run(
                                ['gnome-screenshot', '-a', '-f', tmp],
                                capture_output=True, text=True
                            )
                            if result.returncode == 0 and os.path.exists(tmp):
                                captured = True

                        # Try grim + slurp
                        if not captured and _tool_exists('grim') and _tool_exists('slurp'):
                            slurp = subprocess.run(
                                ['slurp'], capture_output=True, text=True
                            )
                            if slurp.returncode == 0:
                                region = slurp.stdout.strip()
                                result = subprocess.run(
                                    ['grim', '-g', region, tmp],
                                    capture_output=True, text=True
                                )
                                if result.returncode == 0 and os.path.exists(tmp):
                                    captured = True

                        if not captured:
                            raise FileNotFoundError(
                                'No supported Wayland screenshot tool found.\n\n'
                                'Install the one for your desktop:\n'
                                '  KDE Plasma:         sudo apt install spectacle\n'
                                '  GNOME:              sudo apt install gnome-screenshot\n'
                                '  Sway/Hyprland:      sudo apt install grim slurp'
                            )

                    img = Image.open(tmp).copy()
                    os.unlink(tmp)
                    root.after(0, lambda: self.callback(img))

                except subprocess.CalledProcessError:
                    # User cancelled a native selector
                    root.after(0, root.deiconify)
                except FileNotFoundError as e:
                    name = str(e)
                    if name in ('spectacle', 'gnome-screenshot'):
                        msg = (
                            f'"{name}" is not installed.\n\n'
                            f'Install it with:\n  sudo apt install {name}'
                        )
                    else:
                        msg = name  # already a full message from the unknown branch
                    root.after(0, lambda: messagebox.showerror('Missing dependency', msg))
                    root.after(0, root.deiconify)
                except Exception as e:
                    msg = str(e)
                    root.after(0, lambda: messagebox.showerror('Capture error', msg))
                    root.after(0, root.deiconify)

            root.withdraw()
            threading.Thread(target=capture, daemon=True).start()

        # ──────────────────────────────────────────────────────────────
        # X11
        # Takes a desktop screenshot before showing the overlay so the
        # user can see their screen through it. Crops the selected
        # region from that image — no second scrot call needed.
        # ──────────────────────────────────────────────────────────────
        def _init_x11(self):
            try:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    bg_tmp = f.name
                os.unlink(bg_tmp)
                subprocess.run(['scrot', bg_tmp], check=True)
                self.bg_image = Image.open(bg_tmp).copy()
                os.unlink(bg_tmp)
            except FileNotFoundError:
                messagebox.showerror(
                    'Missing dependency',
                    'scrot is not installed.\n\n'
                    'Install it with:\n  sudo apt install scrot\n'
                    '  sudo pacman -S scrot\n  sudo dnf install scrot'
                )
                root.deiconify()
                return
            except Exception as e:
                messagebox.showerror('Capture error', str(e))
                root.deiconify()
                return

            screen_w, screen_h = self.bg_image.size
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)

            self.snip_surface = tk.Toplevel()
            self.snip_surface.attributes('-fullscreen', True)
            self.snip_surface.attributes('-topmost', True)
            self.snip_surface.config(cursor='cross')

            self.canvas = tk.Canvas(
                self.snip_surface,
                cursor='cross',
                highlightthickness=0,
                width=screen_w,
                height=screen_h
            )
            self.canvas.pack(fill='both', expand=True)

            # Screenshot as background so user can see their screen
            self.canvas.create_image(0, 0, anchor='nw', image=self.bg_photo)
            # Dim overlay via stipple — works without a compositor
            self.canvas.create_rectangle(
                0, 0, screen_w, screen_h,
                fill='black', stipple='gray50', outline=''
            )

            self.start_x = None
            self.start_y = None
            self.rect      = None
            self.highlight = None

            self.canvas.bind('<ButtonPress-1>',   self.on_button_press)
            self.canvas.bind('<B1-Motion>',       self.on_move_press)
            self.canvas.bind('<ButtonRelease-1>', self.on_button_release)
            self.snip_surface.bind('<Escape>', lambda e: self._cancel())

        def _cancel(self):
            self.snip_surface.destroy()
            root.deiconify()

        def on_button_press(self, event):
            self.start_x = event.x
            self.start_y = event.y
            self.highlight = self.canvas.create_rectangle(
                self.start_x, self.start_y, 1, 1,
                fill='', outline=''
            )
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, 1, 1,
                outline='white', width=2, dash=(4, 4)
            )

        def on_move_press(self, event):
            self.canvas.coords(self.rect,      self.start_x, self.start_y, event.x, event.y)
            self.canvas.coords(self.highlight, self.start_x, self.start_y, event.x, event.y)
            self.canvas.tag_raise(self.rect)

        def on_button_release(self, event):
            end_x, end_y = event.x, event.y
            self.snip_surface.destroy()

            x1 = min(self.start_x, end_x)
            y1 = min(self.start_y, end_y)
            x2 = max(self.start_x, end_x)
            y2 = max(self.start_y, end_y)

            if (x2 - x1) > 0 and (y2 - y1) > 0:
                # Crop from the pre-captured background — no second scrot call
                img = self.bg_image.crop((x1, y1, x2, y2))
                self.callback(img)
            else:
                root.deiconify()
# ─────────────────────────────────────────────
# Set MacOS (Darwin) snipping tool
# ─────────────────────────────────────────────
    elif OS == "Darwin":
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
                img = ImageGrab.grab(bbox=(x1, y1, x1 + width, y1 + height))
                self.callback(img)
            else:
                root.deiconify()


def runobjectrecognition():
    root.withdraw()
    def process_yolo(img):
        SS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(SS_PATH)
        #set_display_text(f"Image saved. Running YOLO on {SS_PATH}...")
        model = YOLO("yolov8x.pt")
        results = model(str(SS_PATH))
        root.deiconify()
        #clean_files() #remove for testing
    SnippingTool(process_yolo)

def runtextrecognition(use_gtts):
    root.withdraw()
    def process_ocr(img):
        TEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(TEXT_PATH)
        #set_display_text(f"Image saved. Running OCR on {TEXT_PATH}...")
        text = pytesseract.image_to_string(Image.open(TEXT_PATH))
        #set_display_text("--- OCR RESULT ---")
        set_display_text(text)
        speak_text(text, use_gtts)
        root.deiconify()
        #clean_files() #remove for testing
    SnippingTool(process_ocr)

# ─────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────
customtkinter.set_appearance_mode("System")  
customtkinter.set_default_color_theme("green")  

root = customtkinter.CTk()      
root.geometry("400x300")
root.title("Intelligent screen reader")

use_gtts_var = tk.BooleanVar(value=False)

# Create tabview
tabview = customtkinter.CTkTabview(
    root,
    segmented_button_selected_color="#4CAF50",
    segmented_button_selected_hover_color="#45a049",
    segmented_button_unselected_color="#2D7A30",
    segmented_button_unselected_hover_color="#367d39",
    segmented_button_fg_color="#2D7A30",
    text_color="black",
    corner_radius=0,
)
tabview.pack(fill="both", expand=True, padx=0, pady=0)

# Stretch tabs to full width
tabview._segmented_button.configure(corner_radius=0)
tabview._segmented_button.grid_configure(sticky="ew")
tabview._segmented_button.master.grid_columnconfigure(0, weight=1)

# Add tabs
tab1 = tabview.add("Settings")
tab2 = tabview.add("OCR/Object")

# Button style matching
btn_kwargs = dict(
    corner_radius=10,
    fg_color="#4CAF50",
    hover_color="#45a049",
    text_color="black",
)

def set_display_text(text):
    display_box.configure(state="normal")   # unlock
    display_box.delete("1.0", "end")        # clear
    display_box.insert("end", text)         # insert new text
    display_box.configure(state="disabled") # lock again

# Tab 1: Settings 
InstallButton = customtkinter.CTkButton(master=tab1, text="Install model", command=lambda: install_model(False), **btn_kwargs)
InstallButton.pack(pady=5)

GttsCheckbox = customtkinter.CTkCheckBox(tab1, text="Use High Quality Voice, non-local (gTTS)", variable=use_gtts_var)
GttsCheckbox.pack(pady=10)


# Tab 2: OCR/Object
ObjectRecogButton = customtkinter.CTkButton(master=tab2, text="Start Object Recognition", command=runobjectrecognition, **btn_kwargs)
ObjectRecogButton.pack(pady=5)

TextRecogButton = customtkinter.CTkButton(master=tab2, text="Start Text Recognition", command=lambda: runtextrecognition(use_gtts_var.get()), **btn_kwargs)
TextRecogButton.pack(pady=5)

display_box = customtkinter.CTkTextbox(tab2, height=80, state="disabled", wrap="word")
display_box.pack(fill="x", padx=10, pady=(5, 0))

# Stop button
tabview.pack(fill="both", expand=True, padx=0, pady=0)

StopButton = customtkinter.CTkButton(master=root, text="Stop", command=root.destroy, **btn_kwargs)
StopButton.pack(pady=5)

root.after(100, first_run_check)
root.mainloop()
