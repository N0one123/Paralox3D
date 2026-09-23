"""Keyboard input helpers for Paralox3D."""

from __future__ import annotations


_KEY_CODES = {
    **{chr(code): code for code in range(ord("a"), ord("z") + 1)},
    **{str(code): 0x30 + code for code in range(10)},
    "space": 0x20,
    "enter": 0x0D,
    "escape": 0x1B,
    "tab": 0x09,
    "backspace": 0x08,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}


class Input:
    def __init__(self):
        self._keys = set()
        self._pressed = set()

    def _set_key(self, key, down):
        key = str(key).lower()
        if down:
            if key not in self._keys:
                self._pressed.add(key)
            self._keys.add(key)
        else:
            self._keys.discard(key)

    def _sync(self, query):
        """Refresh keyboard state from the native window."""
        for name, key_code in _KEY_CODES.items():
            self._set_key(name, bool(query(key_code)))

    def held(self, key):
        return str(key).lower() in self._keys

    def pressed(self, key):
        return str(key).lower() in self._pressed

    def _end_frame(self):
        self._pressed.clear()


_default_input = Input()


def held(name):
    return _default_input.held(name)


def pressed(name):
    return _default_input.pressed(name)


# Backwards-compatible alias.
def key(name):
    return held(name)
