<div align="center">
  <img src="assets/installer/install_small.png" height="150" alt="MiniKick Logo" />
  <h1>MiniKick</h1>
  <p><strong>El centro de control definitivo para streamers en Kick.com</strong></p>

  <p>
    <a href="https://github.com/Andro2k/MiniKick/releases/latest">
      <img src="https://img.shields.io/github/v/release/Andro2k/MiniKick?style=for-the-badge&logo=kick&color=10BB10&labelColor=191919" alt="Latest Release" height="28"/>
    </a>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=191919" alt="Python Version" height="28"/>
    <img src="https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white&labelColor=191919" alt="PySide6" height="28"/>
    <img src="https://img.shields.io/github/license/Andro2k/MiniKick?style=for-the-badge&color=blue&labelColor=191919" alt="License" height="28"/>
  </p>
  
  <br>
  
  <a href="https://github.com/Andro2k/MiniKick/releases/latest">
    <img src="https://img.shields.io/badge/DESCARGAR_ÚLTIMA_VERSIÓN-10BB10?style=for-the-badge&logo=windows&logoColor=white" alt="Descargar Última Versión">
  </a>
</div>

---

## Descripción General

**KickMonitor** es una aplicación de escritorio nativa orientada a resolver la fragmentación de herramientas en el ecosistema de Kick. Desarrollada bajo una arquitectura eficiente en Python y PyQt6, esta herramienta consolida el monitoreo en tiempo real, automatización de chat, motor de alertas y gestión de overlays en una única interfaz de bajo consumo de recursos.
Diseñada tanto para optimizar la memoria RAM (al eliminar la necesidad de múltiples pestañas de navegador) como para ofrecer latencia cero mediante servidores web locales integrados.

---

## Características Destacadas

### Motor de Overlays Locales (Zero-Latency)
MiniKick incluye servidores web ligeros integrados que transmiten directamente a las fuentes de navegador de OBS Studio, operando enteramente en tu red local (localhost).
* **Chat Pro Overlay (Puerto 6001):** Renderizado de chat en tiempo real con soporte nativo para Emotes de Kick de alta resolución. Altamente personalizable: estilos de burbuja, transparente, neón y flujo horizontal, incluyendo animaciones de entrada y salida fluidas.
* **Alertas Visuales (Puerto 6002):** Sistema de notificaciones en pantalla para Seguidores, Suscripciones y Hosts/Raids. Funciona con independencia del servidor de chat para garantizar cero latencia.
* **Sistema de Triggers:** Capacidad para disparar elementos multimedia (GIFs, videos, efectos de sonido) en OBS mediante el uso de comandos específicos o recompensas en el chat.

### Automatización y Moderación de Chat
* **TTS con IA (Edge-TTS):** Sistema de *Text-to-Speech* integrado de alta fidelidad, permitiendo narración del chat en vivo con voces naturales y acentos configurables.
* **Sistema de Comandos Dinámicos:** Creación de comandos personalizados con soporte para múltiples alias (hasta 5 por comando). Incluye sistema de cobro mediante moneda virtual.
* **Variables de Entorno:** Integración de respuestas dinámicas utilizando variables como `{followers}`, `{time}`, `{date}`, y funciones aleatorias (`{8ball}`, `{coin}`, `{dice}`).
* **Filtros de Seguridad Inteligentes:** Interfaz basada en *Dynamic Tag Pills* para la gestión ágil de usuarios silenciados y bots ignorados. Implementa autocompletado y un limitador inteligente de 500 caracteres para evadir bloqueos por API spam.

### Economía y Retención de Audiencia
* **Lealtad Automatizada:** Distribución de puntos virtuales a los espectadores basada en métricas de participación (mensajes enviados y tiempo de visualización).
* **Sincronización Bidireccional:** Las acciones punitivas (silenciar, banear) ejecutadas desde el panel de base de datos se propagan instantáneamente al motor TTS y al renderizado del overlay en OBS.

---

## Guía de Instalación

### Entorno de Producción (Usuarios Finales)

La forma más rápida y estable de utilizar MiniKick es mediante el instalador precompilado para Windows.

1. Navega a la sección de **[Releases](https://github.com/Andro2k/MiniKick/releases)** del repositorio.
2. Descarga el ejecutable más reciente (`MiniKick_Setup_vX.X.X.exe`).
3. Ejecuta el instalador. Este proceso creará los accesos directos necesarios en tu sistema.
4. **Mantenimiento Autónomo:** La aplicación cuenta con un módulo de actualización OTA (Over-The-Air) silencioso, garantizando acceso a nuevos parches de forma automática.

### Entorno de Desarrollo (Código Fuente)

Para compilar, auditar o contribuir al proyecto. Requiere **Python 3.12+** y **Git**.
```bash
# 1. Clonar el repositorio localmente
git clone [https://github.com/Andro2k/MiniKick.git](https://github.com/Andro2k/MiniKick.git)
cd MiniKick

# 2. Inicializar entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 3. Instalar dependencias del proyecto
pip install -r requirements.txt

# 4. Iniciar la aplicación
python main.py
```

---

## Configuración Inicial

La integración con tus plataformas de streaming está centralizada en el menú de **Ajustes**:

* **Autenticación Kick OAuth:** El proceso es *passwordless*. Haz clic en "Conectar Bot" en el Dashboard para abrir un flujo seguro de autorización en tu navegador predeterminado.
* **Integración OBS Studio:** Añade nuevas "Fuentes de Navegador" en tu escena de OBS apuntando a las siguientes rutas locales (utiliza el botón "Copiar URL" en la interfaz para mayor precisión):
  * `http://localhost:6001/chat`
  * `http://localhost:6002/alerts`
* **Integración Spotify (Opcional):** Accede a *Spotify for Developers*, genera tus credenciales (`Client ID` y `Client Secret`) e introdúcelas en la aplicación para activar el widget de "Reproduciendo ahora" en tu stream.

---

## Stack Tecnológico

El proyecto está construido sobre tecnologías robustas para garantizar estabilidad en sesiones prolongadas de streaming:

* **Core Backend:** Python 3.12+, `asyncio` (Programación asíncrona)
* **Interfaz Gráfica:** PyQt6 (Implementando ventanas *Frameless*, arrastre nativo y *QPropertyAnimation*)
* **Conectividad:** `aiohttp`, webSockets (`Pusher`), `cloudscraper`
* **Persistencia de Datos:** SQLite (Implementa `QMutexLocker` para *thread-safety* y `VACUUM` para auto-mantenimiento)
* **Procesamiento de Audio:** `edge-tts`, `pyttsx3`, `pygame`
* **Despliegue y Distribución:** PyInstaller (Compilación binaria) + Inno Setup 6 (Empaquetado)

---

## Licencia

MiniKick es software de código abierto. Distribuido bajo los términos de la **Licencia MIT**. Consulte el archivo `LICENSE` en la raíz del repositorio para obtener información detallada sobre permisos y limitaciones. 

Las contribuciones mediante *Pull Requests* son bienvenidas.

<div align="center">
  <br>
  <sub>Desarrollado y mantenido por <strong>TheAndro2K</strong></sub>
</div>
