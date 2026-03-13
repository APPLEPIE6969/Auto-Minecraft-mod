import pytest
from pathlib import Path
from mod_generator import ModGenerator
from config import Config

class MockConfig(Config):
    @property
    def has_gemini(self): return False
    @property
    def has_jules(self): return False

@pytest.fixture
def generator():
    return ModGenerator(MockConfig())

def test_parse_multiple_files(generator, tmp_path):
    response = """
===FILE: Mod.java===
public class Mod {}
===END===
===FILE: Utils.java===
public class Utils {}
===END===
"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    created = generator._parse_and_write_files(response, src_dir, "test_mod", tmp_path)

    assert len(created) == 2
    assert (src_dir / "Mod.java").read_text() == "public class Mod {}"
    assert (src_dir / "Utils.java").read_text() == "public class Utils {}"

def test_parse_fallback_codeblock(generator, tmp_path):
    response = """
Here is your mod:
```java
public class FallbackMod {}
```
"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    created = generator._parse_and_write_files(response, src_dir, "test_mod", tmp_path)

    assert len(created) == 1
    assert created[0].endswith("TestModMod.java")
    assert (src_dir / "TestModMod.java").read_text() == "public class FallbackMod {}"

def test_parse_fallback_raw(generator, tmp_path):
    response = "public class RawMod {}"
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    created = generator._parse_and_write_files(response, src_dir, "test_mod", tmp_path)

    assert len(created) == 1
    assert (src_dir / "TestModMod.java").read_text() == "public class RawMod {}"
