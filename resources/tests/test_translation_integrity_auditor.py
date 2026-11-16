# resources\tests\test_translation_integrity_auditor.py
"""El auditor de claves lee los .ftl: aplana ids y selectores, y borra claves sin tocar el resto."""

from pathlib import Path

from resources.tools.project_translation_integrity_auditor import DataLoader

SOURCE = (
    "## demo\n"
    "demo-hello = Hola { $user }\n"
    "demo-songs = { $count ->\n"
    "    [one] { $count } cancion\n"
    "   *[other] { $count } canciones\n"
    "}\n"
    "demo-gone = Sobra\n"
    "demo-pad = { \"\\u0020\" }(Copia)\n"
)


def _load(tmp_path):
    path = Path(tmp_path) / "main.ftl"
    path.write_text(SOURCE, encoding="utf-8", newline="\n")
    return (path, *DataLoader.load_ftl(path))


def test_flatten_maps_ids_to_dotted_keys_with_legacy_placeholders(tmp_path):
    _, _, resource = _load(tmp_path)
    flat = DataLoader.flatten_ftl(resource)
    assert flat["demo.hello"] == "Hola {user}"
    assert flat["demo.songs"] == "{count} canciones"
    assert flat["demo.pad"] == " (Copia)"


def test_remove_keys_deletes_only_the_requested_messages(tmp_path):
    path, text, resource = _load(tmp_path)
    DataLoader.remove_ftl_keys(path, text, resource, {"demo.gone", "demo.songs"})
    assert path.read_text(encoding="utf-8") == (
        "## demo\ndemo-hello = Hola { $user }\ndemo-pad = { \"\\u0020\" }(Copia)\n"
    )
