"""
utils/llm_client.py — Cliente LLM unificado con soporte de tool use

El provider se elige automáticamente según las variables de entorno disponibles:
    - Si GEMINI_API_KEY está definida → usa Google Gemini (DEFAULT)
    - Si no                           → usa Ollama como fallback

Gemini usa ChatGoogleGenerativeAI de LangChain, que expone la misma interfaz
que cualquier otro ChatModel de LangChain (.invoke, .bind_tools).
Esto evita usar el SDK de Google directamente y mantiene consistencia
con el ecosistema LangGraph/LangChain.

Dependencias necesarias:
    pip install langchain-google-genai   # para Gemini
    # Ollama usa requests (ya incluido), no necesita instalación extra

Variables de entorno (.env):
    GEMINI_API_KEY=...               # clave de Google AI Studio → activa Gemini
    GEMINI_MODEL=gemini-2.0-flash    # modelo Gemini a usar
    OLLAMA_BASE_URL=http://localhost:11434
    DEFAULT_MODEL=llama3.2:3b        # modelo Ollama (fallback si no hay GEMINI_API_KEY)
    TEMPERATURE=0.7
    MAX_TOKENS=2048

API pública:
    call_llm(prompt, temperature)
        → llamada simple sin tools, devuelve string

    call_llm_with_tools(prompt, tools, tool_executor, temperature)
        → llamada con tool use. El modelo decide si invocar tools,
          el cliente ejecuta el loop completo y devuelve el texto final.

Formato de tools (igual para ambos providers desde el punto de vista del agente):
    tools = [
        {
            "name": "nombre_de_la_tool",
            "description": "Qué hace esta tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "..."},
                },
                "required": ["param1"],
            },
        },
    ]

tool_executor: dict[str, Callable] que mapea nombre → función Python
"""

import os
import json
from typing import Callable
from dotenv import load_dotenv

load_dotenv()

# Provider se detecta automáticamente:
# si GEMINI_API_KEY está seteada → gemini, si no → ollama
LLM_PROVIDER = "gemini" if os.getenv("GEMINI_API_KEY") else "ollama"

# Máximo de rondas de tool calling para evitar loops infinitos
MAX_TOOL_ROUNDS = 3


# ══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def call_llm(prompt: str, temperature: float = None) -> str:
    """
    Llamada simple al LLM sin tools. Devuelve el texto generado.

    Args:
        prompt:      Prompt completo a enviar
        temperature: Temperatura. Si es None, usa TEMPERATURE del .env (default 0.7)

    Returns:
        Respuesta del modelo como string limpio.
    """
    if temperature is None:
        temperature = float(os.getenv("TEMPERATURE", "0.7"))

    if LLM_PROVIDER == "gemini":
        return _gemini_chat(prompt=prompt, temperature=temperature)
    elif LLM_PROVIDER == "ollama":
        return _ollama_chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    else:
        raise ValueError(f"LLM_PROVIDER='{LLM_PROVIDER}' no válido. Usa 'gemini' o 'ollama'.")


def call_llm_with_tools(
    prompt: str,
    tools: list[dict],
    tool_executor: dict[str, Callable],
    temperature: float = None,
    max_rounds: int = None,
) -> str:
    """
    Llamada al LLM con soporte de tool use. Ejecuta el loop completo:
      1. Envía prompt + definición de tools al modelo
      2. Si el modelo decide llamar una tool → ejecutarla en Python
      3. Devolver el resultado al modelo como contexto
      4. Repetir hasta que el modelo genere texto final (sin tool calls)

    Args:
        prompt:        Prompt del agente
        tools:         Lista de tool definitions (formato unificado, ver módulo)
        tool_executor: Dict {nombre_tool: función_python}
        temperature:   Temperatura. Si es None, usa TEMPERATURE del .env
        max_rounds:    Máximo de rondas de tool use. Si es None usa MAX_TOOL_ROUNDS (3)

    Returns:
        Texto final del modelo tras completar todas las tool calls.
    """
    if temperature is None:
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
    if max_rounds is None:
        max_rounds = MAX_TOOL_ROUNDS

    if LLM_PROVIDER == "gemini":
        return _gemini_tool_loop(prompt, tools, tool_executor, temperature, max_rounds)
    elif LLM_PROVIDER == "ollama":
        return _ollama_tool_loop(prompt, tools, tool_executor, temperature, max_rounds)
    else:
        raise ValueError(f"LLM_PROVIDER='{LLM_PROVIDER}' no válido. Usa 'gemini' o 'ollama'.")


# ══════════════════════════════════════════════════════════════════════════════
# PROVIDER: GOOGLE GEMINI (via langchain-google-genai)
# ══════════════════════════════════════════════════════════════════════════════

