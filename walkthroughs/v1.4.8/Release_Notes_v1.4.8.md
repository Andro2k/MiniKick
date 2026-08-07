# Release Notes - MiniKick Version v1.4.8

> [!NOTE]
> MiniKick v1.4.8 introduce una importante evolución de arquitectura enfocada en **Carga Diferida de Vistas (Lazy Loading)**, **Interfaces Protocol (DIP)** y una **Suite de Pruebas Automatizadas (pytest)** que reducen el tiempo de inicio, el consumo de RAM y garantizan la estabilidad contra fallos.

---

## Novedades Destacadas v1.4.8

> [!IMPORTANT]
> **1. Carga Diferida de Vistas (*Lazy Loading*) & Velocidad Extrema**
> - **Instanciación Bajo Demanda:** `MainWindowCore` únicamente construye la vista del `DashboardView` al iniciar la aplicación. Las 10 vistas secundarias (`Chat`, `Music`, `Triggers`, `Comandos`, `Widgets`, `Spam`, `Timers`, `Settings`, `Developer`, `Network Status`) se crean en memoria **únicamente cuando haces clic por primera vez en su pestaña**.
> - **Reducción de Consumo de RAM y CPU:** Al no tener que crear 11 tablas, sliders y formularios al iniciar, la aplicación arranca en una fracción del tiempo anterior.
> - **Carga Transparente:** La primera vez que visitas una sección se crea de forma imperceptible y se mantiene guardada en caché para las siguientes visitas.

> [!IMPORTANT]
> **2. Suite de Pruebas Automatizadas (`pytest`) & Calidad de Código**
> - **Inspectores Automatizados:** Implementación de 9 pruebas unitarias ejecutadas en **1.65 segundos** que evalúan automáticamente la lógica del bot.
> - **Pruebas Incluidas:**
>   1. `test_spam_service.py`: Verifica que la sanitización no castigue emoticones legítimos de Kick y sancione correctamente el spam de símbolos o textos largos.
>   2. `test_storage.py`: Asegura que el guardado/lectura en la base de datos SQLite preserve configuraciones y booleanos.
>   3. `test_command_parser.py`: Garantiza la validación adecuada de prefijos de comandos (`!tts`, `!sr`, etc.).

> [!IMPORTANT]
> **3. Protocolos de Interfaz (`typing.Protocol`) & Desacoplamiento (DIP)**
> - Definición de contratos formales `IMusicProvider`, `IStorageRepository` y `IChatService` en `backend/interfaces/`.
> - Permite cambiar o probar componentes del backend sin acoplar la interfaz gráfica a clases concretas.

---

## Comparativa de Eficiencia y Rendimiento (Big-O)

| Módulo / Operación | Comportamiento Anterior | Optimización v1.4.8 | Impacto en Rendimiento |
|---|---|---|---|
| Carga de Vistas (UI) | Instanciación simultánea de 11 vistas $\mathcal{O}(V)$ | Carga diferida perezosa (*Lazy Loading*) | Menor huella de RAM y arranque ultrarrápido |
| Verificación de Código | Pruebas manuales lentas | Suite `pytest` con 9 tests automatizados | Verificación automatizada en 1.65s |
| Arquitectura de Clases | Acoplamiento a clases concretas | Interfaces Protocol (`typing.Protocol`) | Alta modularidad y sustitución segura (DIP) |

---

> [!TIP]
> Puedes ejecutar la suite de pruebas unitarias en cualquier momento desde la terminal mediante el comando:
> `uv run pytest tests/`
