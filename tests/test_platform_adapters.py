from __future__ import annotations

import inspect
import sys

import pytest

from elara.platform_adapters import get_adapter
from elara.platform_adapters.base import PlatformAdapter
from elara.platform_adapters.linux import LinuxAdapter
from elara.platform_adapters.macos import MacOSAdapter
from elara.platform_adapters.windows import WindowsAdapter

_CAPABILITY_METHODS = [
    name
    for name, member in inspect.getmembers(PlatformAdapter, predicate=inspect.isfunction)
    if not name.startswith("_")
]


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="constructs a real WindowsAdapter, which needs pycaw/comtypes/pynput (Windows-only deps)",
)
def test_get_adapter_returns_windows_adapter_on_win32(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    adapter = get_adapter()
    assert isinstance(adapter, WindowsAdapter)
    assert adapter.supported is True


@pytest.mark.parametrize("adapter_cls", [WindowsAdapter, MacOSAdapter, LinuxAdapter])
def test_every_capability_method_exists_with_matching_signature(adapter_cls):
    for name in _CAPABILITY_METHODS:
        assert hasattr(adapter_cls, name), f"{adapter_cls.__name__} is missing {name}"
        base_sig = inspect.signature(getattr(PlatformAdapter, name))
        sub_sig = inspect.signature(getattr(adapter_cls, name))
        assert base_sig == sub_sig, f"{adapter_cls.__name__}.{name} signature drifted from base"


def test_macos_and_linux_import_cleanly_and_report_unsupported():
    assert MacOSAdapter.supported is False
    assert LinuxAdapter.supported is False


def test_macos_and_linux_stub_methods_raise_not_implemented():
    mac = MacOSAdapter()
    with pytest.raises(NotImplementedError):
        mac.volume_up()
    linux = LinuxAdapter()
    with pytest.raises(NotImplementedError):
        linux.lock()
