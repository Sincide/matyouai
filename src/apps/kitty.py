#!/usr/bin/env python3
"""Kitty Terminal Themer for MatYouAI"""

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)

class KittyThemer:
    """Applies themes to Kitty terminal configuration"""
    
    def __init__(self):
        self.color_mappings = {
            "background": "background",
            "foreground": "on_background", 
            "cursor": "primary",
            "selection_background": "primary_80",
            "url_color": "accent",
        }
    
    def apply_theme(self, color_palette: Dict[str, str], config_info: Dict, 
                   preview_mode: bool = False) -> bool:
        """Apply Material You theme to Kitty configuration"""
        try:
            success_count = 0
            
            for config_file in config_info["found_configs"]:
                if not config_file.get("writable", False):
                    continue
                
                if self._apply_theme_to_file(config_file["path"], color_palette, preview_mode):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error applying Kitty theme: {e}")
            return False
    
    def _apply_theme_to_file(self, config_path: str, color_palette: Dict[str, str], 
                           preview_mode: bool) -> bool:
        """Apply theme to a specific Kitty config file"""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Generate new theme configuration
            new_config = self._generate_kitty_config(color_palette, content)
            
            if preview_mode:
                logger.info(f"Preview mode: would update {config_path}")
                return True
            
            with open(config_path, 'w') as f:
                f.write(new_config)
            
            logger.info(f"Applied Kitty theme to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme to {config_path}: {e}")
            return False
    
    def _generate_kitty_config(self, color_palette: Dict[str, str], current_config: str) -> str:
        """Generate updated Kitty configuration with new colors"""
        
        # Create kitty color configuration
        kitty_colors = {}
        for kitty_setting, palette_key in self.color_mappings.items():
            if palette_key in color_palette:
                kitty_colors[kitty_setting] = color_palette[palette_key]
        
        # Update the configuration
        updated_config = current_config
        
        # Update color settings
        for setting, color in kitty_colors.items():
            pattern = rf"^\s*{re.escape(setting)}\s+.*$"
            replacement = f"{setting} {color}"
            
            if re.search(pattern, updated_config, re.MULTILINE):
                updated_config = re.sub(pattern, replacement, updated_config, flags=re.MULTILINE)
            else:
                updated_config += f"\n{setting} {color}"
        
        return updated_config 