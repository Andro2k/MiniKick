require('dotenv').config();
const express = require('express');
const axios = require('axios');
const path = require('path');
const sound = require('sound-play'); // El nuevo reproductor local

const app = express();
app.use(express.json());

// --- FUNCIÓN PARA PEDIR AUDIO Y REPRODUCIRLO DIRECTAMENTE ---
async function procesarMensajeTTS(textoMensaje) {
    try {
        console.log(`🗣️ Pidiendo audio a Python: "${textoMensaje}"...`);
        
        // 1. Pedimos a Python que genere el .mp3
        const respuesta = await axios.post('http://127.0.0.1:8000/generar-tts', {
            texto: textoMensaje,
            voz: "es-MX-JorgeNeural"
        });

        const archivo = respuesta.data.archivo;
        
        // 2. Buscamos la ruta exacta del archivo en tu PC
        const rutaAudio = path.join(__dirname, '..', 'media', 'audios', archivo);
        console.log(`🔊 Reproduciendo localmente: ${rutaAudio}`);
        
        // 3. ¡Hacemos que suene en tu Windows!
        sound.play(rutaAudio).then(() => {
            console.log('🎵 Reproducción terminada.');
        }).catch((err) => {
            console.error('❌ Error al reproducir el archivo:', err);
        });

    } catch (error) {
        console.error('❌ Error general:', error.message);
    }
}

// --- RUTA DE PRUEBA ---
app.post('/simular-chat', async (req, res) => {
    const { mensaje } = req.body;
    if (!mensaje) return res.status(400).send('Falta el mensaje');
    
    procesarMensajeTTS(mensaje);
    res.send({ status: 'Sonando en tus altavoces...' });
});

// --- ENCENDER EL SERVIDOR ---
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Cerebro Node.js (App Local) corriendo en http://localhost:${PORT}`);
});