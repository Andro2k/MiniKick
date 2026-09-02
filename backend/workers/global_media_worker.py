# backend\workers\global_media_worker.py

import sys
import ctypes
import ctypes.wintypes
import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("minikick.workers.media_keys")

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP       = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

WH_KEYBOARD_LL = 13
WM_KEYDOWN     = 0x0100
WM_SYSKEYDOWN  = 0x0104
WM_QUIT        = 0x0012

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t)
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)

class GlobalMediaWorker(QThread):
    play_pause_pressed = Signal()
    skip_pressed = Signal()
    stop_pressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Global_Media_Keys")
        self._running = False
        self._hook = None
        self._hook_proc_ref = None
        self._thread_id = None

    def run(self):
        if sys.platform != "win32":
            return

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        kernel32.GetModuleHandleW.restype = ctypes.wintypes.HMODULE

        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.wintypes.HMODULE,
            ctypes.wintypes.DWORD
        ]
        user32.SetWindowsHookExW.restype = ctypes.c_void_p

        user32.CallNextHookEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.wintypes.WPARAM,
            ctypes.wintypes.LPARAM
        ]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t

        user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        user32.UnhookWindowsHookEx.restype = ctypes.wintypes.BOOL

        self._running = True
        self._thread_id = kernel32.GetCurrentThreadId()

        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0 and (wParam == WM_KEYDOWN or wParam == WM_SYSKEYDOWN):
                try:
                    kb_struct = KBDLLHOOKSTRUCT.from_address(lParam)
                    vk = kb_struct.vkCode
                    if vk == VK_MEDIA_PLAY_PAUSE:
                        self.play_pause_pressed.emit()
                    elif vk == VK_MEDIA_NEXT_TRACK:
                        self.skip_pressed.emit()
                    elif vk == VK_MEDIA_STOP:
                        self.stop_pressed.emit()
                except Exception as e:
                    logger.debug("[GlobalMediaWorker] Hook event parsing error: %s", e)
            return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

        self._hook_proc_ref = HOOKPROC(hook_proc)
        hmod = kernel32.GetModuleHandleW(None)
        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            ctypes.cast(self._hook_proc_ref, ctypes.c_void_p),
            hmod,
            0
        )

        if not self._hook:
            err = kernel32.GetLastError()
            logger.warning("[GlobalMediaWorker] Failed to install Windows keyboard hook. Win32 Error: %s", err)
            return

        logger.info("[GlobalMediaWorker] Global media keys hook installed successfully (Hook: %s).", self._hook)

        try:
            msg = ctypes.wintypes.MSG()
            while self._running:
                b_ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if b_ret <= 0 or not self._running:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self._hook:
                user32.UnhookWindowsHookEx(self._hook)
                self._hook = None
                logger.info("[GlobalMediaWorker] Global media keys hook uninstalled cleanly.")

    def stop(self):
        self._running = False
        if sys.platform == "win32" and self._thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            except Exception as e:
                logger.debug("[GlobalMediaWorker] PostThreadMessage error: %s", e)
        self.quit()
