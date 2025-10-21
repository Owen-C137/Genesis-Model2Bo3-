"""Analyze NIF files to understand structure differences"""
import sys
import os
sys.path.insert(0, 'src/pynifly')
sys.path.insert(0, 'src')

from pynifly import NifFile

# Initialize PyNifly with DLL path
dll_path = os.path.abspath('src/pynifly/NiflyDLL/x64/NiflyDLL.dll')
NifFile.Load(dll_path)

def analyze_nif(filepath, name):
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name}")
    print(f"{'='*80}")
    
    nif = NifFile(filepath)
    
    print(f"\n--- SHAPES ({len(nif.shapes)}) ---")
    for i, shape in enumerate(nif.shapes):
        print(f"\nShape {i}: {shape.name}")
        
        # Check if vertices are in local or global space
        verts = shape.verts
        if len(verts) > 0:
            v = verts[0]
            print(f"  First vertex: ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})")
            
            # Check vertex range
            min_vals = [min(v[i] for v in verts) for i in range(3)]
            max_vals = [max(v[i] for v in verts) for i in range(3)]
            print(f"  Vertex range: X=[{min_vals[0]:.1f}, {max_vals[0]:.1f}], Y=[{min_vals[1]:.1f}, {max_vals[1]:.1f}], Z=[{min_vals[2]:.1f}, {max_vals[2]:.1f}]")
        
        # Check for skin data
        if hasattr(shape, 'has_skin_instance') and shape.has_skin_instance:
            print(f"  ✓ Has skin instance (skinned mesh)")
        else:
            print(f"  ✗ No skin instance (static mesh)")
        
        # Check for skin transform
        if hasattr(shape, 'skin_transform'):
            st = shape.skin_transform
            if hasattr(st, 'translation'):
                t = st.translation
                print(f"  Skin transform translation: ({t.x:.3f}, {t.y:.3f}, {t.z:.3f})")
        
        # Check bone weights
        if hasattr(shape, 'bone_weights') and shape.bone_weights:
            print(f"  Bone weights: {len(shape.bone_weights)} vertices weighted")
        else:
            print(f"  No bone weights")
    
    print(f"\n--- NODES ({len(nif.nodes)}) ---")
    for node_name, node in nif.nodes.items():
        parent_name = node.parent.name if hasattr(node, 'parent') and node.parent else 'None'
        
        # Get local transform
        local_trans = (0, 0, 0)
        if hasattr(node, 'transform') and hasattr(node.transform, 'translation'):
            t = node.transform.translation
            local_trans = (
                t.x if hasattr(t, 'x') else t[0],
                t.y if hasattr(t, 'y') else t[1],
                t.z if hasattr(t, 'z') else t[2]
            )
        
        # Get global transform
        global_trans = (0, 0, 0)
        if hasattr(node, 'global_transform') and hasattr(node.global_transform, 'translation'):
            t = node.global_transform.translation
            global_trans = (
                t.x if hasattr(t, 'x') else t[0],
                t.y if hasattr(t, 'y') else t[1],
                t.z if hasattr(t, 'z') else t[2]
            )
        
        print(f"\nNode '{node_name}'")
        print(f"  Parent: {parent_name}")
        print(f"  Local:  ({local_trans[0]:.3f}, {local_trans[1]:.3f}, {local_trans[2]:.3f})")
        print(f"  Global: ({global_trans[0]:.3f}, {global_trans[1]:.3f}, {global_trans[2]:.3f})")
        
        # Check if this node has a corresponding shape
        has_shape = False
        for shape in nif.shapes:
            if shape.name == node_name or shape.name.startswith(f"{node_name}:"):
                has_shape = True
                break
        if has_shape:
            print(f"  ✓ Has shape(s)")

if __name__ == '__main__':
    analyze_nif('c:/Users/owenc/Desktop/Fallout 4 To Bo3/EXAMPLES/CryoPod00.nif', 'CryoPod00.nif')
    analyze_nif('c:/Users/owenc/Desktop/Fallout 4 To Bo3/EXAMPLES/TerminalConsoleOn.nif', 'TerminalConsoleOn.nif')
    analyze_nif('c:/Users/owenc/Desktop/Fallout 4 To Bo3/EXAMPLES/OutfitF.nif', 'OutfitF.nif')
