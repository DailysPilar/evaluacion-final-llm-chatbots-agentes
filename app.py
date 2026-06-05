"""
app.py — Interfaz Streamlit del Asistente Académico (Nexus)
Diseño: chat conversacional dark, tipografía editorial, ícono SVG custom.
"""

import html
import os
import time
import mistune
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
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');

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

    /*
     * Ancho del sidebar de Streamlit.
     * Streamlit lo fija en ~21rem cuando está expandido.
     * Se usa en el footer fijo para que arranque justo donde termina el sidebar.
     */
    --sidebar-width: 21rem;
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

/* Quitar padding/max-width del bloque principal para ocupar todo el ancho */
.block-container {
    padding-top: 3.35rem !important;
    /* El footer fijo mide ~80px; dejamos ese espacio para que el último
       mensaje no quede tapado al llegar al final del scroll. */
    padding-bottom: 100px !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}
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

/* ── TOPBAR ── */
.nexus-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.55rem 1.5rem;
    background: rgba(12,12,16,0.94);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    backdrop-filter: blur(12px);
    position: sticky;
    top: 3.1rem;
    z-index: 100;
    margin-left: -1rem;
    margin-right: -1rem;
    margin-bottom: 1rem;
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
.bub-user,
.bub-bot {
    overflow-wrap: anywhere;
}
.message-content p { margin: 0 0 0.65rem; }
.message-content p:last-child,
.message-content ul:last-child,
.message-content ol:last-child,
.message-content pre:last-child { margin-bottom: 0; }
.message-content ul,
.message-content ol {
    margin: 0.35rem 0 0.8rem;
    padding-left: 1.1rem;
}
.message-content li { margin: 0.2rem 0; }
.message-content code {
    font-family: var(--mono);
    font-size: 0.82rem;
    color: #c4c4d8;
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 5px;
    padding: 0.08rem 0.25rem;
}
.message-content pre {
    overflow-x: auto;
    margin: 0.55rem 0 0.85rem;
    padding: 0.75rem 0.9rem;
    background: #0c0c10;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
}
.message-content pre code {
    padding: 0;
    border: 0;
    background: transparent;
}
.typing-content {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #a9a9c4;
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.typing-dots {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.typing-dots span {
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: #a78bfa;
    animation: typingPulse 1.15s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.16s; }
.typing-dots span:nth-child(3) { animation-delay: 0.32s; }
@keyframes typingPulse {
    0%, 80%, 100% { opacity: 0.28; transform: translateY(0); }
    40% { opacity: 1; transform: translateY(-3px); }
}
/* ── FILE BADGE (archivo adjunto seleccionado) ── */
.file-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 3px 10px 3px 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #a78bfa;
    max-width: 220px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.file-badge svg { flex-shrink: 0; }

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

/* ═══════════════════════════════════════════════════════════════
   COMPOSITOR FOOTER — FIXED AL FONDO DE LA VENTANA
   ═══════════════════════════════════════════════════════════════
   Se usa position: fixed en lugar de sticky para que el footer
   permanezca siempre visible independientemente del scroll.

   left: var(--sidebar-width) → arranca justo donde termina el sidebar
   right: 0                   → llega hasta el borde derecho de la pantalla

   El JS de abajo ajusta --sidebar-width dinámicamente para cubrir
   los estados expandido/colapsado del sidebar de Streamlit.
   ═══════════════════════════════════════════════════════════════ */
.st-key-nexus_input_bar {
    position: fixed !important;
    bottom: 0 !important;
    right: 0 !important;
    margin: 1rem -1rem 0;
    background:
        linear-gradient(180deg, rgba(12,12,16,0.76), rgba(12,12,16,0.98) 28%),
        #0c0c10;
    border-top: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(18px);
    z-index: 90;
    padding: 0.9rem clamp(1rem, 3vw, 2rem);
    box-sizing: border-box;
}

.st-key-nexus_input_bar > div {
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
}

/* Contenedor de columnas dentro del compositor */
.st-key-nexus_input_bar div[data-testid="stHorizontalBlock"] {
    gap: 0.75rem;
    align-items: center;
}

/* Estilo del botón de adjuntar (file uploader) */
.st-key-nexus_input_bar div[data-testid="stFileUploader"] {
    width: auto !important;
    min-width: 44px;
}

.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"] {
    background: #16161f !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
    padding: 0 !important;
    width: 44px !important;
    height: 44px !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #a78bfa !important;
    background: #1a1a24 !important;
}

/* Icono del clip usando Font Awesome */
.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"]::before {
    content: "\\f0c6";
    font-family: "Font Awesome 6 Free";
    font-weight: 900;
    font-size: 1.2rem;
    color: #6b6b8a;
    position: absolute;
}

