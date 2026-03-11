"""
🎮 AI Minecraft Mod Generator — Main Orchestrator
Supports: Google AI Studio (Gemini), Groq, Jules
Target: Minecraft 1.21.111 (Fabric)
"""

import os
import re
import json
import subprocess
import shutil
import time
from pathlib import Path
from mod_generator import ModGenerator
from debugger import AIDebugger
from tester import ModTester
from config import Config

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║        🤖 AI Minecraft Mod Generator — v1.0                 ║
║        Target: Minecraft 1.21.111 (Fabric)                   ║
║        AIs: Gemini + Groq + Jules                           ║
╚══════════════════════════════════════════════════════════════╝
"""

class ModOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.generator = ModGenerator(config)
        self.debugger = AIDebugger(config)
        self.tester = ModTester(config)
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, mod_description: str, mod_name: str = None):
        print(BANNER)
        
        if not mod_name:
            # Use Gemini to suggest a mod name
            mod_name = self.generator.suggest_mod_name(mod_description)
        
        mod_id = self._sanitize_mod_id(mod_name)
        mod_dir = self.output_dir / mod_id
        
        print(f"\n📦 Creating mod: {mod_name} ({mod_id})")
        print(f"📝 Description: {mod_description}\n")

        # ── Step 1: Generate mod scaffold ──────────────────────────────
        print("━" * 60)
        print("🔨 STEP 1: Generating Fabric Mod Scaffold...")
        scaffold = self._create_scaffold(mod_id, mod_name, mod_dir)
        print(f"  ✅ Scaffold created at {mod_dir}")

        # ── Step 2: AI Code Generation (Gemini) ─────────────────────────
        print("\n━" * 60 if True else "")
        print("🧠 STEP 2: Generating Mod Code with Gemini (Google AI Studio)...")
        source_files = self.generator.generate_mod_code(
            description=mod_description,
            mod_id=mod_id,
            mod_name=mod_name,
            mod_dir=mod_dir
        )
        print(f"  ✅ Generated {len(source_files)} source file(s)")
        for f in source_files:
            print(f"     └─ {f}")

        # ── Step 3: Jules Code Review ────────────────────────────────────
        print("\n━" * 60 if True else "")
        print("🔍 STEP 3: Jules API Code Review & Enhancement...")
        jules_suggestions = self.generator.jules_review(mod_dir, source_files)
        if jules_suggestions:
            print(f"  ✅ Jules made {len(jules_suggestions)} improvement(s)")
            for s in jules_suggestions[:3]:
                print(f"     └─ {s}")
        else:
            print("  ✅ Jules: Code looks good!")

        # ── Step 4: Build the mod ────────────────────────────────────────
        print("\n━" * 60 if True else "")
        print("🔧 STEP 4: Building mod with Gradle...")
        build_result = self._build_mod(mod_dir)

        if build_result["success"]:
            print(f"  ✅ Build successful! JAR: {build_result.get('jar', 'unknown')}")
        else:
            print(f"  ❌ Build failed. Starting AI debug loop...")
            # ── Step 4b: Auto-Debug Loop (Groq) ──────────────────────────
            build_result = self._auto_debug_loop(mod_dir, build_result, source_files, max_iterations=5)

        # ── Step 5: AI Testing ───────────────────────────────────────────
        print("\n━" * 60 if True else "")
        print("🧪 STEP 5: AI-Powered Mod Testing...")
        test_results = self.tester.run_tests(mod_dir, mod_id, mod_name, build_result)
        self._print_test_results(test_results)

        # ── Step 6: Final Report ─────────────────────────────────────────
        print("\n━" * 60 if True else "")
        report = self._generate_report(mod_id, mod_name, mod_dir, source_files, test_results, build_result)
        report_path = mod_dir / "AI_REPORT.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Done! Full report saved to: {report_path}")
        print(f"📁 Mod output directory: {mod_dir}")
        if build_result["success"] and build_result.get("jar"):
            print(f"🎮 Install JAR: {build_result['jar']}")
        
        return report

    def _create_scaffold(self, mod_id: str, mod_name: str, mod_dir: Path) -> dict:
        """Creates the standard Fabric mod directory structure."""
        mc_version = "1.21.11"
        java_version = "21"
        fabric_version = "0.16.9+1.21.11"
        fabric_api_version = "0.139.5+1.21.11"

        dirs = [
            f"src/main/java/com/example/{mod_id}",
            f"src/main/resources/assets/{mod_id}/lang",
            f"src/main/resources/assets/{mod_id}/textures",
            f"src/main/resources/data/{mod_id}",
            "gradle/wrapper",
        ]
        for d in dirs:
            (mod_dir / d).mkdir(parents=True, exist_ok=True)

        # fabric.mod.json
        fabric_mod = {
            "schemaVersion": 1,
            "id": mod_id,
            "version": "1.0.0",
            "name": mod_name,
            "description": f"AI-generated mod for Minecraft {mc_version}",
            "authors": ["AI Mod Generator"],
            "license": "MIT",
            "environment": "*",
            "entrypoints": {
                "main": [f"com.example.{mod_id}.{self._to_class_name(mod_id)}Mod"]
            },
            "depends": {
                "fabricloader": ">=0.16.9",
                "fabric-api": f"*",
                "minecraft": f"~{mc_version}",
                "java": f">={java_version}"
            }
        }
        with open(mod_dir / "src/main/resources/fabric.mod.json", "w") as f:
            json.dump(fabric_mod, f, indent=2)

        # build.gradle
        build_gradle = f"""plugins {{
    id 'fabric-loom' version '1.9-SNAPSHOT'
    id 'maven-publish'
}}

