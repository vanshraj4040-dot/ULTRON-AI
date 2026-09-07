import sys
import os
import asyncio
import json
import sqlite3
import uuid
import requests
from pydantic import BaseModel
MODEL_FILE = "ultron_brain_weights.npz"
MODEL_URL = "https://github.com/vanshraj4040-dot/ULTRON-AI/releases/download/V1.0.0/ultron_brain_weights.npz"

def download_model_if_missing():
    if not os.path.exists(MODEL_FILE):
        print("[ULTRON CORE] Downloading model weights from GitHub Releases...")
        res = requests.get(MODEL_URL, stream=True)
        res.raise_for_status()
        with open(MODEL_FILE, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("[ULTRON CORE] Model download completed successfully!")
    else:
        print("[ULTRON CORE] Model weights detected locally.")

# App start hone se pehle execute karein
download_model_if_missing()

from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# System Paths Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "python_code.py"))
sys.path.append("/sdcard/python_code.py")

# Purana try-except hata kar bas yeh ek line rakho:
from AI2_ULTRON import query_ultron_brain, CONNECTED_NODES

app = FastAPI(title="ULTRON Neural Station")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# SQLITE DATABASE ENGINE
# ---------------------------------------------------------
DB_FILE = os.path.join(current_dir, "ultron_chats.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            sender TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def db_create_session(session_id: str, title: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR IGNORE INTO sessions VALUES (?, ?, ?)", (session_id, title, created_at))
    conn.commit()
    conn.close()

def db_save_message(session_id: str, sender: str, role: str, content: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%H:%M")
    cursor.execute(
        "INSERT INTO messages (session_id, sender, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (session_id, sender, role, content, timestamp)
    )
    conn.commit()
    conn.close()

def db_get_all_sessions():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, title, created_at FROM sessions ORDER BY rowid DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"session_id": r[0], "title": r[1], "created_at": r[2]} for r in rows]

def db_get_session_messages(session_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sender, role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"sender": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in rows]

