import pytest
from pathlib import Path
from tester import ModTester
from config import Config

def test_mod_tester_caching_logic(tmp_path):
    config = Config()
    tester = ModTester(config)

    mod_dir = tmp_path / "test_mod"
    src_dir = mod_dir / "src/main/java/com/example"
    src_dir.mkdir(parents=True)

    # Create mock Java files
    file1 = src_dir / "Main.java"
    file1.write_text("package com.example;\nimport net.fabricmc.api.ModInitializer;\npublic class Main implements ModInitializer {\n    @Override\n    public void onInitialize() {}\n}")

    file2 = src_dir / "Utils.java"
    file2.write_text("package com.example;\npublic class Utils {\n    public static void help() {}\n}")

    # Add unbalanced braces to file3
    file3 = src_dir / "Bad.java"
    file3.write_text("package com.example;\npublic class Bad {\n")

    # Mock other files
    res_dir = mod_dir / "src/main/resources"
    res_dir.mkdir(parents=True)
    (res_dir / "fabric.mod.json").write_text('{"schemaVersion": 1, "id": "test", "version": "1.0.0", "name": "Test", "entrypoints": {"main": []}, "depends": {"minecraft": "1.21.11"}}')
    (mod_dir / "build.gradle").write_text('plugins { id "fabric-loom" } \n // 1.21.11')

    build_result = {"success": True, "jar": None}
    results = tester.run_tests(mod_dir, "test", "Test", build_result)

    # Verify results
    test_names = {t["name"]: t for t in results["tests"]}
    print(f"Test names: {list(test_names.keys())}")

    assert any("Java source files exist" in name for name in test_names)
    assert any("Java syntax" in name for name in test_names)
    assert any("Fabric API" in name for name in test_names)
    assert any("MC 1.21.11 compliant" in name for name in test_names)

def test_mod_tester_empty_src(tmp_path):
    config = Config()
    tester = ModTester(config)

    mod_dir = tmp_path / "empty_mod"
    mod_dir.mkdir()

    # Create resources but no src/main/java
    res_dir = mod_dir / "src/main/resources"
    res_dir.mkdir(parents=True)
    (res_dir / "fabric.mod.json").write_text('{"schemaVersion": 1, "id": "test", "version": "1.0.0", "name": "Test", "entrypoints": {"main": []}, "depends": {"minecraft": "1.21.11"}}')
    (mod_dir / "build.gradle").write_text('plugins { id "fabric-loom" } \n // 1.21.11')

    build_result = {"success": True, "jar": None}
    results = tester.run_tests(mod_dir, "test", "Test", build_result)

    test_names = {t["name"]: t for t in results["tests"]}
    assert not test_names["Java source files exist"]["passed"]
    assert not test_names["Java syntax check"]["passed"]
    assert not test_names["Fabric API usage"]["passed"]
