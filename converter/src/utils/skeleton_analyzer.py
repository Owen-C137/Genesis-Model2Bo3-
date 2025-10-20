"""
Skeleton structure analyzer for automatic rotation and scale detection
"""
import numpy as np

class SkeletonAnalyzer:
    """Analyzes skeleton structure to determine appropriate coordinate transforms"""
    
    # Target heights for BO3 (in inches/units)
    BO3_STANDING_HEIGHT = 72.0  # Player standing height
    BO3_HEAD_HEIGHT = 64.0      # Approximate head height
    SCALE_MULTIPLIER = 1.1      # 10% bigger to account for BO3 120% world scale
    
    def __init__(self, bones, vertices):
        self.bones = bones
        self.vertices = vertices
        self.bone_dict = {b['name']: b for b in bones}
        self.skeleton_type = None
        self.root_type = None
        self.scale_factor = 1.0
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0
        # Separate mesh rotation (vertices/normals need different rotation than bones)
        self.mesh_rotation_x = 0
        self.mesh_rotation_y = 0
        self.mesh_rotation_z = 0
        
    def analyze(self):
        """Analyze skeleton and determine transforms"""
        self._detect_skeleton_type()
        self._detect_root_type()
        self._calculate_scale()
        self._determine_rotation()
        
        return {
            'skeleton_type': self.skeleton_type,
            'root_type': self.root_type,
            'scale': self.scale_factor,
            'rotation_x': self.rotation_x,
            'rotation_y': self.rotation_y,
            'rotation_z': self.rotation_z,
            'mesh_rotation_x': self.mesh_rotation_x,
            'mesh_rotation_y': self.mesh_rotation_y,
            'mesh_rotation_z': self.mesh_rotation_z
        }
    
    def _detect_skeleton_type(self):
        """Detect if skeleton is hierarchical or flat"""
        # Count bones with parent = 0 (direct children of root)
        root_children = sum(1 for b in self.bones if b['parent'] == 0)
        
        if root_children > len(self.bones) * 0.8:
            # More than 80% are direct children = flat hierarchy
            self.skeleton_type = 'flat'
        else:
            self.skeleton_type = 'hierarchical'
    
    def _detect_root_type(self):
        """Detect root bone type and orientation"""
        if not self.bones:
            self.root_type = 'unknown'
            return
            
        root = self.bones[0]
        root_name = root['name'].lower()
        
        # Check for file roots (flat hierarchies)
        if '.nif' in root_name or 'export' in root_name or 'rear' in root_name:
            self.root_type = 'file_root'
        # Check for spine-based
        elif 'spine' in root_name:
            self.root_type = 'spine'
        # Check for pelvis-based
        elif 'pelvis' in root_name or 'hip' in root_name:
            self.root_type = 'pelvis'
        # Check for special roots
        elif 'root' in root_name:
            self.root_type = 'spineroot'
        else:
            self.root_type = 'unknown'
    
    def _calculate_scale(self):
        """Calculate scale factor to match BO3 player height based on mesh vertices"""
        if not self.vertices or len(self.vertices) == 0:
            print("  Warning: No vertices provided, using default scale")
            self.scale_factor = 0.43  # Default ~43% for FO4 -> BO3
            return
        
        # Get mesh height from vertices (Z axis)
        vert_z = [v[2] for v in self.vertices]
        mesh_height = max(vert_z) - min(vert_z)
        
        if mesh_height < 1:
            print(f"  Warning: Mesh height too small ({mesh_height}), using default scale")
            self.scale_factor = 0.43
            return
        
        # Calculate scale to match BO3 standing player height (72 units)
        # Apply multiplier to account for BO3's 120% world scale
        self.scale_factor = (self.BO3_STANDING_HEIGHT / mesh_height) * self.SCALE_MULTIPLIER
        
        print(f"  Detected mesh height: {mesh_height:.1f} units")
        print(f"  Calculated scale factor: {self.scale_factor:.3f} (target: {self.BO3_STANDING_HEIGHT} units * {self.SCALE_MULTIPLIER}x)")
    
    def _compute_global_height(self, bone):
        """Compute global Z height for a bone in hierarchy"""
        z = bone['translation'][2]
        current = bone
        
        # Walk up parent chain accumulating Z
        visited = set()
        while current['parent'] >= 0:
            bone_id = id(current)
            if bone_id in visited:
                print(f"  Warning: Circular reference detected in bone hierarchy")
                break
            visited.add(bone_id)
            
            current = self.bones[current['parent']]
            z += current['translation'][2]
        
        return abs(z)
    
    def _determine_rotation(self):
        """Determine rotation based on skeleton structure"""
        # EMPIRICALLY DETERMINED CORRECT ROTATIONS for FO4 -> BO3
        # Mesh and bones need DIFFERENT rotations!
        
        # Default bone rotation for Fallout 4 furniture/static props
        # (Characters may need different values - Y=90, Z=90)
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 90
        
        # Store separate mesh rotation (applied to vertices/normals)
        self.mesh_rotation_x = 180
        self.mesh_rotation_y = 180
        self.mesh_rotation_z = -90
        
        if self.skeleton_type == 'flat':
            # Flat hierarchies (Assaultron, SentryBot)
            pass  # Use defaults above
            
        elif self.root_type == 'spine':
            # Spine-based hierarchy (Alien)
            # Tested and confirmed working
            pass  # Use defaults above
            
        elif self.root_type == 'pelvis':
            # Pelvis-based (FeralGhoul)
            pass  # Use defaults above
            
        elif self.root_type == 'spineroot':
            # SpineRoot (some models)
            pass  # Use defaults above
            
        elif self.root_type == 'file_root':
            # File root with mixed structure (Cat is quadruped)
            # May need different rotation - TODO: test
            pass  # Use defaults for now
            
        else:
            # Unknown - use defaults
            pass
        
        print(f"  Skeleton type: {self.skeleton_type}, Root type: {self.root_type}")
        print(f"  Bone rotation: X={self.rotation_x}°, Y={self.rotation_y}°, Z={self.rotation_z}°")
        print(f"  Mesh rotation: X={self.mesh_rotation_x}°, Y={self.mesh_rotation_y}°, Z={self.mesh_rotation_z}°")

    @staticmethod
    def create_rotation_matrix(angle_degrees, axis='y'):
        """Create rotation matrix for given axis - using FO4->BO3 specific transforms"""
        import numpy as np
        
        # SPECIAL CASE: For FO4->BO3 we use specific hardcoded matrices
        # These were empirically determined to work correctly
        if axis == 'y' and angle_degrees == 90:
            # Y+90 transform: FO4 Z-up to BO3 orientation (step 1)
            return np.array([
                [ 0.0,  0.0, -1.0],
                [ 0.0,  1.0,  0.0],
                [ 1.0,  0.0,  0.0]
            ])
        elif axis == 'z' and angle_degrees == 90:
            # Z+90 transform: Rotate to face correct direction (step 2)
            return np.array([
                [ 0.0, -1.0,  0.0],
                [ 1.0,  0.0,  0.0],
                [ 0.0,  0.0,  1.0]
            ])
        
        # Fallback: Standard rotation matrix
        angle_rad = np.radians(angle_degrees)
        c = np.cos(angle_rad)
        s = np.sin(angle_rad)
        
        if axis == 'x':
            return np.array([
                [1, 0, 0],
                [0, c, -s],
                [0, s, c]
            ])
        elif axis == 'y':
            return np.array([
                [c, 0, s],
                [0, 1, 0],
                [-s, 0, c]
            ])
        elif axis == 'z':
            return np.array([
                [c, -s, 0],
                [s, c, 0],
                [0, 0, 1]
            ])
        else:
            return np.eye(3)
