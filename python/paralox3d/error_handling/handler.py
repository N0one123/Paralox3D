"""The Paralox3D error engine.

The goal is not to hide Python errors. The goal is to translate them into
human-readable information while keeping the original exception available.
"""

import linecache
import sys
import traceback

# Exception groups were introduced in Python 3.11. Keep compatibility with older Python versions.
BaseExceptionGroup = getattr(__builtins__, "BaseExceptionGroup", None)

from .messages import EXPLANATIONS, SUGGESTIONS

_INSTALLED = False
_PREVIOUS_HOOK = None


def _exception_location(error):
    tb = error.__traceback__
    if tb is None:
        return None

    last = traceback.extract_tb(tb)[-1]
    source = linecache.getline(last.filename, last.lineno).strip()
    return last.filename, last.lineno, source


def _details(error):
    location = _exception_location(error)
    if location is None:
        return None

    filename, line, source = location
    return f"{filename}, line {line}: {source}" if source else f"{filename}, line {line}"


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
    return BaseExceptionGroup is not None and isinstance(error, BaseExceptionGroup)


def _explain_single(error, include_context=True):
    """Explain one exception without expanding an exception group."""
    error_type = error.__class__.__name__
    explanation = EXPLANATIONS.get(
        error_type,
        "Paralox3D could not safely classify this error automatically. "
        "The original Python message is shown below so the problem is still "
        "fully visible.",
    )
    specific = _specific_message(error)
    suggestion = SUGGESTIONS.get(
        error_type,
        "Read the Python message and the affected line, then check the object, "
        "value, resource, or operation involved.",
    )
    location = _details(error)

    parts = [
        f"What went wrong: {explanation}",
        f"Python says: {specific}",
        f"What to check: {suggestion}",
    ]

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
    """Report an exception through the Paralox3D error engine."""
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
    """Install the error engine as Python's uncaught-exception handler."""
    global _INSTALLED, _PREVIOUS_HOOK

    if _INSTALLED:
        return

    _PREVIOUS_HOOK = sys.excepthook
    sys.excepthook = _uncaught_exception_hook
    _INSTALLED = True
