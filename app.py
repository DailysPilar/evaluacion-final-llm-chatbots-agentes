"""
app.py — Interfaz Streamlit del Asistente Académico (Nexus)
Diseño: chat conversacional dark, tipografía editorial, ícono SVG custom.
"""

import os
import time
import streamlit as st
from state import create_initial_state

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus — Asistente Académico",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500;600&family=DM+Serif+Display&display=swap');

:root {
    --bg:         #0c0c10;
    --bg2:        #13131a;
    --bg3:        #1a1a24;
    --border:     rgba(255,255,255,0.07);
    --borderhi:   rgba(99,102,241,0.45);
    --text:       #e4e4f0;
    --muted:      #6b6b8a;
    --dim:        #3a3a55;
    --accent:     #6366f1;
    --accent2:    #a78bfa;
    --accent3:    #38bdf8;
    --green:      #34d399;
    --red:        #f87171;
    --mono:       'IBM Plex Mono', monospace;
    --sans:       'DM Sans', sans-serif;
    --serif:      'DM Serif Display', serif;
}

html, body, [class*="css"] { font-family: var(--sans); }

/* Fondo general */
.stApp {
    background:
        radial-gradient(ellipse 70% 50% at 15% 0%, rgba(99,102,241,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 85% 100%, rgba(56,189,248,0.05) 0%, transparent 50%),
        #0c0c10;
}

/* Ocultar chrome de Streamlit */
#MainMenu, footer { visibility: hidden; }

/* Reducir gaps entre elementos de Streamlit */
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { padding: 0 !important; }
.element-container { margin-bottom: 0 !important; }
/* Reducir padding interno del sidebar */
section[data-testid="stSidebar"] > div:first-child { padding: 1rem 1rem 1rem !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #13131a !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    color: #e4e4f0 !important;
    margin-bottom: 0 !important;
}
section[data-testid="stSidebar"] .stCaption > p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.6rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #3a3a55 !important;
    margin-bottom: 4px !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.82rem !important;
    color: #6b6b8a !important;
    line-height: 1.55 !important;
}
section[data-testid="stSidebar"] .stMarkdown strong {
    color: #c4c4d8 !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 0.75rem 0 !important;
}
/* Botón limpiar en sidebar */
section[data-testid="stSidebar"] .stButton > button {
    background: #1a1a24 !important;
    color: #6b6b8a !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    padding: 0.4rem 1rem !important;
    height: auto !important;
    min-width: unset !important;
    width: 100% !important;
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 0.03em !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: rgba(99,102,241,0.4) !important;
    color: #e4e4f0 !important;
    transform: none !important;
    box-shadow: none !important;
    background: #1a1a24 !important;
}
/* Uploader */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: #1a1a24 !important;
    border: 1px dashed rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] .stSuccess > div {
    background: rgba(52,211,153,0.07) !important;
    border: 1px solid rgba(52,211,153,0.2) !important;
    border-radius: 8px !important;
    color: #34d399 !important;
    font-size: 0.78rem !important;
}
section[data-testid="stSidebar"] .stAlert > div {
    border-radius: 8px !important;
    font-size: 0.78rem !important;
}

/* ── TOPBAR ── */
.nexus-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 1.5rem;
    background: rgba(12,12,16,0.92);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    backdrop-filter: blur(12px);
    margin-bottom: 0;
}
.nexus-topbar-left { display: flex; align-items: center; gap: 11px; }
.nexus-topbar-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.92rem;
    font-weight: 600;
    color: #e4e4f0;
    letter-spacing: 0.04em;
}
.nexus-topbar-sub {
    font-size: 0.72rem;
    color: #6b6b8a;
    margin-top: 1px;
}
.nexus-topbar-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    padding: 3px 11px;
    border-radius: 20px;
    border: 1px solid rgba(99,102,241,0.35);
    color: #a78bfa;
    background: rgba(99,102,241,0.07);
    letter-spacing: 0.04em;
}