def _get_gemini_llm(temperature: float, tools_schema: list[dict] = None):
    """
    Crea y devuelve un ChatGoogleGenerativeAI de LangChain.

    Si se pasan tools, las convierte al formato LangChain y hace bind_tools()
    para que el modelo pueda invocarlas.

    Requiere: pip install langchain-google-genai

    Args:
        temperature:  Temperatura de generación
        tools_schema: Lista de tool definitions en formato unificado (opcional)

    Returns:
        ChatGoogleGenerativeAI, con o sin tools según corresponda.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise RuntimeError(
            "Paquete 'langchain-google-genai' no instalado. "
            "Ejecutá: pip install langchain-google-genai"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY no definida en .env. "
            "Obtené tu clave en https://aistudio.google.com/app/apikey"
        )

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    max_tokens = int(os.getenv("MAX_TOKENS", "2048"))

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_tokens,
        # Deshabilitar Automatic Function Calling del SDK de Google.
        # Si está activo, el SDK ejecuta las tools internamente en un loop propio
        # que entra en conflicto con nuestro loop manual en _gemini_tool_loop,
        # causando llamadas duplicadas y bloqueos. Nosotros manejamos el loop.
        max_retries=2,
    )

    if tools_schema:
        # Convierte el formato unificado al formato LangChain y hace bind
        lc_tools = [_to_langchain_tool(t) for t in tools_schema]
        return llm.bind_tools(lc_tools)

    return llm



def _extract_text(content) -> str:
    """
    Normaliza el campo .content de un AIMessage de LangChain a string limpio.

    ChatGoogleGenerativeAI puede devolver .content como:
      - str:  "Hola mundo"                         → caso normal
      - list: [{"type": "text", "text": "Hola"}]   → contenido estructurado

    En ambos casos devuelve el texto plano como string.
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts).strip()
    return str(content).strip()


def _gemini_chat(prompt: str, temperature: float) -> str:
    """
    Llamada simple a Gemini sin tools usando LangChain.

    Usa HumanMessage para enviar el prompt y extrae el texto de la respuesta.
    """
    from langchain_core.messages import HumanMessage

    llm = _get_gemini_llm(temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    return _extract_text(response.content)


def _gemini_tool_loop(
    prompt: str,
    tools: list[dict],
    tool_executor: dict[str, Callable],
    temperature: float,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> str:
    """
    Loop de tool use para Gemini usando LangChain.

    Flujo del loop:
      1. Se envía el prompt como HumanMessage al modelo con tools bindeadas
      2. Si la respuesta contiene tool_calls → ejecutar cada tool en Python
      3. Añadir los resultados como ToolMessages al historial
      4. Reinvocar el modelo con el historial completo
      5. Repetir hasta que no haya más tool_calls o se agoten las rondas

    LangChain maneja la serialización/deserialización de tool calls:
      - AIMessage.tool_calls: lista de {"id": ..., "name": ..., "args": {...}}
      - ToolMessage: resultado de ejecutar una tool, identificado por tool_call_id

    Args:
        prompt:        Prompt inicial del agente
        tools:         Definiciones de tools en formato unificado
        tool_executor: Mapa {nombre_tool: función_python}
        temperature:   Temperatura del modelo

    Returns:
        Texto final generado por el modelo.
    """
    from langchain_core.messages import HumanMessage, ToolMessage
    from utils.logger import log_event

    llm_with_tools = _get_gemini_llm(temperature=temperature, tools_schema=tools)

    # Historial de mensajes que se va construyendo con cada ronda
    messages = [HumanMessage(content=prompt)]

    for round_num in range(max_rounds):
        log_event("llm_client", f"Tool loop ronda {round_num + 1}/{max_rounds} — invocando modelo...")
        response = llm_with_tools.invoke(messages)
        log_event("llm_client", f"Respuesta recibida — tool_calls: {len(response.tool_calls)}, tiene texto: {bool(_extract_text(response.content))}")

        # Sin tool_calls → el modelo generó respuesta final en texto
        if not response.tool_calls:
            return _extract_text(response.content)

        # Añadir la respuesta del asistente (con tool_calls) al historial
        messages.append(response)

        # Ejecutar cada tool call y añadir el resultado como ToolMessage
        for tool_call in response.tool_calls:
            tool_name    = tool_call["name"]
            tool_args    = tool_call["args"]
            tool_call_id = tool_call["id"]

            log_event("llm_client", f"Ejecutando tool: {tool_name}({list(tool_args.keys())})")
            result = _execute_tool(tool_name, tool_args, tool_executor)
            log_event("llm_client", f"Tool {tool_name} completada — resultado: {len(str(result))} chars")

            # ToolMessage vincula el resultado con el tool_call_id
            # para que el modelo sepa qué tool call respondió
            messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_call_id,
                )
            )

    # Se agotaron las rondas: buscar el último texto del asistente en el historial
    for msg in reversed(messages):
        # AIMessage con contenido de texto (no solo tool_calls)
        if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
            return _extract_text(msg.content)

    return "No se pudo completar la respuesta: se agotaron las rondas de tool use."


