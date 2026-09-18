"""Paralox3D engine entry point."""

from __future__ import annotations

import ctypes

from .native import load


class Engine:
    def __init__(self, title="Paralox3D", width=1280, height=720):
        self.title = title
        self.width = width
        self.height = height
        self._native = load()
        self._configure_abi()
        self._engine = self._native.v3d_engine_create(
            width, height, title.encode("utf-8")
        )
        if not self._engine:
            raise RuntimeError("Paralox3D native engine creation failed.")

    def _configure_abi(self):
        self._native.v3d_engine_create.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_char_p
        ]
        self._native.v3d_engine_create.restype = ctypes.c_void_p

        self._native.v3d_engine_destroy.argtypes = [ctypes.c_void_p]
        self._native.v3d_engine_destroy.restype = None

        self._native.v3d_entity_create.argtypes = [ctypes.c_void_p]
        self._native.v3d_entity_create.restype = ctypes.c_uint32

        self._native.v3d_entity_set_position.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        self._native.v3d_entity_set_position.restype = None

        self._native.v3d_engine_step.argtypes = [ctypes.c_void_p]
        self._native.v3d_engine_step.restype = ctypes.c_int

    def _create_entity(self):
        return self._native.v3d_entity_create(self._engine)

    def _set_position(self, handle, position):
        self._native.v3d_entity_set_position(
            self._engine, handle, position.x, position.y, position.z
        )

    def run(self):
        while self._native.v3d_engine_step(self._engine):
            pass

    def close(self):
        if self._engine:
            self._native.v3d_engine_destroy(self._engine)
            self._engine = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
