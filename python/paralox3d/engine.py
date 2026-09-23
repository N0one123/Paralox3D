"""Paralox3D engine and low-boilerplate game loop."""

import ctypes
import inspect
import time
from .input import _default_input
from .native import load
from .modes import modes

_default_engine=None

def get_default_engine():
    global _default_engine
    if _default_engine is None: _default_engine=Engine()
    return _default_engine

class Engine:
    def __init__(self,title="Paralox3D",width=1280,height=720,max_fps=0):
        global _default_engine
        self.title=title; self.width=width; self.height=height; self.max_fps=max_fps
        self._objects=[]; self._update_callback=None; self._running=False
        self._native=load(); self._configure_abi()
        self._engine=self._native.p3d_engine_create(width,height,title.encode("utf-8"))
        if not self._engine: raise RuntimeError("Paralox3D native engine creation failed.")
        if _default_engine is None: _default_engine=self
    def _configure_abi(self):
        self._native.p3d_engine_create.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_char_p]
        self._native.p3d_engine_create.restype=ctypes.c_void_p
        self._native.p3d_engine_destroy.argtypes=[ctypes.c_void_p]; self._native.p3d_engine_destroy.restype=None
        self._native.p3d_entity_create.argtypes=[ctypes.c_void_p]; self._native.p3d_entity_create.restype=ctypes.c_uint32
        self._native.p3d_entity_set_position.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_float,ctypes.c_float,ctypes.c_float]
        self._native.p3d_entity_set_position.restype=None
        self._native.p3d_engine_step.argtypes=[ctypes.c_void_p]; self._native.p3d_engine_step.restype=ctypes.c_int
        self._native.p3d_engine_set_developer_overlay.argtypes=[
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float,
            ctypes.c_char_p, ctypes.c_int
        ]; self._native.p3d_engine_set_developer_overlay.restype=None
        self._native.p3d_engine_diagnostics_clicked.argtypes=[ctypes.c_void_p]
        self._native.p3d_engine_diagnostics_clicked.restype=ctypes.c_int
    def _create_entity(self): return self._native.p3d_entity_create(self._engine)
    def _set_position(self,handle,position):
        self._native.p3d_entity_set_position(self._engine,handle,position.x,position.y,position.z)
    def register(self,obj):
        if obj not in self._objects: self._objects.append(obj)
        return obj
    def update(self,dt):
        if self._update_callback: self._update_callback(dt)
        for obj in tuple(self._objects): obj._update_components(dt)
    def start(self,update=None):
        if update is not None: self._update_callback=update
        self._running=True; previous=time.perf_counter(); fps=0.0
        while self._running and self._native.p3d_engine_step(self._engine):
            now=time.perf_counter(); dt=now-previous; previous=now
            if dt > 0:
                instant_fps = 1.0 / dt
                fps = instant_fps if fps == 0.0 else fps * 0.9 + instant_fps * 0.1
            self._native.p3d_engine_set_developer_overlay(
                self._engine,
                int(modes.developer),
                len(self._objects),
                fps,
                b"Running game loop",
                0,
            )
            self.update(dt); _default_input._end_frame()
            if self.max_fps:
                target=1.0/self.max_fps
                if dt<target: time.sleep(target-dt)
    def run(self): self.start()
    def close(self):
        global _default_engine
        if self._engine:
            self._native.p3d_engine_destroy(self._engine); self._engine=None; self._running=False
            if _default_engine is self: _default_engine=None
    def __del__(self):
        try: self.close()
        except Exception: pass

def start(**engine_options):
    engine=get_default_engine()
    if engine_options: raise TypeError("Use Engine(...) for custom options; start() is the zero-boilerplate default.")
    frame=inspect.currentframe(); caller=frame.f_back if frame else None
    callback=caller.f_globals.get("update") if caller else None
    engine.start(callback if callable(callback) else None)
