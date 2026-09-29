"""The Paralox3D error engine.

The goal is not to hide Python errors. The goal is to translate them into
human-readable information while also looking for likely causes in the
Paralox3D API and in the user's code.
"""

import difflib
import linecache
import re
import sys
import traceback

try:
    BaseExceptionGroupType = BaseExceptionGroup
except NameError:
    BaseExceptionGroupType = None

class ErrorGroup(Exception):
    """Compatibility container for multiple errors on Python 3.8-3.10."""
    def __init__(self, errors, message="Multiple errors occurred"):
        self.exceptions = tuple(errors)
        super().__init__(message)

from .messages import EXPLANATIONS, SUGGESTIONS

_INSTALLED = False
_PREVIOUS_HOOK = None

_P3D_TERMS = (
    "Object", "Entity", "Collider", "Collision", "find", "find_all",
    "find_with_tag", "find_by_id", "destroy", "disable", "enable",
    "collider", "position", "rotation", "scale", "model", "color",
    "Scene", "Controller", "CharacterController", "raycast", "boxcast",
    "spherecast", "overlap_box", "overlap_sphere", "Timer", "after", "every",
)

def _exception_location(error):
    tb = error.__traceback__
    if tb is None:
        return None
    frames = traceback.extract_tb(tb)
    if not frames:
        return None

    # Prefer the last frame outside the Paralox3D package. This usually points
    # at the user's game rather than at the engine internals.
    candidates = [f for f in frames if "paralox3d" not in f.filename.lower()]
    last = candidates[-1] if candidates else frames[-1]
    source = linecache.getline(last.filename, last.lineno).strip()
    return last.filename, last.lineno, last.name, source

def _details(error):
    location = _exception_location(error)
    if location is None:
        return None
    filename, line, function, source = location
    where = f"{filename}, line {line}"
    if function and function != "<module>":
        where += f", in {function}()"
    if source:
        where += f": {source}"
    return where

def _source_context(error):
    location = _exception_location(error)
    if location is None:
        return ""
    filename, line, _, _ = location
    start = max(1, line - 10)
    end = min(line + 2, linecache.getline(filename, 10**9) and line + 2)
    return "\n".join(linecache.getline(filename, n).strip() for n in range(start, end + 1))

def _specific_message(error):
    message = str(error).strip()
    if isinstance(error, NameError):
        name = getattr(error, "name", None)
        if name:
            return f"The name '{name}' was not defined."
    if isinstance(error, AttributeError):
        name = getattr(error, "name", None)
        if name:
            return f"The attribute '{name}' does not exist on the object you used."
    if isinstance(error, TypeError):
        return message or "Python rejected the operation because the supplied types or arguments were not accepted."
    return message or error.__class__.__name__

def _is_exception_group(error):
    return isinstance(error, ErrorGroup) or (
        BaseExceptionGroupType is not None and isinstance(error, BaseExceptionGroupType)
    )

def _add_reason(reasons, text):
    if text and text not in reasons:
        reasons.append(text)

def _possible_reasons(error):
    """Find plausible causes from Python, Paralox3D, and the user's source."""
    py = []
    p3d = []
    code = []

    message = str(error).lower()
    location = _exception_location(error)
    source = location[3] if location else ""
    context = _source_context(error).lower()

    _add_reason(py, "The value, variable, argument, or operation may not be what Python expects.")
    if isinstance(error, AttributeError) and ("nonetype" in message or "none" in message):
        _add_reason(py, "A function or lookup may have returned None instead of an object.")
        _add_reason(py, "A value may have been replaced with None earlier in the program.")
    elif isinstance(error, NameError):
        _add_reason(py, "A name may be misspelled or may not have been defined before it was used.")
    elif isinstance(error, TypeError):
        _add_reason(py, "An argument may have the wrong type, the wrong name, or the wrong number of arguments.")
    elif isinstance(error, ValueError):
        _add_reason(py, "The value may be outside the range or format accepted by the operation.")

    p3d_signal = any(term.lower() in context for term in _P3D_TERMS)
    if p3d_signal or ("paralox3d" in message):
        if "destroy" in context or "destroy()" in message:
            _add_reason(p3d, "The object may have already been destroyed with destroy(), so its collider or other object state is no longer available.")
        if "find(" in context or "find (" in context or "find_with_tag" in context or "find_by_id" in context:
            _add_reason(p3d, "A find operation may have returned None because the requested object could not be found.")
            _add_reason(p3d, "The requested object's name, tag, or ID may be incorrect, or the object may not exist yet.")
        if "collider" in context:
            _add_reason(p3d, "The object's collider may have been removed or may be unavailable because the object was destroyed.")
        if "disable" in context or "enabled" in context:
            _add_reason(p3d, "The object may have been disabled or removed before another part of the code tried to use it.")
        if any(x in context for x in ("position", "rotation", "scale", "model", "color", "visible", "texture")):
            _add_reason(p3d, "The object reference used by the property operation may no longer refer to a live Paralox3D Object.")
        if "collision" in context or "raycast" in context or "boxcast" in context or "spherecast" in context:
            _add_reason(p3d, "A collision or spatial query may be receiving an invalid, destroyed, or missing object.")

    # Connect the actual failing line to likely Paralox3D mistakes.
    if "destroy()" in source:
        _add_reason(code, "The failing operation is on or immediately around a destroy() call. Check whether the same object is used again afterward.")
    if re.search(r"\b(find|find_all|find_with_tag|find_by_id)\s*\(", source):
        _add_reason(code, "The result of a find operation may be None or an empty collection. Check the result before using it.")
    if "disable()" in source or ".enabled" in source:
        _add_reason(code, "Check whether this object was disabled before the failing operation. If it was removed with destroy(), disabling it does not restore it.")
    if "collider" in source:
        _add_reason(code, "Check that the object still exists before accessing its collider.")
    if "Collision(" in source or "raycast(" in source:
        _add_reason(code, "Check that every Object passed to the collision or query function is still valid.")
    if "None" in source:
        _add_reason(code, "The failing line explicitly involves None, so trace where that value came from.")
    if isinstance(error, NameError):
        name = getattr(error, "name", None)
        if name:
            words = re.findall(r"\b[A-Za-z_]\w*\b", context)
            matches = difflib.get_close_matches(name, words, n=3, cutoff=0.75)
            if matches:
                _add_reason(code, f"The name '{name}' may be a spelling mistake. Similar names nearby: {', '.join(matches)}.")

    return py, p3d, code

