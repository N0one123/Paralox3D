"""Paralox3D's offline mini-AI error analyzer.

This module uses Python's standard library plus Paralox3D runtime knowledge.
It never needs an internet connection or an external AI service.
"""

import ast
import difflib
import linecache
import os
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

_SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "build", "dist",
    ".mypy_cache", ".pytest_cache", "node_modules",
    ".tox", ".nox", "pypitest", "site-packages", "Scripts",
    "bin", "include", "lib", "Lib",
}


def _project_python_files(filename):
    """Find the user's project Python files for offline static analysis."""
    if not filename:
        return []
    try:
        current = os.path.dirname(os.path.abspath(filename))
        root = None
        for _ in range(6):
            if any(os.path.exists(os.path.join(current, marker))
                   for marker in (".git", "pyproject.toml", "setup.py", "setup.cfg")):
                root = current
                break
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        root = root or os.path.dirname(os.path.abspath(filename))

        result = []
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]
            for name in files:
                if name.endswith(".py"):
                    result.append(os.path.join(base, name))
                    if len(result) >= 250:
                        return result
        return result
    except Exception:
        return []


def _static_project_evidence(error):
    """Use project source to distinguish typos from real scope errors."""
    location = _exception_location(error)
    name = getattr(error, "name", None)
    if location is None or not name:
        return []

    definitions = {}
    for path in _project_python_files(location[0]):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except (OSError, UnicodeError, SyntaxError):
            continue

        class Visitor(ast.NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    definitions.setdefault(node.id, []).append((path, node.lineno, "variable"))
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                definitions.setdefault(node.name, []).append((path, node.lineno, "function"))
                self.generic_visit(node)

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_ClassDef(self, node):
                definitions.setdefault(node.name, []).append((path, node.lineno, "class"))
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    value = alias.asname or alias.name.split(".")[0]
                    definitions.setdefault(value, []).append((path, node.lineno, "import"))
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    value = alias.asname or alias.name
                    definitions.setdefault(value, []).append((path, node.lineno, "import"))
                self.generic_visit(node)

        Visitor().visit(tree)

    evidence = []
    if name in definitions:
        for path, line, kind in definitions[name][:2]:
            _add_reason(evidence, f"'{name}' is defined at {path}, line {line}, but the failing code cannot see that definition from its current scope.")
    else:
        matches = difflib.get_close_matches(name, list(definitions), n=5, cutoff=0.70)
        same_file = [match for match in matches if any(path == location[0] for path, _, _ in definitions[match])]
        ordered = same_file + [match for match in matches if match not in same_file]
        for match in ordered[:3]:
            path, line, kind = definitions[match][0]
            _add_reason(evidence, f"'{name}' is not defined here, but '{match}' is defined in the project at {path}, line {line}; this is a likely naming typo.")
        if name.endswith("s") and name[:-1] in definitions:
            singular = name[:-1]
            path, line, kind = definitions[singular][0]
            _add_reason(evidence, f"'{name}' is the plural form of '{singular}', which is defined at {path}, line {line}; check whether the extra 's' was accidental.")
    return evidence[:8]


_P3D_TERMS = (
    "Object", "Entity", "Collider", "Collision", "find", "find_all",
    "find_with_tag", "find_by_id", "destroy", "disable", "enable",
    "collider", "position", "rotation", "scale", "model", "color",
    "visible", "Scene", "Controller", "CharacterController", "raycast",
    "boxcast", "spherecast", "overlap_box", "overlap_sphere", "Timer",
    "after", "every",
)


def _is_internal_path(filename):
    try:
        package_root = os.path.normcase(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        candidate = os.path.normcase(os.path.abspath(filename))
        return os.path.commonpath([package_root, candidate]) == package_root
    except Exception:
        return False


def _exception_location(error):
    tb = error.__traceback__
    if tb is None:
        return None
    frames = traceback.extract_tb(tb)
    if not frames:
        return None

    candidates = [f for f in frames if not _is_internal_path(f.filename)]
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
        if not _is_internal_path(frame.f_code.co_filename):
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


def _python_name_suggestion(error):
    """Return Python's own NameError suggestion when available."""
    if not isinstance(error, NameError):
        return None
    marker = "Did you mean: '"
    message = str(error)
    if marker not in message:
        return None
    return message.split(marker, 1)[1].split("'", 1)[0]


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
            last_action = getattr(value, "_last_action", None)
            if destroyed:
                detail = f"{variable} refers to Object '{name}', and that Object is marked destroyed."
                if last_action:
                    detail += f" Its last recorded lifecycle action was {last_action}."
                evidence.append(detail)
            elif collider is None:
                detail = f"{variable} refers to Object '{name}', but its collider is currently missing."
                if last_action:
                    detail += f" Its last recorded lifecycle action was {last_action}."
                evidence.append(detail)
            elif enabled is False:
                detail = f"{variable} refers to Object '{name}', and it is currently disabled."
                if last_action:
                    detail += f" Its last recorded lifecycle action was {last_action}."
                evidence.append(detail)
        except Exception:
            continue
    return evidence


def _analysis(error):
    """Build focused conclusions from the error, source, and live runtime."""
    location = _exception_location(error)
    source = location[3] if location else ""
    context = _source_context(error)
    context_lower = context.lower()
    message = str(error).strip()
    runtime = _runtime_evidence(error)
    what_happened = None
    likely = []
    fixes = []

    if isinstance(error, RuntimeError) and "Collision() cannot use destroyed Object" in message:
        match = re.search(r"destroyed Object ['\"](.+?)['\"] for ([ab])", message)
        object_name = match.group(1) if match else "the Object"
        what_happened = f"Collision() was called with '{object_name}', but {object_name} has already been destroyed."
        likely.extend([
            f"{object_name}.destroy() was called before this collision check.",
            f"The collision check is still running after '{object_name}' was destroyed.",
        ])
        fixes.extend([
            f"Check where '{object_name}' is destroyed and stop collision processing for it afterward.",
            "Move the collision check so it only runs while the involved Objects are still alive.",
        ])
    elif isinstance(error, RuntimeError) and "Collision() cannot use Object" in message and "collider is missing" in message:
        match = re.search(r"Object ['\"](.+?)['\"]", message)
        object_name = match.group(1) if match else "the Object"
        what_happened = f"Collision() was called with '{object_name}', but that Object no longer has a Collider."
        likely.append(f"The Collider is unavailable for '{object_name}'.")
        fixes.append(f"Check the lifecycle of '{object_name}' before passing it to Collision().")
    elif isinstance(error, AttributeError) and ("nonetype" in message.lower() or "none" in message.lower()):
        destroyed = [x for x in runtime if "marked destroyed" in x]
        missing = [x for x in runtime if "collider is currently missing" in x]
        if destroyed:
            what_happened = "An Object reference is being used after the Object was destroyed."
            likely.append("A previous destroy() call left the reference pointing to an Object whose engine state is no longer live.")
            fixes.append("Stop using that Object after destroy(), or keep the operation inside the Object's active lifetime.")
        elif missing:
            what_happened = "Code is trying to use an Object whose Collider is no longer available."
            likely.append("The Object was likely destroyed before this operation reached it.")
            fixes.append("Check the Object's lifecycle before using its Collider or collision-related properties.")
        elif re.search(r"\bfind(?:_all|_with_tag|_by_id)?\s*\(", context_lower):
            what_happened = "A lookup returned None, and the code then tried to use it as an Object."
            likely.append("The requested Object may not exist or may no longer be registered in the scene.")
            fixes.append("Check the result of the find operation before accessing its properties.")

    py, p3d, code = [], [], []
    if isinstance(error, AttributeError) and ("nonetype" in message.lower() or "none" in message.lower()):
        _add_reason(py, "A function, lookup, or previous assignment produced None instead of the object you expected.")
    elif isinstance(error, NameError):
        _add_reason(py, "Python could not resolve the name in the current scope.")
        name = getattr(error, "name", None)
        python_suggestion = _python_name_suggestion(error)
        static = _static_project_evidence(error)

        if python_suggestion:
            what_happened = (
                f"Python could not find '{name}'. Python itself suggests "
                f"'{python_suggestion}', which is a strong indication of a naming typo."
            )
            likely.append(
                f"'{name}' is not defined, and Python suggests '{python_suggestion}'."
            )
            _add_reason(
                code,
                f"Python's NameError analysis suggests '{python_suggestion}' "
                f"as the intended name for '{name}'."
            )

        if static:
            if python_suggestion:
                for item in static:
                    if f"'{python_suggestion}'" in item:
                        _add_reason(code, item)
                        likely.append(item)
            else:
                likely.extend(static[:3])
                for item in static[:3]:
                    _add_reason(code, item)
            fixes.extend([
                f"Check every definition and use of '{name}' across the project, especially similarly named variables.",
                "Fix the name or scope at the source rather than adding another variable just to silence the error.",
            ])
            for item in static:
                _add_reason(code, item)
        elif name:
            words = re.findall(r"\b[A-Za-z_]\w*\b", context)
            matches = difflib.get_close_matches(name, words, n=3, cutoff=0.75)
            if matches:
                likely.append(f"Nearby code contains similar name(s): {', '.join(matches)}.")
                _add_reason(code, f"'{name}' looks similar to nearby name(s): {', '.join(matches)}.")
    elif isinstance(error, TypeError):
        if "'tuple' object is not callable" in message.lower():
            what_happened = "Code tried to call a tuple as if it were a function."
            likely.append("The name before the parentheses is holding a tuple value, not a callable function or method.")
            color_call = re.search(r"([A-Za-z_]\w*)\.color\s*\(([^)]*)\)", source)
            if color_call:
                object_var = color_call.group(1)
                argument = color_call.group(2).strip() or "the supplied value"
                likely.append(
                    f"In this line, '{object_var}.color' is a property containing an RGB tuple, "
                    f"so '{object_var}.color({argument})' tries to call that tuple."
                )
                fixes.append(f"Use '{object_var}.color = {argument}' instead of '{object_var}.color({argument})'.")
                fixes.append("Use parentheses for methods and '=' for properties.")
            else:
                fixes.append("Check the value immediately before the parentheses and use assignment if it is a property rather than a method.")
        else:
            _add_reason(py, "A function, operator, or constructor received an argument or value it does not accept.")
    elif isinstance(error, ValueError):
        _add_reason(py, "The value has an acceptable general type, but its actual value is invalid for this operation.")
    elif not what_happened:
        _add_reason(py, "The operation reached a state or value that Python could not use as requested.")

    p3d_signal = any(term.lower() in context_lower for term in _P3D_TERMS) or "paralox3d" in message.lower()
    if p3d_signal and not what_happened:
        if "destroy" in context_lower:
            _add_reason(p3d, "An Object may have been destroyed before another part of the game tried to use it.")
        if re.search(r"\bfind(?:_all|_with_tag|_by_id)?\s*\(", context_lower):
            _add_reason(p3d, "A find operation can return None or no matching Objects when the requested Object does not exist.")
        if "collider" in context_lower:
            _add_reason(p3d, "A Collider can disappear when its Object is destroyed, so collision code should use a live Object.")
        if "disable" in context_lower or ".enabled" in context_lower:
            _add_reason(p3d, "An Object may be disabled, or it may have been destroyed rather than merely disabled.")
        if any(x in context_lower for x in ("collision", "raycast", "boxcast", "spherecast", "overlap_")) and not ("'tuple' object is not callable" in message.lower()):
            _add_reason(p3d, "A spatial query should only receive live, valid Objects.")
        for item in runtime:
            _add_reason(p3d, item)

    if "'tuple' object is not callable" in message.lower() and re.search(r"\.color\s*\(", source):
        _add_reason(p3d, "Object.color is a property that stores an RGB tuple, not a callable method.")
        _add_reason(p3d, "Paralox3D properties are assigned with '=', while methods are invoked with '()'.")

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

    for item in runtime:
        if "marked destroyed" in item and not any(item == x for x in likely):
            likely.append(item)

    return what_happened, likely[:4], fixes[:3], py[:3], p3d[:6], code[:5]


def _possible_reasons(error):
    """Return categorized possibilities for compatibility with the public analyzer."""
    _, _, _, py, p3d, code = _analysis(error)
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

    what_happened, likely, fixes, _, _, _ = _analysis(error)
    runtime = _runtime_evidence(error)
    if what_happened:
        parts.append(f"What happened: {what_happened}")
    if runtime:
        parts.append("What Paralox3D observed:\n" + "\n".join(f"- {item}" for item in runtime))
    if likely:
        parts.append("Likely Cause:\n" + "\n".join(f"- {item}" for item in likely))

    reasons = _possible_reasons_text(error)
    if reasons:
        parts.append(reasons)

    if fixes:
        parts.append("Suggested Fix:\n" + "\n".join(f"- {item}" for item in fixes))
    else:
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
