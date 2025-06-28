#!/usr/bin/env python3
"""
Theme Applicator for MatYouAI
Main orchestrator for applying Material You themes across applications
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .config_detector import ConfigDetector
from .color_extractor import MaterialYouColorExtractor  
from .ai_models import OllamaManager, ConfigGenerator
from ..utils.backup import ConfigBackupManager
from ..apps.hyprland import HyprlandThemer
from ..apps.kitty import KittyThemer
from ..apps.waybar import WaybarThemer
from ..apps.rofi import RofiThemer
from ..apps.dunst import DunstThemer
from ..apps.gtk import GTKThemer

logger = logging.getLogger(__name__)

class ThemeApplicator:
    """Main theme application orchestrator (handles complex configurations)"""
    
    def __init__(self):
        self.config_detector = ConfigDetector()
        self.color_extractor = MaterialYouColorExtractor()
        self.backup_manager = ConfigBackupManager()
        self.ollama_manager = OllamaManager()
        self.config_generator = ConfigGenerator(self.ollama_manager)
        
        # Register all application themers
        self.themers = {
            "hyprland": HyprlandThemer(),
            "kitty": KittyThemer(),
            "waybar": WaybarThemer(),
            "rofi": RofiThemer(),
            "dunst": DunstThemer(),
            "gtk": GTKThemer()
        }
        
        # Track which apps have modular configs
        self.modular_apps = set()
    
    def apply_theme_from_wallpaper(self, wallpaper_path: str, apps: Optional[List[str]] = None, 
                                  preview_mode: bool = False, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """Apply Material You theme extracted from wallpaper"""
        try:
            logger.info(f"Applying theme from wallpaper: {wallpaper_path}")
            
            # Extract color palette from wallpaper
            color_palette = self.color_extractor.extract_palette(Path(wallpaper_path))
            
            if not color_palette:
                return {"success": False, "error": "Failed to extract colors from wallpaper"}
            
            # Apply the extracted theme
            return self.apply_theme(color_palette, apps, preview_mode, theme_name)
            
        except Exception as e:
            logger.error(f"Error applying theme from wallpaper: {e}")
            return {"success": False, "error": str(e)}
    
    def apply_theme(self, color_palette: Dict[str, str], apps: Optional[List[str]] = None, 
                   preview_mode: bool = False, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """Apply Material You theme to specified applications (handles modular configs)"""
        try:
            # Detect all configurations
            all_configs = self.config_detector.detect_all_configs()
            
            if not all_configs:
                return {"success": False, "error": "No supported application configurations found"}
            
            # Filter to requested apps or use all detected
            target_apps = apps if apps else list(all_configs.keys())
            
            results = {
                "success": True,
                "applied_apps": [],
                "failed_apps": [],
                "skipped_apps": [],
                "modular_configs": {},
                "theme_name": theme_name,
                "preview_mode": preview_mode,
                "color_palette": color_palette
            }
            
            # Create backup snapshot if not in preview mode
            if not preview_mode and theme_name:
                try:
                    snapshot_id = self.backup_manager.create_theme_snapshot(
                        theme_name, all_configs, color_palette
                    )
                    results["snapshot_id"] = snapshot_id
                    logger.info(f"Created theme snapshot: {snapshot_id}")
                except Exception as e:
                    logger.warning(f"Failed to create backup snapshot: {e}")
            
            # Apply theme to each application
            for app_name in target_apps:
                if app_name not in all_configs:
                    results["skipped_apps"].append({
                        "app": app_name,
                        "reason": "Configuration not found"
                    })
                    continue
                
                config_info = all_configs[app_name]
                
                try:
                    # Log modular configuration information
                    if app_name in ["hyprland", "waybar"]:
                        modular_summary = self.config_detector.get_modular_config_summary(app_name)
                        results["modular_configs"][app_name] = modular_summary
                        
                        if modular_summary.get("total_files", 0) > 1:
                            self.modular_apps.add(app_name)
                            logger.info(f"Detected modular {app_name} config: {modular_summary['total_files']} files")
                    
                    # Apply theme using appropriate themer
                    if self._apply_app_theme(app_name, color_palette, config_info, preview_mode):
                        results["applied_apps"].append({
                            "app": app_name,
                            "files_modified": len(config_info["found_configs"]),
                            "is_modular": app_name in self.modular_apps
                        })
                        logger.info(f"Successfully applied theme to {app_name}")
                    else:
                        results["failed_apps"].append({
                            "app": app_name,
                            "reason": "Theme application failed"
                        })
                        
                except Exception as e:
                    logger.error(f"Error applying theme to {app_name}: {e}")
                    results["failed_apps"].append({
                        "app": app_name,
                        "reason": str(e)
                    })
            
            # Update overall success status
            results["success"] = len(results["applied_apps"]) > 0
            
            # Reload configurations if successful and not in preview mode
            if results["success"] and not preview_mode:
                self._reload_applications(results["applied_apps"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error in theme application: {e}")
            return {"success": False, "error": str(e)}
    
    def _apply_app_theme(self, app_name: str, color_palette: Dict[str, str], 
                        config_info: Dict, preview_mode: bool) -> bool:
        """Apply theme to a specific application"""
        
        # Use dedicated themer if available
        if app_name in self.themers:
            themer = self.themers[app_name]
            return themer.apply_theme(color_palette, config_info, preview_mode)
        
        # Fallback to AI-generated config patches
        logger.info(f"No dedicated themer for {app_name}, using AI fallback")
        return self._apply_theme_with_ai(app_name, color_palette, config_info, preview_mode)
    
    def _apply_theme_with_ai(self, app_name: str, color_palette: Dict[str, str], 
                           config_info: Dict, preview_mode: bool) -> bool:
        """Fallback method using AI to generate config patches"""
        try:
            # Check if any models are available 
            models = self.ollama_manager.list_models()
            if not models:
                logger.warning("AI fallback not available - no Ollama models found")
                return False
            
            success_count = 0
            
            for config_file in config_info["found_configs"]:
                if not config_file.get("writable", False):
                    continue
                
                try:
                    # Use ConfigGenerator to create the patch
                    current_config = config_file.get("content", "")
                    config_format = config_file.get("format", "unknown")
                    
                    ai_patch = self.config_generator.generate_config_patch(
                        app_name, config_format, color_palette, current_config
                    )
                    
                    if ai_patch and not preview_mode:
                        # Apply the AI-generated patch
                        with open(config_file["path"], 'w') as f:
                            f.write(ai_patch)
                        success_count += 1
                        
                    elif ai_patch and preview_mode:
                        logger.info(f"AI generated patch for {config_file['path']}")
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"Error applying AI patch to {config_file['path']}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in AI theme application for {app_name}: {e}")
            return False
    
    def _reload_applications(self, applied_apps: List[Dict]) -> None:
        """Reload applications after theme changes"""
        for app_info in applied_apps:
            app_name = app_info["app"]
            
            try:
                if app_name in self.themers:
                    themer = self.themers[app_name]
                    
                    # Call reload method if available
                    if hasattr(themer, 'reload_waybar'):
                        themer.reload_waybar()
                    elif hasattr(themer, 'reload_config'):
                        themer.reload_config()
                    elif hasattr(themer, 'reload_dunst'):
                        themer.reload_dunst()
                    elif hasattr(themer, 'reload_rofi'):
                        themer.reload_rofi()
                        
            except Exception as e:
                logger.warning(f"Failed to reload {app_name}: {e}")
    
    def preview_theme(self, color_palette: Dict[str, str], apps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Preview theme changes without applying them"""
        return self.apply_theme(color_palette, apps, preview_mode=True)
    
    def get_supported_applications(self) -> List[str]:
        """Get list of all supported applications"""
        return list(self.themers.keys())
    
    def get_detected_applications(self) -> Dict[str, Dict]:
        """Get detected application configurations with modular info"""
        all_configs = self.config_detector.detect_all_configs()
        
        enhanced_configs = {}
        for app_name, config_info in all_configs.items():
            enhanced_configs[app_name] = {
                **config_info,
                "has_themer": app_name in self.themers,
                "modular_summary": self.config_detector.get_modular_config_summary(app_name)
            }
        
        return enhanced_configs
    
    def validate_color_palette(self, color_palette: Dict[str, str]) -> Dict[str, Any]:
        """Validate a Material You color palette"""
        required_colors = [
            "primary", "secondary", "surface", "on_surface", 
            "background", "on_background"
        ]
        
        validation = {
            "valid": True,
            "missing_colors": [],
            "invalid_colors": [],
            "warnings": []
        }
        
        # Check for required colors
        for color_key in required_colors:
            if color_key not in color_palette:
                validation["missing_colors"].append(color_key)
                validation["valid"] = False
        
        # Validate color format
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        
        for color_key, color_value in color_palette.items():
            if not hex_pattern.match(color_value):
                validation["invalid_colors"].append({
                    "key": color_key,
                    "value": color_value,
                    "reason": "Invalid hex format"
                })
                validation["valid"] = False
        
        # Check color contrast (basic validation)
        if "surface" in color_palette and "on_surface" in color_palette:
            # This is a simplified contrast check
            surface = color_palette["surface"]
            on_surface = color_palette["on_surface"]
            
            if surface.lower() == on_surface.lower():
                validation["warnings"].append("Surface and on_surface colors are identical")
        
        return validation
    
    def analyze_modular_configurations(self) -> Dict[str, Any]:
        """Analyze and report on modular configuration setups"""
        analysis = {
            "total_apps": 0,
            "modular_apps": 0,
            "single_file_apps": 0,
            "app_details": {},
            "recommendations": []
        }
        
        all_configs = self.config_detector.detect_all_configs()
        analysis["total_apps"] = len(all_configs)
        
        for app_name, config_info in all_configs.items():
            summary = self.config_detector.get_modular_config_summary(app_name)
            
            is_modular = summary.get("total_files", 0) > 1
            
            if is_modular:
                analysis["modular_apps"] += 1
            else:
                analysis["single_file_apps"] += 1
            
            analysis["app_details"][app_name] = {
                "is_modular": is_modular,
                "total_files": summary.get("total_files", 0),
                "files_with_colors": summary.get("files_with_colors", 0),
                "dependency_graph": summary.get("dependency_graph", {}),
                "instances": summary.get("instances", 1)
            }
            
            # Generate recommendations
            if is_modular and summary.get("files_with_colors", 0) == 0:
                analysis["recommendations"].append(
                    f"{app_name}: Modular config detected but no color files found. "
                    "Theme application may not work properly."
                )
            
            if app_name == "waybar" and summary.get("instances", 1) > 1:
                analysis["recommendations"].append(
                    f"waybar: Multiple instances detected ({summary['instances']}). "
                    "All instances will be themed."
                )
        
        return analysis 