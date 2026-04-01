# Manual de Usuario - Asistente Inteligente SixManager

Bienvenido al manual de uso del Panel de Administración del chatbot inteligente (Dashboard Streamlit). Este panel te permitirá controlar la inteligencia de tu asistente, testearlo localmente, personalizar su apariencia web y descargar a los clientes potenciales (leads).

## Acceso al Panel

Para ingresar, abre tu navegador web y visita: `http://<IP-DE-TU-SERVIDOR>:8501`. (Si lo estás ejecutando en tu propia máquina, ingresa a `http://localhost:8501`).

La interfaz está dividida en 4 pestañas principales:

---

### 1. Pestaña: Configuración de LLM (⚙️)

Es el **cerebro del sistema**. Aquí definirás qué inteligencia artificial usará tu asistente web.

1. Selecciona tu **Proveedor de Chat** (Gemini, OpenAI, o OpenRouter).
2. Si seleccionas OpenRouter, ingresa el string del modelo específico (por ej: `anthropic/claude-3-haiku`).
3. Ingresa tu **API Key** correspondiente en la casilla de contraseña. 
4. Selecciona el **Proveedor de Embeddings** (solo Gemini u OpenAI). Este es el modelo que "lee" los PDFs. Ingresa también su respectiva API Key.
5. Ajusta el deslizador de **Temperatura** (0.0 a 1.0).
   - *Valores cercanos a 0.0*: Respuestas precisas, enfocadas y poco creativas.
   - *Valores más altos (0.7+)*: Respuestas variadas y creativas.
6. **IMPORTANTE**: Cada vez que agregues un documento PDF en el servidor, cambies de proveedor, o ingreses por primera vez al panel, **DEBES PRESIONAR EL BOTÓN A FINAL DE PÁGINA**: `💾 Guardar Configuración Global y Aplicar Cambios`.
   - Esto procesará los textos, guardará los parámetros y refrescará el widget. Mientras el botón cargue, el proceso estará "leyendo" tus documentos RAG.

---

### 2. Pestaña: Chat de Prueba (💬)

Una vez que guardes tu configuración con el paso anterior, podrás dirigirte al "Chat de Prueba". 

Esta pestaña sirve como un sandbox aislado donde podrás conversar con el IA en un entorno local, imitando lo que un usuario vería en tu página web.

- **Verificación**: Pregúntale al bot sobre tus productos o protocolos para asegurar que está respondiendo según los documentos oficiales (PDFs) suministrados.
- **Fuentes Documentales**: Debajo de cada respuesta del asistente, verás un recuadro expandible con los extractos de tus PDFs que el IA utilizó para contestar la pregunta. Esto es útil para auditar su seguridad anti-alucinaciones.

---

### 3. Pestaña: Integración Web (🌐)

Aquí personalizarás la identidad que los usuarios finales verán en tu sitio web e integrarás el gestor de llaves multi-sitio.

1. **Gestión de Llaves de Acceso (API Keys)**: Puedes pulsar "➕ Crear Nueva Llave" para generar claves dedicadas para tus distintos clientes o sitios. En la tabla inferior puedes revocar en vivo y al instante si una llave se vio expuesta.
2. **Nombre del Bot**: Este texto aparecerá en la cabecera del Widget web y afectará la personalidad que adopta el asistente.
3. **Color Principal**: Usa el selector de colores para elegir el tono de tu marca corporativa. Esto cambiará el botón flotante y las burbujas de diálogo del usuario.
4. **Fuentes Documentales y Streaming**: 
   - Puedes apagar/encender la visibilidad de los PDFs.
   - **Modo Escritura en Vivo (Streaming)**: El bot responde palabra por palabra de forma instantánea. 
   > [!NOTE]
   > Al usar Streaming, las sugerencias de contacto (Leads) aparecerán al final de la respuesta completa del bot, no de forma inmediata durante el inicio de la misma.
5. **Orígenes Permitidos (CORS)**: Limita qué páginas pueden ejecutar el widget a través de dominios seguros separados por comas. (Ej: `https://mi-empresa.cl`). De lo contrario bloquearemos las llamadas.
6. Presiona `💾 Guardar Configuración Global y Aplicar Cambios`.
7. En la parte inferior, verás un selector interactivo. Selecciona tu Llave creada y obtén el **Código de Instalación HTML** listo para dárselo a webmasters.

---

### 4. Pestaña: Gestión de Leads (🤝)

Toda interacción de los usuarios en donde manifiesten intención (ya sean cotizaciones, demos o interés general) generará triggers automáticos y mostrará un Modal de captura de datos con aceptación de la Ley de Privacidad 19.628 (Chile).

Cuando los usuarios llenen ese formulario flotante:
- Se guardarán los datos de forma inmediata y persistente.
- El asistente generará un mini-resumen inteligente de hasta 150 caracteres basándose en la conversación previa para que el vendedor de turno sepa a qué va la intención de compra.

En la tabla aparecerán los siguientes datos: **Nombre, Email, Teléfono, Empresa, Cargo, Resumen de lo que busca, y Fecha.**

**📥 Descarga de Leads:** Podrás apretar el botón de "Descarga en formato CSV" en la tabla para importar a tus clientes potenciales a tu CRM o hoja de Excel estándar.

---

### 5. Pestaña: Analíticas (📈)

Mide el ROI y la utilidad de tu bot conversacional con dashboards dinámicos para tomar buenas decisiones corporativas:

- **Tasas de Conversión y Abandono (Drop-off)**: Mide cuántas conversaciones "en blanco" se generaron frente a cuántas terminaron registrándose en el lead form.
- **Seguridad e Intención**: Detecta estadísticamente cuántos atacantes o bots trataron de inyectar código malicioso `(Jailbreaks)` o generaron Triggers `(Intención comercial)`.
- **Satisfacción del Usuario (👍/👎)**: Panel con el Feedback general reaccionado por los usuarios para verificar la efectividad de los prompts y base documental.
- _Todos los cuadrantes vienen con un selector que permite filtrar la analítica en métricas de **Esta Semana**, **Últimos 30 días** o un calendario **Personalizado**._

---

### 6. Resolución de Problemas (FAQ)

**¿Olvidó la contraseña del Dashboard?**
- La contraseña se define en el archivo `.env` bajo la variable `ADMIN_PASSWORD`. Si no está definida, el valor por defecto es `admin123`.

**¿El Widget no aparece en mi web?**
- Verifica que el dominio de tu web esté en la lista de **Orígenes Permitidos (CORS)** en la pestaña de Integración Web.
- Asegúrate de que el servidor API (puerto 8000) sea accesible desde internet o desde la red de tu web.

**¿Cómo resetear la configuración?**
- Puedes ejecutar el script `python wipe_config.py` en el servidor para limpiar las API Keys guardadas sin borrar los leads ni el historial.
- Si deseas borrar todo, elimina el archivo `conversations.db` y la carpeta `src/chroma_db`.

**¿El bot no responde sobre mis documentos?**
- Asegúrate de haber presionado el botón `💾 Guardar Configuración Global y Aplicar Cambios` para que el sistema procese los PDFs de la carpeta `src/baseConocimiento/`.
