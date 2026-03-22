#!/bin/bash

# Configuration
APP_NAME="the-council"
VENV_DIR="$HOME/.the-council-venv"
LOCAL_BIN="$HOME/.local/bin"

echo "========================================================="
echo "    Installing THE COUNCIL AI Research Terminal (Mac)    "
echo "========================================================="

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install it (e.g., 'brew install python') and try again."
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

# Install the package in editable mode from the current directory
echo "Installing dependencies and setting up 'the-council' command..."
pip install -e .

# Create a symlink in ~/.local/bin
mkdir -p "$LOCAL_BIN"

# Check shell and update config
SHELL_CONFIG=""
if [[ "$SHELL" == */zsh ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

# Add ~/.local/bin to PATH if not already present
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    if [ -n "$SHELL_CONFIG" ]; then
        echo "Adding $LOCAL_BIN to your PATH in $SHELL_CONFIG..."
        echo -e "\n# THE COUNCIL binary path\nexport PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_CONFIG"
        echo "Please run 'source $SHELL_CONFIG' or restart your terminal after installation."
    else
        echo "Warning: Could not detect shell config file. Please manually add $LOCAL_BIN to your PATH."
    fi
fi

# Create the binary wrapper that activates venv and runs the app
BINARY_WRAPPER="$LOCAL_BIN/$APP_NAME"
echo "#!/bin/bash" > "$BINARY_WRAPPER"
echo "source $VENV_DIR/bin/activate" >> "$BINARY_WRAPPER"
echo "python3 $(pwd)/main.py \"\$@\"" >> "$BINARY_WRAPPER"
chmod +x "$BINARY_WRAPPER"

# Final check for Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "\n[TIP] Ollama not found. For local models, download it from https://ollama.com/download/mac"
fi

echo "========================================================="
echo "    Installation complete!                               "
echo "    You can now run '$APP_NAME' from anywhere.           "
echo "========================================================="
