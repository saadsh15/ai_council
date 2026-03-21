#!/bin/bash

# Configuration
APP_NAME="the-council"
VENV_DIR="$HOME/.the-council-venv"

echo "===================================================="
echo "    Installing THE COUNCIL AI Research Terminal     "
echo "===================================================="

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install it and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install the package in editable mode
echo "Installing dependencies and setting up binary..."
pip install -e .

# Create a symlink in ~/.local/bin if not already in path
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo "Warning: $LOCAL_BIN is not in your PATH. Adding it to .bashrc..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "Please run 'source ~/.bashrc' or restart your terminal after installation."
fi

# Create the binary wrapper
BINARY_WRAPPER="$LOCAL_BIN/$APP_NAME"
echo "#!/bin/bash" > "$BINARY_WRAPPER"
echo "source $VENV_DIR/bin/activate" >> "$BINARY_WRAPPER"
echo "python3 $(pwd)/main.py \"\$@\"" >> "$BINARY_WRAPPER"
chmod +x "$BINARY_WRAPPER"

echo "===================================================="
echo "    Installation complete!                          "
echo "    You can now run '$APP_NAME' from anywhere.     "
echo "===================================================="
