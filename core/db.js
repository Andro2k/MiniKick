const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const os = require('os');

class DBManager {
    constructor() {
        // Buscar la ruta segura de AppData en Windows (o equivalente en Linux/Mac)
        const appData = process.env.LOCALAPPDATA || path.join(os.homedir(), '.local', 'share');
        this.appDir = path.join(appData, 'MiniKick');
        
        // Crear la carpeta MiniKick si no existe
        if (!fs.existsSync(this.appDir)) {
            fs.mkdirSync(this.appDir, { recursive: true });
        }

        this.dbPath = path.join(this.appDir, 'database.sqlite');
        this.db = new Database(this.dbPath);
        
        this.initDB();
    }

    initDB() {
        // 1. Tabla de Configuración (Tokens, Nombres, IDs)
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        `);

        // 2. Tabla de Comandos (Para los videos/sustos)
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS comandos (
                comando TEXT PRIMARY KEY,
                archivo_video TEXT,
                volumen INTEGER DEFAULT 100,
                activo BOOLEAN DEFAULT 1
            )
        `);

        // 3. Tabla Blacklist (Para silenciar trolls del TTS)
        this.db.exec(`
            CREATE TABLE IF NOT EXISTS tts_blacklist (
                username TEXT PRIMARY KEY
            )
        `);
    }

    // --- MÉTODOS PARA LA CONFIGURACIÓN ---
    getConfig(key, defaultValue = null) {
        const stmt = this.db.prepare('SELECT value FROM config WHERE key = ?');
        const row = stmt.get(key);
        return row ? row.value : defaultValue;
    }

    setConfig(key, value) {
        const stmt = this.db.prepare(`
            INSERT INTO config (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        `);
        stmt.run(key, String(value));
    }
}

// Exportamos una única instancia para usarla en toda la app
module.exports = new DBManager();