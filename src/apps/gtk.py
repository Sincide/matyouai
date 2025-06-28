#!/usr/bin/env python3
"""
GTK Themer for MatYouAI
Based on linkfrg's approach but adapted to our architecture
Generates GTK/libadwaita themes with Material You colors
"""

import os
import math
import asyncio
from pathlib import Path
from typing import Dict, Tuple
from jinja2 import Template
from PIL import Image

# Material You color library (same as linkfrg uses)
from materialyoucolor.quantize import QuantizeCelebi
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.score.score import Score


class GTKThemer:
    """
    GTK Themer implementing linkfrg's philosophy:
    - Authentic Material You colors via materialyoucolor library
    - Jinja2 templates for dynamic theme generation
    - Cache-based theme storage
    - Multi-mode (light/dark) support
    - System integration via gsettings
    """
    
    def __init__(self):
        self.cache_dir = Path.home() / ".cache" / "matyouai" / "gtk"
        self.templates_dir = Path(__file__).parent.parent / "templates" / "gtk"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def rgba_to_hex(self, rgba: list) -> str:
        """Convert RGBA list to hex color (linkfrg's utility)"""
        return "#{:02x}{:02x}{:02x}".format(*rgba)
    
    def calculate_optimal_size(self, width: int, height: int, bitmap_size: int) -> Tuple[int, int]:
        """Calculate optimal image size for color processing (linkfrg's approach)"""
        image_area = width * height
        bitmap_area = bitmap_size ** 2
        scale = math.sqrt(bitmap_area / image_area) if image_area > bitmap_area else 1
        new_width = round(width * scale)
        new_height = round(height * scale)
        if new_width == 0:
            new_width = 1
        if new_height == 0:
            new_height = 1
        return new_width, new_height
    
    def extract_material_you_colors(self, wallpaper_path: str, dark_mode: bool = False) -> Dict[str, str]:
        """
        Extract authentic Material You colors using Google's algorithm
        This is linkfrg's exact approach adapted to our needs
        """
        try:
            # Open and optimize image size
            image = Image.open(wallpaper_path)
            wsize, hsize = image.size
            wsize_new, hsize_new = self.calculate_optimal_size(wsize, hsize, 128)
            
            if wsize_new < wsize or hsize_new < hsize:
                image = image.resize((wsize_new, hsize_new), Image.Resampling.BICUBIC)
            
            # Extract pixel data
            pixel_len = image.width * image.height
            image_data = image.getdata()
            pixel_array = [image_data[_] for _ in range(0, pixel_len, 1)]
            
            # Google's Material You color extraction
            colors = QuantizeCelebi(pixel_array, 128)
            argb = Score.score(colors)[0]
            
            # Generate Material You color scheme
            hct = Hct.from_int(argb)
            scheme = SchemeTonalSpot(hct, dark_mode, 0.0)
            
            # Extract all Material Dynamic Colors
            material_colors = {}
            for color in vars(MaterialDynamicColors).keys():
                color_name = getattr(MaterialDynamicColors, color)
                if hasattr(color_name, "get_hct"):
                    rgba = color_name.get_hct(scheme).to_rgba()
                    material_colors[color] = self.rgba_to_hex(rgba)
            
            return material_colors
            
        except Exception as e:
            print(f"Error extracting Material You colors: {e}")
            return {}
    
    def render_template(self, template_path: str, output_path: str, colors: Dict[str, str], dark_mode: bool = False) -> None:
        """
        Render Jinja2 template with Material You colors (linkfrg's approach)
        """
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Add dark_mode flag to colors dict
            colors_with_mode = colors.copy()
            colors_with_mode['dark_mode'] = str(dark_mode).lower()
            
            # Render template
            template = Template(template_content)
            rendered = template.render(colors_with_mode)
            
            # Write output
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                f.write(rendered)
                
            print(f"✅ Generated GTK theme: {output_path}")
            
        except Exception as e:
            print(f"❌ Error rendering template {template_path}: {e}")
    
    def generate_themes(self, wallpaper_path: str) -> None:
        """
        Generate both light and dark GTK themes (linkfrg's multi-mode approach)
        """
        print(f"🎨 Generating GTK themes from wallpaper: {wallpaper_path}")
        
        # Extract colors for both modes
        light_colors = self.extract_material_you_colors(wallpaper_path, dark_mode=False)
        dark_colors = self.extract_material_you_colors(wallpaper_path, dark_mode=True)
        
        if not light_colors or not dark_colors:
            print("❌ Failed to extract Material You colors")
            return
        
        # Generate GTK-4/libadwaita theme
        self.render_template(
            str(self.templates_dir / "gtk4.css"),
            str(self.cache_dir / "gtk.css"),
            light_colors,
            dark_mode=False
        )
        
        self.render_template(
            str(self.templates_dir / "gtk4.css"), 
            str(self.cache_dir / "gtk-dark.css"),
            dark_colors,
            dark_mode=True
        )
        
        print(f"🎯 GTK themes generated in: {self.cache_dir}")
    
    def _is_material_you_palette(self, color_palette: Dict[str, str]) -> bool:
        """Check if color palette contains Material You color names"""
        material_you_keys = ["primary", "surface", "onSurface", "surfaceContainer", "primaryContainer"]
        return any(key in color_palette for key in material_you_keys)
    
    def _generate_dark_variant(self, color_palette: Dict[str, str]) -> Dict[str, str]:
        """Generate dark variant colors from light palette (basic implementation)"""
        # This is a simplified conversion - in practice you'd want proper color science
        dark_colors = color_palette.copy()
        # Add basic dark mode logic here if needed
        return dark_colors
    
    def _generate_themed_configs(self, light_colors: Dict[str, str], dark_colors: Dict[str, str], preview_mode: bool) -> bool:
        """Generate themed configurations with proper error handling"""
        try:
            # Generate GTK-4/libadwaita theme
            self.render_template(
                str(self.templates_dir / "gtk4.css"),
                str(self.cache_dir / "gtk.css"),
                light_colors,
                dark_mode=False
            )
            
            self.render_template(
                str(self.templates_dir / "gtk4.css"), 
                str(self.cache_dir / "gtk-dark.css"),
                dark_colors,
                dark_mode=True
            )
            
            print(f"🎯 GTK themes generated in: {self.cache_dir}")
            return True
        except Exception as e:
            print(f"❌ Error generating GTK themes: {e}")
            return False
    
    def install_themes(self) -> None:
        """
        Install generated themes to system locations (linkfrg's system integration)
        """
        try:
            # GTK-4 theme installation
            gtk4_config_dir = Path.home() / ".config" / "gtk-4.0"
            gtk4_config_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy generated theme
            light_theme = self.cache_dir / "gtk.css"
            dark_theme = self.cache_dir / "gtk-dark.css"
            
            if light_theme.exists():
                import shutil
                shutil.copy2(light_theme, gtk4_config_dir / "gtk.css")
                print(f"✅ Installed GTK-4 theme: {gtk4_config_dir / 'gtk.css'}")
                
            print("🎯 GTK themes installed successfully")
            
        except Exception as e:
            print(f"❌ Error installing GTK themes: {e}")
    
    async def reload_gtk_themes(self) -> None:
        """
        Reload GTK themes using gsettings (linkfrg's system reload approach)
        """
        try:
            # Force GTK theme reload by switching themes
            commands = [
                "gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita'",
                "gsettings set org.gnome.desktop.interface gtk-theme 'Material'", 
                "gsettings set org.gnome.desktop.interface color-scheme 'default'",
                "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'",
                "gsettings set org.gnome.desktop.interface color-scheme 'default'"
            ]
            
            for cmd in commands:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            
            print("✅ GTK themes reloaded successfully")
            
        except Exception as e:
            print(f"❌ Error reloading GTK themes: {e}")
    
    def apply_theme(self, color_palette: Dict[str, str], config_info: Dict, 
                   preview_mode: bool = False) -> bool:
        """
        Apply GTK theme using MatYouAI interface (compatible with other themers)
        """
        try:
            print("🚀 Starting GTK theme application...")
            
            # Convert MatYouAI color palette to Material You colors if needed
            if self._is_material_you_palette(color_palette):
                # Use provided Material You colors directly
                light_colors = color_palette.copy()
                dark_colors = self._generate_dark_variant(color_palette)
            else:
                # Extract Material You colors from wallpaper if available
                wallpaper_path = config_info.get("wallpaper_path")
                if wallpaper_path:
                    light_colors = self.extract_material_you_colors(wallpaper_path, dark_mode=False)
                    dark_colors = self.extract_material_you_colors(wallpaper_path, dark_mode=True)
                else:
                    # Fallback: try to use existing color palette
                    light_colors = color_palette
                    dark_colors = self._generate_dark_variant(color_palette)
            
            if not light_colors:
                print("❌ Failed to obtain Material You colors")
                return False
            
            # Generate themes
            success = self._generate_themed_configs(light_colors, dark_colors, preview_mode)
            
            if success and not preview_mode:
                # Install and reload themes
                self.install_themes()
                asyncio.run(self.reload_gtk_themes())
                print("✅ GTK theme application complete!")
            elif success and preview_mode:
                print("✅ GTK theme preview generated!")
            
            return success
            
        except Exception as e:
            print(f"❌ Error applying GTK theme: {e}")
            return False
    
    def apply_theme_from_wallpaper(self, wallpaper_path: str) -> None:
        """
        Complete theme application workflow from wallpaper (linkfrg's approach)
        """
        print("🚀 Starting GTK theme application...")
        
        # Generate themes
        self.generate_themes(wallpaper_path)
        
        # Install themes
        self.install_themes()
        
        # Reload GTK themes
        asyncio.run(self.reload_gtk_themes())
        
        print("✅ GTK theme application complete!")


def create_gtk_theme(wallpaper_path: str) -> None:
    """
    Main entry point for GTK theming (legacy interface)
    """
    themer = GTKThemer()
    themer.apply_theme_from_wallpaper(wallpaper_path)


if __name__ == "__main__":
    # Test with our test wallpaper
    test_wallpaper = "dotfiles/wallpapers/test_material_you.png"
    if os.path.exists(test_wallpaper):
        create_gtk_theme(test_wallpaper)
    else:
        print("❌ Test wallpaper not found") 