#!/usr/bin/env python3
"""
Dunst Themer for MatYouAI
Applies Material You themes to Dunst notification daemon
"""

import logging
import re
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DunstThemer:
    """Applies themes to Dunst configuration"""
    
    def __init__(self):
        self.section_mappings = {
            "global": {
                "background": "surface",
                "foreground": "on_surface",
                "frame_color": "primary_60"
            },
            "urgency_low": {
                "background": "surface",
                "foreground": "on_surface",
                "frame_color": "neutral_60"
            },
            "urgency_normal": {
                "background": "surface",
                "foreground": "on_surface", 
                "frame_color": "primary"
            },
            "urgency_critical": {
                "background": "error_container",
                "foreground": "on_error_container",
                "frame_color": "error"
            }
        }
    
    def apply_theme(self, color_palette: Dict[str, str], config_info: Dict, 
                   preview_mode: bool = False) -> bool:
        """Apply Material You theme to Dunst configuration"""
        try:
            success_count = 0
            
            for config_file in config_info["found_configs"]:
                if not config_file.get("writable", False):
                    continue
                
                if self._apply_theme_to_file(config_file["path"], color_palette, preview_mode):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error applying Dunst theme: {e}")
            return False
    
    def _apply_theme_to_file(self, config_path: str, color_palette: Dict[str, str], 
                           preview_mode: bool) -> bool:
        """Apply theme to a specific Dunst config file"""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Generate new theme configuration
            new_config = self._update_dunst_colors(content, color_palette)
            
            if preview_mode:
                logger.info(f"Preview mode: would update {config_path}")
                return True
            
            with open(config_path, 'w') as f:
                f.write(new_config)
            
            logger.info(f"Applied Dunst theme to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme to {config_path}: {e}")
            return False
    
    def _update_dunst_colors(self, config_content: str, color_palette: Dict[str, str]) -> str:
        """Update colors in Dunst INI format"""
        updated_content = config_content
        
        # Process each section
        for section_name, color_mappings in self.section_mappings.items():
            for property_name, palette_key in color_mappings.items():
                if palette_key in color_palette:
                    color_value = color_palette[palette_key]
                    updated_content = self._update_ini_property(
                        updated_content, section_name, property_name, color_value
                    )
        
        # Add Material You styling properties
        updated_content = self._add_material_you_styling(updated_content, color_palette)
        
        return updated_content
    
    def _update_ini_property(self, content: str, section: str, property_name: str, value: str) -> str:
        """Update a property in an INI section"""
        # Pattern to match the section
        section_pattern = rf"\[{re.escape(section)}\]"
        section_match = re.search(section_pattern, content)
        
        if not section_match:
            # Section doesn't exist, add it
            new_section = f"\n[{section}]\n{property_name} = {value}\n"
            return content + new_section
        
        # Find the section boundaries
        section_start = section_match.end()
        next_section_match = re.search(r'\n\[.*?\]', content[section_start:])
        
        if next_section_match:
            section_end = section_start + next_section_match.start()
            section_content = content[section_start:section_end]
        else:
            section_content = content[section_start:]
            section_end = len(content)
        
        # Update or add the property within the section
        property_pattern = rf"(\s*{re.escape(property_name)}\s*=\s*)[^\n]+"
        
        if re.search(property_pattern, section_content):
            # Property exists, update it
            new_section_content = re.sub(property_pattern, rf"\1{value}", section_content)
        else:
            # Property doesn't exist, add it
            new_section_content = section_content.rstrip() + f"\n{property_name} = {value}\n"
        
        # Reconstruct the content
        return content[:section_start] + new_section_content + content[section_end:]
    
    def _add_material_you_styling(self, content: str, color_palette: Dict[str, str]) -> str:
        """Add Material You inspired styling to dunst config"""
        styling_properties = {
            "global": {
                "corner_radius": "12",
                "frame_width": "2", 
                "gap_size": "8",
                "offset": "8x8",
                "transparency": "10",
                "font": "JetBrains Mono 11",
                "markup": "full",
                "format": "<b>%s</b>\\n%b",
                "alignment": "left",
                "vertical_alignment": "center",
                "show_age_threshold": "60",
                "ellipsize": "middle",
                "ignore_newline": "no",
                "stack_duplicates": "true",
                "hide_duplicate_count": "false",
                "show_indicators": "yes",
                "sticky_history": "yes",
                "history_length": "20",
                "dmenu": "rofi -dmenu -p dunst:",
                "browser": "xdg-open",
                "always_run_script": "true",
                "title": "Dunst",
                "class": "Dunst",
                "startup_notification": "false",
                "verbosity": "mesg",
                "mouse_left_click": "close_current",
                "mouse_middle_click": "do_action, close_current",
                "mouse_right_click": "close_all"
            }
        }
        
        updated_content = content
        
        for section_name, properties in styling_properties.items():
            for property_name, value in properties.items():
                # Only add if the property doesn't already exist
                section_pattern = rf"\[{re.escape(section_name)}\].*?(?=\n\[|\Z)"
                section_match = re.search(section_pattern, updated_content, re.DOTALL)
                
                if section_match:
                    section_content = section_match.group(0)
                    property_pattern = rf"\b{re.escape(property_name)}\s*="
                    
                    if not re.search(property_pattern, section_content):
                        # Property doesn't exist, add it
                        updated_content = self._update_ini_property(
                            updated_content, section_name, property_name, value
                        )
        
        return updated_content
    
    def generate_material_you_config(self, color_palette: Dict[str, str]) -> str:
        """Generate a complete Material You Dunst configuration"""
        
        config = f"""# Material You Theme for Dunst
# Generated by MatYouAI

[global]
    # Display
    monitor = 0
    follow = mouse
    
    # Geometry
    width = (0, 400)
    height = 300
    origin = top-right
    offset = 8x8
    scale = 0
    notification_limit = 3
    
    # Progress bar
    progress_bar = true
    progress_bar_height = 10
    progress_bar_frame_width = 1
    progress_bar_min_width = 150
    progress_bar_max_width = 300
    
    # Appearance  
    transparency = 10
    corner_radius = 12
    frame_width = 2
    gap_size = 8
    separator_height = 2
    padding = 12
    horizontal_padding = 12
    text_icon_padding = 8
    
    # Material You Colors
    background = "{color_palette.get('surface', '#F7F2FA')}"
    foreground = "{color_palette.get('on_surface', '#1C1B1F')}"
    frame_color = "{color_palette.get('primary_60', '#9A82DB')}"
    separator_color = "{color_palette.get('neutral_80', '#CAC4D0')}"
    
    # Typography
    font = JetBrains Mono 11
    markup = full
    format = "<b>%s</b>\\n%b"
    alignment = left
    vertical_alignment = center
    show_age_threshold = 60
    ellipsize = middle
    ignore_newline = no
    stack_duplicates = true
    hide_duplicate_count = false
    show_indicators = yes
    
    # Icons
    enable_recursive_icon_lookup = true
    icon_theme = "Papirus-Dark, Adwaita"
    icon_position = left
    min_icon_size = 32
    max_icon_size = 64
    icon_path = "/usr/share/icons/Papirus-Dark/16x16/status/:/usr/share/icons/Papirus-Dark/16x16/devices/"
    
    # History
    sticky_history = yes
    history_length = 20
    
    # Misc/Advanced
    dmenu = rofi -dmenu -p dunst:
    browser = xdg-open
    always_run_script = true
    title = Dunst
    class = Dunst
    startup_notification = false
    verbosity = mesg
    corner_radius = 12
    ignore_dbusclose = false
    force_xinerama = false
    
    # Mouse
    mouse_left_click = close_current
    mouse_middle_click = do_action, close_current
    mouse_right_click = close_all

[experimental]
    per_monitor_dpi = false

[urgency_low]
    background = "{color_palette.get('surface', '#F7F2FA')}"
    foreground = "{color_palette.get('on_surface', '#1C1B1F')}"
    frame_color = "{color_palette.get('neutral_60', '#938F96')}"
    timeout = 10
    default_icon = dialog-information

[urgency_normal]
    background = "{color_palette.get('surface', '#F7F2FA')}"
    foreground = "{color_palette.get('on_surface', '#1C1B1F')}"
    frame_color = "{color_palette.get('primary', '#6750A4')}"
    timeout = 10
    override_pause_level = 30
    default_icon = dialog-information

[urgency_critical]
    background = "{color_palette.get('error_container', '#FFDAD6')}"
    foreground = "{color_palette.get('on_error_container', '#410002')}"
    frame_color = "{color_palette.get('error', '#BA1A1A')}"
    timeout = 0
    override_pause_level = 60
    default_icon = dialog-error

# Application specific rules
[play_sound]
    summary = "*"
    script = "~/.config/dunst/scripts/notification_sound.sh"

[Discord]
    appname = "Discord"
    format = "<b>Discord</b>\\n%b"
    urgency = normal
    background = "{color_palette.get('primary_90', '#EADDFF')}"
    foreground = "{color_palette.get('on_primary_container', '#21005D')}"
    frame_color = "{color_palette.get('primary', '#6750A4')}"

[Spotify]
    appname = "Spotify"
    format = "<b>♪ Spotify</b>\\n%b"
    urgency = low
    background = "{color_palette.get('secondary_90', '#E8DEF8')}"
    foreground = "{color_palette.get('on_secondary_container', '#1D192B')}"
    frame_color = "{color_palette.get('secondary', '#625B71')}"
"""
        return config.strip()
    
    def reload_dunst(self) -> bool:
        """Reload Dunst configuration"""
        try:
            import subprocess
            
            # Send SIGUSR1 to reload dunst
            result = subprocess.run(["pkill", "-SIGUSR1", "dunst"], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                logger.info("Dunst configuration reloaded successfully")
                return True
            else:
                logger.warning("Dunst reload signal sent, but process may not be running")
                return True  # Not necessarily an error
                
        except Exception as e:
            logger.error(f"Error reloading Dunst config: {e}")
            return False 