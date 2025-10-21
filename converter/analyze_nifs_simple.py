"""Analyze NIF files using the converter's existing code"""
import sys
sys.path.insert(0, 'src')

from parsers.nif_parser import NIFParser

def analyze_nif(filepath, name):
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name}")
    print(f"{'='*80}")
    
    parser = NIFParser()
    parser._parse_with_nifly(filepath)
    
    print(f"\n--- SUMMARY ---")
    print(f"Bones: {len(parser.data.bones)}")
    print(f"Vertices: {len(parser.data.vertices)}")
    print(f"Faces: {len(parser.data.faces)}")
    
    # Show vertex range
    if parser.data.vertices:
        verts = parser.data.vertices
        min_vals = [min(v[i] for v in verts) for i in range(3)]
        max_vals = [max(v[i] for v in verts) for i in range(3)]
        print(f"\nVertex ranges:")
        print(f"  X: [{min_vals[0]:.1f}, {max_vals[0]:.1f}]")
        print(f"  Y: [{min_vals[1]:.1f}, {max_vals[1]:.1f}]")
        print(f"  Z: [{min_vals[2]:.1f}, {max_vals[2]:.1f}]")
    
    # Show bone positions
    print(f"\n--- BONES ---")
    for i, bone in enumerate(parser.data.bones):
        print(f"Bone {i}: {bone['name']}")
        print(f"  Parent: {bone['parent']}")
        print(f"  Position: ({bone['position'][0]:.3f}, {bone['position'][1]:.3f}, {bone['position'][2]:.3f})")

if __name__ == '__main__':
    analyze_nif('c:/Users/owenc/Desktop/Fallout 4 To Bo3/EXAMPLES/CryoPod00.nif', 'CryoPod00.nif')
    analyze_nif('c:/Users/owenc/Desktop/Fallout 4 To Bo3/EXAMPLES/TerminalConsoleOn.nif', 'TerminalConsoleOn.nif')
    analyze_nif('c:/Users/owenc/Desktop/Fallout 4 To Bo3/EXAMPLES/OutfitF.nif', 'OutfitF.nif')
