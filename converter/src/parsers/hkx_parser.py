"""
HKX Parser for Fallout 4 Animations
Handles .hkx files using HKXPack (Java tool for Havok 2014 format)
"""

import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Transform:
    """Bone transform at a specific frame"""
    translation: Tuple[float, float, float]  # X, Y, Z position
    rotation: Tuple[float, float, float, float]  # Quaternion (X, Y, Z, W)
    scale: float = 1.0


@dataclass
class FrameData:
    """Single frame of animation"""
    frame_number: int
    bone_transforms: Dict[str, Transform]  # bone_name → transform


@dataclass
class HKXData:
    """Container for parsed HKX animation data"""
    name: str = ""
    bones: List[str] = None
    framerate: float = 30.0
    num_frames: int = 0
    frames: List[FrameData] = None
    
    def __post_init__(self):
        if self.bones is None:
            self.bones = []
        if self.frames is None:
            self.frames = []


class HKXParser:
    """Parse Fallout 4 HKX animation files using HKXPack"""
    
    def __init__(self, hkxpack_path: str = None):
        if hkxpack_path is None:
            # Try to find hkxpack-cli.jar relative to this file
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            hkxpack_path = os.path.join(script_dir, "tools", "hkxpack-cli.jar")
        
        self.hkxpack_path = hkxpack_path
        
    def parse(self, filepath: str) -> HKXData:
        """
        Parse an HKX file and extract animation data
        
        Args:
            filepath: Path to .hkx animation file
            
        Returns:
            HKXData object containing parsed animation
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"HKX file not found: {filepath}")
        
        print(f"\n=== Parsing HKX Animation ===")
        print(f"  File: {os.path.basename(filepath)}")
            
        data = HKXData()
        data.name = os.path.splitext(os.path.basename(filepath))[0]
        
        # Step 1: Find skeleton.hkx
        skeleton_path = self._find_skeleton(filepath)
        if not skeleton_path:
            print(f"  ⚠️ Warning: Could not find skeleton.hkx")
            return data
        else:
            print(f"  ✓ Found skeleton: {os.path.basename(skeleton_path)}")
        
        # Step 2: Convert skeleton HKX to XML
        print(f"  Converting skeleton to XML...")
        skeleton_xml = tempfile.NamedTemporaryFile(suffix='_skeleton.xml', delete=False)
        skeleton_xml_path = skeleton_xml.name
        skeleton_xml.close()
        
        if not self._convert_to_xml(skeleton_path, skeleton_xml_path):
            print(f"  ✗ Failed to convert skeleton to XML")
            return data
        
        # Step 3: Convert animation HKX to XML
        print(f"  Converting animation to XML...")
        anim_xml = tempfile.NamedTemporaryFile(suffix='_anim.xml', delete=False)
        anim_xml_path = anim_xml.name
        anim_xml.close()
        
        if not self._convert_to_xml(filepath, anim_xml_path):
            print(f"  ✗ Failed to convert animation to XML")
            try:
                os.remove(skeleton_xml_path)
            except:
                pass
            return data
        
        # Step 4: Parse XMLs
        try:
            print(f"  ✓ Parsing skeleton XML...")
            bone_names = self._parse_skeleton_xml(skeleton_xml_path)
            print(f"    Found {len(bone_names)} bones")
            
            print(f"  ✓ Parsing animation XML...")
            animation_data = self._parse_animation_xml(anim_xml_path, bone_names)
            
            data.bones = animation_data['bones']
            data.framerate = animation_data['framerate']
            data.num_frames = animation_data['num_frames']
            data.frames = animation_data['frames']
            
            print(f"  ✓ Parsed animation:")
            print(f"    Bones: {len(data.bones)}")
            print(f"    Frames: {data.num_frames}")
            print(f"    Framerate: {data.framerate:.2f} fps")
            
        finally:
            # Clean up temporary XML files
            for temp_file in [skeleton_xml_path, anim_xml_path]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
        
        return data
    
    def _find_skeleton(self, hkx_path: str) -> Optional[str]:
        """
        Find the skeleton.hkx file for this animation
        
        Fallout 4 structure:
        - Meshes/Actors/CreatureName/Animations/AnimName.hkx
        - Meshes/Actors/CreatureName/CharacterAssets/skeleton.hkx
        """
        animation_dir = os.path.dirname(hkx_path)
        parent_dir = os.path.dirname(animation_dir)
        
        # Try standard CharacterAssets location
        skeleton_path = os.path.join(parent_dir, "CharacterAssets", "skeleton.hkx")
        if os.path.exists(skeleton_path):
            return skeleton_path
        
        # Try lowercase
        skeleton_path = os.path.join(parent_dir, "characterassets", "skeleton.hkx")
        if os.path.exists(skeleton_path):
            return skeleton_path
        
        # Try same directory as animation
        skeleton_path = os.path.join(animation_dir, "skeleton.hkx")
        if os.path.exists(skeleton_path):
            return skeleton_path
        
        return None
    
    def _convert_to_xml(self, hkx_path: str, xml_path: str) -> bool:
        """
        Convert HKX to XML using HKXPack
        
        Returns True if successful
        """
        if not os.path.exists(self.hkxpack_path):
            raise FileNotFoundError(f"hkxpack-cli.jar not found at: {self.hkxpack_path}")
        
        try:
            # Run: java -jar hkxpack-cli.jar unpack input.hkx -o output.xml
            result = subprocess.run(
                ["java", "-jar", self.hkxpack_path, "unpack", hkx_path, "-o", xml_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"    ⚠️ HKXPack returned error code {result.returncode}")
                if result.stderr:
                    print(f"    Error: {result.stderr.strip()}")
                return False
            
            if not os.path.exists(xml_path) or os.path.getsize(xml_path) == 0:
                print(f"    ⚠️ XML file was not created or is empty")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"    ✗ HKXPack timed out")
            return False
        except Exception as e:
            print(f"    ✗ Error running HKXPack: {e}")
            return False
    
    def _parse_skeleton_xml(self, xml_path: str) -> List[str]:
        """
        Parse skeleton XML to extract bone names
        
        Returns list of bone names in order
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        bones = []
        
        # Find hkaSkeleton object
        for hkobject in root.findall(".//hkobject[@class='hkaSkeleton']"):
            # Find bones parameter
            bones_param = hkobject.find(".//hkparam[@name='bones']")
            if bones_param is not None:
                # Each bone is an hkobject with a name parameter
                for bone_obj in bones_param.findall("hkobject"):
                    name_param = bone_obj.find("hkparam[@name='name']")
                    if name_param is not None and name_param.text:
                        bones.append(name_param.text)
                break
        
        return bones
    
    def _parse_animation_xml(self, xml_path: str, bone_names: List[str]) -> dict:
        """
        Parse animation XML to extract keyframe data
        
        Returns dict with animation data
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        framerate = 30.0
        duration = 0.0
        num_tracks = 0
        num_frames = 0
        
        # Find hkaSplineCompressedAnimation object
        for hkobject in root.findall(".//hkobject[@class='hkaSplineCompressedAnimation']"):
            # Get duration
            duration_param = hkobject.find("hkparam[@name='duration']")
            if duration_param is not None:
                duration = float(duration_param.text)
            
            # Get number of transform tracks
            tracks_param = hkobject.find("hkparam[@name='numberOfTransformTracks']")
            if tracks_param is not None:
                num_tracks = int(tracks_param.text)
            
            # Get num frames
            frames_param = hkobject.find("hkparam[@name='numFrames']")
            if frames_param is not None:
                num_frames = int(frames_param.text)
            
            break
        
        # Calculate framerate from duration and frames
        if duration > 0 and num_frames > 0:
            framerate = (num_frames - 1) / duration
        
        # TODO: Extract actual keyframe data from compressed spline format
        # This is complex - for now just return structure with identity transforms
        frames_data = []
        for frame_idx in range(num_frames):
            bone_transforms = {}
            for bone_name in bone_names:
                bone_transforms[bone_name] = Transform(
                    translation=(0.0, 0.0, 0.0),
                    rotation=(0.0, 0.0, 0.0, 1.0),
                    scale=1.0
                )
            frames_data.append(FrameData(frame_idx, bone_transforms))
        
        return {
            'bones': bone_names,
            'framerate': framerate,
            'num_frames': num_frames,
            'frames': frames_data
        }


if __name__ == "__main__":
    # Test parsing
    import sys
    if len(sys.argv) > 1:
        parser = HKXParser()
        data = parser.parse(sys.argv[1])
        print(f"\n✓ Processed: {data.name}")
