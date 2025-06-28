#!/usr/bin/env python3
"""
Rofi Themer for MatYouAI
Applies Material You themes to Rofi application launcher
"""

import logging
import re
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class RofiThemer:
    """Applies themes to Rofi configuration"""
    
    def __init__(self):
        self.color_mappings = {
            "background": "surface",
            "foreground": "on_surface",
            "selected-normal-background": "primary",
            "selected-normal-foreground": "on_primary",
            "alternate-normal-background": "surface_variant",
            "alternate-normal-foreground": "on_surface",
            "urgent-background": "error",
            "urgent-foreground": "on_error",
            "active-background": "accent",
            "active-foreground": "on_primary",
            "border-color": "primary_60",
            "separatorcolor": "neutral_80"
        }
    
    def apply_theme(self, color_palette: Dict[str, str], config_info: Dict, 
                   preview_mode: bool = False) -> bool:
        """Apply Material You theme to Rofi configuration"""
        try:
            success_count = 0
            
            for config_file in config_info["found_configs"]:
                if not config_file.get("writable", False):
                    continue
                
                if self._apply_theme_to_file(config_file["path"], color_palette, preview_mode):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error applying Rofi theme: {e}")
            return False
    
    def _apply_theme_to_file(self, config_path: str, color_palette: Dict[str, str], 
                           preview_mode: bool) -> bool:
        """Apply theme to a specific Rofi config file"""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Determine file format
            if config_path.endswith('.rasi'):
                new_config = self._update_rasi_colors(content, color_palette)
            else:
                new_config = self._update_config_colors(content, color_palette)
            
            if preview_mode:
                logger.info(f"Preview mode: would update {config_path}")
                return True
            
            with open(config_path, 'w') as f:
                f.write(new_config)
            
            logger.info(f"Applied Rofi theme to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme to {config_path}: {e}")
            return False
    
    def _update_rasi_colors(self, rasi_content: str, color_palette: Dict[str, str]) -> str:
        """Update colors in RASI format (CSS-like)"""
        updated_content = rasi_content
        
        # Map palette colors to Material You values
        rofi_colors = {}
        for rofi_prop, palette_key in self.color_mappings.items():
            if palette_key in color_palette:
                rofi_colors[rofi_prop] = color_palette[palette_key]
        
        # Update color definitions
        for prop, color in rofi_colors.items():
            # Pattern for property: value; format
            pattern = rf"(\s*{re.escape(prop)}\s*:\s*)[^;]+;"
            replacement = rf"\1{color};"
            
            if re.search(pattern, updated_content):
                updated_content = re.sub(pattern, replacement, updated_content)
        
        # Add Material You color variables if they don't exist
        if not re.search(r'@theme', updated_content):
            color_vars = self._generate_rasi_color_variables(color_palette)
            updated_content = color_vars + "\n\n" + updated_content
        
        return updated_content
    
    def _update_config_colors(self, config_content: str, color_palette: Dict[str, str]) -> str:
        """Update colors in traditional rofi config format"""
        updated_content = config_content
        
        # Map palette colors
        rofi_colors = {}
        for rofi_prop, palette_key in self.color_mappings.items():
            if palette_key in color_palette:
                rofi_colors[rofi_prop] = color_palette[palette_key]
        
        # Update rofi.color-* settings
        for prop, color in rofi_colors.items():
            config_key = f"rofi.color-{prop}"
            pattern = rf"(\s*{re.escape(config_key)}\s*:\s*)[^\n]+"
            replacement = rf"\1{color}"
            
            if re.search(pattern, updated_content):
                updated_content = re.sub(pattern, replacement, updated_content)
            else:
                updated_content += f"\n{config_key}: {color}"
        
        return updated_content
    
    def _generate_rasi_color_variables(self, color_palette: Dict[str, str]) -> str:
        """Generate RASI color variables"""
        variables = "/* Material You Theme Variables */\n"
        variables += "* {\n"
        
        for prop, palette_key in self.color_mappings.items():
            if palette_key in color_palette:
                variables += f"    {prop}: {color_palette[palette_key]};\n"
        
        variables += "}"
        return variables
    
    def generate_material_you_theme(self, color_palette: Dict[str, str]) -> str:
        """Generate a complete Material You RASI theme"""
        
        primary = color_palette.get("primary", "#6750A4")
        secondary = color_palette.get("secondary", "#625B71")
        surface = color_palette.get("surface", "#F7F2FA")
        on_surface = color_palette.get("on_surface", "#1C1B1F")
        
        theme = f"""/*
 * Material You Theme for Rofi
 * Generated by MatYouAI
 */

* {{
    background: {surface};
    foreground: {on_surface};
    selected-normal-background: {primary};
    selected-normal-foreground: {color_palette.get("on_primary", "#FFFFFF")};
    alternate-normal-background: {color_palette.get("neutral_95", "#F4EFF4")};
    alternate-normal-foreground: {on_surface};
    urgent-background: {color_palette.get("error", "#BA1A1A")};
    urgent-foreground: {color_palette.get("on_error", "#FFFFFF")};
    active-background: {color_palette.get("accent", "#7C4DFF")};
    active-foreground: {color_palette.get("on_primary", "#FFFFFF")};
    border-color: {color_palette.get("primary_60", "#9A82DB")};
    separatorcolor: {color_palette.get("neutral_80", "#CAC4D0")};
    
    border: 2px;
    border-radius: 12px;
    padding: 8px;
    margin: 4px;
}}

window {{
    background-color: @background;
    border: 2px;
    border-color: @border-color;
    border-radius: 12px;
    padding: 12px;
}}

mainbox {{
    background-color: transparent;
    padding: 8px;
}}

inputbar {{
    background-color: @alternate-normal-background;
    text-color: @foreground;
    border: 1px;
    border-color: @border-color;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 0px 0px 12px 0px;
}}

prompt {{
    background-color: transparent;
    text-color: @foreground;
    padding: 0px 8px 0px 0px;
}}

entry {{
    background-color: transparent;
    text-color: @foreground;
    placeholder-color: @separatorcolor;
}}

listview {{
    background-color: transparent;
    spacing: 2px;
    margin: 4px 0px;
}}

element {{
    background-color: transparent;
    text-color: @foreground;
    border-radius: 8px;
    padding: 8px 12px;
}}

element.selected {{
    background-color: @selected-normal-background;
    text-color: @selected-normal-foreground;
}}

element.urgent {{
    background-color: @urgent-background;
    text-color: @urgent-foreground;
}}

element.active {{
    background-color: @active-background;
    text-color: @active-foreground;
}}

element-text {{
    background-color: transparent;
    text-color: inherit;
}}

element-icon {{
    background-color: transparent;
    size: 24px;
    margin: 0px 8px 0px 0px;
}}

scrollbar {{
    background-color: @separatorcolor;
    handle-color: @border-color;
    width: 4px;
    border-radius: 2px;
    margin: 0px 4px;
}}
"""
        return theme.strip()
    
    def reload_rofi(self) -> bool:
        """Reload rofi (no specific reload needed, changes apply on next launch)"""
        logger.info("Rofi theme updated - changes will apply on next launch")
        return True 