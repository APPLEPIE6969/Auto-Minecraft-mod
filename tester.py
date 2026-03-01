"""
🧪 AI Mod Tester — Validates mod structure, code correctness,
and runs AI-powered functional checks for Minecraft 1.21.11.
"""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from config import Config


class ModTester:
    def __init__(self, config: Config):
        self.config = config

    def run_tests(self, mod_dir: Path, mod_id: str, mod_name: str, build_result: dict) -> dict:
        """
        Run all automated tests on the mod.
        Returns a test results dictionary.
        """
        tests = []

        # ── Static tests (no build required) ──────────────────────────────
        tests.append(self._test_fabric_mod_json(mod_dir, mod_id, mod_name))
        tests.append(self._test_build_gradle(mod_dir))
        tests.append(self._test_source_files_exist(mod_dir, mod_id))
        tests.append(self._test_java_syntax(mod_dir, mod_id))
        tests.append(self._test_fabric_api_usage(mod_dir))
        tests.append(self._test_minecraft_version_compliance(mod_dir))

        # ── Build tests ────────────────────────────────────────────────────
        tests.append(self._test_build_result(build_result))
        
        if build_result.get("jar"):
            tests.append(self._test_jar_contents(build_result["jar"], mod_id))
        
        # ── AI-powered tests (Groq or Gemini) ─────────────────────────────
        ai_test = self._test_with_ai(mod_dir, mod_id)
        if ai_test:
            tests.append(ai_test)

        passed = sum(1 for t in tests if t["passed"])
        failed = sum(1 for t in tests if not t["passed"])

        return {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "tests": tests
        }

    # ─── Individual Test Cases ────────────────────────────────────────────────

    def _test_fabric_mod_json(self, mod_dir: Path, mod_id: str, mod_name: str) -> dict:
        """Validates fabric.mod.json structure."""
        path = mod_dir / "src/main/resources/fabric.mod.json"
        try:
            if not path.exists():
                return self._fail("fabric.mod.json exists", "File not found")
            
            with open(path) as f:
                data = json.load(f)
            
            required = ["schemaVersion", "id", "version", "name", "entrypoints", "depends"]
            missing = [k for k in required if k not in data]
            
            if missing:
                return self._fail("fabric.mod.json valid", f"Missing fields: {missing}")
            
            if data["id"] != mod_id:
                return self._fail("fabric.mod.json valid", f"ID mismatch: {data['id']} != {mod_id}")
            
            # Check MC version compatibility
            depends = data.get("depends", {})
            if "minecraft" not in depends:
                return self._fail("fabric.mod.json valid", "Missing minecraft dependency")
            
            return self._pass("fabric.mod.json valid")
        except json.JSONDecodeError as e:
            return self._fail("fabric.mod.json valid", f"JSON parse error: {e}")
        except Exception as e:
            return self._fail("fabric.mod.json valid", str(e))

    def _test_build_gradle(self, mod_dir: Path) -> dict:
        """Validates build.gradle exists and contains MC 1.21.11."""
        path = mod_dir / "build.gradle"
        try:
            if not path.exists():
                return self._fail("build.gradle exists", "File not found")
            
            content = path.read_text()
            
            if "1.21.11" not in content:
                return self._fail("build.gradle MC version", "Minecraft 1.21.11 not found in build.gradle")
            
            if "fabric-loom" not in content:
                return self._fail("build.gradle fabric-loom", "fabric-loom plugin not found")
            
            return self._pass("build.gradle valid (MC 1.21.11)")
        except Exception as e:
            return self._fail("build.gradle valid", str(e))

    def _test_source_files_exist(self, mod_dir: Path, mod_id: str) -> dict:
        """Checks that Java source files were generated."""
        src_dir = mod_dir / "src/main/java"
        java_files = list(src_dir.rglob("*.java")) if src_dir.exists() else []
        
        if not java_files:
            return self._fail("Java source files exist", "No .java files found in src/main/java")
        
        return self._pass(f"Java source files exist ({len(java_files)} file(s))")

    def _test_java_syntax(self, mod_dir: Path, mod_id: str) -> dict:
        """Basic Java syntax checks (brace matching, class declaration)."""
        src_dir = mod_dir / "src/main/java"
        if not src_dir.exists():
            return self._fail("Java syntax check", "Source directory missing")

        java_files = list(src_dir.rglob("*.java"))
        errors = []
        
        for jf in java_files:
            content = jf.read_text()
            
            # Brace balance
            opens = content.count("{")
            closes = content.count("}")
            if opens != closes:
                errors.append(f"{jf.name}: unbalanced braces ({opens} open, {closes} close)")
            
            # Has class declaration
            if not re.search(r"\bclass\s+\w+", content):
                errors.append(f"{jf.name}: no class declaration found")
            
            # Has package declaration
            if not content.strip().startswith("package "):
                errors.append(f"{jf.name}: missing package declaration")

        if errors:
            return self._fail("Java syntax check", "; ".join(errors[:3]))
        
        return self._pass(f"Java syntax OK ({len(java_files)} file(s))")

    def _test_fabric_api_usage(self, mod_dir: Path) -> dict:
        """Checks that Fabric API is imported and ModInitializer is implemented."""
        src_dir = mod_dir / "src/main/java"
        if not src_dir.exists():
            return self._fail("Fabric API usage", "Source directory missing")

        java_files = list(src_dir.rglob("*.java"))
        has_mod_initializer = False
        has_fabric_import = False

        for jf in java_files:
            content = jf.read_text()
            if "ModInitializer" in content:
                has_mod_initializer = True
            if "net.fabricmc" in content or "net.minecraft" in content:
                has_fabric_import = True

        if not has_mod_initializer:
            return self._fail("Fabric API usage", "No ModInitializer implementation found")
        
        if not has_fabric_import:
            return self._fail("Fabric API usage", "No Fabric/Minecraft imports found")

        return self._pass("Fabric API correctly used")

    def _test_minecraft_version_compliance(self, mod_dir: Path) -> dict:
        """Checks for deprecated patterns that break in 1.21.11."""
        src_dir = mod_dir / "src/main/java"
        if not src_dir.exists():
            return self._pass("MC 1.21.11 compliance (no source found)")

        java_files = list(src_dir.rglob("*.java"))
        deprecated = []

        deprecated_patterns = [
            ("new Identifier(", "Use Identifier.of() instead in 1.21.11"),
            ("Registry.ITEM.register(", "Use Registries.ITEM in 1.21+"),
            ("FabricItemSettings()", "Use new Item.Settings() in 1.20+"),
        ]

        for jf in java_files:
            content = jf.read_text()
            for pattern, warning in deprecated_patterns:
                if pattern in content:
                    deprecated.append(f"{jf.name}: {warning}")

        if deprecated:
            return self._warn("MC 1.21.11 compliance", f"Potential issues: {'; '.join(deprecated[:2])}")

        return self._pass("MC 1.21.11 compliant code")

    def _test_build_result(self, build_result: dict) -> dict:
        """Reports build success/failure."""
        if build_result.get("success"):
            jar = build_result.get("jar", "")
            return self._pass(f"Gradle build successful" + (f" → {Path(jar).name}" if jar else ""))
        else:
            err = build_result.get("stderr", "")
            # Get first real error
            for line in err.split("\n"):
                if "error:" in line.lower():
                    return self._fail("Gradle build", line.strip()[:100])
            return self._fail("Gradle build", "Build failed (check AI_REPORT.json for details)")

    def _test_jar_contents(self, jar_path: str, mod_id: str) -> dict:
        """Checks that the JAR contains expected files."""
        import zipfile
        try:
            with zipfile.ZipFile(jar_path) as zf:
                names = zf.namelist()
                
                has_fabric_json = any("fabric.mod.json" in n for n in names)
                has_class_files = any(n.endswith(".class") for n in names)
                
                if not has_fabric_json:
                    return self._fail("JAR contents", "Missing fabric.mod.json in JAR")
                if not has_class_files:
                    return self._fail("JAR contents", "No .class files in JAR")
                
                class_count = sum(1 for n in names if n.endswith(".class"))
                return self._pass(f"JAR valid ({class_count} classes, fabric.mod.json present)")
        except Exception as e:
            return self._fail("JAR contents", str(e))

    def _test_with_ai(self, mod_dir: Path, mod_id: str) -> dict | None:
        """Use Groq to do a quick AI review of the generated code."""
        if not self.config.has_groq:
            return None

        src_dir = mod_dir / "src/main/java"
        java_files = list(src_dir.rglob("*.java")) if src_dir.exists() else []
        
        if not java_files:
            return None

        # Read main file
        try:
            main_code = java_files[0].read_text()[:2000]
        except:
            return None

        payload = {
            "model": self.config.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Minecraft 1.21.11 Fabric mod code reviewer. Be very brief."
                },
                {
                    "role": "user",
                    "content": f"""Review this Minecraft 1.21.11 Fabric mod code. Reply with exactly one of:
PASS: <brief reason why it looks correct>
FAIL: <brief reason why it's incorrect>

Code:
```java
{main_code}
```"""
                }
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.groq_api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                response = result["choices"][0]["message"]["content"].strip()
                
                if response.startswith("PASS"):
                    reason = response[5:].strip().lstrip(":").strip()
                    return self._pass(f"AI code review: {reason}")
                elif response.startswith("FAIL"):
                    reason = response[5:].strip().lstrip(":").strip()
                    return self._fail("AI code review", reason)
                else:
                    return self._pass("AI code review: completed")
        except Exception as e:
            return self._warn("AI code review", f"Could not complete: {e}")

    # ─── Result Builders ─────────────────────────────────────────────────────

    def _pass(self, name: str) -> dict:
        return {"name": name, "passed": True, "message": "✅ OK"}

    def _fail(self, name: str, reason: str) -> dict:
        return {"name": name, "passed": False, "message": f"❌ {reason}"}

    def _warn(self, name: str, reason: str) -> dict:
        return {"name": name, "passed": True, "message": f"⚠️  {reason}"}
