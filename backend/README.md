# Backend Core Architectural Contract — MiniKick

## 1. Package Overview & Purpose

The `backend` package encapsulates all headless business logic, data persistence, multi-platform streaming protocols, background asynchronous workers, event processing pipelines, and system automation services for MiniKick.

It strictly adheres to **Separation of Responsibilities (SoR)** and **Dependency Inversion (IoC)**:
- Business calculations, stream ingestion, and persistence logic operate completely decoupled from presentation components.
- Controllers expose discrete interfaces and Qt signals to communicate with the `frontend` without leaking internal storage or database state.
- All dependencies are assembled and managed via the central `AppContainerCore` dependency injection root.

---

## 2. Architectural Role & Boundary Invariants

MiniKick follows a layered architectural model governed by automated AST boundary rules enforced by `resources/tools/project_architecture_boundary_auditor.py` and `resources/tools/project_file_placement_auditor.py`:

```
┌────────────────────────────────────────────────────────┐
│                      frontend/                         │
│         (Views, Widgets, Dialogs, Theme Tokens)        │
└───────────────────────────▲────────────────────────────┘
                            │ (Qt Signals / DTOs)
┌───────────────────────────┴────────────────────────────┐
│                 backend/controllers/                   │
│        (BaseController, QObject signal mediation)      │
└─────────────▲────────────────────────────▲─────────────┘
              │                            │
┌─────────────┴───────────────┐ ┌──────────┴─────────────┐
│      backend/workers/       │ │    backend/services/   │
│   (QThread Task Workers)    │ │ (Domain Logic Services)│
└─────────────▲───────────────┘ └──────────▲─────────────┘
              │                            │
┌─────────────┴───────────────┐ ┌──────────┴─────────────┐
│     backend/providers/      │ │    backend/handlers/   │
│   (External API Adapters)   │ │  (Pipeline Interceptors)│
└─────────────▲───────────────┘ └──────────▲─────────────┘
              │                            │
┌─────────────┴────────────────────────────┴─────────────┐
│                 backend/database/                      │
│     (SQLite3 WAL, Encrypted Repositories, Migrations)  │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│            backend/core/ & backend/utils/              │
│    (AppContainerCore, Logging, Fast JSON, Latency)     │
└────────────────────────────────────────────────────────┘
```

### Strict System Invariants:
1. **Persistence Purity (`SOR_DB_QT`)**:
   - `backend/database/` must be 100% pure Python/SQLite.
   - It is strictly forbidden to import PySide6 / Qt packages into any database storage module.
2. **Presentation Decoupling (`SOR_CORE_WIDGETS` & `INVERTED_DEPENDENCY`)**:
   - Modules in `backend/services/`, `backend/database/`, and `backend/workers/` must never import `QtWidgets` or any module from `frontend/`.
   - Communication to the UI occurs exclusively via immutable Data Transfer Objects (`ChatMessageDTO`), domain events, and Qt signals.
3. **Non-Blocking UI Execution (`NO_BLOCKING_UI_SLEEP`)**:
   - Neither `time.sleep` nor blocking synchronous network operations may be executed in `backend/controllers/` or the main Qt event loop.
   - Background tasks must use `backend/workers/` with `cooperative_sleep` to maintain responsive cancellation semantics.
4. **Fast JSON Policy (`BANNED_JSON_IMPORT`)**:
   - Direct `import json` is forbidden in production modules.
   - Code must use accelerated serializers: `from backend.utils import fast_loads, fast_dumps` (`msgspec` with CPython/Rust acceleration and transparent fallback).
5. **Directory Purity (`FOLDER_PURITY_RULES`)**:
   - `backend/workers/` only accepts `*_worker.py`.
   - `backend/controllers/` only accepts `*_controller.py`.
   - `backend/database/` only accepts `*_storage.py`, `database_manager.py`, and `migrations.py`.
   - All backend utility functions must reside under `backend/utils/`.

---

## 3. Subpackage Directory Index

