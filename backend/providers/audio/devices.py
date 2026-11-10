# backend\providers\audio\devices.py

from PySide6.QtMultimedia import QMediaDevices


def _device_id(dev) -> str:
    raw = dev.id()
    return raw.data().decode("utf-8", errors="ignore") if hasattr(raw, "data") else str(raw)


def _is_default(device_id: str | None) -> bool:
    return not device_id or device_id == "default"


def find_audio_output(device_id: str | None):
    if _is_default(device_id):
        return None
    for dev in QMediaDevices.audioOutputs():
        if _device_id(dev) == device_id or dev.description() == device_id:
            return dev
    return None


def resolve_audio_output(device_id: str | None):
    return find_audio_output(device_id) or QMediaDevices.defaultAudioOutput()


def audio_output_exists(device_id: str | None) -> bool:
    return _is_default(device_id) or find_audio_output(device_id) is not None
