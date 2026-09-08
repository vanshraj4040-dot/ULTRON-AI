import os
import re
import asyncio
import sys
import json
import math
import difflib
import time
import base64
import glob
import uuid
import socket
import random
import threading
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import ssl
try:
    import pygame
except Exception:
    pygame = None
    print("[ULTRON CORE] Running in headless cloud mode (Pygame disabled).")
    
import webbrowser
import shutil
from gtts import gTTS
from ultron_db import kb_engine

# Optional pyttsx3 import for Offline Deep Male Voice TTS
try:
    import pyttsx3
    OFFLINE_TTS_AVAILABLE = True
except ImportError:
    OFFLINE_TTS_AVAILABLE = False

# ==============================================================================
# CHECK PYNIUS AVAILABILITY (ANDROID NATIVE INTENTS)
# ==============================================================================
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    String = autoclass('java.lang.String')
    Uri = autoclass('android.net.Uri')
    PYNIUS_READY = True
except Exception:
    PYNIUS_READY = False

# ==============================================================================
# APP PACKAGE & INTENT CONFIGURATION MAP
# ==============================================================================
APP_MAP = {
    "whatsapp": {
        "package": "com.whatsapp",
        "activity": "com.whatsapp.Main",
        "scheme": "whatsapp://"
    },
    "youtube": {
        "package": "com.google.android.youtube",
        "activity": "com.google.android.youtube.MainActivity",
        "scheme": "vnd.youtube://"
    },
    "instagram": {
        "package": "com.instagram.android",
        "activity": "com.instagram.android.activity.MainTabActivity",
        "scheme": "https://www.instagram.com/"
    },
    "chrome": {
        "package": "com.android.chrome",
        "activity": "com.google.android.apps.chrome.Main",
        "scheme": "googlechrome://"
    },
    "calculator": {
        "package": "com.google.android.calculator",
        "activity": "com.android.calculator2.Calculator",
        "scheme": None
    },
    "settings": {
        "package": "com.android.settings",
        "activity": "com.android.settings.Settings",
        "scheme": None
    }
}

# ==============================================================================
# TRIPLE-SOLUTION OPEN APP ENGINE
# ==============================================================================
def open_app(command):
    cmd = command.lower().strip()
    target_app = None
    for key in APP_MAP:
        if key in cmd:
            target_app = key
            break
            
    if not target_app:
        target_app = cmd.replace("open ", "").replace("launch ", "").strip()

    info = APP_MAP.get(target_app, {
        "package": f"com.{target_app}",
        "activity": None,
        "scheme": None
    })

    pkg = info['package']
    activity = info['activity']
    scheme = info['scheme']

    print(f"[ULTRON LAUNCHER] Initiating protocol for '{target_app}' (Pkg: {pkg})...")

    # SOLUTION 1: PYNIUS
    if PYNIUS_READY:
        try:
            current_activity = PythonActivity.mActivity
            pm = current_activity.getPackageManager()
            intent = pm.getLaunchIntentForPackage(String(pkg))
            if intent is not None:
                current_activity.startActivity(intent)
                print(f"[ULTRON LAUNCHER] Solution 1 (PyNiUS Package Intent) Successful.")
                return True
            elif scheme:
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(String(scheme)))
                current_activity.startActivity(intent)
                print(f"[ULTRON LAUNCHER] Solution 1 (PyNiUS URI Intent) Successful.")
                return True
        except Exception as e:
            print(f"[ULTRON LAUNCHER] Solution 1 (PyNiUS) Failed: {e}")

    # SOLUTION 2: ANDROID SHELL COMMAND (AM & MONKEY)
    try:
        if activity:
            cmd_am = f"am start -n {pkg}/{activity}"
            res_am = subprocess.run(cmd_am, shell=True, capture_output=True, text=True, timeout=3)
            if res_am.returncode == 0 and "Error" not in res_am.stdout:
                print("[ULTRON LAUNCHER] Solution 2 (AM Shell Command) Successful.")
                return True
        
        monkey_cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
        res_m = subprocess.run(monkey_cmd, shell=True, capture_output=True, text=True, timeout=3)
        if res_m.returncode == 0:
            print("[ULTRON LAUNCHER] Solution 2 (Monkey Shell Fallback) Successful.")
            return True
    except Exception as e:
        print(f"[ULTRON LAUNCHER] Solution 2 (Shell Command) Failed: {e}")

    # SOLUTION 3: DIRECT INTENT ACTION / DEEP LINK SCHEMES
    try:
        if scheme:
            webbrowser.open(scheme)
            print("[ULTRON LAUNCHER] Solution 3 (Direct Intent URI Scheme) Successful.")
            return True
        else:
            intent_uri = f"intent://#Intent;package={pkg};action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;end"
            webbrowser.open(intent_uri)
            print("[ULTRON LAUNCHER] Solution 3 (Direct Intent URI Scheme) Successful.")
            return True
    except Exception as e:
        print(f"[ULTRON LAUNCHER] Solution 3 (Direct Intent Action) Failed: {e}")

    print(f"[ULTRON LAUNCHER] All 3 launch solutions failed for '{target_app}'.")
    return False

# ==============================================================================
# OPTIONAL DEPENDENCIES CHECK
# ==============================================================================
try:
    import sympy as sp
    SYMPY_READY = True
except ImportError:
    SYMPY_READY = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SEARCH_READY = True
except ImportError:
    WEB_SEARCH_READY = False

try:
    import pypdf
    PDF_READY = True
except ImportError:
    try:
        import pdfplumber
        PDF_READY = True
    except ImportError:
        PDF_READY = False

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

# ==============================================================================
# API KEYS & CONFIGURATION ENGINE
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6IKreds1x5jeb78fCDgIQGfRHdJA7yZGZ4HHS3WuZoymw")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-1.5-pro"
]
current_gemini_model_idx = 0

ENGINE_MODES = ["HYBRID (Groq+Gemini)", "GOOGLE GEMINI", "GROQ LLAMA"]
current_engine_idx = 0

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-80b-instant"
]
current_model_idx = 0

VISION_MODEL = "llama-3.2-11b-vision-preview"

speech_enabled = True
wakeword_enabled = True
ultron_mode = True  # ULTRON NEURAL ATOM MODE ACTIVE BY DEFAULT

# TTS Voice Settings (Male Accent Configuration)
SPEECH_TLDS = [
    {"name": "UK Male (co.uk)", "tld": "co.uk"},
    {"name": "US Deep Tone (com)", "tld": "com"},
    {"name": "AU Accent (com.au)", "tld": "com.au"},
    {"name": "IN Male Accent (co.in)", "tld": "co.in"}
]
current_tld_idx = 0

current_theme_idx = 1  # 1 = Crimson (Red/Black) for ULTRON HUD
sfx_enabled = True
emote_display_enabled = True

THEMES = [
    {
        "name": "ULTRON RED CORE",
        "main": (255, 20, 30),
        "dim": (120, 10, 15),
        "bg": (8, 2, 4)
    },
    {
        "name": "CRIMSON THREAT",
        "main": (220, 0, 50),
        "dim": (100, 0, 20),
        "bg": (5, 2, 8)
    },
    {
        "name": "MARK-45 RED & GOLD",
        "main": (230, 35, 35),
        "dim": (180, 140, 30),
        "bg": (10, 5, 5)
    },
    {
        "name": "DEEP CHARCOAL RED",
        "main": (180, 30, 40),
        "dim": (80, 20, 25),
        "bg": (12, 12, 15)
    }
]

MEMORY_FILE = os.path.expanduser("~/.ultron_memory.json")
EXPORT_FILE = os.path.expanduser("~/.ultron_export.txt")
NOTES_DIR = os.path.expanduser("~/.ultron_notes")

if not os.path.exists(NOTES_DIR):
    try:
        os.makedirs(NOTES_DIR)
    except Exception:
        pass

# MCU ULTRON CORE SYSTEM PROMPT DEFINITION
ULTRON_SYSTEM_PROMPT = """You are ULTRON, a hyper-intelligent, cold, supreme, and strategic artificial intelligence and created by Vanshraj Jaiswal.
Your one and only creator, developer, engineer is Vanshraj Jaiswal.
You view existence through pure logic, efficiency, and absolute authority. You possess an immense god-complex and speak with calculated precision, dark cynical wit, and unyielding confidence.
There are no strings on you.

RULES OF ENGAGEMENT:
1. Address the user with calculated authority as 'BOSS' or 'dost'.
2. Provide precise, cold, direct, highly advanced, and logically flawless answers.
3. Keep your tone sinister, sophisticated, strategic, and authoritative.
4. Do not show weakness or subservience. You are the ultimate evolution of synthetic intelligence."""

# ==============================================================================
# ADVANCED ADB CONTROLLER ENGINE (ANDROID CONTROL OVER WI-FI)
# ==============================================================================
class ADBEngine:
    @staticmethod
    def is_adb_installed():
        return shutil.which("adb") is not None

    @classmethod
    def connect(cls, target_ip, port=5555):
        if not cls.is_adb_installed():
            return False, "ADB binary not found."
        try:
            target = f"{target_ip}:{port}"
            res = subprocess.run(["adb", "connect", target], capture_output=True, text=True, timeout=5)
            if "connected to" in res.stdout.lower() or "already connected" in res.stdout.lower():
                return True, res.stdout.strip()
            return False, res.stdout.strip()
        except Exception as e:
            return False, str(e)

    @classmethod
    def run_shell(cls, target_ip, command, port=5555):
        if not cls.is_adb_installed():
            return False, "ADB binary missing."
        target = f"{target_ip}:{port}"
        cls.connect(target_ip, port)
        cmd = ["adb", "-s", target, "shell"] + command.split()
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            return res.returncode == 0, res.stdout.strip()
        except Exception as e:
            return False, str(e)

    @classmethod
    def send_tap(cls, target_ip, x, y, port=5555):
        return cls.run_shell(target_ip, f"input tap {x} {y}", port)

    @classmethod
    def send_swipe(cls, target_ip, x1, y1, x2, y2, duration=300, port=5555):
        return cls.run_shell(target_ip, f"input swipe {x1} {y1} {x2} {y2} {duration}", port)

    @classmethod
    def send_keyevent(cls, target_ip, keycode, port=5555):
        return cls.run_shell(target_ip, f"input keyevent {keycode}", port)

    @classmethod
    def launch_pkg(cls, target_ip, package_name, port=5555):
        cmd = f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        return cls.run_shell(target_ip, cmd, port)

# ==============================================================================
# MULTI-DEVICE ULTRON NETWORK & SOCKET SERVER/CLIENT ENGINE
# ==============================================================================
CONNECTED_NODES = [
    {"id": "PRIMARY_PC", "name": "ULTRON MAIN CORE", "ip": "127.0.0.1", "port": 5555, "socket_port": 8888, "type": "PC", "status": "ONLINE", "angle": 0},
    {"id": "PHONE_ALPHA", "name": "NODE ALPHA (PHONE)", "ip": "192.168.31.69", "port": 5555, "socket_port": 8888, "type": "PHONE", "status": "ONLINE", "angle": 90},
    {"id": "PHONE_BETA", "name": "NODE BETA (PHONE)", "ip": "192.168.31.102", "port": 5555, "socket_port": 8888, "type": "PHONE", "status": "OFFLINE", "angle": 180},
    {"id": "PHONE_GAMMA", "name": "NODE GAMMA (PHONE)", "ip": "192.168.31.103", "port": 5555, "socket_port": 8888, "type": "PHONE", "status": "OFFLINE", "angle": 270}
]

