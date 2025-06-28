#!/usr/bin/env python3
"""
Wallpaper Picker for MatYouAI
Integrates with rofi to provide wallpaper selection and theme triggering
"""

import subprocess
import logging
from typing import List, Optional, Dict
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class WallpaperPicker:
    """Handles wallpaper selection via rofi and swww integration"""
    
    def __init__(self, wallpaper_dirs: Optional[List[str]] = None):
        self.wallpaper_dirs = wallpaper_dirs or [
            "~/Pictures/wallpapers",
            "~/Pictures",
            "~/Downloads",
            "/usr/share/pixmaps",
            "/usr/share/backgrounds"
        ]
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        
    def find_wallpapers(self) -> List[Dict[str, str]]:
        """Find all wallpapers in configured directories"""
        wallpapers = []
        
        for dir_path in self.wallpaper_dirs:
            expanded_path = Path(dir_path.replace("~", str(Path.home())))
            
            if not expanded_path.exists():
                continue
                
            try:
                for file_path in expanded_path.rglob("*"):
                    if (file_path.is_file() and 
                        file_path.suffix.lower() in self.supported_formats):
                        
                        wallpapers.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "dir": str(file_path.parent),
                            "size": file_path.stat().st_size
                        })
            except PermissionError:
                logger.warning(f"Permission denied accessing {expanded_path}")
            except Exception as e:
                logger.error(f"Error scanning {expanded_path}: {e}")
        
        # Sort by name
        wallpapers.sort(key=lambda x: x["name"])
        return wallpapers
    
    def show_rofi_picker(self, wallpapers: List[Dict[str, str]]) -> Optional[str]:
        """Show rofi picker for wallpaper selection"""
        try:
            # Prepare rofi options
            rofi_options = []
            for wp in wallpapers:
                # Show name and directory for context
                display_name = f"{wp['name']} ({wp['dir']})"
                rofi_options.append(display_name)
            
            if not rofi_options:
                logger.error("No wallpapers found")
                return None
            
            # Create rofi input
            rofi_input = "\n".join(rofi_options)
            
            # Run rofi
            cmd = [
                "rofi", "-dmenu", 
                "-p", "Select Wallpaper",
                "-i",  # case insensitive
                "-format", "i",  # return index
                "-theme-str", "window { width: 60%; } listview { lines: 10; }"
            ]
            
            result = subprocess.run(
                cmd, 
                input=rofi_input, 
                text=True, 
                capture_output=True
            )
            
            if result.returncode == 0:
                try:
                    selected_index = int(result.stdout.strip())
                    if 0 <= selected_index < len(wallpapers):
                        selected_wallpaper = wallpapers[selected_index]["path"]
                        logger.info(f"Selected wallpaper: {selected_wallpaper}")
                        return selected_wallpaper
                except (ValueError, IndexError):
                    logger.error("Invalid selection from rofi")
            else:
                logger.info("Rofi selection cancelled")
            
            return None
            
        except FileNotFoundError:
            logger.error("rofi not found. Please install rofi.")
            return None
        except Exception as e:
            logger.error(f"Error running rofi picker: {e}")
            return None
    
    def set_wallpaper_with_swww(self, wallpaper_path: str) -> bool:
        """Set wallpaper using swww"""
        try:
            # Check if swww daemon is running
            check_cmd = ["pgrep", "swww-daemon"]
            check_result = subprocess.run(check_cmd, capture_output=True)
            
            if check_result.returncode != 0:
                logger.info("Starting swww daemon...")
                start_cmd = ["swww", "init"]
                start_result = subprocess.run(start_cmd, capture_output=True)
                
                if start_result.returncode != 0:
                    logger.error("Failed to start swww daemon")
                    return False
            
            # Set wallpaper
            set_cmd = ["swww", "img", wallpaper_path, "--transition-type", "fade"]
            set_result = subprocess.run(set_cmd, capture_output=True, text=True)
            
            if set_result.returncode == 0:
                logger.info(f"Wallpaper set successfully: {wallpaper_path}")
                return True
            else:
                logger.error(f"Failed to set wallpaper: {set_result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("swww not found. Please install swww.")
            return False
        except Exception as e:
            logger.error(f"Error setting wallpaper with swww: {e}")
            return False
    
    def launch_picker_and_apply_theme(self, theme_applicator=None, 
                                    preview_mode: bool = False) -> Optional[Dict]:
        """Launch wallpaper picker and apply theme in one go"""
        try:
            # Find wallpapers
            wallpapers = self.find_wallpapers()
            if not wallpapers:
                logger.error("No wallpapers found in configured directories")
                return None
            
            # Show picker
            selected_wallpaper = self.show_rofi_picker(wallpapers)
            if not selected_wallpaper:
                return None
            
            # Set wallpaper
            if not preview_mode:
                if not self.set_wallpaper_with_swww(selected_wallpaper):
                    logger.warning("Failed to set wallpaper, but continuing with theme application")
            
            # Apply theme if theme_applicator is provided
            if theme_applicator:
                logger.info("Applying theme from selected wallpaper...")
                
                theme_name = f"wallpaper_{Path(selected_wallpaper).stem}"
                result = theme_applicator.apply_theme_from_wallpaper(
                    selected_wallpaper, 
                    theme_name=theme_name,
                    preview_mode=preview_mode
                )
                
                result["wallpaper_set"] = not preview_mode
                return result
            else:
                return {
                    "success": True,
                    "wallpaper_path": selected_wallpaper,
                    "wallpaper_set": not preview_mode,
                    "theme_applied": False
                }
                
        except Exception as e:
            logger.error(f"Error in picker and theme application: {e}")
            return None
    
    def create_rofi_theme_switcher(self, theme_applicator=None) -> Optional[str]:
        """Create a rofi-based theme switcher for existing themes"""
        try:
            if not theme_applicator:
                return None
            
            # Get available themes
            themes = theme_applicator.get_available_themes()
            if not themes:
                logger.info("No existing themes found")
                return None
            
            # Prepare rofi options
            rofi_options = []
            for theme in themes:
                theme_name = theme.get("theme_name", "Unknown")
                readable_time = theme.get("readable_time", theme.get("timestamp", ""))
                display_name = f"{theme_name} ({readable_time})"
                rofi_options.append(display_name)
            
            # Add special options
            rofi_options.insert(0, "🎨 Pick New Wallpaper")
            rofi_options.insert(1, "👁️ Preview Mode")
            
            rofi_input = "\n".join(rofi_options)
            
            # Run rofi
            cmd = [
                "rofi", "-dmenu",
                "-p", "MatYouAI Theme",
                "-i",
                "-format", "i",
                "-theme-str", "window { width: 50%; } listview { lines: 8; }"
            ]
            
            result = subprocess.run(
                cmd,
                input=rofi_input,
                text=True,
                capture_output=True
            )
            
            if result.returncode == 0:
                try:
                    selected_index = int(result.stdout.strip())
                    
                    if selected_index == 0:
                        # Pick new wallpaper
                        return "new_wallpaper"
                    elif selected_index == 1:
                        # Preview mode
                        return "preview_mode"
                    elif 2 <= selected_index < len(rofi_options):
                        # Restore existing theme
                        theme_index = selected_index - 2
                        if theme_index < len(themes):
                            snapshot_id = themes[theme_index]["snapshot_id"]
                            return f"restore:{snapshot_id}"
                    
                except (ValueError, IndexError):
                    logger.error("Invalid selection from rofi")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in theme switcher: {e}")
            return None
    
    def show_theme_preview(self, wallpaper_path: str, theme_applicator=None) -> bool:
        """Show theme preview with rofi confirmation"""
        try:
            if not theme_applicator:
                return False
            
            # Generate preview
            preview_result = theme_applicator.preview_theme(wallpaper_path)
            
            if not preview_result.get("success", False):
                self._show_rofi_message("Preview Failed", 
                                       f"Could not generate theme preview: {preview_result.get('errors', ['Unknown error'])}")
                return False
            
            # Show preview results
            palette = preview_result.get("color_palette", {})
            applied_apps = preview_result.get("applied_apps", [])
            
            preview_info = f"""Theme Preview
Wallpaper: {Path(wallpaper_path).name}
Primary Color: {palette.get('primary', 'N/A')}
Secondary Color: {palette.get('secondary', 'N/A')}
Apps: {', '.join(applied_apps) if applied_apps else 'None'}

Apply this theme?"""
            
            cmd = [
                "rofi", "-dmenu",
                "-p", "Apply Theme?",
                "-mesg", preview_info,
                "-theme-str", "window { width: 40%; }"
            ]
            
            confirm_options = "Yes\nNo"
            result = subprocess.run(
                cmd,
                input=confirm_options,
                text=True,
                capture_output=True
            )
            
            if result.returncode == 0 and result.stdout.strip().lower() == "yes":
                # Apply the theme for real
                apply_result = theme_applicator.apply_theme_from_wallpaper(
                    wallpaper_path,
                    theme_name=f"applied_{Path(wallpaper_path).stem}"
                )
                
                if apply_result.get("success", False):
                    self._show_rofi_message("Success", "Theme applied successfully!")
                    return True
                else:
                    self._show_rofi_message("Error", f"Failed to apply theme: {apply_result.get('errors', ['Unknown error'])}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error in theme preview: {e}")
            return False
    
    def _show_rofi_message(self, title: str, message: str):
        """Show a message using rofi"""
        try:
            cmd = [
                "rofi", "-e", f"{title}: {message}",
                "-theme-str", "window { width: 30%; }"
            ]
            subprocess.run(cmd, capture_output=True)
        except:
            pass  # Fallback to logger if rofi fails
            logger.info(f"{title}: {message}") 