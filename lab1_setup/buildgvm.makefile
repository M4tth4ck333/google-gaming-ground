# =====================================================================
# buildgvm: Area51 Distributed Runtime Compiler
# Bindet C++ (WASM), Python (Pyodide) & HTML5 Binder Language zusammen
# =====================================================================

CXX = emcc
CXXFLAGS = -std=c++17 -O3 \
           -s WASM=1 \
           -s ALLOW_MEMORY_GROWTH=1 \
           -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap", "setValue", "getValue"]' \
           -s EXPORTED_FUNCTIONS='["_malloc", "_free", "_evaluate_topology_kernel"]'

# Verzeichnisse
SRC_DIR = src
INCLUDE_DIR = include
DIST_DIR = dist

# Ziel-Artefakte
TARGET_WASM = $(DIST_DIR)/buildgvm.wasm
TARGET_JS = $(DIST_DIR)/buildg
