
import pytest
from pathlib import Path
from main import ModOrchestrator
from config import Config

def test_mod_id_sanitization():
    config = Config(
        gemini_api_key="test",
        groq_api_key="test",
        jules_api_key="test",
        output_dir="./output"
    )
    orchestrator = ModOrchestrator(config)

    # Test cases: (input_name, expected_id)
    test_cases = [
        ("../traversal", "traversal"),
        ("mod name with spaces", "mod_name_with_spaces"),
        ("mod-name-with-dashes", "mod_name_with_dashes"),
        ("mod.with.dots", "modwithdots"),
        ("mod!with@special#chars$", "modwithspecialchars"),
        ("123_mod_name", "123_mod_name"),
        ("MOD_NAME_UPPERCASE", "mod_name_uppercase"),
        ("   ", "generated_mod"), # Edge case: all whitespace
        ("", "generated_mod"),    # Edge case: empty string
        ("---", "generated_mod"), # Edge case: only special chars
    ]

    for input_name, expected_id in test_cases:
        mod_id = orchestrator._sanitize_mod_id(input_name)

        assert mod_id == expected_id

        # Verify no directory separators are left
        assert "/" not in mod_id
        assert "\\" not in mod_id
        assert ".." not in mod_id

def test_path_traversal_prevention():
    config = Config(
        gemini_api_key="test",
        groq_api_key="test",
        jules_api_key="test",
        output_dir="./output"
    )
    orchestrator = ModOrchestrator(config)

    malicious_names = [
        "../../../etc/passwd",
        "/absolute/path",
        "C:\\Windows\\System32",
        "mod_name/../traversal",
    ]

    for name in malicious_names:
        mod_id = orchestrator._sanitize_mod_id(name)

        # Since we've stripped all special chars, mod_id will just be alphanumeric or generated_mod
        assert ".." not in mod_id
        assert "/" not in mod_id
        assert "\\" not in mod_id
