#!/usr/bin/env bash
# ==============================================================================
# buildgvm (Area51 Ultimate Edition)
# Clont dein Repo, integriert todo.py, kompiliert mit Nuitka & Pyodide-WASM
# ==============================================================================

set -e

BUILD_DIR="dist/area51"
REPOS_DIR="repos_cache"
REPO_URL="https://github.com/M4tth4ck333/google-gaming-ground.git"

echo "🔮 [BUILDGVM-ULTIMATE] Initialisiere Area51 Build-Pipeline..."

# 1. Arbeitsverzeichnisse vorbereiten
rm -rf "$BUILD_DIR" "$REPOS_DIR"
mkdir -p "$BUILD_DIR" "$REPOS_DIR"

# 2. Echtes Git-Repository klonen (`google-gaming-ground`)
echo "📥 [1/4] Klone Repository: $REPO_URL..."
if git clone "$REPO_URL" "$REPOS_DIR/google-gaming-ground"; then
    echo "   -> Repository erfolgreich geklont."
else
    echo "   ⚠️ Konnte Repo nicht klonen (Netzwerk/Auth). Erstelle lokalen Fallback für todo.py."
    mkdir -p "$REPOS_DIR/google-gaming-ground/lab1_setup"
    cat << 'EOF' > "$REPOS_DIR/google-gaming-ground/lab1_setup/todo.py"
# Fallback todo.py für das SystemT Area51 DOM
class TodoRegistry:
    def __init__(self):
        self.tasks = ["Knotentheorie-AST initialisieren", "Pascalsches Dreieck berechnen", "Holographischen Einwahlpunkt setzen"]
    
    def get_tasks_as_json(self):
        import json
        return json.dumps(self.tasks)
EOF
fi

# Überprüfen, ob `todo.py` im geklonten Pfad existiert, sonst Fallback greifen lassen
TODO_PATH="$REPOS_DIR/google-gaming-ground/lab1_setup/todo.py"
if [ ! -f "$TODO_PATH" ]; then
    echo "   ⚠️ lab1_setup/todo.py im Repo nicht gefunden. Generiere Brücken-Modul."
    mkdir -p "$(dirname "$TODO_PATH")"
    echo "class TodoRegistry: tasks = ['Topologie-Sync aktiv']" > "$TODO_PATH"
fi

# 3. Nuitka-Kompilierung (Python zu C++ Extension / WASM-Vorbereitung)
echo "⚡ [2/4] Kompiliere todo.py & Kernlogik mit Nuitka..."
if command -v nuitka &> /dev/null; then
    python3 -m nuitka --module --lto=yes "$TODO_PATH" --output-dir="$BUILD_DIR/nuitka_out"
    echo "   -> Nuitka C-Extension erfolgreich kompiliert."
else
    echo "   ⚠️ Nuitka nicht gefunden. Kopiere Quellcode direkt für Pyodide-Laufzeit."
    cp "$TODO_PATH" "$BUILD_DIR/todo.py"
fi

# Kopiere das gesamte Modul für den Browser-Zugriff
cp "$TODO_PATH" "$BUILD_DIR/todo.py"

# 4. HTML5-Binder-Language & Metakernel-Gateway generieren
echo "🌐 [3/4] Generiere HTML5-Binder & Metakernel-Gateway..."
cat << 'EOF' > "$BUILD_DIR/index.html"
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Area51 - SystemT Runtime & todo.py Integration</title>
    <script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>
    <style>
        body { background-color: #0b0f19; color: #00ffcc; font-family: 'Courier New', monospace; padding: 2rem; }
        .terminal { border: 1px solid #00ffcc; padding: 1.5rem; background: #000; border-radius: 4px; box-shadow: 0 0 15px rgba(0,255,204,0.2); }
        input, button { background: #0b0f19; color: #00ffcc; border: 1px solid #00ffcc; padding: 0.5rem; margin-top: 0.5rem; }
        button:hover { background: #00ffcc; color: #000; cursor: pointer; }
        ul { list-style-type: square; }
    </style>
</head>
<body>
    <div class="terminal">
        <h1>🌌 SystemT Area51 // buildgvm + todo.py</h1>
        <p>Status: <span id="status">Lade `google-gaming-ground/lab1_setup/todo.py` via Pyodide...</span></p>
        <hr style="border-color: #00ffcc;">
        <div>
            <h3>UML-Torrent-DOM & Todo-Registry</h3>
            <button onclick="loadTodoData()">todo.py ausführen & DOM rendern</button>
        </div>
        <ul id="taskList"></ul>
        <pre id="output" style="margin-top: 1rem; color: #fff;"></pre>
    </div>

    <script>
        let pyodide = null;

        async function initRuntime() {
            document.getElementById('status').innerText = 'Initialisiere Pyodide WASM-Kernel...';
            pyodide = await loadPyodide();
            
            // Lade das echte todo.py aus dem Git-Repo-Build
            const response = await fetch('todo.py');
            const code = await response.text();
            await pyodide.runPythonAsync(code);

            document.getElementById('status').innerText = 'Bereit (Area51 Sandbox aktiv)';
            document.getElementById('output').innerText = '>>> todo.py erfolgreich in die VM geladen.';
        }

        async function loadTodoData() {
            try {
                // Instanziiere die TodoRegistry aus todo.py
                const result = await pyodide.runPythonAsync(`
                    registry = TodoRegistry()
                    # Prüfe, ob Methode oder Attribut existiert
                    if hasattr(registry, 'get_tasks_as_json'):
                        registry.get_tasks_as_json()
                    else:
                        str(registry.tasks)
                `);
                document.getElementById('output').innerText = `[Metakernel Gateway ACK] todo.py Output:\n${result}`;
            } catch (err) {
                document.getElementById('output').innerText = `Fehler beim Ausführen von todo.py: ${err.message}`;
            }
        }

        initRuntime();
    </script>
</body>
</html>
EOF

echo "✨ [SUCCESS] Build vollständig! Artefakte bereit in: $BUILD_DIR/"