version = "1.0.0"
group = "com.example.{mod_id}"

repositories {{
    maven {{ url "https://maven.fabricmc.net/" }}
}}

dependencies {{
    minecraft "com.mojang:minecraft:{mc_version}"
    mappings "net.fabricmc:yarn:{mc_version}+build.1:v2"
    modImplementation "net.fabricmc:fabric-loader:0.16.9"
    modImplementation "net.fabricmc.fabric-api:fabric-api:{fabric_api_version}"
}}

processResources {{
    inputs.property "version", project.version
    filteringCharset "UTF-8"
    filesMatching("fabric.mod.json") {{
        expand "version": project.version
    }}
}}

tasks.withType(JavaCompile).configureEach {{
    it.options.release = {java_version}
}}

java {{
    withSourcesJar()
    sourceCompatibility = JavaVersion.VERSION_{java_version}
    targetCompatibility = JavaVersion.VERSION_{java_version}
}}

jar {{
    from("LICENSE") {{
        rename {{ "${{it}}_${project.archivesBaseName}" }}
    }}
}}
"""
        with open(mod_dir / "build.gradle", "w") as f:
            f.write(build_gradle)

        # settings.gradle
        with open(mod_dir / "settings.gradle", "w") as f:
            f.write(f'rootProject.name = "{mod_id}"\n')

        # gradle.properties
        with open(mod_dir / "gradle.properties", "w") as f:
            f.write(f"""org.gradle.jvmargs=-Xmx1G
