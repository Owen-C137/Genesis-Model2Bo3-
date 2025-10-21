"""
NIF Parser for Fallout 4 Models
Extracts geometry, skeleton, and material data from .nif files
"""

import os
import sys
import numpy as np
from typing import Dict, List, Tuple, Optional

# Fix Unicode output encoding for Windows console
# Only wrap if we have a real stdout/stderr with buffer attribute (not GUI's custom wrapper)
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except:
            pass  # GUI or other custom stdout, skip wrapping
    if hasattr(sys.stderr, 'buffer'):
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except:
            pass  # GUI or other custom stderr, skip wrapping

# Try pynifly first (better FO4 support), fallback to PyFFI
try:
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
            
            # Debug: Print node hierarchy
            if hasattr(nif, 'nodes') and nif.nodes:
                print(f"  Nodes found: {len(nif.nodes)}")
                for node_name, node in list(nif.nodes.items())[:10]:  # Show first 10
                    if hasattr(node, 'transform'):
                        trans = node.transform.translation if hasattr(node.transform, 'translation') else None
                        if trans:
                            t = (trans.x if hasattr(trans, 'x') else trans[0],
                                 trans.y if hasattr(trans, 'y') else trans[1],
                                 trans.z if hasattr(trans, 'z') else trans[2])
                            # Also show parent
                            parent_name = "None"
                            if hasattr(node, 'parent') and node.parent and hasattr(node.parent, 'name'):
                                parent_name = node.parent.name
                            print(f"    Node '{node_name}' (parent: {parent_name}): translation = {t}")
            
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
                    
                    # Debug: Print all available attributes on the shape
                    print(f"    Shape attributes: {[attr for attr in dir(shape) if not attr.startswith('_')][:20]}")
                    
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
            
            # If STILL no bones found, check the main NIF's node hierarchy
            # This is common for furniture/static props where nodes = bones
            if not all_bone_names and hasattr(nif, 'nodes') and nif.nodes:
                print(f"  No skinned bones found, using NIF node hierarchy as bones...")
                # Use all nodes as bones - BUT skip:
                # 1. Shape nodes (those ending with :number) - these are mesh data
                # 2. Special nodes like "OrderedRenderingNode" - these are engine-specific, not bones
                special_node_names = {'OrderedRenderingNode', 'RenderingNode', 'BSFadeNode'}
                for node_name in nif.nodes.keys():
                    # Skip shape nodes like "CryoPod00:0", "arm005:0", etc.
                    # These are mesh data, not bones
                    if ':' in node_name:
                        continue
                    # Skip special engine nodes
                    if node_name in special_node_names:
                        print(f"  Skipping special node '{node_name}' (not a bone)")
                        continue
                    all_bone_names.add(node_name)
                print(f"  Using {len(all_bone_names)} nodes as bones: {list(all_bone_names)[:10]}")
            
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
            
            # Special nodes to skip (not actual bones)
            special_node_names = {'OrderedRenderingNode', 'RenderingNode', 'BSFadeNode'}
            
            # Track offset from removed special nodes (we'll need to subtract this from shapes)
            self._removed_node_offset = (0, 0, 0)
            for special_name in special_node_names:
                if special_name in nodes:
                    special_node = nodes[special_name]
                    if hasattr(special_node, 'transform') and hasattr(special_node.transform, 'translation'):
                        t = special_node.transform.translation
                        self._removed_node_offset = (
                            t.x if hasattr(t, 'x') else t[0],
                            t.y if hasattr(t, 'y') else t[1],
                            t.z if hasattr(t, 'z') else t[2]
                        )
                        print(f"  Removed special node '{special_name}' at offset: {self._removed_node_offset}")
                        break
            
            # Add all parent bones recursively
            for bone_name in list(bones_to_include):
                if bone_name in nodes:
                    node = nodes[bone_name]
                    # Walk up the parent chain
                    current = node
                    while hasattr(current, 'parent') and current.parent:
                        parent_name = current.parent.name if hasattr(current.parent, 'name') else None
                        if parent_name and parent_name in nodes:
                            # Skip file root nodes, engine bones, and special nodes we don't want
                            if ('\\' not in parent_name and '/' not in parent_name and
                                parent_name not in ['skeleton.nif', 'COM', 'Root'] and
                                parent_name not in special_node_names):
                                bones_to_include.add(parent_name)
                            elif parent_name in special_node_names:
                                print(f"  Skipping parent node '{parent_name}' (special node, not a bone)")
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
                            if local_translation != (0, 0, 0):
                                print(f"    Bone '{bone_name}' local translation: {local_translation}")
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
                        'translation': local_translation,  # Start with local, will update for root bones
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
                    # Normal case: parent exists in our bone list - USE LOCAL TRANSFORMS
                    bone['parent'] = bone_name_to_index[parent_name]
                    parent_count[parent_name] = parent_count.get(parent_name, 0) + 1
                    # Use local transform (hierarchy will be applied by viewer)
                    bone['translation'] = bone['local_translation']
                    bone['rotation'] = bone['local_rotation']
                    print(f"  {bone['name']}: parent={parent_name} (index {bone['parent']}), using LOCAL: {bone['local_translation']}")
                    
                elif parent_name and ('\\' in parent_name or '/' in parent_name or parent_name in ['COM', 'Root']):
                    # Parent is filtered out (file root, COM, etc) - USE GLOBAL with COM offset subtracted
                    bone['parent'] = -1
                    parent_count['<filtered_parent>'] = parent_count.get('<filtered_parent>', 0) + 1
                    
                    # CRITICAL FIX: Use global position minus COM offset
                    if bone['global_translation']:
                        bone['translation'] = (
                            bone['global_translation'][0] - com_offset[0],
                            bone['global_translation'][1] - com_offset[1],
                            bone['global_translation'][2] - com_offset[2]
                        )
                        if bone['global_rotation']:
                            bone['rotation'] = bone['global_rotation']
                        print(f"  {bone['name']}: parent filtered ({parent_name}), using GLOBAL {bone['global_translation']} - COM offset {com_offset} = {bone['translation']}")
                    else:
                        print(f"  WARNING: {bone['name']} parent filtered but no global transform")
                else:
                    # No valid parent found - make it a root, USE GLOBAL
                    bone['parent'] = -1
                    if bone['global_translation']:
                        bone['translation'] = bone['global_translation']
                        if bone['global_rotation']:
                            bone['rotation'] = bone['global_rotation']
                        print(f"  {bone['name']}: no parent found, making root with GLOBAL: {bone['global_translation']}")
                    else:
                        print(f"  {bone['name']}: no parent found, making root with LOCAL: {bone['local_translation']}")
                
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
        
        # Filter out FX/effect meshes that shouldn't be exported
        # These are visual effects like water streams, refraction, particles, etc.
        # Use specific FX mesh name patterns to avoid false positives
        fx_patterns = [
            'shinestream', 'refractstream', 'waterstream', 
            'particle', 'emitter', 
            'fxemit', 'fxlight', 'fxglow',
            'lighthelper', 'addonnode'
        ]
        shape_name_lower = shape_name.lower()
        for pattern in fx_patterns:
            if pattern in shape_name_lower:
                print(f"  Skipping FX mesh: {shape_name} (matches pattern '{pattern}')")
                return
        
        base_index = len(self.data.vertices)
        
        # CRITICAL: Get the shape's parent node transform to position it correctly
        # ONLY add offset if the parent node is a BONE (part of skeleton)
        # If parent is just a grouping node, PyNifly already has vertices in correct space
        shape_offset = (0, 0, 0)
        shape_rotation = None
        shape_parent_is_bone = False
        shape_parent_bone_name = None  # Track which bone this shape should be bound to
        
        # Build set of bone names for quick lookup
        bone_names = set(bone['name'] for bone in self.data.bones) if self.data.bones else set()
        
        # Try to find this shape's node in the node hierarchy
        if hasattr(nif, 'nodes') and nif.nodes:
            # Try to find a node for this shape
            # Priority: 1) Base name if shape has ":" (e.g., "arm005" from "arm005:0")
            #          2) Full shape name (e.g., "TerminalConsoleOn:0")
            base_name = shape_name.split(':')[0] if ':' in shape_name else shape_name
            

            
            # First try the BASE name if it's different from full shape name (e.g., "arm005:0" -> check "arm005")
            if base_name in nif.nodes and base_name != shape_name:
                node = nif.nodes[base_name]
                
                # Check if this base node is a BONE
                shape_parent_is_bone = base_name in bone_names
                if shape_parent_is_bone:
                    shape_parent_bone_name = base_name
                
                # Use GLOBAL transform to get cumulative position including all ancestors
                if hasattr(node, 'global_transform') and hasattr(node.global_transform, 'translation'):
                    t = node.global_transform.translation
                    shape_offset = (
                        t.x if hasattr(t, 'x') else t[0],
                        t.y if hasattr(t, 'y') else t[1],
                        t.z if hasattr(t, 'z') else t[2]
                    )
                    print(f"    Using base node '{base_name}' GLOBAL transform: {shape_offset}")
                elif hasattr(node, 'transform') and hasattr(node.transform, 'translation'):
                    # Fallback to local if global not available
                    t = node.transform.translation
                    shape_offset = (
                        t.x if hasattr(t, 'x') else t[0],
                        t.y if hasattr(t, 'y') else t[1],
                        t.z if hasattr(t, 'z') else t[2]
                    )
                    print(f"    Using base node '{base_name}' LOCAL transform: {shape_offset}")
                if hasattr(node, 'transform') and hasattr(node.transform, 'rotation'):
                    shape_rotation = node.transform.rotation
            
            # Otherwise check the full shape name
            elif shape_name in nif.nodes:
                node = nif.nodes[shape_name]
                
                # Check if the shape node itself is a bone OR if its parent is a bone
                shape_node_is_bone = shape_name in bone_names
                parent_name = node.parent.name if hasattr(node, 'parent') and node.parent and hasattr(node.parent, 'name') else None
                parent_is_bone = parent_name in bone_names if parent_name else False
                shape_parent_is_bone = shape_node_is_bone or parent_is_bone
                
                # Store the parent bone name for vertex binding
                if shape_node_is_bone:
                    shape_parent_bone_name = shape_name
                elif parent_is_bone:
                    shape_parent_bone_name = parent_name
                

                
                # Use the shape's LOCAL transform
                if hasattr(node, 'transform') and hasattr(node.transform, 'translation'):
                    t = node.transform.translation
                    local_trans = (
                        t.x if hasattr(t, 'x') else t[0],
                        t.y if hasattr(t, 'y') else t[1],
                        t.z if hasattr(t, 'z') else t[2]
                    )
                    if local_trans != (0, 0, 0):
                        shape_offset = local_trans
                        if parent_is_bone:
                            print(f"    Using shape '{shape_name}' LOCAL transform (parent is bone): {shape_offset}")
                        else:
                            print(f"    Using shape '{shape_name}' LOCAL transform: {shape_offset}")
                    else:
                        if parent_is_bone:
                            print(f"    Shape '{shape_name}' at (0,0,0) relative to bone parent - using NO offset")
                        else:
                            print(f"    Shape '{shape_name}' at (0,0,0) - using NO offset")
                
                # OLD LOGIC REMOVED
                if False and hasattr(node, 'parent') and node.parent:
                    parent_name = node.parent.name if hasattr(node.parent, 'name') else None
                    if parent_name and parent_name in nif.nodes:
                        parent_node = nif.nodes[parent_name]
                        # Use global transform to get cumulative position
                        if hasattr(parent_node, 'global_transform') and hasattr(parent_node.global_transform, 'translation'):
                            t = parent_node.global_transform.translation
                            shape_offset = (
                                t.x if hasattr(t, 'x') else t[0],
                                t.y if hasattr(t, 'y') else t[1],
                                t.z if hasattr(t, 'z') else t[2]
                            )
                            print(f"    Using parent '{parent_name}' GLOBAL transform: {shape_offset}")
                        elif hasattr(parent_node, 'transform') and hasattr(parent_node.transform, 'translation'):
                            # Fallback to local
                            t = parent_node.transform.translation
                            shape_offset = (
                                t.x if hasattr(t, 'x') else t[0],
                                t.y if hasattr(t, 'y') else t[1],
                                t.z if hasattr(t, 'z') else t[2]
                            )
                            print(f"    Using parent '{parent_name}' LOCAL transform: {shape_offset}")
                
                if hasattr(node, 'transform') and hasattr(node.transform, 'rotation'):
                    shape_rotation = node.transform.rotation
        
        # FALLBACK: If shape has no parent bone (orphan shape), try to find a related mesh
        # This handles shapes like ScreenType:0 (layer) that should bind to same bone as Screen:0 (base)
        if not shape_parent_bone_name:
            print(f"    Shape '{shape_name}' has no parent bone, looking for related mesh")
            found_related = False
            
            # Try to find a base mesh name by removing common suffixes
            # e.g., "ScreenType:0" -> look for "Screen:0" or "Screen"
            potential_base_names = []
            
            # Remove "Type" suffix if present
            if "Type" in base_name:
                potential_base_names.append(base_name.replace("Type", ""))
            
            # Try just the base word before "Type"
            if "Type" in shape_name:
                base_word = shape_name.split("Type")[0]
                potential_base_names.append(base_word)
                # Also try with layer number
                if ":" in shape_name:
                    layer_num = shape_name.split(":")[-1]
                    potential_base_names.append(f"{base_word}:{layer_num}")
            
            print(f"    Checking for related meshes: {potential_base_names}")
            
            # Find the nearest bone to this shape based on distance
            # This works for orphan shapes that don't have a parent bone
            if self.data.bones and shape_offset != (0, 0, 0):
                print(f"    Finding nearest bone to shape at position {shape_offset}")
                
                # First compute global positions for all bones
                import math
                bone_global_positions = {}
                for bone in self.data.bones:
                    if bone['parent'] == -1:
                        # Root bone - translation is already global
                        bone_global_positions[bone['name']] = bone['translation']
                    else:
                        # Child bone - need to compute global from parent chain
                        global_pos = list(bone['translation'])
                        parent_idx = bone['parent']
                        while parent_idx >= 0:
                            parent_bone = self.data.bones[parent_idx]
                            global_pos[0] += parent_bone['translation'][0]
                            global_pos[1] += parent_bone['translation'][1]
                            global_pos[2] += parent_bone['translation'][2]
                            parent_idx = parent_bone['parent']
                        bone_global_positions[bone['name']] = tuple(global_pos)
                
                # Calculate distance to each bone's global position
                nearest_bone = None
                nearest_distance = float('inf')
                
                for bone_name, bone_pos in bone_global_positions.items():
                    # Calculate 3D distance
                    dx = shape_offset[0] - bone_pos[0]
                    dy = shape_offset[1] - bone_pos[1]
                    dz = shape_offset[2] - bone_pos[2]
                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_bone = bone_name
                
                if nearest_bone:
                    shape_parent_bone_name = nearest_bone
                    shape_parent_is_bone = True
                    print(f"    Nearest bone is '{nearest_bone}' at distance {nearest_distance:.2f} units")
                    found_related = True
                    
                    # Subtract removed node offset from shape position
                    # Orphan shapes were positioned relative to removed special nodes
                    if hasattr(self, '_removed_node_offset') and self._removed_node_offset != (0, 0, 0):
                        old_offset = shape_offset
                        shape_offset = (
                            shape_offset[0] - self._removed_node_offset[0],
                            shape_offset[1] - self._removed_node_offset[1],
                            shape_offset[2] - self._removed_node_offset[2]
                        )
                        print(f"    Adjusted shape offset (removed node at {self._removed_node_offset}): {old_offset} → {shape_offset}")
            
            if not found_related:
                print(f"    No related mesh found, will bind to root bone")
        
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
        
        # Store skin offset for bone adjustment
        if skin_offset != (0, 0, 0):
            self._skin_offset = skin_offset
        
        # Check if this shape has skin weights (skinned mesh)
        has_skin_weights = hasattr(shape, 'bone_weights') and shape.bone_weights and len(shape.bone_weights) > 0
        
        # Get vertices and apply transform if shape has local translation
        # Skinned meshes already have vertices in bind pose and don't need offsets
        verts = shape.verts
        
        for vert in verts:
            if has_skin_weights:
                # Skinned mesh: vertices already in bind pose, use as-is
                self.data.vertices.append((vert[0], vert[1], vert[2]))
            elif shape_offset != (0, 0, 0):
                # Apply shape's local transform
                transformed_vert = (
                    vert[0] + shape_offset[0],
                    vert[1] + shape_offset[1],
                    vert[2] + shape_offset[2]
                )
                self.data.vertices.append(transformed_vert)
            else:
                # No offset needed
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
        
        # Extract skin weights from PyNifly
        num_verts = len(verts)
        self._extract_nifly_skin_weights(shape, base_index, num_verts, shape_parent_bone_name)
        
        # Extract material info FIRST, before assigning to faces
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
        
        # Check if we already have a material with the same textures
        # This prevents duplicate materials for shapes using the same texture
        material_index = None
        for idx, existing_mat in enumerate(self.data.materials):
            if (existing_mat['diffuse_texture'] == material['diffuse_texture'] and
                existing_mat['normal_texture'] == material['normal_texture']):
                # Reuse existing material
                material_index = idx
                print(f"    Reusing existing material {idx} (same textures)")
                break
        
        # If no matching material found, create a new one
        if material_index is None:
            material_index = len(self.data.materials)
            self.data.materials.append(material)
            print(f"    Created new material {material_index}: diffuse={os.path.basename(material['diffuse_texture']) if material['diffuse_texture'] else 'none'}")
        
        # NOW assign material index to all faces in this shape
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
    
    def _extract_nifly_skin_weights(self, shape, base_index: int, num_verts: int, parent_bone_name: str = None):
        """Extract skin weights from PyNifly shape
        
        Args:
            shape: PyNifly shape object
            base_index: Starting vertex index for this shape
            num_verts: Number of vertices in this shape
            parent_bone_name: Name of the bone this shape is parented to (for rigid binding)
        """
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
                # No skin weights - this is rigid geometry, bind to parent bone
                # Find which bone index to bind to
                bone_idx = 0  # Default to root
                if parent_bone_name:
                    # Find the bone index for the parent bone
                    for idx, bone in enumerate(self.data.bones):
                        if bone['name'] == parent_bone_name:
                            bone_idx = idx
                            print(f"    No skin weights found, binding all vertices to parent bone '{parent_bone_name}' (index {bone_idx})")
                            break
                    else:
                        # Parent bone not found in bone list!
                        bone_list_debug = [(idx, b['name']) for idx, b in enumerate(self.data.bones)]
                        print(f"    WARNING: Parent bone '{parent_bone_name}' not found in bone list, binding to root (index 0)")
                        print(f"    Available bones: {bone_list_debug}")
                else:
                    print(f"    No skin weights found, binding all vertices to root bone (index 0)")
                
                # Bind all vertices to the determined bone
                for vert_idx in range(num_verts):
                    vertex_weights[vert_idx] = [(bone_idx, 1.0)]
        
        except Exception as e:
            print(f"    Warning: Failed to extract skin weights: {e}")
            # Fallback: bind to parent bone if available, otherwise root
            bone_idx = 0
            if parent_bone_name:
                for idx, bone in enumerate(self.data.bones):
                    if bone['name'] == parent_bone_name:
                        bone_idx = idx
                        break
            for vert_idx in range(num_verts):
                vertex_weights[vert_idx] = [(bone_idx, 1.0)]
        
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
