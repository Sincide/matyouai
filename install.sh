#!/bin/bash

# MatYouAI Simple Installation Script
# Installs packages and symlinks dotfiles

set -e

echo "🎨 MatYouAI Installation"
echo "======================="

# Check if running on Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo "❌ Error: This script is for Arch Linux only"
    exit 1
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
    "cursor-bin"
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

# Enable Ollama service
echo "🚀 Starting services..."
sudo systemctl enable ollama
sudo systemctl start ollama

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Reload your shell: exec fish (or exec bash)"
echo "  2. Install AI models: ollama pull llava:7b"
echo "  3. Test theming: matyouai"
echo ""
echo "📁 Dotfiles are symlinked to ~/.config/"
echo "🖼️  Wallpapers copied to ~/Pictures/wallpapers/"
echo "💾 Backup of old configs: $BACKUP_DIR/"
echo "" 