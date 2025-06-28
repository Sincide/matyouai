# MatYouAI Fish Shell Configuration
# This file is symlinked to ~/.config/fish/config.fish by install.sh

# Disable fish greeting
set -U fish_greeting

# Add common paths
fish_add_path ~/.local/bin
fish_add_path /usr/local/bin

# MatYouAI aliases for convenience
alias matyou='matyouai'
alias theme='matyouai'

# Git shortcuts for dotfiles management
alias gc='git commit'
alias gp='git push'
alias gs='git status'
alias ga='git add'

# Hyprland related shortcuts
alias hypr='hyprctl'
alias reload-hypr='hyprctl reload'

# System shortcuts
alias ll='ls -la'
alias la='ls -la'
alias ..='cd ..'
alias ...='cd ../..'

# Ollama shortcuts
alias ai='ollama run'
alias llava='ollama run llava:7b'

# Color scheme for fish
set -U fish_color_normal normal
set -U fish_color_command blue
set -U fish_color_quote yellow
set -U fish_color_redirection cyan
set -U fish_color_end green
set -U fish_color_error red
set -U fish_color_param normal
set -U fish_color_selection white --bold --background=brblack
set -U fish_color_search_match bryellow --background=brblack
set -U fish_color_history_current --bold
set -U fish_color_operator green
set -U fish_color_escape cyan
set -U fish_color_cwd magenta
set -U fish_color_cwd_root red
set -U fish_color_valid_path --underline
set -U fish_color_autosuggestion brblack
set -U fish_color_user brgreen
set -U fish_color_host normal
set -U fish_color_cancel -r

# Welcome message for new fish users
if status --is-interactive
    echo "🎨 MatYouAI Environment Ready"
    echo "• Use 'matyouai' or 'theme' to apply wallpaper themes"
    echo "• Use 'llava' to test AI vision models"
    echo "• Your dotfiles are managed in the MatYouAI repository"
end 