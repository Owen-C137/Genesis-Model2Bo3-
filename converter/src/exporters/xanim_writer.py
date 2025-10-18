"""
XANIM_EXPORT Writer for Black Ops 3
Generates .XANIM_EXPORT text files from animation data
"""

import os
from typing import List, Dict
from ..parsers.hkx_parser import HKXData, Transform


class XAnimWriter:
    """Write Black Ops 3 XANIM_EXPORT format"""
    
    def __init__(self, version: int = 3):
        self.version = version
        
    def write(self, data: HKXData, output_path: str) -> bool:
        """
        Write HKX animation data to XANIM_EXPORT format
        
        Args:
            data: Parsed HKX animation data
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                self._write_header(f, output_path)
                self._write_parts(f, data)
                self._write_keyframes(f, data)
            
            print(f"✓ Exported animation to: {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to write XANIM_EXPORT: {e}")
            return False
    
    def _write_header(self, f, output_path: str):
        """Write file header"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        
        f.write(f"// Export filename: '{output_path}'\n")
        f.write(f"// Source filename: ''\n")
        f.write(f"// Export time: {timestamp}\n\n")
        f.write("ANIMATION\n")
        f.write(f"VERSION {self.version}\n\n")
    
    def _write_parts(self, f, data: HKXData):
        """Write bone/part list"""
        if not data.bones:
            # Default root bone
            f.write("NUMPARTS 1\n")
            f.write('PART 0 "tag_origin"\n\n')
        else:
            f.write(f"NUMPARTS {len(data.bones)}\n")
            for i, bone_name in enumerate(data.bones):
                f.write(f'PART {i} "{bone_name}"\n')
            f.write("\n")
    
    def _write_keyframes(self, f, data: HKXData):
        """Write animation keyframe data"""
        # Framerate and frame count
        f.write(f"FRAMERATE {data.framerate:.6f}\n")
        f.write(f"NUMFRAMES {data.num_frames}\n\n")
        
        # Write each frame
        for frame in data.frames:
            f.write(f"FRAME {frame.frame_number}\n\n")
            
            # Write transform for each bone in this frame
            for bone_idx, bone_name in enumerate(data.bones):
                # Get transform for this bone (or use identity if missing)
                transform = frame.bone_transforms.get(bone_name)
                if transform is None:
                    # Default identity transform
                    transform = Transform(
                        translation=(0.0, 0.0, 0.0),
                        rotation=(0.0, 0.0, 0.0, 1.0),
                        scale=1.0
                    )
                
                # Write bone header
                f.write(f"PART {bone_idx}\n")
                
                # Write OFFSET (translation)
                tx, ty, tz = transform.translation
                f.write(f"OFFSET {tx:.6f}, {ty:.6f}, {tz:.6f}\n")
                
                # Convert quaternion to 3x3 rotation matrix
                rot_matrix = self._quaternion_to_matrix(transform.rotation)
                
                # Write rotation matrix as X, Y, Z rows
                f.write(f"X {rot_matrix[0][0]:.6f}, {rot_matrix[0][1]:.6f}, {rot_matrix[0][2]:.6f}\n")
                f.write(f"Y {rot_matrix[1][0]:.6f}, {rot_matrix[1][1]:.6f}, {rot_matrix[1][2]:.6f}\n")
                f.write(f"Z {rot_matrix[2][0]:.6f}, {rot_matrix[2][1]:.6f}, {rot_matrix[2][2]:.6f}\n")
                f.write("\n")
    
    def _quaternion_to_matrix(self, quat: tuple) -> list:
        """
        Convert quaternion (x, y, z, w) to 3x3 rotation matrix
        
        Args:
            quat: Quaternion as (x, y, z, w)
            
        Returns:
            3x3 rotation matrix as list of lists
        """
        x, y, z, w = quat
        
        # Normalize quaternion
        length = (x*x + y*y + z*z + w*w) ** 0.5
        if length > 0:
            x, y, z, w = x/length, y/length, z/length, w/length
        
        # Convert to rotation matrix
        # Source: https://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm
        xx = x * x
        xy = x * y
        xz = x * z
        xw = x * w
        yy = y * y
        yz = y * z
        yw = y * w
        zz = z * z
        zw = z * w
        
        matrix = [
            [1 - 2*(yy + zz),     2*(xy - zw),     2*(xz + yw)],
            [    2*(xy + zw), 1 - 2*(xx + zz),     2*(yz - xw)],
            [    2*(xz - yw),     2*(yz + xw), 1 - 2*(xx + yy)]
        ]
        
        return matrix


if __name__ == "__main__":
    # Test writing
    from ..parsers.hkx_parser import HKXParser
    import sys
    
    if len(sys.argv) > 1:
        parser = HKXParser()
        hkx_data = parser.parse(sys.argv[1])
        
        output_path = sys.argv[1].replace('.hkx', '.XANIM_EXPORT')
        writer = XAnimWriter()
        writer.write(hkx_data, output_path)
        print(f"\n✓ Animation conversion complete!")
