#!/usr/bin/env python3
"""
Hyprland Themer for MatYouAI
Applies Material You themes to Hyprland window manager
Supports modular configurations with source statements
"""

import logging
import re
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class HyprlandThemer:
    """Applies themes to Hyprland configuration (handles modular setups)"""
    
    def __init__(self):
        self.color_mappings = {
            "col.active_border": ["primary", "accent"],
            "col.inactive_border": ["neutral_60", "secondary_80"],
            "col.group_border": ["secondary", "primary_60"],
            "col.group_border_active": ["primary", "accent"],
            "col.shadow": ["neutral_90", "primary_95"],
        }
        
        # Common decoration-related keywords to help identify theme files
        self.theme_keywords = [
            "decoration", "col.", "rgba", "rgb", "border", "shadow", 
            "blur", "opacity", "rounding", "animation"
        ]
    
    def apply_theme(self, color_palette: Dict[str, str], config_info: Dict, 
                   preview_mode: bool = False) -> bool:
        """Apply Material You theme to Hyprland configuration (modular-aware)"""
        try:
            # Analyze the modular structure
            modular_info = self._analyze_modular_structure(config_info)
            
            if modular_info["is_modular"]:
                logger.info(f"Detected modular Hyprland config with {len(modular_info['color_files'])} theme files")
                return self._apply_theme_modular(color_palette, config_info, modular_info, preview_mode)
            else:
                logger.info("Detected single-file Hyprland config")
                return self._apply_theme_single_file(color_palette, config_info, preview_mode)
            
        except Exception as e:
            logger.error(f"Error applying Hyprland theme: {e}")
            return False
    
    def _analyze_modular_structure(self, config_info: Dict) -> Dict:
        """Analyze the structure to determine if it's modular and where colors are defined"""
        found_configs = config_info.get("found_configs", [])
        dependency_graph = config_info.get("dependency_graph", {})
        
        modular_info = {
            "is_modular": len(found_configs) > 1,
            "main_files": [],
            "color_files": [],
            "other_files": [],
            "dependency_graph": dependency_graph
        }
        
        # Categorize files based on their content and role
        for config_file in found_configs:
            file_path = config_file["path"]
            content = config_file.get("content", "")
            color_references = config_file.get("color_references", [])
            
            # Check if this file has color definitions
            has_colors = len(color_references) > 0
            has_theme_keywords = any(keyword in content for keyword in self.theme_keywords)
            
            # Determine file role
            if self._is_main_config_file(file_path, content):
                modular_info["main_files"].append(config_file)
            elif has_colors or has_theme_keywords or self._looks_like_theme_file(file_path):
                modular_info["color_files"].append(config_file)
            else:
                modular_info["other_files"].append(config_file)
        
        # If no dedicated color files found, check if main file has colors
        if not modular_info["color_files"] and modular_info["main_files"]:
            main_file = modular_info["main_files"][0]
            if main_file.get("color_references"):
                modular_info["color_files"].append(main_file)
        
        return modular_info
    
    def _is_main_config_file(self, file_path: str, content: str) -> bool:
        """Check if this is likely the main hyprland.conf file"""
        path = Path(file_path)
        
        # Check filename
        if path.name in ["hyprland.conf", "hyprland.config"]:
            return True
        
        # Check if it has source statements (typical of main config)
        source_pattern = r'source\s*='
        if re.search(source_pattern, content):
            return True
        
        return False
    
    def _looks_like_theme_file(self, file_path: str) -> bool:
        """Check if filename suggests it contains theme/color definitions"""
        path = Path(file_path)
        theme_names = [
            "decoration", "theme", "color", "style", "appearance", 
            "visual", "ui", "material", "you"
        ]
        
        filename_lower = path.name.lower()
        return any(theme_name in filename_lower for theme_name in theme_names)
    
    def _apply_theme_modular(self, color_palette: Dict[str, str], config_info: Dict, 
                           modular_info: Dict, preview_mode: bool) -> bool:
        """Apply theme to modular Hyprland configuration"""
        success_count = 0
        
        # Apply theme to color/theme files
        for config_file in modular_info["color_files"]:
            if not config_file.get("writable", False):
                logger.warning(f"Color file not writable: {config_file['path']}")
                continue
            
            if self._apply_theme_to_file(config_file["path"], color_palette, preview_mode, config_file):
                success_count += 1
        
        # If no color files were themed but we have main files, try them
        if success_count == 0 and modular_info["main_files"]:
            logger.info("No dedicated color files found, applying to main config")
            for config_file in modular_info["main_files"]:
                if config_file.get("writable", False):
                    if self._apply_theme_to_file(config_file["path"], color_palette, preview_mode, config_file):
                        success_count += 1
        
        return success_count > 0
    
    def _apply_theme_single_file(self, color_palette: Dict[str, str], config_info: Dict, 
                               preview_mode: bool) -> bool:
        """Apply theme to single-file Hyprland configuration"""
        success_count = 0
        
        for config_file in config_info["found_configs"]:
            if not config_file.get("writable", False):
                continue
            
            if self._apply_theme_to_file(config_file["path"], color_palette, preview_mode, config_file):
                success_count += 1
        
        return success_count > 0
    
    def _apply_theme_to_file(self, config_path: str, color_palette: Dict[str, str], 
                           preview_mode: bool, config_file: Optional[Dict] = None) -> bool:
        """Apply theme to a specific Hyprland config file"""
        try:
            # Use cached content if available
            if config_file and "content" in config_file:
                content = config_file["content"]
            else:
                with open(config_path, 'r') as f:
                    content = f.read()
            
            # Check if this file actually has theme-related content
            if not self._file_has_theme_content(content):
                logger.info(f"Skipping {config_path} - no theme content detected")
                return True  # Not an error, just nothing to do
            
            # Generate new theme configuration
            new_config = self._generate_hyprland_config(color_palette, content)
            
            if preview_mode:
                logger.info(f"Preview mode: would update {config_path}")
                self._show_preview_changes(content, new_config, config_path)
                return True
            
            # Write the updated configuration
            with open(config_path, 'w') as f:
                f.write(new_config)
            
            logger.info(f"Applied Hyprland theme to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme to {config_path}: {e}")
            return False
    
    def _file_has_theme_content(self, content: str) -> bool:
        """Check if file contains theme-related content worth modifying"""
        # Check for decoration section
        if re.search(r'decoration\s*\{', content):
            return True
        
        # Check for color properties
        color_patterns = [
            r'col\.',  # Hyprland color properties
            r'rgba?\(',  # RGB/RGBA values
            r'#[0-9a-fA-F]{3,8}',  # Hex colors
        ]
        
        for pattern in color_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _show_preview_changes(self, original: str, updated: str, file_path: str):
        """Show preview of changes to be made"""
        original_colors = re.findall(r'(?:col\.[^=]*=\s*|rgba?\(|#[0-9a-fA-F]{3,8})', original)
        updated_colors = re.findall(r'(?:col\.[^=]*=\s*|rgba?\(|#[0-9a-fA-F]{3,8})', updated)
        
        logger.info(f"Preview changes for {Path(file_path).name}:")
        logger.info(f"  Original colors found: {len(original_colors)}")
        logger.info(f"  Updated colors: {len(updated_colors)}")
        
        # Show specific color changes
        col_changes = []
        for color_key in self.color_mappings:
            original_match = re.search(rf'{re.escape(color_key)}\s*=\s*([^#\n]*)', original)
            updated_match = re.search(rf'{re.escape(color_key)}\s*=\s*([^#\n]*)', updated)
            
            if original_match and updated_match:
                orig_val = original_match.group(1).strip()
                new_val = updated_match.group(1).strip()
                if orig_val != new_val:
                    col_changes.append(f"    {color_key}: {orig_val} → {new_val}")
        
        if col_changes:
            logger.info("  Color changes:")
            for change in col_changes:
                logger.info(change)
    
    def _generate_hyprland_config(self, color_palette: Dict[str, str], current_config: str) -> str:
        """Generate updated Hyprland configuration with new colors"""
        
        # Extract the primary and secondary colors with alpha
        primary = color_palette.get("primary", "#6750A4")
        secondary = color_palette.get("secondary", "#625B71")
        accent = color_palette.get("accent", "#7C4DFF")
        neutral_60 = color_palette.get("neutral_60", "#938F96")
        neutral_90 = color_palette.get("neutral_90", "#E6E0E9")
        
        # Create color mapping with alpha values
        hyprland_colors = {
            "col.active_border": f"rgba({self._hex_to_rgba(primary, 0.8)})",
            "col.inactive_border": f"rgba({self._hex_to_rgba(neutral_60, 0.6)})",
            "col.group_border": f"rgba({self._hex_to_rgba(secondary, 0.7)})",
            "col.group_border_active": f"rgba({self._hex_to_rgba(accent, 0.9)})",
            "col.shadow": f"rgba({self._hex_to_rgba(neutral_90, 0.3)})",
        }
        
        # Update the configuration
        updated_config = current_config
        
        # Update decoration section colors
        for color_key, color_value in hyprland_colors.items():
            # Pattern to match the color setting in any context
            pattern = rf"(\s*{re.escape(color_key)}\s*=\s*)[^#\n]*(.*?)(\n|$)"
            replacement = rf"\1{color_value}\3"
            
            if re.search(pattern, updated_config):
                updated_config = re.sub(pattern, replacement, updated_config)
            else:
                # If color setting doesn't exist, add it to decoration section
                updated_config = self._add_color_to_decoration_section(updated_config, color_key, color_value)
        
        # Add Material You inspired decoration settings if not present
        decoration_enhancements = self._get_decoration_enhancements(color_palette)
        updated_config = self._merge_decoration_settings(updated_config, decoration_enhancements)
        
        return updated_config
    
    def _add_color_to_decoration_section(self, config: str, color_key: str, color_value: str) -> str:
        """Add a color setting to the decoration section"""
        decoration_pattern = r"(decoration\s*\{[^}]*?)"
        
        if re.search(decoration_pattern, config, re.DOTALL):
            def add_color(match):
                section = match.group(1)
                if not section.endswith('\n'):
                    section += '\n'
                return section + f"    {color_key} = {color_value}\n"
            
            return re.sub(decoration_pattern, add_color, config, flags=re.DOTALL)
        else:
            # If no decoration section exists, create one
            decoration_section = f"""
decoration {{
    {color_key} = {color_value}
}}
"""
            return config + decoration_section
        
        return config
    
    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to RGBA format for Hyprland"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        elif len(hex_color) == 3:
            r = int(hex_color[0], 16) * 17
            g = int(hex_color[1], 16) * 17
            b = int(hex_color[2], 16) * 17
        else:
            # Fallback
            r, g, b = 103, 80, 164  # Default primary color
        
        # Convert alpha to hex (0-255)
        alpha_hex = format(int(alpha * 255), '02x')
        
        return f"{r:02x}{g:02x}{b:02x}{alpha_hex}"
    
    def _get_decoration_enhancements(self, color_palette: Dict[str, str]) -> Dict[str, str]:
        """Get additional decoration settings inspired by Material You"""
        
        return {
            "rounding": "12",
            "blur": {
                "enabled": "true",
                "size": "8",
                "passes": "3",
                "noise": "0.02",
                "contrast": "1.1",
                "brightness": "1.0"
            },
            "drop_shadow": "true",
            "shadow_range": "8",
            "shadow_render_power": "2",
            "shadow_offset": "2 2",
            "active_opacity": "1.0",
            "inactive_opacity": "0.95",
            "fullscreen_opacity": "1.0"
        }
    
    def _merge_decoration_settings(self, config: str, enhancements: Dict) -> str:
        """Merge decoration enhancements into the configuration"""
        
        # Find decoration section
        decoration_pattern = r"(decoration\s*\{)(.*?)(\})"
        decoration_match = re.search(decoration_pattern, config, re.DOTALL)
        
        if decoration_match:
            section_start = decoration_match.group(1)
            section_content = decoration_match.group(2)
            section_end = decoration_match.group(3)
            
            # Update or add settings
            for key, value in enhancements.items():
                if key == "blur":
                    # Handle blur subsection
                    blur_pattern = r"(blur\s*\{)(.*?)(\})"
                    blur_match = re.search(blur_pattern, section_content, re.DOTALL)
                    
                    if blur_match:
                        # Update existing blur section
                        blur_content = blur_match.group(2)
                        for blur_key, blur_value in value.items():
                            blur_setting_pattern = rf"(\s*{re.escape(blur_key)}\s*=\s*)[^\n]*"
                            if re.search(blur_setting_pattern, blur_content):
                                blur_content = re.sub(blur_setting_pattern, rf"\1{blur_value}", blur_content)
                            else:
                                blur_content += f"\n        {blur_key} = {blur_value}"
                        
                        section_content = re.sub(blur_pattern, 
                                               rf"\1{blur_content}\3", 
                                               section_content, flags=re.DOTALL)
                    else:
                        # Add new blur section
                        blur_section = "\n    blur {\n"
                        for blur_key, blur_value in value.items():
                            blur_section += f"        {blur_key} = {blur_value}\n"
                        blur_section += "    }\n"
                        section_content += blur_section
                else:
                    # Handle regular settings
                    setting_pattern = rf"(\s*{re.escape(key)}\s*=\s*)[^\n]*"
                    if re.search(setting_pattern, section_content):
                        section_content = re.sub(setting_pattern, rf"\1{value}", section_content)
                    else:
                        section_content += f"\n    {key} = {value}"
            
            # Reconstruct the decoration section
            new_decoration = section_start + section_content + section_end
            config = re.sub(decoration_pattern, new_decoration, config, flags=re.DOTALL)
        
        return config
    
    def generate_material_you_preset(self, color_palette: Dict[str, str]) -> str:
        """Generate a complete Material You themed Hyprland preset"""
        
        primary = color_palette.get("primary", "#6750A4")
        secondary = color_palette.get("secondary", "#625B71")
        accent = color_palette.get("accent", "#7C4DFF")
        background = color_palette.get("background", "#FFFBFE")
        surface = color_palette.get("surface", "#F7F2FA")
        
        preset = f"""
# Material You Theme Generated by MatYouAI
# Primary: {primary}
# Secondary: {secondary}
# Accent: {accent}

decoration {{
    # Material You Colors
    col.active_border = rgba({self._hex_to_rgba(primary, 0.8)})
    col.inactive_border = rgba({self._hex_to_rgba(secondary, 0.4)})
    col.group_border = rgba({self._hex_to_rgba(secondary, 0.6)})
    col.group_border_active = rgba({self._hex_to_rgba(accent, 0.9)})
    col.shadow = rgba({self._hex_to_rgba(primary, 0.2)})
    
    # Material You Styling
    rounding = 12
    
    blur {{
        enabled = true
        size = 8
        passes = 3
        noise = 0.02
        contrast = 1.1
        brightness = 1.0
    }}
    
    drop_shadow = true
    shadow_range = 8
    shadow_render_power = 2
    shadow_offset = 2 2
    
    active_opacity = 1.0
    inactive_opacity = 0.95
    fullscreen_opacity = 1.0
}}

general {{
    border_size = 2
    gaps_in = 8
    gaps_out = 16
    layout = dwindle
    allow_tearing = false
}}

animations {{
    enabled = true
    
    bezier = material, 0.4, 0.0, 0.2, 1.0
    bezier = materialDecelerated, 0.0, 0.0, 0.2, 1.0
    bezier = materialAccelerated, 0.4, 0.0, 1.0, 1.0
    
    animation = windows, 1, 3, material
    animation = windowsOut, 1, 3, materialAccelerated, popin 80%
    animation = border, 1, 2, material
    animation = borderangle, 1, 4, material
    animation = fade, 1, 2, material
    animation = workspaces, 1, 4, materialDecelerated
}}
"""
        return preset.strip()
    
    def reload_config(self) -> bool:
        """Reload Hyprland configuration"""
        try:
            import subprocess
            result = subprocess.run(["hyprctl", "reload"], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                logger.info("Hyprland configuration reloaded successfully")
                return True
            else:
                logger.warning(f"Hyprland reload returned non-zero: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error reloading Hyprland config: {e}")
            return False 