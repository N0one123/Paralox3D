"""Runtime modes for Paralox3D."""

class _Modes:
    def __init__(self):
        self._developer = False
        self._camera = False
        self._low_quality = False

    @staticmethod
    def _validate(name, value):
        if not isinstance(value, bool):
            raise TypeError(
                f"Paralox3D Error: modes.{name} must be True or False. "
                f"Received {type(value).__name__}."
            )

    @property
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, value):
        self._validate("camera", value)
        self._camera = value

    @property
    def developer(self):
        return self._developer

    @developer.setter
    def developer(self, value):
        self._validate("developer", value)
        self._developer = value

    @property
    def low_quality(self):
        """Enable faster rendering with back-face culling and flat cube shading."""
        return self._low_quality

    @low_quality.setter
    def low_quality(self, value):
        self._validate("low_quality", value)
        self._low_quality = value


modes = _Modes()
