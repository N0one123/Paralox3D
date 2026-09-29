"""Human-readable explanations for common Python errors."""

EXPLANATIONS = {
    "NameError": (
        "Python could not find a name you used. This is usually caused by a "
        "misspelled variable, function, class, or import, or by using it before "
        "it was defined."
    ),
    "UnboundLocalError": (
        "A local variable was used before it received a value. Check whether "
        "you assign to that variable inside the function and whether every "
        "path reaches an assignment first."
    ),
    "AttributeError": (
        "Your code tried to use a property or method that the object does not "
        "have. Check the object type and the spelling of the property or method."
    ),
    "TypeError": (
        "Something was given to a function, operator, or object in a form it "
        "does not accept. Check argument names, argument count, and value types."
    ),
    "ValueError": (
        "A value has the right general type, but it is not valid for this "
        "operation. Check its range, format, or allowed values."
    ),
    "KeyError": (
        "Your code requested a dictionary key that does not exist. Check the "
        "key spelling or create the key before reading it."
    ),
    "IndexError": (
        "Your code tried to access an item outside the available range. Check "
        "the sequence length and the index you are using."
    ),
    "ZeroDivisionError": (
        "Your code tried to divide by zero. Make sure the divisor cannot be zero."
    ),
    "FileNotFoundError": (
        "A file or path could not be found. Check the path, filename, and "
        "whether the file exists where the game expects it."
    ),
    "NotADirectoryError": (
        "A path was expected to be a folder, but it is not. Check each part "
        "of the path."
    ),
    "IsADirectoryError": (
        "A file was expected, but the path points to a folder instead."
    ),
    "PermissionError": (
        "Python was not allowed to access this file, folder, device, or other "
        "resource. Check permissions and whether another program is locking it."
    ),
    "FileExistsError": (
        "The program tried to create something that already exists. Check the "
        "path or use the existing resource when appropriate."
    ),
    "OSError": (
        "The operating system rejected an operation. The Python message below "
        "usually contains the specific reason."
    ),
    "ImportError": (
        "Python could not import the requested object. Check the import name "
        "and whether the package exposes that object."
    ),
    "ModuleNotFoundError": (
        "Python could not find a module that your game tried to import. Check "
        "the module name and whether the required package is installed."
    ),
    "RuntimeError": (
        "The program reached an operation that cannot be completed in its "
        "current state. The Python message below identifies the operation."
    ),
    "RecursionError": (
        "A function called itself too deeply. Check for missing base cases or "
        "unexpected recursive calls."
    ),
    "MemoryError": (
        "Python could not allocate enough memory for this operation. Reduce "
        "the amount of data or objects being created, or investigate a memory "
        "leak."
    ),
    "OverflowError": (
        "A calculation produced a value too large for the operation being used."
    ),
    "FloatingPointError": (
        "A floating-point calculation reported an invalid numerical operation. "
        "Check the values and the calculation that produced them."
    ),
    "ArithmeticError": (
        "A mathematical operation failed. Check the values involved in the "
        "calculation."
    ),
    "AssertionError": (
        "An assertion was expected to be true, but it was false. Check the "
        "condition and the values at the point where it failed."
    ),
    "NotImplementedError": (
        "The requested feature or method has not been implemented for this "
        "object or component yet."
    ),
    "StopIteration": (
        "An iterator had no more items, but the code tried to get another one. "
        "Check the loop or iterator handling."
    ),
    "StopAsyncIteration": (
        "An asynchronous iterator had no more items, but the code requested "
        "another one."
    ),
    "EOFError": (
        "Python reached the end of an input source when more input was expected."
    ),
    "UnicodeError": (
        "Text could not be encoded, decoded, or processed using the expected "
        "character encoding. Check the encoding and the text source."
    ),
    "UnicodeDecodeError": (
        "Bytes could not be decoded as the expected text encoding. Check the "
        "file or data encoding."
    ),
    "UnicodeEncodeError": (
        "Text could not be encoded using the selected encoding. Check the "
        "characters and encoding."
    ),
    "UnicodeTranslateError": (
        "Text could not be translated using the selected encoding or translation "
        "operation."
    ),
    "SyntaxError": (
        "Python could not understand the program's syntax. Look at the reported "
        "line and the line just before it for a missing bracket, parenthesis, "
        "quote, comma, or other syntax mistake."
    ),
    "IndentationError": (
        "Python found an invalid indentation level. Check spaces and tabs and "
        "make sure blocks line up consistently."
    ),
    "TabError": (
        "The file mixes tabs and spaces in a way Python cannot interpret. Use "
        "one indentation style consistently."
    ),
    "UnboundLocalError": (
        "A local variable was referenced before it was assigned a value."
    ),
    "ReferenceError": (
        "A reference to an object is no longer valid. Check the object's "
        "lifetime and whether it was destroyed or released."
    ),
}

SUGGESTIONS = {
    "NameError": "Check the spelling and make sure the name is defined before use.",
    "AttributeError": "Check the API documentation for the object's available properties and methods.",
    "TypeError": "Check the constructor or function signature and the type of every argument.",
    "ValueError": "Check the value itself, not just its type.",
    "KeyError": "Print or inspect the available keys before accessing the missing one.",
    "IndexError": "Check the sequence length and make sure the index is between 0 and length - 1.",
    "FileNotFoundError": "Use the correct path and remember that relative paths are based on the process working directory.",
    "PermissionError": "Check file permissions and whether the resource is being used by another program.",
    "ModuleNotFoundError": "Check the import spelling and install the missing dependency if it is external to Paralox3D.",
    "RecursionError": "Look for a recursive function that never reaches its stopping condition.",
    "MemoryError": "Try reducing object counts, texture/data sizes, or other large allocations.",
    "SyntaxError": "Inspect the reported line and the previous line for an unclosed (), [], {}, string, or block.",
    "IndentationError": "Use consistent indentation, preferably four spaces per level.",
    "TabError": "Convert tabs to spaces or spaces to tabs consistently throughout the affected block.",
}
