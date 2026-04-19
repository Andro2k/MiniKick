require('dotenv').config();
const express = require('express');
const axios = require('axios');
const path = require('path');
const sound = require('sound-play');
const fs = require('fs');
const crypto = require('crypto');
const PusherLib = require('pusher-js');
const Pusher = PusherLib.default || PusherLib; // Fuerza a Node a encontrar la clase correcta
const readline = require('readline'); // Para leer tu consola

// Importamos nuestra base de datos local
const db = require('./db');

const app = express();
app.use(express.json());

const TTS_OUTPUT_DIR = path.join(__dirname, '..', 'media', 'audios');
let codeVerifier = '';

// ==========================================
// 1. FLUJO DE AUTENTICACIÓN (OAUTH 2.1)
// ==========================================

app.get('/auth/login', (req, res) => {
    codeVerifier = crypto.randomBytes(32).toString('base64url');
    const codeChallenge = crypto.createHash('sha256').update(codeVerifier).digest('base64url');

    const authUrl = new URL('https://id.kick.com/oauth/authorize');
    authUrl.searchParams.append('response_type', 'code');
    authUrl.searchParams.append('client_id', process.env.KICK_CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', process.env.KICK_REDIRECT_URI);
    authUrl.searchParams.append('scope', 'user:read chat:write'); 
    authUrl.searchParams.append('code_challenge', codeChallenge);
    authUrl.searchParams.append('code_challenge_method', 'S256');
    authUrl.searchParams.append('state', 'minikick_auth');

    console.log('🔗 Redirigiendo a Kick para autorización...');
    res.redirect(authUrl.toString());
});

app.get('/auth/callback', async (req, res) => {
    const { code, error } = req.query;
    if (error) return res.status(400).send(`Error de Kick: ${error}`);

    try {
        const params = new URLSearchParams();
        params.append('grant_type', 'authorization_code');
        params.append('client_id', process.env.KICK_CLIENT_ID);
        params.append('client_secret', process.env.KICK_CLIENT_SECRET);
        params.append('redirect_uri', process.env.KICK_REDIRECT_URI);
        params.append('code', code);
        params.append('code_verifier', codeVerifier); 

        const tokenResponse = await axios.post('https://id.kick.com/oauth/token', params.toString(), {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        const kickAccessToken = tokenResponse.data.access_token;
        db.setConfig('access_token', kickAccessToken); // Guardamos el token

        console.log('🕵️‍♂️ Consultando identidad del streamer...');
        const userResponse = await axios.get('https://api.kick.com/public/v1/users', {
            headers: { 'Authorization': `Bearer ${kickAccessToken}` }
        });

        const userData = userResponse.data.data[0];
        const miNombre = userData.name;
        const miSlug = userData.slug || userData.username || miNombre.toLowerCase();

        db.setConfig('kick_username', miNombre);
        db.setConfig('kick_slug', miSlug);

        console.log(`✅ Sesión guardada en Base de Datos: ${miNombre}`);
        res.send(`<h1 style="color: #53fc18; text-align: center; margin-top: 50px;">¡Autenticado y Guardado!</h1><p style="text-align: center; color: white;">Revisa tu terminal.</p>`);

        conectarChatKick();

    } catch (err) {
        console.error('❌ Error en el proceso de login:', err.response?.data || err.message);
        res.status(500).send('Error al obtener acceso.');
    }
});

// ==========================================
// 2. MOTOR DE VOZ (TTS) CON AUTOLIMPIEZA
// ==========================================

async function procesarMensajeTTS(texto) {
    try {
        const respuesta = await axios.post('http://127.0.0.1:8000/generar-tts', {
            texto: texto,
            voz: "es-MX-JorgeNeural"
        });

        const rutaAudio = path.join(TTS_OUTPUT_DIR, respuesta.data.archivo);
        
        // 1. Reproducimos el audio y ESPERAMOS a que termine por completo
        await sound.play(rutaAudio);

        // 2. Una vez que termina, borramos el archivo del disco duro
        if (fs.existsSync(rutaAudio)) {
            fs.unlinkSync(rutaAudio);
            // console.log(`🧹 Archivo temporal borrado: ${respuesta.data.archivo}`); // Descomenta esto si quieres ver el aviso en consola
        }

    } catch (error) {
        console.error('❌ Error en audio (¿Está Python encendido?):', error.message);
    }
}

// ==========================================
// 3. WEBSOCKET (CHAT EN VIVO)
// ==========================================

async function conectarChatKick() {
    const kickAccessToken = db.getConfig('access_token');
    const nombre = db.getConfig('kick_username');
    let chatroomId = db.getConfig('chatroom_id'); 

    if (!kickAccessToken || !nombre) {
        console.log(`👉 Esperando autenticación. Por favor inicia sesión en http://localhost:${process.env.PORT || 8080}/auth/login`);
        return;
    }

    // Función interna para arrancar el chat una vez tengamos el ID
    const iniciarPusher = (idSala) => {
        // Extractor a prueba de balas para la compatibilidad con Node 24
        const moduloPusher = require('pusher-js');
        const ClientePusher = typeof moduloPusher === 'function' ? moduloPusher : (moduloPusher.default || moduloPusher.Pusher);

        // Instanciamos usando la clase extraída
        const pusher = new ClientePusher('32cbd69e4b950bf97679', { cluster: 'us2', forceTLS: true });

        const channel = pusher.subscribe(`chatrooms.${idSala}.v2`);

        console.log(`🟢 CONECTADO AL CHAT DE [${nombre.toUpperCase()}]`);

        channel.bind('App\\Events\\ChatMessageEvent', (data) => {
            const user = data.sender.username;
            const msg = data.content;
            console.log(`💬 ${user}: ${msg}`);

            if (msg.startsWith('!')) {
                console.log(`🎬 Comando detectado: ${msg} (En breve lo conectamos a la BD)`);
            } else {
                procesarMensajeTTS(`${user} dice: ${msg}`);
            }
        });
    };

    // Si ya tenemos el ID guardado en SQLite, conectamos directo!
    if (chatroomId) {
        iniciarPusher(chatroomId);
        return; 
    }

    // Si no tenemos el ID, se lo pedimos al usuario por consola (Solo pasará 1 vez)
    console.log("\n🛡️ Para protegerte de los bloqueos de Kick, configuraremos tu sala manualmente.");
    
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.question('👉 Pega aquí tu ID de Sala (el número que sacaste del HTML): ', (respuesta) => {
        chatroomId = respuesta.trim();
        
        if (chatroomId && !isNaN(chatroomId)) {
            db.setConfig('chatroom_id', chatroomId);
            console.log(`💾 ¡ID de Sala (${chatroomId}) guardado en tu Base de Datos local para siempre!`);
            rl.close();
            iniciarPusher(chatroomId); 
        } else {
            console.log("❌ No ingresaste un número válido. Reinicia la aplicación (node index.js) para intentar de nuevo.");
            rl.close();
        }
    });
}

// --- LANZAMIENTO ---
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`🚀 MiniKick listo en http://localhost:${PORT}`);
    
    // Al arrancar, intentamos conectarnos automáticamente leyendo la DB
    conectarChatKick();
});