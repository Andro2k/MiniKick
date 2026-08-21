# Release Notes - MiniKick Version 1.5.3

**21 de Agosto, 2026**

## Estabilidad Estructural, Diagnósticos Avanzados, Búsqueda Unificada de Categorías y Optimización Multiplataforma

> [!NOTE]
> MiniKick v1.5.3 introduce un blindaje integral del sistema con captura avanzada de diagnósticos ante fallos nativos, un nuevo componente interactivo de búsqueda de categorías para Kick y Twitch, arquitectura de persistencia optimizada con migración automática, sincronización en tiempo real de horarios programados y total independencia operativa entre plataformas.

---

### Novedades (8)

- **Captura Nativa de Diagnósticos y Fallos de Memoria:** Integración del controlador `faulthandler` a nivel de proceso para registrar trazas completas de todos los hilos ante violaciones de acceso o cierres inesperados en librerías nativas.
- **Nuevo Selector y Buscador Unificado de Categorías:** Componente `CategorySearchComboBox` con búsqueda en vivo, badges visuales por plataforma (`[KICK]` y `[TWITCH]`), debounce de 300 ms, navegación por teclado y menú flotante de alta visibilidad.
- **Auditoría Exhaustiva de Acciones de Usuario:** Instrumentación estandarizada en todos los controladores para registrar de forma instantánea operaciones de configuración, guardado, navegación y cambios de estado con la etiqueta `[User Action]`.
- **Auto-Flush Inmediato de Registros Críticos:** Vaciado forzado a disco en el sistema de logs para advertencias, errores y fallos críticos, evitando la pérdida de información en buffers de memoria.
- **Captura Global de Excepciones en Hilos Secundarios:** Registro automático de errores no controlados en tareas en segundo plano mediante `threading.excepthook`.
- **Soporte para Nivel Crítico en Visor de Logs:** Incorporación del nivel `CRITICAL` con filtrado dedicado por columna y visualización destacada dentro de la interfaz de registros.
- **Migración Automática de Esquemas SQLite:** Detección e incorporación automática de nuevas columnas e índices en bases de datos preexistentes sin requerir reinstalación ni pérdida de datos.
- **Componentes Numéricos No-Wheel:** Creación de `NoWheelSpinBox` para evitar alteraciones accidentales de parámetros mediante el desplazamiento de la rueda del ratón.

---

### Mejoras (10)

- **Optimización de Paso de Señales en PySide6:** Estandarización de señales y slots con tipado `object` en todos los workers, controladores y componentes, eliminando copias profundas innecesarias y avisos de enlace interno.
- **Supresión Nativa de Volcados de FFmpeg:** Silenciamiento de registros verbosos de inspección de medios en terminal mediante enlace con la biblioteca nativa `avutil`.
- **Desacoplamiento Arquitectónico Estricto en Frontend:** Eliminación completa de importaciones directas de módulos del backend en componentes de interfaz mediante inyección de dependencias.
- **Alineación de Cuadrícula en Filtros Anti-Spam:** Reorganización de las tarjetas de configuración mediante `QGridLayout` para una distribución simétrica y alineación uniforme entre parámetros.
- **Ajuste Responsivo de Selectores Desplegables:** Calibración de anchos mínimos en ComboBoxes para asegurar la visualización íntegra de opciones de idioma y configuraciones de sistema.
- **Optimización de la Barra Lateral Colapsada:** Ocultación automática de barras de desplazamiento y ajuste de padding para un centrado exacto de los íconos de navegación.
- **Refactorización y Limpieza Estructural de MainWindowCore y AppContainer:** Eliminación de servicios obsoletos, alias redundantes y organización en bloques modulares cohesivos.
- **Compatibilidad Multiplataforma para Linux:** Blindaje de llamadas COM en el motor de voz local y optimización de cabeceras de cliente para entornos basados en Ubuntu/Debian.
- **Sincronización Automática de Voces TTS:** Restauración inmediata de la voz configurada correspondiente al alternar entre el motor local y el motor online de Edge TTS.
- **Limpieza de Esquema de Horarios:** Eliminación de la columna obsoleta `days` en la tabla de horarios de stream para optimizar el almacenamiento.

---

### Correcciones (7)

- **Sincronización en Tiempo Real de Horarios Programados:** Actualización inmediata de la tabla en la interfaz al completarse la ejecución automática de un horario, reflejando su estado desactivado en el switch.
- **Reutilización y Reactivación de Horarios Programados:** Reseteo automático de la marca de última fecha ejecutada al modificar o reactivar un horario existente, permitiendo su reprogramación y ejecución continua.
- **Independencia en Conexiones de Kick y Twitch:** Aislamiento total de los ciclos de vida de workers, evitando que la autenticación de Kick finalice la conexión activa de Twitch.
- **Aislamiento en Desvinculación de Cuentas:** Modificación del flujo de desvinculación de Kick para mantener operativas las sesiones y conexiones de Twitch sin reinicios forzados.
- **Notificaciones OAuth de Twitch Condicionadas:** Eliminación de avisos emergentes redundantes de inicio de sesión en navegador cuando las credenciales de Twitch ya se encuentran autenticadas.
- **Validación y Fallback de Voces Neurales Online:** Verificación estricta de nombres de voz en el proveedor web para evitar caídas del sintetizador ante identificadores no válidos.
- **Preservación de Espaciado en SpinBoxes Deshabilitados:** Corrección de reglas de estilo para mantener el espaciado interno y legibilidad de valores numéricos inactivos.
