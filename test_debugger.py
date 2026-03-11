import pytest
from debugger import AIDebugger
from config import Config

@pytest.fixture
def debugger():
    config = Config()
    return AIDebugger(config)

def test_parse_errors_empty(debugger):
    assert debugger._parse_errors("") == []

def test_parse_errors_no_errors(debugger):
    output = "Building project...\nSuccess!"
    assert debugger._parse_errors(output) == []

def test_parse_errors_single_error(debugger):
    output = "Main.java:10: error: cannot find symbol"
    assert debugger._parse_errors(output) == ["Main.java:10: error: cannot find symbol"]

def test_parse_errors_multiple_patterns(debugger):
    output = """
    > Task :compileJava FAILED
    /src/main/java/Mod.java:5: error: incompatible types
    symbol not found: class MyItem
    BUILD FAILED in 2s
    """
    errors = debugger._parse_errors(output)
    assert len(errors) == 4
    assert "> Task :compileJava FAILED" in errors
    assert "/src/main/java/Mod.java:5: error: incompatible types" in errors
    assert "symbol not found: class MyItem" in errors
    assert "BUILD FAILED in 2s" in errors

def test_parse_errors_strips_whitespace(debugger):
    output = "   error: leading and trailing spaces   "
    assert debugger._parse_errors(output) == ["error: leading and trailing spaces"]

def test_parse_errors_limit_30(debugger):
    output = "\n".join([f"error: line {i}" for i in range(50)])
    errors = debugger._parse_errors(output)
    assert len(errors) == 30
    assert errors[0] == "error: line 0"
    assert errors[29] == "error: line 29"

@pytest.mark.parametrize("pattern", [
    "error:", "ERROR:", ": error",
    "cannot find symbol", "incompatible types",
    "does not override", "unreachable statement",
    "BUILD FAILED", "Task :compileJava FAILED",
    "Execution failed", "symbol not found"
])
def test_parse_errors_all_patterns(debugger, pattern):
    output = f"Some prefix {pattern} some suffix"
    assert debugger._parse_errors(output) == [f"Some prefix {pattern} some suffix"]