.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"]:hover::before {
    color: #a78bfa;
}

/* Ocultar texto interno del uploader */
.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"] span,
.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"] p,
.st-key-nexus_input_bar section[data-testid="stFileUploaderDropzone"] small {
    display: none !important;
}

/* Textarea */
.st-key-nexus_input_bar textarea {
    min-height: 44px !important;
    height: 44px !important;
    background: #16161f !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
    color: #e4e4f0 !important;
    font-family: var(--sans) !important;
    font-size: 0.9rem !important;
    line-height: 1.45 !important;
    padding: 10px 14px !important;
    resize: none !important;
}

.st-key-nexus_input_bar textarea:focus {
    border-color: #6366f1 !important;
    outline: none !important;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.3) !important;
}

.st-key-nexus_input_bar textarea::placeholder {
    color: #3a3a55 !important;
}

/* Botón de enviar con flecha hacia arriba */
.st-key-nexus_input_bar .stButton {
    width: auto !important;
}

.st-key-nexus_input_bar .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    width: 44px !important;
    height: 44px !important;
    padding: 0 !important;
    margin: 0 !important;
    color: white !important;
    font-size: 1.3rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

.st-key-nexus_input_bar .stButton > button:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.08);
}

.st-key-nexus_input_bar .stButton > button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

/* Ajuste de las columnas para mejor centrado */
.st-key-nexus_input_bar div[data-testid="column"] {
    display: flex;
    align-items: center;
}

/* El area de chat necesita padding inferior para que el último mensaje
   no quede tapado por el footer fijo (~80px de alto + margen). */
.main-area {
    padding-bottom: 1.25rem;
}
.main-area > div:last-child {
    margin-bottom: 0;
}

/* ── RESPONSIVE: sidebar colapsado ──
   Cuando el sidebar está colapsado Streamlit lo reduce a ~4rem.
   La clase data-collapsed="true" se detecta con JS y ajusta la variable. */
@media (max-width: 780px) {
    .st-key-nexus_input_bar {
        margin-inline: -1rem;
        padding-inline: 1rem;
    }
    .st-key-nexus_input_bar div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a3d; border-radius: 2px; }
</style>

<script>
// ─────────────────────────────────────────────────────────────────────────────
// FOOTER LEFT TRACKING — basado en aria-expanded del sidebar de Streamlit
//
// Streamlit pone aria-expanded="true/false" en el botón de colapsar sidebar.
// Cuando está expandido el sidebar mide exactamente 336px (valor hardcodeado
// en el CSS de Streamlit). Cuando está colapsado mide 0.
// Usamos ese atributo en lugar de medir píxeles para evitar saltos durante
// la transición CSS del sidebar.
// ─────────────────────────────────────────────────────────────────────────────
(function() {
    var SIDEBAR_OPEN_W  = '336px';
    var SIDEBAR_CLOSE_W = '0px';

    function getSidebarExpanded() {
        // Streamlit ≥ 1.x: el botón colapsar tiene data-testid="collapsedControl"
        // y aria-expanded refleja si el sidebar está abierto.
        var btn = document.querySelector('[data-testid="collapsedControl"]');
        if (btn) {
            // aria-expanded="true"  → sidebar VISIBLE   → footer arranca en 336px
            // aria-expanded="false" → sidebar COLAPSADO → footer arranca en 0
            return btn.getAttribute('aria-expanded') !== 'false';
        }
        // Fallback: si no encontramos el botón asumimos expandido
        return true;
    }

    function applyWidth() {
        var w = getSidebarExpanded() ? SIDEBAR_OPEN_W : SIDEBAR_CLOSE_W;
        document.documentElement.style.setProperty('--sidebar-width', w);
    }

    // Aplicar en cuanto el DOM esté listo
    applyWidth();
    setTimeout(applyWidth, 200);   // por si Streamlit tarda en pintar el botón

    // Observar cambios de atributo en el botón (clic expandir/colapsar)
    var mo = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
            if (mutations[i].type === 'attributes' &&
                mutations[i].attributeName === 'aria-expanded') {
                applyWidth();
                return;
            }
        }
    });

    function attachObserver() {
        var btn = document.querySelector('[data-testid="collapsedControl"]');
        if (btn && !btn.__nexusObserved) {
            btn.__nexusObserved = true;
            mo.observe(btn, { attributes: true, attributeFilter: ['aria-expanded'] });
        }
    }

    attachObserver();

    // Si el botón aparece después del primer render (Streamlit a veces lo inyecta tarde)
    var bodyObs = new MutationObserver(function() {
        attachObserver();
        applyWidth();
    });
    bodyObs.observe(document.body, { childList: true, subtree: false });
})();

