# Manual de Implementación Técnica del Widget

Esta guía está orientada a desarrolladores, webmasters o administradores de sistemas que deseen incrustar (embed) el Asistente Inteligente de SixManager en páginas web externas.

## 1. Funcionamiento Básico

El Widget es un script en JavaScript (`widget.js`) servido por el Backend FastAPI en el puerto `8000`. Al cargarse, el script inyectará automáticamente un botón flotante y una ventana de chat en la esquina inferior derecha de la página donde se coloque.

### Autonomía del Script:
- Crea su propia estructura HTML en el DOM (`#sm-chat-widget-container`).
- Inyecta sus propios estilos CSS, asegurando que no afecte ni rompa los estilos preexistentes del sitio web que lo hospeda.
- Gestiona sesiones únicas por pestaña vía `sessionStorage`.
- Se comunica directamente con la API REST enviando mensajes, recibiendo un Markdown interpretado de los LLM, y gestionando la captura de leads a través de modales.
- Permite al usuario calificar las respuestas con un sistema de **Feedback (👍/👎)** integrado.

## 2. Instalación en la Web Externa

Para incrustar el Widget IA, debes agregar una única línea de código en tu HTML, idealmente justo antes de la etiqueta de cierre `</body>`.

```html
<!-- Incrustación del Asistente SixManager -->
<script 
    src="http://<IP_O_DOMINIO_DEL_SERVIDOR>:8000/static/widget.js" 
    data-api-key="tu_clave_secreta_multisitio"
    data-api-base="https://<HOST_DE_LA_API>"
    defer>
</script>
```

### Parámetros Críticos de Conexión:
- **`src`**: Reemplaza `<IP_O_DOMINIO_DEL_SERVIDOR>` con la IP pública o el dominio donde esté corriendo el contenedor Docker (`robotito_chatbot_api`).
- **`data-api-key`**: Es tu llave de autorización **Multi-Sitio**. Debes generarla desde el panel administrativo de Streamlit en la pestaña "Integración Web". Sin esta llave válida, el servidor bloqueará los mensajes con `HTTP 401: Unauthorized`. *(Nota: También puedes usar la llave maestra global del `.env`).*
- **`data-api-base`**: Recomendado cuando el widget se sirve detrás de proxy, CDN o un dominio distinto al que expone la API. Permite fijar explícitamente la base de la API sin depender del host del `script`.

### Opciones de Integración Disponibles

El widget también acepta estos atributos opcionales:

- `data-primary-color="#761472"` para fijar un color inicial antes de cargar la configuración remota.
- `data-bot-name="Robotito"` para personalizar el nombre visible del asistente.
- `data-position="left"` para mover el botón a la esquina inferior izquierda.
- `data-z-index="999999"` para ajustar la superposición frente al sitio anfitrión.

## 3. Seguridad y CORS Estricto (Protección de Origen)

Debido a que el `data-api-key` es visible en el código fuente HTML del navegador (Client-Side), el backend implementa una fuerte política de validación de Origen para evitar que sitios de terceros roben y abusen de tus llaves.

- **Validación HTTP Origin/Referer:** El middleware analiza las cabeceras HTTP evaluando dinámicamente el dominio exacto desde el cual se generó la petición al bot.
- **Configuración Obligatoria:** Debes declarar la variable `Orígenes Permitidos (CORS)` en el tablero administrativo (o variable de entorno `ALLOWED_ORIGINS`), separando por comas los dominios de confianza que utilizarán tu asistente. Ej: `https://mi-empresa.cl,http://localhost:5500`.
- **Protección Rate Limiting:** El servidor utiliza la librería `slowapi` con una política por defecto de **5 mensajes por minuto** por cada dirección IP para prevenir abusos.
- Si alguien roba tu `data-api-key` e intenta ejecutar tu script en su computadora local o desde `sitio-pirata.com` (origen no registrado), el servidor anulará la interacción con un error `HTTP 403: Forbidden`.

## 4. Captura de Datos de Leads (Modal)

El widget incluye un formulario flotante programado para aparecer **automáticamente** en dos situaciones (Triggers):

1. **Trigger Semántico por LLM**: Si el flujo del Prompt del LLM detecta que el usuario quiere contratar servicios corporativos o marcas representadas, el LLM emite internamente un flag `[TRIGGER_LEAD_MODAL]` que el servidor captura.
2. **Trigger por Regex / Palabras Clave**: Si el usuario final escribe explícitamente palabras como *"cotizar"*, *"precio"*, *"interesado"*, *"demo"*, o detecta un **número de celular** o un **email**, se activará el flujo de captura.

> [!NOTE]
> Para garantizar una experiencia de usuario fluida, el trigger no abre el modal de forma intrusiva e inmediata. En su lugar, el widget inyecta un **Botón de Llamado a la Acción (CTA)** dentro del chat: *"Solicitar Atención Personalizada ✨"*. Al hacer clic, el usuario abre voluntariamente el formulario de contacto.

### Captcha Matemático y Consentimiento de Privacidad:
- Para evitar interacciones de bots externos en los formularios web de Leads, el modal inyecta dinámicamente un **Captcha matemático simple** provisto en JavaScript.
- Requiere Checkbox obligatorio validando el marco de **Ley 19.628 de Chile** para almacenar la información recolectada de forma persistente en `conversations.db` (visibles posteriormente en el Dashboard).

## 5. Pruebas Rápidas de Integración Local

Si estás probando el widget durante el desarrollo, puedes renderizar este bloque fácilmente en un archivo `index.html` simple:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Sitio Demo de Integración SixManager</title>
</head>
<body style="background-color: #f4f4f4;">
    <h1>Página de Pruebas de la Integración</h1>
    <p>El botón de chat debería aparecer abajo a la derecha en unos segundos...</p>

    <script src="http://localhost:8000/static/widget.js" defer></script>
</body>
</html>
```

Abre este archivo HTML directamente en tu navegador (ej: doble click, abriendo `file:///...`) y verifica que el chat funciona contra `localhost:8000`.
