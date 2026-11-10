# resources\tests\test_gui_bridge.py

import threading

from PySide6.QtCore import QCoreApplication, QThread

from frontend.common.gui_bridge import run_on_gui


def test_run_on_gui_executes_in_main_thread():
    app = QCoreApplication.instance() or QCoreApplication([])
    seen = {}

    def target(value):
        seen["thread"] = QThread.currentThread()
        seen["value"] = value

    t = threading.Thread(target=lambda: run_on_gui(target, 7))
    t.start()
    t.join()
    for _ in range(50):
        app.processEvents()
        if seen:
            break
    assert seen["value"] == 7
    assert seen["thread"] is app.thread()


def test_get_bridge_is_a_single_instance_across_threads():
    from frontend.common import gui_bridge

    QCoreApplication.instance() or QCoreApplication([])
    gui_bridge._bridge = None
    found = []
    threads = [threading.Thread(target=lambda: found.append(gui_bridge._get_bridge())) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({id(b) for b in found}) == 1
