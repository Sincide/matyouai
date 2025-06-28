#!/bin/bash

# MatYouAI Simple Installation Script (AMD GPU Edition)
# Installs packages, ROCm support, and symlinks dotfiles

set -e

echo "🎨 MatYouAI Installation (AMD GPU)"
echo "=================================="

# Check if running on Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo "❌ Error: This script is for Arch Linux only"
    exit 1
fi

# Check for AMD GPU
echo "🔍 Checking for AMD GPU..."
if ! lspci | grep -i "VGA" | grep -i "AMD\|ATI" > /dev/null; then
    echo "❌ Error: No AMD GPU detected. This script is optimized for AMD GPUs only."
    echo "   For NVIDIA GPUs, you'll need different drivers and CUDA setup."
    echo "   Detected GPUs:"
    lspci | grep -i "VGA"
    exit 1
else
    echo "✅ AMD GPU detected"
    lspci | grep -i "VGA" | grep -i "AMD\|ATI"
fi

# Install yay-bin if not present
if ! command -v yay &> /dev/null; then
    echo "📦 Installing yay-bin..."
    cd /tmp
    git clone https://aur.archlinux.org/yay-bin.git
    cd yay-bin
    makepkg -si --noconfirm
    cd
    rm -rf /tmp/yay-bin
else
    echo "✅ yay already installed"
fi

# System packages (easy to add/remove)
PACKAGES=(
    # Core dependencies
    "python"
    "python-pillow"
    "python-numpy" 
    "python-scikit-learn"
    "python-requests"
    
    # AMD GPU and ROCm support
    "mesa"
    "vulkan-radeon"
    "xf86-video-amdgpu"
    "rocm-core"
    "rocm-hip-runtime"
    "rocm-opencl-runtime"
    
    # Wayland desktop
    "hyprland"
    "waybar"
    "kitty"
    "rofi-wayland"
    "dunst"
    "swww"
    
    # Shell and utilities
    "fish"
    "git"
)

# AUR packages (easy to add/remove)
AUR_PACKAGES=(
    "ollama"
    "python-materialyoucolor-git"
    "python-jinja"
    "rocm-smi-lib"
    "hip-runtime-amd"
)

# Install system packages
echo "📦 Installing system packages..."
for package in "${PACKAGES[@]}"; do
    echo "  Installing: $package"
    sudo pacman -S --noconfirm "$package" || echo "  ⚠️  Failed to install $package"
done

# Install AUR packages
echo "📦 Installing AUR packages..."
for package in "${AUR_PACKAGES[@]}"; do
    echo "  Installing: $package"
    yay -S --noconfirm "$package" || echo "  ⚠️  Failed to install $package"
done

# Create symlinks for dotfiles
echo "🔗 Creating symlinks for dotfiles..."

# Backup existing configs
BACKUP_DIR="$HOME/.config/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Symlink each dotfile directory
for dir in dotfiles/*/; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        target="$HOME/.config/$dirname"
        
        # Skip wallpapers and other non-config directories
        if [[ "$dirname" == "wallpapers" ]]; then
            continue
        fi
        
        # Backup existing config if it exists
        if [ -e "$target" ]; then
            echo "  Backing up existing $dirname to $BACKUP_DIR/"
            mv "$target" "$BACKUP_DIR/"
        fi
        
        # Create symlink
        echo "  Linking: $dir -> $target"
        ln -sf "$(realpath "$dir")" "$target"
    fi
done

# Handle special cases
# Wallpapers directory
WALLPAPER_DIR="$HOME/Pictures/wallpapers"
mkdir -p "$WALLPAPER_DIR"
if [ -d "dotfiles/wallpapers" ]; then
    cp -r dotfiles/wallpapers/* "$WALLPAPER_DIR/" 2>/dev/null || true
fi

# Make scripts executable
chmod +x scripts/matyouai 2>/dev/null || true

# Create bin directory and symlink
mkdir -p "$HOME/.local/bin"
ln -sf "$(realpath scripts/matyouai)" "$HOME/.local/bin/matyouai" 2>/dev/null || true

# Configure fish shell as default
echo "🐟 Configuring fish shell..."

# Add user to render and video groups for GPU access
sudo usermod -a -G render,video "$USER"

# Set fish as default shell
if command -v fish &> /dev/null; then
    echo "  Setting fish as default shell..."
    chsh -s /usr/bin/fish
    
    # Create fish config directory
    mkdir -p ~/.config/fish
    
    # Configure fish environment variables
    cat >> ~/.config/fish/config.fish << 'EOF'

# MatYouAI and ROCm environment
set -gx HSA_OVERRIDE_GFX_VERSION 10.3.0
set -gx ROC_ENABLE_PRE_VEGA 1
set -gx OLLAMA_GPU_DRIVER rocm

# Add ~/.local/bin to PATH
fish_add_path ~/.local/bin

EOF
    
    echo "  ✅ Fish shell configured with AMD GPU support"
else
    echo "  ❌ Fish shell not found - this shouldn't happen!"
    exit 1
fi

# Enable Ollama service
echo "🚀 Starting services..."
sudo systemctl enable ollama
sudo systemctl start ollama

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Reboot system (required for GPU groups, shell change, and ROCm setup)"
echo "  2. After reboot, you'll be using fish shell by default"
echo "  3. Install AI models: ollama pull llava:7b"
echo "  4. Test GPU acceleration: ollama run llava:7b"
echo "  5. Test theming: matyouai"
echo ""
echo "🐟 Fish Shell Setup:"
echo "  • Fish set as default shell"
echo "  • ~/.local/bin added to PATH automatically"
echo "  • ROCm environment variables configured"
echo ""
echo "🎮 AMD GPU Setup:"
echo "  • ROCm environment configured for Ollama"
echo "  • User added to render and video groups"
echo "  • GPU acceleration will work after reboot"
echo ""
echo "📁 Dotfiles are symlinked to ~/.config/"
echo "🖼️  Wallpapers copied to ~/Pictures/wallpapers/"
echo "💾 Backup of old configs: $BACKUP_DIR/"
echo "" 