#!/bin/bash

# ==============================================================================
# Script de Despliegue Automatizado - Asistente IA SixManager (Robotito RAG)
# ==============================================================================

# Colores para la salida en consola
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  Inicializando Despliegue de SixManager AI...      ${NC}"
echo -e "${BLUE}====================================================${NC}"

BOOTSTRAP_ONLY=false
COMPOSE_FILE="docker-compose.yml"

for arg in "$@"; do
    case "$arg" in
        --bootstrap-only)
            BOOTSTRAP_ONLY=true
            ;;
        --prod)
            COMPOSE_FILE="docker-compose.prod.yml"
            ;;
    esac
done

# 1. Verificación de Docker y Docker-Compose
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker no está instalado en este servidor.${NC}"
    echo "Instala Docker usando: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose no está instalado.${NC}"
    echo "Instálalo usando: sudo apt install docker-compose (o tu gestor equivalente)"
    exit 1
fi

echo -e "${GREEN}✓ Docker y Docker-Compose detectados.${NC}"

# 2. Generación de `.env` si no existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}► No se encontró archivo .env. Creando uno a partir de la plantilla...${NC}"
    cp .env.example .env
    
    # Generar Password robusto para el Admin automáticamente
    RAND_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    sed -i "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$RAND_PASS/" .env
    
    # Generar API Key robusta para el Widget automáticamente
    RAND_WIDGET_KEY=$(python3 -c "import secrets; print('sm_' + secrets.token_hex(16))")
    sed -i "s/^WIDGET_API_KEY=.*/WIDGET_API_KEY=$RAND_WIDGET_KEY/" .env
    
    echo -e "${GREEN}✓ Archivo .env base creado con credenciales aleatorias robustas.${NC}"
else
    echo -e "${GREEN}✓ Archivo .env ya existe.${NC}"
fi

if [[ "$BOOTSTRAP_ONLY" == true ]]; then
    echo -e "${YELLOW}► Modo bootstrap-only activado: se omitirá la configuración de API Keys y del motor RAG.${NC}"
    input_gemini=""
    input_openai=""
    input_openrouter=""
    CHAT_PROVIDER="Gemini"
    EMBED_PROVIDER="Gemini"
else
    # 3. Configuración Interactiva de API Keys
    echo -e "${YELLOW}► Configuración de Inteligencia Artificial (Opcional)${NC}"
    echo "Presiona Enter para dejarlas en blanco y configurarlo luego en el Panel de Administración Web."

    read -p "Ingresa tu GOOGLE_API_KEY (Para Gemini): " input_gemini
    read -p "Ingresa tu OPENAI_API_KEY (Para ChatGPT): " input_openai
    read -p "Ingresa tu OPENROUTER_API_KEY (Para Claude, etc): " input_openrouter

    # 3.1 Configuración de Proveedores por Defecto
    echo -e "${YELLOW}► Selección de Proveedores de IA (Escribe el número)${NC}"

    options_chat=("Gemini" "OpenAI" "OpenRouter")
    PS3="Selecciona el Proveedor de Chat [1-3, def: Gemini]: "
    select opt in "${options_chat[@]}"
    do
        case $opt in
            "Gemini"|"OpenAI"|"OpenRouter")
                CHAT_PROVIDER=$opt
                break
                ;;
            *)
                if [[ -z "$REPLY" ]]; then
                    CHAT_PROVIDER="Gemini"
                    break
                fi
                echo -e "${RED}Opción inválida. Intenta con un número del 1 al 3.${NC}"
                ;;
        esac
    done

    options_embed=("Gemini" "OpenAI")
    PS3="Selecciona el Proveedor de Embedding [1-2, def: Gemini]: "
    select opt in "${options_embed[@]}"
    do
        case $opt in
            "Gemini"|"OpenAI")
                EMBED_PROVIDER=$opt
                break
                ;;
            *)
                if [[ -z "$REPLY" ]]; then
                    EMBED_PROVIDER="Gemini"
                    break
                fi
                echo -e "${RED}Opción inválida. Intenta con un número 1 o 2.${NC}"
                ;;
        esac
    done
fi

if [[ ! -z "$input_gemini" ]]; then
    sed -i "s/^GOOGLE_API_KEY=.*/GOOGLE_API_KEY=$input_gemini/" .env
    echo -e "${GREEN}✓ Clave Gemini inyectada.${NC}"
else
    sed -i "s/^GOOGLE_API_KEY=.*/GOOGLE_API_KEY=/" .env
fi

if [[ ! -z "$input_openai" ]]; then
    sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$input_openai/" .env
    echo -e "${GREEN}✓ Clave OpenAI inyectada.${NC}"
else
    sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=/" .env
fi

if [[ ! -z "$input_openrouter" ]]; then
    sed -i "s/^OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$input_openrouter/" .env
    echo -e "${GREEN}✓ Clave OpenRouter inyectada.${NC}"
else
    sed -i "s/^OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=/" .env
fi

# Inyectar en el .env
if ! grep -q "^CHAT_PROVIDER=" .env; then
    echo "CHAT_PROVIDER=$CHAT_PROVIDER" >> .env
else
    sed -i "s/^CHAT_PROVIDER=.*/CHAT_PROVIDER=$CHAT_PROVIDER/" .env
fi

if ! grep -q "^EMBED_PROVIDER=" .env; then
    echo "EMBED_PROVIDER=$EMBED_PROVIDER" >> .env
