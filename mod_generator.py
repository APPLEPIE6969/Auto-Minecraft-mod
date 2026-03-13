"""
🧠 Mod Generator — Uses Google AI Studio (Gemini) and Jules API
to generate complete Fabric 1.21.11 mod source code.
"""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from config import Config


SYSTEM_PROMPT = """You are an expert Minecraft Fabric mod developer specializing in Minecraft 1.21.11 (Mounts of Mayhem).
You write clean, idiomatic Java code using the Fabric API and Yarn mappings (1.21.11 is the LAST version to use Yarn).

Rules:
- Target: Minecraft 1.21.111, Fabric Loader >=0.16.9, Java 21
- Use modern Fabric API (net.fabricmc.fabric.api.*)
- Use Yarn mappings (net.fabricmc:yarn:1.21.11+build.1:v2)
- Always include proper imports
- Follow Java naming conventions
- Make code functional and complete, not placeholder
- Use Identifier.of(modId, path) — NOT new Identifier() which is removed in 1.21+
- Register items/blocks in the mod initializer
- New in 1.21.11: Spear weapon, Nautilus mob, NautilusArmor, CamelHusk, ZombieHorsemen are available
"""

MC_VERSION = "1.21.11"

# Pre-compiled regex patterns for performance
FILE_BLOCK_PATTERN = re.compile(r"===FILE:\s*(.+?\.java)===\s*\n(.*?)===END===", re.DOTALL)
JAVA_CODE_BLOCK_PATTERN = re.compile(r"```java\s*(.*?)\s*```", re.DOTALL)


