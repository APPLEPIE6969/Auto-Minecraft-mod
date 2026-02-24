"""
⚡ AI Debugger — Uses Groq (ultra-fast LLaMA) to analyze build errors
and automatically fix Java source files.
"""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from config import Config


GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

DEBUG_SYSTEM = """You are an expert Minecraft Fabric mod debugger. You specialize in fixing Java compilation errors 
for Minecraft 1.21.11 mods using Fabric API and Yarn mappings (1.21.11+build.1).

Common 1.21.11 issues to watch for:
- NEVER use new Identifier() — must use Identifier.of(modId, path) 
- Use Registries.ITEM / Registries.BLOCK (not Registry.ITEM)
- Item.Settings() constructor changes
- Block.Settings.create() vs copy()
- Registry.register() signature changes  
- fabricloader version must be >=0.16.9
- fabric-api version must be 0.139.5+1.21.11
- 1.21.11 adds: Spear, Nautilus, NautilusArmor, CamelHusk — these are valid new entities/items
- 1.21.11 is the LAST version using Yarn mappings; do NOT use Mojang mappings

When you fix code, always:
1. Fix ALL errors, not just the first one
2. Maintain the original logic/intent
3. Use correct 1.21.11 API signatures
"""


class AIDebugger:
    def __init__(self, config: Config):
        self.config = config

    def fix_errors(self, errors: str, source_files: dict, mod_dir: Path) -> list:
        """
        Analyze build errors with Groq and apply fixes.
        
        Args:
            errors: Combined stderr/stdout from failed build
            source_files: dict of {filepath: source_code}
            mod_dir: Path to mod directory
            
        Returns:
            List of files that were fixed
        """
        if not errors.strip():
            return []

        # Parse specific compiler errors
        error_summary = self._parse_errors(errors)
        
        if not error_summary:
            return []

        fixed_files = []
        
        for filepath, code in source_files.items():
            # Check if this file has errors
            filename = Path(filepath).name
            relevant_errors = [e for e in error_summary if filename in e or filepath in e]
            
            if not relevant_errors:
                # Include all errors for context
                relevant_errors = error_summary[:10]
            
            fixed_code = self._fix_file_with_groq(
                filepath=filepath,
                source_code=code,
                errors="\n".join(relevant_errors),
                all_errors=errors[:2000]
            )
            
            if fixed_code and fixed_code != code and len(fixed_code) > 50:
                try:
                    with open(filepath, "w") as f:
                        f.write(fixed_code)
                    fixed_files.append(filepath)
                    print(f"     🔧 Fixed: {filename}")
                except Exception as e:
                    print(f"     ⚠️  Could not write fix to {filepath}: {e}")

        return fixed_files

    def analyze_errors(self, errors: str) -> str:
        """
        Get a human-readable analysis of build errors.
        Returns a summary string.
        """
        prompt = f"""Analyze these Minecraft Fabric mod build errors and give a brief summary of what's wrong:

{errors[:2000]}

Give a 2-3 sentence summary of the root cause(s). Be concise."""
        
        return self._call_groq_simple(prompt)

    # ─── Private Helpers ─────────────────────────────────────────────────────

    def _fix_file_with_groq(self, filepath: str, source_code: str, errors: str, all_errors: str) -> str:
        """Call Groq to fix a specific Java file."""
        if not self.config.has_groq:
            print("     ⚠️  Groq API key not set, cannot auto-debug")
            return ""

        prompt = f"""Fix the following Minecraft 1.21.11 Fabric mod Java file.

BUILD ERRORS:
{errors}

FULL BUILD OUTPUT (for context):
{all_errors[:1500]}

FILE TO FIX ({filepath}):
```java
{source_code}
```

Return ONLY the complete, corrected Java file. No explanations, no markdown code blocks — just raw Java code."""

        messages = [
            {"role": "system", "content": DEBUG_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, max_tokens=3000)
        
        # Strip markdown if present
        if response:
            code_match = re.search(r"```(?:java)?\s*\n?(.*?)\s*```", response, re.DOTALL)
            if code_match:
                response = code_match.group(1)
        
        return response.strip() if response else ""

    def _parse_errors(self, build_output: str) -> list:
        """Extract meaningful error lines from build output."""
        errors = []
        for line in build_output.split("\n"):
            # Gradle/Java compiler error patterns
            if any(p in line for p in [
                "error:", "ERROR:", ": error", 
                "cannot find symbol", "incompatible types",
                "does not override", "unreachable statement",
                "BUILD FAILED", "Task :compileJava FAILED",
                "Execution failed", "symbol not found"
            ]):
                errors.append(line.strip())
        return errors[:30]  # Limit to avoid token overflow

    def _call_groq(self, messages: list, max_tokens: int = 2048) -> str:
        """Call Groq API with OpenAI-compatible format."""
        if not self.config.has_groq:
            return ""
        
        payload = {
            "model": self.config.groq_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,  # Low temp for precise fixes
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                GROQ_ENDPOINT,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.groq_api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"     ⚠️  Groq API error {e.code}: {body[:200]}")
            return ""
        except Exception as e:
            print(f"     ⚠️  Groq request failed: {e}")
            return ""

    def _call_groq_simple(self, prompt: str) -> str:
        """Convenience wrapper for single-prompt Groq calls."""
        return self._call_groq([{"role": "user", "content": prompt}], max_tokens=256)
