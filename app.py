import streamlit as st
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno desde .env por defecto
load_dotenv()

from src.engine import initialize_engine

st.set_page_config(page_title="Gestor de IA - SixManager", page_icon="⚙️", layout="wide")

# --- AUTENTICACIÓN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

def login():
    st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>🔒 Ingreso a SixManager</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            pwd = st.text_input("Contraseña de Administrador", type="password")
            submitted = st.form_submit_button("Acceder", use_container_width=True)
            if submitted:
                if pwd == admin_password:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")

if not st.session_state.logged_in:
    login()
    st.stop()
# ---------------------

CONFIG_FILE = "config/config.json"

def save_config(chat_provider, chat_key, embed_provider, embed_key, openrouter_model, bot_name, primary_color, show_sources=True, allowed_origins="", temperature=0.1, use_streaming=False):
    os.makedirs("config", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "chat_provider": chat_provider,
            "chat_key": chat_key,
            "embed_provider": embed_provider,
            "embed_key": embed_key,
            "openrouter_model": openrouter_model,
            "bot_name": bot_name,
            "primary_color": primary_color,
            "show_sources": show_sources,
            "allowed_origins": allowed_origins,
            "temperature": temperature,
            "use_streaming": use_streaming
        }, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# Leer config existente persistente para defaults
saved_config = load_config()

# Inicializar cache de Streamlit Local
@st.cache_resource(show_spinner=False)
def get_engine(chat_p, chat_k, embed_p, embed_k, or_model, b_name, temp=0.1):
    return initialize_engine(chat_p, chat_k, embed_p, embed_k, or_model, b_name, temperature=temp)

st.title("🤖 Administrador de IA - SixManager")
st.markdown("Panel de control unificado para gestionar tu Asistente Inteligente y su despliegue web.")

tab_chat, tab_config, tab_widget, tab_leads, tab_analytics = st.tabs(["💬 Chat de Prueba", "⚙️ Configuración de LLM", "🌐 Integración Web", "🤝 Gestión de Leads", "📈 Analíticas"])