class ModGenerator:
    def __init__(self, config: Config):
        self.config = config

    # ─── Public API ───────────────────────────────────────────────────────────

    def suggest_mod_name(self, description: str) -> str:
        prompt = f"""Given this Minecraft mod idea, suggest a short, catchy mod name (2-4 words max, no special chars):
Idea: {description}
Reply with ONLY the mod name, nothing else."""
        response = self._call_gemini(prompt, max_tokens=50)
        name = response.strip().strip('"\'').replace(" ", "_")
        return name if name else "my_mod"

    def generate_mod_code(self, description: str, mod_id: str, mod_name: str, mod_dir: Path) -> list:
        """
        Generates Java source files for the mod. Returns list of created file paths.
        """
        class_name = self._to_class_name(mod_id)
        package = f"com.example.{mod_id}"
        src_dir = mod_dir / f"src/main/java/{package.replace('.', '/')}"
        src_dir.mkdir(parents=True, exist_ok=True)

        prompt = f"""{SYSTEM_PROMPT}

Create a complete Minecraft {MC_VERSION} Fabric mod with the following requirements:
- Mod ID: {mod_id}
- Mod Name: {mod_name}
- Package: {package}
- Main Class: {class_name}Mod
- Description: {description}

Generate ALL necessary Java files. For each file, output it in this exact format:

===FILE: <filename>.java===
<complete java source code>
===END===

Include at minimum:
1. {class_name}Mod.java (main entrypoint implementing ModInitializer)
2. Any additional classes needed for the described functionality

Make the mod FULLY FUNCTIONAL for {MC_VERSION}. Use Fabric API and Yarn mappings."""

        response = self._call_gemini(prompt, max_tokens=4096)
        return self._parse_and_write_files(response, src_dir, mod_id, mod_dir)

    def jules_review(self, mod_dir: Path, source_files: list) -> list:
        """
        Uses Jules API (Google AI coding agent) to review and improve code.
        Returns list of improvement descriptions.
        """
        if not self.config.has_jules:
            print("  ⚠️  Jules API key not set, skipping review")
            return []

        # Read all source files
        code_context = ""
        for sf in source_files:
            try:
                with open(sf) as f:
                    code_context += f"\n\n// === {sf} ===\n" + f.read()
            except:
                pass

        prompt = f"""You are Jules, a Google AI coding agent. Review this Minecraft {MC_VERSION} Fabric mod code for:
1. Correctness (proper API usage, right method signatures for 1.21.11)
2. Best practices
3. Potential runtime errors
4. Missing registrations

Code to review:
{code_context}

List up to 5 specific issues or improvements. Format each as:
ISSUE: <brief description>
FIX: <what to change>

If no issues found, reply: NO_ISSUES"""

        # Jules API uses the same Google AI Studio endpoint
        response = self._call_jules(prompt)
        
        if "NO_ISSUES" in response:
            return []
        
        suggestions = []
        for line in response.split("\n"):
            if line.startswith("ISSUE:"):
                suggestions.append(line[6:].strip())
        
        # Apply fixes if Jules found any
        if suggestions:
            self._apply_jules_fixes(response, source_files, mod_dir)
        
        return suggestions

    # ─── Private Helpers ─────────────────────────────────────────────────────

    def _call_gemini(self, prompt: str, max_tokens: int = 2048) -> str:
        """Call Google AI Studio (Gemini) API."""
        if not self.config.has_gemini:
            print("  ⚠️  Gemini API key not set — using template fallback")
            return self._fallback_template()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.gemini_model}:generateContent?key={self.config.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3
            }
        }
        return self._http_post(url, payload, parser=self._parse_gemini)

    def _call_jules(self, prompt: str) -> str:
        """Call Jules API (uses Google AI Studio endpoint with Jules capabilities)."""
        if not self.config.has_jules:
            return "NO_ISSUES"

        # Jules API v1 — uses the AI Studio endpoint  
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.jules_model}:generateContent?key={self.config.jules_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.1
            },
            "systemInstruction": {
                "parts": [{"text": "You are Jules, Google's AI coding agent. Be precise and technical."}]
            }
        }
        return self._http_post(url, payload, parser=self._parse_gemini)

    def _http_post(self, url: str, payload: dict, parser) -> str:
        """Generic HTTPS POST with JSON payload."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return parser(result)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  ⚠️  API error {e.code}: {body[:300]}")
            return ""
        except Exception as e:
            print(f"  ⚠️  Request failed: {e}")
            return ""

    def _parse_gemini(self, result: dict) -> str:
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return str(result)

    def _parse_and_write_files(self, response: str, src_dir: Path, mod_id: str, mod_dir: Path) -> list:
        """Parse ===FILE: ... ===END=== blocks and write them."""
        created = []
        matches = FILE_BLOCK_PATTERN.findall(response)

        if not matches:
            # Fallback: treat whole response as main class
            main_class = self._to_class_name(mod_id) + "Mod.java"
            # Extract code block if present
            code_match = JAVA_CODE_BLOCK_PATTERN.search(response)
            code = code_match.group(1) if code_match else response
            path = src_dir / main_class
            with open(path, "w") as f:
                f.write(code)
            created.append(str(path))
        else:
            for filename, code in matches:
                filename = filename.strip()
                path = src_dir / filename
                with open(path, "w") as f:
                    f.write(code.strip())
                created.append(str(path))

        return created

    def _apply_jules_fixes(self, jules_response: str, source_files: list, mod_dir: Path):
        """Ask Gemini to apply Jules' suggested fixes."""
        if not source_files:
            return
        try:
            main_file = source_files[0]
            with open(main_file) as f:
                original = f.read()
            
            fix_prompt = f"""Apply these code fixes to the Java file and return the COMPLETE fixed file.
Jules suggested fixes:
{jules_response}

Original file ({main_file}):
```java
{original}
```

Return ONLY the corrected Java code, no explanations."""
            
            fixed_code = self._call_gemini(fix_prompt, max_tokens=2048)
            code_match = JAVA_CODE_BLOCK_PATTERN.search(fixed_code)
            if code_match:
                fixed_code = code_match.group(1)
            
            if fixed_code and len(fixed_code) > 100:
                with open(main_file, "w") as f:
                    f.write(fixed_code)
        except Exception as e:
            print(f"  ⚠️  Could not apply Jules fixes: {e}")

    def _fallback_template(self) -> str:
        """Returns a basic mod template when no API key is available."""
        return """===FILE: ExampleMod.java===
package com.example.example_mod;

import net.fabricmc.api.ModInitializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ExampleMod implements ModInitializer {
    public static final String MOD_ID = "example_mod";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {
        LOGGER.info("Example Mod initialized!");
    }
}
===END==="""

    def _to_class_name(self, mod_id: str) -> str:
        return "".join(word.capitalize() for word in mod_id.split("_"))
