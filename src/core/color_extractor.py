#!/usr/bin/env python3
"""
Color Extraction Module for MatYouAI
Advanced color palette extraction using AI models and fallback algorithms
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import colorsys
import math

from .ai_models import OllamaManager, ImageAnalyzer

logger = logging.getLogger(__name__)

class MaterialYouColorExtractor:
    """Extract Material You compliant color palettes from wallpapers"""
    
    def __init__(self):
        self.ollama_manager = OllamaManager()
        self.image_analyzer = ImageAnalyzer(self.ollama_manager)
        
    def extract_palette(self, wallpaper_path: Path, use_ai: bool = True) -> Dict[str, str]:
        """Extract complete color palette from wallpaper"""
        try:
            if use_ai and self.ollama_manager.check_ollama_availability():
                logger.info("Using AI model for color extraction")
                palette = self.image_analyzer.analyze_image(wallpaper_path, "color_palette")
                if palette:
                    return self._enhance_palette(palette)
            
            logger.info("Using fallback color extraction")
            return self._fallback_extraction(wallpaper_path)
            
        except Exception as e:
            logger.error(f"Color extraction failed: {e}")
            return self._get_default_palette()
    
    def _enhance_palette(self, base_palette: Dict[str, str]) -> Dict[str, str]:
        """Enhance AI-generated palette with additional Material You colors"""
        enhanced = base_palette.copy()
        
        # Generate additional tonal variants
        primary = base_palette.get("primary", "#6750A4")
        secondary = base_palette.get("secondary", "#625B71")
        
        # Add tonal variants for primary
        enhanced.update({
            "primary_10": self._lighten_color(primary, 0.9),
            "primary_20": self._lighten_color(primary, 0.8),
            "primary_30": self._lighten_color(primary, 0.7),
            "primary_40": self._lighten_color(primary, 0.6),
            "primary_50": primary,
            "primary_60": self._darken_color(primary, 0.1),
            "primary_70": self._darken_color(primary, 0.2),
            "primary_80": self._darken_color(primary, 0.3),
            "primary_90": self._darken_color(primary, 0.4),
            "primary_95": self._darken_color(primary, 0.5),
            "primary_99": self._darken_color(primary, 0.6),
        })
        
        # Add tonal variants for secondary
        enhanced.update({
            "secondary_10": self._lighten_color(secondary, 0.9),
            "secondary_20": self._lighten_color(secondary, 0.8),
            "secondary_30": self._lighten_color(secondary, 0.7),
            "secondary_40": self._lighten_color(secondary, 0.6),
            "secondary_50": secondary,
            "secondary_60": self._darken_color(secondary, 0.1),
            "secondary_70": self._darken_color(secondary, 0.2),
            "secondary_80": self._darken_color(secondary, 0.3),
            "secondary_90": self._darken_color(secondary, 0.4),
        })
        
        # Add neutral variants
        enhanced.update({
            "neutral_10": "#FEFBFF",
            "neutral_20": "#F5F0F7",
            "neutral_30": "#E8E0E8",
            "neutral_40": "#CAC4CF",
            "neutral_50": "#8E8B91",
            "neutral_60": "#76727E",
            "neutral_70": "#5F5B66",
            "neutral_80": "#49454E",
            "neutral_90": "#322F37",
            "neutral_95": "#211F26",
            "neutral_99": "#121113",
        })
        
        # Error and warning colors
        enhanced.update({
            "error": "#BA1A1A",
            "error_container": "#FFDAD6",
            "on_error": "#FFFFFF",
            "on_error_container": "#410002",
            "warning": "#F57C00",
            "warning_container": "#FFECB3",
            "success": "#4CAF50",
            "success_container": "#C8E6C9",
        })
        
        return enhanced
    
    def _fallback_extraction(self, wallpaper_path: Path) -> Dict[str, str]:
        """Advanced fallback color extraction using image analysis"""
        try:
            from PIL import Image, ImageFilter
            import numpy as np
            from sklearn.cluster import KMeans
            
            with Image.open(wallpaper_path) as img:
                img = img.convert('RGB')
                
                # Resize for processing
                img = img.resize((300, 300))
                
                # Apply slight blur to smooth out noise
                img = img.filter(ImageFilter.GaussianBlur(radius=1))
                
                # Convert to numpy array
                img_array = np.array(img)
                img_array = img_array.reshape((-1, 3))
                
                # Use K-means clustering to find dominant colors
                n_colors = 8
                kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
                kmeans.fit(img_array)
                
                # Get the colors and their frequencies
                colors = kmeans.cluster_centers_.astype(int)
                labels = kmeans.labels_
                label_counts = np.bincount(labels)
                
                # Sort by frequency
                color_freq = list(zip(colors, label_counts))
                color_freq.sort(key=lambda x: x[1], reverse=True)
                
                # Extract primary colors
                dominant_colors = [self._rgb_to_hex(color[0]) for color in color_freq[:4]]
                
                # Generate Material You palette
                return self._generate_material_palette(dominant_colors)
                
        except ImportError:
            logger.warning("Advanced libraries not available, using basic extraction")
            return self._basic_fallback_extraction(wallpaper_path)
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return self._get_default_palette()
    
    def _basic_fallback_extraction(self, wallpaper_path: Path) -> Dict[str, str]:
        """Basic fallback using PIL only"""
        try:
            from PIL import Image
            
            with Image.open(wallpaper_path) as img:
                img = img.convert('RGB')
                img = img.resize((150, 150))
                
                # Get most common colors
                colors = img.getcolors(maxcolors=256*256*256)
                if not colors:
                    return self._get_default_palette()
                
                colors = sorted(colors, key=lambda x: x[0], reverse=True)
                
                # Convert to hex
                hex_colors = []
                for count, rgb in colors[:8]:
                    hex_color = self._rgb_to_hex(rgb)
                    hex_colors.append(hex_color)
                
                return self._generate_material_palette(hex_colors)
                
        except Exception as e:
            logger.error(f"Basic fallback failed: {e}")
            return self._get_default_palette()
    
    def _generate_material_palette(self, dominant_colors: List[str]) -> Dict[str, str]:
        """Generate Material You compliant palette from dominant colors"""
        if not dominant_colors:
            return self._get_default_palette()
        
        # Select primary color (most vibrant)
        primary = self._select_primary_color(dominant_colors)
        
        # Generate secondary color
        secondary = self._generate_secondary_color(primary, dominant_colors)
        
        # Generate base palette
        base_palette = {
            "primary": primary,
            "secondary": secondary,
            "background": "#FFFBFE",
            "surface": "#F7F2FA",
            "accent": self._generate_accent_color(primary),
            "on_primary": "#FFFFFF" if self._is_dark_color(primary) else "#000000",
            "on_secondary": "#FFFFFF" if self._is_dark_color(secondary) else "#000000",
            "on_background": "#1C1B1F",
            "on_surface": "#1C1B1F"
        }
        
        return self._enhance_palette(base_palette)
    
    def _select_primary_color(self, colors: List[str]) -> str:
        """Select the most suitable primary color"""
        best_color = colors[0]
        best_score = 0
        
        for color in colors[:4]:  # Check top 4 colors
            # Score based on saturation and vibrancy
            h, s, v = self._hex_to_hsv(color)
            
            # Prefer colors with good saturation and value
            score = s * 0.7 + v * 0.3
            
            # Boost score for colors in preferred hue ranges
            if 240 <= h <= 300 or 0 <= h <= 60:  # Purple/pink/red range
                score *= 1.2
            elif 180 <= h <= 240:  # Blue range
                score *= 1.1
            
            if score > best_score:
                best_score = score
                best_color = color
        
        return best_color
    
    def _generate_secondary_color(self, primary: str, available_colors: List[str]) -> str:
        """Generate or select secondary color"""
        primary_h, primary_s, primary_v = self._hex_to_hsv(primary)
        
        # Try to find a good secondary from available colors
        for color in available_colors[1:4]:
            h, s, v = self._hex_to_hsv(color)
            
            # Good secondary should be different enough in hue
            hue_diff = abs(h - primary_h)
            if hue_diff > 180:
                hue_diff = 360 - hue_diff
            
            if 30 <= hue_diff <= 150 and s > 0.2:
                return color
        
        # Generate secondary algorithmically
        secondary_h = (primary_h + 60) % 360  # Complementary-ish
        secondary_s = max(0.3, primary_s - 0.2)
        secondary_v = min(1.0, primary_v - 0.1)
        
        return self._hsv_to_hex(secondary_h, secondary_s, secondary_v)
    
    def _generate_accent_color(self, primary: str) -> str:
        """Generate accent color from primary"""
        h, s, v = self._hex_to_hsv(primary)
        
        # Make accent more vibrant
        accent_s = min(1.0, s + 0.2)
        accent_v = min(1.0, v + 0.1)
        
        return self._hsv_to_hex(h, accent_s, accent_v)
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a color by mixing with white"""
        r, g, b = self._hex_to_rgb(hex_color)
        
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        return self._rgb_to_hex((r, g, b))
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a color by reducing brightness"""
        r, g, b = self._hex_to_rgb(hex_color)
        
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        
        return self._rgb_to_hex((r, g, b))
    
    def _is_dark_color(self, hex_color: str) -> bool:
        """Check if color is dark (for determining text color)"""
        r, g, b = self._hex_to_rgb(hex_color)
        
        # Calculate perceived brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _hex_to_hsv(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSV"""
        r, g, b = self._hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        return h * 360, s, v
    
    def _hsv_to_hex(self, h: float, s: float, v: float) -> str:
        """Convert HSV to hex color"""
        r, g, b = colorsys.hsv_to_rgb(h/360.0, s, v)
        return self._rgb_to_hex((int(r*255), int(g*255), int(b*255)))
    
    def _get_default_palette(self) -> Dict[str, str]:
        """Get default Material You palette"""
        return {
            "primary": "#6750A4",
            "secondary": "#625B71",
            "background": "#FFFBFE",
            "surface": "#F7F2FA",
            "accent": "#7C4DFF",
            "on_primary": "#FFFFFF",
            "on_secondary": "#FFFFFF",
            "on_background": "#1C1B1F",
            "on_surface": "#1C1B1F",
            # Extended tonal palette
            "primary_10": "#21005D",
            "primary_20": "#381E72",
            "primary_30": "#4F378B",
            "primary_40": "#6750A4",
            "primary_50": "#7F67BE",
            "primary_60": "#9A82DB",
            "primary_70": "#B69DF8",
            "primary_80": "#D0BCFF",
            "primary_90": "#EADDFF",
            "primary_95": "#F6EDFF",
            "primary_99": "#FFFBFE",
            "secondary_10": "#1D192B",
            "secondary_20": "#332D41",
            "secondary_30": "#4A4458",
            "secondary_40": "#625B71",
            "secondary_50": "#7A7289",
            "secondary_60": "#958DA5",
            "secondary_70": "#B0A7C0",
            "secondary_80": "#CCC2DC",
            "secondary_90": "#E8DEF8",
            "neutral_10": "#1C1B1F",
            "neutral_20": "#313033",
            "neutral_30": "#48464C",
            "neutral_40": "#605D64",
            "neutral_50": "#79767D",
            "neutral_60": "#938F96",
            "neutral_70": "#AEA9B1",
            "neutral_80": "#CAC4D0",
            "neutral_90": "#E6E0E9",
            "neutral_95": "#F4EFF4",
            "neutral_99": "#FFFBFE",
            "error": "#BA1A1A",
            "error_container": "#FFDAD6",
            "on_error": "#FFFFFF",
            "on_error_container": "#410002",
            "warning": "#F57C00",
            "warning_container": "#FFECB3",
            "success": "#4CAF50",
            "success_container": "#C8E6C9",
        }

