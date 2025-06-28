#!/usr/bin/env fish

# Power Menu Script for Waybar
# Provides shutdown, reboot, logout, and lock options

set OPTIONS "Lock\nLogout\nSleep\nReboot\nShutdown"

set CHOICE (echo -e $OPTIONS | wofi --dmenu --prompt "Power Menu")

switch $CHOICE
    case "Lock"
        swaylock -f
    case "Logout"
        hyprctl dispatch exit
    case "Sleep"
        systemctl suspend
    case "Reboot"
        systemctl reboot
    case "Shutdown"
        systemctl poweroff
    case "*"
        # Do nothing if cancelled
end 