# Administrador de IA - SixManager (Robotito RAG Chatbot)

Este proyecto despliega un ecosistema completo para un Asistente Inteligente basado en RAG (Retrieval-Augmented Generation) con capacidades de captura de Leads. Está compuesto por un **Dashboard de Administración (Streamlit)** y una **API Backend (FastAPI)** que sirve un **Widget Web (JavaScript)** integrable en cualquier página externa.

## Características Principales

- **Multi-Proveedor de LLMs**: Soporte integrado para Gemini, OpenAI y OpenRouter (Claude, etc.).
- **Motor RAG Dinámico**: Lectura e indexación automática de documentos PDF usando LlamaIndex. Las fuentes consultadas se muestran en las respuestas.
- **Panel de Control UI**: Un panel en Streamlit para configurar las API Keys, seleccionar los modelos, probar el chat internamente, configurar el aspecto visual del Widget web y gestionar los leads obtenidos.
- **Gestión Multi-Sitio Segura**: Sistema nativo de API Keys con validación estricta de dominios permitidos (CORS) para integrar el widget en múltiples webs cliente bloqueando usos no autorizados.
- **Analíticas Avanzadas**: Métricas gerenciales sobre la tasa de abandono, aprobación de usuarios, intención de compra y detecciones de Jailbreaks, filtrables con calendarios de rango de fechas.
- **Widget Web Embebible**: Un script `widget.js` configurable (Streaming mode, diseño Premium de cristal, renderizado Markdown) que permite inyectar el asistente en cualquier sitio externo usando un simple `<script>`.
- **Captura de Leads y Cumplimiento Legal**: Detecta automáticamente la intención de compra del usuario (o usando el flag `[TRIGGER_LEAD_MODAL]`) y despliega un formulario. Incluye casilla de consentimiento acorde a la Ley 19.628 (Chile) y sistema de Captcha para evitar spam.
- **Seguridad Robusta**: Incluye filtros activos contra inyecciones de prompts (Jailbreaks) y protección de identidad corporativa inquebrantable.
- **Base de Datos Local**: Almacena las conversaciones y recopila los prospectos comerciales de forma estructurada en SQLite local (`conversations.db`).
- **Preparado para Producción**: Despliegue empaquetado y orquestado mediante Docker Compose para garantizar portabilidad.

## Requisitos Previos

- **Docker** y **Docker Compose** instalados en el servidor o equipo local.
- Claves de API de los servicios de IA que desees utilizar (Google AI Studio, OpenAI, o OpenRouter).

## Estructura del Proyecto

```text
├── .env.example         # Plantilla de variables de entorno (Copiar a .env)
├── Dockerfile           # Imagen Docker base para la API y la UI
├── docker-compose.yml   # Orquestación de los contenedores
├── app.py               # Dashboard administrativo (Streamlit)
├── api.py               # Servidor Backend RAG (FastAPI)
├── config/              # Almacena el archivo config.json (persistencia de configuración UI)
├── src/
│   ├── baseConocimiento/ # Carpeta donde deben ir los archivos PDF de tu empresa
│   └── engine.py        # Inicialización del motor LLM y de Embeddings
├── static/
│   └── widget.js        # Código fuente del botón asistente para webs externas
└── wipe_config.py       # Script de utilidad para limpiar las API Keys de la configuración local
```

## Guía de Instalación y Despliegue Rápido

### Despliegue por Etapas Recomendado

Si quieres dejar el sistema montado antes de configurar modelos, embeddings o documentos, puedes hacer primero una etapa de **bootstrap de despliegue**:

```bash
chmod +x deploy.sh
./deploy.sh --bootstrap-only --prod
```

Eso deja levantados los servicios, la persistencia básica y el widget listo para integrarse, pero sin intentar inicializar todavía el motor RAG.

### 1. Preparar las Variables de Entorno

Clona el repositorio y duplica el archivo `.env.example` renombrándolo como `.env`.

```bash
cp .env.example .env
```
Abre el archivo `.env` y rellena las API Keys que vayas a usar. 

> [!IMPORTANT]
> Define la variable `ADMIN_PASSWORD` en el `.env`. Por defecto es `admin123`. Esta será la clave para acceder al Dashboard administrativo.

También puedes definir el `ALLOWED_ORIGINS` para controlar qué dominios web pueden renderizar el widget.

### 2. Proveer el Conocimiento (Lectura de Documentos)

Coloca todos los archivos PDF con la información, catálogos, y normativas de la empresa dentro de la carpeta `src/baseConocimiento/`. El sistema los leerá en el arranque o al guardar los cambios desde el Dashboard.

### 3. Levantar los Servicios

#### Opción A: Despliegue Manual (Docker Compose)
Ejecuta el siguiente comando en la raíz del proyecto para crear la imagen y levantar los contenedores:

```bash
docker compose up -d --build
```
Esto levantará dos contenedores:
1. `robotito_chatbot_ui` (Puerto 8501)
2. `robotito_chatbot_api` (Puerto 8000)

#### Opción B: Script de Despliegue Automatizado (Recomendado)
Si prefieres una configuración guiada que gestione automáticamente el archivo `.env`, las API Keys y los puertos, puedes usar el script incluido:

```bash
chmod +x deploy.sh
./deploy.sh
```
Este script se encarga de verificar dependencias, crear el archivo `.env` con contraseñas seguras, solicitarte las llaves de IA de forma interactiva y levantar los servicios por ti.

Para un despliegue base sin llaves ni documentos, usa:

```bash
./deploy.sh --bootstrap-only --prod
```

### 4. Acceder al Panel de Control

Una vez que los contenedores estén corriendo, abre tu navegador web y dirígete a:
👉 `http://localhost:8501` (o la IP de tu servidor seguida del puerto 8501).

Desde el panel, dirígete a **"Configuración de LLM"**, confirma los proveedores deseados y presiona el botón **"Guardar Configuración Global y Aplicar Cambios"** para que el RAG procese los PDFs recarguen la configuración de los modelos.

> **Nota:** ¡El chat y el Widget no funcionarán hasta que guardes la configuración en el panel por primera vez!

## Manuales Adicionales

Para entender más a fondo la operación y despliegue del proyecto, dirígete a las siguientes guías:

- **[Manual de Usuario (MANUAL_USUARIO.md)](MANUAL_USUARIO.md)**: Guía detallada sobre cómo operar el panel administrativo, modificar configuraciones del bot, usar el chat de prueba y descargar los Leads.
- **[Manual de Implementación del Widget (MANUAL_IMPLEMENTACION.md)](MANUAL_IMPLEMENTACION.md)**: Instrucciones paso a paso para desarrolladores sobre cómo incrustar y personalizar el widget inteligente en páginas web externas.