| Subpackage | Responsibility | Canonical Pattern | Primary Exports |
| :--- | :--- | :--- | :--- |
| [`config/`](./config) | Application versioning, TOML provider, credentials & endpoint constants | `*config*.py` | `APP_VERSION`, `TomlConfigProvider`, `KICK_PUSHER` |
| [`core/`](./core) | Dependency injection container & hardened logging engine | `*core*.py` | `AppContainerCore`, `setup_application_logging` |
| [`controllers/`](./controllers) | Presentation orchestration and Qt signal bridging | `*_controller.py` | `BaseController`, `ChatController`, `WidgetsController` |
| [`database/`](./database) | SQLite WAL persistence, encryption, migrations & cache | `*_storage.py` | `DatabaseManager`, `EncryptedTokenStorage`, `SQLite*Storage` |
| [`handlers/`](./handlers) | Stream interceptors, command dispatch & structured log emission | `*_handler.py` | `ChatFilterHandler`, `TTSVoiceHandler`, `LogEmitter` |
| [`interfaces/`](./interfaces) | Abstract contracts, protocols, and interface definitions | `i_*.py` | `IConfigProvider`, `ITTSProvider`, `IMusicProvider`, `TokenStorage` |
| [`providers/`](./providers) | External platform adapters (Kick, Twitch, YouTube, TikTok, Piper) | Multi-provider | `KickWebSocketManager`, `TwitchSocketManager`, `YouTubeMusicProvider` |
| [`services/`](./services) | Pure domain logic (Alerts, Auth, Chat, Overlay, Schedule, System) | Multi-domain | `AlertService`, `ChatService`, `OverlayServerManager`, `ScheduleService` |
| [`utils/`](./utils) | High-performance utilities, parsing, latency & execution helpers | Modular | `fast_loads`, `fast_dumps`, `LatencyMonitor`, `cooperative_sleep` |
| [`workers/`](./workers) | Multithreaded background tasks running in isolated `QThread` | `*_worker.py` | `KickChatWorker`, `TwitchChatWorker`, `MusicWorker`, `ScheduleWorker` |

---

## 4. Exported Interfaces & Public Contracts

### Central Container (`backend.core.AppContainerCore`)
Assembles and coordinates the entire backend lifecycle:
```python
class AppContainerCore:
    def __init__(self, db_manager: DatabaseManager, i18n: TranslationService, config_provider: IConfigProvider): ...
    def get_music_provider(self) -> YouTubeMusicProvider: ...
    def shutdown(self) -> None: ...
```

### Configuration Provider Protocol (`backend.interfaces.IConfigProvider`)
Thread-safe, atomic configuration persistence contract:
```python
class IConfigProvider(ABC):
    def get(self, key: str, default: ConfigValue = None) -> ConfigValue: ...
    def set(self, key: str, value: ConfigValue) -> None: ...
    def delete(self, key: str) -> None: ...
    def as_dict(self) -> dict[str, ConfigValue]: ...
```

### Token Storage Protocol (`backend.interfaces.TokenStorage`)
Secure OAuth token persistence contract with AES-GCM cipher encryption:
```python
class TokenStorage(ABC):
    def load_token(self) -> dict | None: ...
    def save_token(self, token_data: dict) -> None: ...
    def clear_token(self) -> None: ...
```

### TTS Synthesis Provider (`backend.interfaces.ITTSProvider`)
Contract for real-time speech synthesis adapters:
```python
class ITTSProvider(ABC):
    def synthesize(self, text: str, voice: str, speed: float = 1.0) -> bytes: ...
    def get_available_voices(self) -> list[str]: ...
```

---

## 5. Side Effects & External Boundaries

1. **Local Filesystem & SQLite Persistence**:
   - **Database**: `%LOCALAPPDATA%/.Minikick/minikick.db` operates in SQLite `WAL` mode with `PRAGMA busy_timeout=30000` and `AutoCloseConnection` context lifecycle.
   - **Configuration**: `%LOCALAPPDATA%/.Minikick/config.toml` written using atomic temp-file replace (`TomlConfigProvider`) with corrupt-file quarantine.
   - **Logging**: Rotating daily log files `%LOCALAPPDATA%/.Minikick/logs/minikick.log` managed by `AutoFlushTimedRotatingFileHandler`.
2. **Network Communications**:
   - **Kick**: Pusher WebSocket protocol 7 (`wss://ws-{cluster}.pusher.com`) with automated RTT heartbeat probing and backoff reconnection (`KickWebSocketManager`).
   - **Twitch**: IRC WebSocket (`wss://irc-ws.chat.twitch.tv:443`) and Helix REST API / EventSub webhooks (`TwitchSocketManager`, `TwitchEventSubProvider`).
   - **YouTube & TikTok**: Asynchronous livestream chat ingestion via `YouTubeChatProvider` and `TikTokChatProvider`.
   - **Local Overlay Server**: Asynchronous HTTP and WebSocket server running locally on port `8090` (`backend/services/overlay/`) serving live OBS assets and reactive state updates.
3. **Audio & Media**:
   - On-demand audio streaming and metadata scraping via `yt-dlp` and `PySide6.QtMultimedia.QMediaPlayer`.
   - Local CPU neural speech synthesis via `Piper TTS` (ONNX models in memory).

---

## 6. Testing & Quality Verification

Run the targeted test suites and architectural linters from the repository root:

```bash
# 1. Run all backend automated tests
pytest resources/tests/ -q

# 2. Run critical network, database resiliency, and message path benchmarks
pytest resources/tests/test_network_and_db_resiliency.py resources/tests/test_message_path_performance.py resources/tests/test_latency_monitor.py -q

# 3. Verify architectural boundaries (SoR, Qt separation, and forbidden imports)
python resources/tools/project_architecture_boundary_auditor.py --check

# 4. Verify directory purity and canonical file placement
python resources/tools/project_file_placement_auditor.py --check

# 5. Full quality suite health check
python resources/tools/project_quality_suite.py --quick
```
