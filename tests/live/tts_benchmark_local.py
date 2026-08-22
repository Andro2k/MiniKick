# tests\live\tts_benchmark_local.py

import os
import sys
import time
import wave
import urllib.request
import argparse
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

MODELS_DIR = os.path.join(PROJECT_ROOT, "tests", "logs", "tts_models")
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "tests", "logs", "tts_samples")

# Standard test benchmark phrases in Spanish & English
TEST_PHRASES = [
    {
        "id": "short_es",
        "category": "Short Alert (ES)",
        "text": "¡Gracias por el follow, bienvenido al stream!"
    },
    {
        "id": "medium_es",
        "category": "Chat Message (ES)",
        "text": "Hola streamer, qué buena jugada te acabas de mandar en la partida anterior. ¿Vas a jugar otra ronda o cambiamos de juego?"
    },
    {
        "id": "long_es",
        "category": "Donation / Sub Tier 3 (ES)",
        "text": "Muchísimas gracias por esa suscripción nivel tres y por apoyar tanto el canal de Kick. Recuerden todos en el chat dejar su mensaje y disfrutar del contenido en directo."
    },
    {
        "id": "short_en",
        "category": "Short Alert (EN)",
        "text": "Thank you for the raid and welcome to the channel!"
    }
]

# Model download URLs
PIPER_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"
PIPER_CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json"

KOKORO_MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
KOKORO_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

def ensure_directory(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path

def download_file_with_progress(url: str, dest_path: str, description: str = "Downloading") -> bool:
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"  [OK] {description} ya existe en cache local ({os.path.getsize(dest_path) / (1024*1024):.2f} MB).", flush=True)
        return True
    
    print(f"  [..] Descargando {description}...", flush=True)
    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                downloaded_mb = (count * block_size) / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                sys.stdout.write(f"\r     -> {percent}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
                sys.stdout.flush()
        
        temp_dest = dest_path + ".tmp"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_dest, 'wb') as out_file:
            total_size = int(response.headers.get('content-length', 0))
            count = 0
            block_size = 1024 * 64
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                count += 1
                reporthook(count, block_size, total_size)
        print("", flush=True)
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(temp_dest, dest_path)
        print(f"  [OK] {description} completado exitosamente.", flush=True)
        return True
    except Exception as e:
        print(f"\n  [ERROR] Error descargando {description}: {e}", flush=True)
        return False

# ============================================================================
# Engine 1: Pyttsx3 (SAPI5 Baseline)
# ============================================================================
class Pyttsx3Engine:
    def __init__(self):
        self.name = "pyttsx3 (SAPI5)"

    def _init_com(self):
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

    def _uninit_com(self):
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def initialize(self) -> float:
        t0 = time.perf_counter()
        try:
            self._init_com()
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.stop()
            del engine
            self._uninit_com()
            return (time.perf_counter() - t0) * 1000.0
        except Exception as e:
            self._uninit_com()
            print(f"[pyttsx3] Error init: {e}", flush=True)
            return -1.0

    def synthesize(self, text: str, output_path: str, lang: str = "es") -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            self._init_com()
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            try:
                engine.stop()
                del engine
            except Exception:
                pass
            self._uninit_com()
            
            elapsed_sec = time.perf_counter() - t0
            duration_sec = 0.0
            if os.path.exists(output_path) and os.path.getsize(output_path) > 44:
                try:
                    with wave.open(output_path, 'r') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration_sec = frames / float(rate)
                except Exception:
                    duration_sec = len(text.split()) * 0.35
            
            rtf = elapsed_sec / max(0.001, duration_sec)
            return {
                "success": True,
                "latency_ms": elapsed_sec * 1000.0,
                "duration_sec": duration_sec,
                "rtf": rtf,
                "file_path": output_path
            }
        except Exception as e:
            self._uninit_com()
            return {"success": False, "error": str(e), "latency_ms": 0, "duration_sec": 0, "rtf": 0}

