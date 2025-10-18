# Model2Bo3 - Complete Feature List

This document details all implemented features in Model2Bo3, organized by category.

## 📥 Input & File Handling

### Multi-File Input Methods
- **Browse Button** - Standard file picker dialog
- **Drag & Drop** - Drop single or multiple NIF files directly into window
- **Batch Processing** - Convert entire folders of models at once
- **File Queue System** - Add multiple files to queue before conversion

### Supported File Formats
- **NIF Files** (Netimmerse/Gamebryo)
  - ✅ Fallout 4 NIF format (full support via PyNifly)
  - ✅ Fallout 4 Layered materials (BGSM/BGEM)
  - 🔄 Skyrim NIF format (planned)
  - 🔄 Fallout 3/NV NIF format (planned)
- **HKX Files** (Havok animations)
  - 🔄 Animation support (coming soon)

### File Validation
- Automatic file type detection
- Format compatibility checking
- Error reporting for invalid files

## 🎨 Material & Texture Processing

### Material Handling
- **Multi-Material Meshes** - Preserves all materials per mesh without splitting
- **Layered Material Separation** - Automatically separates layered materials (e.g., "Material:0", "Material:1")
- **Material Name Cleaning** - Sanitizes material names for BO3 compatibility
- **Material Reassignment** - Maps each face/triangle to correct material index
- **Material JSON Export** - Creates detailed `_materials.json` file with:
  - Original and cleaned material names
  - Texture references with paths
  - Material properties (shader, specular, transparency)
  - Layer information for multi-layer materials

### Texture Discovery & Copying
- **Intelligent Texture Search** - Finds textures in multiple locations:
  1. Same directory as model file
  2. Game-specific texture directories (Fallout 4/Data/Textures/, etc.)
  3. Relative paths from model location
  4. Recursive subdirectory search

- **Texture Cache System** - Builds fast lookup cache of all textures in game directory
- **Smart Texture Matching** - Case-insensitive filename matching
- **Multi-Type Support** - Handles diffuse, normal, specular, glow, and other maps

### Texture Processing Options
- **Auto-Copy Textures** - Automatically copies all referenced textures to output
- **Format Conversion** - Convert DDS/TGA/JPG textures to PNG format
- **Normal Map Inversion** - Automatically inverts green channel of normal maps for BO3 compatibility
- **Organized Output Structure**:
  ```
  output/
    ModelName/
      ModelName.XMODEL_EXPORT
      ModelName_materials.json
      textures/
        material_name_1/
          texture_d.png (diffuse)
          texture_n.png (normal, inverted)
          texture_s.png (specular)
        material_name_2/
          ...
  ```

### BO3 Texture Path Generation
- **Automatic Path Formatting** - Creates BO3-compatible texture paths:
  - `color:_images\\i_modelname_d_c.png` (diffuse)
  - `normal:_images\\i_modelname_n.png` (normal)
- **Prefix Support** - Applies custom prefixes to texture names
- **Naming Convention** - Follows BO3 texture naming standards

## 📐 Geometry & Mesh Processing

### Mesh Data Extraction
- **Full Geometry Support**:
  - Vertex positions (X, Y, Z)
  - Vertex normals
  - UV coordinates (multiple UV sets supported)
  - Vertex colors (if present)
  - Face/triangle indices

### Multi-Part Meshes
- **Mesh Merging** - Combines multiple shape nodes into single model
- **Shape Preservation** - Maintains individual shape data for reference
- **Material-per-Shape** - Each shape can have different material

### Coordinate System Transformation
- **Automatic Transform Detection** - Analyzes skeleton to determine best transforms
- **Manual Transform Override** - Custom scale and rotation settings
- **Dual Transform System**:
  - **Bone Transforms** - Applied to skeleton/bones
  - **Mesh Transforms** - Separate transforms for vertices/normals
- **Default BO3 Alignment** - Automatically converts to BO3 coordinate system

## 🦴 Skeleton & Bone Processing

### Bone System
- **Full Skeleton Export** - Preserves complete bone hierarchy
- **Bone Weights** - Vertex skinning weights (up to 4 bones per vertex)
- **Bone Indices** - Proper bone index mapping
- **Parent-Child Relationships** - Maintains bone hierarchy

