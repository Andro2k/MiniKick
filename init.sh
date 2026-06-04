#!/bin/bash

# =============================================================
# CONSTANTES Y UI (Configuración Global)
# =============================================================
ROJO="\e[31m"
VERDE="\e[32m"
MAGENTA="\e[35m"
CIAN="\e[36m"
AMARILLO="\e[33m"
GRIS="\e[90m"
BG_AZUL="\e[44m\e[97m"
RESET="\e[0m"

trap 'tput cnorm; echo -e "\n  ${ROJO}✘ Operación cancelada.${RESET}"; exit 1' INT

# =============================================================
# CAPA DE PRESENTACIÓN / MOTOR INTERACTIVO
# =============================================================

ejecutar_con_spinner() {
    local mensaje="$1"
    shift
    local comando=("$@")
    tput civis 
    "${comando[@]}" > /tmp/repo_init_log.txt 2>&1 &
    local pid=$!
    local frames=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    local i=0
    while kill -0 $pid 2>/dev/null; do
        printf "\r  ${CIAN}%s${RESET} %s..." "${frames[i]}" "$mensaje"
        i=$(( (i + 1) % 10 ))
        sleep 0.1
    done
    tput cnorm 
    wait $pid
    local status=$?
    if [ $status -eq 0 ]; then
        printf "\r  ${VERDE}✔${RESET} %s... Hecho.       \n" "$mensaje"
    else
        printf "\r  ${ROJO}✘${RESET} %s... Error. (Ver /tmp/repo_init_log.txt)\n" "$mensaje"
    fi
    return $status
}

generar_menu_interactivo() {
    local opciones=("$@")
    local seleccion=0
    local total=${#opciones[@]}
    tput civis 
    while true; do
        for i in "${!opciones[@]}"; do
            if [ $i -eq $seleccion ]; then
                local texto_limpio=$(echo -e "${opciones[$i]}" | sed 's/\x1b\[[0-9;]*m//g')
                echo -e "  ${MAGENTA}❯${RESET} ${BG_AZUL} ${texto_limpio} ${RESET}\033[K"
            else
                echo -e "    ${opciones[$i]} \033[K"
            fi
        done
        read -rsn1 tecla
        if [[ $tecla == $'\e' ]]; then
            read -rsn2 tecla_resto
            tecla="$tecla$tecla_resto"
        fi
        case $tecla in
            $'\e[A') ((seleccion--)); [ $seleccion -lt 0 ] && seleccion=$((total - 1)) ;;
            $'\e[B') ((seleccion++)); [ $seleccion -ge $total ] && seleccion=0 ;;
            "") break ;;
        esac
        tput cuu $total
    done
    tput cnorm 
    return $seleccion
}

pausa() { read -p "$(echo -e "\n  ${GRIS}•••••••••\n  Presiona [ENTER] para continuar...${RESET}")"; }

# =============================================================
# DATA ACCESS LAYER (Verificación de herramientas)
# =============================================================

binario_existe() { command -v "$1" >/dev/null 2>&1; }

verificar_dependencias() {
    if ! binario_existe "git"; then
        ejecutar_con_spinner "Instalando Git" sudo apt-get update -qq && sudo apt-get install -y git
    fi

    if ! binario_existe "uv"; then
        echo -e "\n  ${AMARILLO}⚠ Astral-UV no está instalado en el sistema.${RESET}"
        read -p "  ❯ ¿Deseas instalarlo ahora para continuar? (s/n): " resp
        if [[ "$resp" =~ ^[sS]$ ]]; then
            ejecutar_con_spinner "Instalando Astral-UV" bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
            
            # Exportar temporalmente al PATH del script para poder usarlo inmediatamente
            export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
        else
            echo -e "  ${ROJO}✘ Se requiere UV para gestionar el entorno. Abortando.${RESET}"
            return 1
        fi
    fi
    return 0
}

# =============================================================
# BUSINESS LOGIC (Flujo del Repositorio)
# =============================================================

inicializar_repositorio() {
    verificar_dependencias || return

    echo -e "\n  ${MAGENTA}•${RESET} Configuración de Proyecto"
    read -p "  ❯ Ingresa la URL del repositorio Git: " repo_url

    if [ -z "$repo_url" ]; then
        echo -e "  ${ROJO}✘ La URL no puede estar vacía.${RESET}"
        return
    fi

    # Extraer el nombre de la carpeta (Ej: https://.../MiniKick.git -> MiniKick)
    local folder_name=$(basename "$repo_url" .git)

    if [ -d "$folder_name" ]; then
        echo -e "\n  ${ROJO}✘ Ya existe un directorio llamado '$folder_name' en esta ubicación.${RESET}"
        return
    fi

    echo "" # Espaciado
    ejecutar_con_spinner "Clonando repositorio ($folder_name)" git clone -q "$repo_url"

    if [ ! -d "$folder_name" ]; then
        echo -e "  ${ROJO}✘ Falló la clonación. Verifica el enlace o tus credenciales SSH/Git.${RESET}"
        return
    fi

    # Entrar a la carpeta
    cd "$folder_name" || return

    # Inicializar el entorno virtual
    ejecutar_con_spinner "Creando entorno virtual (uv venv)" uv venv > /dev/null

    # Gestión de dependencias
    if [ -f "requirements.txt" ]; then
        ejecutar_con_spinner "Instalando dependencias (uv pip)" uv pip install -r requirements.txt > /dev/null
    else
        echo -e "  ${AMARILLO}• requirements.txt no encontrado. Generando uno vacío...${RESET}"
        touch requirements.txt
    fi

    echo -e "\n  ${VERDE}✔ ¡Repositorio inicializado con éxito!${RESET}"
    echo -e "  ${GRIS}•••••••••${RESET}"
    echo -e "  ${CIAN}Para empezar a trabajar, ejecuta el siguiente comando:${RESET}"
    echo -e "  ${MAGENTA}cd $folder_name && source .venv/bin/activate${RESET}"
}

# =============================================================
# PUNTO DE ENTRADA (Main Controller)
# =============================================================

main() {
    while true; do
        clear
        echo -e "\n  ${BG_AZUL} Git & Python Bootstrapper ${RESET}\n"
        
        echo -e "  ${GRIS}Automatiza Git Clone, Entornos Virtuales y Dependencias.${RESET}\n"

        local OPCIONES_MENU=(
            "${VERDE}•${RESET} Clonar e Inicializar Repositorio (UV)"
            "${ROJO}•${RESET} Salir"
        )

        echo -e "  ${GRIS}Usa ↑/↓ y presiona Enter${RESET}\n"
        generar_menu_interactivo "${OPCIONES_MENU[@]}"
        local eleccion=$?

        case $eleccion in
            0) inicializar_repositorio; pausa ;;
            1) clear; exit 0 ;;
        esac
    done
}

main
