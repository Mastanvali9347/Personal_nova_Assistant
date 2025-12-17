import os
import sys
import time
import datetime
import threading
import platform
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import messagebox
import math
import random
import subprocess
import requests


import speech_recognition as sr
import pyttsx3
import pywhatkit
import wikipedia
import pyjokes
import pyautogui
import psutil
import screen_brightness_control as sbc
from bs4 import BeautifulSoup


AI_NAME = "Nova"
USER_NAME = "Hey Nova"
WAKE_WORD = "nova" 
THEME_COLOR = "#00f0ff"  # Cyberpunk Cyan
BG_COLOR = "#050505"     # Deep Black

# --- SOUND ENGINE ---
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

def speak(text):
    """Thread-safe speaking"""
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass

def speak_async(text, gui=None):
    if gui: gui.log_event(text, "bot")
    print(f"[{AI_NAME}]: {text}")
    threading.Thread(target=speak, args=(text,)).start()

# --- ADVANCED FEATURES ---

def get_weather():
    """Gets weather without an API key using wttr.in"""
    try:
        # Get location based on IP automatically
        ip_info = requests.get("https://ipinfo.io/json").json()
        city = ip_info['city']
        url = f"https://wttr.in/{city}?format=%C+%t"
        res = requests.get(url)
        return f"Weather in {city}: {res.text.strip()}"
    except:
        return "I couldn't retrieve the weather data."

def get_news():
    """Scrapes Google News for top 3 headlines"""
    try:
        url = 'https://news.google.com/rss'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, features='xml')
        items = soup.findAll('item')[0:3]
        news_str = ""
        for i, item in enumerate(items):
            news_str += f"Headline {i+1}: {item.title.text}. "
        return news_str
    except:
        return "I cannot access the news feed right now."

def set_brightness(level):
    """Sets screen brightness (0-100)"""
    try:
        sbc.set_brightness(level)
        return f"Brightness set to {level} percent."
    except:
        return "I cannot control brightness on this monitor."

def take_note(text):
    """Saves a note to a text file"""
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = "nova_notes.txt"
    with open(filename, "a") as f:
        f.write(f"[{date}] {text}\n")
    return "Note saved successfully."

def system_cleanup():
    """Simulates a system cleanup"""
    # Windows only - empty recycle bin
    if platform.system() == "Windows":
        try:
            subprocess.run(["powershell.exe", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], shell=True)
            return "Recycle bin emptied."
        except:
            pass
    return "Cleanup routine finished."

# --- MAPPINGS ---
SITES = {
    "google": "https://google.com", "youtube": "https://youtube.com",
    "github": "https://github.com", "linkedin": "https://linkedin.com",
    "chatgpt": "https://chat.openai.com", "netflix": "https://netflix.com",
    "whatsapp": "https://web.whatsapp.com", "instagram": "https://instagram.com"
}