### Skeleton Analysis
- **Automatic Scale Detection** - Analyzes model scale vs BO3 standard
- **Rotation Detection** - Determines optimal bone rotation angles
- **Skeleton Validation** - Checks for valid bone structure
- **Transform Preview** - Shows detected transforms before export

### Transform Options
- **Auto-Scale** - Automatically scales model to BO3 standard (default: ~0.472x for FO4)
- **Bone Rotation** - Separate X, Y, Z rotation for bones
- **Mesh Rotation** - Independent X, Y, Z rotation for mesh geometry
- **Manual Override** - Disable auto-detection and set custom values

## 📁 Folder Structure & Organization

### Intelligent Path Preservation
- **Automatic Structure Detection** - Finds "Meshes/" folder in source path
- **Relative Path Extraction** - Preserves folder structure after "Meshes/"
- **Recursive Structure** - Maintains nested folder hierarchies

### Example Structure Preservation
```
Input:
  C:/Games/Fallout4/Data/Meshes/Weapons/LaserRifle/LaserRifle.nif

Output (with preservation):
  output/Weapons/LaserRifle/
    LaserRifle.XMODEL_EXPORT
    LaserRifle_materials.json
    textures/
      laserriflemat/
        textures...
```

### Batch Organization
- **Folder Hierarchy Maintained** - Batch converts preserve source structure
- **Material Folders** - Each material gets its own texture subfolder
- **Clean Output** - Organized, predictable file structure

## ⚙️ Settings & Configuration

### Export Options
- **Material Name Prefix** - Add prefix to all material names (e.g., "zm_asylum_")
- **Filename Prefix** - Add prefix to output filenames
- **Custom Paths** - Set custom texture search paths
- **Auto-Compile to BIN** - Automatically run export2bin.exe after conversion
- **Clean Old Exports** - Remove .XMODEL_EXPORT files after successful BIN compilation

### Transform Settings
- **Use Auto-Transforms** - Enable automatic scale/rotation detection (recommended)
- **Custom Scale** - Manual scale factor (0.01 - 10.0)
- **Custom Bone Rotation** - X, Y, Z rotation in degrees
- **Custom Mesh Rotation** - Separate mesh rotation values

### Texture Settings
- **Texture Base Path** - Fallout 4 Data/Textures folder location
- **Auto-Copy Textures** - Enable/disable automatic texture copying
- **Convert to PNG** - Convert all textures to PNG format
- **Invert Normal Maps** - Auto-invert normal map green channel

### UI Preferences
- **Output Directory** - Default output folder location
- **Export2Bin Path** - Path to BO3 export2bin.exe tool
- **Window Size** - Customizable window dimensions
- **Theme** - Dark theme (default)

### Settings Persistence
- **Auto-Save** - Settings saved automatically on change
- **JSON Config** - Human-readable `config/settings.json` file
- **Per-Format Settings** - Different settings for different game formats
- **Last-Used Paths** - Remembers last input file and output directory

## 🖥️ User Interface

### Main Window
- **Clean Minimal Design** - Focus on conversion workflow
- **Real-Time Preview** - Shows mesh stats before conversion:
  - Number of shapes/meshes
  - Vertex count
  - Triangle count
  - Material count
  - Bone count
- **File List** - Shows all files in queue with status icons
- **Progress Bar** - Real-time conversion progress
- **Console Output** - Live log of conversion process with colored status messages

### Drag & Drop
- **Visual Feedback** - Window highlights when dragging files over it
- **Multi-File Drop** - Drop multiple files simultaneously
- **Auto-Queue** - Dropped files automatically added to conversion queue

### Status Indicators
- ✅ Success - Green checkmark
- ❌ Error - Red X
- ⚠️ Warning - Yellow warning
- 🔄 Processing - Blue spinner
- 📦 File icons for different types

### Toolbar & Menus
- **File Menu** - Standard file operations
- **Settings Button** - Quick access to settings dialog
- **About Dialog** - Version and technology information
- **Help System** - Integrated documentation

## 📊 Conversion Output

### XMODEL_EXPORT Format
- **BO3 Version 6** - Latest XMODEL_EXPORT format
- **Complete Geometry** - All vertices, normals, UVs, faces
- **Material Assignments** - Per-face material indices
- **Bone Data** - Full skeleton with weights
- **Proper Formatting** - Correctly formatted for BO3 modtools

