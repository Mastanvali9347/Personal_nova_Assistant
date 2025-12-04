import os
import time
import threading
import platform
import webbrowser
import urllib.parse
from pathlib import Path

import speech_recognition as sr
import pyttsx3
import pywhatkit
import tkinter as tk

MY_NAME = "Mastan"
LISTEN_SECONDS = 5       # seconds per listen attempt


# TTS engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 160)

def speak(text):
    print("[Nova]:", text)
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)
def speak_async(text):
    threading.Thread(target=speak, args=(text,)).start()
    print("[Nova]:", text)
    # Add any additional async handling here


# Simple pulsing circle GUI
class NovaGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Nova Assistant")
        self.w, self.h = 420, 460
        self.root.geometry(f"{self.w}x{self.h}")
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h, bg="#0f1226", highlightthickness=0)
        self.canvas.pack()
        self.phase = 0.0
        self.status = "idle"   # idle, listening, ready, denied
        self.message = "Say your name to trigger me"
        self.running = True
        self._update()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def set_status(self, status, message=None, timeout_ms=1200):
        self.status = status
        if message:
            self.message = message
        if timeout_ms:
            self.root.after(timeout_ms, self._reset)

    def _reset(self):
        self.status = "idle"
        self.message = "Say your name to trigger me"

    def _draw(self):
        self.canvas.delete("all")
        cx, cy = self.w//2, self.h//2 - 20
        pulse = ( ( (self.phase % (2*3.14159)) ) )
        # make a smooth pulse 0..1
        import math
        p = (math.sin(self.phase) + 1)/2
        r = 50 + p * 90
        if self.status == "idle":
            outline = "#2cd6c8"
            fill = "#11112a"
        elif self.status == "listening":
            outline = "#fce6b5"
            fill = "#2a240d"
        elif self.status == "ready":
            outline = "#3ddc84"
            fill = "#042a14"
        elif self.status == "denied":
            outline = "#ff4d4d"
            fill = "#2a0b0b"
        else:
            outline = "#888"
            fill = "#111"

        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=6)
        self.canvas.create_oval(cx - r*0.55, cy - r*0.55, cx + r*0.55, cy + r*0.55, fill=fill, outline="")
        inner = 12 + p*6
        self.canvas.create_oval(cx - inner, cy - inner, cx + inner, cy + inner, fill=outline, outline="")
        self.canvas.create_text(cx, cy + 170, text=self.message, fill="#fff", font=("Helvetica", 12))
        enroll_count_text = f"Listening (name: {MY_NAME})"
        self.canvas.create_text(cx, self.h - 20, text=enroll_count_text, fill="#aaa", font=("Helvetica", 9))

    def _update(self):
        if not self.running:
            return
        self.phase += 0.12
        self._draw()
        self.root.after(60, self._update)

    def close(self):
        self.running = False
        try:
            self.root.quit()
        except:
            pass

    def mainloop(self):
        self.root.mainloop()

    def speak_async(self, text):
        threading.Thread(target=self.speak, args=(text,)).start()
        print("[Nova]:", text)
        # Add any additional async handling here
        

# Command execution (safe)
def execute_command(text):
    t = text.lower().strip()
    print("[Command request] " + t)
    if t == "":
        return "No command captured."

    # play / youtube search
    if t.startswith("play ") or "youtube" in t:
        if t.startswith("play "):
            q = t[5:].strip()
            try:
                pywhatkit.playonyt(q)
                return f"Playing {q} on YouTube"
            except Exception:
                url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q)
                webbrowser.open(url)
                return f"Searching YouTube for {q}"
        else:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube"

    # google search
    if t.startswith("search ") or "search google for" in t or "google " in t:
        q = t.replace("search google for", "").replace("search", "").replace("google", "").strip()
        if q == "":
            return "What should I search?"
        url = "https://www.google.com/search?q=" + urllib.parse.quote(q)
        webbrowser.open(url)
        return f"Searching Google for {q}"

    # file manager
    if "file manager" in t or "open files" in t or "open explorer" in t or "open file" in t:
        try:
            plat = platform.system().lower()
            if "windows" in plat:
                os.startfile(os.path.expanduser("~"))
            elif "darwin" in plat:
                os.system("open ~")
            else:
                os.system("xdg-open ~")
            return "Opening file manager"
        except Exception as e:
            return f"Failed to open file manager: {e}"

    # whatsapp
    if "open whatsapp" in t:
        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp Web"
    # facebook
    if "open facebook" in t:
        webbrowser.open("https://facebook.com")
        return "Opening Facebook"
    # instagram
    if "open instagram" in t or "open insta" in t:
        webbrowser.open("https://instagram.com")
        return "Opening Instagram"
    # twitter
    if "open twitter" in t:
        webbrowser.open("https://twitter.com")
        return "Opening Twitter"
    # linkedin
    if "open linkedin" in t:
        webbrowser.open("https://linkedin.com")
        return "Opening LinkedIn"
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(t))
    return f"Searched web for: {t}"

# Listening thread
def listener_thread(gui):
    recognizer = sr.Recognizer()
    mic = None
    try:
        mic = sr.Microphone()  # use default microphone
    except Exception as e:
        print("Microphone error:", e)
        speak("Microphone not found or PyAudio missing. Please install PyAudio and try again.")
        gui.set_status("denied", "Microphone error")
        return

    # calibrate for ambient noise once
    with mic as source:
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
        except Exception as e:
            print("Calibration error:", e)

    speak("Nova is online. Say your name to activate.")
    while gui.running:
        try:
            gui.set_status("listening", "Listening for your name...", timeout_ms=2000)
            with mic as source:
                audio = recognizer.listen(source, phrase_time_limit=LISTEN_SECONDS)
            try:
                heard = recognizer.recognize_google(audio).lower()
            except sr.UnknownValueError:
                heard = ""
            except Exception as e:
                print("STT error:", e)
                heard = ""

            if heard:
                print("[Heard]:", heard)
            # check if your name is in the transcript
            if MY_NAME.lower() in heard:
                gui.set_status("ready", "Name detected. Listening for command...", timeout_ms=4000)
                speak("Yes, I'm listening.")
                # Listen for a command
                with mic as source:
                    audio2 = recognizer.listen(source, phrase_time_limit=6)
                try:
                    cmd = recognizer.recognize_google(audio2)
                except sr.UnknownValueError:
                    cmd = ""
                except Exception as e:
                    print("STT error (cmd):", e)
                    cmd = ""
                if cmd.strip() == "":
                    speak("I couldn't understand the command. Please try again.")
                    continue
                result = execute_command(cmd)
                speak(result)
            else:
                # optional: do not announce on unrecognized voices
                print("Name not detected in speech.")
                # show brief denied state but do not speak loudly
                gui.set_status("denied", "Not your name - ignoring", timeout_ms=900)
                # a small pause before next listen
                time.sleep(0.2)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Listener loop error:", e)
            time.sleep(0.5)
            continue

# ---- main ----
def main():
    gui = NovaGUI()
    t = threading.Thread(target=listener_thread, args=(gui,), daemon=True)
    t.start()
    try:
        gui.mainloop()
    except KeyboardInterrupt:
        pass
    gui.close()
    t.join(timeout=1)
    speak("Nova stopped.")

if __name__ == "__main__":
    main()