// ─────────────────────────────────────────────────────────────────────────────
// CTRL+ENTER para enviar mensaje
// ─────────────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    function setupCtrlEnter() {
        var textarea = document.querySelector('.st-key-nexus_input_bar textarea');
        if (textarea && !textarea.hasAttribute('data-ctrl-enter-listener')) {
            textarea.setAttribute('data-ctrl-enter-listener', 'true');
            textarea.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    var sendButton = document.querySelector('.st-key-nexus_input_bar .stButton button');
                    if (sendButton && !sendButton.disabled) {
                        sendButton.click();
                    }
                }
            });
        }
    }

    setupCtrlEnter();
    setTimeout(setupCtrlEnter, 500);
    setTimeout(setupCtrlEnter, 1000);

    var observer = new MutationObserver(function() {
        setupCtrlEnter();
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# ── SVG ───────────────────────────────────────────────────────────────────────
ICON_SM = '<svg width="30" height="30" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="15" fill="none" stroke="#6366f1" stroke-width="4.5"/><circle cx="50" cy="50" r="6" fill="#6366f1"/><circle cx="50" cy="14" r="7" fill="#6366f1"/><circle cx="50" cy="86" r="7" fill="#6366f1"/><circle cx="14" cy="50" r="7" fill="#a78bfa"/><circle cx="86" cy="50" r="7" fill="#a78bfa"/><circle cx="22" cy="22" r="5" fill="#38bdf8" opacity=".75"/><circle cx="78" cy="78" r="5" fill="#38bdf8" opacity=".75"/><line x1="50" y1="21" x2="50" y2="35" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="50" y1="65" x2="50" y2="79" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="21" y1="50" x2="35" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="65" y1="50" x2="79" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="26" y1="26" x2="36" y2="36" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/><line x1="64" y1="64" x2="74" y2="74" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/></svg>'

ICON_LG = '<svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="15" fill="none" stroke="#6366f1" stroke-width="4.5"/><circle cx="50" cy="50" r="6" fill="#6366f1"/><circle cx="50" cy="14" r="7" fill="#6366f1"/><circle cx="50" cy="86" r="7" fill="#6366f1"/><circle cx="14" cy="50" r="7" fill="#a78bfa"/><circle cx="86" cy="50" r="7" fill="#a78bfa"/><circle cx="22" cy="22" r="5" fill="#38bdf8" opacity=".75"/><circle cx="78" cy="78" r="5" fill="#38bdf8" opacity=".75"/><line x1="50" y1="21" x2="50" y2="35" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="50" y1="65" x2="50" y2="79" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/><line x1="21" y1="50" x2="35" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="65" y1="50" x2="79" y2="50" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/><line x1="26" y1="26" x2="36" y2="36" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/><line x1="64" y1="64" x2="74" y2="74" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" opacity=".7"/></svg>'

# ── Session state ─────────────────────────────────────────────────────────────
def init():
    defaults = {
        "messages": [],
        "graph": None,
        "graph_error": None,
        "attached_file_name": None,
        "attached_file_text": None,
        "chat_input_key": 0,
        "pending_response": None,
    }
    for k, v in defaults.items():
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
    """Lee el contenido de un archivo subido (txt, md, pdf)."""
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
    if not intent:
        return "#fca5a5"
    return {"planificar":"#818cf8","explicar":"#7dd3fc","resumir":"#6ee7b7"}.get(intent,"#fca5a5")

render_markdown = mistune.create_markdown(escape=True)

def plain_html(text: str) -> str:
    return html.escape(text or "").replace("\n", "<br>")

def markdown_html(text: str) -> str:
    return render_markdown(text or "")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:9px;padding:0.2rem 0 0.8rem;'
        f'border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:0.8rem;">'
        f'{ICON_SM}<span style="font-family:IBM Plex Mono,monospace;font-size:1.05rem;'
        f'font-weight:700;letter-spacing:0.1em;color:#e4e4f0;">NEX<span style="color:#6366f1;">US</span></span></div>',
        unsafe_allow_html=True,
    )

    st.caption("SISTEMA")
    if st.session_state["graph_error"]:
        st.error("⚠ Error al iniciar")
        with st.expander("Ver detalle"):
            st.code(st.session_state["graph_error"])
    else:
        st.success("● Sistema listo")

    st.divider()
    st.caption("QUÉ PODÉS PEDIRME")
    st.write("📅 **Planificar** — cronograma semanal de estudio")
    st.write("💡 **Explicar** — conceptos con ejemplos y analogías")
    st.write("📝 **Resumir** — sintetizá temas o documentos")
    st.write("📎 **Adjuntar** — usá el clip en el chat para subir un PDF/TXT")
    st.write("⌨️ **Ctrl+Enter** — enviar mensaje")

    if st.session_state["messages"]:
        st.divider()
        st.caption("HISTORIAL")
        user_msgs = [m for m in st.session_state["messages"] if m["role"] == "user"]
        for msg in reversed(user_msgs[-5:]):
            intent  = msg.get("intent") or "—"
            preview = msg["content"][:48] + "…" if len(msg["content"]) > 48 else msg["content"]
            color   = ic(intent)
            intent_str = intent if isinstance(intent, str) else "—"
            st.markdown(
                f'<span style="font-family:monospace;font-size:0.65rem;color:{color};font-weight:600;">'
                f'{html.escape(intent_str.upper())}</span> '
                f'<span style="font-size:0.78rem;color:#6b6b8a;">{html.escape(preview)}</span>',
                unsafe_allow_html=True,
            )
        st.write("")
        if st.button("↺ Limpiar conversación", key="clear", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["attached_file_name"] = None
            st.session_state["attached_file_text"] = None
            st.session_state["pending_response"] = None
            st.session_state["chat_input_key"] += 1
            st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
provider = "Gemini" if os.getenv("GEMINI_API_KEY") else "Ollama"
model    = os.getenv("GEMINI_MODEL", os.getenv("DEFAULT_MODEL", "local"))

# Topbar sticky
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
pending_response = st.session_state.get("pending_response")

if not st.session_state["messages"] and not pending_response:
    st.markdown(
        f'<div class="nexus-empty">'
        f'{ICON_LG}'
        f'<div class="nexus-empty-title">¿En qué te ayudo hoy?</div>'
        f'<div class="nexus-empty-sub">Soy tu asistente académico. Planificá tu estudio, aprendé conceptos y generá resúmenes.</div>'
        f'<div class="nexus-cards">'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#818cf8;">📅 Planificar</div>'
        f'<div class="nexus-card-text">"Quiero estudiar álgebra lineal en dos semanas"</div></div>'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#7dd3fc;">💡 Explicar</div>'
        f'<div class="nexus-card-text">"Explicame qué es una integral definida"</div></div>'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#6ee7b7;">📝 Resumir</div>'
        f'<div class="nexus-card-text">"Resumí el tema de distribuciones de probabilidad"</div></div>'
        f'<div class="nexus-card"><div class="nexus-card-label" style="color:#a78bfa;">📎 Adjuntar</div>'
        f'<div class="nexus-card-text">Usá el clip en el chat para subir un PDF o TXT y pedí que lo resuma</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
else:
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            file_badge = ""
            if msg.get("attached_file"):
                attached_file = html.escape(msg["attached_file"])
                file_badge = (
                    f'<div style="display:flex;justify-content:flex-end;padding:0 1.5rem 3px;">'
                    f'<span class="file-badge">'
                    f'<i class="fas fa-paperclip" style="font-size:0.65rem;"></i> {attached_file}'
                    f'</span></div>'
                )
            st.markdown(
                f'{file_badge}'
                f'<div class="msg-user">'
                f'<div class="bub-user">{plain_html(msg["content"])}</div>'
                f'<div class="av-user">TÚ</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="msg-bot">'
                f'<div class="av-bot">N</div>'
                f'<div class="bub-bot"><div class="message-content">{markdown_html(msg["content"])}</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    if pending_response:
        st.markdown(
            f'<div class="msg-bot">'
            f'<div class="av-bot">N</div>'
            f'<div class="bub-bot">'
            f'<div class="typing-content">Pensando'
            f'<span class="typing-dots"><span></span><span></span><span></span></span>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# ── Input fijo: archivo, mensaje y enviar ─────────────────────────────────────
has_file = bool(st.session_state["attached_file_name"])
fname    = st.session_state["attached_file_name"] or ""
input_key = f"chat_input_{st.session_state['chat_input_key']}"
is_thinking = bool(pending_response)

with st.container(key="nexus_input_bar"):
    if has_file:
        st.markdown(
            f'<div class="composer-file-badge"><span class="file-badge">'
            f'<i class="fas fa-paperclip"></i> {html.escape(fname)}'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    col_file, col_text, col_send = st.columns(
        [0.1, 0.8, 0.1],
        gap="small",
        vertical_alignment="center",
    )

    with col_file:
        upload_key = f"fu_{len(st.session_state['messages'])}_{st.session_state['chat_input_key']}"
        uploaded_file = st.file_uploader(
            "Adjuntar archivo",
            type=["txt", "md", "pdf"],
            label_visibility="collapsed",
            key=upload_key,
        )
        if uploaded_file is not None and st.session_state["attached_file_name"] != uploaded_file.name:
            st.session_state["attached_file_name"] = uploaded_file.name
            st.session_state["attached_file_text"] = read_file(uploaded_file)
            st.rerun()

    with col_text:
        user_input = st.text_area(
            "Mensaje",
            placeholder="Escribí tu consulta aquí… (Ctrl+Enter para enviar)",
            height=42,
            label_visibility="collapsed",
            key=input_key,
            disabled=is_thinking,
        )

    with col_send:
        has_text = bool((user_input or "").strip())
        send = st.button(
            "↑",  # Flecha hacia arriba
            key="send_btn",
            disabled=is_thinking or not has_text or bool(st.session_state["graph_error"]),
            help="Enviar mensaje (Ctrl+Enter)",
            use_container_width=True,
        )

# ── Procesar ──────────────────────────────────────────────────────────────────
if send and (user_input or "").strip():
    attached_name = st.session_state.get("attached_file_name")
    attached_text = st.session_state.get("attached_file_text") or ""
    user_text = user_input.strip()

    st.session_state["messages"].append({
        "role":          "user",
        "content":       user_text,
        "intent":        None,
        "topics":        [],
        "elapsed":       0,
        "error":         None,
        "attached_file": attached_name,
    })
    st.session_state["pending_response"] = {
        "user_input": user_text,
        "attached_text": attached_text,
        "message_index": len(st.session_state["messages"]) - 1,
    }

    st.session_state["attached_file_name"] = None
    st.session_state["attached_file_text"] = None
    st.session_state["chat_input_key"] += 1
    st.rerun()

pending = st.session_state.get("pending_response")
if pending and not st.session_state["graph_error"]:
    t0 = time.time()
    try:
        result  = run_graph(pending["user_input"], pending.get("attached_text") or "")
        elapsed = time.time() - t0
        st.session_state["messages"].append({
            "role":    "assistant",
            "content": result.get("final_response") or "_Sin respuesta. Intentá reformular._",
            "intent":  result.get("intent", "desconocido"),
            "topics":  result.get("topics") or [],
            "elapsed": elapsed,
            "error":   result.get("error"),
        })
        idx = pending.get("message_index")
        if isinstance(idx, int) and 0 <= idx < len(st.session_state["messages"]):
            st.session_state["messages"][idx]["intent"] = result.get("intent", "desconocido")
    except Exception as e:
        elapsed = time.time() - t0
        st.session_state["messages"].append({
            "role":    "assistant",
            "content": f"**Error:** `{e}`",
            "intent":  "desconocido",
            "topics":  [],
            "elapsed": elapsed,
            "error":   str(e),
        })
        idx = pending.get("message_index")
        if isinstance(idx, int) and 0 <= idx < len(st.session_state["messages"]):
            st.session_state["messages"][idx]["intent"] = "desconocido"
    finally:
        st.session_state["pending_response"] = None
    st.rerun()