# --- COMMAND PROCESSOR ---
def process_command(cmd, gui):
    cmd = cmd.lower()
    gui.log_event(cmd, "user")

    # 1. Conversation
    if any(x in cmd for x in ["hello", "hi", "wake up"]):
        return f"Online and ready, {USER_NAME}."
    
    if any(x in cmd for x in ["exit", "shutdown", "goodbye"]):
        gui.close_app()
        return "Shutting down systems."

    # 2. System Hardware
    if "brightness" in cmd:
        # Extract numbers
        import re
        nums = re.findall(r'\d+', cmd)
        if nums:
            val = int(nums[0])
            return set_brightness(val)
        else:
            return "Please specify a brightness level."

    if "volume" in cmd:
        if "up" in cmd:
            pyautogui.press("volumeup", presses=5)
            return "Volume increased."
        elif "down" in cmd:
            pyautogui.press("volumedown", presses=5)
            return "Volume decreased."
        elif "mute" in cmd:
            pyautogui.press("volumemute")
            return "Audio muted."

    if "battery" in cmd or "power" in cmd:
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery is at {battery.percent} percent."
        return "Desktop detected. No battery info."

    # 3. Information & Internet
    if "weather" in cmd:
        speak_async("Fetching meteorological data...", gui)
        return get_weather()
    
    if "news" in cmd or "headlines" in cmd:
        speak_async("Accessing global feeds...", gui)
        return get_news()

    if "time" in cmd:
        return f"Current time is {datetime.datetime.now().strftime('%H:%M')}"

    if "wikipedia" in cmd or "who is" in cmd:
        query = cmd.replace("wikipedia", "").replace("who is", "").strip()
        try:
            res = wikipedia.summary(query, sentences=2)
            return res
        except:
            return "Database query failed."

    # 4. Utilities
    if "write a note" in cmd or "take a note" in cmd:
        speak_async("What should I write?", gui)
        # We need a quick listen here - tricky in threaded env, 
        # so we'll just parse the rest of the string if it exists
        content = cmd.replace("write a note", "").replace("take a note", "").strip()
        if content:
            return take_note(content)
        else:
            return "Command incomplete. Say 'write a note [text]' next time."

    if "screenshot" in cmd:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pyautogui.screenshot(f"scr_{ts}.png")
        return "Screenshot captured."

    if "cleanup" in cmd or "clean system" in cmd:
        return system_cleanup()

    if "play" in cmd:
        song = cmd.replace("play", "").strip()
        speak_async(f"Playing {song}", gui)
        pywhatkit.playonyt(song)
        return "Media player launched."

    # 5. Apps/Sites
    if "open" in cmd:
        for site, url in SITES.items():
            if site in cmd:
                webbrowser.open(url)
                return f"Opening {site}."
        # Generic App launch (Windows)
        target = cmd.replace("open", "").strip()
        pyautogui.press("win")
        time.sleep(0.2)
        pyautogui.write(target)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Attempting to launch {target}."

    # Fallback
    webbrowser.open(f"https://google.com/search?q={cmd}")
    return f"Searching Google for {cmd}"