### Materials JSON
- **Comprehensive Material Data**:
  ```json
  {
    "export_info": {
      "timestamp": "2025-10-18 14:30:00",
      "source_file": "LaserRifle.nif",
      "model_name": "LaserRifle"
    },
    "model_stats": {
      "num_materials": 2,
      "num_bones": 15,
      "num_vertices": 2450,
      "num_triangles": 4200
    },
    "materials": [
      {
        "index": 0,
        "name": {
          "original": "LaserRifleMaterial:0",
          "cleaned": "laserriflematerial_layer0",
          "final": "zm_asylum_laserriflematerial_layer0"
        },
        "shader": "Phong",
        "textures": [
          {
            "type": "diffuse",
            "filename": "LaserRifle_d.dds",
            "bo3_path": "color:_images\\\\i_zm_asylum_laserrifle_d_c.png"
          }
        ]
      }
    ]
  }
  ```

### Export Statistics
- **Conversion Summary** - Success/fail counts
- **Processing Time** - Time taken for each file
- **File Sizes** - Output file sizes
- **Texture Counts** - Number of textures found/copied

## 🔧 Advanced Features

### Layered Material Processing
- **Layer Detection** - Identifies multi-layer materials in NIF
- **Layer Separation** - Splits "Material:0", "Material:1" into separate materials
- **Layer Naming** - Appends "_layer0", "_layer1" to material names
- **Face Reassignment** - Correctly assigns triangles to separated layers
- **Maintains Layer Count** - Preserves exact number of layers from source

### Error Handling & Recovery
- **Graceful Failures** - Continues batch processing even if one file fails
- **Detailed Error Messages** - Clear explanations of what went wrong
- **Error Logging** - Console shows full error context
- **Partial Success** - Can complete conversion even with missing textures

### Performance Optimization
- **Texture Cache** - Fast texture lookups after initial scan
- **Background Processing** - UI remains responsive during conversion
- **Thread Safety** - Proper handling of concurrent operations
- **Memory Management** - Efficient handling of large models

## 🚀 Workflow Features

### Batch Conversion
- **Folder Conversion** - Convert entire folders with one click
- **Queue Management** - Add/remove files from queue
- **Progress Tracking** - Per-file progress indicators
- **Summary Statistics** - Overall batch statistics

### Output Management
- **Organized Structure** - Logical folder organization
- **No Overwrites (Optional)** - Warn before overwriting files
- **Clean Output** - Option to remove intermediate files
- **Export2Bin Integration** - Directly compile to BIN format

### Quality Control
- **Preview Before Convert** - See model stats first
- **Validation Checks** - Verify output files created correctly
- **Texture Verification** - Check which textures found/missing
- **Material Review** - Inspect materials JSON before use

## 📝 Documentation & Help

### Integrated Help
- **Tooltips** - Hover help for all controls
- **Status Messages** - Real-time feedback on actions
- **Error Explanations** - Detailed error messages with solutions
- **About Dialog** - Version info and credits

### External Documentation
- **README.md** - Complete user guide
- **FEATURES.md** - This document
- **Settings Documentation** - Full settings reference
- **Workflow Examples** - Step-by-step tutorials

## 🔄 Future Features (Planned)

### Additional Game Support
- 🔄 Skyrim NIF format
- 🔄 Fallout 3/New Vegas NIF format
- 🔄 Oblivion NIF format
- 🔄 OBJ file format
- 🔄 FBX file format

### Animation Support
- 🔄 HKX animation parsing
- 🔄 XANIM_EXPORT generation
- 🔄 Animation timeline preview
- 🔄 Keyframe editing

### Advanced Features
- 🔄 LOD generation
- 🔄 Collision mesh export
- 🔄 Material editor
- 🔄 Texture preview
- 🔄 Model preview/renderer
- 🔄 Batch texture editing

### Integration
- 🔄 Direct BO3 modtools integration
- 🔄 Asset Manager plugin
- 🔄 APE tool integration
- 🔄 Custom scripts support

---

## Legend
- ✅ Fully implemented and tested
- 🔄 Planned for future release
- ⚠️ Experimental/beta feature

**Last Updated:** October 18, 2025  
**Version:** Current Release
