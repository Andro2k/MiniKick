# backend/default_es.py

DEFAULT_DICTIONARY = {
    "settings": {
        "header": {
            "title": "Configuración General",
            "subtitle": "Ajustes globales del sistema, gestión de cuenta y actualizaciones."
        },
        "system": {
            "tray_title": "Ejecución en Segundo Plano",
            "tray_desc": "Minimizar a la bandeja del sistema en lugar de cerrar la aplicación por completo.",
            "lang_title": "Idioma de la Aplicación",
            "lang_desc": "Selecciona el idioma de la interfaz (requiere reiniciar).",
            "update_title": "Actualizaciones de Software",
            "update_desc": "Buscar e instalar nuevas versiones de MiniKick.",
            "btn_update": "Buscar actualizaciones"
        },
        "backup": {
            "title": "Respaldo de Configuración",
            "desc": "Exporta o importa tus alertas, voces y ajustes generales.",
            "btn_export": "Exportar",
            "btn_import": "Importar"
        },
        "account": {
            "title": "Desvincular Cuenta",
            "desc": "Cierra la sesión actual. Tendrás que volver a autorizar a MiniKick la próxima vez.",
            "btn_unlink": "Desvincular"
        },
        "dialogs": {
            "export_title": "Exportar Configuración",
            "import_title": "Importar Configuración"
        }
    },
    "spam": {
        "header": {
            "title": "Filtros Anti-Spam (Auto-Mod)",
            "subtitle": "Usa estos filtros para mantener tu chat amigable, divertido y libre de toxicidad."
        },
        "card": {
            "config_title": "Configuración de Penalización",
            "action": "Acción",
            "action_timeout": "Timeout al usuario",
            "action_delete": "Borrar mensaje (Delete)",
            "duration": "Duración (segundos)",
            "exclude": "Excluir rango (Inmunes)",
            "exclude_none": "Ninguno",
            "exclude_mod": "Moderadores y Broadcaster",
            "exclude_sub": "Suscriptores y VIPs",
            "max_amount": "Cantidad máxima permitida"
        },
        "filters": {
            "caps": {
                "title": "Protección de Mayúsculas",
                "desc": "Elimina mensajes con una cantidad excesiva de letras mayúsculas."
            },
            "link": {
                "title": "Protección de Links",
                "desc": "Elimina mensajes que contengan enlaces no autorizados."
            },
            "emote": {
                "title": "Protección de Emotes",
                "desc": "Elimina mensajes que abusen de la cantidad de emotes."
            },
            "paragraph": {
                "title": "Muros de Texto",
                "desc": "Bloquea mensajes excesivamente largos (Muchos caracteres)."
            },
            "symbol": {
                "title": "Protección de Símbolos",
                "desc": "Elimina mensajes con un uso excesivo de símbolos (Ej: @#!%)."
            }
        }
    },
    "command": {
        "header": {
            "title": "Triggers y Respuestas de Comandos",
            "subtitle": "Vincula comandos de chat o expresiones regulares a respuestas automatizadas del bot."
        },
        "table": {
            "title": "Comandos Vinculados",
            "search_placeholder": "Buscar comando vinculado...",
            "btn_new": "+ Nuevo Comando",
            "col_command": "Comando",
            "col_aliases": "Aliases / Regex",
            "col_response": "Respuesta",
            "col_actions": "Acciones",
            "regex_prefix": "Regex",
            "tooltip_edit": "Modificar configuración del comando",
            "tooltip_delete": "Eliminar comando permanentemente"
        }
    },
    "alerts": {
        "header": {
            "title": "Triggers & Alertas",
            "subtitle": "Vincula las recompensas de tu canal con elementos multimedia en pantalla."
        },
        "obs": {
            "title": "Fuente de Navegador OBS",
            "desc": "Copia este enlace y pégalo en tu software de transmisión (Resolución recomendada: 1920x1080).",
            "copied": "¡Enlace Copiado!"
        },
        "table": {
            "title": "Recompensas Vinculadas",
            "btn_new": "+ Nueva Alerta",
            "col_reward": "Recompensa de Kick",
            "col_file": "Archivo",
            "col_actions": "Acciones",
            "unknown_file": "Desconocido",
            "tooltip_play": "Probar en OBS",
            "tooltip_edit": "Modificar ajustes",
            "tooltip_delete": "Eliminar alerta"
        },
        "dialogs": {
            "visual": {
                "title": "Posicionador Visual (1920x1080)",
                "desc": "Arrastra tu alerta. Al soltarla, se mostrará una vista previa en OBS.",
                "btn_save": "Guardar y Cerrar"
            },
            "wizard": {
                "title_edit": "Editar Alerta",
                "title_new": "Nueva Alerta",
                "btn_cancel": "Cancelar",
                "btn_next": "Siguiente ➔",
                "btn_back": "🡠 Atrás",
                "btn_save": "Guardar Alerta",
                "file_dialog_title": "Multimedia",
                "file_dialog_filter": "Media (*.mp4 *.webm *.mp3 *.wav *.ogg *.gif *.png *.jpg);;Todos (*.*)",
                "step1": {
                    "title": "Recompensa y Archivo",
                    "desc": "Configura qué punto de canal activará esta alerta.",
                    "reward_selection": "Selección de Recompensa",
                    "loading": "Cargando recompensas...",
                    "tooltip_refresh": "Actualizar Recompensas de Kick",
                    "file_label": "Archivo Multimedia",
                    "file_placeholder": "Ej. tu_alerta.mp4 o sonido.mp3",
                    "btn_browse": "Explorar"
                },
                "step2": {
                    "title": "Ajustes de Pantalla",
                    "desc": "Define cómo y dónde se mostrará tu alerta en el lienzo.",
                    "volume": "Volumen de la alerta",
                    "random_pos": "Posición Aleatoria",
                    "btn_visual": "Posicionar en OBS",
                    "coord_x": "X:",
                    "coord_y": "Y:",
                    "scale": "Escala:"
                }
            }
        }
    },
    "log": {
        "header": {
            "title": "Registro de Desarrollador",
            "subtitle": "Monitorea eventos del sistema, depura errores y carga historiales usando el explorador."
        },
        "controls": {
            "search_placeholder": "Buscar en los registros...",
            "filter_all": "TODOS",
            "btn_folder": "Carpeta",
            "tooltip_folder": "Abrir ubicación en Windows",
            "btn_load": "Cargar Histórico",
            "btn_live": "Ver en Vivo",
            "btn_clear": "Limpiar",
            "btn_report": "Reportar"
        },
        "table": {
            "col_level": "Nivel",
            "col_time": "Marca de Tiempo",
            "col_message": "Mensaje"
        },
        "dialogs": {
            "select_history": "Seleccionar Histórico de Logs",
            "file_filter": "Archivos Log (*.log*);;Todos los archivos (*.*)"
        },
        "misc": {
            "historical": "HISTÓRICO"
        }
    },
    "chat": {
        "header": {
            "title": "Chat en Vivo",
            "subtitle": "Gestiona la moderación, lectura de voz interactiva (TTS) y eventos del canal en tiempo real."
        },
        "settings": {
            "tts_title": "Servicio de Voz (TTS)",
            "tts_desc": "Habilita la lectura automatizada de mensajes.",
            "name_title": "Leer Nombres",
            "name_desc": "Pronuncia el nombre del emisor antes del mensaje.",
            "provider_title": "Motor de Voz Premium",
            "provider_desc": "Alterna entre voces web de Edge o locales.",
            "cmd_title": "Requerir Comando",
            "cmd_desc": "Solo leer mensajes que inicien con un prefijo.",
            "vol_title": "Volumen General",
            "vol_desc": "Ajusta la intensidad del sintetizador de voz.",
            "prefix_title": "Prefijo del Comando",
            "prefix_desc": "Define el texto exacto que activará la lectura del bot.",
            "prefix_placeholder": "Ej. !tts"
        },
        "bots": {
            "title": "Usuarios Silenciados",
            "input_placeholder": "ej. botrix",
            "btn_add": "Agregar"
        },
        "display": {
            "title": "Historial de la Sala"
        }
    },
    "dashboard": {
        "header": {
            "title": "Dashboard",
            "subtitle": "Gestión de autenticación, conexión automática y estado general del sistema."
        },
        "banner": {
            "text": "<b>Actualización requerida:</b> Tu cuenta no tiene permisos para las nuevas funciones Anti-Spam.",
            "btn_update": "Actualizar Permisos"
        },
        "connection": {
            "autostart_title": "Conexión Automática",
            "autostart_desc": "Inicia el bot automáticamente.",
            "status_waiting": "Estado: Esperando conexión...",
            "status_auth": "Estado: Autenticando...",
            "status_connected": "Estado: Conectado y Escuchando",
            "status_error": "Error",
            "btn_connect": "Conectar a Kick",
            "btn_active": "Sistema Activo",
            "btn_retry": "Reintentar"
        },
        "stats": {
            "followers": "Seguidores",
            "room_id": "ID Sala (Chat)",
            "category": "Última Categoría",
            "affiliate": "Estado Afiliado",
            "vods": "VODs"
        }
    },
    "dialogs": {
        "confirm": {
            "btn_continue": "Continuar",
            "btn_cancel": "Cancelar"
        }
    },
    "main": {
        "dialogs": {
            "unlink_title": "Desvincular Cuenta",
            "unlink_desc": "¿Estás seguro de que deseas cerrar sesión? Tendrás que volver a autorizar a MiniKick la próxima vez que te conectes.",
            "close_title": "Cerrar MiniKick",
            "close_desc": "¿Estás seguro de que deseas salir de la aplicación? El bot dejará de escuchar el chat."
        }
    }
}