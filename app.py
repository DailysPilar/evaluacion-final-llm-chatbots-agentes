"""
app.py — Interfaz Streamlit del Asistente Académico

Punto de entrada de la aplicación. Gestiona:
  - Carga de documentos (txt, md, pdf)
  - Input del usuario
  - Invocación del grafo LangGraph
  - Visualización de respuestas según el intent
  - Historial de la sesión
"""

import streamlit as st
from state import create_initial_state

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Asistente Académico",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
    }

    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.03);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {
        color: #b0b8d4 !important;
        font-size: 0.85rem;
    }

    /* Título principal */
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #7c83fd, #a78bfa, #60d4f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .main-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        font-weight: 300;
        margin-bottom: 2rem;
    }

    /* Chips de intent */
    .intent-chip {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .chip-planificar { background: rgba(124,131,253,0.18); color: #7c83fd; border: 1px solid rgba(124,131,253,0.35); }
    .chip-explicar   { background: rgba(96,212,247,0.18); color: #60d4f7; border: 1px solid rgba(96,212,247,0.35); }
    .chip-resumir    { background: rgba(52,211,153,0.18); color: #34d399; border: 1px solid rgba(52,211,153,0.35); }
    .chip-desconocido{ background: rgba(156,163,175,0.18); color: #9ca3af; border: 1px solid rgba(156,163,175,0.35); }

    /* Cards de respuesta */
    .response-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }

    /* Historial items */
    .history-item {
        background: rgba(255,255,255,0.03);
        border-left: 3px solid rgba(124,131,253,0.5);
        border-radius: 0 8px 8px 0;
        padding: 0.7rem 1rem;
        margin-bottom: 0.6rem;
        font-size: 0.82rem;
        color: #9ca3af;
        cursor: pointer;
        transition: all 0.2s;
    }
    .history-item:hover {
        background: rgba(124,131,253,0.08);
        border-left-color: #7c83fd;
        color: #e2e8f0;
    }
    .history-intent {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }

    /* Input area */
    .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 0.95rem !important;
        resize: vertical !important;
    }
    .stTextArea textarea:focus {
        border-color: rgba(124,131,253,0.5) !important;
        box-shadow: 0 0 0 2px rgba(124,131,253,0.15) !important;
    }

    /* Botón principal */
    .stButton > button {
        background: linear-gradient(135deg, #7c83fd, #a78bfa) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.8rem !important;
        font-family: 'Sora', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(124,131,253,0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Botón secundario (limpiar) */
    .stButton.secondary > button {
        background: rgba(255,255,255,0.05) !important;
        color: #9ca3af !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* File uploader */
    .stFileUploader {
        background: rgba(255,255,255,0.03) !important;
        border: 1px dashed rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
    }

    /* Topics tags */
    .topic-tag {
        display: inline-block;
        background: rgba(96,212,247,0.1);
        color: #60d4f7;
        border: 1px solid rgba(96,212,247,0.25);
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
        margin: 2px 3px;
    }

    /* Separador */
    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.07);
        margin: 1.5rem 0;
    }

    /* Texto general */
    p, li, td, th {
        color: #cbd5e1;
    }
    h1, h2, h3, h4 {
        color: #e2e8f0;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #7c83fd !important;
    }

    /* Alertas */
    .stAlert {
        background: rgba(239,68,68,0.1) !important;
        border: 1px solid rgba(239,68,68,0.25) !important;
        border-radius: 10px !important;
        color: #fca5a5 !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(124,131,253,0.3); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(124,131,253,0.5); }

    /* Ocultar elementos de Streamlit que no necesitamos */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ── Estado de sesión ──────────────────────────────────────────────────────────

def init_session_state():
    """Inicializa todas las variables de sesión si no existen."""
    defaults = {
        "history":       [],      # Lista de dicts {input, intent, topics, response}
        "last_result":   None,    # Último estado del grafo
        "graph":         None,    # Grafo LangGraph compilado (cacheado)
        "graph_error":   None,    # Error al compilar el grafo
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()


# ── Carga del grafo (con caché) ───────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_graph():
    """
    Compila el grafo LangGraph una sola vez y lo cachea en sesión.
    @st.cache_resource persiste entre reruns del mismo usuario.
    """
    from workflow import build_graph
    return build_graph()

# Intentar cargar el grafo al iniciar
if st.session_state["graph"] is None and st.session_state["graph_error"] is None:
    try:
        st.session_state["graph"] = load_graph()
    except Exception as e:
        st.session_state["graph_error"] = str(e)


# ── Helpers ───────────────────────────────────────────────────────────────────

def read_uploaded_file(uploaded_file) -> str:
    """
    Lee el contenido de un archivo subido por el usuario.
    Soporta .txt, .md y .pdf (si pypdf está instalado).
    """
    if uploaded_file is None:
        return ""

    name = uploaded_file.name.lower()

    if name.endswith((".txt", ".md")):
        return uploaded_file.read().decode("utf-8", errors="replace")

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(uploaded_file.read()))
            pages  = [p.extract_text() or "" for p in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            st.warning("Para leer PDFs instalá pypdf: `pip install pypdf`")
            return ""
        except Exception as e:
            st.warning(f"No se pudo leer el PDF: {e}")
            return ""

    return ""


def intent_chip_html(intent: str) -> str:
    """Genera el HTML del chip de intent coloreado."""
    labels = {
        "planificar": "📅 Planificar",
        "explicar":   "💡 Explicar",
        "resumir":    "📝 Resumir",
        "desconocido":"❓ Sin clasificar",
    }
    label = labels.get(intent, intent)
    return f'<span class="intent-chip chip-{intent}">{label}</span>'


def topics_html(topics: list) -> str:
    """Genera los tags HTML de los topics detectados."""
    if not topics:
        return ""
    tags = "".join(f'<span class="topic-tag">{t}</span>' for t in topics)
    return f'<div style="margin-bottom:1rem;">{tags}</div>'


def run_graph(user_input: str, document_text: str = "") -> dict:
    """
    Ejecuta el grafo LangGraph con el input del usuario.

    Args:
        user_input:    Mensaje del usuario
        document_text: Texto de documento subido (vacío si no hay)

    Returns:
        Estado final del grafo como dict
    """
    graph = st.session_state["graph"]
    if graph is None:
        raise RuntimeError("El grafo no está disponible.")

    initial_state = create_initial_state(
        user_input=user_input,
        document_text=document_text if document_text else None,
    )
    return graph.invoke(initial_state)


# ── Layout: Sidebar ───────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 Asistente Académico")
    st.markdown("---")

    # Estado del sistema
    if st.session_state["graph_error"]:
        st.error(f"⚠️ Error al cargar el grafo:\n\n{st.session_state['graph_error']}")
    else:
        st.success("✅ Sistema listo")

    st.markdown("---")

    # Carga de documento
    st.markdown("### 📄 Documento (opcional)")
    st.caption("Subí un archivo para que el resumidor lo use como base.")
    uploaded_file = st.file_uploader(
        label="Subir archivo",
        type=["txt", "md", "pdf"],
        label_visibility="collapsed",
    )
    document_text = read_uploaded_file(uploaded_file) if uploaded_file else ""
    if document_text:
        st.success(f"✅ {uploaded_file.name} cargado ({len(document_text):,} caracteres)")

    st.markdown("---")

    # Instrucciones rápidas
    st.markdown("### ℹ️ ¿Qué puedo hacer?")
    st.markdown("""
<div style="color:#9ca3af; font-size:0.82rem; line-height:1.7;">
📅 <b style="color:#7c83fd;">Planificar</b><br>
<i>"Quiero estudiar cálculo en 2 semanas"</i><br><br>
💡 <b style="color:#60d4f7;">Explicar</b><br>
<i>"¿Qué es una derivada?"</i><br><br>
📝 <b style="color:#34d399;">Resumir</b><br>
<i>"Resume el tema de estadística"</i>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Historial
    if st.session_state["history"]:
        st.markdown("### 🕘 Historial")
        for i, item in enumerate(reversed(st.session_state["history"][-8:])):
            intent = item.get("intent", "desconocido")
            color_map = {
                "planificar": "#7c83fd",
                "explicar":   "#60d4f7",
                "resumir":    "#34d399",
                "desconocido":"#9ca3af",
            }
            color = color_map.get(intent, "#9ca3af")
            preview = item["input"][:55] + "…" if len(item["input"]) > 55 else item["input"]
            st.markdown(f"""
<div class="history-item">
    <div class="history-intent" style="color:{color};">{intent.upper()}</div>
    {preview}
</div>
""", unsafe_allow_html=True)

        if st.button("🗑️ Limpiar historial", key="clear_history"):
            st.session_state["history"] = []
            st.session_state["last_result"] = None
            st.rerun()


# ── Layout: Main ─────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">Asistente Académico</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Planificá tu estudio, entendé conceptos, generá resúmenes.</div>', unsafe_allow_html=True)

# Área de input
user_input = st.text_area(
    label="Pregunta o solicitud",
    placeholder="Ej: Explicame qué es una integral definida y para qué sirve...",
    height=120,
    label_visibility="collapsed",
    key="user_input_area",
)

col_send, col_clear = st.columns([4, 1])

with col_send:
    send_clicked = st.button("✨ Consultar", key="send_btn", disabled=not user_input.strip())

with col_clear:
    if st.button("↺", key="clear_btn", help="Limpiar resultado"):
        st.session_state["last_result"] = None
        st.rerun()

# ── Ejecución del grafo ───────────────────────────────────────────────────────

if send_clicked and user_input.strip():
    if st.session_state["graph_error"]:
        st.error("El grafo no está disponible. Revisá la configuración.")
    else:
        with st.spinner("Procesando tu consulta…"):
            try:
                result = run_graph(user_input.strip(), document_text)
                st.session_state["last_result"] = result

                # Guardar en historial
                st.session_state["history"].append({
                    "input":    user_input.strip(),
                    "intent":   result.get("intent", "desconocido"),
                    "topics":   result.get("topics") or [],
                    "response": result.get("final_response", ""),
                })

            except Exception as e:
                st.error(f"**Error al procesar la consulta:**\n\n{e}")

# ── Mostrar resultado ─────────────────────────────────────────────────────────

result = st.session_state.get("last_result")

if result:
    intent   = result.get("intent", "desconocido")
    topics   = result.get("topics") or []
    response = result.get("final_response", "")
    error    = result.get("error")
    retries  = result.get("retry_count", 0)

    # Chip de intent + topics
    st.markdown(intent_chip_html(intent), unsafe_allow_html=True)
    if topics:
        st.markdown(topics_html(topics), unsafe_allow_html=True)

    # Advertencia si hubo reintentos
    if retries > 0 and not error:
        st.info(f"ℹ️ Se necesitaron {retries} reintento(s) para generar la respuesta.")

    # Card de respuesta
    st.markdown('<div class="response-card">', unsafe_allow_html=True)
    if response:
        st.markdown(response)
    else:
        st.warning("No se obtuvo una respuesta. Intentá reformular tu consulta.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Detalle de debug (expandible, no visible por defecto)
    with st.expander("🔍 Detalle técnico", expanded=False):
        debug_cols = st.columns(3)
        debug_cols[0].metric("Intent", intent)
        debug_cols[1].metric("Reintentos", retries)
        debug_cols[2].metric("Topics", len(topics))

        if topics:
            st.markdown("**Topics detectados:** " + ", ".join(f"`{t}`" for t in topics))

        if error:
            st.error(f"Último error registrado: {error}")

        # Campos intermedios del estado (útil para debugging del grafo)
        st.markdown("**Estado completo del grafo:**")
        state_preview = {
            "intent":        result.get("intent"),
            "topics":        result.get("topics"),
            "retry_count":   result.get("retry_count"),
            "error":         result.get("error"),
            "has_plan":      bool(result.get("plan")),
            "has_explanation": bool(result.get("explanation")),
            "has_summary":   bool(result.get("summary")),
        }
        st.json(state_preview)

# ── Estado vacío (sin consultas aún) ─────────────────────────────────────────

elif not result:
    st.markdown("""
<div style="
    text-align: center;
    padding: 3rem 2rem;
    color: #4b5563;
">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🎓</div>
    <div style="font-size: 1.1rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;">
        Escribí tu consulta arriba para comenzar
    </div>
    <div style="font-size: 0.85rem; line-height: 1.8;">
        Podés pedirme que te <b style="color:#7c83fd">planifique un estudio</b>,
        te <b style="color:#60d4f7">explique un concepto</b>
        o te <b style="color:#34d399">resuma un tema</b>.
    </div>
</div>
""", unsafe_allow_html=True)