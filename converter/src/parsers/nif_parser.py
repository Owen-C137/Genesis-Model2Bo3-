"""
NIF Parser for Fallout 4 Models
Extracts geometry, skeleton, and material data from .nif files
"""

import os
import numpy as np
from typing import Dict, List, Tuple, Optional

# Try pynifly first (better FO4 support), fallback to PyFFI
try:
    import sys
    import os
    import importlib.util
    
    # Find pynifly files - check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
        pynifly_dir = os.path.join(base_path, 'pynifly')
    else:
        # Running as script
        pynifly_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pynifly')
    
    pynifly_file = os.path.join(pynifly_dir, 'pynifly.py')
    
    if not os.path.exists(pynifly_file):
        raise FileNotFoundError(f"pynifly.py not found at {pynifly_file}")
    
    # Add pynifly dir to path so it can find its dependencies
    if pynifly_dir not in sys.path:
        sys.path.insert(0, pynifly_dir)
    
    # Load pynifly module directly
    spec = importlib.util.spec_from_file_location("pynifly", pynifly_file)
    pynifly = importlib.util.module_from_spec(spec)
    sys.modules['pynifly'] = pynifly  # Register it so imports work
    spec.loader.exec_module(pynifly)
    
    USE_NIFLY = True
    print("✓ Using PyNifly for NIF parsing (Fallout 4 support)")
except Exception as e:
    USE_NIFLY = False
    from pyffi.formats.nif import NifFormat
    print(f"⚠ Using PyFFI for NIF parsing (limited FO4 support). Error: {e}")


class NIFData:
    """Container for parsed NIF data"""
    def __init__(self):
        self.bones: List[Dict] = []
        self.vertices: List[Tuple[float, float, float]] = []
        self.normals: List[Tuple[float, float, float]] = []
        self.uvs: List[Tuple[float, float]] = []
        self.colors: List[Tuple[float, float, float, float]] = []
        self.faces: List[Tuple[int, int, int]] = []
        self.face_materials: List[int] = []  # Material index for each face
        self.skin_weights: List[List[Tuple[int, float]]] = []  # [(bone_index, weight), ...]
        self.materials: List[Dict] = []
        self.name: str = ""


