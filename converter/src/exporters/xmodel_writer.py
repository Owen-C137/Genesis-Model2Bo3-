"""
XMODEL_EXPORT Writer for Black Ops 3
Generates .XMODEL_EXPORT text files from parsed data
"""

import os
import json
import datetime
from typing import List, Dict, Tuple
from ..parsers.nif_parser import NIFData
from ..utils.skeleton_analyzer import SkeletonAnalyzer


class XModelWriter:
    """Write Black Ops 3 XMODEL_EXPORT format"""
    
    def __init__(self, version: int = 6):
        self.version = version
        self.auto_scale = 1.0
        # Bone rotations (for skeleton) - Default for Fallout 4 furniture/props
        self.auto_rotation_x = 0
        self.auto_rotation_y = 0
        self.auto_rotation_z = 90
        # Mesh rotations (for vertices/normals) - separate from bones!
        self.mesh_rotation_x = 180
        self.mesh_rotation_y = 180
        self.mesh_rotation_z = -90
        # Naming prefixes
        self.material_prefix = ''
        self.filename_prefix = ''
        
    def write(self, data: NIFData, output_path: str) -> bool:
        """
        Write NIF data to XMODEL_EXPORT format
        
        Args:
            data: Parsed NIF data
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            # Check if rotation/scale were manually set (not default values)
            # Default bone rotation for Fallout 4: X=0°, Y=0°, Z=90°
            manually_set = (self.auto_rotation_x != 0 or 
                           self.auto_rotation_y != 0 or 
                           self.auto_rotation_z != 90 or
                           self.auto_scale != 1.0 or
                           self.mesh_rotation_x != 180 or
                           self.mesh_rotation_y != 180 or
                           self.mesh_rotation_z != -90)
            
            if not manually_set:
                # Analyze skeleton for automatic transforms
                print("\n=== Analyzing Skeleton ===")
                analyzer = SkeletonAnalyzer(data.bones, data.vertices)
                analysis = analyzer.analyze()
                
                # Store auto-detected values
                self.auto_scale = analysis['scale']
                self.auto_rotation_x = analysis['rotation_x']
                self.auto_rotation_y = analysis['rotation_y']
                self.auto_rotation_z = analysis['rotation_z']
                self.mesh_rotation_x = analysis['mesh_rotation_x']
                self.mesh_rotation_y = analysis['mesh_rotation_y']
                self.mesh_rotation_z = analysis['mesh_rotation_z']
                
                print(f"  Auto-transform applied:")
                print(f"    Scale: {self.auto_scale:.3f}x (BO3 standard)")
                print(f"    Bone rotation: X={self.auto_rotation_x}°, Y={self.auto_rotation_y}°, Z={self.auto_rotation_z}°")
                print(f"    Mesh rotation: X={self.mesh_rotation_x}°, Y={self.mesh_rotation_y}°, Z={self.mesh_rotation_z}°")
                print()
            else:
                # Use manually set values
                print("\n=== Using Manual Transform ===")
                print(f"    Scale: {self.auto_scale:.3f}x")
                print(f"    Bone rotation: X={self.auto_rotation_x}°, Y={self.auto_rotation_y}°, Z={self.auto_rotation_z}°")
                print(f"    Mesh rotation: X={self.mesh_rotation_x}°, Y={self.mesh_rotation_y}°, Z={self.mesh_rotation_z}°")
                print()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                self._write_header(f)
                self._write_bones(f, data)
                self._write_vertices(f, data)
                self._write_faces(f, data)
                self._write_objects(f, data)
                self._write_materials(f, data)
            
            print(f"✓ Exported to: {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to write XMODEL_EXPORT: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def write_materials_json(self, data: NIFData, output_path: str) -> bool:
        """
        Write material and texture information to JSON file
        
        Args:
            data: Parsed NIF data
            output_path: Path to output JSON file (usually model_name_materials.json)
            
        Returns:
            True if successful
        """
        try:
            # Build material info dictionary
            materials_info = {
                "export_info": {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_file": data.name if hasattr(data, 'name') else "Unknown",
                    "model_name": os.path.splitext(os.path.basename(output_path))[0].replace("_materials", "")
                },
                "model_stats": {
                    "num_materials": len(data.materials) if data.materials else 0,
                    "num_bones": len(data.bones) if data.bones else 0,
                    "num_vertices": len(data.vertices) if data.vertices else 0,
                    "num_triangles": len(data.faces) if data.faces else 0
                },
                "materials": []
            }
            
            # Process each material
            if data.materials:
                for i, material in enumerate(data.materials):
                    # Get material name
                    mat_name_orig = material.get('name', f'material_{i}')
                    
                    # Handle layered materials (e.g., "V111Hall01:0", "V111Hall01:1")
                    # Keep the layer index to ensure unique material names
                    if ':' in mat_name_orig:
                        parts = mat_name_orig.split(':')
                        base_name = parts[0].lower()
                        layer_index = parts[1]  # Keep the layer number
                        mat_name_clean = f"{base_name}_layer{layer_index}"
                    else:
                        mat_name_clean = mat_name_orig.lower()
                    
                    # Remove any remaining special characters except underscore
                    mat_name_clean = ''.join(c if c.isalnum() or c == '_' else '_' for c in mat_name_clean)
                    
                    mat_name_final = self.material_prefix + mat_name_clean if self.material_prefix else mat_name_clean
                    
                    # Get texture paths
                    diffuse_orig = material.get('diffuse_texture', '')
                    normal_orig = material.get('normal_texture', '')
                    
                    # Extract texture info
                    textures = []
                    if diffuse_orig:
                        tex_name = os.path.splitext(os.path.basename(diffuse_orig))[0].split(':')[0].lower()
                        tex_name_final = self.material_prefix + tex_name if self.material_prefix else tex_name
                        textures.append({
                            "type": "diffuse",
                            "original_path": diffuse_orig,
                            "filename": os.path.basename(diffuse_orig),
                            "name_clean": tex_name,
                            "bo3_path": f"color:_images\\\\i_{tex_name_final}_c.png",
                            "description": "Base color/albedo texture"
                        })
                    
                    if normal_orig:
                        tex_name = os.path.splitext(os.path.basename(normal_orig))[0].split(':')[0].lower()
                        tex_name_final = self.material_prefix + tex_name if self.material_prefix else tex_name
                        textures.append({
                            "type": "normal",
                            "original_path": normal_orig,
                            "filename": os.path.basename(normal_orig),
                            "name_clean": tex_name,
                            "bo3_path": f"normal:_images\\\\i_{tex_name_final}_n.png",
                            "description": "Normal map texture"
                        })
                    
                    # Get material properties
                    mat_info = {
                        "index": i,
                        "name": {
                            "original": mat_name_orig,
                            "cleaned": mat_name_clean,
                            "final": mat_name_final
                        },
                        "shader": material.get('shader', 'Phong'),
                        "textures": textures,
                        "properties": {
                            "specular_color": material.get('specular_color', [0.5, 0.5, 0.5, 1.0]),
                            "has_transparency": material.get('alpha', 1.0) < 1.0
                        }
                    }
                    
                    materials_info["materials"].append(mat_info)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(materials_info, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Material info exported to: {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            print(f"  ⚠️ Failed to write materials JSON: {e}")
            return False
    
    def _write_header(self, f):
        """Write file header"""
        f.write("// Generated by Genesis (Model2Bo3)\n")
        f.write("// Original format: Fallout 4 NIF\n")
        f.write("MODEL\n")
        f.write(f"VERSION {self.version}\n\n")
    
    def _apply_coordinate_transform(self, position: List[float], rotation: List[List[float]]) -> Tuple[List[float], List[List[float]]]:
        """
        Apply coordinate system conversion from Fallout 4 to Black Ops 3.
        Uses auto-detected rotation and scale from skeleton analysis.
        
        Args:
            position: [x, y, z] position vector
            rotation: 3x3 rotation matrix
            
        Returns:
            Tuple of (transformed_position, transformed_rotation)
        """
        import numpy as np
        
        # Build rotation transform from auto-detected angles
        rot_x = SkeletonAnalyzer.create_rotation_matrix(self.auto_rotation_x, 'x')
        rot_y = SkeletonAnalyzer.create_rotation_matrix(self.auto_rotation_y, 'y')
        rot_z = SkeletonAnalyzer.create_rotation_matrix(self.auto_rotation_z, 'z')
        
        # Combined transform: X first, then Y, then Z rotation
        coord_transform = rot_z @ rot_y @ rot_x
        
        # Transform position: new_pos = scale * (transform * pos)
        pos_vec = np.array(position)
        new_position = (self.auto_scale * (coord_transform @ pos_vec)).tolist()
        
        # Transform rotation: new_rot = transform * rot * transform^T
        rot_mat = np.array(rotation)
        new_rotation = (coord_transform @ rot_mat @ coord_transform.T).tolist()
        
        return new_position, new_rotation
    
    def _compute_global_transforms(self, bones: List[Dict]) -> List[Dict]:
        """
        Convert local bone transforms to global (world-space) transforms.
        BO3 expects OFFSET to be global position, not parent-relative.
        
        If bones already have 'global_translation' and 'global_rotation' from the parser,
        use those directly instead of recalculating.
        
        Args:
            bones: List of bones with local transforms
            
        Returns:
            List of bones with global transforms added
        """
        import numpy as np
        
        # ALWAYS compute global transforms from the bone['translation'] and bone['rotation'] values
        # The parser provides local transforms for bones with parents, and global for root bones
        # We need to compute the full global hierarchy for XMODEL OFFSET values
        print("  Computing global transforms for XMODEL (local→global with hierarchy)")
        
        # Create index lookup
        bone_by_index = {bone['index']: bone for bone in bones}
        
        # Add global transforms to each bone
        for bone in bones:
            parent_idx = bone['parent']
            
            if parent_idx == -1:
                # Root bone - global == local
                bone['global_translation'] = bone['translation']
                bone['global_rotation'] = bone['rotation']
            else:
                # Child bone - compute global from parent's global + local
                parent = bone_by_index[parent_idx]
                
                # Ensure parent has global transform computed
                if 'global_translation' not in parent:
                    raise RuntimeError(f"Parent bone {parent_idx} not processed before child {bone['index']}")
                
                # Convert rotation matrix to numpy
                parent_rot = np.array(parent['global_rotation'])
                local_rot = np.array(bone['rotation'])
                local_trans = np.array(bone['translation'])
                
                # Global rotation = parent_global_rot * local_rot
                global_rot = parent_rot @ local_rot
                
                # Global translation = parent_global_pos + parent_global_rot * local_pos
                global_trans = np.array(parent['global_translation']) + parent_rot @ local_trans
                
                bone['global_rotation'] = global_rot.tolist()
                bone['global_translation'] = global_trans.tolist()
        
        # Apply coordinate system conversion to all bones
        for bone in bones:
            transformed_pos, transformed_rot = self._apply_coordinate_transform(
                bone['global_translation'], 
                bone['global_rotation']
            )
            bone['global_translation'] = transformed_pos
            bone['global_rotation'] = transformed_rot
        
        return bones
    
    def _write_bones(self, f, data: NIFData):
        """Write bone hierarchy"""
        if not data.bones:
            # Create a default root bone if none exist
            f.write("NUMBONES 1\n")
            f.write(f'BONE 0 -1 "{data.name}"\n\n')
            
            f.write("BONE 0\n")
            f.write("OFFSET 0.000000, 0.000000, 0.000000\n")
            f.write("SCALE 1.000000, 1.000000, 1.000000\n")
            f.write("X 1.000000, 0.000000, 0.000000\n")
            f.write("Y 0.000000, 1.000000, 0.000000\n")
            f.write("Z 0.000000, 0.000000, 1.000000\n\n")
        else:
            # Compute global transforms from local transforms
            bones_with_global = self._compute_global_transforms(data.bones)
            
            # Write bone count and hierarchy
            f.write(f"NUMBONES {len(bones_with_global)}\n")
            for bone in bones_with_global:
                f.write(f'BONE {bone["index"]} {bone["parent"]} "{bone["name"]}"\n')
            f.write("\n")
            
            # Write bone transforms (using GLOBAL positions)
            for bone in bones_with_global:
                f.write(f'BONE {bone["index"]}\n')
                
                # Translation - USE GLOBAL POSITION
                trans = bone['global_translation']
                f.write(f"OFFSET {trans[0]:.6f}, {trans[1]:.6f}, {trans[2]:.6f}\n")
                
                # Rotation matrix as X, Y, Z vectors - USE GLOBAL ROTATION
                # NOTE: Don't write SCALE for skeletal meshes (only for static props)
                rot = bone['global_rotation']
                f.write(f"X {rot[0][0]:.6f}, {rot[0][1]:.6f}, {rot[0][2]:.6f}\n")
                f.write(f"Y {rot[1][0]:.6f}, {rot[1][1]:.6f}, {rot[1][2]:.6f}\n")
                f.write(f"Z {rot[2][0]:.6f}, {rot[2][1]:.6f}, {rot[2][2]:.6f}\n")
                f.write("\n")
    
    def _write_vertices(self, f, data: NIFData):
        """Write vertex data"""
        import numpy as np
        
        # Build coordinate transform using MESH rotation (not bone rotation!)
        rot_x = SkeletonAnalyzer.create_rotation_matrix(self.mesh_rotation_x, 'x')
        rot_y = SkeletonAnalyzer.create_rotation_matrix(self.mesh_rotation_y, 'y')
        rot_z = SkeletonAnalyzer.create_rotation_matrix(self.mesh_rotation_z, 'z')
        coord_transform = rot_z @ rot_y @ rot_x
        
        f.write(f"NUMVERTS {len(data.vertices)}\n")
        
        for i, vertex in enumerate(data.vertices):
            f.write(f"VERT {i}\n")
            
            # Position - Apply coordinate transform AND scale
            vertex_vec = np.array(vertex)
            transformed_vertex = (self.auto_scale * (coord_transform @ vertex_vec)).tolist()
            f.write(f"OFFSET {transformed_vertex[0]:.6f}, {transformed_vertex[1]:.6f}, {transformed_vertex[2]:.6f}\n")
            
            # Bone weights
            if i < len(data.skin_weights) and data.skin_weights[i]:
                weights = data.skin_weights[i]
                f.write(f"BONES {len(weights)}\n")
                for bone_idx, weight in weights:
                    f.write(f"BONE {bone_idx} {weight:.6f}\n")
            else:
                # Default to root bone
                f.write("BONES 1\n")
                f.write("BONE 0 1.000000\n")
            
            f.write("\n")
    
    def _write_faces(self, f, data: NIFData):
        """Write face/triangle data"""
        f.write(f"NUMFACES {len(data.faces)}\n")
        
        for i, face in enumerate(data.faces):
            v1, v2, v3 = face
            
            # REVERSE WINDING ORDER: FO4 uses CCW, BO3 uses CW (or vice versa)
            # This fixes the inverted/inside-out faces issue
            v1, v2, v3 = v3, v2, v1
            
            # Get material index for this face (default to 0 if not available)
            material_index = 0
            if data.face_materials and i < len(data.face_materials):
                material_index = data.face_materials[i]
            
            # Use same index for object as material (one object per material)
            object_index = material_index
            
            # Write triangle header with correct material and object indices
            # Format: TRI <material_index> <object_index> <smoothing_group> <unknown>
            f.write(f"TRI {material_index} {object_index} 0 0\n")
            
            # Write each vertex of the triangle with full data
            for vert_idx in [v1, v2, v3]:
                f.write(f"VERT {vert_idx}\n")
                
                # Normal - validate and fix zero normals, then transform
                if vert_idx < len(data.normals):
                    normal = data.normals[vert_idx]
                    # Check if normal is zero/invalid
                    length = (normal[0]**2 + normal[1]**2 + normal[2]**2) ** 0.5
                    if length < 0.0001:  # Near-zero normal
                        # Use default up normal (already in BO3 coords)
                        f.write("NORMAL 0.000000 0.000000 1.000000\n")
                    else:
                        # Normalize the normal (ensure unit length)
                        import numpy as np
                        normalized = [normal[0] / length, normal[1] / length, normal[2] / length]
                        
                        # Apply coordinate transform to normal (use MESH rotation, same as vertices)
                        rot_x = SkeletonAnalyzer.create_rotation_matrix(self.mesh_rotation_x, 'x')
                        rot_y = SkeletonAnalyzer.create_rotation_matrix(self.mesh_rotation_y, 'y')
                        rot_z = SkeletonAnalyzer.create_rotation_matrix(self.mesh_rotation_z, 'z')
                        coord_transform = rot_z @ rot_y @ rot_x
                        
                        normal_vec = np.array(normalized)
                        transformed_normal = (coord_transform @ normal_vec).tolist()
                        
                        f.write(f"NORMAL {transformed_normal[0]:.6f} {transformed_normal[1]:.6f} {transformed_normal[2]:.6f}\n")
                else:
                    f.write("NORMAL 0.000000 0.000000 1.000000\n")
                
                # Color
                if vert_idx < len(data.colors):
                    color = data.colors[vert_idx]
                    f.write(f"COLOR {color[0]:.6f} {color[1]:.6f} {color[2]:.6f} {color[3]:.6f}\n")
                else:
                    f.write("COLOR 1.000000 1.000000 1.000000 1.000000\n")
                
                # UV coordinates
                if vert_idx < len(data.uvs):
                    uv = data.uvs[vert_idx]
                    f.write(f"UV 1 {uv[0]:.6f} {uv[1]:.6f}\n")
                else:
                    f.write("UV 1 0.000000 0.000000\n")
    
    def _write_objects(self, f, data: NIFData):
        """Write object definitions - one object per material for proper rendering"""
        # Create one object for each material (required for multi-material meshes)
        num_objects = max(len(data.materials), 1)
        f.write(f"\nNUMOBJECTS {num_objects}\n")
        
        if data.materials:
            for i, material in enumerate(data.materials):
                mat_name = material.get('name', f'material_{i}')
                # Use cleaned material name for object name
                if ':' in mat_name:
                    parts = mat_name.split(':')
                    mat_name = f"{parts[0]}_layer{parts[1]}"
                object_name = mat_name if mat_name else f"{data.name}_obj{i}"
                f.write(f'OBJECT {i} "{object_name}"\n')
        else:
            f.write(f'OBJECT 0 "{data.name}"\n')
        f.write("\n")
    
    def _write_materials(self, f, data: NIFData):
        """Write material definitions"""
        if not data.materials:
            data.materials = [{
                'name': 'default_material',
                'shader': 'Phong',
                'diffuse_texture': '',
                'normal_texture': '',
                'specular_color': (0.5, 0.5, 0.5, 1.0)
            }]
        
        f.write(f"NUMMATERIALS {len(data.materials)}\n")
        
        for i, material in enumerate(data.materials):
            mat_name = material.get('name', f'material_{i}')
            
            # Handle layered materials (e.g., "V111Hall01:0", "V111Hall01:1")
            # Keep the layer index to ensure unique material names
            if ':' in mat_name:
                parts = mat_name.split(':')
                base_name = parts[0].lower()
                layer_index = parts[1]  # Keep the layer number
                mat_name = f"{base_name}_layer{layer_index}"
            else:
                mat_name = mat_name.lower()
            
            # Remove any remaining special characters except underscore
            mat_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in mat_name)
            
            # Apply material prefix if set
            if self.material_prefix:
                mat_name = self.material_prefix + mat_name
            
            shader = material.get('shader', 'Phong')
            diffuse = material.get('diffuse_texture', '')
            
            # Convert texture path to BO3 format
            if diffuse:
                # Extract filename and convert to BO3 path format
                tex_name = os.path.splitext(os.path.basename(diffuse))[0]
                # Clean texture name as well
                tex_name = tex_name.split(':')[0].lower()
                # Apply prefix to texture as well
                if self.material_prefix:
                    tex_name = self.material_prefix + tex_name
                diffuse_path = f"color:_images\\\\i_{tex_name}_c.png"
            else:
                diffuse_path = f"color:_images\\\\i_{mat_name}_c.png"
            
            f.write(f'MATERIAL {i} "{mat_name}" "{shader}" "{diffuse_path}"\n')
            
            # Material properties
            f.write("COLOR 0.000000 0.000000 0.000000 1.000000\n")
            f.write("TRANSPARENCY 0.000000 0.000000 0.000000 1.000000\n")
            f.write("AMBIENTCOLOR 1.000000 1.000000 1.000000 1.000000\n")
            f.write("INCANDESCENCE 0.000000 0.000000 0.000000 1.000000\n")
            f.write("COEFFS 0.800000 0.000000\n")
            f.write("GLOW 0.000000 0\n")
            f.write("REFRACTIVE 6 1.000000\n")
            
            # Specular color
            spec = material.get('specular_color', (0.5, 0.5, 0.5, 1.0))
            f.write(f"SPECULARCOLOR {spec[0]:.6f} {spec[1]:.6f} {spec[2]:.6f} {spec[3]:.6f}\n")
            
            f.write("REFLECTIVECOLOR 0.000000 0.000000 0.000000 1.000000\n")
            f.write("REFLECTIVE 1 0.500000\n")
            f.write("BLINN -1.000000 -1.000000\n")
            f.write("PHONG 20.000000\n")


if __name__ == "__main__":
    # Test writing
    from ..parsers.nif_parser import NIFParser
    import sys
    
    if len(sys.argv) > 1:
        parser = NIFParser()
        nif_data = parser.parse(sys.argv[1])
        
        output_path = sys.argv[1].replace('.nif', '.XMODEL_EXPORT')
        writer = XModelWriter()
        writer.write(nif_data, output_path)
        print(f"\n✓ Conversion complete!")
