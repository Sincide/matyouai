#!/usr/bin/env python3
"""
Configuration Detection Module for MatYouAI
Automatically detects and analyzes configuration files for various applications
Supports modular configs, source statements, and imports
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class ConfigDetector:
    """Detect and analyze application configuration files with advanced parsing"""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".config"
        self.app_configs = self._load_app_config_rules()
    
    def _load_app_config_rules(self) -> Dict[str, Dict]:
        """Load application configuration detection rules"""
        return {
            "hyprland": {
                "paths": [
                    "~/.config/hypr/hyprland.conf"
                ],
                "format": "hyprland",
                "theme_sections": ["decoration", "general", "misc"],
                "color_keywords": ["col.active_border", "col.inactive_border"],
                "backup_name": "hyprland.conf.matyou.bak",
                "supports_includes": True,
                "include_patterns": [r'source\s*=\s*([^\s#]+)']
            },
            "waybar": {
                "paths": [
                    "~/.config/waybar/config",
                    "~/.config/waybar/config.json"
                ],
                "format": "json",
                "style_file": "~/.config/waybar/style.css",
                "modules_dir": "~/.config/waybar/modules/",
                "scripts_dir": "~/.config/waybar/scripts/",
                "theme_sections": ["colors", "styling"],
                "backup_name": "waybar.matyou.bak",
                "supports_discovery": True  # Use advanced waybar discovery
            },
            "rofi": {
                "paths": [
                    "~/.config/rofi/config.rasi",
                    "~/.config/rofi/theme.rasi",
                    "~/.config/rofi/themes/"
                ],
                "format": "rasi",
                "theme_sections": ["colors", "window", "element"],
                "backup_name": "rofi.matyou.bak",
                "supports_includes": True,
                "include_patterns": [r'@import\s*["\']([^"\']+)["\']']
            },
            "kitty": {
                "paths": [
                    "~/.config/kitty/kitty.conf"
                ],
                "format": "kitty",
                "theme_sections": ["colors"],
                "color_keywords": ["foreground", "background", "cursor"],
                "backup_name": "kitty.conf.matyou.bak",
                "supports_includes": True,
                "include_patterns": [r'include\s+([^\s#]+)']
            },
            "fish": {
                "paths": [
                    "~/.config/fish/config.fish",
                    "~/.config/fish/conf.d/"
                ],
                "format": "fish",
                "theme_sections": ["colors"],
                "backup_name": "fish.matyou.bak"
            },
            "dunst": {
                "paths": [
                    "~/.config/dunst/dunstrc"
                ],
                "format": "ini",
                "theme_sections": ["global", "urgency_low", "urgency_normal"],
                "color_keywords": ["background", "foreground", "frame_color"],
                "backup_name": "dunstrc.matyou.bak"
            },
            "gtk": {
                "paths": [],  # GTK themes are generated, not based on existing files
                "format": "css",
                "theme_sections": ["colors", "widgets"],
                "backup_name": "gtk.matyou.bak",
                "is_generated": True,  # Special flag for generated themes
                "always_available": True  # Always available for theming
            }
        }
    
    def detect_all_configs(self) -> Dict[str, Dict]:
        """Detect all supported application configurations"""
        detected_configs = {}
        
        for app_name in self.app_configs:
            config_info = self.detect_app_config(app_name)
            if config_info:
                detected_configs[app_name] = config_info
        
        return detected_configs
    
    def detect_app_config(self, app_name: str) -> Optional[Dict]:
        """Detect configuration for a specific application with advanced parsing"""
        if app_name not in self.app_configs:
            logger.warning(f"Unknown application: {app_name}")
            return None
        
        app_config = self.app_configs[app_name]
        
        # Handle always available apps (like GTK that generate themes dynamically)
        if app_config.get("always_available", False):
            return {
                "app": app_name,
                "format": app_config["format"],
                "found_configs": [{
                    "path": "generated",
                    "format": app_config["format"],
                    "writable": True,
                    "type": "generated",
                    "is_generated": True
                }],
                "theme_sections": app_config.get("theme_sections", []),
                "backup_name": app_config.get("backup_name", f"{app_name}.matyou.bak"),
                "dependency_graph": {},
                "is_generated": True
            }
        
        # Use advanced discovery for supported apps
        if app_config.get("supports_discovery", False):
            return self._advanced_discovery(app_name, app_config)
        
        # Standard detection with include parsing
        config_info = {
            "app": app_name,
            "format": app_config["format"],
            "found_configs": [],
            "theme_sections": app_config.get("theme_sections", []),
            "backup_name": app_config.get("backup_name", f"{app_name}.matyou.bak"),
            "dependency_graph": {}
        }
        
        discovered_files = set()
        
        # Check each possible path
        for path_pattern in app_config["paths"]:
            path = Path(path_pattern.replace("~", str(self.home_dir)))
            
            if path.is_dir():
                # Handle directory paths (scan for config files)
                self._scan_config_directory(path, app_config, config_info, discovered_files)
            elif path.exists():
                # Handle single file paths
                self._analyze_config_file_recursive(path, app_config, config_info, discovered_files)
        
        return config_info if config_info["found_configs"] else None
    
    def _advanced_discovery(self, app_name: str, app_config: Dict) -> Optional[Dict]:
        """Advanced discovery for apps like waybar that need special handling"""
        if app_name == "waybar":
            return self._discover_waybar_configs(app_config)
        
        # Add other advanced discovery methods here
        return None
    
    def _discover_waybar_configs(self, app_config: Dict) -> Optional[Dict]:
        """Advanced waybar configuration discovery"""
        from ..apps.waybar import WaybarThemer
        
        try:
            waybar_themer = WaybarThemer()
            all_configs = waybar_themer._discover_all_waybar_configs()
            
            if not all_configs:
                return None
            
            found_configs = []
            for config_set in all_configs:
                # Add config files
                for config_file in config_set["config_files"]:
                    found_configs.append({
                        "path": config_file["path"],
                        "format": "json",
                        "writable": config_file["writable"],
                        "instance": config_set["instance_name"],
                        "type": "config"
                    })
                
                # Add CSS files
                for css_file in config_set["css_files"]:
                    file_info = {
                        "path": css_file["path"],
                        "format": "css",
                        "writable": css_file["writable"],
                        "instance": config_set["instance_name"],
                        "type": "css",
                        "color_references": css_file["colors"]
                    }
                    found_configs.append(file_info)
            
            return {
                "app": "waybar",
                "format": "mixed",
                "found_configs": found_configs,
                "theme_sections": app_config.get("theme_sections", []),
                "backup_name": app_config.get("backup_name", "waybar.matyou.bak"),
                "instances": len(all_configs)
            }
            
        except Exception as e:
            logger.error(f"Error in advanced waybar discovery: {e}")
            return None
    
    def _scan_config_directory(self, directory: Path, app_config: Dict, 
                              config_info: Dict, discovered_files: Set[str]):
        """Scan a directory for configuration files"""
        try:
            for item in directory.rglob("*"):
                if item.is_file() and self._looks_like_config_file(item, app_config):
                    self._analyze_config_file_recursive(item, app_config, config_info, discovered_files)
        except Exception as e:
            logger.warning(f"Error scanning directory {directory}: {e}")
    
    def _looks_like_config_file(self, file_path: Path, app_config: Dict) -> bool:
        """Check if a file looks like a configuration file for the app"""
        format_type = app_config["format"]
        
        format_extensions = {
            "hyprland": [".conf"],
            "json": [".json", ".jsonc"],
            "rasi": [".rasi"],
            "kitty": [".conf"],
            "fish": [".fish"],
            "ini": [".ini", ".conf"],
            "css": [".css"]
        }
        
        valid_extensions = format_extensions.get(format_type, [])
        return file_path.suffix.lower() in valid_extensions
    
    def _analyze_config_file_recursive(self, file_path: Path, app_config: Dict, 
                                     config_info: Dict, discovered_files: Set[str]):
        """Analyze a config file and recursively follow includes"""
        file_path_str = str(file_path)
        
        if file_path_str in discovered_files or not file_path.exists():
            return
        
        discovered_files.add(file_path_str)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_info = {
                "path": file_path_str,
                "format": app_config["format"],
                "writable": os.access(file_path, os.W_OK),
                "size": file_path.stat().st_size,
                "color_references": self._extract_colors_from_string(content),
                "content": content,
                "included_files": []
            }
            
            config_info["found_configs"].append(file_info)
            
            # Follow includes if supported
            if app_config.get("supports_includes", False):
                included_files = self._find_included_files(content, file_path, app_config)
                file_info["included_files"] = [str(f) for f in included_files]
                
                # Recursively analyze included files
                for included_file in included_files:
                    self._analyze_config_file_recursive(included_file, app_config, config_info, discovered_files)
                    
                    # Build dependency graph
                    if file_path_str not in config_info["dependency_graph"]:
                        config_info["dependency_graph"][file_path_str] = []
                    config_info["dependency_graph"][file_path_str].append(str(included_file))
            
        except Exception as e:
            logger.error(f"Error analyzing config file {file_path}: {e}")
    
    def _find_included_files(self, content: str, base_file: Path, app_config: Dict) -> List[Path]:
        """Find files included by source/import statements"""
        included_files = []
        include_patterns = app_config.get("include_patterns", [])
        
        for pattern in include_patterns:
            matches = re.findall(pattern, content)
            
            for match in matches:
                # Resolve relative paths
                if match.startswith('~'):
                    included_path = Path(match.replace("~", str(self.home_dir)))
                elif match.startswith('/'):
                    included_path = Path(match)
                else:
                    included_path = base_file.parent / match
                
                if included_path.exists():
                    included_files.append(included_path)
                else:
                    logger.warning(f"Included file not found: {included_path}")
        
        return included_files
    
    def _extract_colors_from_string(self, text: str) -> List[str]:
        """Extract color values from a string"""
        colors = []
        
        # Hex colors
        hex_pattern = r'#[0-9a-fA-F]{3,8}\b'
        colors.extend(re.findall(hex_pattern, text))
        
        # RGB/RGBA colors
        rgb_pattern = r'rgba?\s*\(\s*[^)]+\)'
        colors.extend(re.findall(rgb_pattern, text))
        
        # HSL colors
        hsl_pattern = r'hsla?\s*\(\s*[^)]+\)'
        colors.extend(re.findall(hsl_pattern, text))
        
        # CSS variables (might contain colors)
        css_var_pattern = r'var\(--[^)]+\)'
        colors.extend(re.findall(css_var_pattern, text))
        
        return list(set(colors))  # Remove duplicates
    
    def get_config_dependencies(self, app_name: str) -> Dict[str, List[str]]:
        """Get dependency graph for an application's configs"""
        config_info = self.detect_app_config(app_name)
        if config_info:
            return config_info.get("dependency_graph", {})
        return {}
    
    def find_color_definition_files(self, app_name: str) -> List[str]:
        """Find which config files actually contain color definitions"""
        config_info = self.detect_app_config(app_name)
        if not config_info:
            return []
        
        color_files = []
        
        for config_file in config_info["found_configs"]:
            if config_file.get("color_references"):
                color_files.append(config_file["path"])
        
        return color_files
    
    def get_modular_config_summary(self, app_name: str) -> Dict[str, Any]:
        """Get a summary of modular configuration setup"""
        config_info = self.detect_app_config(app_name)
        if not config_info:
            return {}
        
        summary = {
            "total_files": len(config_info["found_configs"]),
            "writable_files": len([f for f in config_info["found_configs"] if f.get("writable", False)]),
            "files_with_colors": len([f for f in config_info["found_configs"] if f.get("color_references")]),
            "dependency_graph": config_info.get("dependency_graph", {}),
            "instances": config_info.get("instances", 1)
        }
        
        if app_name == "waybar":
            summary["waybar_instances"] = {}
            for config_file in config_info["found_configs"]:
                instance = config_file.get("instance", "main")
                if instance not in summary["waybar_instances"]:
                    summary["waybar_instances"][instance] = {"config_files": 0, "css_files": 0}
                
                if config_file.get("type") == "css":
                    summary["waybar_instances"][instance]["css_files"] += 1
                else:
                    summary["waybar_instances"][instance]["config_files"] += 1 