class PaletteValidator:
    """Validate and adjust color palettes for accessibility and aesthetics"""
    
    @staticmethod
    def validate_contrast(fg_color: str, bg_color: str, min_ratio: float = 4.5) -> bool:
        """Check if color combination meets WCAG contrast requirements"""
        fg_luminance = PaletteValidator._get_luminance(fg_color)
        bg_luminance = PaletteValidator._get_luminance(bg_color)
        
        lighter = max(fg_luminance, bg_luminance)
        darker = min(fg_luminance, bg_luminance)
        
        contrast_ratio = (lighter + 0.05) / (darker + 0.05)
        return contrast_ratio >= min_ratio
    
    @staticmethod
    def _get_luminance(hex_color: str) -> float:
        """Calculate relative luminance of a color"""
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Convert to sRGB
        r, g, b = r/255.0, g/255.0, b/255.0
        
        # Apply gamma correction
        def gamma_correct(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r = gamma_correct(r)
        g = gamma_correct(g)
        b = gamma_correct(b)
        
        # Calculate luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    @staticmethod
    def adjust_for_accessibility(palette: Dict[str, str]) -> Dict[str, str]:
        """Adjust palette colors to meet accessibility standards"""
        adjusted = palette.copy()
        
        # Ensure text colors have sufficient contrast
        if not PaletteValidator.validate_contrast(adjusted["on_primary"], adjusted["primary"]):
            adjusted["on_primary"] = "#FFFFFF" if PaletteValidator._is_dark(adjusted["primary"]) else "#000000"
        
        if not PaletteValidator.validate_contrast(adjusted["on_secondary"], adjusted["secondary"]):
            adjusted["on_secondary"] = "#FFFFFF" if PaletteValidator._is_dark(adjusted["secondary"]) else "#000000"
        
        if not PaletteValidator.validate_contrast(adjusted["on_background"], adjusted["background"]):
            adjusted["on_background"] = "#000000" if PaletteValidator._is_light(adjusted["background"]) else "#FFFFFF"
        
        return adjusted
    
    @staticmethod
    def _is_dark(hex_color: str) -> bool:
        """Check if color is dark"""
        return PaletteValidator._get_luminance(hex_color) < 0.5
    
    @staticmethod
    def _is_light(hex_color: str) -> bool:
        """Check if color is light"""
        return PaletteValidator._get_luminance(hex_color) > 0.5 