class NIFParser:
    """Parse Fallout 4 NIF files"""
    
    def __init__(self):
        self.data = None
        
    def parse(self, filepath: str) -> NIFData:
        """
        Parse a NIF file and extract all relevant data
        
        Args:
            filepath: Path to .nif file
            
        Returns:
            NIFData object containing parsed data
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"NIF file not found: {filepath}")
            
        self.data = NIFData()
        self.data.name = os.path.splitext(os.path.basename(filepath))[0]
        self.current_filepath = filepath  # Store for skeleton lookup
        
        if USE_NIFLY:
            return self._parse_with_nifly(filepath)
        else:
            return self._parse_with_pyffi(filepath)
    
    def _parse_with_nifly(self, filepath: str) -> NIFData:
        """Parse using pynifly library (better FO4 support)"""
        try:
            print(f"  Reading NIF with PyNifly...")
            
            # Load the DLL if not already loaded
            if not hasattr(pynifly.NifFile, 'nifly') or pynifly.NifFile.nifly is None:
                # Find the DLL path
                dll_path = None
                
                # Check 1: PyInstaller temp directory (sys._MEIPASS)
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable - check temp extraction folder
                    base_path = sys._MEIPASS
                    check_path = os.path.join(base_path, 'NiflyDLL.dll')
                    if os.path.exists(check_path):
                        dll_path = check_path
                    else:
                        raise FileNotFoundError(
                            f"NiflyDLL.dll not found in PyInstaller temp folder.\n"
                            f"Expected location: {check_path}\n"
                            f"This should have been bundled with the executable."
                        )
                else:
                    # Running from source - check standard pynifly locations
                    pynifly_dir = os.path.dirname(pynifly.__file__)
                    
                    # Try NiflyDLL/x64/ subfolder first
                    check_path = os.path.join(pynifly_dir, 'NiflyDLL', 'x64', 'NiflyDLL.dll')
                    if os.path.exists(check_path):
                        dll_path = check_path
                    else:
                        # Try direct in pynifly directory
                        check_path = os.path.join(pynifly_dir, 'NiflyDLL.dll')
                        if os.path.exists(check_path):
                            dll_path = check_path
                
                if not dll_path:
                    raise FileNotFoundError(f"NiflyDLL.dll not found in any expected location")
                    
                print(f"  Loading NiflyDLL from: {dll_path}")
                pynifly.NifFile.Load(dll_path)
            
            # Load NIF file
            nif = pynifly.NifFile(filepath)
            
            print(f"  NIF loaded successfully")
            print(f"  Shapes found: {len(nif.shapes)}")
            
            # Extract skeleton from NIF
            self._extract_nifly_skeleton(nif)
            
            # Extract geometry from each shape
            # nif.shapes is a list of NiShape objects
            for idx, shape in enumerate(nif.shapes):
                if shape:
                    shape_name = shape.name if hasattr(shape, 'name') and shape.name else f"shape_{idx}"
                    
                    # Skip LOD meshes (they're lower quality versions for distance rendering)
                    if 'lo-poly' in shape_name.lower() or 'lod' in shape_name.lower():
                        print(f"  Skipping LOD shape: {shape_name}")
                        continue
                    
                    print(f"  Processing shape: {shape_name}")
                    self._extract_nifly_shape(nif, shape, shape_name)
            
            # NOW align skeleton with mesh (after vertices are loaded)
            self._align_skeleton_to_mesh()
            
            print(f"✓ Parsed {filepath}")
            print(f"  Bones: {len(self.data.bones)}")
            print(f"  Vertices: {len(self.data.vertices)}")
            print(f"  Faces: {len(self.data.faces)}")
            
        except Exception as e:
            import traceback
            print(f"  Error details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to parse NIF with nifly: {str(e)}")
        
        return self.data
    
    def _align_skeleton_to_mesh(self):
        """
        Keep bones and vertices exactly as they are in the NIF.
        No transformation needed - the NIF already has the correct spatial relationship.
        """
        print(f"  Using original bone hierarchy with {len(self.data.bones)} bones")
        
        # Show root bones for debugging
        root_bones = [b['name'] for b in self.data.bones if b['parent'] == -1]
        if root_bones:
            print(f"  Root bones: {', '.join(root_bones)}")
    
    def _try_load_external_skeleton(self):
        """Try to load external skeleton.nif file for character models"""
        try:
            # Check if there's a skeleton.nif in the same directory or parent CharacterAssets
            if hasattr(self, 'current_filepath'):
                filepath = self.current_filepath
                dir_path = os.path.dirname(filepath)
                
                # Try skeleton.nif in same directory
                skeleton_path = os.path.join(dir_path, 'skeleton.nif')
                if os.path.exists(skeleton_path):
                    print(f"  Loading external skeleton from: {skeleton_path}")
                    if USE_NIFLY:
                        skeleton_nif = pynifly.NifFile(skeleton_path)
                        return skeleton_nif
                
                # Try CharacterAssets/skeleton.nif if we're in a subdirectory
                parent_dir = os.path.dirname(dir_path)
                skeleton_path = os.path.join(parent_dir, 'CharacterAssets', 'skeleton.nif')
                if os.path.exists(skeleton_path):
                    print(f"  Loading external skeleton from: {skeleton_path}")
                    if USE_NIFLY:
                        skeleton_nif = pynifly.NifFile(skeleton_path)
                        return skeleton_nif
                        
        except Exception as e:
            print(f"  Could not load external skeleton: {e}")
        
        return None
    
    def _extract_nifly_skeleton(self, nif):
        """Extract skeleton/bones from NIF file"""
        try:
            # Collect bones from all shapes AND their skin-to-bone transforms
            all_bone_names = set()
            shape_bone_transforms = {}  # Store bone transforms from shapes' skinning data
            
            for shape in nif.shapes:
                if hasattr(shape, 'bone_names'):
                    bone_names = shape.bone_names
                    if bone_names:
                        all_bone_names.update(bone_names)
                        
                        # CRITICAL: Get skin-to-bone transforms from the shape
                        # These transforms position the bones relative to the mesh vertices
                        for bone_name in bone_names:
                            try:
                                # Get the skin-to-bone transform
                                skin_to_bone = shape.get_shape_skin_to_bone(bone_name)
                                if skin_to_bone:
                                    shape_bone_transforms[bone_name] = skin_to_bone
                            except Exception as e:
                                pass
            
            print(f"  Found {len(shape_bone_transforms)} bone transforms from shape skinning data")
            
            # Try to load external skeleton for proper hierarchy
            skeleton_nif = self._try_load_external_skeleton()
            
            # If no bones found in shapes, use skeleton nodes
            if not all_bone_names and skeleton_nif:
                print(f"  No skeleton bones found in mesh shapes, using skeleton nodes...")
                nodes = skeleton_nif.nodes
                if nodes:
                    all_bone_names = set(nodes.keys())
            
            # If still no bones found, create default root
            if not all_bone_names:
                print(f"  No skeleton bones found, creating default root bone")
                self.data.bones.append({
                    'index': 0,
                    'parent': -1,
                    'name': self.data.name + '_root',
                    'translation': (0, 0, 0),
                    'rotation': ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    'scale': (1, 1, 1)
                })
                return
            
            print(f"  Found {len(all_bone_names)} bones")
            
            # Use BOTH skeleton.nif and main NIF nodes (some models have bones in mesh, not skeleton)
            skeleton_nodes = skeleton_nif.nodes if skeleton_nif else {}
            main_nodes = nif.nodes if nif else {}
            
            # Combine nodes: prefer skeleton.nif, fall back to main NIF
            nodes = {}
            nodes.update(main_nodes)  # Main NIF first
            nodes.update(skeleton_nodes)  # Skeleton overrides if present
            
            # Build bone hierarchy - need to include parent bones too
            bones_to_include = set(all_bone_names)
            
            # Add all parent bones recursively
            for bone_name in list(bones_to_include):
                if bone_name in nodes:
                    node = nodes[bone_name]
                    # Walk up the parent chain
                    current = node
                    while hasattr(current, 'parent') and current.parent:
                        parent_name = current.parent.name if hasattr(current.parent, 'name') else None
                        if parent_name and parent_name in nodes:
                            # Skip file root nodes and engine bones we don't want
                            if ('\\' not in parent_name and '/' not in parent_name and
                                parent_name not in ['skeleton.nif', 'COM', 'Root']):
                                bones_to_include.add(parent_name)
                            current = current.parent
                        else:
                            break
            
            print(f"  Including {len(bones_to_include)} bones (with parents)")
            
            # Build bone list - CRITICAL: For bones whose parent was COM,
            # we need to offset them by COM's global position (to cancel it out)
            bone_list = []
            bone_name_to_index = {}
            
            # Find COM's global position to subtract from its children
            com_offset = (0, 0, 0)
            if 'COM' in nodes:
                com_node = nodes['COM']
                if hasattr(com_node, 'global_transform') and hasattr(com_node.global_transform, 'translation'):
                    t = com_node.global_transform.translation
                    com_offset = (
                        t.x if hasattr(t, 'x') else t[0],
                        t.y if hasattr(t, 'y') else t[1],
                        t.z if hasattr(t, 'z') else t[2]
                    )
                    print(f"  Found COM at global position: {com_offset}")
                    # Store for vertex alignment later
                    self._com_global_position = com_offset
            
            # First, collect bones with both local AND global transforms
            for bone_name in bones_to_include:
                if bone_name in nodes:
                    node = nodes[bone_name]
                    bone_index = len(bone_list)
                    bone_name_to_index[bone_name] = bone_index
                    
                    # Get LOCAL transform from the skeleton node
                    local_translation = (0, 0, 0)
                    local_rotation = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
                    scale = (1, 1, 1)
                    
                    if hasattr(node, 'transform'):
                        lt = node.transform
                        if hasattr(lt, 'translation'):
                            t = lt.translation
                            local_translation = (
                                t.x if hasattr(t, 'x') else t[0],
                                t.y if hasattr(t, 'y') else t[1],
                                t.z if hasattr(t, 'z') else t[2]
                            )
                        if hasattr(lt, 'rotation'):
                            rot = lt.rotation
                            try:
                                local_rotation = (
                                    (rot[0][0], rot[0][1], rot[0][2]),
                                    (rot[1][0], rot[1][1], rot[1][2]),
                                    (rot[2][0], rot[2][1], rot[2][2])
                                )
                            except:
                                pass
                        if hasattr(lt, 'scale'):
                            scale = (lt.scale, lt.scale, lt.scale)
                    
                    # Also get GLOBAL transform (we'll use this for bones that lost COM parent)
                    global_translation = None
                    global_rotation = None
                    if hasattr(node, 'global_transform'):
                        gt = node.global_transform
                        if hasattr(gt, 'translation'):
                            t = gt.translation
                            global_translation = (
                                t.x if hasattr(t, 'x') else t[0],
                                t.y if hasattr(t, 'y') else t[1],
                                t.z if hasattr(t, 'z') else t[2]
                            )
                        if hasattr(gt, 'rotation'):
                            rot = gt.rotation
                            try:
                                global_rotation = (
                                    (rot[0][0], rot[0][1], rot[0][2]),
                                    (rot[1][0], rot[1][1], rot[1][2]),
                                    (rot[2][0], rot[2][1], rot[2][2])
                                )
                            except:
                                pass
                    
                    bone_list.append({
                        'index': bone_index,
                        'parent': -1,
                        'name': bone_name,
                        'local_translation': local_translation,
                        'local_rotation': local_rotation,
                        'global_translation': global_translation,
                        'global_rotation': global_rotation,
                        'translation': local_translation,  # Will update if parent was COM
                        'rotation': local_rotation,
                        'scale': scale,
                        'node': node
                    })
            
            # Second pass: set parent relationships (only for bones in our list)
            parent_count = {}
            for bone in bone_list:
                node = bone['node']
                parent_name = None
                if hasattr(node, 'parent') and node.parent:
                    parent_name = node.parent.name if hasattr(node.parent, 'name') else None
                
                if parent_name and parent_name in bone_name_to_index:
                    # Normal case: parent exists in our bone list
                    bone['parent'] = bone_name_to_index[parent_name]
                    parent_count[parent_name] = parent_count.get(parent_name, 0) + 1
                    # Keep local transform
                    print(f"  {bone['name']}: parent={parent_name} (index {bone['parent']}), local: {bone['local_translation']}")
                    
                elif parent_name and ('\\' in parent_name or '/' in parent_name or parent_name in ['COM', 'Root']):
                    # Parent is filtered out (file root, COM, etc) - subtract COM offset from global
                    bone['parent'] = -1
                    parent_count['<filtered_parent>'] = parent_count.get('<filtered_parent>', 0) + 1
                    
                    # CRITICAL FIX: Subtract COM offset from global position
                    if bone['global_translation']:
                        bone['translation'] = (
                            bone['global_translation'][0] - com_offset[0],
                            bone['global_translation'][1] - com_offset[1],
                            bone['global_translation'][2] - com_offset[2]
                        )
                        print(f"  {bone['name']}: parent filtered ({parent_name}), global {bone['global_translation']} - COM offset {com_offset} = {bone['translation']}")
                    else:
                        print(f"  WARNING: {bone['name']} parent filtered but no global transform")
                else:
                    # No valid parent found - make it a root
                    bone['parent'] = -1
                    print(f"  {bone['name']}: no parent found, making root")
                
                del bone['node']  # Remove temporary node reference
            
            print(f"  Parent bone distribution: {parent_count}")
            
            # No conversion needed - we're using local transforms directly!
            # This is the correct approach for XMODEL format
            if not bone_list:
                print(f"  No valid bones found, creating default root bone")
                self.data.bones.append({
                    'index': 0,
                    'parent': -1,
                    'name': self.data.name + '_root',
                    'translation': (0, 0, 0),
                    'rotation': ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                    'scale': (1, 1, 1)
                })
            else:
                # BO3 REQUIREMENT: Must have exactly ONE root bone (parent=-1)
                # Find all root bones and make extras children of the first root
                # DO THIS BEFORE SORTING!
                root_bones = [bone for bone in bone_list if bone['parent'] == -1]
                
                if len(root_bones) > 1:
                    print(f"  Found {len(root_bones)} root bones: {[b['name'] for b in root_bones]}")
                    first_root = root_bones[0]
                    first_root_idx = bone_name_to_index[first_root['name']]
                    
                    # Make all other roots children of the first root
                    for root_bone in root_bones[1:]:
                        root_bone['parent'] = first_root_idx
                        print(f"  Making {root_bone['name']} a child of {first_root['name']} (BO3 single-root requirement)")
                elif len(root_bones) == 1:
                    print(f"  Single root bone: {root_bones[0]['name']}")
                
                # Sort bones in hierarchy order (parents before children)
                # This is required by BO3 - parent index must be < child index
                sorted_bones = []
                bone_name_to_bone = {bone['name']: bone for bone in bone_list}
                processed = set()
                
                def add_bone_and_children(bone):
                    """Recursively add bone and all its children"""
                    if bone['name'] in processed:
                        return
                    processed.add(bone['name'])
                    
                    # Add this bone
                    bone['index'] = len(sorted_bones)
                    sorted_bones.append(bone)
                    
                    # Add all children
                    for child_bone in bone_list:
                        if child_bone['name'] not in processed:
                            # Check if this bone's parent is the current bone
                            if child_bone['parent'] >= 0:
                                parent_bone = bone_list[child_bone['parent']]
                                if parent_bone['name'] == bone['name']:
                                    add_bone_and_children(child_bone)
                
                # Start with root bones (parent = -1)
                for bone in bone_list:
                    if bone['parent'] == -1:
                        add_bone_and_children(bone)
                
                # Update parent indices to match new sorted order
                name_to_new_index = {bone['name']: bone['index'] for bone in sorted_bones}
                for bone in sorted_bones:
                    if bone['parent'] >= 0:
                        old_parent = bone_list[bone['parent']]
                        bone['parent'] = name_to_new_index[old_parent['name']]
                
                bone_list = sorted_bones
                
                # Use bones exactly as they are - no renaming, no adding tag_origin
                # This preserves compatibility with FO4 animations
                self.data.bones = bone_list
                print(f"  Extracted {len(bone_list)} bones (using original hierarchy)")
                
        except Exception as e:
            import traceback
            print(f"  Warning: Could not extract skeleton: {e}")
            print(f"  {traceback.format_exc()}")
            # Create default root bone as fallback
            self.data.bones.append({
                'index': 0,
                'parent': -1,
                'name': self.data.name + '_root',
                'translation': (0, 0, 0),
                'rotation': ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                'scale': (1, 1, 1)
            })
    
    def _extract_nifly_shape(self, nif, shape, shape_name: str):
        """Extract geometry from a pynifly shape"""
        base_index = len(self.data.vertices)
        
        # Try to get skin transform (aligns skeleton to mesh)
        skin_offset = (0, 0, 0)
        if hasattr(shape, 'skin_transform'):
            try:
                st = shape.skin_transform
                if hasattr(st, 'translation'):
                    t = st.translation
                    skin_offset = (
                        -(t.x if hasattr(t, 'x') else t[0]),
                        -(t.y if hasattr(t, 'y') else t[1]),
                        -(t.z if hasattr(t, 'z') else t[2])
                    )
                    print(f"    Found skin transform offset: {skin_offset}")
            except:
                pass
        
        # Also check shape transform
        shape_offset = (0, 0, 0)
        if hasattr(shape, 'global_transform'):
            gt = shape.global_transform
            if hasattr(gt, 'translation'):
                t = gt.translation
                shape_offset = (
                    t.x if hasattr(t, 'x') else t[0],
                    t.y if hasattr(t, 'y') else t[1],
                    t.z if hasattr(t, 'z') else t[2]
                )
                if shape_offset != (0, 0, 0):
                    print(f"    Shape has transform offset: {shape_offset}")
        
        # Store skin offset for bone adjustment
        if skin_offset != (0, 0, 0):
            self._skin_offset = skin_offset
        
        # Get vertices - local bone transforms match mesh coordinate space
        verts = shape.verts
        for vert in verts:
            self.data.vertices.append((vert[0], vert[1], vert[2]))
        
        # Get normals
        normals = shape.normals
        if normals and len(normals) == len(verts):
            for normal in normals:
                self.data.normals.append((normal[0], normal[1], normal[2]))
        else:
            self.data.normals.extend([(0, 0, 1)] * len(verts))
        
        # Get UVs
        uvs = shape.uvs
        if uvs and len(uvs) > 0:
            for uv in uvs:
                self.data.uvs.append((uv[0], uv[1]))
        else:
            self.data.uvs.extend([(0, 0)] * len(verts))
        
        # Get vertex colors
        colors = shape.colors
        if colors and len(colors) == len(verts):
            for color in colors:
                self.data.colors.append((color[0], color[1], color[2], color[3]))
        else:
            self.data.colors.extend([(1, 1, 1, 1)] * len(verts))
        
        # Get triangles
        tris = shape.tris
        for tri in tris:
            self.data.faces.append((
                base_index + tri[0],
                base_index + tri[1],
                base_index + tri[2]
            ))
        
        # Track material index for each triangle (for layered materials)
        # PyNifly provides partition_tris: a list of partition indices, one per triangle
        material_index = len(self.data.materials)  # This material's index
        
        # Check if this shape has partitions (layered materials)
        if hasattr(shape, 'partition_tris') and hasattr(shape, 'partitions'):
            partition_tris = shape.partition_tris
            partitions = shape.partitions
            
            if partition_tris and len(partition_tris) == len(tris):
                # This shape has layered materials - each partition gets its own material
                # We need to create a material for each partition used
                print(f"    Shape has {len(partitions)} partitions with {len(partition_tris)} tri assignments")
                
                # For now, assign the current material index to all faces
                # We'll need to create additional materials per partition in a follow-up fix
                for _ in tris:
                    self.data.face_materials.append(material_index)
            else:
                # No partition data or mismatch - assign same material to all faces
                for _ in tris:
                    self.data.face_materials.append(material_index)
        else:
            # No partitions - assign same material to all faces
            for _ in tris:
                self.data.face_materials.append(material_index)
        
        # Extract skin weights from PyNifly
        num_verts = len(verts)
        self._extract_nifly_skin_weights(shape, base_index, num_verts)
        
        # Extract material info
        material = {
            'name': shape_name,
            'shader': 'Phong',
            'diffuse_texture': '',
            'normal_texture': '',
            'specular_color': (0.5, 0.5, 0.5, 1.0)
        }
        
        # Try to get textures from shader - shape.shader.textures is a dict with string keys
        if hasattr(shape, 'shader') and hasattr(shape.shader, 'textures'):
            try:
                textures = shape.shader.textures
                # Common texture slots: 'Diffuse', 'Normal', 'Specular', 'Glow', etc.
                if 'Diffuse' in textures:
                    material['diffuse_texture'] = textures['Diffuse']
                if 'Normal' in textures:
                    material['normal_texture'] = textures['Normal']
            except Exception as e:
                print(f"⚠ Could not extract textures from {shape_name}: {e}")
        
        self.data.materials.append(material)
    
    def _extract_nifly_skin_weights(self, shape, base_index: int, num_verts: int):
        """Extract skin weights from PyNifly shape"""
        # Initialize empty weights for all vertices in this shape
        vertex_weights = [[] for _ in range(num_verts)]
        
        try:
            # Get bone weights from PyNifly: {bone_name: [(vertex_idx, weight), ...]}
            bone_weights = shape.bone_weights
            
            if bone_weights:
                print(f"    Found skin weights for {len(bone_weights)} bones")
                
                # Create a mapping of bone names to indices
                bone_name_to_index = {bone['name']: idx for idx, bone in enumerate(self.data.bones)}
                
                # Process weights for each bone
                for bone_name, weight_list in bone_weights.items():
                    if bone_name not in bone_name_to_index:
                        print(f"    Warning: Bone '{bone_name}' has weights but not in skeleton")
                        continue
                    
                    bone_idx = bone_name_to_index[bone_name]
                    
                    # Add weights to vertices
                    for vert_idx, weight in weight_list:
                        if 0 <= vert_idx < num_verts and weight > 0.0001:  # Skip tiny weights
                            vertex_weights[vert_idx].append((bone_idx, weight))
                
                # Normalize weights for each vertex (should sum to 1.0)
                weights_found = 0
                for vert_idx, weights in enumerate(vertex_weights):
                    if weights:
                        weights_found += 1
                        total_weight = sum(w for _, w in weights)
                        if total_weight > 0:
                            # Normalize
                            normalized = [(bone_idx, w / total_weight) for bone_idx, w in weights]
                            # Sort by weight (highest first) and keep top 4 influences
                            normalized.sort(key=lambda x: x[1], reverse=True)
                            vertex_weights[vert_idx] = normalized[:4]
                        else:
                            # No valid weights, bind to root
                            vertex_weights[vert_idx] = [(0, 1.0)]
                    else:
                        # No weights for this vertex, bind to root bone
                        vertex_weights[vert_idx] = [(0, 1.0)]
                
                print(f"    Extracted weights for {weights_found}/{num_verts} vertices")
            else:
                print(f"    No skin weights found, binding all vertices to root bone")
                # Bind all vertices to root bone
                for vert_idx in range(num_verts):
                    vertex_weights[vert_idx] = [(0, 1.0)]
        
        except Exception as e:
            print(f"    Warning: Failed to extract skin weights: {e}")
            # Fallback: bind all to root
            for vert_idx in range(num_verts):
                vertex_weights[vert_idx] = [(0, 1.0)]
        
        # Add to global skin weights list
        self.data.skin_weights.extend(vertex_weights)
    
    def _parse_with_pyffi(self, filepath: str) -> NIFData:
        """Parse using PyFFI (fallback, limited FO4 support)"""
        try:
            print(f"  Reading NIF with PyFFI...")
            with open(filepath, 'rb') as f:
                nif_data = NifFormat.Data()
                nif_data.read(f)
                
            print(f"  NIF version: {nif_data.version}")
            print(f"  Root blocks: {len(nif_data.roots)}")
            
            # Extract bones from skeleton
            self._extract_bones(nif_data)
            
            # Extract geometry from all shape nodes
            for block in nif_data.roots:
                self._process_node(block)
                
            print(f"✓ Parsed {filepath}")
            print(f"  Bones: {len(self.data.bones)}")
            print(f"  Vertices: {len(self.data.vertices)}")
            print(f"  Faces: {len(self.data.faces)}")
            
        except ValueError as e:
            if "string too long" in str(e):
                raise RuntimeError(f"Unsupported NIF format. PyNifly not available - FO4 NIF support limited.")
            raise RuntimeError(f"Failed to parse NIF: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to parse NIF: {str(e)}")
            
        return self.data
    
    def _extract_bones(self, nif_data):
        """Extract bone hierarchy from NIF"""
        # Find skeleton root
        for block in nif_data.roots:
            if isinstance(block, NifFormat.NiNode):
                self._process_bone_node(block, -1)
    
    def _process_bone_node(self, node, parent_index: int):
        """Recursively process bone nodes"""
        if isinstance(node, NifFormat.NiNode):
            bone_index = len(self.data.bones)
            
            # Extract transform
            transform = node.get_transform()
            translation = transform.translation
            rotation = transform.rotation
            scale = transform.scale
            
            bone_data = {
                'index': bone_index,
                'parent': parent_index,
                'name': node.name.decode('utf-8') if node.name else f"bone_{bone_index}",
                'translation': (translation.x, translation.y, translation.z),
                'rotation': self._matrix_to_vectors(rotation),
                'scale': (scale, scale, scale)
            }
            
            self.data.bones.append(bone_data)
            
            # Process children
            for child in node.children:
                if child:
                    self._process_bone_node(child, bone_index)
    
    def _process_node(self, node):
        """Process a node to extract geometry"""
        if isinstance(node, NifFormat.BSTriShape):
            self._extract_geometry(node)
        elif isinstance(node, NifFormat.NiTriShape) or isinstance(node, NifFormat.NiTriStrips):
            self._extract_legacy_geometry(node)
        
        # Process children
        if hasattr(node, 'children'):
            for child in node.children:
                if child:
                    self._process_node(child)
    
    def _extract_geometry(self, shape):
        """Extract geometry from BSTriShape (Fallout 4 format)"""
        vertex_data = shape.vertex_data
        num_verts = shape.num_vertices
        
        base_index = len(self.data.vertices)
        
        # Extract vertices
        for i in range(num_verts):
            vertex = vertex_data[i]
            self.data.vertices.append((
                vertex.vertex.x,
                vertex.vertex.y,
                vertex.vertex.z
            ))
            
            # Normals
            if hasattr(vertex, 'normal'):
                self.data.normals.append((
                    vertex.normal.x,
                    vertex.normal.y,
                    vertex.normal.z
                ))
            else:
                self.data.normals.append((0, 0, 1))
            
            # UVs
            if hasattr(vertex, 'uv'):
                self.data.uvs.append((vertex.uv.u, vertex.uv.v))
            else:
                self.data.uvs.append((0, 0))
            
            # Vertex colors
            if hasattr(vertex, 'vertex_colors'):
                vc = vertex.vertex_colors
                self.data.colors.append((vc[0], vc[1], vc[2], vc[3]))
            else:
                self.data.colors.append((1, 1, 1, 1))
        
        # Extract triangles
        if hasattr(shape, 'triangles'):
            for triangle in shape.triangles:
                self.data.faces.append((
                    base_index + triangle.v1,
                    base_index + triangle.v2,
                    base_index + triangle.v3
                ))
        
        # Extract skin weights if present
        self._extract_skin_data(shape, base_index, num_verts)
        
        # Extract material
        self._extract_material(shape)
    
    def _extract_legacy_geometry(self, shape):
        """Extract geometry from older NIF formats"""
        # Get geometry data
        geom_data = shape.data
        if not geom_data:
            return
            
        base_index = len(self.data.vertices)
        
        # Vertices
        for vertex in geom_data.vertices:
            self.data.vertices.append((vertex.x, vertex.y, vertex.z))
        
        # Normals
        if geom_data.has_normals:
            for normal in geom_data.normals:
                self.data.normals.append((normal.x, normal.y, normal.z))
        else:
            self.data.normals.extend([(0, 0, 1)] * len(geom_data.vertices))
        
        # UVs
        if geom_data.uv_sets:
            for uv in geom_data.uv_sets[0]:
                self.data.uvs.append((uv.u, uv.v))
        else:
            self.data.uvs.extend([(0, 0)] * len(geom_data.vertices))
        
        # Colors
        if geom_data.has_vertex_colors:
            for color in geom_data.vertex_colors:
                self.data.colors.append((color.r, color.g, color.b, color.a))
        else:
            self.data.colors.extend([(1, 1, 1, 1)] * len(geom_data.vertices))
        
        # Triangles
        for triangle in geom_data.triangles:
            self.data.faces.append((
                base_index + triangle.v1,
                base_index + triangle.v2,
                base_index + triangle.v3
            ))
    
    def _extract_skin_data(self, shape, base_index: int, num_verts: int):
        """Extract skin weights from shape"""
        # Initialize empty weights for all vertices
        for _ in range(num_verts):
            self.data.skin_weights.append([])
        
        # Look for skin instance
        skin_instance = shape.skin_instance
        if not skin_instance:
            return
            
        # Get bone nodes and weights
        if hasattr(skin_instance, 'bones'):
            for bone_idx, bone_node in enumerate(skin_instance.bones):
                bone_name = bone_node.name.decode('utf-8') if bone_node and bone_node.name else f"bone_{bone_idx}"
                
                # Find bone index in our bone list
                bone_index = -1
                for idx, bone in enumerate(self.data.bones):
                    if bone['name'] == bone_name:
                        bone_index = idx
                        break
                
                if bone_index == -1:
                    continue
                
                # Get weight data for this bone
                if hasattr(skin_instance, 'bone_data') and bone_idx < len(skin_instance.bone_data):
                    bone_data = skin_instance.bone_data[bone_idx]
                    if hasattr(bone_data, 'vertex_weights'):
                        for weight_data in bone_data.vertex_weights:
                            vert_idx = weight_data.index
                            weight = weight_data.weight
                            if 0 <= vert_idx < num_verts:
                                self.data.skin_weights[base_index + vert_idx].append((bone_index, weight))
    
    def _extract_material(self, shape):
        """Extract material properties"""
        # Get shader property
        for prop in shape.properties:
            if isinstance(prop, NifFormat.BSLightingShaderProperty):
                material = {
                    'name': f"material_{len(self.data.materials)}",
                    'shader': 'Phong',
                    'diffuse_texture': '',
                    'normal_texture': '',
                    'specular_color': (0.5, 0.5, 0.5, 1.0)
                }
                
                # Get texture set
                if prop.texture_set:
                    textures = prop.texture_set.textures
                    if len(textures) > 0 and textures[0]:
                        material['diffuse_texture'] = textures[0].decode('utf-8')
                    if len(textures) > 1 and textures[1]:
                        material['normal_texture'] = textures[1].decode('utf-8')
                
                self.data.materials.append(material)
                return
        
        # Default material if none found
        if not self.data.materials:
            self.data.materials.append({
                'name': 'default_material',
                'shader': 'Phong',
                'diffuse_texture': '',
                'normal_texture': '',
                'specular_color': (0.5, 0.5, 0.5, 1.0)
            })
    
    def _matrix_to_vectors(self, matrix) -> Tuple:
        """Convert rotation matrix to X, Y, Z vectors"""
        return (
            (matrix.m11, matrix.m12, matrix.m13),
            (matrix.m21, matrix.m22, matrix.m23),
            (matrix.m31, matrix.m32, matrix.m33)
        )


if __name__ == "__main__":
    # Test parsing
    import sys
    if len(sys.argv) > 1:
        parser = NIFParser()
        data = parser.parse(sys.argv[1])
        print(f"\n✓ Successfully parsed: {data.name}")
        print(f"  Bones: {len(data.bones)}")
        print(f"  Vertices: {len(data.vertices)}")
        print(f"  Faces: {len(data.faces)}")
        print(f"  Materials: {len(data.materials)}")
