# Paralox3D Error Engine

Paralox3D treats error handling as an engine feature rather than an afterthought.

The error engine translates common Python exceptions into three useful pieces of information.

1. What went wrong
2. What Python actually reported
3. What to check next

It also reports the exact source location when Python provides one.

Normal mode shows the human explanation without overwhelming a beginner with a large traceback.

Developer mode keeps the same explanation and additionally prints the complete Python traceback.

Unknown exceptions are never silently swallowed. Their original type and message are always shown.

The error engine deliberately does not replace KeyboardInterrupt or SystemExit.

Some errors happen before Python can execute Paralox3D at all, such as a syntax error in the main game file. A library cannot intercept those before Python parses the file. Those errors remain Python's responsibility unless the game is launched through a separate Paralox3D validation or runner command.