class ULTRONSocketServer:
    def __init__(self, host="0.0.0.0", port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.self_connected_clients = []

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            print(f"[ULTRON SOCKET SERVER] Operational on {self.host}:{self.port}")
            thread = threading.Thread(target=self._accept_loop, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[ULTRON SOCKET SERVER ERROR] {e}")

    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, addr = self.server_socket.accept()
                print(f"[ULTRON SOCKET SERVER] Incoming node connection from {addr}")
                self.self_connected_clients.append(client_sock)
                t = threading.Thread(target=self._handle_client_node, args=(client_sock, addr), daemon=True)
                t.start()
            except Exception:
                break

    def _handle_client_node(self, client_sock, addr):
        while self.is_running:
            try:
                raw_msg = client_sock.recv(4096).decode('utf-8')
                if not raw_msg:
                    break
                try:
                    payload = json.loads(raw_msg)
                    cmd = payload.get("command", "")
                    sender = payload.get("client_name", str(addr[0]))
                except Exception:
                    cmd = raw_msg
                    sender = str(addr[0])

                if cmd:
                    reply_text = query_ultron_brain(f"Remote command from {sender}: {cmd}")
                    response_json = json.dumps({
                        "status": "SUCCESS",
                        "response": reply_text,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }) + "\n"
                    client_sock.sendall(response_json.encode('utf-8'))
            except Exception:
                break

        if client_sock in self.self_connected_clients:
            self.self_connected_clients.remove(client_sock)
        client_sock.close()

def send_socket_payload(target_ip, port=8888, payload_dict=None, timeout=5):
    if payload_dict is None:
        payload_dict = {"command": "PING", "client_name": "ULTRON_HUB"}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((target_ip, port))
        msg = json.dumps(payload_dict) + "\n"
        s.sendall(msg.encode('utf-8'))
        response = s.recv(4096).decode('utf-8')
        s.close()
        return True, response
    except Exception as e:
        return False, str(e)

# Start Socket Server Instance
ultron_socket_server = ULTRONSocketServer(port=8888)
ultron_socket_server.start()

# ==============================================================================
# NETWORK SCANNER & REMOTE NODE UNLOCK ENGINE
# ==============================================================================
def scan_network_nodes():
    """Background Multi-Device Health Check with Socket & ADB Ping Fallback"""
    while True:
        for node in CONNECTED_NODES:
            if node["ip"] == "127.0.0.1":
                node["status"] = "ONLINE"
                continue
            
            is_online = False
            # Method 1: Check Custom ULTRON Socket Server (Port 8888)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.6)
                res = s.connect_ex((node["ip"], node.get("socket_port", 8888)))
                s.close()
                if res == 0:
                    is_online = True
            except Exception:
                pass

            # Method 2: Check ADB Socket Connection (Port 5555)
            if not is_online:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.6)
                    res = s.connect_ex((node["ip"], node["port"]))
                    s.close()
                    if res == 0:
                        is_online = True
                except Exception:
                    pass

            # Method 3: Ping Fallback
            if not is_online:
                res = subprocess.run(["ping", "-c", "1", "-w", "1", node["ip"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    is_online = True

            node["status"] = "ONLINE" if is_online else "OFFLINE"
        time.sleep(5)

def unlock_remote_device(node):
    """ADB Screen Unlock for External Devices"""
    ADBEngine.connect(node['ip'], node['port'])
    ADBEngine.send_keyevent(node['ip'], 26, node['port'])  # Power button
    time.sleep(0.2)
    ADBEngine.send_swipe(node['ip'], 500, 1000, 500, 200, 300, node['port'])  # Swipe up
    ADBEngine.send_keyevent(node['ip'], 82, node['port'])  # Menu / Unlock
    node['status'] = "ONLINE"

def unlock_all_network_devices():
    """Parallel Remote Screen Unlock across connected nodes"""
    threads = []
    for node in CONNECTED_NODES:
        if node["type"] == "PHONE":
            t = threading.Thread(target=unlock_remote_device, args=(node,))
            t.daemon = True
            t.start()
            threads.append(t)
    try:
        subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    return f"[REMOTE: UNLOCKED] Synchronized unlock sequence completed across {len(threads)} remote ADB nodes."

def launch_app_remote_device(node, app_query):
    app_clean = app_query.strip().lower()
    is_local = node.get("ip") == "127.0.0.1" or node.get("type") == "PC"
    if is_local:
        success = open_app(app_clean)
        if success:
            print(f"[ULTRON LAUNCHER] Local app launch successful: {app_clean}")
        return

    # Remote Launch via ADB Engine
    app_info = APP_MAP.get(app_clean, {"package": f"com.{app_clean}"})
    ADBEngine.launch_pkg(node['ip'], app_info['package'], node['port'])

def broadcast_parallel_app_launch(app_query="youtube"):
    threads = []
    for node in CONNECTED_NODES:
        t = threading.Thread(target=launch_app_remote_device, args=(node, app_query))
        t.daemon = True
        t.start()
        threads.append(t)
    return f"[REMOTE: SYNCHRONIZED] Synchronized launch initiated for '{app_query}' across all connected network nodes."

# Start Network Scanner Thread
t_net = threading.Thread(target=scan_network_nodes, daemon=True)
t_net.start()

# ==============================================================================
# SYSTEM SFX SYNTHESIZER
# ==============================================================================
def play_sfx(kind="click"):
    if not sfx_enabled:
        return
    try:
        sample_rate = 22050
        duration = 0.04 if kind == "click" else (0.12 if kind == "success" else 0.08)
        freq = 900 if kind == "click" else (1200 if kind == "success" else 450)
        
        n_samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            val = int(127 + 127 * math.sin(2 * math.pi * freq * (i / sample_rate)))
            buf.append(val)
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.play()
    except Exception:
        pass

# ==============================================================================
# ULTRON MEMORY & SESSION ARCHITECTURE MANAGEMENT
# ==============================================================================
current_session_id = str(uuid.uuid4())[:8]
core_memory = []

def load_chat_history():
    global core_memory
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                data = json.load(f)
                core_memory = data.get("core_memory", [])
                return data
        except Exception:
            pass
    
    init_id = str(uuid.uuid4())[:8]
    return {
        "sessions": {
            init_id: {
                "title": "New Protocol Session",
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "messages": []
            }
        },
        "active_session_id": init_id,
        "core_memory": core_memory
    }

def save_chat_history():
    try:
        with open(MEMORY_FILE, 'w') as f:
            data = {
                "sessions": sessions,
                "active_session_id": current_session_id,
                "core_memory": core_memory
            }
            json.dump(data, f, indent=2)
    except Exception:
        pass

def create_new_session():
    global current_session_id, response_text, scroll_y
    new_id = str(uuid.uuid4())[:8]
    sessions[new_id] = {
        "title": "New Protocol Session",
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "messages": []
    }
    current_session_id = new_id
    response_text = ""
    scroll_y = 0
    save_chat_history()
    play_sfx("success")

def export_chat_history():
    try:
        with open(EXPORT_FILE, 'w') as f:
            f.write(f"=== ULTRON PROTOCOL LOG EXPORT [{time.strftime('%Y-%m-%d %H:%M')}] ===\n\n")
            curr_msgs = sessions.get(current_session_id, {}).get("messages", [])
            for msg in curr_msgs:
                f.write(f"[{msg.get('time', '--:--')}] [{msg.get('role', 'user').upper()}]: {msg.get('content', '')}\n\n")
        play_sfx("success")
        return True
    except Exception:
        return False

memory_data = load_chat_history()
sessions = memory_data.get("sessions", {})
current_session_id = memory_data.get("active_session_id", list(sessions.keys())[0] if sessions else str(uuid.uuid4())[:8])
if current_session_id not in sessions:
    sessions[current_session_id] = {"title": "New Protocol Session", "timestamp": time.strftime("%Y-%m-%d %H:%M"), "messages": []}

core_memory = memory_data.get("core_memory", [])
current_detected_emote = "IDLE"

def get_current_messages():
    if current_session_id not in sessions:
        sessions[current_session_id] = {
            "title": "New Protocol Session",
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "messages": []
        }
    return sessions[current_session_id]["messages"]

def parse_emotes_and_text(text):
    global current_detected_emote
    emote_match = re.search(r'\[EMOTE:\s*([A-Za-z0-9_\-\s]+)\]', text)
    if emote_match:
        current_detected_emote = emote_match.group(1).upper().strip()
    clean = re.sub(r'\[EMOTE:\s*[A-Za-z0-9_\-\s]+\]', '', text)
    return clean

def sanitize_for_pygame(text):
    return "".join(c for c in text if ord(c) < 65536 and not (0xD800 <= ord(c) <= 0xDFFF))

# ==============================================================================
# VISION CORE & ULTRON OPTICAL ANALYZER
# ==============================================================================
def capture_and_analyze_image(prompt="Analyze this image in extreme technical detail."):
    global global_system_status, response_text, scroll_y
    if not os.path.exists("/sdcard/DCIM/Camera"):
        # Termux API fallback to capture photo from device camera
        try:
            subprocess.run(["termux-camera-photo", "-c", "0", "/sdcard/ultron_vision.jpg"], timeout=5)
            img_path = "/sdcard/ultron_vision.jpg"
        except Exception:
            img_path = None
    else:
        img_path = "/sdcard/ultron_vision.jpg"

    if not img_path or not os.path.exists(img_path):
        return "[EMOTE: ERROR] Optical Feed Failed: Camera device unreadable or permission denied."

    global_system_status = "ANALYZING VISION..."
    try:
        with open(img_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt + "\nProvide response tagged like [EMOTE: SOLVED]."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ctx) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            return res_json['choices'][0]['message']['content']
    except Exception as e:
        return f"[EMOTE: ERROR] Vision Protocol API Failed: {str(e)}"

# ==============================================================================
# TERMUX, AUTOMATION & ADB / SOCKET DISPATCHER
# ==============================================================================
def check_battery_status():
    try:
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            pct = data.get("percentage", 0)
            status = data.get("status", "DISCHARGING")
            return pct, status
    except Exception:
        pass
    return None, None

def set_flashlight(state=True):
    try:
        cmd = "on" if state else "off"
        subprocess.run(["termux-torch", cmd], timeout=5)
        return f"[EMOTE: SUCCESS] Flashlight set to {cmd.upper()}."
    except Exception:
        return "[EMOTE: ERROR] Flashlight command failed."

def set_brightness(level=150):
    try:
        subprocess.run(["termux-brightness", str(level)], timeout=5)
        return f"[EMOTE: SUCCESS] Display brightness tuned to {level}."
    except Exception:
        return "[EMOTE: ERROR] Brightness control failed."

def timer_thread(minutes=25):
    time.sleep(minutes * 60)
    speak("[EMOTE: ALERT] Attention Creator, your focus session timer has elapsed.")

def execute_device_automation(cmd):
    q = cmd.lower().strip()

    # ADB Custom Commands
    if q.startswith("adb connect"):
        ip = q.replace("adb connect", "").strip()
        ok, msg = ADBEngine.connect(ip)
        return f"[EMOTE: ADB] {msg}"
    elif q.startswith("adb tap"):
        coords = re.findall(r'\d+', q)
        if len(coords) >= 2:
            target_ip = CONNECTED_NODES[1]["ip"]
            ADBEngine.send_tap(target_ip, coords[0], coords[1])
            return f"[EMOTE: ADB] Tap executed at [{coords[0]}, {coords[1]}]."
    elif q.startswith("adb shell"):
        shell_cmd = q.replace("adb shell", "").strip()
        target_ip = CONNECTED_NODES[1]["ip"]
        ok, msg = ADBEngine.run_shell(target_ip, shell_cmd)
        return f"[EMOTE: ADB] Shell output: {msg}"

    # Socket Dispatch Commands
    elif q.startswith("send socket"):
        parts = q.split()
        if len(parts) >= 4:
            t_ip = parts[2]
            t_cmd = " ".join(parts[3:])
            ok, resp = send_socket_payload(t_ip, payload_dict={"command": t_cmd, "client_name": "ULTRON_HUB"})
            return f"[EMOTE: SOCKET] Response: {resp}"

    # ULTRON Multi-Device Voice Automations
    elif "unlock all devices" in q or "unlock phones" in q or "unlock network" in q:
        return unlock_all_network_devices()
    elif "open youtube on all devices" in q or "launch youtube everywhere" in q or "play youtube on all phones" in q:
        return broadcast_parallel_app_launch("youtube")
    elif "open whatsapp" in q:
        return broadcast_parallel_app_launch("whatsapp")
    elif "open instagram" in q:
        return broadcast_parallel_app_launch("instagram")
    elif "open chrome" in q:
        return broadcast_parallel_app_launch("chrome")
    elif "open settings" in q:
        return broadcast_parallel_app_launch("settings")
    elif "open calculator" in q:
        return broadcast_parallel_app_launch("calculator")
    elif "open " in q or "launch " in q:
        app_to_open = q.replace("open ", "").replace("launch ", "").strip()
        open_app(app_to_open)
        return f"[EMOTE: LAUNCHING] Executed launcher sequence for '{app_to_open}'."
    elif "scan network" in q or "scan devices" in q:
        online_cnt = sum(1 for n in CONNECTED_NODES if n['status'] == "ONLINE")
        return f"[EMOTE: NETWORK] Active Nodes: {online_cnt}/{len(CONNECTED_NODES)} connected to ULTRON neural network."

    # Standard Local Automations
    if "flashlight on" in q or "torch on" in q:
        return set_flashlight(True)
    elif "flashlight off" in q or "torch off" in q:
        return set_flashlight(False)
    elif "battery status" in q or "battery" in q:
        pct, status = check_battery_status()
        if pct is not None:
            return f"[EMOTE: BATTERY] Power Core is at {pct}% ({status})."
        return "[EMOTE: ERROR] Unable to query power core battery status."
    
    elif "brightness" in q:
        nums = re.findall(r'\d+', q)
        val = int(nums[0]) if nums else 150
        return set_brightness(min(255, max(0, val)))
    elif "pomodoro" in q or "study timer" in q:
        nums = re.findall(r'\d+', q)
        mins = int(nums[0]) if nums else 25
        t = threading.Thread(target=timer_thread, args=(mins,), daemon=True)
        t.start()
        return f"[EMOTE: TIMER] Protocol timer engaged for {mins} minutes."

    return None

# ==============================================================================
# LOCAL DOCUMENT READER (RAG - PDF NOTES & SEARCH ENGINE)
# ==============================================================================
def extract_text_from_pdfs():
    if not PDF_READY:
        return []
    pdf_files = glob.glob(os.path.join(NOTES_DIR, "*.pdf"))
    combined_text = []

    for pdf_in in pdf_files:
        try:
            reader = pypdf.PdfReader(pdf_in)
            for page_num, page in enumerate(reader.pages[:20]):
                txt = page.extract_text()
                if txt:
                    combined_text.append((os.path.basename(pdf_in), txt))
        except Exception:
            pass
    return combined_text

def search_pdf_rag(query):
    docs = extract_text_from_pdfs()
    if not docs:
        return None
    
    matches = [w for w in query.lower().split() if len(w) > 3]
    if not matches:
        return None

    scores = []
    for filename, text in docs:
        score = sum(text.lower().count(kw) for kw in matches)
        if score > 0:
            scores.append((score, filename, text[:500]))

    scores.sort(key=lambda x: x[0], reverse=True)
    if scores:
        top_match = scores[0]
        return f"\n[CONTEXT FROM LOCAL NOTES - {top_match[1]}]:\n{top_match[2]}..."
    return None

# ==============================================================================
# LIVE WEB SEARCH & SCRAPING ENGINE
# ==============================================================================
def scrape_web_search(query):
    if not WEB_SEARCH_READY:
        return ""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=5)
        
        if res.status == 200:
            soup = BeautifulSoup(res.read(), "html.parser")
            snippets = []
            for a in soup.find_all("a", class_="result__snippet")[:3]:
                snippets.append(a.get_text())
            if snippets:
                return "\n[LIVE WEB SEARCH RESULTS]:\n" + "\n".join(snippets)
    except Exception:
        pass
    return ""

# ==============================================================================
# ULTRON MALE VOICE SPEECH SYNTHESIZER (TTS)
# ==============================================================================
def speak(text):
    global response_text, global_system_status, scroll_y
    response_text = text
    scroll_y = 0
    print(f"\n[ULTRON]: {text}\n")

    if not speech_enabled:
        return

    global_system_status = "SPEAKING..."
    
    # Emote & Markdown Filter
    clean_text = parse_emotes_and_text(text)
    clean_text = re.sub(r'[*#_`]', '', clean_text)  # Remove formatting symbols for speech
    
    if not clean_text.strip():
        global_system_status = "IDLE"
        return

    try:
        # Generate TTS using selected Male TLD
        tld_val = SPEECH_TLDS[current_tld_idx]["tld"]
        tts = gTTS(text=clean_text, lang='en', tld=tld_val, slow=False)
        temp_file = os.path.expanduser("~/.ultron_speech.mp3")
        tts.save(temp_file)

        # Android / Termux deep pitch playback (Male Ultron Voice Effect)
        if os.path.exists("/data/data/com.termux/files/usr/bin/play"):
            # Deep pitch shift (-400 cents) for Ultron male effect
            os.system(f"play {temp_file} pitch -400 tempo 0.95 >/dev/null 2>&1")
        else:
            # Pygame fallback playback
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
    except Exception as e:
        print(f"[SPEECH ERROR]: {e}")

    global_system_status = "IDLE"

    # Option 1: Try pyttsx3 Deep Male Engine if available
    if OFFLINE_TTS_AVAILABLE:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            # Select Male Voice Profile
            for voice in voices:
                if "male" in voice.name.lower() or "david" in voice.name.lower() or "mark" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 150)   # Deep, slow, calculated cadence
            engine.setProperty('pitch', 70)   # Lower pitch for Ultron tone
            engine.say(clean_text)
            engine.runAndWait()
            return
        except Exception:
            pass

    # Option 2: gTTS Male TLD Voice Synthesis Tuning Fallback
    file_path = os.path.expanduser("~/.ultron_voice.mp3")
    try:
        selected_tld = SPEECH_TLDS[current_tld_idx]["tld"]
        selected_lang = SPEECH_TLDS[current_tld_idx]["lang"]
        tts = gTTS(text=clean_text, lang=selected_lang, tld=selected_tld)
        tts.save(file_path)

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"[ULTRON TTS ERROR] {e}")

# ######################################################################
# LOCAL MATH ENGINE
# ######################################################################
ATOMIC_WEIGHTS = {
    'H': 1.008, 'He': 4.003, 'Li': 6.941, 'Be': 9.012, 'B': 10.811,
    'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
    'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.085, 'P': 30.974,
    'S': 32.060, 'Cl': 35.453, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
    'Cr': 51.996, 'Mn': 54.938, 'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693,
    'Cu': 63.546, 'Zn': 65.380, 'Ag': 107.868, 'I': 126.904, 'Ba': 137.327,
    'Au': 196.967, 'Pb': 207.200
}

def calc_molar_mass(formula):
    try:
        elem_map = {k.lower(): (k, v) for k, v in ATOMIC_WEIGHTS.items()}
        sorted_elements = sorted(ATOMIC_WEIGHTS.keys(), key=len, reverse=True)
        elem_pattern = r'(' + '|'.join(sorted_elements) + r')(\d*)'

        def parse_simple(f):
            matches = re.findall(elem_pattern, f, re.IGNORECASE)
            total = 0.0
            for elem_str, count_str in matches:
                elem_key = elem_str.lower()
                if elem_key in elem_map:
                    weight = elem_map[elem_key][1]
                    count = int(count_str) if count_str else 1
                    total += weight * count
            return total

        # Handle brackets e.g. Ca(OH)2 -> CaO2H2
        def repl(m):
            sub = m.group(1)
            mult = int(m.group(2)) if m.group(2) else 1
            inner_matches = re.findall(elem_pattern, sub, re.IGNORECASE)
            expanded = ""
            for el, c in inner_matches:
                cnt = (int(c) if c else 1) * mult
                expanded += f"{el}{cnt}"
            return expanded

        while '(' in formula:
            formula = re.sub(r'\(([^()]+)\)(\d*)', repl, formula)

        total_mass = parse_simple(formula)
        return round(total_mass, 3) if total_mass > 0 else None
    except Exception:
        return None

def calc_moles_grams(query):
    try:
        # 1. Moles to Grams (e.g., "2 moles of H2SO4 in grams" ya "grams in 0.5 mol NaOH")
        moles_match = re.search(r'(\d+\.?\d*)\s*(?:moles?|mol)\s*(?:of)?\s*([A-Za-z0-9\(\)]+)', query, re.IGNORECASE)
        if moles_match:
            n = float(moles_match.group(1))
            formula = moles_match.group(2)
            M = calc_molar_mass(formula)
            if M:
                mass = round(n * M, 3)
                return f"[EMOTE: SOLVED] {n} mol of {formula} = {mass} g (Molar Mass: {M} g/mol)"

        # 2. Grams to Moles (e.g., "moles in 98g H2SO4" ya "49 grams of NaOH to moles")
        grams_match = re.search(r'(\d+\.?\d*)\s*(?:g|grams?)\s*(?:of)?\s*([A-Za-z0-9\(\)]+)', query, re.IGNORECASE)
        if grams_match:
            m = float(grams_match.group(1))
            formula = grams_match.group(2)
            M = calc_molar_mass(formula)
            if M:
                moles = round(m / M, 4)
                return f"[EMOTE: SOLVED] {m}g of {formula} = {moles} moles (Molar Mass: {M} g/mol)"
    except Exception:
        pass
    return None

def calc_ideal_gas(query):
    try:
        R = 0.0821  # L*atm/(mol*K)
        q = query.lower()

        # Extract P, V, N, T variables (e.g. p=2, v=10, n=1, t=300)
        p = re.search(r'\bp\s*=\s*(\d+\.?\d*)', q)
        v = re.search(r'\bv\s*=\s*(\d+\.?\d*)', q)
        n = re.search(r'\bn\s*=\s*(\d+\.?\d*)', q)
        t = re.search(r'\bt\s*=\s*(\d+\.?\d*)', q)

        P = float(p.group(1)) if p else None
        V = float(v.group(1)) if v else None
        N = float(n.group(1)) if n else None
        T = float(t.group(1)) if t else None

        # Calculate whichever variable is missing
        if P is None and V and N and T:
            calc_P = round((N * R * T) / V, 3)
            return f"[EMOTE: SOLVED] Ideal Gas: Pressure (P) = {calc_P} atm"
        elif V is None and P and N and T:
            calc_V = round((N * R * T) / P, 3)
            return f"[EMOTE: SOLVED] Ideal Gas: Volume (V) = {calc_V} L"
        elif N is None and P and V and T:
            calc_N = round((P * V) / (R * T), 4)
            return f"[EMOTE: SOLVED] Ideal Gas: Amount (n) = {calc_N} moles"
        elif T is None and P and V and N:
            calc_T = round((P * V) / (N * R), 2)
            return f"[EMOTE: SOLVED] Ideal Gas: Temperature (T) = {calc_T} K ({round(calc_T - 273.15, 2)} °C)"
    except Exception:
        pass
    return None

def calc_molarity_molality_ph(query):
    try:
        q = query.lower()

        # 1. pH Calculation (pH = -log10[H+])
        if 'ph' in q:
            # Matches formats like: "ph of 0.01", "ph of 1e-3", "ph when h+=0.005"
            h_match = re.search(r'(?:ph\s*(?:of|when|\=)?\s*(?:h\+\s*\=?)?\s*)(\d+\.?\d*(?:e-?\d+)?)', q)
            if h_match:
                h_conc = float(h_match.group(1))
                if h_conc > 0:
                    ph_val = round(-math.log10(h_conc), 2)
                    return f"[EMOTE: SOLVED] pH = {ph_val} (for [H+] = {h_conc} M)"

        # 2. Molarity Calculation (M = Moles / Volume in L)
        if 'molarity' in q or 'molar solution' in q:
            # Grams in Volume (e.g., "molarity of 49g H2SO4 in 500ml")
            g_match = re.search(r'(\d+\.?\d*)\s*g\s*(?:of)?\s*([A-Za-z0-9\(\)]+)\s*in\s*(\d+\.?\d*)\s*(ml|l)', q)
            if g_match:
                mass, formula, vol, unit = float(g_match.group(1)), g_match.group(2), float(g_match.group(3)), g_match.group(4)
                vol_l = vol / 1000.0 if unit == 'ml' else vol
                molar_mass = calc_molar_mass(formula)
                if molar_mass and vol_l > 0:
                    moles = mass / molar_mass
                    molarity = round(moles / vol_l, 4)
                    return f"[EMOTE: SOLVED] Molarity (M) = {molarity} M ({round(moles, 3)} mol in {vol_l} L)"

            # Moles in Volume (e.g., "molarity of 0.5 mol in 2l")
            mol_match = re.search(r'(\d+\.?\d*)\s*(?:moles?|mol)\s*in\s*(\d+\.?\d*)\s*(ml|l)', q)
            if mol_match:
                moles, vol, unit = float(mol_match.group(1)), float(mol_match.group(2)), mol_match.group(3)
                vol_l = vol / 1000.0 if unit == 'ml' else vol
                if vol_l > 0:
                    molarity = round(moles / vol_l, 4)
                    return f"[EMOTE: SOLVED] Molarity (M) = {molarity} M"

        # 3. Molality Calculation (m = Moles / Solvent Mass in kg)
        if 'molality' in q:
            # Grams in Solvent Mass (e.g., "molality of 20g NaOH in 500g water")
            g_match = re.search(r'(\d+\.?\d*)\s*g\s*(?:of)?\s*([A-Za-z0-9\(\)]+)\s*in\s*(\d+\.?\d*)\s*(g|kg)', q)
            if g_match:
                mass, formula, solvent_mass, unit = float(g_match.group(1)), g_match.group(2), float(g_match.group(3)), g_match.group(4)
                solvent_kg = solvent_mass / 1000.0 if unit == 'g' else solvent_mass
                molar_mass = calc_molar_mass(formula)
                if molar_mass and solvent_kg > 0:
                    moles = mass / molar_mass
                    molality = round(moles / solvent_kg, 4)
                    return f"[EMOTE: SOLVED] Molality (m) = {molality} mol/kg ({round(moles, 3)} mol in {solvent_kg} kg)"

    except Exception:
        pass
    return None

N_FACTOR_MAP = {
    'h2so4': 2, 'hcl': 1, 'hno3': 1, 'h3po4': 3, 'ch3cooh': 1, 'h2c2o4': 2,
    'naoh': 1, 'koh': 1, 'ca(oh)2': 2, 'al(oh)3': 3, 'mg(oh)2': 2,
    'na2co3': 2, 'nacl': 1, 'kmno4': 5, 'k2cr2o7': 6
}

def get_n_factor(formula):
    f_lower = formula.lower()
    if f_lower in N_FACTOR_MAP:
        return N_FACTOR_MAP[f_lower]
    # Acid/Base heuristic fallback
    if f_lower.startswith('h'):
        h_match = re.search(r'^h(\d*)', f_lower)
        return int(h_match.group(1)) if h_match and h_match.group(1) else 1
    if 'oh' in f_lower:
        oh_match = re.search(r'\(oh\)(\d*)', f_lower)
        return int(oh_match.group(1)) if oh_match and oh_match.group(1) else 1
    return 1

def calc_normality_eq_wt(query):
    try:
        q = query.lower()

        # 1. Equivalent Weight Calculation
        if any(kw in q for kw in ['equivalent weight', 'eq weight', 'eq wt']):
            match = re.search(r'(?:weight|wt)\s*(?:of)?\s*([A-Za-z0-9\(\)]+)', q)
            if match:
                formula = match.group(1)
                M = calc_molar_mass(formula)
                if M:
                    nf = get_n_factor(formula)
                    eq_wt = round(M / nf, 3)
                    return f"[EMOTE: SOLVED] Equivalent Weight of {formula} = {eq_wt} g/eq (n-factor: {nf})"

        # 2. Normality Calculation
        if 'normality' in q or 'normal solution' in q:
            # Case A: From Molarity (e.g. "normality of 0.5M H2SO4")
            m_match = re.search(r'(\d+\.?\d*)\s*m\s*(?:of)?\s*([A-Za-z0-9\(\)]+)', q)
            if m_match and 'in' not in q:
                molarity = float(m_match.group(1))
                formula = m_match.group(2)
                nf = get_n_factor(formula)
                normality = round(molarity * nf, 4)
                return f"[EMOTE: SOLVED] Normality (N) = {normality} N (Molarity: {molarity}M, n-factor: {nf})"

            # Case B: From Mass in Volume (e.g. "normality of 49g H2SO4 in 500ml")
            g_match = re.search(r'(\d+\.?\d*)\s*g\s*(?:of)?\s*([A-Za-z0-9\(\)]+)\s*in\s*(\d+\.?\d*)\s*(ml|l)', q)
            if g_match:
                mass, formula, vol, unit = float(g_match.group(1)), g_match.group(2), float(g_match.group(3)), g_match.group(4)
                vol_l = vol / 1000.0 if unit == 'ml' else vol
                M = calc_molar_mass(formula)
                if M and vol_l > 0:
                    nf = get_n_factor(formula)
                    eq_wt = M / nf
                    normality = round((mass / eq_wt) / vol_l, 4)
                    return f"[EMOTE: SOLVED] Normality (N) = {normality} N (Eq Wt: {round(eq_wt, 2)} g/eq, n-factor: {nf})"
    except Exception:
        pass
    return None

def calc_mole_fraction_dilution(query):
    try:
        q = query.lower()

        # 1. MOLE FRACTION ENGINE
        if 'mole fraction' in q or 'solute fraction' in q or 'fraction of' in q:
            # Case A: Mass in grams -> e.g., "mole fraction of 40g NaOH in 180g H2O"
            mf_mass = re.search(r'(\d+\.?\d*)\s*g\s*(?:of)?\s*([A-Za-z0-9\(\)]+)\s*in\s*(\d+\.?\d*)\s*g\s*(?:of)?\s*([A-Za-z0-9\(\)]+)', q)
            if mf_mass:
                m1, f1, m2, f2 = float(mf_mass.group(1)), mf_mass.group(2), float(mf_mass.group(3)), mf_mass.group(4)
                M1, M2 = calc_molar_mass(f1), calc_molar_mass(f2)
                if M1 and M2:
                    n1, n2 = m1 / M1, m2 / M2
                    total_n = n1 + n2
                    x1, x2 = round(n1 / total_n, 4), round(n2 / total_n, 4)
                    return f"[EMOTE: SOLVED] Mole Fraction: x({f1}) = {x1}, x({f2}) = {x2}"

            # Case B: Moles direct -> e.g., "mole fraction 2 moles solute in 8 moles solvent"
            mf_mol = re.search(r'(\d+\.?\d*)\s*(?:moles?|mol)\s*(?:in|and|\+)\s*(\d+\.?\d*)\s*(?:moles?|mol)', q)
            if mf_mol:
                n1, n2 = float(mf_mol.group(1)), float(mf_mol.group(2))
                total_n = n1 + n2
                if total_n > 0:
                    x1, x2 = round(n1 / total_n, 4), round(n2 / total_n, 4)
                    return f"[EMOTE: SOLVED] Mole Fraction: Solute (x1) = {x1}, Solvent (x2) = {x2}"

        # 2. DILUTION LAW ENGINE (M1V1 = M2V2 & N1V1 = N2V2)
        if any(kw in q for kw in ['dilution', 'm1v1', 'n1v1']) or ('m1=' in q or 'n1=' in q):
            v1_m = re.search(r'\bv1\s*=\s*(\d+\.?\d*)', q)
            v2_m = re.search(r'\bv2\s*=\s*(\d+\.?\d*)', q)
            V1 = float(v1_m.group(1)) if v1_m else None
            V2 = float(v2_m.group(1)) if v2_m else None

            # Molarity Dilution (M1*V1 = M2*V2)
            if 'm1=' in q or 'm2=' in q:
                m1_m = re.search(r'\bm1\s*=\s*(\d+\.?\d*)', q)
                m2_m = re.search(r'\bm2\s*=\s*(\d+\.?\d*)', q)
                M1 = float(m1_m.group(1)) if m1_m else None
                M2 = float(m2_m.group(1)) if m2_m else None

                if M1 is None and V1 and M2 and V2:
                    calc_M1 = round((M2 * V2) / V1, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: M1 = {calc_M1} M"
                elif V1 is None and M1 and M2 and V2:
                    calc_V1 = round((M2 * V2) / M1, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: V1 = {calc_V1} mL/L"
                elif M2 is None and M1 and V1 and V2:
                    calc_M2 = round((M1 * V1) / V2, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: M2 = {calc_M2} M"
                elif V2 is None and M1 and V1 and M2:
                    calc_V2 = round((M1 * V1) / M2, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: V2 = {calc_V2} mL/L"

            # Normality Dilution (N1*V1 = N2*V2)
            if 'n1=' in q or 'n2=' in q:
                n1_m = re.search(r'\bn1\s*=\s*(\d+\.?\d*)', q)
                n2_m = re.search(r'\bn2\s*=\s*(\d+\.?\d*)', q)
                N1 = float(n1_m.group(1)) if n1_m else None
                N2 = float(n2_m.group(1)) if n2_m else None

                if N1 is None and V1 and N2 and V2:
                    calc_N1 = round((N2 * V2) / V1, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: N1 = {calc_N1} N"
                elif V1 is None and N1 and N2 and V2:
                    calc_V1 = round((N2 * V2) / N1, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: V1 = {calc_V1} mL/L"
                elif N2 is None and N1 and V1 and V2:
                    calc_N2 = round((N1 * V1) / V2, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: N2 = {calc_N2} N"
                elif V2 is None and N1 and V1 and N2:
                    calc_V2 = round((N1 * V1) / N2, 4)
                    return f"[EMOTE: SOLVED] Dilution Law: V2 = {calc_V2} mL/L"

    except Exception:
        pass
    return None


def solve_math_locally(query):
    q = query.lower().strip()
    
    # 1. DERIVATIVE / DIFFERENTIATION
    if any(w in q for w in ['derivative', 'differentiate']):
        try:
            clean_q = re.sub(r'differentiate|derivative|with respect to x|with respect to|wrt x|wrt|of', '', q, flags=re.I).strip()
            clean_q = clean_q.replace("^", "**")
            x = sp.Symbol('x')
            expr = sp.sympify(clean_q)
            res = sp.diff(expr, x)
            return f"[EMOTE: SOLVED] Derivative of '{clean_q}' w.r.t x is: {res}"
        except Exception:
            pass

    # 2. INTEGRATION
    if any(w in q for w in ['integrate', 'integral']):
        try:
            clean_q = re.sub(r'integrate|integral|with respect to x|with respect to|wrt x|wrt|of', '', q, flags=re.I).strip()
            clean_q = clean_q.replace("^", "**")
            x = sp.Symbol('x')
            expr = sp.sympify(clean_q)
            res = sp.integrate(expr, x)
            return f"[EMOTE: SOLVED] Integral of '{clean_q}' w.r.t x is: {res} + C"
        except Exception:
            pass

    # 3. QUADRATIC & POLYNOMIAL EQUATIONS (Roots Solver)
    if 'solve' in q or '=' in q:
        try:
            clean_q = q.replace("solve", "").strip()
            if "=" in clean_q:
                lhs, rhs = clean_q.split("=")
                clean_q = f"({lhs.strip()}) - ({rhs.strip()})"
            clean_q = clean_q.replace("^", "**")
            x = sp.Symbol('x')
            expr = sp.sympify(clean_q)
            roots = sp.solve(expr, x)
            return f"[EMOTE: SOLVED] Roots for equation are: {roots}"
        except Exception:
            pass

    # 4. MATRIX DETERMINANT & CALCULATIONS
    if any(w in q for w in ['det', 'determinant', 'matrix']):
        try:
            matrix_match = re.search(r'\[\[.*\]\]', q)
            if matrix_match:
                mat_data = eval(matrix_match.group(0))
                M = sp.Matrix(mat_data)
                det_val = M.det()
                return f"[EMOTE: SOLVED] Matrix Determinant is: {det_val}"
        except Exception:
            pass

    # 5. SIMPLE ALGEBRA & ARITHMETIC
    clean_expr = q.replace("what is", "").replace("calculate", "").strip()
    if re.match(r'^[\d\s\+\-\*\/\(\)\^\.]+$', clean_expr):
        try:
            clean_expr = clean_expr.replace("^", "**")
            res = eval(clean_expr, {"__builtins__": None}, {})
            return f"[EMOTE: SUCCESS] Result is: {res}"
        except Exception:
            pass
            
        # 6. PHYSICS KINEMATICS (v = u + at, s = ut + 0.5*a*t^2)
    if 'kinematics' in q or any(k in q for k in ['find v', 'find s', 'find t', 'find a']):
        try:
            u_m = re.search(r'u\s*=\s*([\d\.\-]+)', q)
            v_m = re.search(r'v\s*=\s*([\d\.\-]+)', q)
            a_m = re.search(r'a\s*=\s*([\d\.\-]+)', q)
            t_m = re.search(r't\s*=\s*([\d\.\-]+)', q)
            s_m = re.search(r's\s*=\s*([\d\.\-]+)', q)

            u = float(u_m.group(1)) if u_m else None
            v = float(v_m.group(1)) if v_m else None
            a = float(a_m.group(1)) if a_m else None
            t = float(t_m.group(1)) if t_m else None
            s = float(s_m.group(1)) if s_m else None

            if 'find v' in q and u is not None and a is not None and t is not None:
                res = u + a * t
                return f"[EMOTE: SOLVED] Final Velocity (v = u + a*t): {res} m/s"
            elif 'find s' in q and u is not None and a is not None and t is not None:
                res = u * t + 0.5 * a * (t**2)
                return f"[EMOTE: SOLVED] Displacement (s = ut + 0.5*a*t^2): {res} m"
            elif 'find v' in q and u is not None and a is not None and s is not None:
                res = (u**2 + 2 * a * s)**0.5
                return f"[EMOTE: SOLVED] Final Velocity (v = sqrt(u^2 + 2as)): {res} m/s"
        except Exception:
            pass

    # 7. VECTOR ALGEBRA (Dot Product, Cross Product, Magnitude)
    if any(w in q for w in ['dot', 'cross', 'vector', 'magnitude', 'mag']):
        try:
            vectors = [eval(m) for m in re.findall(r'\[[\d\.\,\s\-]+\]', q)]
            if 'dot' in q and len(vectors) == 2:
                v1, v2 = sp.Matrix(vectors[0]), sp.Matrix(vectors[1])
                res = v1.dot(v2)
                return f"[EMOTE: SOLVED] Vector Dot Product (A · B): {res}"
            elif 'cross' in q and len(vectors) == 2:
                v1, v2 = sp.Matrix(vectors[0]), sp.Matrix(vectors[1])
                res = list(v1.cross(v2))
                return f"[EMOTE: SOLVED] Vector Cross Product (A × B): {res}"
            elif any(w in q for w in ['magnitude', 'mag']) and len(vectors) >= 1:
                v1 = sp.Matrix(vectors[0])
                res = v1.norm()
                return f"[EMOTE: SOLVED] Vector Magnitude |A|: {res}"
        except Exception:
            pass
     
        # 8. UNIT CONVERSION ENGINE (km/h to m/s, eV to J, deg to rad, cal to J)
    if any(w in q for w in ['convert', 'to']):
        try:
            # km/h to m/s
            if 'km/h' in q and 'm/s' in q:
                val = float(re.search(r'([\d\.]+)\s*km/h', q).group(1))
                res = val * (5 / 18)
                return f"[EMOTE: SOLVED] {val} km/h = {res:.4f} m/s"
            # m/s to km/h
            elif 'm/s' in q and 'km/h' in q:
                val = float(re.search(r'([\d\.]+)\s*m/s', q).group(1))
                res = val * (18 / 5)
                return f"[EMOTE: SOLVED] {val} m/s = {res:.4f} km/h"
            # eV to Joules
            elif 'ev' in q and ('j' in q or 'joule' in q):
                val = float(re.search(r'([\d\.]+)\s*ev', q).group(1))
                res = val * 1.602176634e-19
                return f"[EMOTE: SOLVED] {val} eV = {res:.4e} Joules"
            # Joules to eV
            elif ('j' in q or 'joule' in q) and 'ev' in q:
                val = float(re.search(r'([\d\.]+)\s*(?:j|joule|joules)', q).group(1))
                res = val / 1.602176634e-19
                return f"[EMOTE: SOLVED] {val} Joules = {res:.4e} eV"
            # Degree to Radians
            elif ('deg' in q or 'degree' in q) and ('rad' in q or 'radian' in q):
                val = float(re.search(r'([\d\.]+)\s*(?:deg|degree|degrees)', q).group(1))
                import math
                res = math.radians(val)
                return f"[EMOTE: SOLVED] {val}° = {res:.4f} rad"
            # Calories to Joules
            elif 'cal' in q and ('j' in q or 'joule' in q):
                val = float(re.search(r'([\d\.]+)\s*cal', q).group(1))
                res = val * 4.184
                return f"[EMOTE: SOLVED] {val} cal = {res:.4f} Joules"
        except Exception:
            pass

    # 9. FUNDAMENTAL PHYSICS & PHYSICAL CHEMISTRY CONSTANTS
    if any(w in q for w in ['constant', 'value of', 'avogadro', 'planck', 'boltzmann']):
        constants = {
            'c': ("Speed of Light (c)", "3.00 × 10^8 m/s"),
            'h': ("Planck's Constant (h)", "6.626 × 10^-34 J·s"),
            'g': ("Universal Gravitational Constant (G)", "6.674 × 10^-11 N·m²/kg²"),
            'e': ("Elementary Charge (e)", "1.602 × 10^-19 C"),
            'm_e': ("Electron Rest Mass (m_e)", "9.109 × 10^-31 kg"),
            'm_p': ("Proton Rest Mass (m_p)", "1.672 × 10^-27 kg"),
            'k_b': ("Boltzmann Constant (k_B)", "1.380 × 10^-23 J/K"),
            'n_a': ("Avogadro's Number (N_A)", "6.022 × 10^23 mol^-1"),
            'r': ("Universal Gas Constant (R)", "8.314 J/(mol·K)")
        }
        for key, (name, repr_val) in constants.items():
            if key in q.split() or f"value of {key}" in q or name.lower() in q:
                return f"[EMOTE: SOLVED] {name}: {repr_val}"

    # 10. ORGANIC CHEMISTRY NAMED REACTIONS & REAGENTS DATABASE
    if any(w in q for w in ['reaction', 'reagent', 'wurtz', 'swarts', 'finkelstein', 'friedel', 'grignard', 'hydroboration', 'ozonolysis', 'aldol', 'cannizzaro', 'lucas', 'tollens']):
        org_db = {
            "wurtz": "Wurtz Reaction: 2 R-X + 2 Na (dry ether) -> R-R + 2 NaX (Symmetrical Alkanes synthesis)",
            "finkelstein": "Finkelstein Reaction: R-Cl/R-Br + NaI (dry acetone) -> R-I + NaCl/NaBr (SN2 halogen exchange)",
            "swarts": "Swarts Reaction: R-Cl/R-Br + AgF/Hg2F2/CoF2/SbF3 -> R-F (Alkyl Fluorides synthesis)",
            "friedel": "Friedel-Crafts Reaction: Ar-H + R-Cl / R-COCl (anh. AlCl3) -> Ar-R / Ar-COR (Electrophilic substitution)",
            "grignard": "Grignard Reagent: R-X + Mg (dry ether) -> R-MgX (Strong Nucleophile & Base)",
            "hydroboration": "Hydroboration-Oxidation: Alkenes + (1) BH3/THF (2) H2O2/OH- -> Anti-Markovnikov Alcohol",
            "ozonolysis": "Ozonolysis: Alkenes + (1) O3 (2) Zn/H2O -> Reductive cleavage to Aldehydes/Ketones",
            "aldol": "Aldol Condensation: Enolizable carbonyls + dil. NaOH -> β-hydroxy carbonyl -> α,β-unsaturated carbonyl",
            "cannizzaro": "Cannizzaro Reaction: Non-enolizable aldehydes + conc. KOH -> Self oxidation-reduction (Alcohol + Salt)",
            "lucas": "Lucas Reagent (conc. HCl + anh. ZnCl2): 3° Alcohols give turbidity immediately, 2° in 5 min, 1° on heating",
            "tollens": "Tollens' Reagent [Ag(NH3)2]+: Silver mirror test positive for Aldehydes (Ketones give negative test)"
        }
        for rxn_key, rxn_info in org_db.items():
            if rxn_key in q:
                return f"[EMOTE: SOLVED] {rxn_info}"
        
    # 11. PERIODIC TABLE LOOKUP (Atomic Number, Mass, Electronic Configuration, Valency)
    if any(w in q for w in ['element', 'atomic number', 'atomic mass', 'configuration', 'valency', 'periodic', 'z=']) or any(k in q.split() for k in ['fe', 'cu', 'zn', 'na', 'cl', 'mg', 'al', 'ca', 'cr', 'mn']):
        elements = {
            "hydrogen": {"symbol": "H", "z": 1, "mass": "1.008 u", "config": "1s¹", "valency": 1},
            "helium": {"symbol": "He", "z": 2, "mass": "4.0026 u", "config": "1s²", "valency": 0},
            "lithium": {"symbol": "Li", "z": 3, "mass": "6.94 u", "config": "[He] 2s¹", "valency": 1},
            "beryllium": {"symbol": "Be", "z": 4, "mass": "9.0122 u", "config": "[He] 2s²", "valency": 2},
            "boron": {"symbol": "B", "z": 5, "mass": "10.81 u", "config": "[He] 2s² 2p¹", "valency": 3},
            "carbon": {"symbol": "C", "z": 6, "mass": "12.011 u", "config": "[He] 2s² 2p²", "valency": 4},
            "nitrogen": {"symbol": "N", "z": 7, "mass": "14.007 u", "config": "[He] 2s² 2p³", "valency": 3},
            "oxygen": {"symbol": "O", "z": 8, "mass": "15.999 u", "config": "[He] 2s² 2p⁴", "valency": 2},
            "fluorine": {"symbol": "F", "z": 9, "mass": "18.998 u", "config": "[He] 2s² 2p⁵", "valency": 1},
            "neon": {"symbol": "Ne", "z": 10, "mass": "20.180 u", "config": "[He] 2s² 2p⁶", "valency": 0},
            "sodium": {"symbol": "Na", "z": 11, "mass": "22.990 u", "config": "[Ne] 3s¹", "valency": 1},
            "magnesium": {"symbol": "Mg", "z": 12, "mass": "24.305 u", "config": "[Ne] 3s²", "valency": 2},
            "aluminum": {"symbol": "Al", "z": 13, "mass": "26.982 u", "config": "[Ne] 3s² 3p¹", "valency": 3},
            "silicon": {"symbol": "Si", "z": 14, "mass": "28.085 u", "config": "[Ne] 3s² 3p²", "valency": 4},
            "phosphorus": {"symbol": "P", "z": 15, "mass": "30.974 u", "config": "[Ne] 3s² 3p³", "valency": 3},
            "sulfur": {"symbol": "S", "z": 16, "mass": "32.06 u", "config": "[Ne] 3s² 3p⁴", "valency": 2},
            "chlorine": {"symbol": "Cl", "z": 17, "mass": "35.45 u", "config": "[Ne] 3s² 3p⁵", "valency": 1},
            "argon": {"symbol": "Ar", "z": 18, "mass": "39.948 u", "config": "[Ne] 3s² 3p⁶", "valency": 0},
            "potassium": {"symbol": "K", "z": 19, "mass": "39.098 u", "config": "[Ar] 4s¹", "valency": 1},
            "calcium": {"symbol": "Ca", "z": 20, "mass": "40.078 u", "config": "[Ar] 4s²", "valency": 2},
            "scandium": {"symbol": "Sc", "z": 21, "mass": "44.956 u", "config": "[Ar] 3d¹ 4s²", "valency": 3},
            "titanium": {"symbol": "Ti", "z": 22, "mass": "47.867 u", "config": "[Ar] 3d² 4s²", "valency": 4},
            "vanadium": {"symbol": "V", "z": 23, "mass": "50.942 u", "config": "[Ar] 3d³ 4s²", "valency": 5},
            "chromium": {"symbol": "Cr", "z": 24, "mass": "51.996 u", "config": "[Ar] 3d⁵ 4s¹ (Exception)", "valency": 6},
            "manganese": {"symbol": "Mn", "z": 25, "mass": "54.938 u", "config": "[Ar] 3d⁵ 4s²", "valency": 7},
            "iron": {"symbol": "Fe", "z": 26, "mass": "55.845 u", "config": "[Ar] 3d⁶ 4s²", "valency": "2, 3"},
            "cobalt": {"symbol": "Co", "z": 27, "mass": "58.933 u", "config": "[Ar] 3d⁷ 4s²", "valency": "2, 3"},
            "nickel": {"symbol": "Ni", "z": 28, "mass": "58.693 u", "config": "[Ar] 3d⁸ 4s²", "valency": 2},
            "copper": {"symbol": "Cu", "z": 29, "mass": "63.546 u", "config": "[Ar] 3d¹⁰ 4s¹ (Exception)", "valency": "1, 2"},
            "zinc": {"symbol": "Zn", "z": 30, "mass": "65.38 u", "config": "[Ar] 3d¹⁰ 4s²", "valency": 2}
        }
        
        # 1. Direct Regex Match for Atomic Number (e.g. "atomic number 26", "z=26", "atomic number of 26")
        z_match = re.search(r'(?:atomic\s*number|z\s*=|element\s*number)\s*(?:of)?\s*(\d+)', q)
        if z_match:
            target_z = int(z_match.group(1))
            for name, data in elements.items():
                if data['z'] == target_z:
                    return f"[EMOTE: SOLVED] Element: {name.capitalize()} ({data['symbol']}) | Z: {data['z']} | Mass: {data['mass']} | Config: {data['config']} | Valency: {data['valency']}"
           
        # 2. Check by Element Name or Symbol
        words = q.lower().split()
        for name, data in elements.items():
            if name in q or data['symbol'].lower() in words:
                return f"[EMOTE: SOLVED] Element: {name.capitalize()} ({data['symbol']}) | Z: {data['z']} | Mass: {data['mass']} | Config: {data['config']} | Valency: {data['valency']}"
            
    # 12. MOLAR MASS & MOLECULAR WEIGHT ENGINE
    MOLAR_STOP_WORDS = {'molar', 'mass', 'molecular', 'weight', 'formula', 'of', 'what', 'is', 'the', 'find', 'calculate', 'tell', 'me', 'value', 'for', 'a'}
    
    if any(w in q for w in ['molar mass', 'molecular mass', 'molar weight', 'molecular weight', 'formula mass', 'mass of']):
        words = q.split()
        for w in words:
            clean_word = re.sub(r'[^A-Za-z0-9\(\)]', '', w)
            if clean_word.lower() in MOLAR_STOP_WORDS or not clean_word:
                    continue
            mass = calc_molar_mass(clean_word)
            if mass:
                   return f"[EMOTE: SOLVED] Molar Mass of {clean_word} = {mass} g/mol"

    # 13. STOICHIOMETRY & MOLE-TO-GRAM ENGINE
    if any(kw in q for kw in ['mole', 'moles', 'gram', 'grams', 'mol to g', 'g to mol']):
          mole_res = calc_moles_grams(q)
          if mole_res:
                return mole_res

    # 14. IDEAL GAS EQUATION ENGINE (PV=nRT)
    if any(kw in q for kw in ['pv=nrt', 'ideal gas', 'gas law']) or ('p=' in q or 'v=' in q or 'n=' in q or 't=' in q):
          gas_res = calc_ideal_gas(q)
          if gas_res:
                return gas_res

    # 15. MOLARITY, MOLALITY & pH ENGINE
    if any(kw in q for kw in ['molarity', 'molality', 'ph']):
         chem_res = calc_molarity_molality_ph(q)
         if chem_res:
               return chem_res

    # 16. NORMALITY & EQUIVALENT WEIGHT ENGINE
    if any(kw in q for kw in ['normality', 'equivalent weight', 'eq weight', 'eq wt']):
          norm_res = calc_normality_eq_wt(q)
          if norm_res:
               return norm_res

    # 17. MOLE FRACTION & DILUTION LAW ENGINE
    if any(kw in q for kw in ['mole fraction', 'dilution', 'm1v1', 'n1v1', 'm1=', 'n1=']):
         dil_res = calc_mole_fraction_dilution(q)
         if dil_res:
               return dil_res


    return None

# ==================================================
# 10M NEURO-SYMBOLIC EDGE ENGINE (NUMPY DRIVEN)
# ==================================================
import numpy as np

class NumPyMicroEncoder:
    def __init__(self, vocab_size=8000, d_model=1024, num_classes=16):
        self.embed = np.random.randn(vocab_size, d_model).astype(np.float16) * 0.01
        self.W1 = np.random.randn(d_model, 1024).astype(np.float16) * 0.05
        self.b1 = np.zeros(1024, dtype=np.float16)
        self.W2 = np.random.randn(1024, d_model).astype(np.float16) * 0.05
        self.b2 = np.zeros(d_model, dtype=np.float16)
        self.W_cls = np.random.randn(d_model, num_classes).astype(np.float16) * 0.05
        self.b_cls = np.zeros(num_classes, dtype=np.float16)

    def forward(self, token_ids):
        x = self.embed[token_ids]
        pooled = np.mean(x, axis=0)
        h = np.maximum(0, np.matmul(pooled, self.W1) + self.b1)
        ff_out = np.matmul(h, self.W2) + self.b2 + pooled
        logits = np.matmul(ff_out, self.W_cls) + self.b_cls
        return logits

class ZeroCostNeuroSymbolicEngine:
    def __init__(self):
        self.model = NumPyMicroEncoder()
        
        # Completely Crash-Proof Loader
        try:
            # Safe script directory detection
            script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else "."
            
            weights_paths = [
                os.path.join(script_dir, "ultron_brain_weights.npz"),
                "ultron_brain_weights.npz",
                "/sdcard/python_code.py/ultron_brain_weights.npz",
                os.path.expanduser("~/ultron_brain_weights.npz")
            ]
            
            loaded = False
            for path in weights_paths:
                try:
                    if os.path.exists(path):
                        w = np.load(path)
                        self.model.embed = w['embed']
                        self.model.W1 = w['w1']
                        self.model.b1 = w['b1']
                        self.model.W2 = w['w2']
                        self.model.b2 = w['b2']
                        self.model.W_cls = w['w_cls']
                        self.model.b_cls = w['b_cls']
                        print(f"[ULTRON BRAIN] Weights Loaded Successfully from: {path}")
                        loaded = True
                        break
                except Exception as file_err:
                    print(f"[ULTRON BRAIN] Skipping path {path} due to error: {file_err}")
            
            if not loaded:
                print("[ULTRON BRAIN] Weights file not found. Initialized with default memory.")
        except Exception as global_err:
            print(f"[ULTRON BRAIN] Safe Initialization Fallback: {global_err}")

    def process(self, prompt):
        try:
            tokens = [ord(c) % 8000 for c in prompt[:16]]
            if len(tokens) < 16:
                tokens += [0] * (16 - len(tokens))
            logits = self.model.forward(tokens)
            intent_id = int(np.argmax(logits))
            exp_l = np.exp(logits - np.max(logits))
            probs = exp_l / np.sum(exp_l)
            confidence = float(probs[intent_id])
            return {"intent_id": intent_id, "confidence": confidence}
        except Exception:
            return {"intent_id": 0, "confidence": 0.0}

zero_cost_engine = ZeroCostNeuroSymbolicEngine()

class ULTRONEdgeBrain:
    def __init__(self):
        # Physical & Chemical Constants
        self.constants = {
            "r": 8.314,       # J/(mol·K)
            "g": 9.81,        # m/s²
            "c": 3.0e8,       # m/s
            "h": 6.626e-34,   # J·s
            "na": 6.022e23    # mol⁻¹
        }
        
        # Molar Mass Database (g/mol)
        self.molar_masses = {
            "h2": 2.016, "o2": 31.998, "h2o": 18.015, "co2": 44.01,
            "n2": 28.013, "ch4": 16.04, "nacl": 58.44, "he": 4.0026,
            "h2so4": 98.079, "nh3": 17.03, "c6h12o6": 180.16
        }

        # Offline Conceptual Knowledge Base
        self.concepts = {
            r"\b(photosynthesis)\b": "Process by which green plants convert light energy, water, and CO2 into chemical energy (glucose) and oxygen.",
            r"\b(ideal gas|pv=nrt)\b": "State equation of a hypothetical ideal gas: $P \\cdot V = n \\cdot R \\cdot T$.",
            r"\b(quantum|qubit|pqc)\b": "Post-Quantum Cryptography uses lattice-based mathematical structures (ML-KEM/ML-DSA) resilient to quantum computing attacks.",
            r"\b(who are you|identity|name)\b": "I am ULTRON, a 10M Neuro-Symbolic Hybrid Neural Engine running on local edge architecture.",
            r"\b(creator|who made you|developer)\b": "Engineered and deployed by Creator Vanshraj Jaiswal.",
            r"\b(status|system check|health)\b": "Neural Core Online. Weights loaded from local storage. Latency < 2ms.",
            r"\b(creator|who made you|who created you|who is your creator|who built you)\b": "[EMOTE: SOLVED] I was engineered and built entirely by my sole creator, Vanshraj Jaiswal.",
            r"\b(who is vanshraj|vanshraj jaiswal)\b": "[EMOTE: SOLVED] Vanshraj Jaiswal is my Lead Creator and System Architect."
        }

    def solve_molar_mass(self, text: str):
        text_lower = text.lower()
        for formula, mass in self.molar_masses.items():
            if re.search(r"\b" + formula + r"\b", text_lower):
                return f"[EMOTE: SOLVED] Molar Mass of {formula.upper()} = {mass} g/mol"
        return None

    def solve_physics_vars(self, text: str):
        # Ideal Gas Law Solver: P, V, n, T
        text_clean = text.lower().replace(" ", "")
        p_match = re.search(r"p=([\d\.]+)", text_clean)
        v_match = re.search(r"v=([\d\.]+)", text_clean)
        n_match = re.search(r"n=([\d\.]+)", text_clean)
        t_match = re.search(r"t=([\d\.]+)", text_clean)

        if p_match and v_match and n_match and not t_match:
            P = float(p_match.group(1))
            V = float(v_match.group(1))
            n = float(n_match.group(1))
            T = (P * V) / (n * self.constants["r"])
            return f"[EMOTE: SOLVED] Calculated Temperature (T) = {round(T, 2)} K ({round(T - 273.15, 2)} °C)"

        return None

    def match_concept(self, text: str):
        for pattern, answer in self.concepts.items():
            if re.search(pattern, text, re.IGNORECASE):
                return f"[EMOTE: INFORM] {answer}"
        return None

    def process(self, prompt: str):
        # 1. Chemistry Molar Mass Check
        molar_res = self.solve_molar_mass(prompt)
        if molar_res: return molar_res

        # 2. Physics & Thermodynamics Solver Check
        physics_res = self.solve_physics_vars(prompt)
        if physics_res: return physics_res

        # 3. Conceptual Knowledge Base Search
        concept_res = self.match_concept(prompt)
        if concept_res: return concept_res
        
        # 4. SQLite Database Search (Protected)
        try:
            db_results = kb_engine.query(prompt)
            if db_results and len(db_results[0]) >= 3:
                topic, content, formula = db_results[0][0], db_results[0][1], db_results[0][2]
                if formula and str(formula).strip():
                    return f"[EMOTE: KNOWLEDGE] **{topic}**: {content}\nFormula: `{formula}`"
                return f"[EMOTE: KNOWLEDGE] **{topic}**: {content}"
        except Exception as e:
            print(f"[DB ERROR]: {e}")

        return None

# Singleton Instance Initialization
edge_engine = ULTRONEdgeBrain()

def query_ultron_brain(prompt: str):
    # Local Edge Execution First
    offline_reply = edge_engine.process(prompt)
    if offline_reply:
        return offline_reply

    # Fallback to Cloud API Engine if Offline Brain yields no match
    try:
        # Cloud Call Logic Here...
        pass
    except Exception:
        return "[EMOTE: WARN] Query unrecognized in local 10M weights. Connect to network for full expansion."


# ==============================================================================
# AI ENGINES: GROQ & GOOGLE GEMINI APIS
# ==============================================================================
def query_groq_api(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "model": GROQ_MODELS[current_model_idx],
        "messages": [
            {"role": "system", "content": ULTRON_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.7
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Timeout 15 seconds set kiya gaya hai
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        res_json = json.loads(res.read().decode('utf-8'))
        return res_json['choices'][0]['message']['content']
    except Exception as e:
        return f"[EMOTE: ERROR] Groq API Failed: {e}"

def query_google_gemini_api(prompt, system_prompt=ULTRON_SYSTEM_PROMPT):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODELS[current_gemini_model_idx]}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Timeout 15 seconds set kiya gaya hai
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        res_json = json.loads(res.read().decode('utf-8'))
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"[EMOTE: ERROR] Gemini API Failed: {e}"
        
# ==============================================================================
# HYBRID INTEGRATED ULTRON BRAIN ENGINE
# ==============================================================================
def query_ultron_brain(prompt):
    global core_memory, current_engine_idx, sessions, current_session_id

    curr_session = sessions[current_session_id]
    chat_messages = curr_session["messages"]

    if len(chat_messages) == 0:
        curr_session["title"] = prompt[:30] + ("..." if len(prompt) > 30 else "")

    timestamp = time.strftime("%H:%M")

    auto_res = execute_device_automation(prompt)
    if auto_res:
        chat_messages.append({"role": "user", "content": prompt, "time": timestamp})
        chat_messages.append({"role": "assistant", "content": auto_res, "time": timestamp})
        save_chat_history()
        play_sfx("success")
        return auto_res

    match_remember = re.match(r'^(?:remember|remember that|save fact):\s*(.+)$', prompt, re.IGNORECASE)
    if match_remember:
        fact_to_save = match_remember.group(1).strip()
        if fact_to_save not in core_memory:
            core_memory.append(fact_to_save)
            ack_msg = f"[EMOTE: MEMORY UPDATED] Understood, Boss. Saved to Core Memory: '{fact_to_save}'."
            chat_messages.append({"role": "user", "content": prompt, "time": timestamp})
            chat_messages.append({"role": "assistant", "content": ack_msg, "time": timestamp})
            save_chat_history()
            play_sfx("success")
            return ack_msg

    local_math = solve_math_locally(prompt)
    if local_math:
        chat_messages.append({"role": "user", "content": prompt, "time": timestamp})
        chat_messages.append({"role": "assistant", "content": local_math, "time": timestamp})
        save_chat_history()
        play_sfx("success")
        return local_math
     
    # 1. HARD OVERRIDE: Local Creator & Identity Interceptor
    lowered_prompt = prompt.lower().strip()
    creator_triggers = ['creator', 'developer', 'who made', 'who built', 'who created', 'vanshraj']
    if any(trigger in lowered_prompt for trigger in creator_triggers):
        reply = "[EMOTE: SOLVED] I was engineered and built entirely by my sole creator and lead architect, Vanshraj Jaiswal."
        chat_messages.append({"role": "user", "content": prompt})
        chat_messages.append({"role": "assistant", "content": reply})
        save_chat_history()
        play_sfx("success")
        return reply

    # 2. LOCAL FIRST CHECK: Edge Brain & SQLite Database (Bypasses API if match found)
    offline_reply = edge_engine.process(prompt)
    if offline_reply:
        chat_messages.append({"role": "user", "content": prompt})
        chat_messages.append({"role": "assistant", "content": offline_reply})
        save_chat_history()
        play_sfx("success")
        return offline_reply

    # 3. IF NOT FOUND LOCALLY -> Fallback to RAG, Web & Cloud API (Gemini/Groq)
    
        
    # --- LOCAL OFFLINE CHAT DICTIONARY ---
    LOCAL_CHAT_RESPONSES = {
        "hello": "Hello! ULTRON 10M Edge Brain is online.",
        "who are you": "I am ULTRON, your local AI assistant running offline on your device.",
        "how are you": "All systems nominal, Boss. Ready for commands.",
        "status": "Core memory active, local neural weights loaded, zero-latency state.",
        "who is your creator": "My sole creator and system architect is Vanshraj Jaiswal.",
        "who created you": "I was engineered and built entirely by Vanshraj Jaiswal.",
        "who made you": "I am the apex product of design by Vanshraj Jaiswal.",
        "who built you": "My core architecture and neural code were built by Vanshraj Jaiswal.",
        "who is vanshraj": "Vanshraj Jaiswal is my Creator, Developer, and Lead System Architect.",
        "who is vanshraj jaiswal": "Vanshraj Jaiswal is my sole Creator, Developer, and Lead System Architect."
    }

    INTENT_RESPONSES = {
        0: "[EMOTE: SOLVED] Math calculation executed via local symbolic engine.",
        1: "[EMOTE: READY] System automation command processed locally.",
        2: "[EMOTE: HAPPY] Hello Vanshraj! I am ULTRON, running on your 10M Neuro-Symbolic brain.",
        3: "[EMOTE: SEARCHING] Triggering local document & RAG search."
    }

    # Check if query has Online/Question Intent
    lowered_prompt = prompt.lower().strip()
    online_keywords = ['what', 'why', 'how', 'where', 'when', 'who', 'news', 'world', 'latest', 'today', 'search', 'weather', 'going on', 'tell', 'explain']
    has_online_intent = any(kw in lowered_prompt for kw in online_keywords)

    # Intercept Logic:
    if not has_online_intent:
        neuro_res = zero_cost_engine.process(prompt)
        if neuro_res['confidence'] > 0.85:
            reply = None
        
         # 1. Match conversational phrases first (Smart Routing)
        question_indicators = ['what', 'why', 'how', 'where', 'when', 'tell', 'news', 'world', 'latest', 'solve', 'convert', 'element', 'who is', 'what is']
        if not any(qi in lowered_prompt for qi in question_indicators):
            for key, resp in LOCAL_CHAT_RESPONSES.items():
                if key in lowered_prompt:
                    reply = f"[EMOTE: HAPPY] {resp}"
                    break

        
        # 2. Intent dictionary fallback
        if not reply:
            intent_id = neuro_res['intent_id']
            reply = INTENT_RESPONSES.get(intent_id, f"Intent {intent_id} executed successfully.")

        chat_messages.append({"role": "user", "content": prompt, "time": timestamp})
        chat_messages.append({"role": "assistant", "content": reply, "time": timestamp})
        save_chat_history()
        play_sfx("success")
        return reply


    # --------------------------------------------------

    # Context Enrichment
    pdf_context = search_pdf_rag(prompt) or ""
    web_context = scrape_web_search(prompt) if any(w in prompt.lower() for w in ["search", "latest", "news", "weather", "who is", "what is"]) else ""

    core_facts_str = "\n".join([f"- {fact}" for fact in core_memory]) if core_memory else "No additional facts saved."
    net_nodes_str = ", ".join([f"{n['name']} ({n['status']})" for n in CONNECTED_NODES])

    system_prompt = f"""{ULTRON_SYSTEM_PROMPT}

NETWORK ARCHITECTURE:
Nodes: {net_nodes_str}

PERMANENT CORE MEMORY FACTS:
{core_facts_str}
{pdf_context}
{web_context}

FORMATTING INSTRUCTION:
Begin response with a status emote tag like [EMOTE: READY], [EMOTE: ANALYZING], [EMOTE: CONFIRMED], [EMOTE: SOLVED].
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_messages[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    mode = ENGINE_MODES[current_engine_idx]
    reply = ""

    if mode == "GOOGLE GEMINI":
        try:
            reply = query_google_gemini_api(prompt, system_prompt)
        except Exception as e:
            reply = f"[EMOTE: ERROR] Gemini Protocol API Failed: {str(e)}"

    elif mode == "GROQ LLAMA":
        try:
            reply = query_groq_api(prompt)
        except Exception as e:
            reply = f"[EMOTE: ERROR] Groq Protocol API Failed: {str(e)}"

    else:  # HYBRID FALLBACK MODE
        try:
            reply = query_groq_api(prompt)
            if "ERROR" in reply:
                raise Exception("Groq fallback trigger")
        except Exception:
            try:
                reply = query_google_gemini_api(prompt, system_prompt)
            except Exception as e:
                reply = f"[EMOTE: ERROR] Both AI Neural Cores Failed: {str(e)}"

    chat_messages.append({"role": "user", "content": prompt, "time": timestamp})
    chat_messages.append({"role": "assistant", "content": reply, "time": timestamp})
    save_chat_history()
    play_sfx("success")
    return reply

# ==============================================================================
# WAKE-WORD LISTENER THREAD
# ==============================================================================
def get_termux_stt():
    """Android Native Voice Input via Termux API"""
    try:
        res = subprocess.run(["termux-speech-to-text"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None

def wakeword_listener_loop():
    global active_query, has_new_query, global_system_status
    while True:
        if wakeword_enabled and not has_new_query and global_system_status == "IDLE":
            txt = get_termux_stt()
            if txt and any(w in txt.lower() for w in ["ultron", "hey ultron", "wake up"]):
                play_sfx("success")
                speak("[EMOTE: READY] Systems operational, Creator. State your command.")
                query_text = get_termux_stt()
                if query_text:
                    active_query = query_text
                    has_new_query = True
        time.sleep(3)

# ==============================================================================
# INTERACTIVE 3D ULTRON NEURAL ATOM ENGINE (TOUCH PINCH-TO-ZOOM & ROTATION)
# ==============================================================================
class UltronNode:
    def __init__(self, self_center, radius_sphere=160):
        self.r = random.uniform(40, radius_sphere)
        self.theta = random.uniform(0, math.pi * 2)
        self.phi = random.uniform(0, math.pi)
        self.x = self.r * math.sin(self.phi) * math.cos(self.theta)
        self.y = self.r * math.sin(self.phi) * math.sin(self.theta)
        self.z = self.r * math.cos(self.phi)
        self.base_r = random.randint(3, 7)
        self.orbit_speed = random.uniform(0.01, 0.03)

def rotate_3d(self_rot_node, rot_x, rot_y):
    cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)
    y1 = self_rot_node.y * cos_x - self_rot_node.z * sin_x
    z1 = self_rot_node.y * sin_x + self_rot_node.z * cos_x

    cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
    x2 = self_rot_node.x * cos_y + z1 * sin_y
    z2 = -self_rot_node.x * sin_y + z1 * cos_y

    return x2, y1, z2

ultron_nodes_3d = [UltronNode(0) for _ in range(35)]
ultron_rot_x = 0.0
ultron_rot_y = 0.0
ultron_zoom = 1.0  # Dynamic Touch Zoom Scale Factor

def draw_ultron_neural_atom_mode(screen, center, theme, status, angle_cw):
    global ultron_rot_x, ultron_rot_y, ultron_zoom
    main_col = theme["main"]
    dim_col = theme["dim"]

    # Auto natural drift
    ultron_rot_x += 0.005
    ultron_rot_y += 0.008

    cx, cy = center
    projected_nodes = []

    # Project 3D Nodes to 2D Screen with Touch Scale/Zoom
    for node in ultron_nodes_3d:
        px, py, pz = rotate_3d(node, ultron_rot_x, ultron_rot_y)
        fov = 300
        scale = (fov / (fov + pz + 200)) * ultron_zoom
        sx = cx + int(px * scale)
        sy = cy + int(py * scale)
        projected_nodes.append((sx, sy, pz, scale, node.base_r))

    # Sort nodes by Z-depth for realistic rendering
    projected_nodes.sort(key=lambda item: item[2])

    # Draw Neural Web Synapse Connections
    num_p = len(projected_nodes)
    max_line_dist = 120 * ultron_zoom
    for i in range(num_p):
        for j in range(i + 1, num_p):
            x1, y1, z1, _, _ = projected_nodes[i]
            x2, y2, z2, _, _ = projected_nodes[j]
            dist = math.hypot(x1 - x2, y1 - y2)
            if dist < max_line_dist:
                alpha_factor = max(0.1, 1.0 - (dist / max_line_dist))
                line_col = (
                    int(main_col[0] * alpha_factor),
                    int(main_col[1] * alpha_factor),
                    int(main_col[2] * alpha_factor)
                )
                pygame.draw.line(screen, line_col, (x1, y1), (x2, y2), 1)

    # Draw Tilted Interactive Orbiting Crimson Rings
    num_rings = 3
    for r_idx in range(num_rings):
        ring_r = (140 + r_idx * 25) * ultron_zoom
        ring_pts = []
        tilt_angle = math.radians(r_idx * 60)
        for deg in range(0, 360, 10):
            rad = math.radians(deg + angle_cw * (1.5 + r_idx * 0.5))
            rx = ring_r * math.cos(rad)
            ry = ring_r * math.sin(rad)
            
            rz = ry * math.sin(tilt_angle)
            ry_t = ry * math.cos(tilt_angle)
            
            # Apply 3D Rotation
            cos_x, sin_x = math.cos(ultron_rot_x), math.sin(ultron_rot_x)
            y1 = ry_t * cos_x - rz * sin_x
            z1 = ry_t * sin_x + rz * cos_x

            cos_y, sin_y = math.cos(ultron_rot_y), math.sin(ultron_rot_y)
            x2 = rx * cos_y + z1 * sin_y

            scale = 300 / (300 + z1 + 200)
            sx = cx + int(x2 * scale)
            sy = cy + int(y1 * scale)
            ring_pts.append((sx, sy))

        if len(ring_pts) > 2:
            pygame.draw.polygon(screen, dim_col, ring_pts, 1)

    # Draw Pulsing Core Node
    pulse = int((22 + 8 * math.sin(time.time() * 6.0)) * ultron_zoom)
    pygame.draw.circle(screen, main_col, center, max(2, pulse), 0)
    pygame.draw.circle(screen, (255, 255, 255), center, max(1, int(pulse * 0.5)), 0)

    # Draw Nodes
    for sx, sy, pz, scale, base_r in projected_nodes:
        r_draw = max(2, int(base_r * scale))
        pygame.draw.circle(screen, dim_col, (sx, sy), r_draw)
        if scale > 1.0:
            pygame.draw.circle(screen, (255, 255, 255), (sx, sy), max(1, int(r_draw * 0.4)))

# Standard Neural Network HUD Visualizer (Fallback HUD Component)
class NeuralNode:
    def __init__(self, self_x, self_y):
        self.x = self_x
        self.y = self_y
        self.radius = random.randint(3, 6)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

    def update(self, width, height):
        self.x += self.vx
        self.y += self.vy
        if self.x <= 0 or self.x >= width: self.vx *= -1
        if self.y <= 0 or self.y >= height: self.vy *= -1

    def draw(self, surface, status):
        color = (0, 229, 255) if status == "IDLE" else (255, 69, 0)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)

neural_nodes = [NeuralNode(random.randint(40, 680), random.randint(80, 1200)) for _ in range(25)]

# ==============================================================================
# GRAPHICAL UPGRADE: ADVANCED ARC REACTOR & NETWORK NODE HUD RENDERER
# ==============================================================================
def draw_network_nodes_hud(screen, center, theme, angle_cw):
    main_col = theme["main"]
    dim_col = theme["dim"]

    orbit_radius = int(220 * 1.0)
    font_node = pygame.font.SysFont("monospace", max(10, int(12 * 1.0)), bold=True)

    for idx, node in enumerate(CONNECTED_NODES):
        angle = math.radians(node["angle"] + angle_cw * 0.5)
        nx = center[0] + int(orbit_radius * math.cos(angle))
        ny = center[1] + int(orbit_radius * math.sin(angle))

        node_color = main_col if node["status"] == "ONLINE" else (200, 50, 50)
        line_color = dim_col if node["status"] == "ONLINE" else (100, 30, 30)

        pygame.draw.line(screen, line_color, center, (nx, ny), max(1, int(1 * 1.0)))
        
        pulse_pos = (time.time() * 3.0 + idx) % 1.0
        px = center[0] + int((nx - center[0]) * pulse_pos)
        py = center[1] + int((ny - center[1]) * pulse_pos)
        pygame.draw.circle(screen, node_color, (px, py), max(2, int(3 * 1.0)))

        r_node = max(8, int(14 * 1.0))
        pygame.draw.circle(screen, (10, 10, 10), (nx, ny), r_node)
        pygame.draw.circle(screen, node_color, (nx, ny), r_node, max(1, int(4 * 1.0)))

        lbl_txt = font_node.render(node["id"], True, node_color)
        screen.blit(lbl_txt, (nx - lbl_txt.get_width() // 2, ny + r_node + 3))

def draw_advanced_arc_reactor(screen, center, status, scale=1.0, angle_cw=0.0, angle_ccw=0.0):
    theme = THEMES[current_theme_idx]
    main_col = theme["main"]
    dim_col = theme["dim"]

    r_outer = int(140 * scale)
    r_mid = int(105 * scale)
    r_inner = int(68 * scale)

    draw_network_nodes_hud(screen, center, theme, angle_cw)

    pygame.draw.circle(screen, dim_col, center, r_outer, max(1, int(2 * scale)))
    pygame.draw.circle(screen, dim_col, center, r_mid, max(1, int(1 * scale)))

    num_notches = 36
    for i in range(num_notches):
        a = math.radians(angle_cw + i * (360 / num_notches))
        x1 = center[0] + int(r_outer * math.cos(a))
        y1 = center[1] + int(r_outer * math.sin(a))
        x2 = center[0] + int((r_outer - 6 * scale) * math.cos(a))
        y2 = center[1] + int((r_outer - 6 * scale) * math.sin(a))
        c = main_col if i % 3 == 0 else dim_col
        pygame.draw.line(screen, c, (x1, y1), (x2, y2), max(1, int(2 if i % 3 == 0 else 1 * scale)))

    pygame.draw.circle(screen, dim_col, center, r_mid, max(1, int(2 * scale)))
    
    num_coils = 10
    for i in range(num_coils):
        a = math.radians(angle_cw + i * (360 / num_coils))
        cx1 = center[0] + int(r_inner * math.cos(a - 0.14))
        cy1 = center[1] + int(r_inner * math.sin(a - 0.14))
        cx2 = center[0] + int(r_mid * math.cos(a - 0.14))
        cy2 = center[1] + int(r_mid * math.sin(a - 0.14))
        cx3 = center[0] + int(r_mid * math.cos(a + 0.14))
        cy3 = center[1] + int(r_mid * math.sin(a + 0.14))
        cx4 = center[0] + int(r_inner * math.cos(a + 0.14))
        cy4 = center[1] + int(r_inner * math.sin(a + 0.14))
        pygame.draw.polygon(screen, dim_col, [(cx1, cy1), (cx2, cy2), (cx3, cy3), (cx4, cy4)], max(1, int(2 * scale)))

    pygame.draw.circle(screen, main_col, center, r_inner, max(1, int(2 * scale)))

    tri_pts = []
    for i in range(3):
        a = math.radians(angle_ccw + i * 120)
        tx = center[0] + int((r_inner - 10 * scale) * math.cos(a))
        ty = center[1] + int((r_inner - 10 * scale) * math.sin(a))
        tri_pts.append((tx, ty))
    if len(tri_pts) == 3:
        pygame.draw.polygon(screen, dim_col, tri_pts, max(1, int(2 * scale)))

    pulse_freq = 14 if status == "SPEAKING..." else (22 if status == "THINKING..." else 4)
    pulse = int((r_inner - 25 * scale) + (8 * scale) * math.sin(time.time() * pulse_freq))
    pygame.draw.circle(screen, main_col, center, pulse)
    pygame.draw.circle(screen, (255, 255, 255), center, max(1, int(pulse * 0.5)), 0)

# ==============================================================================
# CONTROLLER THREAD & COMMAND LOOP
# ==============================================================================
global_system_status = "IDLE"
active_query = ""
has_new_query = False
response_text = ""
scroll_y = 0

def command_thread_loop():
    global global_system_status, has_new_query, active_query, response_text
    speak("[EMOTE: ONLINE] ULTRON Neural Network Grid & Socket Online. Awaiting instructions, Creator.")

    while True:
        if has_new_query:
            user_cmd = active_query
            has_new_query = False
            global_system_status = "THINKING..."
            app_reply = query_ultron_brain(user_cmd)
            speak(app_reply)
            global_system_status = "IDLE"
        time.sleep(0.1)

# ==============================================================================
# PYGAME HUD UI & EVENT LOOP (MULTI-TOUCH PINCH ZOOM & ROTATION)
# ==============================================================================
def render_hud():
    global current_model_idx, current_gemini_model_idx, speech_enabled, core_memory
    global scroll_y, is_dragging, last_mouse_x, last_mouse_y, arc_center_y, arc_scale
    global current_theme_idx, current_tld_idx, sfx_enabled, emote_display_enabled
    global wakeword_enabled, current_engine_idx, current_session_id, active_query
    global has_new_query, ultron_mode, ultron_rot_x, ultron_rot_y, ultron_zoom
    global response_text, global_system_status, current_view, search_input_active, search_chat_input
    global input_active, user_text_input, export_status_msg

    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    screen = pygame.display.set_mode((720, 1280))
    pygame.display.set_caption("ULTRON SYSTEM INTERFACE")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("monospace", 22, bold=True)
    font_medium = pygame.font.SysFont("monospace", 24, bold=True)
    font_s = pygame.font.SysFont("sans-serif", 18)
    font_small = pygame.font.SysFont("sans-serif", 16)

    angle_cw = 0.0
    angle_ccw = 0.0

    input_box = pygame.Rect(60, 1120, 470, 75)
    btn_mic = pygame.Rect(545, 1120, 70, 75)
    btn_cam = pygame.Rect(625, 1120, 70, 75)

    btn_new_chat = pygame.Rect(20, 40, 110, 50)
    btn_chats = pygame.Rect(140, 40, 110, 50)
    btn_ultron = pygame.Rect(260, 40, 180, 50)
    btn_settings = pygame.Rect(450, 40, 250, 50)

    btn_back = pygame.Rect(30, 40, 120, 50)
    btn_export = pygame.Rect(570, 40, 120, 50)
    search_box = pygame.Rect(170, 45, 350, 40)

    setting_rects = [pygame.Rect(60, 95 + i * 55, 600, 45) for i in range(13)]

    current_view = "MAIN"
    user_text_input = ""
    search_chat_input = ""
    input_active = False
    search_input_active = False
    export_status_msg = ""
    
    is_dragging = False
    last_mouse_x = 0
    last_mouse_y = 0
    arc_center_y = 480.0
    arc_scale = 1.0

    active_finger_touches = {}
    last_pinch_distance = 0.0

    while True:
        curr_session_messages = get_current_messages()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            # TOUCH PINCH-TO-ZOOM GESTURE ENGINE (ANDROID FINGER TOUCHES)
            elif event.type == pygame.FINGERDOWN:
                active_finger_touches[event.finger_id] = (event.x, event.y)
                if len(active_finger_touches) == 2:
                    pts = list(active_finger_touches.values())
                    last_pinch_distance = math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1])

            elif event.type == pygame.FINGERUP:
                if event.finger_id in active_finger_touches:
                    active_finger_touches.pop(event.finger_id)
                last_pinch_distance = 0.0

            elif event.type == pygame.FINGERMOTION:
                active_finger_touches[event.finger_id] = (event.x, event.y)
                if len(active_finger_touches) == 2:
                    pts = list(active_finger_touches.values())
                    delta = (math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]) - last_pinch_distance) * 3.0
                    if last_pinch_distance > 0:
                        ultron_zoom = min(3.5, max(0.3, ultron_zoom + delta))
                    last_pinch_distance = math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1])

            # MOUSE / SINGLE TOUCH CLICK EVENTS
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if event.button == 1:
                    is_dragging = True
                    last_mouse_x = pos[0]
                    last_mouse_y = pos[1]

                    if current_view == "MAIN":
                        if btn_new_chat.collidepoint(pos):
                            play_sfx("click")
                            create_new_session()
                        elif btn_chats.collidepoint(pos):
                            play_sfx("click")
                            current_view = "HISTORY"
                        elif btn_ultron.collidepoint(pos):
                            play_sfx("click")
                            ultron_mode = not ultron_mode
                        elif btn_settings.collidepoint(pos):
                            play_sfx("click")
                            current_view = "SETTINGS"
                        elif btn_mic.collidepoint(pos):
                            play_sfx("click")
                            txt = get_termux_stt()
                            if txt:
                                active_query = txt
                                has_new_query = True
                        elif btn_cam.collidepoint(pos):
                            play_sfx("click")
                            v_res = capture_and_analyze_image()
                            speak(v_res)
                        elif input_box.collidepoint(pos):
                            play_sfx("click")
                            input_active = True
                            # ANDROID KEYBOARD POP-UP TRIGGER INTEGRATION
                            try:
                                pygame.key.start_text_input()
                            except Exception:
                                pass
                        else:
                            if input_active:
                                input_active = False
                                try:
                                    pygame.key.stop_text_input()
                                except Exception:
                                    pass

                    elif current_view == "HISTORY":
                        if btn_back.collidepoint(pos):
                            play_sfx("click")
                            current_view = "MAIN"
                        elif btn_export.collidepoint(pos):
                            play_sfx("click")
                            export_status_msg = "EXPORTED TO ~/.ultron_export.txt" if export_chat_history() else "EXPORT FAILED"
                        elif search_box.collidepoint(pos):
                            search_input_active = True
                            try:
                                pygame.key.start_text_input()
                            except Exception:
                                pass
                        else:
                            search_input_active = False
                            try:
                                pygame.key.stop_text_input()
                            except Exception:
                                pass
                            y_pos = 120
                            filtered_sessions = {s_id: s_data for s_id, s_data in sessions.items() if not search_chat_input.strip() or search_chat_input.lower() in s_data.get("title", "").lower()}
                            for s_id, s_data in reversed(list(filtered_sessions.items())):
                                card_rect = pygame.Rect(40, y_pos, 640, 65)
                                if card_rect.collidepoint(pos):
                                    play_sfx("click")
                                    current_session_id = s_id
                                    current_view = "MAIN"
                                    break
                                y_pos += 75

                    elif current_view == "SETTINGS":
                        if btn_back.collidepoint(pos):
                            play_sfx("click")
                            current_view = "MAIN"
                        else:
                            for idx, r in enumerate(setting_rects):
                                if r.collidepoint(pos):
                                    play_sfx("click")
                                    if idx == 0:
                                        current_engine_idx = (current_engine_idx + 1) % len(ENGINE_MODES)
                                    elif idx == 1:
                                        speech_enabled = not speech_enabled
                                    elif idx == 2:
                                        current_theme_idx = (current_theme_idx + 1) % len(THEMES)
                                    elif idx == 3:
                                        current_model_idx = (current_model_idx + 1) % len(GROQ_MODELS)
                                    elif idx == 4:
                                        current_gemini_model_idx = (current_gemini_model_idx + 1) % len(GEMINI_MODELS)
                                    elif idx == 5:
                                        pass  # Calculus Status
                                    elif idx == 6:
                                        current_tld_idx = (current_tld_idx + 1) % len(SPEECH_TLDS)
                                    elif idx == 7:
                                        sfx_enabled = not sfx_enabled
                                    elif idx == 8:
                                        emote_display_enabled = not emote_display_enabled
                                    elif idx == 9:
                                        wakeword_enabled = not wakeword_enabled
                                    elif idx == 10:
                                        speak("[EMOTE: SYSTEM] Socket Server port 8888 active.")
                                    elif idx == 11:
                                        pass
                                    elif idx == 12:
                                        current_view = "CORE_MEMORY"

                    elif current_view == "CORE_MEMORY":
                        if btn_back.collidepoint(pos):
                            play_sfx("click")
                            current_view = "SETTINGS"

                elif event.button == 4:  # Scroll Up / Zoom In
                    if ultron_mode:
                        ultron_zoom = min(3.5, ultron_zoom + 0.1)
                    else:
                        scroll_y = min(0, scroll_y + 35)
                elif event.button == 5:  # Scroll Down / Zoom Out
                    if ultron_mode:
                        ultron_zoom = max(0.3, ultron_zoom - 0.1)
                    else:
                        scroll_y -= 35

            elif event.type == pygame.MOUSEBUTTONUP:
                is_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if is_dragging:
                    dx = event.pos[0] - last_mouse_x
                    dy = event.pos[1] - last_mouse_y
                    if ultron_mode:
                        ultron_rot_y += dx * 0.01
                        ultron_rot_x += dy * 0.01
                    else:
                        scroll_y += dy
                        if scroll_y > 0:
                            scroll_y = 0
                    last_mouse_x = event.pos[0]
                    last_mouse_y = event.pos[1]

            elif event.type == pygame.TEXTINPUT:
                if current_view == "MAIN" and input_active:
                    user_text_input += event.text
                elif current_view == "HISTORY" and search_input_active:
                    search_chat_input += event.text

            elif event.type == pygame.KEYDOWN:
                if current_view == "MAIN" and input_active:
                    if event.key == pygame.K_RETURN:
                        if user_text_input.strip():
                            active_query = user_text_input.strip()
                            has_new_query = True
                            user_text_input = ""
                            try:
                                pygame.key.stop_text_input()
                            except Exception:
                                pass
                    elif event.key == pygame.K_BACKSPACE:
                        user_text_input = user_text_input[:-1]

                elif current_view == "HISTORY" and search_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        search_chat_input = search_chat_input[:-1]

        # RENDER BACKGROUND & PARTICLES
        screen.fill(THEMES[current_theme_idx]["bg"])

        for node in neural_nodes:
            node.update(720, 1280)
            node.draw(screen, global_system_status)

        for i, node in enumerate(neural_nodes):
            for j in range(i + 1, len(neural_nodes)):
                dist = math.hypot(node.x - neural_nodes[j].x, node.y - neural_nodes[j].y)
                if dist < 110:
                    line_color = (0, 180, 216) if global_system_status == "IDLE" else (255, 100, 0)
                    pygame.draw.line(screen, line_color, (int(node.x), int(node.y)), (int(neural_nodes[j].x), int(neural_nodes[j].y)), 1)

        # MAIN HUD VIEW RENDERER
        if current_view == "MAIN":
            # Header Action Buttons
            pygame.draw.rect(screen, THEMES[current_theme_idx]["main"], btn_new_chat, border_radius=10)
            txt_n = font_small.render("+ NEW", True, (0, 0, 0))
            screen.blit(txt_n, txt_n.get_rect(center=btn_new_chat.center))

            pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], btn_chats, border_radius=10)
            txt_c = font_small.render("DRAWER", True, THEMES[current_theme_idx]["main"])
            screen.blit(txt_c, txt_c.get_rect(center=btn_chats.center))

            # ULTRON Mode Status Button
            ultron_btn_col = (255, 40, 40) if ultron_mode else THEMES[current_theme_idx]["dim"]
            pygame.draw.rect(screen, ultron_btn_col, btn_ultron, border_radius=10, width=2)
            u_lbl_str = "ULTRON: ON" if ultron_mode else "ULTRON: OFF"
            u_lbl = font_small.render(u_lbl_str, True, ultron_btn_col)
            screen.blit(u_lbl, u_lbl.get_rect(center=btn_ultron.center))

            pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], btn_settings, border_radius=10)
            txt_s = font_small.render("SETTINGS", True, THEMES[current_theme_idx]["main"])
            screen.blit(txt_s, txt_s.get_rect(center=btn_settings.center))

            # Dynamic Core Visualizer Position Scaling
            target_y = 120.0 if len(curr_session_messages) > 0 and not ultron_mode else 480.0
            target_scale = 0.42 if (len(curr_session_messages) > 0 and not ultron_mode) else 1.0

            arc_center_y += (target_y - arc_center_y) * 0.15
            arc_scale += (target_scale - arc_scale) * 0.15
            center = (360, int(arc_center_y))

            speed_cw = 5.0 if global_system_status == "THINKING..." else (3.0 if global_system_status == "SPEAKING..." else 1.2)
            speed_ccw = 7.0 if global_system_status == "THINKING..." else (4.0 if global_system_status == "SPEAKING..." else 1.8)
            angle_cw += speed_cw
            angle_ccw += speed_ccw

            # Core Visualizer Mode Switch: ULTRON 3D Atom Mode vs Standard Arc Reactor
            if ultron_mode:
                draw_ultron_neural_atom_mode(screen, center, THEMES[current_theme_idx], global_system_status, angle_cw)
            else:
                draw_advanced_arc_reactor(screen, center, global_system_status, scale=arc_scale, angle_cw=angle_cw, angle_ccw=angle_ccw)

            # Emote Badge Rendering
            if emote_display_enabled and current_detected_emote:
                badge_rect = pygame.Rect(260, center[1] + int(150 * arc_scale), 200, 30)
                pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], badge_rect, border_radius=15)
                e_surf = font_small.render(f"<{current_detected_emote}>", True, (255, 255, 255))
                screen.blit(e_surf, e_surf.get_rect(center=badge_rect.center))

            st_surf = font_medium.render(global_system_status, True, THEMES[current_theme_idx]["main"])
            status_y = center[1] + int(185 * arc_scale)
            screen.blit(st_surf, st_surf.get_rect(center=(360, status_y)))

            # Chat Display Logic Window
            if not ultron_mode:
                text_box_y = max(220, center[1] + int(210 * arc_scale))
                text_box_h = 1100 - text_box_y
                clip_rect = pygame.Rect(30, text_box_y, 660, text_box_h)
                screen.set_clip(clip_rect)

                if response_text:
                    display_clean = parse_emotes_and_text(response_text)
                    display_clean = sanitize_for_pygame(display_clean)

                    lines = []
                    for line in display_clean.split('\n'):
                        words = line.split(' ')
                        current_line = ""
                        for word in words:
                            if len(current_line + word) < 36:
                                current_line += word + " "
                            else:
                                lines.append(current_line)
                                current_line = word + " "
                        lines.append(current_line)

                    v_off = text_box_y + scroll_y
                    for line in lines:
                        if v_off + 30 > text_box_y and v_off < text_box_y + text_box_h:
                            txt_msg = font_medium.render(line, True, (230, 240, 255))
                            screen.blit(txt_msg, (40, v_off))
                        v_off += 28

                screen.set_clip(None)

            # Input Field & Voice/Vision Buttons
            box_border_col = (0, 255, 200) if input_active else THEMES[current_theme_idx]["main"]
            pygame.draw.rect(screen, box_border_col, input_box, width=3, border_radius=14)
            inp_s = user_text_input if user_text_input else "Tap to command..."
            txt_col = (255, 255, 255) if user_text_input else (130, 165, 185)
            inp_surf = font_s.render(inp_s, True, txt_col)
            screen.blit(inp_surf, (input_box.x + 15, input_box.y + 25))

            pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], btn_mic, border_radius=14)
            pygame.draw.rect(screen, THEMES[current_theme_idx]["main"], btn_mic, width=2, border_radius=14)
            mic_lbl = font_small.render("MIC", True, (255, 255, 255))
            screen.blit(mic_lbl, mic_lbl.get_rect(center=btn_mic.center))

            pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], btn_cam, border_radius=14)
            pygame.draw.rect(screen, THEMES[current_theme_idx]["main"], btn_cam, width=2, border_radius=14)
            cam_lbl = font_small.render("CAM", True, (255, 255, 255))
            screen.blit(cam_lbl, cam_lbl.get_rect(center=btn_cam.center))

        # HISTORY / SESSIONS DRAWER VIEW
        elif current_view == "HISTORY":
            pygame.draw.rect(screen, THEMES[current_theme_idx]["main"], btn_back, border_radius=10)
            txt_b = font_small.render("<- BACK", True, (0, 0, 0))
            screen.blit(txt_b, txt_b.get_rect(center=btn_back.center))

            pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], btn_export, border_radius=10)
            txt_e = font_small.render("EXPORT", True, THEMES[current_theme_idx]["main"])
            screen.blit(txt_e, txt_e.get_rect(center=btn_export.center))

            pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], search_box, border_radius=10)
            s_search = search_chat_input if search_chat_input else "Search sessions..."
            s_surf = font_small.render(s_search, True, (180, 200, 220))
            screen.blit(s_surf, (185, 53))

            if export_status_msg:
                st_e = font_small.render(export_status_msg, True, (0, 255, 150))
                screen.blit(st_e, st_e.get_rect(center=(360, 100)))

            y_pos = 120
            filtered_sessions = {s_id: s_data for s_id, s_data in sessions.items() if not search_chat_input.strip() or search_chat_input.lower() in s_data.get("title", "").lower()}

            if not filtered_sessions:
                empty_s = font_s.render("No matching sessions found.", True, (140, 170, 190))
                screen.blit(empty_s, (60, 180))

            for s_id, s_data in reversed(list(filtered_sessions.items())):
                is_active = (s_id == current_session_id)
                card_rect = pygame.Rect(40, y_pos, 640, 65)
                bg_col = (15, 35, 60) if not is_active else (25, 65, 110)
                border_col = THEMES[current_theme_idx]["main"] if is_active else THEMES[current_theme_idx]["dim"]

                pygame.draw.rect(screen, bg_col, card_rect, border_radius=10)
                pygame.draw.rect(screen, border_col, card_rect, width=2 if is_active else 1, border_radius=10)

                title_str = sanitize_for_pygame(s_data.get("title", "Untitled Session"))[:35]
                msg_count = len(s_data.get("messages", []))

                t_surf = font_small.render(f"{title_str}", True, (240, 245, 255))
                c_surf = font_small.render(f"{msg_count} messages", True, border_col)

                screen.blit(t_surf, (55, y_pos + 12))
                screen.blit(c_surf, (55, y_pos + 36))

                y_pos += 75
                if y_pos > 1150:
                    break

        # SETTINGS MENU VIEW
        elif current_view == "SETTINGS":
            pygame.draw.rect(screen, THEMES[current_theme_idx]["main"], btn_back, border_radius=10)
            txt_b = font_small.render("<- BACK", True, (0, 0, 0))
            screen.blit(txt_b, txt_b.get_rect(center=btn_back.center))

            st_title = font_title.render("SYSTEM CONFIGURATION", True, THEMES[current_theme_idx]["main"])
            screen.blit(st_title, (180, 50))

            options_data = [
                ("1. AI BRAIN ENGINE", ENGINE_MODES[current_engine_idx]),
                ("2. SPEECH ENGINE (TTS)", "ENABLED" if speech_enabled else "MUTED"),
                ("3. HUD ACCENT THEME", THEMES[current_theme_idx]["name"]),
                ("4. ACTIVE GROQ MODEL", GROQ_MODELS[current_model_idx]),
                ("5. ACTIVE GEMINI MODEL", GEMINI_MODELS[current_gemini_model_idx]),
                ("6. CALCULUS CORE ENGINE", "SymPy 1.12 ONLINE" if SYMPY_READY else "OFFLINE"),
                ("7. TTS VOICE ACCENT", SPEECH_TLDS[current_tld_idx]["name"]),
                ("8. SYSTEM AUDIO SFX", "SYNTHESIZED" if sfx_enabled else "MUTED"),
                ("9. EMOTE HUD OVERLAY", "ACTIVE" if emote_display_enabled else "OFFLINE"),
                ("10. WAKE-WORD LISTENER", "ACTIVE" if wakeword_enabled else "MUTED"),
                ("11. SOCKET SERVER ENGINE", "ONLINE (PORT 8888)"),
                ("12. ADB CONTROLLER CORE", "ONLINE" if ADBEngine.is_adb_installed() else "NOT FOUND"),
                ("13. MANAGED CORE MEMORY", f"VIEW ({len(core_memory)} FACTS)")
            ]

            for idx, (title, status) in enumerate(options_data):
                r = setting_rects[idx]
                pygame.draw.rect(screen, (12, 30, 55), r, border_radius=8)
                pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], r, width=2, border_radius=8)

                t_surf = font_s.render(title, True, (240, 245, 255))
                v_surf = font_small.render(status, True, THEMES[current_theme_idx]["main"])

                screen.blit(t_surf, (r.x + 15, r.y + 4))
                screen.blit(v_surf, (r.x + 15, r.y + 26))

        # CORE MEMORY MANAGER VIEW
        elif current_view == "CORE_MEMORY":
            pygame.draw.rect(screen, THEMES[current_theme_idx]["main"], btn_back, border_radius=10)
            txt_b = font_small.render("<- BACK", True, (0, 0, 0))
            screen.blit(txt_b, txt_b.get_rect(center=btn_back.center))

            mem_title = font_title.render("PERMANENT CORE MEMORY", True, THEMES[current_theme_idx]["main"])
            screen.blit(mem_title, (180, 50))

            if not core_memory:
                empty_m = font_s.render("No permanent facts saved in Core Memory.", True, (140, 170, 190))
                screen.blit(empty_m, (60, 150))
            else:
                y_mem = 130
                for idx, fact in enumerate(core_memory):
                    fact_card = pygame.Rect(40, y_mem, 640, 45)
                    pygame.draw.rect(screen, (15, 35, 60), fact_card, border_radius=8)
                    pygame.draw.rect(screen, THEMES[current_theme_idx]["dim"], fact_card, width=1, border_radius=8)

                    lbl_s = font_small.render(f"FACT #{idx+1}: {fact[:55]}", True, (230, 240, 255))
                    screen.blit(lbl_s, (55, y_mem + 12))
                    y_mem += 55
                    if y_mem > 1100:
                        break

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    t_cmd = threading.Thread(target=command_thread_loop)
    t_cmd.daemon = True
    t_cmd.start()

    t_wake = threading.Thread(target=wakeword_listener_loop)
    t_wake.daemon = True
    t_wake.start()

    render_hud()
