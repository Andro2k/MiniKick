# apply_paso4.py
#
# Paso 4: reemplaza 10 bloques "except ...: pass" por un log, sin tocar nada más.
#
# Uso (desde la RAÍZ del repo, donde está la carpeta backend/):
#     python apply_paso4.py                      # solo muestra qué haría (no escribe nada)
#     python apply_paso4.py --apply              # aplica los cambios (todo o nada)
#     python apply_paso4.py --apply --partial    # aplica los que coinciden y OMITE los que no
#
# Seguro por diseño:
#   - Cada bloque debe aparecer EXACTAMENTE una vez; si no, no se escribe nada
#     (salvo que uses --partial, que omite SOLO los bloques que no coinciden).
#   - Respeta tus saltos de línea (CRLF o LF).
#   - Es idempotente: si ya está aplicado, lo indica y no lo repite.

import pathlib
import sys

ROOT = pathlib.Path("backend")

# (archivo, bloque_original, bloque_nuevo)  -> la indentación es parte del bloque
EDITS: list[tuple[str, str, str]] = [
    # 1) cache_storage.py — limpieza de caché (check_and_clean_cache)
    (
        "database/cache_storage.py",
        "                        deleted_files += 1\n"
        "                    except Exception:\n"
        "                        pass\n",
        "                        deleted_files += 1\n"
        "                    except OSError as e:\n"
        "                        logger.debug(\"[CacheStorage] Could not remove cached file '%s': %s\", fpath, e)\n",
    ),
    # 2) cache_storage.py — clear_all_cache
    (
        "database/cache_storage.py",
        "                            deleted += 1\n"
        "                        except Exception:\n"
        "                            pass\n",
        "                            deleted += 1\n"
        "                        except OSError as e:\n"
        "                            logger.debug(\"[CacheStorage] Could not remove cached file '%s': %s\", fpath, e)\n",
    ),
    # 3) database_manager.py — _prune_corrupt_backups
    (
        "database/database_manager.py",
        "                try:\n"
        "                    os.remove(stale_path)\n"
        "                except OSError:\n"
        "                    pass\n",
        "                try:\n"
        "                    os.remove(stale_path)\n"
        "                except OSError as e:\n"
        "                    logger.debug(\"[DatabaseManager] Could not remove old corrupt backup '%s': %s\", stale_path, e)\n",
    ),
    # 4) kick_provider.py — update_channel_metadata (category_id inválido)
    (
        "providers/chat/kick_provider.py",
        "                    payload[\"category_id\"] = cid\n"
        "            except (ValueError, TypeError):\n"
        "                pass\n",
        "                    payload[\"category_id\"] = cid\n"
        "            except (ValueError, TypeError):\n"
        "                logger.warning(\"[KickAPIClient] Ignoring invalid category_id: %r\", category_id)\n",
    ),
    # 5) kick_ws_provider.py — _heartbeat_watchdog_loop (cierre del socket zombie)
    (
        "providers/chat/kick_ws_provider.py",
        "                    ws.close()\n"
        "                except Exception:\n"
        "                    pass\n"
        "                break\n",
        "                    ws.close()\n"
        "                except Exception as e:\n"
        "                    logger.debug(\"[KickWebSocket] Error closing zombie socket: %s\", e)\n"
        "                break\n",
    ),
    # 6) twitch_ws_provider.py — _heartbeat_watchdog_loop
    (
        "providers/chat/twitch_ws_provider.py",
        "                    ws.close()\n"
        "                except Exception:\n"
        "                    pass\n"
        "                break\n",
        "                    ws.close()\n"
        "                except Exception as e:\n"
        "                    logger.debug(\"[TwitchWS] Error closing zombie socket: %s\", e)\n"
        "                break\n",
    ),
    # 7) twitch_ws_provider.py — strip_twitch_emotes (rango mal formado)
    (
        "providers/chat/twitch_ws_provider.py",
        "                            ranges.append((start, end))\n"
        "                        except ValueError:\n"
        "                            pass\n",
        "                            ranges.append((start, end))\n"
        "                        except ValueError:\n"
        "                            logger.debug(\"[TwitchWS] Ignoring malformed emote range '%s'\", r)\n",
    ),
    # 8) twitch_eventsub_provider.py — _on_close_handler (callback on_disconnected)
    (
        "providers/chat/twitch_eventsub_provider.py",
        "                self._on_disconnected()\n"
        "            except Exception:\n"
        "                pass\n",
        "                self._on_disconnected()\n"
        "            except Exception as cb_err:\n"
        "                logger.debug(\"[TwitchEventSub] on_disconnected callback failed: %s\", cb_err)\n",
    ),
    # 9) tiktok_provider.py — stop_chat (disconnect asíncrono)
    (
        "providers/chat/tiktok_provider.py",
        "                        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)\n"
        "                    except Exception:\n"
        "                        pass\n",
        "                        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)\n"
        "                    except Exception as e:\n"
        "                        logger.debug(\"[TikTokChatProvider] Error scheduling client disconnect: %s\", e)\n",
    ),
    # 10) music_worker.py — borrado de descarga parcial al interrumpir
    (
        "workers/music_worker.py",
        "                            try:\n"
        "                                os.remove(p)\n"
        "                            except Exception:\n"
        "                                pass\n",
        "                            try:\n"
        "                                os.remove(p)\n"
        "                            except OSError as e:\n"
        "                                logger.debug(\"[MusicWorker] Could not remove partial download '%s': %s\", p, e)\n",
    ),
]


def main() -> int:
    apply = "--apply" in sys.argv
    partial = "--partial" in sys.argv
    if not ROOT.is_dir():
        print("ERROR: ejecuta este script desde la raíz del repo (donde está la carpeta 'backend').")
        return 2

    # Agrupa por archivo para escribir cada uno una sola vez
    texts: dict[str, tuple[str, str]] = {}  # archivo -> (texto normalizado a LF, newline original)
    errors = 0
    pending = 0
    skipped = 0
    for rel, old, new in EDITS:
        path = ROOT / rel
        if rel not in texts:
            if not path.is_file():
                print(f"{'OMITE' if partial else 'ERROR'} {rel}: archivo no encontrado")
                errors += 0 if partial else 1
                skipped += 1
                continue
            raw = path.read_bytes().decode("utf-8")
            newline = "\r\n" if "\r\n" in raw else "\n"
            texts[rel] = (raw.replace("\r\n", "\n"), newline)
        text, newline = texts[rel]
        count = text.count(old)
        if count == 1:
            texts[rel] = (text.replace(old, new), newline)
            pending += 1
            print(f"OK     {rel}: bloque encontrado")
        elif count == 0 and text.count(new) == 1:
            print(f"YA     {rel}: ya estaba aplicado")
        else:
            print(f"{'OMITE' if partial else 'ERROR'} {rel}: el bloque aparece {count} veces (debe ser 1).")
            errors += 0 if partial else 1
            skipped += 1

    if errors:
        print(f"\n{errors} problema(s). No se modificó ningún archivo. "
              "(Usa --partial para aplicar solo los bloques que sí coinciden.)")
        return 1
    if not apply:
        extra = f", {skipped} omitido(s)" if skipped else ""
        print(f"\nSimulación: {pending} cambio(s) listos{extra}. Ejecuta con --apply para escribirlos.")
        return 0

    for rel, (text, newline) in texts.items():
        path = ROOT / rel
        path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    extra = f" ({skipped} omitido(s): revísalos aparte)" if skipped else ""
    print(f"\nListo: {pending} cambio(s) aplicados{extra}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
