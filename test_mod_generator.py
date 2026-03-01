import pytest
from mod_generator import ModGenerator
from config import Config

@pytest.fixture
def generator():
    config = Config()
    return ModGenerator(config)

@pytest.mark.parametrize("mod_id, expected", [
    ("my_mod", "MyMod"),
    ("mod", "Mod"),
    ("my_cool_mod", "MyCoolMod"),
    ("_mod_", "Mod"),
    ("my__mod", "MyMod"),
    ("", ""),
    ("abc_def_ghi", "AbcDefGhi"),
    ("already_PascalCase", "AlreadyPascalcase"), # Note: capitalize() makes the rest lowercase
])
def test_to_class_name(generator, mod_id, expected):
    assert generator._to_class_name(mod_id) == expected