else
    sed -i "s/^EMBED_PROVIDER=.*/EMBED_PROVIDER=$EMBED_PROVIDER/" .env
fi

echo -e "${GREEN}✓ Proveedores configurados: Chat -> $CHAT_PROVIDER | Embedding -> $EMBED_PROVIDER${NC}"

if ! grep -q "^ROBOTITO_BOOTSTRAP_ENGINE=" .env; then
    echo "ROBOTITO_BOOTSTRAP_ENGINE=false" >> .env
else
    sed -i "s/^ROBOTITO_BOOTSTRAP_ENGINE=.*/ROBOTITO_BOOTSTRAP_ENGINE=false/" .env
fi

# Limpieza de config.json si existe para evitar fugas de sesiones anteriores
if [ -f "config/config.json" ]; then
    echo -e "${YELLOW}► Detectado config.json previo. ¿Deseas resetear las llaves del Dashboard para una instalación limpia? (s/n)${NC}"
    read -p "> " reset_config
    if [[ "$reset_config" == "s" || "$reset_config" == "S" ]]; then
        # Usar python para limpiar el JSON de forma segura
        python3 -c 'import json, os; cfg="config/config.json"; d=json.load(open(cfg)); d["chat_key"]=""; d["embed_key"]=""; json.dump(d, open(cfg, "w"))' 2>/dev/null
        echo -e "${GREEN}✓ Configuración del Dashboard reseteada (Keys borradas).${NC}"
    fi
fi

# 4. Configuración Dinámica de Puertos
echo -e "${YELLOW}► Configuración de Puertos del Sistema${NC}"
read -p "Puerto para el Panel Administrativo [Enter para 8501]: " input_ui
UI_PORT=${input_ui:-8501}

read -p "Puerto para el Backend (Widget API) [Enter para 8000]: " input_api
API_PORT=${input_api:-8000}

# Exportar las variables localmente para que docker-compose las tome durante esta ejecución.
export UI_PORT=$UI_PORT
export API_PORT=$API_PORT

# Además inyectarlas en el .env si no existen, para que reinicios posteriores las mantengan.
if ! grep -q "^UI_PORT=" .env; then
    echo "UI_PORT=$UI_PORT" >> .env
else
    sed -i "s/^UI_PORT=.*/UI_PORT=$UI_PORT/" .env
fi

if ! grep -q "^API_PORT=" .env; then
    echo "API_PORT=$API_PORT" >> .env
else
    sed -i "s/^API_PORT=.*/API_PORT=$API_PORT/" .env
fi

echo -e "${GREEN}✓ Puertos configurados: UI -> $UI_PORT | API -> $API_PORT${NC}"

# 5. Creación de Directorios Críticos y Base de Datos (Prevención de permisos Root de Docker)
echo -e "${YELLOW}► Verificando estructura de directorios y Base de Datos...${NC}"

mkdir -p src/baseConocimiento
mkdir -p config
mkdir -p static
mkdir -p data

# Auto-generamos el archivo SQLite para que se cree con los permisos del usuario local
if [ ! -f "conversations.db" ]; then
    touch conversations.db
    echo -e "${GREEN}✓ Base de datos conversations.db pre-creada vacía.${NC}"
fi
if [ ! -f "data/conversations.db" ]; then
    touch data/conversations.db
fi

echo -e "${GREEN}✓ Estructura de archivos lista.${NC}"

# 6. Construcción y Ejecución de Docker Compose
echo -e "${BLUE}► Construyendo imagenes y levantando contenedores (esto tomará unos minutos)...${NC}"
docker compose -f "$COMPOSE_FILE" down # Limpieza
docker compose -f "$COMPOSE_FILE" up -d --build

# 7. Comprobación y Mensaje Final
if [ $? -eq 0 ]; then
    # Extraer el password actual del .env para mostrarlo al usuario al final
    CURRENT_ADMIN_PASS=$(grep "^ADMIN_PASSWORD=" .env | cut -d'=' -f2)

    echo -e "${BLUE}====================================================${NC}"
    echo -e "${GREEN}¡Despliegue Exitoso! 🚀${NC}"
    echo -e "Tu ecosistema Robotito está corriendo en segundo plano."
    echo -e ""
    echo -e "${YELLOW}Panel de Control (Admin):${NC} http://localhost:${UI_PORT}"
    echo -e "${BLUE}CONTRASEÑA DE ACCESO ADMINISTRADOR:${NC} ${GREEN}${CURRENT_ADMIN_PASS}${NC}"
    echo -e ""
    echo -e "${YELLOW}Endpoint de la API IA:${NC}    http://localhost:${API_PORT}"
    echo -e ""
    echo -e "Siguientes Pasos Obligatorios:"
    echo -e "1. Sube tus PDFs dentro de la carpeta: ${NC}src/baseConocimiento/"
    echo -e "2. Entra al Panel de Control en el puerto ${UI_PORT}."
    echo -e "3. Completa llaves y proveedores cuando llegue la etapa de configuración."
    echo -e "4. Presiona el botón ${GREEN}'Guardar Configuración y Aplicar Cambios'${NC}."
    echo -e "${BLUE}====================================================${NC}"
else
    echo -e "${RED}Ocurrió un error al intentar levantar docker-compose. Revisa los logs.${NC}"
fi
