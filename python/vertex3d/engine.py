"""Vertex3D engine entry point."""

from __future__ import annotations

from .native import load


class Engine:
    def __init__(self, title="Vertex3D", width=1280, height=720):
        self.title = title
        self.width = width
        self.height = height
        self._native = load()
        self._configure_abi()
        self._engine = self._native.v3d_engine_create(
            width, height, title.encode("utf-8")
        )
        if not self._engine:
            raise RuntimeError("Vertex3D native engine creation failed.")

    def _configure_abi(self):
        self._native.v3d_engine_create.argtypes = [
            __import__("ctypes").c_int,
            __import__("ctypes").c_int,
            __import__("ctypes").c_char_p,
        ]
        self._native.v3d_engine_create.restype = __import__("ctypes").c_void_p

        self._native.v3d_engine_destroy.argtypes = [__import__("ctypes").c_void_p]
        self._native.v3d_engine_destroy.restype = None

        self._native.v3d_entity_create.argtypes = [__import__("ctypes").c_void_p]
        self._native.v3d_entity_create.restype = __import__("ctypes").c_uint32

        self._native.v3d_entity_set_position.argtypes = [
            __import__("ctypes").c_void_p,
            __import__("ctypes").c_uint32,
            __import__("ctypes").c_float,
            __import__("ctypes").c_float,
            __import__("ctypes").c_float,
        ]
        self._native.v3d_entity_set_position.restype = None

        self._native.v3d_engine_step.argtypes = [__import__("ctypes").c_void_p]
        self._native.v3d_engine_step.restype = None

    def _create_entity(self):
        return self._native.v3d_entity_create(self._engine)

    def _set_position(self, handle, position):
        self._native.v3d_entity_set_position(
            self._engine, handle, position.x, position.y, position.z
        )

    def run(self):
        while self._native.v3d_engine_step(self._engine) != 0:
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
