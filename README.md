# MatYouAI 🎨🤖

**Material You AI-Driven Theming System for Arch Linux Wayland**

MatYouAI is an intelligent theming system that automatically extracts Material You-style color palettes from your wallpapers and applies them across your entire Wayland desktop environment using local AI models.

## ✨ Features

### 🎯 Core Capabilities
- **AI-Powered Color Extraction**: Uses local vision models (llava) to analyze wallpapers and extract harmonious color palettes
- **Intelligent Theme Generation**: Employs coding models (wizardcoder, codegemma) to generate configuration patches
- **Material You Compliance**: Follows Google's Material You design principles for color relationships and accessibility
- **Fully Local**: All AI processing happens locally via Ollama - no cloud dependencies

### 🛠 Supported Applications
- **Hyprland** - Window manager colors, borders, shadows, blur effects
- **Waybar** - Status bar theming with CSS generation
- **Rofi** - Application launcher themes
- **Kitty** - Terminal colors and schemes
- **Fish** - Shell prompt and syntax highlighting
- **Dunst** - Notification styling
- **GTK3/GTK4** - System-wide application theming

### 🔧 Smart Features
- **Config Preservation**: Only modifies color-related settings, preserves your custom layouts and keybindings
- **Automatic Detection**: Intelligently finds and analyzes existing configuration files
- **Backup & Versioning**: Creates automatic backups with rollback capability
- **Preview Mode**: See changes before applying them
- **Accessibility**: Ensures proper contrast ratios for readability

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/matyouai.git
cd matyouai

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Install AI models (optional but recommended)
ollama pull llava:7b          # For image analysis
ollama pull wizardcoder:15b   # For config generation
```

> **Note**: MatYouAI uses only system packages via pacman - no pip, venv, or virtual environments needed!

### First Use

```bash
# Launch the wallpaper picker and apply theme
matyouai pick

# Or apply theme from a specific wallpaper
matyouai apply ~/Pictures/my-wallpaper.jpg

# Preview a theme without applying
matyouai preview ~/Pictures/wallpaper.png

# Check current status
matyouai status
```

## 📋 Requirements

### System Requirements
- **OS**: Arch Linux (or Arch-based distributions)
- **Display Server**: Wayland
- **Window Manager**: Hyprland (recommended)
- **Python**: 3.9+

### Dependencies
**Core Dependencies** (installed automatically via pacman):
- `python` - Python runtime
- `rofi-wayland` - Application launcher for wallpaper selection
- `swww` - Wallpaper setter for Wayland
- `hyprland` - Window manager
- `python-pillow` - Image processing fallback
- `python-numpy` - Numerical computations
- `python-scikit-learn` - Color clustering algorithms
- `python-requests` - HTTP requests for AI communication

**Optional Dependencies** (for full functionality):
- `waybar` - Status bar
- `kitty` - Terminal emulator
- `fish` - Shell
- `dunst` - Notification daemon
- `ollama` - Local AI model runner (install via AUR)

## 📖 Usage Guide

### Basic Commands

```bash
# Interactive wallpaper picker
matyouai pick

# Apply theme from wallpaper
matyouai apply /path/to/wallpaper.jpg

# Preview theme changes
matyouai preview /path/to/wallpaper.jpg

# Theme management
matyouai themes              # Show theme switcher
matyouai restore theme_123   # Restore previous theme

# Status and diagnostics
matyouai status              # Show current theme and app status
matyouai detect              # Show detailed config detection
```

### Advanced Options

```bash
# Apply to specific apps only
matyouai apply wallpaper.jpg --apps hyprland kitty

# Custom theme name
matyouai apply wallpaper.jpg --theme-name "Sunset Theme"

# Additional wallpaper directories
matyouai pick --wallpaper-dirs ~/Backgrounds ~/Downloads

# Verbose logging
matyouai pick --verbose

