"""Runtime modes for Paralox3D."""

class _Modes:
    def __init__(self):
        self._developer = False

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
