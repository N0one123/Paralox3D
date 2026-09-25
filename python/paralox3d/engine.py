"""Paralox3D engine and low-boilerplate game loop."""

import ctypes
import inspect
import time
from .clock import _set_dt
from .input import _default_input
from .native import load
from .modes import modes
from .camera import camera
from .input import mouse
from .timing import update as _update_timers

_default_engine = None


def get_default_engine():
    global _default_engine
    if _default_engine is None:
        _default_engine = Engine()
    return _default_engine


class Engine:
    def __init__(self, title="Paralox3D", width=1280, height=720, max_fps=0):
        global _default_engine
        self.title = title
        self.width = width
        self.height = height
        self.max_fps = max_fps
        self._objects = []
        self._update_callback = None
        self._running = False
        self._camera_active = False

        self._native = load()
        self._configure_abi()

        self._engine = self._native.p3d_engine_create(
            width, height, title.encode("utf-8")
        )
        if not self._engine:
            raise RuntimeError("Paralox3D native engine creation failed.")

        if _default_engine is None:
            _default_engine = self

    def _configure_abi(self):
        self._native.p3d_engine_create.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_char_p
        ]
        self._native.p3d_engine_create.restype = ctypes.c_void_p

        self._native.p3d_engine_destroy.argtypes = [ctypes.c_void_p]
        self._native.p3d_engine_destroy.restype = None

        self._native.p3d_entity_create.argtypes = [ctypes.c_void_p]
        self._native.p3d_entity_create.restype = ctypes.c_uint32

        self._native.p3d_entity_set_position.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        self._native.p3d_entity_set_position.restype = None

        self._native.p3d_entity_set_scale.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        self._native.p3d_entity_set_scale.restype = None

        self._native.p3d_entity_set_rotation.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_float,ctypes.c_float,ctypes.c_float]
        self._native.p3d_entity_set_rotation.restype=None
        self._native.p3d_entity_set_color.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_float,ctypes.c_float,ctypes.c_float,ctypes.c_float]
        self._native.p3d_entity_set_color.restype=None
        self._native.p3d_entity_set_enabled.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_int]
        self._native.p3d_entity_set_enabled.restype=None
        self._native.p3d_mouse_state.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_int)]
        self._native.p3d_mouse_state.restype=None

        self._native.p3d_input_key_held.argtypes = [
            ctypes.c_void_p, ctypes.c_int
        ]
        self._native.p3d_input_key_held.restype = ctypes.c_int

        self._native.p3d_engine_step.argtypes = [ctypes.c_void_p]
        self._native.p3d_engine_step.restype = ctypes.c_int

        self._native.p3d_engine_set_developer_overlay.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_float,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        self._native.p3d_engine_set_developer_overlay.restype = None

        self._native.p3d_engine_diagnostics_clicked.argtypes = [ctypes.c_void_p]
        self._native.p3d_engine_diagnostics_clicked.restype = ctypes.c_int

        self._native.p3d_engine_set_debug_colliders.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.c_int]
        self._native.p3d_engine_set_debug_colliders.restype = None

        self._native.p3d_camera_set_enabled.argtypes = [
            ctypes.c_void_p, ctypes.c_int
        ]
        self._native.p3d_camera_set_enabled.restype = None

        self._native.p3d_camera_set_transform.argtypes = [
            ctypes.c_void_p,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        self._native.p3d_camera_set_transform.restype = None

    def _create_entity(self):
        return self._native.p3d_entity_create(self._engine)

    def _set_position(self, handle, position):
        self._native.p3d_entity_set_position(
            self._engine, handle, position.x, position.y, position.z
        )

    def _set_scale(self, handle, scale):
        self._native.p3d_entity_set_scale(
            self._engine, handle, scale.x, scale.y, scale.z
        )

    def register(self, obj):
        if obj not in self._objects:
            self._objects.append(obj)
        return obj

    def update(self):
        if self._update_callback:
            self._update_callback()
        for obj in tuple(self._objects):
            obj._update_components()

    def start(self, update=None):
        if update is not None:
            self._update_callback = update

        self._running = True
        previous = time.perf_counter()
        fps = 0.0

        while self._running:
            engine_ptr = ctypes.c_void_p(self._engine)

            camera_enabled = bool(modes.camera)
            self._native.p3d_camera_set_enabled(
                engine_ptr, int(camera_enabled)
            )

            if camera_enabled and (camera._dirty or not self._camera_active):
                self._native.p3d_camera_set_transform(
                    engine_ptr,
                    camera.x,
                    camera.y,
                    camera.z,
                    camera.pitch,
                    camera.yaw,
                    camera.roll,
                )
                camera._clear_dirty()

            self._camera_active = camera_enabled

            if not self._native.p3d_engine_step(engine_ptr):
                break

            now = time.perf_counter()
            frame_dt = now - previous
            previous = now
            _set_dt(frame_dt)

            if frame_dt > 0:
                instant_fps = 1.0 / frame_dt
                fps = (
                    instant_fps
                    if fps == 0.0
                    else fps * 0.9 + instant_fps * 0.1
                )

            self._native.p3d_engine_set_developer_overlay(
                engine_ptr,
                int(modes.developer),
                len(self._objects),
                fps,
                b"Running game loop",
                0,
            )

            if modes.developer:
                values = []
                for obj in self._objects:
                    minimum, maximum = obj.collider.min, obj.collider.max
                    values.extend((minimum.x, minimum.y, minimum.z, maximum.x, maximum.y, maximum.z))
                bounds = (ctypes.c_float * len(values))(*values) if values else None
                self._native.p3d_engine_set_debug_colliders(engine_ptr, bounds, len(self._objects))
            else:
                self._native.p3d_engine_set_debug_colliders(engine_ptr, None, 0)

            _default_input._sync(
                lambda key_code: self._native.p3d_input_key_held(
                    engine_ptr, key_code
                )
            )

            self.update()
            _default_input._end_frame()

            if self.max_fps:
                target = 1.0 / self.max_fps
                if frame_dt < target:
                    time.sleep(target - frame_dt)

    def run(self):
        self.start()

    def close(self):
        global _default_engine
        if self._engine:
            self._native.p3d_engine_destroy(
                ctypes.c_void_p(self._engine)
            )
            self._engine = None
            self._running = False

            if _default_engine is self:
                _default_engine = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def start(**engine_options):
    engine = get_default_engine()

    if engine_options:
        raise TypeError(
            "Use Engine(...) for custom options; "
            "start() is the zero-boilerplate default."
        )

    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    callback = caller.f_globals.get("update") if caller else None

    engine.start(callback if callable(callback) else None)
