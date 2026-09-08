"""Windows implementation. pycaw for volume (Core Audio IAudioEndpointVolume),
pynput + raw VK codes for media keys, win32com/WMI for brightness, ctypes
user32 for lock/monitor power, win32gui/win32process/psutil for foreground
app and window management.

COM (pycaw, WMI) needs CoInitialize on the calling thread. Actions run on
the Qt main thread (ADR-007), so this happens once here at adapter
construction — asserted explicitly rather than discovered at 3am, per
CLAUDE.md.
"""

from __future__ import annotations

import ctypes
import logging

from elara.platform_adapters.base import AppInfo, PlatformAdapter

logger = logging.getLogger(__name__)

VK_MEDIA_STOP = 0xB2
_WM_SYSCOMMAND = 0x0112
_SC_MONITORPOWER = 0xF170
_HWND_BROADCAST = 0xFFFF


class WindowsAdapter(PlatformAdapter):
    supported = True

    def __init__(self) -> None:
        import comtypes

        try:
            comtypes.CoInitialize()
        except OSError:
            pass  # already initialized on this thread — fine

        from pynput.keyboard import Controller as KeyboardController

        self._keyboard = KeyboardController()
        self._volume_interface = None  # created lazily; the audio device can change

    # -- Volume (pycaw) --
    def _volume(self):
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return interface.QueryInterface(IAudioEndpointVolume)

    def volume_up(self, step: int = 5) -> None:
        vol = self._volume()
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(min(1.0, current + step / 100.0), None)

    def volume_down(self, step: int = 5) -> None:
        vol = self._volume()
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(max(0.0, current - step / 100.0), None)

    def volume_set(self, percent: int) -> None:
        vol = self._volume()
        vol.SetMasterVolumeLevelScalar(max(0.0, min(1.0, percent / 100.0)), None)

    def volume_get(self) -> float:
        return self._volume().GetMasterVolumeLevelScalar() * 100.0

    def volume_mute_toggle(self) -> None:
        vol = self._volume()
        vol.SetMute(not vol.GetMute(), None)

    # -- Media keys --
    def media_play_pause(self) -> None:
        from pynput.keyboard import Key

        self._keyboard.tap(Key.media_play_pause)

    def media_next(self) -> None:
        from pynput.keyboard import Key

        self._keyboard.tap(Key.media_next)

    def media_prev(self) -> None:
        from pynput.keyboard import Key

        self._keyboard.tap(Key.media_previous)

    def media_stop(self) -> None:
        # pynput has no media-stop key; send the raw virtual key directly.
        ctypes.windll.user32.keybd_event(VK_MEDIA_STOP, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_STOP, 0, 2, 0)  # KEYEVENTF_KEYUP

    # -- Brightness (WMI via win32com, no extra dependency) --
    def _wmi_root(self):
        import win32com.client

        return win32com.client.GetObject(r"winmgmts:\\.\root\wmi")

    def brightness_get(self) -> float:
        root = self._wmi_root()
        rows = root.ExecQuery("SELECT * FROM WmiMonitorBrightness")
        for row in rows:
            return float(row.CurrentBrightness)
        raise RuntimeError("no WmiMonitorBrightness instance (external monitor or unsupported panel?)")

    def brightness_set(self, percent: int) -> None:
        root = self._wmi_root()
        methods = root.ExecQuery("SELECT * FROM WmiMonitorBrightnessMethods")
        for row in methods:
            row.WmiSetBrightness(max(0, min(100, percent)), 0)
            return
        raise RuntimeError("no WmiMonitorBrightnessMethods instance")

    def brightness_up(self, step: int = 10) -> None:
        self.brightness_set(int(min(100, self.brightness_get() + step)))

    def brightness_down(self, step: int = 10) -> None:
        self.brightness_set(int(max(0, self.brightness_get() - step)))

    # -- Lock / sleep --
    def lock(self) -> None:
        ctypes.windll.user32.LockWorkStation()

    def sleep_display(self) -> None:
        ctypes.windll.user32.SendMessageW(_HWND_BROADCAST, _WM_SYSCOMMAND, _SC_MONITORPOWER, 2)

    # -- Foreground app / windows --
    def get_foreground_app(self) -> AppInfo:
        import psutil
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()
        _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            return AppInfo(name=proc.name(), pid=pid, exe_path=proc.exe())
        except psutil.Error:
            return AppInfo(name=win32gui.GetWindowText(hwnd) or "unknown", pid=pid, exe_path=None)

    def _foreground_hwnd(self) -> int:
        import win32gui

        return win32gui.GetForegroundWindow()

    def window_minimize(self) -> None:
        import win32con
        import win32gui

        win32gui.ShowWindow(self._foreground_hwnd(), win32con.SW_MINIMIZE)

    def window_maximize(self) -> None:
        import win32con
        import win32gui

        win32gui.ShowWindow(self._foreground_hwnd(), win32con.SW_MAXIMIZE)

    def window_close(self) -> None:
        import win32con
        import win32gui

        win32gui.PostMessage(self._foreground_hwnd(), win32con.WM_CLOSE, 0, 0)

    def _snap(self, side: str) -> None:
        import win32api
        import win32con
        import win32gui

        hwnd = self._foreground_hwnd()
        monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        info = win32api.GetMonitorInfo(monitor)
        left, top, right, bottom = info["Work"]
        width = (right - left) // 2
        x = left if side == "left" else left + width
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, 0, x, top, width, bottom - top, win32con.SWP_NOZORDER)

    def window_snap_left(self) -> None:
        self._snap("left")

    def window_snap_right(self) -> None:
        self._snap("right")

    def window_switch_next(self) -> None:
        from pynput.keyboard import Key

        with self._keyboard.pressed(Key.alt):
            self._keyboard.tap(Key.tab)

    def window_switch_prev(self) -> None:
        from pynput.keyboard import Key

        with self._keyboard.pressed(Key.alt):
            with self._keyboard.pressed(Key.shift):
                self._keyboard.tap(Key.tab)

    def show_desktop(self) -> None:
        import win32com.client

        shell = win32com.client.Dispatch("Shell.Application")
        shell.ToggleDesktop()

    # -- Do not disturb --
    def dnd_set(self, enabled: bool) -> None:
        # Windows Focus Assist has no supported public API — the registry
        # keys involved are undocumented and version-fragile. Left
        # unimplemented deliberately rather than shipping a hack that
        # silently breaks on the next Windows update. See ADR-021.
        raise NotImplementedError("Focus Assist has no supported public API on Windows")

    def dnd_get(self) -> bool:
        raise NotImplementedError("Focus Assist has no supported public API on Windows")