def _possible_reasons_text(error):
    py, p3d, code = _possible_reasons(error)
    groups = []
    if py:
        groups.append(("Python", py))
    if p3d:
        groups.append(("Paralox3D", p3d))
    if code:
        groups.append(("Your code", code))
    if not groups:
        return ""
    lines = ["Possible Reasons:"]
    for title, reasons in groups:
        lines.append(f"\n{title}:")
        lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines)

def _explain_single(error, include_context=True):
    error_type = error.__class__.__name__
    explanation = EXPLANATIONS.get(
        error_type,
        "Paralox3D could not classify this error automatically. The original Python message is shown below.",
    )
    specific = _specific_message(error)
    suggestion = SUGGESTIONS.get(
        error_type,
        "Read the Python message and the affected line, then check the object, value, resource, or operation involved.",
    )
    location = _details(error)

    parts = [
        f"What went wrong: {explanation}",
        f"Python says: {specific}",
    ]

    reasons = _possible_reasons_text(error)
    if reasons:
        parts.append(reasons)

    parts.append(f"What to check: {suggestion}")

    if location:
        parts.append(f"Where it happened: {location}")

    if include_context:
        if error.__cause__ is not None:
            parts.append(
                f"Underlying cause: {error.__cause__.__class__.__name__}: "
                f"{str(error.__cause__).strip() or '(no message)'}"
            )
        elif error.__context__ is not None and not error.__suppress_context__:
            parts.append(
                "While handling another error, Python also encountered: "
                f"{error.__context__.__class__.__name__}: "
                f"{str(error.__context__).strip() or '(no message)'}"
            )

    return "\n".join(parts)

def explain_error(error):
    """Return a complete, human-readable explanation for one or many exceptions."""
    if isinstance(error, (list, tuple)):
        error = ErrorGroup(error)

    if not _is_exception_group(error):
        return _explain_single(error)

    errors = list(error.exceptions)
    parts = [
        "Multiple errors occurred during the same operation.",
        f"Error count: {len(errors)}",
    ]
    for index, child in enumerate(errors, 1):
        parts.append(f"\n--- Error {index} of {len(errors)} ---")
        parts.append(explain_error(child))
    return "\n".join(parts)

def _print_header(error):
    print("\n=== Paralox3D Error Engine ===")
    print("Error type: Multiple errors" if _is_exception_group(error) else f"Error type: {error.__class__.__name__}")
    print(explain_error(error))
    print("================================")

def report_error(error, *, traceback_enabled=None):
    if traceback_enabled is None:
        try:
            from ..modes import modes
            traceback_enabled = bool(modes.developer)
        except Exception:
            traceback_enabled = False
    _print_header(error)
    if traceback_enabled:
        print("\nFull Python traceback:")
        traceback.print_exception(type(error), error, error.__traceback__)

def report_errors(errors, *, traceback_enabled=None):
    report_error(ErrorGroup(errors), traceback_enabled=traceback_enabled)

def _uncaught_exception_hook(exc_type, exc_value, exc_traceback):
    if exc_value is None:
        return
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        if _PREVIOUS_HOOK is not None:
            _PREVIOUS_HOOK(exc_type, exc_value, exc_traceback)
        else:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    _print_header(exc_value)
    try:
        from ..modes import modes
        developer = bool(modes.developer)
    except Exception:
        developer = False
    if developer:
        print("\nFull Python traceback:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

def install():
    global _INSTALLED, _PREVIOUS_HOOK
    if _INSTALLED:
        return
    _PREVIOUS_HOOK = sys.excepthook
    sys.excepthook = _uncaught_exception_hook
    _INSTALLED = True
