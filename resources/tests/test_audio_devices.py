# resources\tests\test_audio_devices.py

import backend.providers.audio.devices as devices


class _FakeId:
    def __init__(self, text):
        self._text = text

    def data(self):
        return self._text.encode("utf-8")


class _FakeDevice:
    def __init__(self, dev_id, description):
        self._id = _FakeId(dev_id)
        self._description = description

    def id(self):
        return self._id

    def description(self):
        return self._description


def _patch_devices(monkeypatch, outputs, default):
    class _FakeMediaDevices:
        @staticmethod
        def audioOutputs():
            return outputs

        @staticmethod
        def defaultAudioOutput():
            return default

    monkeypatch.setattr(devices, "QMediaDevices", _FakeMediaDevices)


def test_resolve_matches_by_id_and_by_description(monkeypatch):
    speakers = _FakeDevice("dev-1", "Speakers")
    headset = _FakeDevice("dev-2", "Headset")
    default = _FakeDevice("dev-0", "Default")
    _patch_devices(monkeypatch, [speakers, headset], default)

    assert devices.resolve_audio_output("dev-2") is headset
    assert devices.resolve_audio_output("Speakers") is speakers


def test_resolve_falls_back_to_default(monkeypatch):
    default = _FakeDevice("dev-0", "Default")
    _patch_devices(monkeypatch, [_FakeDevice("dev-1", "Speakers")], default)

    for device_id in (None, "", "default", "missing-device"):
        assert devices.resolve_audio_output(device_id) is default


def test_audio_output_exists(monkeypatch):
    _patch_devices(monkeypatch, [_FakeDevice("dev-1", "Speakers")], _FakeDevice("dev-0", "Default"))

    assert devices.audio_output_exists(None)
    assert devices.audio_output_exists("default")
    assert devices.audio_output_exists("dev-1")
    assert not devices.audio_output_exists("unplugged")
