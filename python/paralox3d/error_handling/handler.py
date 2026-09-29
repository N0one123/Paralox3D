"""Paralox3D's offline mini-AI error analyzer.

This module uses Python's standard library plus Paralox3D runtime knowledge.
It never needs an internet connection or an external AI service.
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
    "visible", "Scene", "Controller", "CharacterController", "raycast",
    "boxcast", "spherecast", "overlap_box", "overlap_sphere", "Timer",
    "after", "every",
)


def _exception_location(error):
    tb = error.__traceback__
    if tb is None:
        return None
    frames = traceback.extract_tb(tb)
    if not frames:
        return None

    candidates = [f for f in frames if "paralox3d" not in f.filename.lower()]
    last = candidates[-1] if candidates else frames[-1]
    source = linecache.getline(last.filename, last.lineno).strip()
    return last.filename, last.lineno, last.name, source


def _traceback_frame(error):
    """Return the last useful user frame without assuming a specific Python version."""
    tb = error.__traceback__
    if tb is None:
        return None
    candidates = []
    while tb is not None:
        frame = tb.tb_frame
        if "paralox3d" not in frame.f_code.co_filename.lower():
            candidates.append(frame)
        tb = tb.tb_next
    return candidates[-1] if candidates else error.__traceback__.tb_frame


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
    end = line + 2
    lines = []
    for number in range(start, end + 1):
        value = linecache.getline(filename, number)
        if value:
            lines.append(value.rstrip())
    return "\n".join(lines)


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


def _runtime_evidence(error):
    """Inspect the user's live locals for evidence about Paralox3D Objects.

    This is deliberately read-only. It lets the error engine say what it
    actually observed instead of pretending that a guess is certain.
    """
    frame = _traceback_frame(error)
    if frame is None:
        return []
    evidence = []
    try:
        values = list(frame.f_locals.items())
    except Exception:
        return evidence

    for variable, value in values:
        try:
            if not hasattr(value, "_destroyed"):
                continue
            name = getattr(value, "name", variable)
            destroyed = bool(getattr(value, "_destroyed", False))
            collider = getattr(value, "collider", None)
            enabled = getattr(value, "enabled", None)
            if destroyed:
                evidence.append(
                    f"{variable} refers to Object '{name}', and that Object is marked destroyed."
                )
            elif collider is None:
                evidence.append(
                    f"{variable} refers to Object '{name}', but its collider is currently missing."
                )
            elif enabled is False:
                evidence.append(
                    f"{variable} refers to Object '{name}', and it is currently disabled."
                )
        except Exception:
            continue
    return evidence


def _possible_reasons(error):
    """Reason over Python, Paralox3D, source code, and live runtime evidence."""
    py, p3d, code = [], [], []
    message = str(error).lower()
    location = _exception_location(error)
    source = location[3] if location else ""
    context = _source_context(error).lower()
    runtime = _runtime_evidence(error)

    # Keep a useful Python-side explanation, but avoid dumping generic noise.
    if isinstance(error, AttributeError) and ("nonetype" in message or "none" in message):
        _add_reason(py, "A function, lookup, or previous assignment may have produced None instead of the object you expected.")
    elif isinstance(error, NameError):
        _add_reason(py, "A name may be misspelled, out of scope, or used before it was defined.")
        name = getattr(error, "name", None)
        if name:
            words = re.findall(r"\b[A-Za-z_]\w*\b", context)
            matches = difflib.get_close_matches(name, words, n=3, cutoff=0.75)
            if matches:
                _add_reason(code, f"'{name}' looks similar to nearby name(s): {', '.join(matches)}.")
    elif isinstance(error, TypeError):
        _add_reason(py, "A function, operator, or constructor received an argument or value it does not accept.")
    elif isinstance(error, ValueError):
        _add_reason(py, "The value has an acceptable general type, but its actual value is invalid for this operation.")
    else:
        _add_reason(py, "The operation reached a state or value that Python could not use as requested.")

    p3d_signal = any(term.lower() in context for term in _P3D_TERMS) or "paralox3d" in message
    if p3d_signal:
        if "destroy" in context:
            _add_reason(p3d, "An Object may have been destroyed before another part of the game tried to use it.")
        if re.search(r"\bfind(?:_all|_with_tag|_by_id)?\s*\(", context):
            _add_reason(p3d, "A find operation can return None or no matching Objects when the requested Object does not exist.")
        if "collider" in context:
            _add_reason(p3d, "A Collider can disappear when its Object is destroyed, so collision code should use a live Object.")
        if "disable" in context or ".enabled" in context:
            _add_reason(p3d, "An Object may be disabled, or it may have been destroyed rather than merely disabled.")
        if any(x in context for x in ("collision", "raycast", "boxcast", "spherecast", "overlap_")):
            _add_reason(p3d, "A spatial query may be receiving an invalid, destroyed, or missing Object.")
        if runtime:
            for item in runtime:
                _add_reason(p3d, item)

    if "destroy()" in source:
        _add_reason(code, "Check whether the same Object is used again after destroy().")
    if re.search(r"\bfind(?:_all|_with_tag|_by_id)?\s*\(", source):
        _add_reason(code, "Check the result of the find operation before accessing its properties.")
    if "disable()" in source or ".enabled" in source:
        _add_reason(code, "Check whether the Object was disabled or destroyed before this line.")
    if "collider" in source:
        _add_reason(code, "Check that the Object still has a Collider before using it.")
    if any(x in source for x in ("Collision(", "raycast(", "boxcast(", "spherecast(", "overlap_")):
        _add_reason(code, "Check every Object supplied to this collision or spatial query.")
    if "None" in source:
        _add_reason(code, "Trace where the None value on this line came from.")

    return py[:4], p3d[:6], code[:5]


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

    runtime = _runtime_evidence(error)
    if runtime:
        parts.append("What Paralox3D observed:\n" + "\n".join(f"- {item}" for item in runtime))

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
    """Return a human-readable explanation for one or many exceptions."""
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


def _safe_explain(error):
    """The error engine must never replace the original error with its own error."""
    try:
        return explain_error(error)
    except Exception as analyzer_error:
        return (
            "The Paralox3D Error Engine could not complete its analysis.\n"
            f"Original error: {error.__class__.__name__}: {str(error).strip() or '(no message)'}\n"
            f"Analyzer detail: {analyzer_error.__class__.__name__}: "
            f"{str(analyzer_error).strip() or '(no message)'}"
        )


def _print_header(error):
    print("\n=== Paralox3D Error Engine ===")
    try:
        title = "Multiple errors" if _is_exception_group(error) else error.__class__.__name__
    except Exception:
        title = "Unknown error"
    print(f"Error type: {title}")
    print(_safe_explain(error))
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
        try:
            traceback.print_exception(type(error), error, error.__traceback__)
        except Exception:
            pass


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
        try:
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        except Exception:
            pass


def install():
    global _INSTALLED, _PREVIOUS_HOOK
    if _INSTALLED:
        return
    _PREVIOUS_HOOK = sys.excepthook
    sys.excepthook = _uncaught_exception_hook
    _INSTALLED = True
