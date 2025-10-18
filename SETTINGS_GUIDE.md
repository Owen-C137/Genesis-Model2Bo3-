# Model2Bo3 - Complete Settings Guide

This guide provides detailed information about every setting in Model2Bo3, how they work, and when to use them.

## Table of Contents
- [Accessing Settings](#accessing-settings)
- [Settings File Structure](#settings-file-structure)
- [Fallout 4 Settings](#fallout-4-settings)
- [General Settings](#general-settings)
- [Export Options](#export-options)
- [UI Preferences](#ui-preferences)
- [Advanced Configuration](#advanced-configuration)

---

## Accessing Settings

### Via GUI
1. Launch Model2Bo3.exe
2. Click the **⚙️ Settings** button in toolbar
3. Navigate through tabs:
   - **📦 Fallout 4 (NIF/HKX)** - Format-specific settings
   - **⚙️ General** - Application-wide settings
   - **🚀 Coming Soon** - Placeholder for future formats

### Via Settings File
Settings are stored in `config/settings.json` and can be edited directly:
1. Close Model2Bo3.exe
2. Open `config/settings.json` in text editor
3. Edit values (see format below)
4. Save and restart application

**⚠️ Important:** Always close the application before editing settings.json manually to avoid conflicts.

---

## Settings File Structure

The `config/settings.json` file is organized into sections:

```json
{
  "fallout4": {
    "texture_path": "C:/Games/Fallout4/Data/Textures",
    "auto_copy_textures": false,
    "auto_convert_to_png": false,
    "auto_invert_normals": false
  },
  "export_options": {
    "material_prefix": "",
    "filename_prefix": "",
    "use_auto_transforms": true,
    "custom_scale": 0.472,
    "bone_rotation_x": 0,
    "bone_rotation_y": 90,
    "bone_rotation_z": 90,
    "mesh_rotation_x": 180,
    "mesh_rotation_y": 180,
    "mesh_rotation_z": -90
  },
  "general": {
    "output_directory": "",
    "export2bin_path": "",
    "auto_compile_to_bin": false
  },
  "ui_preferences": {
    "window_width": 1000,
    "window_height": 700,
    "theme": "dark",
    "clean_old_exports": false
  }
}
```

---

## Fallout 4 Settings

Settings specific to Fallout 4 NIF file conversion.

### Texture Path

**Setting Name:** `texture_path`  
**Type:** String (file path)  
**Default:** Empty  
**Location:** Fallout 4 tab → "Texture Folder"

**Description:**  
Path to your **extracted** Fallout 4 textures folder. Textures must be extracted from Fallout 4's BA2 archives using **Bethesda Archive Extractor (B.A.E)** before Model2Bo3 can find them.

**⚠️ IMPORTANT:** Fallout 4 stores textures in compressed BA2 archive files, not as loose files. You **must** extract them first using B.A.E or similar tools.

**How to Extract Textures:**
1. Download **Bethesda Archive Extractor (B.A.E)** from Nexus Mods
2. Open B.A.E and navigate to Fallout 4's Data folder
3. Extract all texture archives (Textures - Main.ba2, etc.)
4. Choose extraction location (e.g., `C:/FO4_Extracted/Textures`)
5. Point Model2Bo3 to the extracted Textures folder

**Typical Values (Extracted Textures):**
- `C:/FO4_Extracted/Textures` (recommended - separate extraction folder)
- `D:/Modding/FO4_Textures/Textures`
- `C:/Users/YourName/Desktop/FO4_Textures/Textures`

**NOT These (Game Installation Paths - Won't Work):**
- ❌ `C:/Games/Fallout4/Data/Textures` (only contains BA2 archives)
- ❌ `D:/SteamLibrary/steamapps/common/Fallout 4/Data/Textures`
- ❌ Game installation folders (textures are compressed in BA2 files)

**How It Works:**
1. Model2Bo3 scans this entire folder recursively
2. Builds a cache of all texture files (DDS, PNG, TGA, etc.)
3. When a NIF references a texture, looks it up in cache
4. Copies found textures to output (if auto-copy enabled)

**When to Use:**
- ✅ Enable when you want automatic texture copying
- ✅ Set to your Fallout 4 installation texture folder
- ❌ Leave empty if textures are in same folder as NIF

**Performance Note:**  
First scan of texture folder may take 30-60 seconds depending on size. Cache is reused for subsequent conversions in same session.

---

### Auto-Copy Textures

**Setting Name:** `auto_copy_textures`  
**Type:** Boolean  
**Default:** `false`  
**Location:** Fallout 4 tab → "Automatically find and copy textures to output folder"

**Description:**  
When enabled, Model2Bo3 automatically searches for and copies all textures referenced in the NIF file to the output directory.

**How It Works:**
1. Parses NIF file for texture references
2. Searches for each texture in:
   - Same directory as NIF
   - Configured texture path
   - Texture cache
3. Copies found textures to organized output structure:
   ```
   output/
     ModelName/
       textures/
         material_name/
           texture_d.dds
           texture_n.dds
           texture_s.dds
   ```

**Dependencies:**
- Requires `texture_path` to be set for best results
- Works with `auto_convert_to_png` setting
- Works with `auto_invert_normals` setting

**When to Use:**
- ✅ Creating complete model packages for distribution
- ✅ Working with models that reference scattered textures
- ✅ Batch converting entire model libraries
- ❌ Textures already organized in output location
- ❌ Working with single test models

**Output Structure:**
```
output/
  V111Door01/
    V111Door01.XMODEL_EXPORT
    V111Door01_materials.json
    textures/
      v111door01_layer0/
        v111door01_d.dds
        v111door01_n.dds
        v111door01_s.dds
      v111door01_layer1/
        v111door01_metal_d.dds
        v111door01_metal_n.dds
```

---

### Auto-Convert to PNG

**Setting Name:** `auto_convert_to_png`  
**Type:** Boolean  
**Default:** `false`  
**Location:** Fallout 4 tab → "Auto convert copied textures to PNG"

**Description:**  
Automatically converts all copied textures (DDS, TGA, JPG, etc.) to PNG format after copying.

**How It Works:**
1. Copies texture from source (as DDS, TGA, etc.)
2. Opens with Pillow (PIL) image library
3. Converts to PNG format
4. Saves as PNG in output folder
5. Deletes original DDS/TGA file (optional)

**Supported Input Formats:**
- ✅ DDS (Direct Draw Surface) - Most common in FO4
- ✅ TGA (Targa)
- ✅ JPG/JPEG
- ✅ BMP
- ✅ Already-PNG files (skipped)

**Dependencies:**
- Requires `auto_copy_textures` to be enabled
- Requires Pillow (PIL) library (included in exe)

**When to Use:**
- ✅ BO3 modding tools prefer PNG format
- ✅ Need to edit textures in Photoshop/GIMP
- ✅ Want smaller file sizes (PNG compression)
- ✅ Preparing textures for web/preview
- ❌ Working directly with BO3 (can use DDS)
- ❌ Want to preserve original format

**Quality Considerations:**
- **Lossless conversion** - No quality loss from DDS to PNG
- **RGB/RGBA preserved** - Alpha channels maintained
- **Mipmaps discarded** - Only base level texture converted
- **File size varies** - PNG may be larger or smaller than DDS

**Example Output:**
```
Before:
  textures/material/texture_d.dds (2.8 MB)
  textures/material/texture_n.dds (2.8 MB)

After (with conversion):
  textures/material/texture_d.png (1.2 MB)
  textures/material/texture_n.png (1.5 MB)
```

---

### Auto-Invert Normals

**Setting Name:** `auto_invert_normals`  
**Type:** Boolean  
**Default:** `false`  
**Location:** Fallout 4 tab → "Auto invert normal maps after PNG conversion"

**Description:**  
Automatically inverts normal map textures to fix Y-axis (green channel) direction for Black Ops 3 compatibility.

**Technical Background:**  
Different engines use different normal map standards:
- **Fallout 4:** Y+ (green = up) - DirectX standard
- **Black Ops 3:** Y- (green = down) - OpenGL standard
- **Result:** Normal maps appear "inverted" or lighting looks wrong

**How It Works:**
1. Identifies normal map textures by:
   - Texture type in materials JSON
   - Filename patterns: `_n.`, `_normal.`, `_nrm.`
2. Opens PNG with Pillow
3. Inverts entire image (like Photoshop Ctrl+I)
4. Saves inverted PNG back to disk

**Dependencies:**
- Requires `auto_copy_textures` enabled
- Requires `auto_convert_to_png` enabled (only works on PNG)
- Requires Pillow (PIL) library

**When to Use:**
- ✅ Converting Fallout 4 models to BO3
- ✅ Normal maps show incorrect lighting in BO3
- ✅ Want automatic workflow without Photoshop
- ❌ Normal maps already in correct format
- ❌ Not converting to PNG (works only on PNG)

**Visual Effect:**
```
Before Inversion (FO4):
  - Bumps appear as dents
  - Lighting incorrect in BO3
  - Green channel points "up"

After Inversion (BO3):
  - Bumps appear correctly
  - Lighting matches BO3 engine
  - Green channel points "down"
```

**Technical Details:**
- Inverts all RGB channels equally
- Preserves alpha channel (if present)
- Safe for all image types (but targets normal maps)
- Irreversible (original overwritten)

---

## Export Options

Settings that control model export format and transformations.

### Material Prefix

**Setting Name:** `material_prefix`  
**Type:** String  
**Default:** Empty  
**Location:** Fallout 4 tab → "Material Prefix"

**Description:**  
Adds a prefix to all exported material names. Useful for organizing materials in BO3 or avoiding name conflicts.

**How It Works:**
1. Original material name: `DoorMetal`
2. Cleaned name: `doormetal`
3. With prefix `zm_asylum_`: `zm_asylum_doormetal`
4. Applied to:
   - Material names in XMODEL_EXPORT
   - Material names in materials JSON
   - Texture paths in BO3 format

**Common Use Cases:**

**Map Prefixes:**
```
zm_asylum_     → Zombie map "Asylum"
mp_city_       → Multiplayer map "City"
cp_training_   → Campaign "Training"
```

**Category Prefixes:**
```
weapon_        → Weapon models
character_     → Character models
prop_          → Static props
fx_            → Effect models
```

**Format:**
- Use lowercase and underscores
- End with underscore (e.g., `zm_map_`)
- Avoid spaces and special characters
- Keep short for readability

**Example Output:**
```json
{
  "materials": [
    {
      "name": {
        "original": "V111Door01",
        "cleaned": "v111door01",
        "final": "zm_asylum_v111door01"
      },
      "textures": [
        {
          "bo3_path": "color:_images\\\\i_zm_asylum_v111door01_d_c.png"
        }
      ]
    }
  ]
}
```

---

### Filename Prefix

**Setting Name:** `filename_prefix`  
**Type:** String  
**Default:** Empty  
**Location:** Fallout 4 tab → "Filename Prefix"

**Description:**  
Adds a prefix to all exported filenames (XMODEL_EXPORT and materials JSON).

**How It Works:**
1. Original filename: `DoorRusty.nif`
2. With prefix `zm_asylum_`: `zm_asylum_DoorRusty.XMODEL_EXPORT`
3. Also applies to materials JSON: `zm_asylum_DoorRusty_materials.json`

**Difference from Material Prefix:**
- **Filename Prefix:** Changes output file names
- **Material Prefix:** Changes material names inside files

**When to Use:**
- ✅ Organizing multiple map assets
- ✅ Batch converting with consistent naming
- ✅ Avoiding filename conflicts
- ❌ Single model conversions
- ❌ When file names already organized

**Example:**
```
Input Files:
  Door01.nif
  Door02.nif
  Window01.nif

With Prefix "zm_asylum_":
  zm_asylum_Door01.XMODEL_EXPORT
  zm_asylum_Door01_materials.json
  zm_asylum_Door02.XMODEL_EXPORT
  zm_asylum_Door02_materials.json
  zm_asylum_Window01.XMODEL_EXPORT
  zm_asylum_Window01_materials.json
```

---

### Use Auto-Transforms

**Setting Name:** `use_auto_transforms`  
**Type:** Boolean  
**Default:** `true`  
**Location:** Fallout 4 tab → "Use automatic scale and rotation detection (recommended)"

**Description:**  
Enables automatic detection and application of scale and rotation transforms to align model from source game coordinate system to Black Ops 3 coordinate system.

**How It Works:**
1. Analyzes model skeleton and bones
2. Calculates bounding box and scale
3. Determines axis orientation
4. Applies optimal transforms:
   - **Scale:** ~0.472x for Fallout 4 (to match BO3 unit scale)
   - **Bone Rotation:** X=0°, Y=90°, Z=90° (typical for FO4)
   - **Mesh Rotation:** X=180°, Y=180°, Z=-90° (coordinate conversion)

**Why It's Needed:**
Different game engines use different coordinate systems:

| Game | Up Axis | Forward Axis | Right Axis | Units |
|------|---------|--------------|------------|-------|
| Fallout 4 | Z | Y | X | ~70 units per meter |
| Black Ops 3 | Z | X | Y | ~40 units per meter |

**What Auto-Transform Does:**
- ✅ Scales model to BO3 size standard
- ✅ Rotates skeleton to align bones correctly
- ✅ Rotates mesh geometry separately for proper orientation
- ✅ Maintains bone weights and hierarchy
- ✅ Preserves UV coordinates

**When to Enable (Recommended):**
- ✅ Converting from any game to BO3
- ✅ First time converting a model
- ✅ Default for all conversions
- ✅ Model appears too large/small in BO3
- ✅ Model appears rotated incorrectly

**When to Disable:**
- ❌ Model already correctly sized/rotated
- ❌ Applying custom transforms for special cases
- ❌ Troubleshooting transform issues
- ❌ Working with pre-converted models

**Console Output Example:**
```
=== Analyzing Skeleton ===
  Detected coordinate system: Fallout 4 (Z-up)
  Model bounds: 200.5 units (FO4 scale)
  Target bounds: 95.2 units (BO3 scale)
  Auto-transform applied:
    Scale: 0.472x (BO3 standard)
    Bone rotation: X=0°, Y=90°, Z=90°
    Mesh rotation: X=180°, Y=180°, Z=-90°
```

---

### Custom Scale

**Setting Name:** `custom_scale`  
**Type:** Float (0.01 - 10.0)  
**Default:** `0.472`  
**Location:** Fallout 4 tab → "Custom Scale"

**Description:**  
Manual scale factor applied to model when auto-transforms are disabled.

**Enabled When:**  
Only active when "Use Auto-Transforms" is **unchecked**.

**How It Works:**
1. Multiplies all vertex positions by scale factor
2. Multiplies all bone positions by scale factor
3. Does not affect UV coordinates or normals

**Common Scale Values:**

| Source Game | Typical Scale | Notes |
|-------------|---------------|-------|
| Fallout 4 | 0.472 | Default FO4 to BO3 |
| Skyrim | 0.571 | Approximate |
| 1:1 Export | 1.0 | No scaling |
| Test/Debug | 0.1 - 2.0 | Experimentation |

**How to Determine Correct Scale:**
1. Export model with scale 1.0
2. Import to BO3 and measure in modtools
3. Calculate: `desired_size / actual_size`
4. Update custom scale setting

**Example:**
```
Model too large in BO3:
  Current scale: 1.0
  Current height: 200 units
  Desired height: 95 units
  New scale: 95 / 200 = 0.475
```

**⚠️ Important:**
- Scale affects both geometry AND skeleton
- Too small scale (<0.1) may cause precision issues
- Too large scale (>5.0) may exceed BO3 limits

---

### Bone Rotation

**Setting Names:** `bone_rotation_x`, `bone_rotation_y`, `bone_rotation_z`  
**Type:** Integer (degrees, -360 to 360)  
**Defaults:** X=0°, Y=90°, Z=90°  
**Location:** Fallout 4 tab → "Bone Rotation (degrees)"

**Description:**  
Manual rotation applied to skeleton bones when auto-transforms are disabled. Rotates bones around their parent's coordinate system.

**Enabled When:**  
Only active when "Use Auto-Transforms" is **unchecked**.

**How It Works:**
1. Rotates each bone's local transform
2. Applies rotations in order: X → Y → Z (Euler angles)
3. Maintains parent-child relationships
4. Affects bone positions and orientations

**Why Separate from Mesh Rotation:**  
Bones and mesh geometry may need different rotations to align correctly with BO3's coordinate system while maintaining proper skeletal structure.

**Common Rotation Combinations:**

| Source | X | Y | Z | Notes |
|--------|---|---|---|-------|
| Fallout 4 | 0 | 90 | 90 | Standard FO4 |
| Skyrim | 0 | 90 | 0 | Approximate |
| No Rotation | 0 | 0 | 0 | Test/debug |
| 180° Flip | 180 | 0 | 0 | Upside-down fix |

**Step Values:**  
Use 90° increments for axis-aligned rotations (recommended):
- 0°, 90°, 180°, 270°, -90°, -180°, -270°

**Troubleshooting:**

**Skeleton appears twisted:**
- Try 0°, 0°, 0° first
- Add 90° rotations one axis at a time

**Bones point wrong direction:**
- Adjust Y rotation (±90°)
- Check Z rotation (±90°)

**Arms/legs reversed:**
- May need negative rotations
- Try -90° instead of 90°

---

### Mesh Rotation

**Setting Names:** `mesh_rotation_x`, `mesh_rotation_y`, `mesh_rotation_z`  
**Type:** Integer (degrees, -360 to 360)  
**Defaults:** X=180°, Y=180°, Z=-90°  
**Location:** Fallout 4 tab → "Mesh Rotation (degrees)" (in settings file)

**Description:**  
Manual rotation applied to mesh geometry (vertices, normals) when auto-transforms are disabled. Independent from bone rotation.

**Enabled When:**  
Only active when "Use Auto-Transforms" is **unchecked**.

**How It Works:**
1. Rotates all vertex positions around origin
2. Rotates all vertex normals (for lighting)
3. Preserves UV coordinates
4. Applied AFTER bone rotation
5. Does not affect skeleton structure

**Why Separate:**  
The mesh geometry may need to be oriented differently than the skeleton to display correctly in BO3, especially when converting between different coordinate systems.

**Default Values Explained:**
- **X=180°:** Flips model front-to-back
- **Y=180°:** Flips model left-to-right
- **Z=-90°:** Rotates 90° clockwise around vertical axis

Combined effect: Converts Fallout 4 mesh orientation to BO3 standard.

**When to Modify:**

**Model appears upside-down:**
```
Change X from 180° to 0°
```

**Model faces wrong direction:**
```
Adjust Z rotation (try 0°, 90°, 180°, -90°)
```

**Model appears mirrored:**
```
Change Y from 180° to 0°
```

**Normals inverted (black surfaces):**
```
Flip one axis by ±180°
```

**⚠️ Advanced Setting:**  
Most users should keep auto-transforms enabled. Only modify if you understand 3D coordinate systems and transforms.

---

## General Settings

Application-wide settings not specific to any format.

### Output Directory

**Setting Name:** `output_directory`  
**Type:** String (folder path)  
**Default:** Empty (uses `./output` relative to exe)  
**Location:** General tab → "Output Directory"

**Description:**  
Default folder where all converted models and textures will be saved.

**How It Works:**
1. If set, uses this as base output path
2. If empty, uses `output/` folder next to Model2Bo3.exe
3. Creates folder structure inside this directory
4. Preserves relative paths from source (if enabled)

**Typical Values:**
```
C:/BO3_Modding/Converted_Models
D:/Projects/BlackOps3/Assets
C:/Users/YourName/Desktop/BO3_Models
./output (relative to exe)
```

**Folder Structure Created:**
```
[Output Directory]/
  ModelName1/
    ModelName1.XMODEL_EXPORT
    ModelName1_materials.json
    textures/
      ...
  Weapons/           ← Folder structure preserved
    LaserRifle/
      LaserRifle.XMODEL_EXPORT
      ...
```

**When to Change:**
- ✅ Working on specific project
- ✅ Want models on different drive
- ✅ Integrating with existing folder structure
- ❌ Just testing (use default ./output)

---

### Export2Bin Path

**Setting Name:** `export2bin_path`  
**Type:** String (file path)  
**Default:** Empty  
**Location:** General tab → "Export2Bin.exe Path"

**Description:**  
Path to Black Ops 3's `export2bin.exe` tool, which compiles XMODEL_EXPORT files to XMODEL_BIN format for use in game.

**Typical Location:**
```
[BO3 Install]/bin/export2bin.exe

Example:
C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III/bin/export2bin.exe
D:/SteamLibrary/steamapps/common/Call of Duty Black Ops III/bin/export2bin.exe
```

**What export2bin.exe Does:**
- Compiles text XMODEL_EXPORT to binary XMODEL_BIN
- Required for models to load in Black Ops 3
- Part of official BO3 modtools

**When Needed:**
- Required if "Auto-Compile to BIN" is enabled
- Optional otherwise (can compile manually)

**How to Find:**
1. Open Steam
2. Right-click "Call of Duty: Black Ops III"
3. Properties → Installed Files → Browse
4. Navigate to `bin/` folder
5. Copy path to `export2bin.exe`

**⚠️ Note:**  
Must have Black Ops 3 Mod Tools installed for this exe to exist.

---

### Auto-Compile to BIN

**Setting Name:** `auto_compile_to_bin`  
**Type:** Boolean  
**Default:** `false`  
**Location:** General tab → "Auto-compile to BIN after conversion"

**Description:**  
Automatically runs export2bin.exe after XMODEL_EXPORT is created, compiling it to XMODEL_BIN format.

**How It Works:**
1. Model2Bo3 creates XMODEL_EXPORT file
2. Automatically runs: `export2bin.exe ModelName.XMODEL_EXPORT`
3. Creates XMODEL_BIN in same folder
4. Optionally deletes XMODEL_EXPORT (if clean_old_exports enabled)

**Dependencies:**
- Requires `export2bin_path` to be set correctly
- Requires BO3 Mod Tools installed
- Requires valid XMODEL_EXPORT file

**When to Use:**
- ✅ Final production workflow
- ✅ Batch converting many models
- ✅ Want ready-to-use BIN files immediately
- ❌ Debugging XMODEL_EXPORT format
- ❌ Need to manually edit EXPORT files
- ❌ Don't have BO3 Mod Tools installed

**Workflow Comparison:**

**Without Auto-Compile:**
```
1. Run Model2Bo3
2. Get XMODEL_EXPORT files
3. Manually run export2bin for each
4. Get XMODEL_BIN files
```

**With Auto-Compile:**
```
1. Run Model2Bo3
2. Get XMODEL_BIN files directly
   (EXPORT files optional)
```

**Console Output:**
```
✓ Exported to: output/ModelName/ModelName.XMODEL_EXPORT
🔧 Compiling to BIN format...
✓ Created: ModelName.XMODEL_BIN
```

---

## UI Preferences

User interface and experience settings.

### Window Size

**Setting Names:** `window_width`, `window_height`  
**Type:** Integer (pixels)  
**Defaults:** Width=1000, Height=700  
**Location:** Settings file only (not in GUI)

**Description:**  
Size of main application window in pixels.

**How to Change:**
1. Close Model2Bo3.exe
2. Open `config/settings.json`
3. Edit values:
   ```json
   "ui_preferences": {
     "window_width": 1200,
     "window_height": 800
   }
   ```
4. Save and restart

**Recommended Values:**

| Screen Resolution | Width | Height |
|-------------------|-------|--------|
| 1920x1080 (1080p) | 1000 | 700 |
| 2560x1440 (1440p) | 1200 | 800 |
| 3840x2160 (4K) | 1400 | 900 |
| Laptop (Small) | 800 | 600 |

**Minimum Size:**  
- Width: 600px
- Height: 400px

---

### Theme

**Setting Name:** `theme`  
**Type:** String  
**Default:** `"dark"`  
**Location:** Settings file only

**Description:**  
UI color theme. Currently only dark theme implemented.

**Available Values:**
- `"dark"` - Dark theme (current)
- `"light"` - Light theme (future)
- `"system"` - Follow system theme (future)

**Current Dark Theme:**
- Background: #1e1e1e (dark gray)
- Text: #ffffff (white)
- Accents: #0d47a1 (blue)
- Borders: #444444 (medium gray)

---

### Clean Old Exports

**Setting Name:** `clean_old_exports`  
**Type:** Boolean  
**Default:** `false`  
**Location:** Settings file only (not in GUI)

**Description:**  
Automatically deletes XMODEL_EXPORT files after successful compilation to XMODEL_BIN.

**How It Works:**
1. Model2Bo3 creates XMODEL_EXPORT
2. export2bin.exe compiles to XMODEL_BIN
3. If compilation successful AND this setting enabled:
   - Deletes XMODEL_EXPORT file
   - Keeps XMODEL_BIN file

**Dependencies:**
- Requires `auto_compile_to_bin` enabled
- Only deletes if BIN compilation succeeds

**When to Enable:**
- ✅ Only need final BIN files
- ✅ Want cleaner output folders
- ✅ Confident in conversion process
- ❌ Need to debug EXPORT format
- ❌ May need to re-compile with different settings
- ❌ Want to keep source EXPORT files

**Disk Space:**
```
With EXPORT kept:
  ModelName.XMODEL_EXPORT (500 KB)
  ModelName.XMODEL_BIN (650 KB)
  Total: 1150 KB

With EXPORT cleaned:
  ModelName.XMODEL_BIN (650 KB)
  Total: 650 KB
  Savings: 43%
```

---

## Advanced Configuration

### Adding Custom Texture Search Paths

You can add additional texture search directories to settings.json:

```json
{
  "fallout4": {
    "texture_path": "C:/Games/Fallout4/Data/Textures",
    "extra_texture_paths": [
      "C:/BO3_Textures",
      "D:/Modding/Shared_Textures",
      "C:/Users/YourName/Desktop/Project_Textures"
    ]
  }
}
```

Model2Bo3 will search all paths when looking for textures.

---

### Per-Project Settings

Create different settings files for different projects:

1. Copy `config/settings.json` to `config/settings_project1.json`
2. Edit project-specific settings
3. When running conversion, swap settings file
4. Or: Keep multiple Model2Bo3 folders with different configs

**Example Structure:**
```
BO3_Projects/
  ZM_Asylum/
    Model2Bo3.exe
    config/settings.json (zm_asylum_ prefix)
  MP_City/
    Model2Bo3.exe
    config/settings.json (mp_city_ prefix)
```

---

### Backup Settings

Always backup your settings before major changes:

**Windows (PowerShell):**
```powershell
Copy-Item "config\settings.json" "config\settings_backup.json"
```

**Restore:**
```powershell
Copy-Item "config\settings_backup.json" "config\settings.json"
```

---

### Reset to Defaults

To reset all settings to default values:

1. Close Model2Bo3.exe
2. Delete `config/settings.json`
3. Restart Model2Bo3.exe
4. New default settings.json created automatically

---

## Quick Reference Table

| Setting | Default | Impact | Change Frequency |
|---------|---------|--------|------------------|
| texture_path | Empty | High | Once per install |
| auto_copy_textures | false | High | Per project |
| auto_convert_to_png | false | Medium | Per project |
| auto_invert_normals | false | Medium | Per project |
| material_prefix | Empty | Medium | Per map/project |
| filename_prefix | Empty | Low | Per map/project |
| use_auto_transforms | true | Critical | Rarely |
| custom_scale | 0.472 | High | Rarely |
| output_directory | Empty | Low | Per project |
| export2bin_path | Empty | Medium | Once per install |
| auto_compile_to_bin | false | Medium | Per workflow |
| clean_old_exports | false | Low | Per workflow |

---

## Troubleshooting Settings

### Settings Not Saving
- Close application before editing JSON manually
- Check JSON syntax (use JSONLint.com to validate)
- Ensure file isn't read-only

### Textures Not Found
- Verify `texture_path` points to correct folder
- Enable `auto_copy_textures`
- Check console output for texture search results

### Wrong Model Scale
- Enable `use_auto_transforms` for automatic scaling
- If manual: adjust `custom_scale` value
- Test with 1.0 first, then calculate correct scale

### Model Appears Rotated
- Enable `use_auto_transforms` (recommended)
- If manual: adjust bone and mesh rotation values
- Try 90° increments on each axis

### Auto-Compile Fails
- Verify `export2bin_path` is correct
- Check BO3 Mod Tools are installed
- Look for error messages in console

---

**Last Updated:** October 18, 2025  
**Version:** Current Release  
**For:** Model2Bo3 - Universal Game Model to Black Ops 3 Converter
