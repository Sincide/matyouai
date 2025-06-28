#!/usr/bin/env python3
"""
AI Models Integration for MatYouAI
Handles Ollama integration for local AI model operations
"""

import json
import subprocess
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class OllamaManager:
    """Manages Ollama model operations for local AI processing"""
    
    def __init__(self):
        self.available_models = {}
        self.preloaded_models = set()
        
    def check_ollama_availability(self) -> bool:
        """Check if Ollama is installed and running"""
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def list_models(self) -> Dict[str, Dict]:
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to list models: {result.stderr}")
                return {}
            
            models = {}
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        size = parts[1]
                        modified = ' '.join(parts[2:])
                        models[name] = {
                            'size': size,
                            'modified': modified,
                            'loaded': False
                        }
            
            self.available_models = models
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return {}
    
    def preload_model(self, model_name: str) -> bool:
        """Preload a model to reduce inference latency"""
        if model_name in self.preloaded_models:
            return True
            
        try:
            logger.info(f"Preloading model: {model_name}")
            # Send a minimal request to warm up the model
            result = subprocess.run([
                'ollama', 'run', model_name, 
                '--verbose', 'echo "warming up"'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.preloaded_models.add(model_name)
                logger.info(f"Model {model_name} preloaded successfully")
                return True
            else:
                logger.error(f"Failed to preload {model_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error preloading model {model_name}: {e}")
            return False
    
    def generate_response(self, model_name: str, prompt: str, 
                         system_prompt: str = None, **kwargs) -> Optional[str]:
        """Generate response from Ollama model"""
        try:
            cmd = ['ollama', 'run', model_name]
            
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            else:
                full_prompt = prompt
            
            result = subprocess.run(
                cmd, 
                input=full_prompt, 
                capture_output=True, 
                text=True, 
                timeout=kwargs.get('timeout', 60)
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Model generation failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Model {model_name} timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

class ImageAnalyzer:
    """Handles image analysis using local vision models"""
    
    def __init__(self, ollama_manager: OllamaManager):
        self.ollama = ollama_manager
        self.vision_models = ['llava:7b', 'llava:13b', 'llava:34b', 'bakllava']
        
    def find_available_vision_model(self) -> Optional[str]:
        """Find the best available vision model"""
        available = self.ollama.list_models()
        
        for model in self.vision_models:
            if model in available:
                return model
                
        # Check for partial matches (e.g., llava:latest, llava)
        for available_model in available:
            if any(vm.split(':')[0] in available_model for vm in self.vision_models):
                return available_model
                
        return None
    
    def analyze_image(self, image_path: Path, analysis_type: str = "color_palette") -> Optional[Dict]:
        """Analyze image using vision model"""
        vision_model = self.find_available_vision_model()
        if not vision_model:
            logger.error("No vision model available for image analysis")
            return None
        
        if not image_path.exists():
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Preload the vision model
        self.ollama.preload_model(vision_model)
        
        if analysis_type == "color_palette":
            return self._extract_color_palette(image_path, vision_model)
        else:
            logger.error(f"Unknown analysis type: {analysis_type}")
            return None
    
    def _extract_color_palette(self, image_path: Path, model: str) -> Optional[Dict]:
        """Extract color palette from image using vision model"""
        prompt = """Analyze this wallpaper image and extract a Material You style color palette. 
        Focus on identifying:
        1. Primary color (most dominant/vibrant)
        2. Secondary color (complementary or supporting)
        3. Background colors (neutral tones)
        4. Accent colors (for highlights/emphasis)
        
        Return ONLY a JSON object in this exact format:
        {
            "primary": "#hexcolor",
            "secondary": "#hexcolor", 
            "background": "#hexcolor",
            "surface": "#hexcolor",
            "accent": "#hexcolor",
            "on_primary": "#hexcolor",
            "on_secondary": "#hexcolor",
            "on_background": "#hexcolor",
            "on_surface": "#hexcolor"
        }
        
        Ensure colors work well together and follow Material You principles.
        Use actual hex color codes, not color names."""
        
        try:
            # Note: This is a simplified approach. In reality, we'd need to 
            # encode the image and send it with the prompt to the vision model
            # For now, we'll simulate the process and create a fallback
            
            # TODO: Implement actual image encoding for Ollama vision models
            # This requires base64 encoding the image and sending it properly
            
            logger.warning("Vision model integration pending - using fallback color extraction")
            return self._fallback_color_extraction(image_path)
            
        except Exception as e:
            logger.error(f"Error extracting color palette: {e}")
            return None
    
    def _fallback_color_extraction(self, image_path: Path) -> Dict:
        """Fallback color extraction using PIL when AI models aren't available"""
        try:
            from PIL import Image
            import colorsys
            from collections import Counter
            
            # Open and resize image for faster processing
            with Image.open(image_path) as img:
                img = img.convert('RGB')
                img = img.resize((150, 150))  # Reduce size for speed
                
                # Get dominant colors
                colors = img.getcolors(maxcolors=256*256*256)
                colors = sorted(colors, key=lambda x: x[0], reverse=True)
                
                # Extract top colors and convert to hex
                hex_colors = []
                for count, rgb in colors[:10]:
                    hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                    hex_colors.append(hex_color)
                
                # Generate Material You style palette
                primary = hex_colors[0] if hex_colors else "#6750A4"
                
                # Simple algorithm to generate complementary colors
                # In production, this would be much more sophisticated
                return {
                    "primary": primary,
                    "secondary": self._generate_secondary(primary),
                    "background": "#FFFBFE",
                    "surface": "#F7F2FA", 
                    "accent": self._generate_accent(primary),
                    "on_primary": "#FFFFFF",
                    "on_secondary": "#FFFFFF",
                    "on_background": "#1C1B1F",
                    "on_surface": "#1C1B1F"
                }
                
        except ImportError:
            logger.error("PIL not available for fallback color extraction")
            return self._default_palette()
        except Exception as e:
            logger.error(f"Fallback color extraction failed: {e}")
            return self._default_palette()
    
    def _generate_secondary(self, primary_hex: str) -> str:
        """Generate secondary color from primary"""
        # Simple complementary color generation
        try:
            primary_rgb = tuple(int(primary_hex[i:i+2], 16) for i in (1, 3, 5))
            h, s, v = colorsys.rgb_to_hsv(*[x/255.0 for x in primary_rgb])
            
            # Shift hue by 30 degrees and adjust saturation
            h = (h + 0.083) % 1.0  # 30/360 = 0.083
            s = max(0.3, s - 0.2)
            
            rgb = colorsys.hsv_to_rgb(h, s, v)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        except:
            return "#E8DEF8"
    
    def _generate_accent(self, primary_hex: str) -> str:
        """Generate accent color from primary"""
        try:
            primary_rgb = tuple(int(primary_hex[i:i+2], 16) for i in (1, 3, 5))
            h, s, v = colorsys.rgb_to_hsv(*[x/255.0 for x in primary_rgb])
            
            # Increase saturation and value for accent
            s = min(1.0, s + 0.2)
            v = min(1.0, v + 0.1)
            
            rgb = colorsys.hsv_to_rgb(h, s, v)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        except:
            return "#7C4DFF"
    
    def _default_palette(self) -> Dict:
        """Default Material You palette as fallback"""
        return {
            "primary": "#6750A4",
            "secondary": "#625B71", 
            "background": "#FFFBFE",
            "surface": "#F7F2FA",
            "accent": "#7C4DFF",
            "on_primary": "#FFFFFF",
            "on_secondary": "#FFFFFF", 
            "on_background": "#1C1B1F",
            "on_surface": "#1C1B1F"
        }

class ConfigGenerator:
    """Generates configuration snippets using local coding models"""
    
    def __init__(self, ollama_manager: OllamaManager):
        self.ollama = ollama_manager
        self.coding_models = ['wizardcoder:15b', 'codegemma', 'codellama', 'deepseek-coder']
    
    def find_available_coding_model(self) -> Optional[str]:
        """Find the best available coding model"""
        available = self.ollama.list_models()
        
        for model in self.coding_models:
            if model in available:
                return model
                
        # Check for partial matches
        for available_model in available:
            if any(cm.split(':')[0] in available_model for cm in self.coding_models):
                return available_model
                
        return None
    
    def generate_config_patch(self, app_name: str, config_format: str, 
                            color_palette: Dict, current_config: str = None) -> Optional[str]:
        """Generate configuration patch for specific app"""
        coding_model = self.find_available_coding_model()
        if not coding_model:
            logger.error("No coding model available for config generation")
            return None
        
        # Preload the coding model
        self.ollama.preload_model(coding_model)
        
        system_prompt = f"""You are an expert in {app_name} configuration and theming.
        Your task is to generate precise configuration updates that apply the given color palette
        while preserving all existing settings unrelated to theming."""
        
        prompt = f"""Generate a {config_format} configuration patch for {app_name} that applies this color palette:
        {json.dumps(color_palette, indent=2)}
        
        Requirements:
        1. Only modify color-related settings
        2. Preserve all non-theming configurations
        3. Use proper {config_format} syntax
        4. Include only the sections that need changes
        5. Ensure the colors work well together
        
        {f"Current config to update: {current_config}" if current_config else ""}
        
        Return only the configuration code, no explanations."""
        
        response = self.ollama.generate_response(
            coding_model, prompt, system_prompt, timeout=45
        )
        
        return response 