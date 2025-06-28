#!/bin/bash
"""
MatYouAI Setup Script
Installs dependencies and sets up the MatYouAI theming system
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Arch Linux
check_arch_linux() {
    if [ ! -f /etc/arch-release ]; then
        log_error "This setup script is designed for Arch Linux"
        exit 1
    fi
    log_success "Arch Linux detected"
}

# Check if running in Wayland
check_wayland() {
    if [ -z "$WAYLAND_DISPLAY" ] && [ -z "$XDG_SESSION_TYPE" ]; then
        log_warning "Wayland environment not detected. MatYouAI is designed for Wayland."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Wayland environment detected"
    fi
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Core dependencies
    local DEPS=(
        "python"
        "rofi-wayland"
        "swww"
        "hyprland"
        "python-pillow"          # Image processing
        "python-numpy"           # Scientific computing
        "python-scikit-learn"    # Machine learning
        "python-requests"        # HTTP requests
    )
    
    # Optional dependencies
    local OPTIONAL_DEPS=(
        "waybar"
        "kitty"
        "fish"
        "dunst"
    )
    
    # Install core dependencies
    for dep in "${DEPS[@]}"; do
        if ! pacman -Qi "$dep" >/dev/null 2>&1; then
            log_info "Installing $dep..."
            sudo pacman -S --noconfirm "$dep" || {
                log_error "Failed to install $dep"
                exit 1
            }
        else
            log_info "$dep already installed"
        fi
    done
    
    # Install optional dependencies
    log_info "Installing optional dependencies..."
    for dep in "${OPTIONAL_DEPS[@]}"; do
        if ! pacman -Qi "$dep" >/dev/null 2>&1; then
            log_info "Installing optional dependency: $dep"
            sudo pacman -S --noconfirm "$dep" || {
                log_warning "Failed to install optional dependency: $dep"
            }
        else
            log_info "$dep already installed"
        fi
    done
    
    log_success "System dependencies installed"
}

# Install Ollama (for AI models)
install_ollama() {
    log_info "Checking for Ollama..."
    
    if command -v ollama >/dev/null 2>&1; then
        log_success "Ollama already installed"
        return
    fi
    
    # Check if ollama is available in AUR
    if command -v yay >/dev/null 2>&1; then
        log_info "Installing Ollama via AUR (yay)..."
        yay -S --noconfirm ollama || {
            log_warning "Failed to install via AUR, falling back to direct installation"
            install_ollama_direct
        }
    elif command -v paru >/dev/null 2>&1; then
        log_info "Installing Ollama via AUR (paru)..."
        paru -S --noconfirm ollama || {
            log_warning "Failed to install via AUR, falling back to direct installation"
            install_ollama_direct
        }
    else
        log_info "No AUR helper found, installing directly..."
        install_ollama_direct
    fi
    
    # Start Ollama service
    sudo systemctl enable ollama 2>/dev/null || true
    sudo systemctl start ollama 2>/dev/null || true
    
    log_success "Ollama installed"
    
    # Suggest models to install
    log_info "Consider installing these AI models for better performance:"
    echo "  ollama pull llava:7b          # For image analysis"
    echo "  ollama pull wizardcoder:15b   # For config generation"
    echo "  ollama pull codegemma         # Alternative code model"
    echo ""
    echo "Run these commands after setup completes."
}

# Direct Ollama installation
install_ollama_direct() {
    log_info "Installing Ollama directly..."
    
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh || {
        log_error "Failed to install Ollama"
        exit 1
    }
}

# Setup MatYouAI
setup_matyouai() {
    log_info "Setting up MatYouAI..."
    
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    
    # Create config directory
    local CONFIG_DIR="$HOME/.config/matyouai"
    mkdir -p "$CONFIG_DIR"
    
    # Create default config
    cat > "$CONFIG_DIR/config.json" << EOF
{
    "wallpaper_directories": [
        "$HOME/Pictures/wallpapers",
        "$HOME/Pictures",
        "$HOME/Downloads"
    ],
    "ai_enabled": true,
    "backup_enabled": true,
    "auto_reload_configs": true,
    "preferred_ai_models": {
        "vision": "llava:7b",
        "code": "wizardcoder:15b"
    }
}
EOF
    
    # Make main script executable
    chmod +x "$PROJECT_DIR/scripts/matyouai"
    
    # Create symbolic link for global access
    local BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    
    if [ -L "$BIN_DIR/matyouai" ] || [ -f "$BIN_DIR/matyouai" ]; then
        rm "$BIN_DIR/matyouai"
    fi
    
    ln -s "$PROJECT_DIR/scripts/matyouai" "$BIN_DIR/matyouai"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
        
        # For fish shell
        if command -v fish >/dev/null 2>&1; then
            fish -c "set -U fish_user_paths \$fish_user_paths $BIN_DIR" 2>/dev/null || true
        fi
    fi
    
    log_success "MatYouAI setup completed"
}

# Create sample wallpaper directory
setup_wallpapers() {
    log_info "Setting up wallpaper directories..."
    
    local WALLPAPER_DIR="$HOME/Pictures/wallpapers"
    mkdir -p "$WALLPAPER_DIR"
    
    # Check if directory is empty and suggest downloading wallpapers
    if [ -z "$(ls -A "$WALLPAPER_DIR" 2>/dev/null)" ]; then
        log_info "Wallpaper directory is empty: $WALLPAPER_DIR"
        echo "Consider adding some wallpapers to this directory for testing."
        echo "You can download sample Material You wallpapers from:"
        echo "  https://storage.googleapis.com/gweb-uniblog-publish-prod/images/Android_12_Blog_Header.max-1300x1300.png"
    fi
    
    log_success "Wallpaper directories configured"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Test if matyouai command works
    if command -v matyouai >/dev/null 2>&1; then
        log_success "matyouai command available"
    else
        log_warning "matyouai command not found in PATH"
        echo "You may need to reload your shell or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    
    # Test Python imports
    log_info "Testing Python dependencies..."
    python3 -c "
import sys
try:
    from PIL import Image
    import numpy as np
    import sklearn
    import requests
    print('✅ All Python dependencies available')
except ImportError as e:
    print(f'❌ Missing Python dependency: {e}')
    sys.exit(1)
" || {
        log_error "Python dependencies test failed"
        log_info "Make sure python-pillow, python-numpy, python-scikit-learn, and python-requests are installed"
        exit 1
    }
    
    # Test configuration detection
    log_info "Testing configuration detection..."
    "$HOME/.local/bin/matyouai" detect || {
        log_warning "Configuration detection test failed"
    }
    
    log_success "Installation test completed"
}

# Main setup function
main() {
    echo "================================================"
    echo "         MatYouAI Setup Script"
    echo "   Material You AI-Driven Theming System"
    echo "================================================"
    echo
    
    # Checks
    check_arch_linux
    check_wayland
    
    echo
    log_info "Starting MatYouAI installation..."
    echo
    
    # Install dependencies
    install_system_deps
    
    # Install Ollama if not skipped
    if [ -z "$SKIP_OLLAMA" ]; then
        install_ollama
    fi
    
    # Setup MatYouAI
    setup_matyouai
    setup_wallpapers
    
    # Test
    test_installation
    
    echo
    echo "================================================"
    log_success "MatYouAI installation completed!"
    echo "================================================"
    echo
    echo "Quick start:"
    echo "  1. Reload your shell or run: source ~/.bashrc"
    echo "  2. Install AI models: ollama pull llava:7b"
    echo "  3. Launch theme picker: matyouai pick"
    echo "  4. Check status: matyouai status"
    echo
    echo "All dependencies installed via pacman (no pip/venv needed)!"
    echo
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MatYouAI Setup Script"
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --no-ollama   Skip Ollama installation"
        echo "  --test        Run installation test only"
        exit 0
        ;;
    --no-ollama)
        SKIP_OLLAMA=1
        ;;
    --test)
        test_installation
        exit 0
        ;;
esac

# Run main setup
main "$@" 