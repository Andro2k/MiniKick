<div align="center">

# MiniKick

**El centro de control definitivo, modular y ligero para streamers en Kick.com**

[![Latest Release](https://img.shields.io/github/v/release/Andro2k/MiniKick?style=for-the-badge&logo=kick&color=10BB10&labelColor=191919)](https://github.com/Andro2k/MiniKick/releases/latest)
[![Windows Support](https://img.shields.io/badge/Plataforma-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white&labelColor=191919)](https://github.com/Andro2k/MiniKick/releases/latest)
[![Python Version](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=191919)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white&labelColor=191919)](https://doc.qt.io/qtforpython-6/)
[![Clean Architecture](https://img.shields.io/badge/Arquitectura-Clean_Code-FFb900?style=for-the-badge&logo=dataiku&logoColor=white&labelColor=191919)](#arquitectura-e-ingeniería)
[![License](https://img.shields.io/github/license/Andro2k/MiniKick?style=for-the-badge&color=blue&labelColor=191919)](LICENSE)

<br>

**MiniKick** es una aplicación de escritorio nativa diseñada para orquestar la interacción en directo sin sacrificar los FPS de tu transmisión. Operando por completo fuera del navegador, reduce drásticamente el consumo de memoria RAM y ciclos de CPU, integrando lectura de chat inteligente por voz (TTS), moderación automatizada y control multimedia en tiempo real.

<br>

[![Descargar Última Versión](https://img.shields.io/badge/DESCARGAR_ÚLTIMA_VERSIÓN-10BB10?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Andro2k/MiniKick/releases/latest)

</div>

---

## ⚡ Funcionalidades Principales

| Módulo | Función | Descripción |
| :--- | :--- | :--- |
| **Motor de Chat** | Pipeline Unidireccional | Procesamiento de mensajes mediante tubería de interceptores puros (*AutoMod ➔ Comandos ➔ UI ➔ TTS*) con cortocircuito de ejecución. |
| **Voz Híbrida (TTS)** | Narración Inteligente | Alternancia dinámica entre voces neurales en la nube (`edge-tts`) y SAPI5 local (`pyttsx3`) con limpieza matemática de enlaces y emotes. |
| **Integración Spotify** | Control de Puntos | Canje de canciones (`!sr`), saltos (`!skip`) y consulta de pista (`!song`) con resolución automática de alias y *cooldowns* por base de datos. |
| **Conectividad Edge** | WebSockets $O(1)$ | Captura instantánea de eventos de Kick.com con tablas de despacho en memoria RAM y supresión de parseo JSON redundante. |
| **AutoMod Integrado** | Filtros Anti-Spam | Protección activa contra exceso de mayúsculas, símbolos, párrafos masivos y enlaces con sanciones directas a la API de Kick. |
| **Sistema OTA** | Actualizaciones | Verificación, descarga e instalación de parches en segundo plano de forma totalmente transparente e ininterrumpida. |

> [!NOTE]
> Todas las preferencias de usuario, bases de datos locales (`SQLite`) y tokens cifrados de sesión persisten de forma aislada en el directorio nativo del sistema: `AppData\Local\.Minikick`.

---

## 🧠 Arquitectura e Ingeniería

MiniKick no es un script convencional; está construido bajo estándares estrictos de **Ingeniería de Software a Escala**. Para garantizar latencias inferiores a un milisegundo y cero fugas de memoria durante streams de más de 12 horas, el código respeta los siguientes principios:

1. **Eficiencia Algorítmica Big-O ($O(1)$):** Erradicación de bucles anidados en rutas críticas (*Hot-Paths*). Las validaciones de usuarios ignorados utilizan tablas hash `Set()` nativas, y los analizadores de texto reemplazan condicionales masivas por **Tablas de Despacho estáticas**.
2. **Patrón Pipeline (Chain of Responsibility):** Desacoplamiento absoluto del flujo del chat. Cada mensaje entrante es un objeto inmutable (`DTO`) que atraviesa transformaciones puras e independientes.
3. **Gestión Segura de Memoria C++/Qt:** Prevención de hilos huérfanos (*Memory Leaks*). Todos los procesos asíncronos aplican liberación determinista del Kernel mediante el patrón `.finished.connect(deleteLater)`.
4. **Inversión de Dependencias y SoR:** Separación estricta entre capas de Red (*Providers*), Lógica de Dominio (*Services*) y Presentación Pasiva (*Views/PySide6*).

> [!IMPORTANT]
> **Normativa de Contribución:** Cualquier *Pull Request* propuesta para el proyecto debe pasar auditoría de complejidad temporal y respetar el desacoplamiento de capas para ser fusionada en la rama `main`.

---

## 🛠️ Stack Tecnológico

* **Core & GUI:** Python 3.10+ | PySide6 (Qt for Python) | Qt Style Sheets (QSS contextual)
* **Networking:** WebSockets | Requests | Cloudscraper (CF Bypass)
* **Audio Engine:** Edge-TTS (Edge Cloud) | Pyttsx3 (Native OS)
* **Database & Storage:** SQLite3 | JSON File Storage
* **Build & Deployment:** PyInstaller | Inno Setup

---

## 🚀 Guía de Despliegue

### Entorno de Producción (Creadores)

1. Dirígete a la página de [Releases Oficiales](https://github.com/Andro2k/MiniKick/releases/latest).
2. Descarga el instalador ejecutable (`MiniKick_Installer.exe`).
3. Ejecuta el asistente nativo en tu ordenador Windows 10/11.

### Entorno de Desarrollo (Ingenieros)

Configuración del entorno local para experimentación y desarrollo:

```bash
# 1. Clonar el repositorio
git clone [https://github.com/Andro2k/MiniKick.git](https://github.com/Andro2k/MiniKick.git)
cd MiniKick

# 2. Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

# 3. Instalar dependencias de desarrollo
pip install -r requirements.txt

# 4. Iniciar aplicación con recolector de logs
python main.py

```
> [!TIP]
> Si experimentas algún comportamiento inesperado de red o cierre abrupto, revisa primero la pestaña interna **Developer ➔ Logs** de la aplicación antes de abrir un *Issue* adjuntando el trazo de error.

<div align="center">
<sub>Diseñado y desarrollado con estándares de arquitectura por <a href="https://github.com/Andro2k"><strong>TheAndro2K</strong></a></sub>
<sub>Distribuido bajo la Licencia MIT</sub>
</div>
