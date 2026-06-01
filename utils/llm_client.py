"""
utils/llm_client.py — Cliente LLM unificado con soporte de tool use

Soporta dos providers configurables desde .env:
    LLM_PROVIDER=ollama  → llama3.x vía /api/chat (soporta tool use nativo)
    LLM_PROVIDER=gemini  → Google Gemini vía SDK (soporta function calling)

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
                    "param2": {"type": "integer", "description": "..."},
                },
                "required": ["param1"],
            },
        },
        ...
    ]

tool_executor: dict[str, Callable] que mapea nombre → función Python a ejecutar
    tool_executor = {
        "nombre_de_la_tool": mi_funcion_python,
    }
"""

import os
import json
from typing import Callable
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Máximo de rondas de tool calling para evitar loops infinitos
MAX_TOOL_ROUNDS = 5


# ══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def call_llm(prompt: str, temperature: float = 0.3) -> str:
    """
    Llamada simple al LLM sin tools. Devuelve el texto generado.

    Args:
        prompt:      Prompt completo a enviar
        temperature: 0.1-0.3 estructurado, 0.5-0.7 creativo

    Returns:
        Respuesta del modelo como string limpio.
    """
    if LLM_PROVIDER == "ollama":
        return _ollama_chat(messages=[{"role": "user", "content": prompt}],
                            temperature=temperature)
    elif LLM_PROVIDER == "gemini":
        return _gemini_chat(prompt=prompt, temperature=temperature)
    else:
        raise ValueError(f"LLM_PROVIDER='{LLM_PROVIDER}' no válido. Usa 'ollama' o 'gemini'.")