# ============================================================================
# Engine 2: Piper TTS Engine (VITS / ONNX)
# ============================================================================
class PiperEngine:
    def __init__(self, model_name: str = "es_ES-davefx-medium"):
        self.name = f"Piper TTS ({model_name})"
        self.model_name = model_name
        self.model_path = os.path.join(MODELS_DIR, "piper", f"{model_name}.onnx")
        self.config_path = os.path.join(MODELS_DIR, "piper", f"{model_name}.onnx.json")
        self._voice = None

    def ensure_models(self) -> bool:
        ensure_directory(os.path.join(MODELS_DIR, "piper"))
        ok1 = download_file_with_progress(PIPER_MODEL_URL, self.model_path, "Modelo Piper ONNX (es_ES-davefx)")
        ok2 = download_file_with_progress(PIPER_CONFIG_URL, self.config_path, "Configuración Piper JSON")
        return ok1 and ok2

    def initialize(self) -> float:
        t0 = time.perf_counter()
        try:
            from piper.voice import PiperVoice
            self._voice = PiperVoice.load(self.model_path, config_path=self.config_path)
            return (time.perf_counter() - t0) * 1000.0
        except Exception as e:
            print(f"[Piper] Error cargando modelo: {e}", flush=True)
            return -1.0

    def synthesize(self, text: str, output_path: str, lang: str = "es") -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            if self._voice is None:
                return {"success": False, "error": "Voice not initialized"}
            
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self._voice.config.sample_rate)
                for chunk in self._voice.synthesize(text):
                    wav_file.writeframes(chunk.audio_int16_bytes)
            
            elapsed_sec = time.perf_counter() - t0
            duration_sec = 0.0
            if os.path.exists(output_path) and os.path.getsize(output_path) > 44:
                with wave.open(output_path, 'r') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration_sec = frames / float(rate)
            
            rtf = elapsed_sec / max(0.001, duration_sec)
            return {
                "success": True,
                "latency_ms": elapsed_sec * 1000.0,
                "duration_sec": duration_sec,
                "rtf": rtf,
                "file_path": output_path
            }
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": 0, "duration_sec": 0, "rtf": 0}

# ============================================================================
# Engine 3: Kokoro TTS Engine (Kokoro-82M / ONNX)
# ============================================================================
class KokoroEngine:
    def __init__(self, voice_name: str = "em_alex"):
        self.name = f"Kokoro-82M ({voice_name})"
        self.voice_name = voice_name
        self.model_path = os.path.join(MODELS_DIR, "kokoro", "kokoro-v1.0.onnx")
        self.voices_path = os.path.join(MODELS_DIR, "kokoro", "voices-v1.0.bin")
        self._kokoro = None

    def ensure_models(self) -> bool:
        ensure_directory(os.path.join(MODELS_DIR, "kokoro"))
        ok1 = download_file_with_progress(KOKORO_MODEL_URL, self.model_path, "Modelo Kokoro-82M ONNX v1.0")
        ok2 = download_file_with_progress(KOKORO_VOICES_URL, self.voices_path, "Voces Kokoro Bin v1.0")
        return ok1 and ok2

    def initialize(self) -> float:
        t0 = time.perf_counter()
        try:
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro(self.model_path, self.voices_path)
            return (time.perf_counter() - t0) * 1000.0
        except Exception as e:
            print(f"[Kokoro] Error cargando modelo: {e}", flush=True)
            return -1.0

    def synthesize(self, text: str, output_path: str, lang: str = "es") -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            if self._kokoro is None:
                return {"success": False, "error": "Kokoro not initialized"}
            
            kokoro_lang = "es" if lang == "es" else "en-us"
            available_voices = self._kokoro.get_voices()
            voice_to_use = self.voice_name
            
            if voice_to_use not in available_voices:
                es_voices = [v for v in available_voices if v.startswith("e")]
                if kokoro_lang == "es" and es_voices:
                    voice_to_use = es_voices[0]
                elif available_voices:
                    voice_to_use = available_voices[0]

            samples, sample_rate = self._kokoro.create(
                text=text,
                voice=voice_to_use,
                speed=1.0,
                lang=kokoro_lang
            )
            
            import numpy as np
            audio_int16 = (samples * 32767).astype(np.int16)
            
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            elapsed_sec = time.perf_counter() - t0
            duration_sec = len(samples) / float(sample_rate)
            rtf = elapsed_sec / max(0.001, duration_sec)
            
            return {
                "success": True,
                "latency_ms": elapsed_sec * 1000.0,
                "duration_sec": duration_sec,
                "rtf": rtf,
                "file_path": output_path,
                "voice_used": voice_to_use
            }
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": 0, "duration_sec": 0, "rtf": 0}

