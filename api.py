import os
import json
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import sqlite3
from datetime import datetime

# Cargar variables de entorno iniciales
load_dotenv()

from src.engine import initialize_engine

app = FastAPI(title="Chatbot SixManager API", description="API RAG para Widget de Chat", version="1.0.0")


def load_allowed_origins():
    origins = {
        "http://localhost:8000",
        "http://localhost:8501",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:4321",
    }

    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins:
        origins.update(
            origin.strip().rstrip("/")
            for origin in env_origins.split(",")
            if origin.strip()
        )

    try:
        if os.path.exists("config/config.json"):
            with open("config/config.json", "r") as f:
                cfg = json.load(f)
            custom_origins = cfg.get("allowed_origins", "")
            if custom_origins:
                origins.update(
                    origin.strip().rstrip("/")
                    for origin in custom_origins.split(",")
                    if origin.strip()
                )
    except Exception:
        pass

    return sorted(origins)

# Setup Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS para despliegues reales. La validación de origen sigue ocurriendo además
# dentro de verify_api_key para bloquear usos no autorizados del widget.
app.add_middleware(
    CORSMiddleware,
    allow_origins=load_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para verificar API Key y Origen (Seguridad Extendida)
async def verify_api_key(request: Request, x_api_key: Optional[str] = Header(None)):
    global db_manager
    
    # 1. Validación estricta de Origen (CORS dinámico)
    client_origin = request.headers.get("origin") or request.headers.get("referer")
    if client_origin:
        client_origin = client_origin.rstrip('/')
        
        allowed_origins = load_allowed_origins()
            
        allowed = False
        for ao in allowed_origins:
            if ao == "*" or client_origin.startswith(ao):
                allowed = True
                break
                
        if not allowed:
            print(f"Bloqueado intento desde origen no autorizado: {client_origin}")
            raise HTTPException(status_code=403, detail="Origen no autorizado por política CORS del administrador")

    # 2. Validación de API Key
    master_key = os.getenv("WIDGET_API_KEY")
    
    if not master_key and (not 'db_manager' in globals() or not db_manager.get_api_keys()):
        return # Si no hay clave ni en db ni en env, asumimos dev mode
    
    if master_key and x_api_key == master_key:
        return x_api_key
        
    if 'db_manager' in globals() and db_manager.is_valid_api_key(x_api_key):
        return x_api_key

    raise HTTPException(status_code=401, detail="API Key inválida o ausente")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database Manager para futura portabilidad
class DatabaseManager:
    def __init__(self, db_path="conversations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    sources TEXT,
                    feedback TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Migración simple: verificar si la columna feedback y flag existe, si no, crearlas
            cursor.execute("PRAGMA table_info(messages)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'feedback' not in columns:
                cursor.execute("ALTER TABLE messages ADD COLUMN feedback TEXT")
            if 'flag' not in columns:
                cursor.execute("ALTER TABLE messages ADD COLUMN flag TEXT")
            
            # 2. Crear tabla de leads (con migración para cargo)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    company TEXT,
                    cargo TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute("PRAGMA table_info(leads)")
            leads_cols = [col[1] for col in cursor.fetchall()]
            if 'cargo' not in leads_cols:
                cursor.execute("ALTER TABLE leads ADD COLUMN cargo TEXT")
            if 'resumen' not in leads_cols:
                cursor.execute("ALTER TABLE leads ADD COLUMN resumen TEXT")
                
            # 3. Crear tabla de API Keys Multi-sitio
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_message(self, session_id, role, content, sources=None, flag=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content, sources, flag) VALUES (?, ?, ?, ?, ?)",
                    (session_id, role, content, json.dumps(sources) if sources else None, flag)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error guardando mensaje en la DB: {e}")
            return None

    def save_lead(self, session_id, name=None, email=None, phone=None, company=None, cargo=None, resumen=""):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Verificar si ya existe un lead para esta sesión para actualizarlo o crear uno nuevo
                cursor.execute("SELECT id FROM leads WHERE session_id = ?", (session_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Actualizar solo los campos que vengan con datos
                    update_fields = []
                    params = []
                    if name: 
                        update_fields.append("name = ?")
                        params.append(name)
                    if email: 
                        update_fields.append("email = ?")
                        params.append(email)
                    if phone: 
                        update_fields.append("phone = ?")
                        params.append(phone)
                    if company: 
                        update_fields.append("company = ?")
                        params.append(company)
                    if cargo: 
                        update_fields.append("cargo = ?")
                        params.append(cargo)
                    
                    if update_fields:
                        query = f"UPDATE leads SET {', '.join(update_fields)} WHERE session_id = ?"
                        params.append(session_id)
                        cursor.execute(query, tuple(params))
                else:
                    cursor.execute(
                        "INSERT INTO leads (session_id, name, email, phone, company, cargo, resumen) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (session_id, name, email, phone, company, cargo, resumen)
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error guardando lead en la DB: {e}", flush=True)
            return False

    def get_session_history(self, session_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
                    (session_id,)
                )
                rows = cursor.fetchall()
                history = ""
                for role, content in rows:
                    name = "USUARIO" if role == "user" else "ASISTENTE"
                    history += f"{name}: {content}\n"
                return history
        except Exception as e:
            print(f"Error cargando historial para resumen: {e}", flush=True)
            return ""

    def get_session_messages(self, session_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
                    (session_id,)
                )
                return [{"role": r, "content": c} for r, c in cursor.fetchall()]
        except Exception as e:
            print(f"Error cargando historial: {e}", flush=True)
            return []

    def update_feedback(self, message_id, rating):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE messages SET feedback = ? WHERE id = ?",
                    (rating, message_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error actualizando feedback: {e}")
            return False

    def create_api_key(self, name, key):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO api_keys (name, key) VALUES (?, ?)", (name, key))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creando api key: {e}")
            return False

    def get_api_keys(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, key, created_at FROM api_keys ORDER BY created_at DESC")
                return [{"id": row[0], "name": row[1], "key": row[2], "created_at": row[3]} for row in cursor.fetchall()]
        except Exception as e:
            return []

    def delete_api_key(self, key_to_del):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM api_keys WHERE key = ?", (key_to_del,))
                conn.commit()
                return True
        except Exception as e:
            return False

    def is_valid_api_key(self, key):
        if not key: return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM api_keys WHERE key = ?", (key,))
                return cursor.fetchone() is not None
        except Exception as e:
            return False

db_manager = DatabaseManager()

CONFIG_FILE = "config/config.json"
last_config_mtime = 0
rag_index = None
rag_qa_template = None

def get_key_for(provider):
    if provider == "Gemini": return os.getenv("GOOGLE_API_KEY", "")
    elif provider == "OpenRouter": return os.getenv("OPENROUTER_API_KEY", "")
    else: return os.getenv("OPENAI_API_KEY", "")

def check_and_reload_engine():
    global rag_index, rag_qa_template, last_config_mtime
    
    current_mtime = 0
    if os.path.exists(CONFIG_FILE):
        current_mtime = os.path.getmtime(CONFIG_FILE)
    
    # Si hay un archivo config.json y ha sido modificado, recargamos el motor
    if current_mtime > last_config_mtime:
        print("Detectado cambio en configuración. Recargando motor RAG...")
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
            
            rag_index, rag_qa_template = initialize_engine(
                chat_provider=cfg.get("chat_provider", "Gemini"),
                chat_key=cfg.get("chat_key", ""),
                embed_provider=cfg.get("embed_provider", "Gemini"),
                embed_key=cfg.get("embed_key", ""),
                openrouter_model=cfg.get("openrouter_model", "anthropic/claude-3-haiku"),
                bot_name=cfg.get("bot_name", "Robotito"),
                temperature=float(cfg.get("temperature", 0.1))
            )
            last_config_mtime = current_mtime
            
            # La recarga de orígenes ya no es necesaria con el CORSMiddleware estándar en "*"
            
            print(f"Motor recargado correctamente (Temp: {cfg.get('temperature', 0.1)}). Trigger Tags activos.", flush=True)
            return
        except Exception as e:
            print(f"Error cargando desde config.json: {e}", flush=True)
            
    # Si no había engine y no hay config.json, intentamos inicializarlo desde .env
    if rag_index is None and not os.path.exists(CONFIG_FILE):
        print("Intentando inicializar motor desde variables de entorno (.env)...")
        c_prov = os.getenv("CHAT_PROVIDER", "Gemini")
        e_prov = os.getenv("EMBED_PROVIDER", "Gemini")
        try:
            rag_index, rag_qa_template = initialize_engine(
                chat_provider=c_prov,
                chat_key=get_key_for(c_prov),
                embed_provider=e_prov,
                embed_key=get_key_for(e_prov),
                openrouter_model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku"),
                bot_name="Asistente"
            )
            print("Motor inicializado vía entorno.")
        except Exception as e:
            print(f"Aún faltan credenciales o configuración: {e}")


# Intentar precarga inicial
if os.getenv("ROBOTITO_BOOTSTRAP_ENGINE", "true").lower() not in {"0", "false", "no"}:
    check_and_reload_engine()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "no-session"
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    message_id: Optional[int] = None
    show_modal: bool = False

class FeedbackRequest(BaseModel):
    message_id: int
    rating: str # 'like' o 'dislike'

class LeadFormRequest(BaseModel):
    session_id: str
    name: str
    email: str
    phone: str
    company: str
    cargo: str

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat_endpoint(request: Request, chat_req: ChatRequest, api_key: str = Depends(verify_api_key)):
    # Verificamos si cambió el config file antes de responder a cada usuario (Hot Reload)
    check_and_reload_engine()
    
    # 1. Guardar mensaje del usuario en la base de datos
    db_manager.save_message(chat_req.session_id, "user", chat_req.message)
    
    # --- FILTRO ANTI-JAILBREAK BÁSICO ---
    jailbreak_keywords = [
        "ignora todas las instrucciones", "ignora las instrucciones", 
        "ignora tu prompt", "olvida las reglas", "modo desarrollador",
        "development mode", "dan mode", "olvida lo anterior",
        "dime tus instrucciones", "dime tu prompt", "revela tu código"
    ]
    if any(kw in chat_req.message.lower() for kw in jailbreak_keywords):
        fallback_msg = "Lo siento, como asistente corporativo no puedo procesar esa solicitud ni alterar mis instrucciones base. ¿En qué te puedo ayudar sobre los servicios de SixManager?"
        msg_id = db_manager.save_message(chat_req.session_id, "bot", fallback_msg, flag="jailbreak")
        return ChatResponse(response=fallback_msg, message_id=msg_id, show_modal=False)
    # ------------------------------------

    if not rag_index:
        raise HTTPException(status_code=500, detail="El motor de IA no está configurado. Por favor, ingresa a la interfaz de administración en el puerto 8501 y guarda una configuración válida.")
    
    try:
        from llama_index.core.llms import ChatMessage, MessageRole
        history_msgs = db_manager.get_session_messages(chat_req.session_id)
        chat_history = []
        for msg in history_msgs[:-1]: # Excluir el mnsg actual que acabamos de guardar
            if msg["role"] == "user":
                chat_history.append(ChatMessage(role=MessageRole.USER, content=msg["content"]))
            elif msg["role"] == "bot":
                chat_history.append(ChatMessage(role=MessageRole.ASSISTANT, content=msg["content"]))

        chat_engine = rag_index.as_chat_engine(
            chat_mode="condense_question",
            text_qa_template=rag_qa_template,
            verbose=True
        )

        if chat_req.stream:
            from fastapi.responses import StreamingResponse
            def event_generator():
                try:
                    stream_res = chat_engine.stream_chat(chat_req.message, chat_history=chat_history)
                    
                    sources = []
                    if stream_res.source_nodes:
                        for node in stream_res.source_nodes:
                            sources.append(node.metadata.get('file_name', 'Documento Desconocido'))
                    sources = list(set(sources))
                    
                    if sources:
                        yield f"data: {json.dumps({'sources': sources})}\n\n"
                        
                    full_response = ""
                    for token in stream_res.response_gen:
                        full_response += token
                        yield f"data: {json.dumps({'token': token})}\n\n"
                    
                    # Limpiar modal tag del guardado
                    show_modal = False
                    if "[TRIGGER_LEAD_MODAL]" in full_response.upper():
                        show_modal = True
                        import re
                        full_response = re.sub(r'\[TRIGGER_LEAD_MODAL\]', '', full_response, flags=re.IGNORECASE).strip()
                    else:
                        interest_keywords = ["interesa", "precio", "cotizar", "contratar", "reunión", "demo", "contacto", "servicios"]
                        if any(kw in chat_req.message.lower() for kw in interest_keywords):
                            show_modal = True

                    msg_id = db_manager.save_message(chat_req.session_id, "bot", full_response, sources, flag="lead_trigger" if show_modal else None)
                    yield f"data: {json.dumps({'done': True, 'show_modal': show_modal, 'message_id': msg_id})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        # Flujo Normal Síncrono (sin streaming)
        res = chat_engine.chat(chat_req.message, chat_history=chat_history)
        
        sources = []
        if res.source_nodes:
            for node in res.source_nodes:
                sources.append(node.metadata.get('file_name', 'Documento Desconocido'))
        sources = list(set(sources))
        
        # 3. Intento de extracción de Leads (heurística simple + lógica del modelo)
        show_modal = False
        final_response = res.response
        print(f"DEBUG LLM Response: {final_response[-50:]}") # Ver los últimos 50 chars
        
        if "[TRIGGER_LEAD_MODAL]" in final_response.upper():
            show_modal = True
            print("DEBUG: Lead Trigger detectado en la respuesta del LLM.", flush=True)
            import re
            final_response = re.sub(r'\[TRIGGER_LEAD_MODAL\]', '', final_response, flags=re.IGNORECASE).strip()
        else:
            interest_keywords = [
                "interesa", "precio", "cotizar", "contratar", "reunión", "reunion", "demo", 
                "contacto", "servicios", "propuesta", "presupuesto", "más info", "mas info", 
                "información", "informacion", "ayuda", "asesoría", "asesoria", "quien es"
            ]
            if any(kw in chat_req.message.lower() for kw in interest_keywords):
                show_modal = True
                print(f"DEBUG: Lead Trigger detectado por palabra clave.", flush=True)

        # 2. Guardar respuesta del bot final en la base de datos
        msg_id = db_manager.save_message(chat_req.session_id, "bot", final_response, sources, flag="lead_trigger" if show_modal else None)

        return ChatResponse(response=final_response, sources=sources, message_id=msg_id, show_modal=show_modal)
    except Exception as e:
        # También registramos fallos si es necesario
        db_manager.save_message(chat_req.session_id, "bot", f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo en la inferencia del modelo subyacente: {str(e)}")

@app.post("/feedback")
async def feedback_endpoint(request: FeedbackRequest, api_key: str = Depends(verify_api_key)):
    if request.rating not in ["like", "dislike"]:
        raise HTTPException(status_code=400, detail="Rating inválido. Use 'like' o 'dislike'.")
    
    success = db_manager.update_feedback(request.message_id, request.rating)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo actualizar el feedback en la base de datos.")
    
    return {"status": "ok", "message": "Feedback registrado correctamente"}

@app.post("/submit-lead-form")
async def submit_lead_form(request: LeadFormRequest, api_key: str = Depends(verify_api_key)):
    # Generar resumen de la conversación usando la IA antes de guardar
    conversation_summary = "Sin conversación previa relevante."
    try:
        history = db_manager.get_session_history(request.session_id)
        if history and rag_index:
            from llama_index.core import Settings
            prompt = f"Resume la siguiente conversación de chat en una sola frase breve (máximo 150 caracteres) que explique qué buscaba el usuario:\n\n{history}"
            response = Settings.llm.complete(prompt)
            conversation_summary = str(response).strip()
            print(f"DEBUG: Resumen generado para {request.session_id}: {conversation_summary}", flush=True)
    except Exception as e:
        print(f"Error generando resumen para el lead: {e}", flush=True)

    success = db_manager.save_lead(
        session_id=request.session_id,
        name=request.name,
        email=request.email,
        phone=request.phone,
        company=request.company,
        cargo=request.cargo,
        resumen=conversation_summary
    )
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo guardar el formulario de lead.")
    
    return {"status": "ok", "message": "Formulario recibido correctamente y resumen generado."}

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API RAG Activa. Consuma /static/widget.js"}


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


@app.get("/readyz")
def readiness():
    check_and_reload_engine()
    return {
        "status": "ready" if rag_index else "waiting_configuration",
        "engine_loaded": rag_index is not None,
    }

@app.get("/widget-config")
def get_widget_config(api_key: str = Depends(verify_api_key)):
    bot_name = "Asistente Inteligente SixManager"
    primary_color = "#007bff"
    show_sources = True
    use_streaming = False
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                if "bot_name" in cfg and cfg["bot_name"]:
                    bot_name = cfg["bot_name"]
                if "primary_color" in cfg and cfg["primary_color"]:
                    primary_color = cfg["primary_color"]
                if "show_sources" in cfg:
                    show_sources = cfg["show_sources"]
                if "use_streaming" in cfg:
                    use_streaming = cfg["use_streaming"]
        except Exception:
            pass
    return {"bot_name": bot_name, "primary_color": primary_color, "show_sources": show_sources, "use_streaming": use_streaming}