# --- ARC REACTOR GUI ---
class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NOVA A.I.")
        self.w, self.h = 600, 700
        self.root.geometry(f"{self.w}x{self.h}")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        
        # Center on screen
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws/2) - (self.w/2)
        y = (hs/2) - (self.h/2)
        self.root.geometry('%dx%d+%d+%d' % (self.w, self.h, x, y))

        # Canvas for Arc Reactor
        self.canvas = tk.Canvas(self.root, width=self.w, height=400, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(pady=20)

        # Status / Chat Area
        self.status_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.status_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.log_box = tk.Text(self.status_frame, bg="#0a0a0a", fg=THEME_COLOR, 
                               font=("Consolas", 10), bd=1, relief="flat", state="disabled")
        self.log_box.pack(fill="both", expand=True)

        # Bottom Info Bar
        self.info_lbl = tk.Label(self.root, text="SYSTEM ONLINE | WAITING FOR INPUT", 
                                 font=("Arial", 8, "bold"), bg=BG_COLOR, fg="#444")
        self.info_lbl.pack(side="bottom", pady=5)

        self.running = True
        self.phase = 0.0
        self.state = "idle" # idle, listening, speaking
        
        # Start animations
        self._animate()
        self._update_hud()
        
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def log_event(self, text, sender):
        self.log_box.config(state="normal")
        prefix = ">> " if sender == "user" else f"[{AI_NAME}] "
        color = "#ffffff" if sender == "user" else THEME_COLOR
        
        self.log_box.tag_config("user_tag", foreground="#aaaaaa")
        self.log_box.tag_config("bot_tag", foreground=THEME_COLOR)
        
        tag = "user_tag" if sender == "user" else "bot_tag"
        self.log_box.insert(tk.END, f"{prefix}{text}\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def set_state(self, state):
        self.state = state
        if state == "listening":
            self.info_lbl.config(text="LISTENING...", fg="#ff0")
        elif state == "processing":
            self.info_lbl.config(text="PROCESSING DATA...", fg=THEME_COLOR)
        else:
            self.info_lbl.config(text="SYSTEM READY", fg="#444")

    def _update_hud(self):
        if not self.running: return
        # System Stats Update
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Draw HUD text on canvas
        self.canvas.delete("hud")
        self.canvas.create_text(50, 20, text=f"CPU: {cpu}%", fill=THEME_COLOR, font=("Consolas", 10), tags="hud", anchor="w")
        self.canvas.create_text(50, 40, text=f"RAM: {ram}%", fill=THEME_COLOR, font=("Consolas", 10), tags="hud", anchor="w")
        self.canvas.create_text(self.w-50, 20, text=time_str, fill="#fff", font=("Consolas", 12, "bold"), tags="hud", anchor="e")
        
        self.root.after(1000, self._update_hud)

    def _animate(self):
        if not self.running: return
        self.canvas.delete("reactor")
        cx, cy = self.w // 2, 200
        self.phase += 0.1
        
        # Determine Activity Level
        if self.state == "listening":
            pulse_speed = 0.4
            color = "#ffdd00" # Yellow
            noise = random.randint(-5, 5)
        elif self.state == "processing":
            pulse_speed = 0.8
            color = "#ff0055" # Red/Pink
            noise = 0
        else:
            pulse_speed = 0.1
            color = THEME_COLOR # Cyan
            noise = 0

        # Pulse Math
        pulse = (math.sin(self.phase * pulse_speed) + 1) / 2
        r = 80 + (pulse * 20) + noise
        
        # 1. Outer Rotating Ring (Triangles)
        for i in range(0, 360, 60):
            angle = math.radians(i + (self.phase * 5))
            x1 = cx + math.cos(angle) * (r + 40)
            y1 = cy + math.sin(angle) * (r + 40)
            x2 = cx + math.cos(angle) * (r + 30)
            y2 = cy + math.sin(angle) * (r + 30)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2, tags="reactor")

        # 2. Main Glow Circle
        # Simulate glow by stacking translucent circles (tk doesn't support alpha well, using stipples or widths)
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=4, tags="reactor")
        self.canvas.create_oval(cx-(r-10), cy-(r-10), cx+(r-10), cy+(r-10), outline=color, width=2, tags="reactor")
        
        # 3. Core
        core_r = 30 + (pulse * 5)
        self.canvas.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r, fill=color, outline="#fff", width=2, tags="reactor")

        self.root.after(40, self._animate)

    def close_app(self):
        self.running = False
        try:
            self.root.destroy()
        except:
            pass
        os._exit(0)
    
    def start(self):
        self.root.mainloop()

# --- MAIN LOGIC THREAD ---
def brain_thread(gui):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 2000
    recognizer.dynamic_energy_threshold = True

    try:
        mic = sr.Microphone()
    except:
        gui.log_event("CRITICAL: NO MICROPHONE FOUND", "bot")
        return

    # Calibration
    gui.set_state("processing")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
    
    gui.set_state("idle")
    speak_async("Core systems initialized. Waiting for command.", gui)

    while gui.running:
        try:
            with mic as source:
                # 1. Listen for Wake Word (passive)
                try:
                    audio = recognizer.listen(source, timeout=1.5, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                except:
                    continue
                
                if WAKE_WORD in text:
                    # 2. Active Command Listening
                    gui.set_state("listening")
                    speak_async("Yes?", gui)
                    
                    try:
                        cmd_audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                        cmd_text = recognizer.recognize_google(cmd_audio)
                        
                        gui.set_state("processing")
                        response = process_command(cmd_text, gui)
                        
                        speak_async(response, gui)
                        
                        # Wait for speaking to finish (roughly)
                        time.sleep(len(response.split()) * 0.4) 
                        gui.set_state("idle")
                        
                    except sr.WaitTimeoutError:
                        speak_async("I didn't hear a command.", gui)
                        gui.set_state("idle")
                    except sr.UnknownValueError:
                        speak_async("I didn't understand.", gui)
                        gui.set_state("idle")
                    except Exception as e:
                        print(f"Error: {e}")
                        gui.set_state("idle")

        except Exception as e:
            print(f"Loop Error: {e}")
            gui.set_state("idle")

if __name__ == "__main__":
    app = JarvisGUI()
    t = threading.Thread(target=brain_thread, args=(app,), daemon=True)
    t.start()
    app.start()