/* ── CHAT BUBBLES ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    align-items: flex-end;
    gap: 10px;
    padding: 0.25rem 1.5rem;
    animation: fadein 0.25s ease-out;
}
.msg-bot {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    gap: 10px;
    padding: 0.25rem 1.5rem;
    animation: fadein 0.25s ease-out;
}
@keyframes fadein {
    from { opacity:0; transform: translateY(6px); }
    to   { opacity:1; transform: translateY(0); }
}
.av-user {
    width:32px; height:32px; border-radius:50%; flex-shrink:0;
    background: linear-gradient(135deg, #6366f1, #a78bfa);
    display:flex; align-items:center; justify-content:center;
    font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
    font-weight:700; color:#fff; order:2;
}
.av-bot {
    width:32px; height:32px; border-radius:50%; flex-shrink:0;
    background:#1a1a24; border:1px solid rgba(255,255,255,0.08);
    display:flex; align-items:center; justify-content:center;
    font-size:0.9rem;
}
.bub-user {
    max-width:68%;
    background: linear-gradient(135deg, rgba(99,102,241,0.22), rgba(167,139,250,0.15));
    border: 1px solid rgba(99,102,241,0.28);
    border-radius: 16px 16px 4px 16px;
    padding: 0.75rem 1.1rem;
    font-size: 0.9rem;
    color: #e4e4f0;
    line-height: 1.6;
}
.bub-bot {
    max-width: 74%;
    background: #13131a;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px 16px 16px 4px;
    padding: 0.9rem 1.2rem;
    font-size: 0.9rem;
    color: #e4e4f0;
    line-height: 1.65;
}
.meta-row {
    display:flex; align-items:center; gap:7px; flex-wrap:wrap;
    padding: 0.1rem 1.5rem 0.1rem calc(1.5rem + 42px);
    animation: fadein 0.25s ease-out;
}
.ib {
    font-family:'IBM Plex Mono',monospace; font-size:0.58rem;
    font-weight:600; letter-spacing:0.08em; text-transform:uppercase;
    padding:2px 9px; border-radius:20px;
}
.ib-planificar { background:rgba(99,102,241,0.12); color:#818cf8; border:1px solid rgba(99,102,241,0.25); }
.ib-explicar   { background:rgba(56,189,248,0.10);  color:#7dd3fc; border:1px solid rgba(56,189,248,0.25); }
.ib-resumir    { background:rgba(52,211,153,0.10);  color:#6ee7b7; border:1px solid rgba(52,211,153,0.25); }
.ib-desconocido{ background:rgba(248,113,113,0.10); color:#fca5a5; border:1px solid rgba(248,113,113,0.25);}
.topic-chip {
    font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
    color:#6b6b8a; background:#1a1a24;
    border:1px solid rgba(255,255,255,0.07);
    padding:1px 7px; border-radius:4px;
}
.elapsed { font-family:'IBM Plex Mono',monospace; font-size:0.58rem; color:#3a3a55; margin-left:auto; }

/* ── EMPTY STATE ── */
.nexus-empty {
    text-align:center; padding: 2rem 1rem 5rem;
}
.nexus-empty-title {
    font-family:'DM Serif Display',serif;
    font-size:1.8rem; color:#e4e4f0; margin-bottom:0.5rem;
}
.nexus-empty-sub {
    font-size:0.85rem; color:#6b6b8a; max-width:360px;
    margin:0 auto 2rem; line-height:1.6;
}
.nexus-cards {
    display:grid; grid-template-columns:1fr 1fr;
    gap:10px; max-width:520px; margin:0 auto;
}
.nexus-card {
    background:#13131a; border:1px solid rgba(255,255,255,0.07);
    border-radius:12px; padding:0.9rem 1rem; text-align:left;
}
.nexus-card-label {
    font-family:'IBM Plex Mono',monospace;
    font-size:0.6rem; font-weight:600;
    letter-spacing:0.1em; text-transform:uppercase; margin-bottom:4px;
}
.nexus-card-text { font-size:0.8rem; color:#6b6b8a; line-height:1.4; }

/* ── INPUT FIJO ── */
.nexus-input-bar {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    padding: 0.7rem 1.5rem 0.9rem;
    background: rgba(12,12,16,0.97);
    border-top: 1px solid rgba(255,255,255,0.07);
    backdrop-filter: blur(16px);
    z-index: 999;
}
.nexus-input-inner {
    max-width: 780px;
    margin: 0 auto;
    display: flex;
    align-items: flex-end;
    gap: 10px;
}

/* Textarea override */
.stTextArea textarea {
    background: #1a1a24 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 20px !important;
    color: #e4e4f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1.1rem !important;
    resize: none !important;
    line-height: 1.5 !important;
    transition: border-color 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}
.stTextArea textarea::placeholder { color: #3a3a55 !important; }
div[data-testid="stTextArea"] { margin-bottom: 0 !important; }
.stTextArea { margin-bottom: 0 !important; }

/* Botón enviar circular (solo en main, no sidebar) */
.main-area .stButton > button,
div[data-testid="column"] + div[data-testid="column"] .stButton > button {
    background: linear-gradient(135deg, #6366f1, #a78bfa) !important;
    color: white !important;
    border: none !important;
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    padding: 0 !important;
    font-size: 1.1rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: transform 0.15s, box-shadow 0.2s !important;
    flex-shrink: 0 !important;
}
.main-area .stButton > button:hover {
    transform: scale(1.07) !important;
    box-shadow: 0 0 18px rgba(99,102,241,0.4) !important;
}
.main-area .stButton > button:disabled {
    opacity: 0.25 !important; transform: none !important;
}

/* Padding inferior para no quedar tapado por barra fija */
.main-area { padding-bottom: 90px; }

/* Spinner */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #3a3a55; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── SVG ───────────────────────────────────────────────────────────────────────
ICON_SM = '<svg width="30" height="30" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="15" fill="none" stroke="#6366f1" stroke-width="4.5"/><circle cx="50" cy="50" r="6" fill="#6366f1"/><circle cx="50" cy="14" r="7" fill="#6366f1"/><circle cx="50" cy="86" r="7" fill="#6366f1"/><circle cx="14" cy="50" r="7" fill="#a78bfa"/><circle cx="86" cy="50" r="7" fill="#a78bfa"/><circle cx="22" cy="22" r="5" fill="#38bdf8" opacity=".75"/><circle cx="78" cy="78" r="5" fill="#38bdf8" opacity=".75"/><line x1="50" y1="21" x2="50" y2="35" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="50" y1="65" x2="50" y2="79" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="21" y1="50" x2="35" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="65" y1="50" x2="79" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="26" y1="26" x2="36" y2="36" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/><line x1="64" y1="64" x2="74" y2="74" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/></svg>'

ICON_LG = '<svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="15" fill="none" stroke="#6366f1" stroke-width="4.5"/><circle cx="50" cy="50" r="6" fill="#6366f1"/><circle cx="50" cy="14" r="7" fill="#6366f1"/><circle cx="50" cy="86" r="7" fill="#6366f1"/><circle cx="14" cy="50" r="7" fill="#a78bfa"/><circle cx="86" cy="50" r="7" fill="#a78bfa"/><circle cx="22" cy="22" r="5" fill="#38bdf8" opacity=".75"/><circle cx="78" cy="78" r="5" fill="#38bdf8" opacity=".75"/><line x1="50" y1="21" x2="50" y2="35" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="50" y1="65" x2="50" y2="79" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="21" y1="50" x2="35" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="65" y1="50" x2="79" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="26" y1="26" x2="36" y2="36" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/><line x1="64" y1="64" x2="74" y2="74" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/></svg>'

# ── Session state ─────────────────────────────────────────────────────────────
def init():
    for k, v in {"messages": [], "graph": None, "graph_error": None}.items():
        if k not in st.session_state:
            st.session_state[k] = v
init()

# ── Grafo ─────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_graph():
    from workflow import build_graph
    return build_graph()

if st.session_state["graph"] is None and st.session_state["graph_error"] is None:
    try:
        st.session_state["graph"] = load_graph()
    except Exception as e:
        st.session_state["graph_error"] = str(e)

# ── Helpers ───────────────────────────────────────────────────────────────────
def read_file(f) -> str:
    if not f:
        return ""
    name = f.name.lower()
    if name.endswith((".txt", ".md")):
        return f.read().decode("utf-8", errors="replace")
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            return "\n\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(f.read())).pages)
        except Exception:
            return ""
    return ""

def run_graph(user_input: str, doc: str = "") -> dict:
    g = st.session_state["graph"]
    if not g:
        raise RuntimeError("Grafo no disponible.")
    return g.invoke(create_initial_state(user_input=user_input, document_text=doc or None))

def ic(intent):
    return {"planificar":"#818cf8","explicar":"#7dd3fc","resumir":"#6ee7b7"}.get(intent,"#fca5a5")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="display:flex;align-items:center;gap:9px;padding:0.2rem 0 0.8rem;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:0.8rem;">{ICON_SM}<span style="font-family:IBM Plex Mono,monospace;font-size:1.05rem;font-weight:700;letter-spacing:0.1em;color:#e4e4f0;">NEX<span style="color:#6366f1;">US</span></span></div>', unsafe_allow_html=True)

    st.caption("SISTEMA")
    if st.session_state["graph_error"]:
        st.error("⚠ Error al iniciar")
        with st.expander("Ver detalle"):
            st.code(st.session_state["graph_error"])
    else:
        st.success("● Sistema listo")

    st.divider()
    st.caption("DOCUMENTO")
    st.write("Subí un archivo como base de conocimiento.")
    uploaded_file = st.file_uploader(
        "archivo", type=["txt","md","pdf"], label_visibility="collapsed"
    )
    document_text = read_file(uploaded_file) if uploaded_file else ""
    if document_text:
        st.success(f"✓ {uploaded_file.name} · {len(document_text):,} chars")

    st.divider()
    st.caption("QUÉ PODÉS PEDIRME")
    st.write("📅 **Planificar** — cronograma semanal de estudio")
    st.write("💡 **Explicar** — conceptos con ejemplos y analogías")
    st.write("📝 **Resumir** — sintetizá temas o documentos")

    if st.session_state["messages"]:
        st.divider()
        st.caption("HISTORIAL")
        user_msgs = [m for m in st.session_state["messages"] if m["role"] == "user"]
        for msg in reversed(user_msgs[-5:]):
            intent  = msg.get("intent", "—")
            preview = msg["content"][:48] + "…" if len(msg["content"]) > 48 else msg["content"]
            color   = ic(intent)
            st.markdown(f'<span style="font-family:monospace;font-size:0.65rem;color:{color};font-weight:600;">{intent.upper()}</span> <span style="font-size:0.78rem;color:#6b6b8a;">{preview}</span>', unsafe_allow_html=True)
        st.write("")
        if st.button("↺ Limpiar conversación", key="clear", use_container_width=True):
            st.session_state["messages"] = []
            st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
provider = "Gemini" if os.getenv("GEMINI_API_KEY") else "Ollama"
model    = os.getenv("GEMINI_MODEL", os.getenv("DEFAULT_MODEL", "local"))

st.markdown(
    f'<div class="nexus-topbar">'
    f'<div class="nexus-topbar-left">{ICON_SM}'
    f'<div><div class="nexus-topbar-title">Nexus — Asistente Académico</div>'
    f'<div class="nexus-topbar-sub">Planificá · Aprendé · Resumí</div></div></div>'
    f'<div class="nexus-topbar-badge">{provider} · {model}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Chat ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-area">', unsafe_allow_html=True)

if not st.session_state["messages"]:
    st.markdown(
        f'<div class="nexus-empty">'
        f'{ICON_LG}'
        f'<div class="nexus-empty-title">¿En qué te ayudo hoy?</div>'
        f'<div class="nexus-empty-sub">Soy tu asistente académico. Planificá tu estudio, aprendé conceptos y generá resúmenes.</div>'
        f'<div class="nexus-cards">'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#818cf8;">📅 Planificar</div><div class="nexus-card-text">"Quiero estudiar álgebra lineal en dos semanas"</div></div>'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#7dd3fc;">💡 Explicar</div><div class="nexus-card-text">"Explicame qué es una integral definida"</div></div>'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#6ee7b7;">📝 Resumir</div><div class="nexus-card-text">"Resumí el tema de distribuciones de probabilidad"</div></div>'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#a78bfa;">📄 Documento</div><div class="nexus-card-text">Subí un PDF o TXT y pedí que lo resuma</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
else:
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user">'
                f'<div class="bub-user">{msg["content"]}</div>'
                f'<div class="av-user">TÚ</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            intent  = msg.get("intent", "desconocido")
            topics  = msg.get("topics") or []
            elapsed = msg.get("elapsed", 0)
            chips   = "".join(f'<span class="topic-chip">{t}</span>' for t in topics[:4])
            st.markdown(
                f'<div class="meta-row">'
                f'<span class="ib ib-{intent}">▸ {intent}</span>'
                f'{chips}'
                f'<span class="elapsed">{elapsed:.1f}s</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="msg-bot"><div class="av-bot">◈</div><div class="bub-bot">',
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])
            st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # cierre main-area

# ── Input fijo ────────────────────────────────────────────────────────────────
st.markdown('<div class="nexus-input-bar"><div class="nexus-input-inner">', unsafe_allow_html=True)

col_txt, col_btn = st.columns([14, 1])
with col_txt:
    user_input = st.text_area(
        "msg", placeholder="Escribí tu consulta aquí…",
        height=52, label_visibility="collapsed", key="chat_input",
    )
with col_btn:
    send = st.button(
        "↑", key="send_btn",
        disabled=not (user_input or "").strip() or bool(st.session_state["graph_error"]),
        help="Enviar",
    )

st.markdown("</div></div>", unsafe_allow_html=True)

# ── Procesar ──────────────────────────────────────────────────────────────────
if send and (user_input or "").strip():
    st.session_state["messages"].append({
        "role": "user", "content": user_input.strip(),
        "intent": None, "topics": [], "elapsed": 0, "error": None,
    })
    with st.spinner("Procesando…"):
        t0 = time.time()
        try:
            result  = run_graph(user_input.strip(), document_text)
            elapsed = time.time() - t0
            st.session_state["messages"].append({
                "role":    "assistant",
                "content": result.get("final_response") or "_Sin respuesta. Intentá reformular._",
                "intent":  result.get("intent", "desconocido"),
                "topics":  result.get("topics") or [],
                "elapsed": elapsed,
                "error":   result.get("error"),
            })
            st.session_state["messages"][-2]["intent"] = result.get("intent", "desconocido")
        except Exception as e:
            elapsed = time.time() - t0
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"**Error:** `{e}`",
                "intent": "desconocido", "topics": [],
                "elapsed": elapsed, "error": str(e),
            })
    st.rerun()