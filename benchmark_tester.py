import time
import shutil
from pathlib import Path
from tester import ModTester
from config import Config

def create_mock_mod(mod_dir: Path, num_files: int):
    src_dir = mod_dir / "src/main/java/com/example/benchmark"
    src_dir.mkdir(parents=True, exist_ok=True)

    # fabric.mod.json
    res_dir = mod_dir / "src/main/resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "fabric.mod.json").write_text('{"schemaVersion": 1, "id": "benchmark", "version": "1.0.0", "name": "Benchmark", "entrypoints": {"main": []}, "depends": {"minecraft": "1.21.11"}}')

    # build.gradle
    (mod_dir / "build.gradle").write_text('plugins { id "fabric-loom" } \n // 1.21.11')

    for i in range(num_files):
        file_path = src_dir / f"TestFile{i}.java"
        content = f"""package com.example.benchmark;

import net.fabricmc.api.ModInitializer;

public class TestFile{i} implements ModInitializer {{
    @Override
    def onInitialize() {{
        System.out.println("Hello {i}");
    }}
}}
"""
        file_path.write_text(content)

def benchmark():
    mod_dir = Path("benchmark_mod")
    if mod_dir.exists():
        shutil.rmtree(mod_dir)

    num_files = 1000
    create_mock_mod(mod_dir, num_files)

    config = Config()
    tester = ModTester(config)

    build_result = {"success": True, "jar": None}

    # Warm up
    tester.run_tests(mod_dir, "benchmark", "Benchmark", build_result)

    start_time = time.time()
    iterations = 5
    for _ in range(iterations):
        tester.run_tests(mod_dir, "benchmark", "Benchmark", build_result)
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Average run_tests time with {num_files} files: {avg_time:.4f} seconds")

    shutil.rmtree(mod_dir)

if __name__ == "__main__":
    benchmark()
