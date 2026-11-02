"""Runtime modes for Paralox3D."""

class _Modes:
    def __init__(self):
        self._developer = False
        self._camera = False

    @property
    def camera(self) -> bool:
        return self._camera

    @camera.setter
    def camera(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Paralox3D Error: modes.camera must be True or False. " f"Received {type(value).__name__}.")
        self._camera = value

    @property
    def developer(self) -> bool:
        return self._developer

    @developer.setter
    def developer(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(
                "Paralox3D Error: modes.developer must be True or False. "
                f"Received {type(value).__name__}."
            )
        self._developer = value

modes = _Modes()
