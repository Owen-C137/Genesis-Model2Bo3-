"""
Texture Copier Utility
Finds and copies textures from Fallout 4 texture folders to organized output structure
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️ Pillow not installed - PNG conversion will be disabled")


class TextureCopier:
    """
    Handles finding and copying textures from Fallout 4 to organized output folders
    """
    
    def __init__(self, texture_base_path: str):
        """
        Initialize texture copier
        
        Args:
            texture_base_path: Base path to Fallout 4 textures folder
        """
        self.texture_base_path = texture_base_path
        self.texture_cache = {}  # Cache of texture filename -> full path
        
    def build_texture_cache(self):
        """
        Build a cache of all texture files in the Fallout 4 textures folder
        This makes subsequent lookups much faster
        """
        if not os.path.exists(self.texture_base_path):
            print(f"⚠️ Texture path does not exist: {self.texture_base_path}")
            return
        
        print(f"📁 Scanning texture folder: {self.texture_base_path}")
        print("   This may take a moment...")
        
        texture_count = 0
        for root, dirs, files in os.walk(self.texture_base_path):
            for file in files:
                if file.lower().endswith(('.dds', '.png', '.tga', '.jpg', '.jpeg')):
                    # Store lowercase filename -> full path mapping
                    full_path = os.path.join(root, file)
                    self.texture_cache[file.lower()] = full_path
                    texture_count += 1
        
        print(f"✓ Found {texture_count} texture files")
    
    def find_texture(self, filename: str) -> Optional[str]:
        """
        Find a texture file in the cache
        
        Args:
            filename: Texture filename to find (e.g., "V111Door01_d.dds")
            
        Returns:
            Full path to texture file, or None if not found
        """
        return self.texture_cache.get(filename.lower())
    
    def invert_image(self, image_path: str) -> bool:
        """
        Invert an image (like Photoshop Ctrl+I)
        Used for normal maps to convert between Y+ and Y- conventions
        
        Args:
            image_path: Path to the PNG image to invert
            
        Returns:
            True if successful, False otherwise
        """
        if not PILLOW_AVAILABLE:
            return False
        
        try:
            # Load the image
            img = Image.open(image_path)
            
            # Convert to RGB/RGBA if needed
            if img.mode not in ('RGB', 'RGBA'):
                if img.mode == 'RGBA' or 'transparency' in img.info:
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            
            # Invert the image (like Photoshop Ctrl+I)
            from PIL import ImageOps
            inverted = ImageOps.invert(img.convert('RGB'))
            
            # If original had alpha, restore it
            if img.mode == 'RGBA':
                alpha = img.split()[-1]
                inverted.putalpha(alpha)
            
            # Save the inverted image
            inverted.save(image_path, 'PNG')
            return True
            
        except Exception as e:
            print(f"  ⚠️ Could not invert {os.path.basename(image_path)}: {e}")
            return False
    
    def convert_to_png(self, source_path: str, delete_original: bool = True) -> Tuple[bool, str]:
        """
        Convert a texture file to PNG format
        
        Args:
            source_path: Path to the source texture file (DDS, TGA, etc.)
            delete_original: Whether to delete the original file after conversion
            
        Returns:
            Tuple of (success, new_path)
        """
        if not PILLOW_AVAILABLE:
            return (False, source_path)
        
        # Skip if already PNG
        if source_path.lower().endswith('.png'):
            return (True, source_path)
        
        try:
            # Load the image
            img = Image.open(source_path)
            
            # Generate PNG path
            png_path = os.path.splitext(source_path)[0] + '.png'
            
            # Convert and save as PNG
            # Convert RGBA if image has alpha channel, otherwise RGB
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            
            img.save(png_path, 'PNG')
            
            # Delete original if requested
            if delete_original and os.path.exists(png_path):
                try:
                    os.remove(source_path)
                except:
                    pass  # Don't fail if we can't delete original
            
            return (True, png_path)
            
        except Exception as e:
            print(f"  ⚠️ Could not convert {os.path.basename(source_path)} to PNG: {e}")
            return (False, source_path)
    
    def copy_textures_for_model(self, materials_json_path: str, output_base_dir: str, 
                               model_name: str, convert_to_png: bool = False, 
                               invert_normals: bool = False) -> Tuple[int, int]:
        """
        Copy all textures for a model based on its materials JSON
        
        Args:
            materials_json_path: Path to the model's materials JSON file
            output_base_dir: Base output directory (should already include folder structure)
            model_name: Name of the model (for folder structure)
            convert_to_png: Whether to convert textures to PNG
            invert_normals: Whether to invert normal maps (after PNG conversion)
            
        Returns:
            Tuple of (successful_copies, failed_copies)
        """
        # Build cache if not already built
        if not self.texture_cache:
            self.build_texture_cache()
        
        if not self.texture_cache:
            print("⚠️ No textures found in cache, skipping texture copy")
            return (0, 0)
        
        # Load materials JSON
        try:
            with open(materials_json_path, 'r', encoding='utf-8') as f:
                materials_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not read materials JSON: {e}")
            return (0, 0)
        
        # Create textures directory structure: output_base_dir/textures/
        textures_base_dir = os.path.join(output_base_dir, 'textures')
        os.makedirs(textures_base_dir, exist_ok=True)
        
        successful = 0
        failed = 0
        
        # Process each material
        materials = materials_data.get('materials', [])
        if not materials:
            print("⚠️ No materials found in JSON")
            return (0, 0)
        
        print(f"\n📦 Copying textures for {model_name}...")
        
        for material in materials:
            material_name = material.get('name', {}).get('final', f"material_{material.get('index', 0)}")
            textures = material.get('textures', [])
            
            if not textures:
                continue
            
            # Create material subfolder inside textures directory
            material_folder = os.path.join(textures_base_dir, material_name)
            os.makedirs(material_folder, exist_ok=True)
            
            # Copy each texture
            for texture in textures:
                filename = texture.get('filename', '')
                texture_type = texture.get('type', '')  # 'diffuse', 'normal', etc.
                bo3_path = texture.get('bo3_path', '')  # BO3 format path
                if not filename:
                    continue
                
                # Find texture in cache
                source_path = self.find_texture(filename)
                
                if source_path and os.path.exists(source_path):
                    # Use BO3 naming convention: extract filename from bo3_path
                    # bo3_path format: "color:_images\\i_fo4_v111struct01_d_c.png"
                    if bo3_path:
                        # Extract just the filename part after the last backslash
                        bo3_filename = bo3_path.split('\\\\')[-1]  # Gets "i_fo4_v111struct01_d_c.png"
                        dest_filename = bo3_filename
                    else:
                        dest_filename = filename
                    
                    dest_path = os.path.join(material_folder, dest_filename)
                    try:
                        # Copy the file
                        shutil.copy2(source_path, dest_path)
                        
                        # Convert to PNG if requested
                        converted = False
                        inverted = False
                        final_path = dest_path
                        
                        if convert_to_png:
                            success, new_path = self.convert_to_png(dest_path, delete_original=True)
                            if success:
                                converted = True
                                final_path = new_path
                                
                                # Invert normal maps if requested
                                # Check if this is a normal map by texture type or filename pattern
                                is_normal = (texture_type == 'normal' or 
                                           '_n.' in filename.lower() or 
                                           '_normal.' in filename.lower() or
                                           '_nrm.' in filename.lower())
                                
                                if invert_normals and is_normal:
                                    if self.invert_image(final_path):
                                        inverted = True
                        
                        # Build status message
                        status_parts = []
                        if converted:
                            status_parts.append("converted")
                        if inverted:
                            status_parts.append("inverted")
                        
                        status = f" ({', '.join(status_parts)})" if status_parts else ""
                        print(f"  ✓ {material_name}/{os.path.basename(final_path)}{status}")
                        
                        successful += 1
                    except Exception as e:
                        print(f"  ✗ Failed to copy {filename}: {e}")
                        failed += 1
                else:
                    print(f"  ✗ Texture not found: {filename}")
                    failed += 1
        
        if successful > 0:
            print(f"\n✓ Copied {successful} textures to textures/{material_name}/")
            if convert_to_png:
                print(f"  (Converted to PNG format)")
            if invert_normals:
                print(f"  (Normal maps inverted)")
        if failed > 0:
            print(f"⚠️ {failed} textures could not be copied")
        
        return (successful, failed)
    
    def copy_textures_simple(self, texture_filenames: List[str], material_name: str, 
                           output_dir: str) -> Tuple[int, int]:
        """
        Simple texture copy for a single material
        
        Args:
            texture_filenames: List of texture filenames to copy
            material_name: Name of the material (for subfolder)
            output_dir: Base output directory
            
        Returns:
            Tuple of (successful_copies, failed_copies)
        """
        # Build cache if not already built
        if not self.texture_cache:
            self.build_texture_cache()
        
        if not self.texture_cache:
            return (0, 0)
        
        # Create material folder
        material_folder = os.path.join(output_dir, material_name)
        os.makedirs(material_folder, exist_ok=True)
        
        successful = 0
        failed = 0
        
        for filename in texture_filenames:
            source_path = self.find_texture(filename)
            
            if source_path and os.path.exists(source_path):
                dest_path = os.path.join(material_folder, filename)
                try:
                    shutil.copy2(source_path, dest_path)
                    successful += 1
                except Exception as e:
                    print(f"⚠️ Failed to copy {filename}: {e}")
                    failed += 1
            else:
                failed += 1
        
        return (successful, failed)
