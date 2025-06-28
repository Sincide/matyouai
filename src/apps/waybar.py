#!/usr/bin/env python3
"""
Waybar Themer for MatYouAI
Handles multiple waybar configurations, modular CSS, and @import statements
"""

import logging
import re
import json
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class WaybarThemer:
    """Applies themes to Waybar configurations (handles multiple instances and modular setups)"""
    
    def __init__(self):
        self.css_color_mappings = {
            # Common waybar CSS variables and properties
            "background-color": "surface",
            "background": "surface", 
            "color": "on_surface",
            "border-color": "primary_60",
            "border": "primary_60",
            "--primary": "primary",
            "--secondary": "secondary",
            "--background": "surface",
            "--text": "on_surface",
            "--accent": "accent",
            "--workspace-active": "primary",
            "--workspace-inactive": "neutral_60",
            "--urgent": "error",
            "--warning": "warning"
        }
    
    def apply_theme(self, color_palette: Dict[str, str], config_info: Dict, 
                   preview_mode: bool = False) -> bool:
        """Apply Material You theme to all detected Waybar configurations"""
        try:
            success_count = 0
            all_waybar_configs = self._discover_all_waybar_configs()
            
            logger.info(f"Found {len(all_waybar_configs)} waybar configuration sets")
            
            for config_set in all_waybar_configs:
                if self._apply_theme_to_config_set(config_set, color_palette, preview_mode):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error applying Waybar theme: {e}")
            return False
    
    def _discover_all_waybar_configs(self) -> List[Dict]:
        """Discover all waybar configuration sets (including multiple instances)"""
        config_sets = []
        waybar_root = Path.home() / ".config" / "waybar"
        
        if not waybar_root.exists():
            return config_sets
        
        # Find all potential config directories
        config_dirs = [waybar_root]
        
        # Recursively find subdirectories that might contain configs
        for item in waybar_root.rglob("*"):
            if item.is_dir() and self._looks_like_waybar_config_dir(item):
                config_dirs.append(item)
        
        # Analyze each directory for config files
        for config_dir in config_dirs:
            config_set = self._analyze_waybar_config_dir(config_dir)
            if config_set:
                config_sets.append(config_set)
        
        return config_sets
    
    def _looks_like_waybar_config_dir(self, directory: Path) -> bool:
        """Check if a directory looks like it contains waybar configs"""
        config_indicators = [
            "config", "config.json", "style.css", "config.jsonc"
        ]
        
        for indicator in config_indicators:
            if (directory / indicator).exists():
                return True
        
        return False
    
    def _analyze_waybar_config_dir(self, config_dir: Path) -> Optional[Dict]:
        """Analyze a waybar config directory and find all relevant files"""
        config_files = []
        css_files = []
        
        # Find config files
        for config_name in ["config", "config.json", "config.jsonc"]:
            config_path = config_dir / config_name
            if config_path.exists():
                config_files.append({
                    "path": str(config_path),
                    "type": "config",
                    "writable": config_path.exists() and config_path.stat().st_mode & 0o200
                })
        
        # Find CSS files and follow @import chains
        css_files.extend(self._discover_css_files(config_dir))
        
        # Specifically look for our modular structure
        modules_dir = config_dir / "modules"
        if modules_dir.exists():
            for module_css in modules_dir.glob("*.css"):
                if str(module_css) not in [css_file["path"] for css_file in css_files]:
                    try:
                        with open(module_css, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        css_files.append({
                            "path": str(module_css),
                            "type": "module_css",
                            "writable": module_css.exists() and module_css.stat().st_mode & 0o200,
                            "content": content,
                            "colors": self._extract_css_colors(content),
                            "is_module": True
                        })
                    except Exception as e:
                        logger.warning(f"Error processing module CSS {module_css}: {e}")
        
        if not (config_files or css_files):
            return None
        
        return {
            "directory": str(config_dir),
            "config_files": config_files,
            "css_files": css_files,
            "instance_name": self._get_instance_name(config_dir),
            "is_modular": modules_dir.exists()
        }
    
    def _discover_css_files(self, config_dir: Path) -> List[Dict]:
        """Discover all CSS files including those referenced by @import"""
        css_files = []
        discovered_files = set()
        
        # Start with main style files
        main_css_candidates = ["style.css", "styles.css", "main.css"]
        
        for css_name in main_css_candidates:
            css_path = config_dir / css_name
            if css_path.exists():
                self._discover_css_recursive(css_path, css_files, discovered_files, config_dir)
        
        # Also scan for any other CSS files in the directory
        for css_file in config_dir.glob("*.css"):
            if str(css_file) not in discovered_files:
                self._discover_css_recursive(css_file, css_files, discovered_files, config_dir)
        
        return css_files
    
    def _discover_css_recursive(self, css_path: Path, css_files: List[Dict], 
                               discovered_files: Set[str], base_dir: Path):
        """Recursively discover CSS files following @import statements"""
        css_path_str = str(css_path)
        
        if css_path_str in discovered_files or not css_path.exists():
            return
        
        discovered_files.add(css_path_str)
        
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            css_files.append({
                "path": css_path_str,
                "type": "css",
                "writable": css_path.exists() and css_path.stat().st_mode & 0o200,
                "content": content,
                "colors": self._extract_css_colors(content)
            })
            
            # Find @import statements
            import_pattern = r'@import\s+["\']([^"\']+)["\']'
            imports = re.findall(import_pattern, content)
            
            for import_path in imports:
                # Resolve relative imports
                if not import_path.startswith('/'):
                    resolved_path = css_path.parent / import_path
                else:
                    resolved_path = Path(import_path)
                
                # Recursively process imported files
                self._discover_css_recursive(resolved_path, css_files, discovered_files, base_dir)
        
        except Exception as e:
            logger.warning(f"Error processing CSS file {css_path}: {e}")
    
    def _extract_css_colors(self, css_content: str) -> List[str]:
        """Extract color values from CSS content"""
        colors = []
        
        # Hex colors
        hex_pattern = r'#[0-9a-fA-F]{3,8}\b'
        colors.extend(re.findall(hex_pattern, css_content))
        
        # RGB/RGBA colors
        rgb_pattern = r'rgba?\s*\(\s*[^)]+\)'
        colors.extend(re.findall(rgb_pattern, css_content))
        
        # HSL colors
        hsl_pattern = r'hsla?\s*\(\s*[^)]+\)'
        colors.extend(re.findall(hsl_pattern, css_content))
        
        # CSS variables that might contain colors
        var_pattern = r'var\(--[^)]+\)'
        colors.extend(re.findall(var_pattern, css_content))
        
        return list(set(colors))
    
    def _get_instance_name(self, config_dir: Path) -> str:
        """Generate a descriptive name for this waybar instance"""
        waybar_root = Path.home() / ".config" / "waybar"
        
        # Handle test directories that aren't under the real waybar root
        if not str(config_dir).startswith(str(waybar_root)):
            return config_dir.name or "test"
        
        if config_dir == waybar_root:
            return "main"
        
        # Generate name based on directory structure
        try:
            relative_path = config_dir.relative_to(waybar_root)
            return str(relative_path).replace('/', '-')
        except ValueError:
            # If relative_to fails, just use the directory name
            return config_dir.name or "unknown"
    
    def _apply_theme_to_config_set(self, config_set: Dict, color_palette: Dict[str, str], 
                                  preview_mode: bool) -> bool:
        """Apply theme to a complete waybar configuration set"""
        try:
            instance_name = config_set["instance_name"]
            logger.info(f"Applying theme to waybar instance: {instance_name}")
            
            success = True
            
            # Apply theme to CSS files
            for css_file in config_set["css_files"]:
                if not css_file.get("writable", False):
                    logger.warning(f"CSS file not writable: {css_file['path']}")
                    continue
                
                if not self._apply_theme_to_css_file(css_file, color_palette, preview_mode):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying theme to config set {config_set.get('instance_name', 'unknown')}: {e}")
            return False
    
    def _apply_theme_to_css_file(self, css_file: Dict, color_palette: Dict[str, str], 
                                preview_mode: bool) -> bool:
        """Apply theme to a specific CSS file"""
        try:
            css_path = css_file["path"]
            current_content = css_file["content"]
            
            # Generate new CSS content with updated colors
            new_content = self._update_css_colors(current_content, color_palette)
            
            if preview_mode:
                logger.info(f"Preview mode: would update {css_path}")
                logger.debug(f"Color changes preview:\n{self._preview_color_changes(current_content, new_content)}")
                return True
            
            # Write updated CSS
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"Applied theme to CSS file: {css_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme to CSS file {css_file['path']}: {e}")
            return False
    
    def _update_css_colors(self, css_content: str, color_palette: Dict[str, str]) -> str:
        """Update colors in CSS content while preserving structure"""
        updated_content = css_content
        
        # Replace CSS custom properties (variables)
        variable_patterns = [
            (r'(--primary\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("primary", "#6750A4")}'),
            (r'(--secondary\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("secondary", "#625B71")}'),
            (r'(--background\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("surface", "#F7F2FA")}'),
            (r'(--text\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("on_surface", "#1C1B1F")}'),
            (r'(--accent\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("accent", "#7C4DFF")}'),
            (r'(--workspace-active\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("primary", "#6750A4")}'),
            (r'(--workspace-inactive\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("neutral_60", "#938F96")}'),
            (r'(--urgent\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("error", "#BA1A1A")}'),
            (r'(--warning\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("warning", "#F57C00")}'),
        ]
        
        for pattern, replacement in variable_patterns:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.IGNORECASE)
        
        # Replace direct color properties for common waybar elements
        element_patterns = [
            # Window/container backgrounds
            (r'(window#waybar[^{]*\{[^}]*background[^:]*:\s*)[^;]+', f'\\g<1>{self._to_rgba(color_palette.get("surface", "#F7F2FA"), 0.9)}'),
            (r'(\.modules-[^{]*\{[^}]*background[^:]*:\s*)[^;]+', f'\\g<1>{color_palette.get("surface", "#F7F2FA")}'),
            
            # Text colors
            (r'(window#waybar[^{]*\{[^}]*color\s*:\s*)[^;]+', f'\\g<1>{color_palette.get("on_surface", "#1C1B1F")}'),
            
            # Workspace buttons
            (r'(#workspaces\s+button\.focused[^{]*\{[^}]*background[^:]*:\s*)[^;]+', f'\\g<1>{color_palette.get("primary", "#6750A4")}'),
            (r'(#workspaces\s+button\.active[^{]*\{[^}]*background[^:]*:\s*)[^;]+', f'\\g<1>{color_palette.get("primary", "#6750A4")}'),
            (r'(#workspaces\s+button\.urgent[^{]*\{[^}]*background[^:]*:\s*)[^;]+', f'\\g<1>{color_palette.get("error", "#BA1A1A")}'),
            
            # Border colors
            (r'(border[^:]*:\s*[^;]*?)(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))', f'\\g<1>{color_palette.get("primary_60", "#9A82DB")}'),
        ]
        
        for pattern, replacement in element_patterns:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL | re.IGNORECASE)
        
        return updated_content
    
    def _to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to rgba format"""
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
            return hex_color  # Return original if invalid
        
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    def _preview_color_changes(self, original: str, updated: str) -> str:
        """Generate a preview of color changes"""
        original_colors = set(self._extract_css_colors(original))
        updated_colors = set(self._extract_css_colors(updated))
        
        changes = []
        
        # This is a simplified preview - in reality we'd want to track specific changes
        if original_colors != updated_colors:
            changes.append(f"Colors found in original: {len(original_colors)}")
            changes.append(f"Colors in updated version: {len(updated_colors)}")
        
        return "\n".join(changes) if changes else "No color changes detected"
    
    def reload_waybar(self) -> bool:
        """Reload all waybar instances"""
        try:
            import subprocess
            
            # Kill and restart waybar
            subprocess.run(["pkill", "waybar"], check=False, capture_output=True)
            
            # Wait a moment then start waybar
            import time
            time.sleep(0.5)
            
            # Start waybar (it will read the updated configs)
            result = subprocess.run(["waybar"], check=False, capture_output=True)
            
            logger.info("Waybar reloaded")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading waybar: {e}")
            return False 