def call_llm_with_tools(
    prompt: str,
    tools: list[dict],
    tool_executor: dict[str, Callable],
    temperature: float = 0.3,
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
        temperature:   Temperatura del modelo

    Returns:
        Texto final del modelo tras completar todas las tool calls.
    """
    if LLM_PROVIDER == "ollama":
        return _ollama_tool_loop(prompt, tools, tool_executor, temperature)
    elif LLM_PROVIDER == "gemini":
        return _gemini_tool_loop(prompt, tools, tool_executor, temperature)
    else:
        raise ValueError(f"LLM_PROVIDER='{LLM_PROVIDER}' no válido. Usa 'ollama' o 'gemini'.")


# ══════════════════════════════════════════════════════════════════════════════
# PROVIDER: OLLAMA (llama3.x — /api/chat)
# ══════════════════════════════════════════════════════════════════════════════

def _get_ollama_config() -> tuple[str, str]:
    """Devuelve (url_chat, model) desde variables de entorno."""
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    # Normalizar: aceptar tanto la URL base como la URL con /api/chat o /api/generate
    base_url = base_url.replace("/api/generate", "").replace("/api/chat", "").rstrip("/")
    url   = f"{base_url}/api/chat"
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    return url, model


def _ollama_chat(messages: list[dict], temperature: float,
                 tools: list[dict] = None) -> str:
    """
    Llamada básica a /api/chat de Ollama.
    Devuelve el contenido del mensaje de respuesta como string.
    """
    import requests

    url, model = _get_ollama_config()

    payload = {
        "model":   model,
        "messages": messages,
        "stream":  False,
        "options": {"temperature": temperature},
    }
    if tools:
        # Ollama espera tools en formato OpenAI-compatible
        payload["tools"] = [_to_ollama_tool(t) for t in tools]

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"No se pudo conectar con Ollama en {url}. "
            "Asegúrate de tener Ollama corriendo: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timeout (120s). Intenta con un modelo más pequeño.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Error HTTP de Ollama: {e}")


def _ollama_tool_loop(
    prompt: str,
    tools: list[dict],
    tool_executor: dict[str, Callable],
    temperature: float,
) -> str:
    """
    Loop de tool use para Ollama/llama3.x.

    Ollama devuelve tool calls en:
        response["message"]["tool_calls"] = [
            {"function": {"name": "...", "arguments": {...}}}
        ]

    Fix problema 8: el fallback anterior hacía messages[-1].get("content") cuando
    se agotaban las rondas, pero el último mensaje del historial es siempre un
    mensaje de tipo "tool" (resultado JSON de ejecutar una función), no texto
    legible para el usuario. Ahora se rastrea por separado el último texto real
    del asistente y se usa ese como fallback.

    Fix problema 10: si el modelo devuelve contenido vacío Y sin tool_calls,
    se advierte claramente en lugar de retornar silenciosamente string vacío.
    Esto ocurre con modelos pequeños (ej: llama3.2:3b) que no soportan tool use.
    """
    messages = [{"role": "user", "content": prompt}]

    # Rastrear el último texto real generado por el asistente (no JSON de tool)
    last_assistant_text = ""

    for round_num in range(MAX_TOOL_ROUNDS):
        raw = _ollama_chat(messages, temperature, tools)
        message    = raw.get("message", {})
        tool_calls = message.get("tool_calls", [])
        content    = message.get("content", "").strip()

        # Sin tool calls → el modelo generó respuesta final en texto
        if not tool_calls:
            if content:
                return content

            # Fix problema 10: contenido vacío sin tool calls indica que el modelo
            # no soporta tool use correctamente (común en modelos pequeños como 3b).
            # Se avisa con un mensaje claro en lugar de retornar string vacío.
            if last_assistant_text:
                return last_assistant_text

            _, model = _get_ollama_config()
            raise RuntimeError(
                f"El modelo '{model}' devolvió una respuesta vacía sin tool calls. "
                "Es posible que no soporte tool use. "
                "Probá con llama3.1:8b, mistral o qwen2.5:7b."
            )

        # Guardar el texto del asistente si lo hubo en esta ronda
        if content:
            last_assistant_text = content

        # Añadir respuesta del asistente al historial
        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        })

        # Ejecutar cada tool call y añadir resultados al historial
        for tool_call in tool_calls:
            fn     = tool_call.get("function", {})
            name   = fn.get("name", "")
            args   = fn.get("arguments", {})
            result = _execute_tool(name, args, tool_executor)

            # Ollama espera el resultado como mensaje "tool"
            messages.append({
                "role":    "tool",
                "content": json.dumps(result, ensure_ascii=False),
            })

    # Se agotaron las rondas: usar el último texto real del asistente si existe,
    # en lugar del último mensaje del historial que sería JSON de una tool (Fix #8)
    if last_assistant_text:
        return last_assistant_text

    return "No se pudo completar la respuesta: se agotaron las rondas de tool use."


def _to_ollama_tool(tool: dict) -> dict:
    """
    Convierte el formato unificado de tool al formato OpenAI-compatible
    que espera Ollama.
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
# PROVIDER: GOOGLE GEMINI
# ══════════════════════════════════════════════════════════════════════════════

def _get_gemini_model(tools_schema=None, temperature: float = 0.3):
    """
    Inicializa y devuelve el modelo Gemini configurado.
    Si se pasan tools, las registra en el modelo.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "Paquete 'google-generativeai' no instalado. "
            "Ejecuta: pip install google-generativeai"
        )

    # Fix problema 3: antes se leía GOOGLE_API_KEY que no coincidía con el .env
    # Ahora se lee GEMINI_API_KEY, consistente con el .env-example corregido
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY no definida en .env. "
            "Obtén tu clave en https://aistudio.google.com/app/apikey"
        )

    # Fix problema 4: el default era gemini-1.5-flash pero el .env tenía un modelo
    # inválido. Ahora el default es gemini-2.0-flash, consistente con .env-example.
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    genai.configure(api_key=api_key)

    generation_config = genai.GenerationConfig(temperature=temperature)

    if tools_schema:
        # Gemini recibe las tools como lista de FunctionDeclaration
        gemini_tools = [_to_gemini_tool(t) for t in tools_schema]
        model = genai.GenerativeModel(
            model_name,
            tools=gemini_tools,
            generation_config=generation_config,
        )
    else:
        model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config,
        )

    return model


def _gemini_chat(prompt: str, temperature: float) -> str:
    """Llamada simple a Gemini sin tools."""
    try:
        model    = _get_gemini_model(temperature=temperature)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Error al llamar a Gemini: {e}")


def _gemini_tool_loop(
    prompt: str,
    tools: list[dict],
    tool_executor: dict[str, Callable],
    temperature: float,
) -> str:
    """
    Loop de tool use para Gemini.

    Gemini devuelve function calls en:
        response.candidates[0].content.parts[*].function_call
            .name  → nombre de la tool
            .args  → dict de argumentos
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("Paquete 'google-generativeai' no instalado.")

    model   = _get_gemini_model(tools_schema=tools, temperature=temperature)
    chat    = model.start_chat()
    message = prompt

    for round_num in range(MAX_TOOL_ROUNDS):
        response   = chat.send_message(message)
        parts      = response.candidates[0].content.parts
        tool_calls = [p for p in parts if hasattr(p, "function_call") and p.function_call.name]

        # Sin tool calls → respuesta final en texto
        if not tool_calls:
            return response.text.strip()

        # Ejecutar cada tool call y preparar respuesta de vuelta al modelo
        tool_responses = []
        for part in tool_calls:
            fc     = part.function_call
            name   = fc.name
            args   = dict(fc.args)
            result = _execute_tool(name, args, tool_executor)

            tool_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=name,
                        response={"result": result},
                    )
                )
            )

        # Devolver todos los resultados al modelo en un solo mensaje
        message = genai.protos.Content(parts=tool_responses, role="user")

    return "No se pudo completar la respuesta tras el máximo de rondas."


def _to_gemini_tool(tool: dict):
    """
    Convierte el formato unificado al FunctionDeclaration de Gemini.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("Paquete 'google-generativeai' no instalado.")

    return genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        k: genai.protos.Schema(
                            type=_map_type_gemini(v.get("type", "string")),
                            description=v.get("description", ""),
                        )
                        for k, v in tool["parameters"].get("properties", {}).items()
                    },
                    required=tool["parameters"].get("required", []),
                ),
            )
        ]
    )


def _map_type_gemini(type_str: str):
    """Convierte tipos JSON Schema al enum Type de Gemini."""
    try:
        import google.generativeai as genai
        mapping = {
            "string":  genai.protos.Type.STRING,
            "integer": genai.protos.Type.INTEGER,
            "number":  genai.protos.Type.NUMBER,
            "boolean": genai.protos.Type.BOOLEAN,
            "array":   genai.protos.Type.ARRAY,
            "object":  genai.protos.Type.OBJECT,
        }
        return mapping.get(type_str, genai.protos.Type.STRING)
    except ImportError:
        return "STRING"


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
        # Convertir a string si no lo es (el modelo espera texto)
        return str(result) if not isinstance(result, str) else result
    except Exception as e:
        return f"Error ejecutando '{name}': {e}"