def _to_langchain_tool(tool: dict) -> dict:
    """
    Convierte el formato unificado de tool al formato que acepta
    ChatGoogleGenerativeAI.bind_tools() de LangChain.

    LangChain bind_tools() acepta dicts con la estructura OpenAI function-calling:
        {
            "type": "function",
            "function": {
                "name": ...,
                "description": ...,
                "parameters": {JSON Schema}
            }
        }

    Este formato es compatible con ChatGoogleGenerativeAI, ChatOpenAI y
    ChatOllama, por lo que no se necesita conversión específica por provider.
    """
    return {
        "type": "function",
        "function": {
            "name":        tool["name"],
            "description": tool["description"],
            "parameters":  tool["parameters"],
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# PROVIDER: OLLAMA (llama3.x — /api/chat via requests)
# ══════════════════════════════════════════════════════════════════════════════

def _get_ollama_config() -> tuple[str, str]:
    """Devuelve (url_chat, model) desde variables de entorno."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    base_url = base_url.rstrip("/")
    url   = f"{base_url}/api/chat"
    model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    return url, model


def _ollama_chat(messages: list[dict], temperature: float,
                 tools: list[dict] = None):
    """
    Llamada básica a /api/chat de Ollama.
    Devuelve el JSON completo de la respuesta.
    """
    import requests

    url, model = _get_ollama_config()
    max_tokens = int(os.getenv("MAX_TOKENS", "2048"))

    payload = {
        "model":    model,
        "messages": messages,
        "stream":   False,
        "options":  {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if tools:
        payload["tools"] = [_to_langchain_tool(t) for t in tools]

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"No se pudo conectar con Ollama en {url}. "
            "Asegurate de tener Ollama corriendo: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timeout (120s). Intentá con un modelo más pequeño.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Error HTTP de Ollama: {e}")


def _ollama_tool_loop(
    prompt: str,
    tools: list[dict],
    tool_executor: dict[str, Callable],
    temperature: float,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> str:
    """
    Loop de tool use para Ollama/llama3.x.

    Ollama devuelve tool calls en:
        response["message"]["tool_calls"] = [
            {"function": {"name": "...", "arguments": {...}}}
        ]

    Notas:
    - Modelos pequeños como llama3.2:3b pueden no soportar tool use correctamente
      y devolver contenido vacío sin tool_calls. Se advierte con error claro.
    - Se rastrea el último texto real del asistente como fallback si se
      agotan las rondas (el último mensaje del historial suele ser un ToolMessage JSON).
    """
    messages = [{"role": "user", "content": prompt}]
    last_assistant_text = ""  # fallback si se agotan las rondas

    for round_num in range(max_rounds):
        raw        = _ollama_chat(messages, temperature, tools)
        message    = raw.get("message", {})
        tool_calls = message.get("tool_calls", [])
        content    = message.get("content", "").strip()

        # Sin tool calls → respuesta final en texto
        if not tool_calls:
            if content:
                return content

            # Contenido vacío sin tool_calls: modelo no soporta tool use
            if last_assistant_text:
                return last_assistant_text

            _, model = _get_ollama_config()
            raise RuntimeError(
                f"El modelo '{model}' devolvió una respuesta vacía sin tool calls. "
                "Es posible que no soporte tool use. "
                "Probá con llama3.1:8b, mistral o qwen2.5:7b."
            )

        if content:
            last_assistant_text = content

        # Añadir respuesta del asistente al historial
        messages.append({
            "role":       "assistant",
            "content":    content,
            "tool_calls": tool_calls,
        })

        # Ejecutar cada tool y añadir resultados como mensajes "tool"
        for tool_call in tool_calls:
            fn     = tool_call.get("function", {})
            name   = fn.get("name", "")
            args   = fn.get("arguments", {})
            result = _execute_tool(name, args, tool_executor)

            messages.append({
                "role":    "tool",
                "content": json.dumps(result, ensure_ascii=False),
            })

    # Rondas agotadas: usar el último texto real del asistente
    if last_assistant_text:
        return last_assistant_text

    return "No se pudo completar la respuesta: se agotaron las rondas de tool use."


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS COMUNES
# ══════════════════════════════════════════════════════════════════════════════

def _execute_tool(name: str, args: dict, tool_executor: dict[str, Callable]) -> str:
    """
    Ejecuta la función Python correspondiente a una tool call.

    Args:
        name:          Nombre de la tool que pidió el modelo
        args:          Argumentos como dict
        tool_executor: Mapa {nombre: función}

    Returns:
        Resultado de la tool como string (para devolverlo al modelo).
    """
    fn = tool_executor.get(name)
    if fn is None:
        return f"Error: tool '{name}' no encontrada en tool_executor."
    try:
        result = fn(**args)
        return str(result) if not isinstance(result, str) else result
    except Exception as e:
        return f"Error ejecutando '{name}': {e}"