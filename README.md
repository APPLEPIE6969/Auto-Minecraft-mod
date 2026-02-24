# ⚔️ AI Minecraft Mod Generator

Automatically generate, debug, and test **Minecraft 1.21.11 Fabric mods** ("Mounts of Mayhem") using three AI systems working together.

> ⚠️ **Note:** 1.21.11 is the **last Minecraft version using Yarn mappings**. Future versions (26.x+) will use Mojang Mappings. This system targets 1.21.11 with Yarn.

---

## 🤖 AI Systems

| AI | Provider | Role |
|----|---------|------|
| **Gemini 2.0 Flash** | Google AI Studio | Generates complete Java source code |
| **Jules** | Google (AI coding agent) | Code review & improvement |
| **LLaMA 3.3 70B** | Groq | Ultra-fast auto-debugging (up to 5 iterations) |

---

## 📋 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Orchestrator |
| Java JDK | 21 | Compiling mods (required by 1.21.11) |
| Gradle | 8+ | Build system |
| Fabric Loader | 0.16.9+ | Mod loader |
| Fabric API | 0.139.5+1.21.11 | Auto-configured |
| Minecraft | 1.21.11 (optional) | Testing mods |

---

## 🚀 Quick Start

### 1. Get API Keys

- **Google AI Studio (Gemini)**: https://aistudio.google.com/app/apikey
- **Groq**: https://console.groq.com/keys  
- **Jules**: Uses the same Google AI Studio key (https://jules.google.com)

### 2. Set Environment Variables

```bash
export GEMINI_API_KEY="AIza..."
export GROQ_API_KEY="gsk_..."
export JULES_API_KEY="AIza..."   # Same as Gemini key
```

### 3. Run the Generator

```bash
# Basic usage
python main.py "A magic sword that shoots lightning bolts"

# With custom name and output
python main.py "A new lucky ore that drops random loot" \
  --name "Lucky Ore Mod" \
  --output ./my_mods

# Pass keys directly
python main.py "A backpack item with 18 slots" \
  --gemini-key "AIza..." \
  --groq-key "gsk_..." \
  --jules-key "AIza..."
```

> The system auto-configures: `minecraft=1.21.11`, `fabric-api=0.139.5+1.21.11`, `yarn=1.21.11+build.1`

---

## 🌐 Web Dashboard

Open `dashboard.html` in your browser for a visual interface:
- Enter API keys
- Describe your mod
- See live generation progress
- Preview generated code
- View test results

> The dashboard calls Gemini directly from the browser and shows you the exact CLI command to run for the full build + debug pipeline.

---

## 📁 Project Structure

```
mc_mod_ai/
├── main.py          # 🎯 Main orchestrator — run this
├── mod_generator.py # 🧠 Gemini + Jules code generation
├── debugger.py      # ⚡ Groq auto-debug engine  
├── tester.py        # 🧪 Automated mod validation
├── config.py        # ⚙️  Configuration
├── dashboard.html   # 🌐 Web UI
└── requirements.txt # 📦 Dependencies (stdlib only!)
```

---

## 🔄 Pipeline

```
User Input
    ↓
[1] Gemini → Generate Java source code
    ↓
[2] Jules → Code review + improvements
    ↓
[3] Gradle → Build the mod
    ↓ (if build fails)
[4] Groq → Analyze errors → Fix code → Rebuild (×5 max)
    ↓
[5] Tests → Validate structure, API usage, JAR contents
    ↓
[6] Output → Ready-to-install .jar + AI_REPORT.json
```

---

## 🎮 Generated Mod Structure

```
generated_mods/<mod_id>/
├── src/
│   └── main/
│       ├── java/com/example/<mod_id>/
│       │   └── <ModName>Mod.java   ← AI-generated
│       └── resources/
│           ├── fabric.mod.json
│           └── assets/<mod_id>/lang/en_us.json
├── build/libs/<mod_id>-1.0.0.jar  ← Install this!
├── build.gradle
├── gradle.properties
├── settings.gradle
└── AI_REPORT.json                  ← Full generation report
```

---

## ✅ Automated Tests

1. `fabric.mod.json` validation (schema, required fields)
2. `build.gradle` MC version check (must be 1.21.11)
3. Java source file existence
4. Java syntax (brace balance, class declaration, package)
5. Fabric API usage (ModInitializer, imports)
6. MC 1.21.11 API compliance (deprecated API detection)
7. Gradle build result
8. JAR contents validation
9. **Groq AI code review** (if API key set)

---

## 📝 Example Mods You Can Generate

```bash
python main.py "A magic wand that shoots fireballs on right-click"
python main.py "A new Amethyst Sword with a special AOE attack"
python main.py "Lucky ore that drops random items and has a 5% mob spawn chance"
python main.py "Backpack item with 27 inventory slots you can open anywhere"
python main.py "Gravity gun that lets you pick up and throw blocks"
python main.py "Auto-smelter block that smelts items faster when heated by lava"
```

---

## ⚙️ Configuration

Edit `config.py` or pass CLI args:

```python
Config(
    gemini_model = "gemini-2.0-flash-exp",   # or gemini-1.5-pro
    groq_model   = "llama-3.3-70b-versatile", # or mixtral-8x7b-32768
    max_debug_iterations = 5,
    build_timeout = 300,  # seconds
)
```

---

## 🛠️ Troubleshooting

**Build fails even after 5 debug iterations?**
- Check Java 21 is installed: `java -version`
- Check Gradle is installed: `gradle -version`  
- Run `gradle wrapper` in the mod directory first
- Check the full error in `AI_REPORT.json`

**Gemini returning empty code?**
- Verify API key at https://aistudio.google.com
- Check you haven't exceeded quota

**Groq not fixing errors?**
- Verify API key at https://console.groq.com
- Some errors require manual fixes (e.g. missing Gradle setup)

---

## 📄 License

MIT — generated mods are yours to use freely.