# Disable AI models (use fallback algorithms)
matyouai apply wallpaper.jpg --no-ai
```

## 🏗 Architecture

### Project Structure
```
matyouai/
├── src/
│   ├── core/                    # Core system components
│   │   ├── ai_models.py         # Ollama integration
│   │   ├── color_extractor.py   # AI + fallback color extraction
│   │   ├── config_detector.py   # Smart config file detection
│   │   └── theme_applicator.py  # Main theme application engine
│   ├── apps/                    # App-specific themers
│   │   ├── hyprland.py
│   │   ├── waybar.py
│   │   ├── kitty.py
│   │   └── ...
│   ├── utils/
│   │   └── backup.py            # Backup and versioning system
│   └── wallpaper_picker.py      # Rofi integration
├── scripts/
│   ├── matyouai                 # Main CLI entry point
│   └── setup.sh                 # Installation script
└── docs/                        # Documentation
```

### How It Works

1. **Wallpaper Selection**: Rofi-based picker scans configured directories
2. **Color Analysis**: AI vision model (llava) extracts dominant colors
3. **Palette Generation**: Creates Material You compliant color scheme
4. **Config Detection**: Scans system for application configuration files
5. **Theme Application**: Uses dedicated themers or AI-generated patches
6. **Backup Creation**: Automatically backs up original configurations
7. **Config Reload**: Signals applications to reload their configurations

## 🎨 Theming System

### Material You Principles
MatYouAI follows Material You design guidelines:
- **Dynamic Color**: Palettes derived from wallpaper imagery
- **Tonal Palettes**: Multiple shades and variants of each color
- **Accessibility**: WCAG-compliant contrast ratios
- **Harmony**: Colors that work well together across interfaces

### Color Palette Structure
```json
{
  "primary": "#6750A4",
  "secondary": "#625B71", 
  "background": "#FFFBFE",
  "surface": "#F7F2FA",
  "accent": "#7C4DFF",
  "on_primary": "#FFFFFF",
  "on_secondary": "#FFFFFF",
  "on_background": "#1C1B1F",
  "neutral_10": "#FEFBFF",
  "neutral_90": "#E6E0E9",
  "error": "#BA1A1A",
  "warning": "#F57C00",
  "success": "#4CAF50"
}
```

## 🔧 Configuration

### User Configuration
Config file: `~/.config/matyouai/config.json`

```json
{
  "wallpaper_directories": [
    "~/Pictures/wallpapers",
    "~/Pictures",
    "~/Downloads"
  ],
  "ai_enabled": true,
  "backup_enabled": true,
  "auto_reload_configs": true,
  "preferred_ai_models": {
    "vision": "llava:7b",
    "code": "wizardcoder:15b"
  }
}
```

### Adding Custom App Support
Create a new themer in `src/apps/myapp.py`:

```python
class MyAppThemer:
    def apply_theme(self, color_palette: Dict[str, str], 
                   config_info: Dict, preview_mode: bool = False) -> bool:
        # Implement your theming logic
        pass
```

## 🔄 Backup System

MatYouAI automatically creates versioned backups:
- **File-level**: Individual config file backups
- **Theme-level**: Complete theme snapshots
- **Rollback**: Easy restoration of previous states

```bash
# List available themes
matyouai themes

# Restore specific theme
matyouai restore theme_sunset_20241201_143022

# Manual backup management via Python API
from src.utils.backup import ConfigBackupManager
backup_manager = ConfigBackupManager()
backups = backup_manager.list_backups()
```

## 🤖 AI Integration

### Local AI Models
MatYouAI uses Ollama for local AI processing:

**Vision Models** (for image analysis):
- `llava:7b` - Recommended, good balance of speed/quality
- `llava:13b` - Higher quality, slower
- `bakllava` - Lightweight alternative

**Code Models** (for config generation):
- `wizardcoder:15b` - Recommended for config generation
- `codegemma` - Google's coding model
- `codellama` - Meta's coding model
- `deepseek-coder` - Specialized coding model

### Fallback System
If AI models are unavailable, MatYouAI falls back to:
- PIL-based dominant color extraction
- K-means clustering for color analysis
- Template-based config generation

## 🛡 Safety Features

- **Non-destructive**: Never overwrites configs without backup
- **Preview Mode**: Test changes before applying
- **Granular Control**: Choose which apps to theme
- **Rollback**: Easy restoration of previous configurations
- **Validation**: Config syntax checking before application

## 🐛 Troubleshooting

### Common Issues

**AI models not working:**
```bash
# Check Ollama status
ollama list
systemctl status ollama

# Pull required models
ollama pull llava:7b
ollama pull wizardcoder:15b
```

**Config detection issues:**
```bash
# Run detailed detection
matyouai detect --verbose

# Check file permissions
ls -la ~/.config/hypr/hyprland.conf
```

**Rofi not launching:**
```bash
# Test rofi manually
rofi -dmenu

# Check if rofi-wayland is installed
pacman -Qi rofi-wayland
```

### Debug Mode
```bash
# Enable verbose logging
matyouai pick --verbose

# Check logs
journalctl -f | grep matyouai
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/yourusername/matyouai.git
cd matyouai

# Install system dependencies
sudo pacman -S python python-pillow python-numpy python-scikit-learn python-requests

# Make CLI executable
chmod +x scripts/matyouai

# Run tests (if test suite exists)
python -m pytest tests/ 2>/dev/null || echo "No test suite available yet"
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Material You** design system by Google
- **Ollama** for local AI model infrastructure
- **Hyprland** community for the amazing window manager
- **Arch Linux** for the excellent package management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/matyouai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/matyouai/discussions)
- **Wiki**: [Project Wiki](https://github.com/yourusername/matyouai/wiki)

---

**MatYouAI** - Bringing intelligent, beautiful theming to your Arch Linux Wayland desktop! 🎨✨ 