def db_delete_session(session_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

# REST Endpoints
@app.get("/api/sessions")
async def get_sessions():
    return db_get_all_sessions()

@app.get("/api/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    return db_get_session_messages(session_id)

@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    db_delete_session(session_id)
    return {"status": "success", "deleted": session_id}

@app.get("/manifest.json")
async def manifest():
    return {
        "name": "ULTRON AI",
        "short_name": "ULTRON",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#090A0F",
        "theme_color": "#090A0F",
        "icons": [
            {
                "src": "https://img.icons8.com/color/512/cyborg.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }

# ---------------------------------------------------------
# FRONTEND UI
# ---------------------------------------------------------
HTML_UI = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ULTRON // Neural Engine</title>
  <link rel="manifest" href="/manifest.json">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="ULTRON">

  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/tokyo-night-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

  <style>
    body { background-color: #090A0F; color: #E2E8F0; font-family: system-ui, -apple-system, sans-serif; }
    .glass { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(16px); border: 1px solid rgba(255, 0, 60, 0.2); }
    .glass-sidebar { background: rgba(10, 14, 26, 0.95); backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.08); }
    .glow-border { box-shadow: 0 0 15px rgba(255, 0, 60, 0.25); }
    pre code { font-family: 'JetBrains Mono', monospace; border-radius: 0.5rem; }
  </style>
</head>
<body class="h-screen flex overflow-hidden">

  <!-- SIDEBAR -->
  <aside id="sidebar" class="w-72 glass-sidebar flex flex-col justify-between transition-all duration-300 z-20 absolute md:relative h-full -translate-x-full md:translate-x-0">
    <div class="p-4 space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i data-lucide="cpu" class="text-red-500 w-6 h-6 animate-pulse"></i>
          <span class="font-bold text-lg tracking-wider text-white">ULTRON OS</span>
        </div>
        <button onclick="toggleSidebar()" class="md:hidden text-slate-400 hover:text-white"><i data-lucide="x"></i></button>
      </div>

      <button onclick="createNewSession()" class="w-full py-2.5 px-4 rounded-xl bg-red-600/20 hover:bg-red-600/40 border border-red-500/40 text-red-400 flex items-center justify-center gap-2 font-semibold text-xs tracking-wide transition">
        <i data-lucide="plus" class="w-4 h-4"></i> NEW THREAD
      </button>

      <div class="space-y-2">
        <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">SAVED HISTORY</p>
        <div id="sessionList" class="space-y-1 overflow-y-auto max-h-[60vh]"></div>
      </div>
    </div>

    <div class="p-4 border-t border-slate-800/80 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-red-600/30 border border-red-500 flex items-center justify-center font-bold text-xs text-red-400">VJ</div>
        <div>
          <p class="text-xs font-bold text-white">Vanshraj</p>
          <p class="text-[10px] text-green-400 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span> DB Sync Active</p>
        </div>
      </div>
    </div>
  </aside>

  <!-- MAIN WORKSPACE -->
  <main class="flex-1 flex flex-col justify-between h-full relative overflow-hidden">
    <header class="glass p-3 px-4 flex justify-between items-center z-10">
      <div class="flex items-center gap-3">
        <button onclick="toggleSidebar()" class="md:hidden text-slate-300"><i data-lucide="menu"></i></button>
        <select id="modelSelect" class="bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-red-500 font-medium">
          <option value="auto">🧠 Auto (Hybrid Edge-Cloud Core)</option>
          <option value="groq">⚡ Groq OpenAI (Fast Cloud)</option>
          <option value="gemini">♊ Gemini 3.6 Flash (Analytical)</option>
          <option value="local">💻 Local 10M Edge Brain (Offline)</option>
        </select>
      </div>

      <span id="statusBadge" class="text-xs px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/30 font-semibold flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-green-400 animate-ping"></span> ONLINE
      </span>
    </header>

    <div id="chatBox" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
      <div class="text-center my-6 space-y-2" id="heroBlock">
        <div class="inline-block p-3 rounded-full bg-red-600/10 border border-red-500/20 text-red-500 mb-2">
          <i data-lucide="bot" class="w-8 h-8"></i>
        </div>
        <h2 class="text-xl font-bold text-white">ULTRON Neural Station</h2>
        <p class="text-xs text-slate-400 max-w-md mx-auto">Database-backed Workspace. Manage sessions directly from the sidebar.</p>
      </div>
    </div>

    <footer class="p-3 md:p-4 max-w-4xl w-full mx-auto">
      <div class="glass rounded-2xl p-2 flex flex-col gap-2 glow-border">
        <textarea id="promptInput" rows="1" placeholder="Command ULTRON..." 
                  class="bg-transparent px-3 py-2 text-sm text-white focus:outline-none resize-none max-h-32"></textarea>
        
        <div class="flex justify-between items-center px-2 pt-1 border-t border-slate-800">
          <div class="flex gap-1 text-slate-400">
            <button onclick="startVoiceRecognition()" title="Voice Input" class="p-2 hover:bg-slate-800 rounded-lg transition hover:text-red-400"><i data-lucide="mic" class="w-4 h-4"></i></button>
            <button onclick="toggleAudioOutput()" id="ttsBtn" title="Toggle Speech Output" class="p-2 hover:bg-slate-800 rounded-lg transition hover:text-cyan-400"><i data-lucide="volume-2" class="w-4 h-4"></i></button>
          </div>

          <button onclick="sendPrompt()" class="bg-red-600 hover:bg-red-700 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 shadow-lg transition">
            <span>SEND</span> <i data-lucide="send" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    </footer>
  </main>

  <script>
    lucide.createIcons();
    marked.setOptions({
      highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value;
        return hljs.highlightAuto(code).value;
      },
      breaks: true
    });

    let currentSessionId = localStorage.getItem('active_ultron_session') || "session_" + Math.random().toString(36).substring(7);
    localStorage.setItem('active_ultron_session', currentSessionId);

    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    let ws = new WebSocket(`${wsProtocol}//${location.host}/ws/ultron/${currentSessionId}`);
    let ttsEnabled = false;

    const chatBox = document.getElementById('chatBox');
    const promptInput = document.getElementById('promptInput');
    const statusBadge = document.getElementById('statusBadge');
    const sessionList = document.getElementById('sessionList');

    async function loadSessions() {
      const res = await fetch('/api/sessions');
      const sessions = await res.json();
      sessionList.innerHTML = '';
      
      sessions.forEach(s => {
        const activeClass = s.session_id === currentSessionId ? 'bg-red-600/20 text-red-400 border-red-500/40' : 'text-slate-400 hover:bg-slate-800/60';
        const item = document.createElement('div');
        item.className = `p-2 rounded-xl border border-transparent cursor-pointer text-xs flex items-center justify-between transition group ${activeClass}`;
        item.onclick = () => switchSession(s.session_id);
        
        item.innerHTML = `
          <div class="flex items-center gap-2 overflow-hidden flex-1">
            <i data-lucide="message-square" class="w-3.5 h-3.5 shrink-0"></i>
            <span class="truncate font-medium">${s.title}</span>
          </div>
          <button onclick="deleteSession(event, '${s.session_id}')" title="Delete Session" class="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 rounded transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        `;
        sessionList.appendChild(item);
      });
      lucide.createIcons();
    }

    async function deleteSession(event, sessionId) {
      event.stopPropagation();
      await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      if(sessionId === currentSessionId) {
        createNewSession();
      } else {
        loadSessions();
      }
    }

    async function switchSession(sessionId) {
      currentSessionId = sessionId;
      localStorage.setItem('active_ultron_session', currentSessionId);
      
      if(ws) ws.close();
      ws = new WebSocket(`${wsProtocol}//${location.host}/ws/ultron/${currentSessionId}`);
      attachWsEvents();
      
      chatBox.innerHTML = '';
      const res = await fetch(`/api/sessions/${sessionId}/messages`);
      const msgs = await res.json();
      
      if(msgs.length === 0) {
        chatBox.innerHTML = `<div class="text-center my-6 text-xs text-slate-400">Empty thread initialized.</div>`;
      } else {
        msgs.forEach(m => appendMessage(m.sender, m.content, m.role));
      }
      loadSessions();
    }

    function createNewSession() {
      const newId = "session_" + Math.random().toString(36).substring(7);
      switchSession(newId);
    }

    function attachWsEvents() {
      ws.onopen = () => statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-green-400 animate-ping"></span> ONLINE`;
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if(data.type === "REPLY") {
          appendMessage("ULTRON", data.text, "ai");
          loadSessions();
          if(ttsEnabled) speakText(data.text);
        }
      };
    }

    attachWsEvents();
    loadSessions();

    function sendPrompt() {
      const text = promptInput.value.trim();
      if(!text) return;
      appendMessage("YOU", text, "user");
      ws.send(JSON.stringify({ prompt: text, model: document.getElementById('modelSelect').value }));
      promptInput.value = "";
    }

    function appendMessage(sender, text, role) {
      const hero = document.getElementById('heroBlock');
      if(hero) hero.remove();

      const div = document.createElement('div');
      div.className = `flex gap-3 max-w-3xl ${role === 'user' ? 'ml-auto flex-row-reverse' : ''}`;
      const parsedText = role === 'ai' ? marked.parse(text) : text;
      
      div.innerHTML = `
        <div class="w-8 h-8 rounded-xl ${role === 'user' ? 'bg-cyan-600/30 text-cyan-400 border-cyan-500/40' : 'bg-red-600/30 text-red-400 border-red-500/40'} border flex items-center justify-center font-bold text-xs shrink-0">
          ${role === 'user' ? 'YOU' : 'AI'}
        </div>
        <div class="p-3.5 rounded-2xl ${role === 'user' ? 'bg-cyan-950/40 border border-cyan-800/40 text-slate-100' : 'bg-slate-900/80 border border-slate-800 text-slate-200'} text-sm leading-relaxed overflow-x-auto space-y-2 max-w-full">
          <div class="font-bold text-xs ${role === 'user' ? 'text-cyan-400' : 'text-red-400'} mb-1">${sender}</div>
          <div class="prose prose-invert max-w-none text-xs md:text-sm">${parsedText}</div>
        </div>
      `;
      chatBox.appendChild(div);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    promptInput.addEventListener('keydown', (e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendPrompt(); } });
    function toggleSidebar() { document.getElementById('sidebar').classList.toggle('-translate-x-full'); }
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTML_UI

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, ws: WebSocket):
        await ws.accept()
        self.active[client_id] = ws

    def disconnect(self, client_id: str):
        if client_id in self.active:
            del self.active[client_id]

    async def send(self, client_id: str, data: dict):
        if client_id in self.active:
            await self.active[client_id].send_text(json.dumps(data))

manager = ConnectionManager()

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    response_text = await asyncio.to_thread(query_ultron_brain, req.prompt)
    return {"text": response_text}
    
@app.websocket("/ws/ultron/{client_id}")
async def websocket_endpoint(ws: WebSocket, client_id: str):
    await manager.connect(client_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
                prompt = data.get("prompt", raw)
            except json.JSONDecodeError:
                prompt = raw

            await manager.send_json(client_id, {
                "type": "STATUS_UPDATE",
                "state": "THINKING"
            })
            payload = json.loads(raw)
            prompt = payload.get("prompt", "")

            session_title = prompt[:22] + "..." if len(prompt) > 22 else prompt
            db_create_session(client_id, session_title)
            db_save_message(client_id, "YOU", "user", prompt)

            await manager.send(client_id, {"type": "STATUS"})
            reply = await asyncio.to_thread(query_ultron_brain, prompt)
            db_save_message(client_id, "ULTRON", "ai", reply)

            await manager.send(client_id, {"type": "REPLY", "text": reply})
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
