<img align="left" src="assets/installer/install_bg.png" width="180" />

<div align="left">
  <p><strong>MiniKick v1.2.8</strong></p>
  <p>El centro de control definitivo para streamers en Kick.com</p>
  <p>
    <strong>MiniKick</strong> es una aplicación de escritorio nativa diseñada para optimizar la interacción en Kick.com. Actualmente, el proyecto se centra en ofrecer un sistema de lectura de chat avanzado y personalizable, operando completamente fuera del navegador para reducir drásticamente el consumo de recursos de tu PC mientras transmites.
  </p>

  <br>

  <p>
    <a href="https://github.com/Andro2k/MiniKick/releases/latest">
      <img src="https://img.shields.io/github/v/release/Andro2k/MiniKick?style=for-the-badge&logo=kick&color=10BB10&labelColor=191919" alt="Latest Release"/>
    </a>
    <img src="https://img.shields.io/badge/Plataforma-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white&labelColor=191919" alt="Windows Support"/>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=191919" alt="Python Version"/>
    <img src="https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white&labelColor=191919" alt="PySide6"/>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Arquitectura-Clean_Code-FFb900?style=for-the-badge&logo=dataiku&logoColor=white&labelColor=191919" alt="Clean Architecture"/>
    <img src="https://img.shields.io/github/license/Andro2k/MiniKick?style=for-the-badge&color=blue&labelColor=191919" alt="License"/>
  </p>
  
  <a href="https://github.com/Andro2k/MiniKick/releases/latest">
    <img src="https://img.shields.io/badge/DESCARGAR_ÚLTIMA_VERSIÓN-10BB10?style=for-the-badge&logo=windows&logoColor=white" alt="Descargar Última Versión">
  </a>
</div>

<br clear="both" />

---

## Funcionalidades Principales

| Módulo | Función | Implementación |
| :--- | :--- | :--- |
| **Lectura de Chat** | TTS Híbrido | Narración capaz de alternar de forma transparente entre voces naturales con IA (`edge-tts`) y motores locales de Windows (`pyttsx3`). |
| **Interacción OBS** | Alertas Dinámicas | Posicionamiento aleatorio de video en el lienzo de OBS para evitar la obstrucción de elementos visuales clave durante el directo. |
| **Conectividad** | Tiempo Real | Integración directa e instantánea con los eventos de Kick mediante WebSockets. |
| **Sistema OTA** | Actualizaciones | Búsqueda, descarga e instalación de nuevas versiones en segundo plano. |

> [!NOTE]
> A partir de la versión 1.1.2, todas las configuraciones, tokens de sesión y la base de datos de alertas persisten de forma local y segura en tu directorio de Windows `AppData\Local\.Minikick`.

---

## Stack Tecnológico

| Categoría | Tecnologías | Propósito |
| :--- | :--- | :--- |
| **Interfaz Gráfica** | ![PySide6](https://img.shields.io/badge/PySide6-41CD52?style=flat-square&logo=qt&logoColor=white) | Desarrollo de la UI moderna (Dark/Mint) y gestión del ciclo de vida de los hilos de la aplicación. |
| **Voz y Audio** | ![Edge-TTS](https://img.shields.io/badge/Edge--TTS-0078D7?style=flat-square&logo=microsoftedge&logoColor=white) ![Pyttsx3](https://img.shields.io/badge/Pyttsx3-3776AB?style=flat-square&logo=python&logoColor=white) | Motores de síntesis de voz orquestados mediante un patrón de diseño unificado. |
| **Conexión** | ![WebSockets](https://img.shields.io/badge/WebSockets-010101?style=flat-square&logo=socketdotio&logoColor=white) ![Requests](https://img.shields.io/badge/Requests-00599C?style=flat-square) | Gestión de sockets en tiempo real y peticiones HTTP con bypass de seguridad (Cloudscraper) y tolerancia a fallos. |
| **Persistencia** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) | Almacenamiento local estructurado y ligero sin dependencias externas. |
| **Distribución** | ![PyInstaller](https://img.shields.io/badge/PyInstaller-191919?style=flat-square&logo=python&logoColor=white) | Compilación, gestión de rutas estáticas y empaquetado para despliegue nativo en sistemas Windows. |

---

## Arquitectura y Buenas Prácticas

El núcleo de MiniKick está diseñado para ser altamente escalable y resistente a cuelgues (Segfaults). El desarrollo se rige estrictamente por estas 5 reglas de arquitectura para garantizar la mantenibilidad:

1. **Dependency Inversion:** Uso intensivo de interfaces abstractas para desacoplar la lógica de negocio de las implementaciones concretas.
2. **Separation of Responsibilities (SoR):** Capas claramente delimitadas. Las Vistas son pasivas, los Workers manejan la carga pesada de red/archivos, y los Controladores orquestan de forma segura.
3. **High Cohesion:** Cada clase y módulo tiene un propósito único y bien definido en el sistema.
4. **DRY (Don't Repeat Yourself):** Centralización de lógica repetitiva priorizando siempre la legibilidad y limpieza del código.
5. **YAGNI (You Aren't Gonna Need It):** Abstracciones justificadas. Resolvemos problemas reales de forma simple sin caer en la sobre-ingeniería.

> [!IMPORTANT]
> Toda nueva contribución o *Pull Request* debe respetar obligatoriamente estos 5 principios de arquitectura en su código para ser aprobada.

---

## Instalación

### Entorno de Producción (Usuarios)

La forma más sencilla de usar MiniKick:

1. Navega a la sección de [Releases](https://github.com/Andro2k/MiniKick/releases/latest).
2. Descarga el archivo ejecutable (`MiniKick_Installer.exe`).
3. Sigue las instrucciones del asistente de instalación en tu máquina Windows.

### Entorno de Desarrollo (Contribuidores)

Si deseas explorar el código fuente o contribuir al proyecto en local:

```bash
# Clonar el repositorio
git clone https://github.com/Andro2k/MiniKick.git
cd MiniKick

# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate  # En Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python main.py
```

---
> [!TIP]
> Si descubres algún comportamiento inesperado o un crash del sistema, por favor revisa primero los Issues abiertos en el repositorio y la consola de desarrollador interna de la app antes de abrir un reporte nuevo.

## Licencia

Este proyecto se distribuye bajo la Licencia MIT. Consulte el archivo LICENSE para mas detalles.

<div align="center">
  <br>
  <sub>Desarrollado por <strong>TheAndro2K</strong></sub>
</div>

