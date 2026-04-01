# Changelog - Robotito (SixManager)

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [v1.2.0] - 2026-04-01
### Añadido
- **Seguridad Robusta**: Implementación de filtros dinámicos contra Jailbreaks e inyecciones de prompts en `api.py`.
- **Sistema de Feedback**: Botones de calificación (👍/👎) en el widget web con métricas integradas en el Dashboard.
- **Troubleshooting**: Nueva sección de FAQ en el Manual de Usuario y guía de solución de problemas de conexión/CORS.
- **Limpieza de Configuración**: Script `wipe_config.py` para saneamiento rápido de credenciales locales.

### Mejorado
- **Documentación Completa**: Actualización profunda de `README.md`, `MANUAL_USUARIO.md` y `MANUAL_IMPLEMENTACION.md`.
- **Experiencia de Usuario (Widget)**: Clarificación visual en los triggers de Leads mediante botones CTA menos intrusivos.
- **Modo Streaming**: Ahora las acciones posteriores (Leads/Fuentes) se sincronizan correctamente tras finalizar la generación de texto.

## [v1.1.0] - 2026-03-31
### Añadido
- **Gestión Multi-Sitio**: Sistema de generación y revocación de API Keys dedicadas por cliente en el Dashboard.
- **Validación de Origen (CORS)**: Middleware de seguridad estricto que valida el dominio `Origin/Referer` contra la lista blanca del administrador.
- **Analíticas de Conversión**: Nuevas métricas de Tasa de Abandono (Drop-off) y análisis estadístico de sesiones vs leads.

## [v1.0.0] - 2026-03-26
### Añadido
- **Captura de Leads**: Formulario dinámico con cumplimiento de la Ley 19.628 (Chile) y Captcha matemático.
- **Motor RAG Multi-Proveedor**: Soporte para Gemini, OpenAI y OpenRouter (Claude) configurables desde la UI.
- **Persistencia Local**: Base de datos SQLite (`conversations.db`) para historial de chats y almacenamiento de prospectos.
- **Dashboard Administrativo**: Interfaz en Streamlit para control total del ecosistema IA.
- **Widget Web Premium**: Script JavaScript inyectable con diseño de cristal y soporte para Markdown.