# --- TAB 2: CONFIGURACIÓN LLM ---
with tab_config:
    st.header("⚙️ Configuración de LLM")
    st.markdown("Aquí puedes definir los modelos de Inteligencia Artificial y Embeddings (vectores) que darán vida a tu asistente.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Modelo Principal (Chat)")
        current_chat_provider = saved_config.get("chat_provider", os.getenv("CHAT_PROVIDER", "Gemini"))
        provider_idx = ["Gemini", "OpenAI", "OpenRouter"].index(current_chat_provider) if current_chat_provider in ["Gemini", "OpenAI", "OpenRouter"] else 0
        chat_provider = st.selectbox("Proveedor de Chat", ["Gemini", "OpenAI", "OpenRouter"], index=provider_idx)
        
        openrouter_model = "anthropic/claude-3-haiku"
        if chat_provider == "OpenRouter":
            default_or_model = saved_config.get("openrouter_model", os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku"))
            openrouter_model = st.text_input("Modelo de OpenRouter", value=default_or_model)
            chat_key_env = saved_config.get("chat_key") or os.environ.get("OPENROUTER_API_KEY", "")
            chat_key = st.text_input("OpenRouter API Key", type="password", value=chat_key_env)
        elif chat_provider == "Gemini":
            chat_key_env = saved_config.get("chat_key") or os.environ.get("GOOGLE_API_KEY", "")
            chat_key = st.text_input("Google API Key", type="password", value=chat_key_env)
        else:
            chat_key_env = saved_config.get("chat_key") or os.environ.get("OPENAI_API_KEY", "")
            chat_key = st.text_input("OpenAI API Key", type="password", value=chat_key_env)

    with col2:
        st.subheader("Modelo de Embeddings (Lectura PDF)")
        current_embed_provider = saved_config.get("embed_provider", os.getenv("EMBED_PROVIDER", "Gemini"))
        embed_idx = ["Gemini", "OpenAI"].index(current_embed_provider) if current_embed_provider in ["Gemini", "OpenAI"] else 0
        embed_provider = st.selectbox("Proveedor de Embeddings", ["Gemini", "OpenAI"], index=embed_idx, help="OpenRouter no provee embeddings directamente. Selecciona OpenAI o Gemini para vectorizar los PDFs.")
        
        if embed_provider == "Gemini":
            embed_key_env = saved_config.get("embed_key") or os.environ.get("GOOGLE_API_KEY", "")
            embed_key = st.text_input("API Key (Google Embeddings)", type="password", value=embed_key_env)
        else:
            embed_key_env = saved_config.get("embed_key") or os.environ.get("OPENAI_API_KEY", "")
            embed_key = st.text_input("API Key (OpenAI Embeddings)", type="password", value=embed_key_env)

    st.divider()
    st.subheader("🌋 Creatividad y Variedad")
    temperature_default = saved_config.get("temperature", 0.1)
    temperature = st.slider("Temperatura", min_value=0.0, max_value=1.0, value=float(temperature_default), step=0.05, help="0.0 es más preciso/determinista, 1.0 es más creativo/variado (recomendado: 0.7 para mayor variedad).")

# --- TAB 3: INTEGRACIÓN Y PERSONALIZACIÓN WEB ---
with tab_widget:
    st.header("🎨 Apariencia del Widget")
    st.markdown("Personaliza el aspecto de tu bot antes de copiar el código de instalación.")
    
    col_name, col_color = st.columns(2)
    with col_name:
        bot_name_default = saved_config.get("bot_name", "Robotito")
        bot_name = st.text_input("Nombre del Bot (Personalidad)", value=bot_name_default, help="Este nombre aparecerá en la ventana de chat del Widget y se usará en el Prompt del sistema.")
    with col_color:
        primary_color_default = saved_config.get("primary_color", "#007bff")
        primary_color = st.color_picker("Color Principal de tu Marca", value=primary_color_default, help="Selecciona el color corporativo para alinear el Widget de chat al estilo de tu sitio web.")
    
    show_sources_default = saved_config.get("show_sources", True)
    show_sources = st.toggle("Mostrar fuentes documentales en el Widget", value=show_sources_default, help="Si está activado, el Widget mostrará al usuario final el nombre del PDF de donde extrajo la respuesta.")
    
    use_streaming_default = saved_config.get("use_streaming", False)
    use_streaming = st.toggle("Habilitar modo Escritura en Vivo (Streaming)", value=use_streaming_default, help="Si se activa, el bot responderá progresivamente. Es mucho más rápido, pero desactiva los popups emergentes automáticos (modal de leads).")
    
    st.divider()
    st.subheader("🔒 Seguridad de la API")
    allowed_origins_default = saved_config.get("allowed_origins", os.getenv("ALLOWED_ORIGINS", "http://localhost:8000"))
    allowed_origins = st.text_area("Orígenes Permitidos (CORS)", value=allowed_origins_default, help="Dominios autorizados para usar el widget, separados por comas. Ej: http://localhost:5500, https://tu-sitio.com")
    
    st.divider()
    
    st.header("🔑 Gestión de Llaves de Acceso (API Keys)")
    st.markdown("Genera múltiples llaves para distintos clientes o dominios y adminístralas aquí.")
    
    col_k1, col_k2 = st.columns([2, 1])
    with col_k1:
        new_key_name = st.text_input("Nombre de la nueva Llave (ej. 'Sitio Cliente A')")
    with col_k2:
        st.write("") # Spacer
        st.write("") # Spacer
        import secrets
        if st.button("➕ Crear Nueva Llave", use_container_width=True):
            if new_key_name.strip():
                new_key = "sm_" + secrets.token_hex(16)
                from api import db_manager
                if db_manager.create_api_key(new_key_name.strip(), new_key):
                    st.success(f"Llave '{new_key_name}' creada con éxito.")
                    st.rerun()
                else:
                    st.error("Error al crear la llave en la base de datos.")
            else:
                st.warning("Debes ingresar un nombre para la llave.")
                
    st.subheader("Llaves Activas")
    from api import db_manager
    keys = db_manager.get_api_keys()
    
    selected_key_for_snippet = os.getenv("WIDGET_API_KEY", "TU_API_KEY") # Default fallback
    
    if keys:
        import pandas as pd
        df_keys = pd.DataFrame(keys)
        # Reordenar columnas para visualización
        df_keys = df_keys[['name', 'key', 'created_at']]
        df_keys.columns = ['Nombre del Sitio / Cliente', 'API Key', 'Fecha de Creación']
        st.dataframe(df_keys, use_container_width=True)
        
        st.markdown("**Revocar Acceso**")
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            key_to_delete = st.selectbox("Selecciona la llave a eliminar", [k['key'] for k in keys], format_func=lambda x: next(k['name'] for k in keys if k['key'] == x) + " (" + x[:10] + "...)")
        with col_r2:
            st.write("")
            if st.button("🗑️ Eliminar Llave", type="secondary", use_container_width=True):
                if db_manager.delete_api_key(key_to_delete):
                    st.success("Llave revocada exitosamente. El widget asociado dejará de funcionar inmediatamente.")
                    st.rerun()
                else:
                    st.error("Hubo un error al eliminar la llave.")
                    
        # Para el snippet
        selected_key_for_snippet = st.selectbox("🔑 Selecciona qué llave usar para generar el código de instalación:", [k['key'] for k in keys], format_func=lambda x: next(k['name'] for k in keys if k['key'] == x))
    else:
        st.info("No tienes llaves multi-sitio generadas aún. El widget usará la llave global de tu .env.")

    st.divider()
    
    st.header("🌐 Código de Instalación")
    st.markdown("Simplemente copia y pega el siguiente código HTML justo antes de que cierre la etiqueta `</body>` en tu página externa:")
    
    col_ip, _ = st.columns(2)
    with col_ip:
        domain_or_ip = st.text_input("IP o Dominio de este servidor:", value="localhost", help="Coloca la IP pública o el nombre de dominio donde se hospeda este contenedor. Ej: 181.43.151.255")
    
    api_port = os.getenv("API_PORT", "8000")
    code = f'<script src="http://{domain_or_ip}:{api_port}/static/widget.js" data-api-key="{selected_key_for_snippet}" defer></script>'
    st.code(code, language="html")
    st.info("¡Eso es todo! El botón flotante aparecerá automáticamente en tu sitio web consumiendo de forma nativa la Configuración que hayas guardado.")

# --- TAB 4: GESTIÓN DE LEADS ---
with tab_leads:
    st.header("🤝 Leads Capturados")
    st.markdown("Lista de prospectos que han interactuado con el bot y han proporcionado sus datos de contacto.")
    
    DB_PATH = "conversations.db"
    if os.path.exists(DB_PATH):
        try:
            import sqlite3
            import pandas as pd
            
            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query("SELECT name as Nombre, email as Email, phone as Teléfono, company as Empresa, cargo as Cargo, resumen as Resumen, timestamp as Fecha FROM leads ORDER BY timestamp DESC", conn)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Botón de descarga CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Descargar Leads (CSV)",
                    csv,
                    "leads_chatbot.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.info("Aún no se han capturado leads. El bot empezará a recopilarlos cuando los usuarios proporcionen sus datos.")
        except Exception as e:
            st.error(f"Error al cargar los leads: {e}")
    else:
        st.warning("La base de datos aún no se ha inicializado.")

# --- TAB 5: ANALÍTICAS ---
with tab_analytics:
    st.header("📈 Analíticas Avanzadas del Asistente")
    st.markdown("Métricas detalladas de comportamiento de usuario, seguridad y rendimiento.")
    if os.path.exists(DB_PATH):
        try:
            import sqlite3
            import pandas as pd
            import datetime
            with sqlite3.connect(DB_PATH) as conn:
                df_leads = pd.read_sql_query("SELECT session_id, timestamp FROM leads", conn)
                df_msgs = pd.read_sql_query("SELECT session_id, role, flag, feedback, timestamp FROM messages", conn)
            
            if not df_msgs.empty:
                df_msgs['date'] = pd.to_datetime(df_msgs['timestamp']).dt.date
                if not df_leads.empty:
                    df_leads['date'] = pd.to_datetime(df_leads['timestamp']).dt.date
                
                min_date = df_msgs['date'].min()
                max_date = df_msgs['date'].max()
                
                def filter_by_date(df, start, end):
                    return df[(df['date'] >= start) & (df['date'] <= end)]

                def render_date_filter(key_prefix, min_date, max_date):
                    today = datetime.date.today()
                    col_opt, col_cust = st.columns([1, 2])
                    option = col_opt.selectbox("Periodo", ["Esta semana", "Últimos 30 días", "Personalizado"], key=f"sel_{key_prefix}")
                    
                    start_date = None
                    end_date = None
                    
                    if option == "Esta semana":
                        start_date = today - datetime.timedelta(days=today.weekday())
                        end_date = today
                    elif option == "Últimos 30 días":
                        start_date = today - datetime.timedelta(days=30)
                        end_date = today
                    else:
                        date_range = col_cust.date_input("Rango Personalizado", value=(min_date, max_date), min_value=min_date, max_value=max_date, key=f"date_{key_prefix}")
                        if len(date_range) == 2:
                            start_date, end_date = date_range

                    return start_date, end_date

                st.divider()
                st.subheader("📊 Métricas Clave de Conversión")
                s_conv, e_conv = render_date_filter("conv", min_date, max_date)
                if s_conv and e_conv:
                    f_msgs_conv = filter_by_date(df_msgs, s_conv, e_conv)
                    f_leads_conv = filter_by_date(df_leads, s_conv, e_conv) if not df_leads.empty else pd.DataFrame()
                    
                    unique_sessions = f_msgs_conv['session_id'].nunique()
                    lead_sessions = f_leads_conv['session_id'].nunique() if not f_leads_conv.empty else 0
                    dropoff_rate = ((unique_sessions - lead_sessions) / unique_sessions * 100) if unique_sessions > 0 else 0
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Sesiones Únicas (Total)", unique_sessions)
                    m2.metric("Leads Generados", lead_sessions, f"{(lead_sessions/unique_sessions*100) if unique_sessions>0 else 0:.1f}%")
                    m3.metric("Tasa de Abandono", f"{dropoff_rate:.1f}%", "-Sesiones sin Lead", delta_color="inverse")
                else:
                    st.info("Selecciona un rango de fechas válido.")

                st.divider()
                st.subheader("🛡️ Seguridad e Intención")
                s_sec, e_sec = render_date_filter("sec", min_date, max_date)
                if s_sec and e_sec:
                    f_msgs_sec = filter_by_date(df_msgs, s_sec, e_sec)
                    unique_sessions_sec = f_msgs_sec['session_id'].nunique()
                    
                    jailbreak_sessions = f_msgs_sec[f_msgs_sec['flag'] == 'jailbreak']['session_id'].nunique()
                    trigger_sessions = f_msgs_sec[f_msgs_sec['flag'] == 'lead_trigger']['session_id'].nunique()
                    
                    jb_rate = (jailbreak_sessions / unique_sessions_sec * 100) if unique_sessions_sec > 0 else 0
                    tr_rate = (trigger_sessions / unique_sessions_sec * 100) if unique_sessions_sec > 0 else 0
                    
                    s1, s2 = st.columns(2)
                    s1.metric("Intentos de Jailbreak", jailbreak_sessions, f"{jb_rate:.1f}% de sesiones", delta_color="inverse")
                    s2.metric("Solicitudes de Contacto Humano", trigger_sessions, f"{tr_rate:.1f}% de sesiones")
                else:
                    st.info("Selecciona un rango de fechas válido.")

                st.divider()
                st.subheader("⭐ Satisfacción del Usuario (Feedback)")
                s_feed, e_feed = render_date_filter("feed", min_date, max_date)
                if s_feed and e_feed:
                    f_msgs_feed = filter_by_date(df_msgs, s_feed, e_feed)
                    feedbacks = f_msgs_feed['feedback'].value_counts()
                    likes = feedbacks.get('like', 0)
                    dislikes = feedbacks.get('dislike', 0)
                    total_feedback = likes + dislikes
                    
                    fb1, fb2, fb3 = st.columns(3)
                    fb1.metric("👍 Me Gusta", likes)
                    fb2.metric("👎 No Me Gusta", dislikes)
                    if total_feedback > 0:
                        fb3.metric("Ratio de Aprobación", f"{(likes/total_feedback*100):.1f}%")
                    else:
                        fb3.metric("Ratio de Aprobación", "N/A")
                else:
                    st.info("Selecciona un rango de fechas válido.")

                st.divider()
                st.subheader("📈 Tráfico de Interacciones (Mensajes Usuario)")
                s_traf, e_traf = render_date_filter("traf", min_date, max_date)
                if s_traf and e_traf:
                    f_msgs_traf = filter_by_date(df_msgs, s_traf, e_traf)
                    user_msgs = f_msgs_traf[f_msgs_traf['role'] == 'user']
                    chats_per_day = user_msgs.groupby('date').size()
                    st.bar_chart(chats_per_day)
                else:
                    st.info("Selecciona un rango de fechas válido.")
            else:
                st.info("Aún no hay mensajes para mostrar métricas.")
        except Exception as e:
            st.error(f"Error cargando analíticas: {e}")
    else:
        st.warning("Debe interactuar primero para generar la Base de Datos.")

st.divider()
cargar_btn = st.button("💾 Guardar Configuración Global y Aplicar Cambios", type="primary", use_container_width=True)

# --- LÓGICA DE GUARDADO ---
if "engine_ready" not in st.session_state:
    st.session_state.engine_ready = False

if saved_config and "chat_key" in saved_config and not st.session_state.engine_ready:
    st.session_state.engine_ready = True

if cargar_btn:
    if not chat_key or not embed_key:
        st.error("⚠️ Por favor, ingresa las API Keys necesarias antes de guardar.")
    else:
        with st.spinner("Guardando configuración y recargando vectores de documentos..."):
            try:
                save_config(chat_provider, chat_key, embed_provider, embed_key, openrouter_model, bot_name, primary_color, show_sources, allowed_origins, temperature, use_streaming)
                st.cache_resource.clear()
                st.session_state.messages = []
                index, qa_template = get_engine(chat_provider, chat_key, embed_provider, embed_key, openrouter_model, bot_name, temperature)
                query_engine = index.as_query_engine(text_qa_template=qa_template, similarity_top_k=3)
                st.session_state.engine_ready = True
                st.success("✅ ¡Configuración LLM guardada! El motor principal y el Widget web han sido actualizados exitosamente.")
            except Exception as e:
                st.error(f"Error al inicializar el motor de IA: {e}")
                st.session_state.engine_ready = False

if not st.session_state.engine_ready:
    with tab_chat:
        st.info("👈 Ve a la pestaña **Configuración de LLM**, ingresa tus API Keys y presiona **'Guardar Configuración'** para activar el chat.")
    st.stop()
else:
    try:
         index, qa_template = get_engine(
            chat_provider, 
            chat_key or saved_config.get("chat_key"), 
            embed_provider, 
            embed_key or saved_config.get("embed_key"), 
            openrouter_model,
            bot_name or bot_name_default
        )
         query_engine = index.as_query_engine(text_qa_template=qa_template, similarity_top_k=3)
    except Exception as e:
        with tab_chat:
            st.error(f"El motor no se pudo cargar desde la caché: {e}")
        st.stop()

# --- TAB 1: CHAT DE PRUEBA ---
with tab_chat:
    st.header("🧪 Prueba Local del Asistente")
    st.markdown("Verifica que el bot esté respondiendo correctamente antes de llevar el Widget a tu web externa.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Escribe tu pregunta de prueba..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Buscando respuestas en la base de conocimiento..."):
                    try:
                        response = query_engine.query(prompt)
                        st.markdown(response.response)
                        
                        if response.source_nodes:
                            with st.expander("Fuentes documentales extraídas"):
                                for idx, node in enumerate(response.source_nodes):
                                    source_file = node.metadata.get('file_name', 'Archivo desconocido')
                                    st.write(f"**Fuente {idx+1}: {source_file}**")
                                    st.caption(f'"{node.get_text()[:400]}..."')
                                    
                        st.session_state.messages.append({"role": "assistant", "content": response.response})
                    except Exception as e:
                        error_msg = f"Ocurrió un error de conexión al LLM: {e}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
