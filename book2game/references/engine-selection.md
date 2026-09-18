# Engine Selection & Game Studio MCP Compatibility Reference

> Οδηγός επιλογής game engine (Godot, Unreal, Unity, Phaser, Custom) με βάση το είδος, το ύφος, την πλατφόρμα και τη συμβατότητα με τους MCP servers του Claude Code Game Studio.

---

## 1. Κριτήρια Επιλογής Engine

| Engine | Ιδανικό για Είδος | Footprint | Language | Studio MCP Server |
|--------|------------------|-----------|----------|-------------------|
| **Godot 4.x** | Adventure, RPG, Puzzle, 2D/Indie 3D | Ελαφρύ (~50MB) | GDScript / C# | Godot MCP Server (Headless CLI, GUT, Scene Inspector) |
| **Unity** | Action, RPG, Simulation, 3D/2D | Μέτριο (~GB) | C# | Unity MCP Bridge (Editor WebSocket, Playmode Automation) |
| **Unreal Engine 5** | Action-Adventure, High-End 3D, Shooter | Βαρύ (>GB) | C++ / Blueprints | Unreal Remote Execution (Editor Automation, Blueprint Compiling) |
| **Phaser 3 / Web** | Visual Novel, Educational, 2D Puzzle, Browser | Πολύ ελαφρύ (Browser) | JavaScript / TypeScript | Node.js / Playwright MCP (DOM Inspector, E2E testing) |
| **Custom / Python** | Text-based, Strategy, Simulation, Retro | Minimal | Python / C++ | CLI / Subprocess / GDB |

---

## 2. Κανόνες Αντιστοίχισης (Genre → Engine)

1. **Visual Novel / Educational / Narrative-heavy:** Προτείνεται **Phaser 3** ή **Godot 4** (UI Toolkit).
2. **Adventure / Puzzle / 2D Exploration:** Προτείνεται **Godot 4** (εξαιρετικό 2D tilemap, γρήγορο compilation, εύκολος integration με Godot MCP).
3. **Action / Heavy 3D / Open World:** Προτείνεται **Unreal Engine 5** (αν υπάρχει 3D assets/GAS) ή **Unity**.
4. **Strategy / Simulation / Text RPG:** Προτείνεται **Godot 4** (C#) ή **Custom Python**.

---

## 3. Game Studio MCP Integration Requirements

Για να μπορέσουν οι 49 agents του Game Studio να αλληλεπιδράσουν με το engine:
- **Godot:** Απαιτείται εγκατεστημένος Godot 4.x και `godot-mcp` server. Οι agents (`godot-specialist`, `gdscript`) εκτελούν unit tests μέσω GUT (`Godot Unit Test`) και ελέγχουν σκηνές (`.tscn`) μέσω headless CLI.
- **Unity:** Απαιτείται Unity Editor 6+ και Unity MCP Bridge. Οι agents (`unity-specialist`, `dots/ecs`) επικοινωνούν μέσω WebSocket/IPC για playmode automation.
- **Unreal:** Απαιτείται UE 5.x και Python Remote Execution enabled. Οι agents (`unreal-specialist`, `gas`) στέλνουν εντολές μεταγλώττισης και ελέγχου Blueprints.
- **Phaser:** Απαιτείται Node.js και Playwright/Vite. Οι agents ελέγχουν το UI μέσω DOM inspection.