minecraft_version={mc_version}
yarn_mappings={mc_version}+build.1
loader_version=0.16.9
fabric_version={fabric_api_version}
mod_version=1.0.0
maven_group=com.example.{mod_id}
archives_base_name={mod_id}
# NOTE: 1.21.11 is the last version using Yarn mappings.
# Future versions (26.x+) will use Mojang Mappings instead.
""")

        # en_us.json lang file
        with open(mod_dir / f"src/main/resources/assets/{mod_id}/lang/en_us.json", "w") as f:
            json.dump({f"mod.{mod_id}.name": mod_name}, f, indent=2)

        return {"mod_id": mod_id, "mod_name": mod_name, "mc_version": mc_version}

    def _build_mod(self, mod_dir: Path) -> dict:
        """Attempt to build the mod. Returns build result dict."""
        # Check if gradle wrapper exists
        gradlew = mod_dir / "gradlew"
        if not gradlew.exists():
            # Try system gradle
            gradle_cmd = ["gradle", "build", "--no-daemon", "--stacktrace"]
        else:
            os.chmod(gradlew, 0o755)
            gradle_cmd = ["./gradlew", "build", "--no-daemon", "--stacktrace"]

        try:
            result = subprocess.run(
                gradle_cmd,
                cwd=mod_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            success = result.returncode == 0
            jar_path = None
            if success:
                jars = list((mod_dir / "build/libs").glob("*.jar"))
                jars = [j for j in jars if "sources" not in j.name]
                jar_path = str(jars[0]) if jars else None

            return {
                "success": success,
                "stdout": result.stdout[-3000:],
                "stderr": result.stderr[-3000:],
                "jar": jar_path,
                "returncode": result.returncode
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Gradle not found. Please install Gradle or run `gradle wrapper` first.",
                "jar": None,
                "returncode": -1
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Build timed out after 5 minutes.",
                "jar": None,
                "returncode": -1
            }

    def _auto_debug_loop(self, mod_dir: Path, build_result: dict, source_files: list, max_iterations: int = 5) -> dict:
        """Groq-powered auto-debug loop."""
        for i in range(max_iterations):
            print(f"\n  🔄 Debug Iteration {i+1}/{max_iterations} (Groq)...")
            
            errors = build_result.get("stderr", "") + build_result.get("stdout", "")
            
            # Read current source files
            source_code = {}
            for sf in source_files:
                try:
                    with open(sf) as f:
                        source_code[sf] = f.read()
                except:
                    pass
            
            fixed_files = self.debugger.fix_errors(
                errors=errors,
                source_files=source_code,
                mod_dir=mod_dir
            )
            
            if not fixed_files:
                print(f"  ⚠️  Groq couldn't fix errors in iteration {i+1}")
                break
            
            print(f"  🔧 Applied fixes to {len(fixed_files)} file(s)")
            
            # Rebuild
            print(f"  🔨 Rebuilding...")
            build_result = self._build_mod(mod_dir)
            
            if build_result["success"]:
                print(f"  ✅ Build succeeded after {i+1} debug iteration(s)!")
                return build_result
            
            print(f"  ❌ Still failing, continuing debug loop...")
            time.sleep(1)

        print(f"  ⚠️  Could not fix all errors after {max_iterations} iterations")
        return build_result

    def _print_test_results(self, results: dict):
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        print(f"  Tests: {passed}/{total} passed | {failed} failed")
        for test in results.get("tests", []):
            icon = "✅" if test["passed"] else "❌"
            print(f"  {icon} {test['name']}: {test['message']}")

    def _generate_report(self, mod_id, mod_name, mod_dir, source_files, test_results, build_result) -> dict:
        return {
            "mod_id": mod_id,
            "mod_name": mod_name,
            "mod_dir": str(mod_dir),
            "mc_version": "1.21.11",
            "loader": "Fabric",
            "source_files": source_files,
            "build": {
                "success": build_result["success"],
                "jar": build_result.get("jar")
            },
            "tests": test_results,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

    def _to_class_name(self, mod_id: str) -> str:
        return "".join(word.capitalize() for word in mod_id.split("_"))

    def _sanitize_mod_id(self, mod_name: str) -> str:
        """
        Sanitize mod_id to prevent path traversal and other injection attacks.
        Only allows lowercase alphanumeric characters and underscores.
        """
        mod_id = mod_name.lower().replace(" ", "_").replace("-", "_")
        mod_id = re.sub(r'[^a-z0-9_]', '', mod_id)
        mod_id = re.sub(r'_+', '_', mod_id).strip('_')

        if not mod_id:
            mod_id = "generated_mod"

        return mod_id


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Minecraft Mod Generator")
    parser.add_argument("description", help="Describe the mod you want to create")
    parser.add_argument("--name", help="Mod name (optional, AI will suggest one)")
    parser.add_argument("--output", default="./generated_mods", help="Output directory")
    parser.add_argument("--gemini-key", default=os.environ.get("GEMINI_API_KEY"), help="Google AI Studio API key")
    parser.add_argument("--groq-key", default=os.environ.get("GROQ_API_KEY"), help="Groq API key")
    parser.add_argument("--jules-key", default=os.environ.get("JULES_API_KEY"), help="Jules API key")
    args = parser.parse_args()

    config = Config(
        gemini_api_key=args.gemini_key or "",
        groq_api_key=args.groq_key or "",
        jules_api_key=args.jules_key or "",
        output_dir=args.output
    )

    orchestrator = ModOrchestrator(config)
    orchestrator.run(args.description, args.name)