# ============================================================================
# Benchmark Runner & Presentation
# ============================================================================
class LocalTTSBenchmarkRunner:
    def __init__(self):
        ensure_directory(SAMPLES_DIR)
        self.engines: List[Any] = []
        self.results: Dict[str, Dict[str, Any]] = {}

    def setup_engines(self, skip_kokoro: bool = False, skip_piper: bool = False) -> None:
        print("\n" + "=" * 70, flush=True)
        print("  [MiniKick] PREPARACIÓN DE MOTORES DE VOZ LOCALES", flush=True)
        print("=" * 70, flush=True)

        # 1. Pyttsx3 (SAPI5)
        pyttsx3_engine = Pyttsx3Engine()
        self.engines.append(pyttsx3_engine)

        # 2. Piper TTS
        if not skip_piper:
            piper_engine = PiperEngine()
            print("\n-> Verificando dependencias de Piper TTS...", flush=True)
            if piper_engine.ensure_models():
                self.engines.append(piper_engine)
            else:
                print("  [!] Saltando Piper TTS debido a error de descarga.", flush=True)

        # 3. Kokoro TTS
        if not skip_kokoro:
            kokoro_engine = KokoroEngine()
            print("\n-> Verificando dependencias de Kokoro-82M TTS...", flush=True)
            if kokoro_engine.ensure_models():
                self.engines.append(kokoro_engine)
            else:
                print("  [!] Saltando Kokoro-82M debido a error de descarga.", flush=True)

    def run_benchmark(self) -> None:
        print("\n" + "=" * 70, flush=True)
        print("  [MiniKick] INICIANDO BENCHMARK DE RENDIMIENTO TTS LOCAL", flush=True)
        print("=" * 70, flush=True)
        
        # 1. Model Initializations
        init_times = {}
        for engine in self.engines:
            print(f"\n[+] Inicializando motor: {engine.name}...", flush=True)
            init_ms = engine.initialize()
            init_times[engine.name] = init_ms
            if init_ms >= 0:
                print(f"    ✓ Tiempo de carga/arranque en frío: {init_ms:.2f} ms", flush=True)
            else:
                print(f"    X Fallo al inicializar.", flush=True)

        # 2. Test phrase synthesis
        print("\n" + "-" * 70, flush=True)
        print("  SINTETIZANDO FRASES DE PRUEBA (Latencia, Duración y RTF)...", flush=True)
        print("-" * 70, flush=True)

        benchmark_matrix = []

        for phrase in TEST_PHRASES:
            phrase_id = phrase["id"]
            phrase_cat = phrase["category"]
            phrase_text = phrase["text"]
            lang = "en" if "_en" in phrase_id else "es"
            
            print(f"\n📝 Frase [{phrase_cat}] ({len(phrase_text)} caracteres):", flush=True)
            print(f"   \"{phrase_text}\"", flush=True)

            for engine in self.engines:
                out_filename = f"sample_{engine.name.split()[0].lower()}_{phrase_id}.wav"
                out_path = os.path.join(SAMPLES_DIR, out_filename)

                res = engine.synthesize(phrase_text, out_path, lang=lang)

                if res.get("success"):
                    lat_ms = res["latency_ms"]
                    dur_s = res["duration_sec"]
                    rtf = res["rtf"]
                    speedup = (1.0 / rtf) if rtf > 0 else 0
                    print(f"   ⚡ {engine.name:<25}: Latencia = {lat_ms:6.1f} ms | Audio = {dur_s:4.1f}s | RTF = {rtf:.3f} ({speedup:.1f}x tiempo real)", flush=True)
                    
                    benchmark_matrix.append({
                        "Motor": engine.name,
                        "Categoría": phrase_cat,
                        "Caracteres": len(phrase_text),
                        "Latencia (ms)": f"{lat_ms:.1f} ms",
                        "Duración": f"{dur_s:.2f} s",
                        "RTF": f"{rtf:.3f}",
                        "Velocidad": f"{speedup:.1f}x",
                        "Archivo": out_filename
                    })
                else:
                    print(f"   X {engine.name:<25}: Error -> {res.get('error')}", flush=True)

        # 3. Print Final Comparison Table
        print("\n" + "=" * 90, flush=True)
        print("                 RESUMEN COMPARATIVO DE RENDIMIENTO LOCAL", flush=True)
        print("=" * 90, flush=True)
        try:
            from tabulate import tabulate
            table_headers = ["Motor", "Categoría", "Chars", "Latencia", "Audio", "RTF", "Velocidad", "Muestra WAV"]
            table_data = [
                [row["Motor"], row["Categoría"], row["Caracteres"], row["Latencia (ms)"], row["Duración"], row["RTF"], row["Velocidad"], row["Archivo"]]
                for row in benchmark_matrix
            ]
            print(tabulate(table_data, headers=table_headers, tablefmt="fancy_grid"), flush=True)
        except Exception:
            for row in benchmark_matrix:
                print(row, flush=True)

        print("\n📂 Muestras de audio generadas guardadas en:", flush=True)
        print(f"   {SAMPLES_DIR}", flush=True)
        print("\n💡 GLOSARIO DE MÉTRICAS:", flush=True)
        print("   - Latencia: Tiempo transcurrido desde que se solicita el texto hasta que el audio está 100% generado.", flush=True)
        print("   - RTF (Real-Time Factor): Tiempo de cómputo / Duración del audio. Un RTF < 0.2 significa que es 5x más rápido que hablar en tiempo real.", flush=True)
        print("   - Velocidad (x): Cuántas veces más rápido que la voz humana genera el audio el procesador.", flush=True)

def main():
    parser = argparse.ArgumentParser(description="MiniKick Local TTS Benchmark (Piper vs Kokoro vs pyttsx3)")
    parser.add_argument("--skip-kokoro", action="store_true", help="Saltar pruebas de Kokoro TTS")
    parser.add_argument("--skip-piper", action="store_true", help="Saltar pruebas de Piper TTS")
    args = parser.parse_args()

    runner = LocalTTSBenchmarkRunner()
    runner.setup_engines(skip_kokoro=args.skip_kokoro, skip_piper=args.skip_piper)
    runner.run_benchmark()

if __name__ == "__main__":
    main()
