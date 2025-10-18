# Model2Bo3 Repository Structure

**GitHub Repository:** https://github.com/Owen-C137/Genesis-Model2Bo3-

This repository contains the Model2Bo3 converter application source code and documentation.

## What's Included

```
Fallout 4 To Bo3/
├── README.md              ← Main user documentation
├── FEATURES.md            ← Complete feature list
├── SETTINGS_GUIDE.md      ← Detailed settings reference
├── .gitignore             ← Git exclusions
├── converter/             ← Application source code
│   ├── main.py            ← Entry point
│   ├── run_gui.py         ← GUI launcher
│   ├── setup.py           ← Installation script
│   ├── requirements.txt   ← Python dependencies
│   ├── Model2Bo3.spec     ← PyInstaller build config
│   ├── genesis.ico        ← Application icon
│   ├── genesis_text.png   ← Logo image
│   ├── config/            ← Configuration files
│   │   └── settings.json  ← User settings (not tracked)
│   └── src/               ← Source code modules
│       ├── gui/           ← User interface
│       ├── parsers/       ← File format parsers
│       ├── exporters/     ← Export writers
│       ├── utils/         ← Utility modules
│       └── pynifly/       ← PyNifly library (included)
└── EXAMPLES/              ← Example files (optional)
```

## External Dependencies

### PyNifly (Required - Not Included)

**⚠️ IMPORTANT:** This repository does **NOT** include the PyNifly library. You must download it separately.

**What is PyNifly?**
- Python library for parsing NIF files (Fallout 4, Skyrim, etc.)
- Includes NiflyDLL.dll for native parsing performance
- Part of the NifTools Blender addon project

**How to Install PyNifly:**

**Option 1: Download from GitHub (Recommended)**
1. Visit: https://github.com/niftools/blender_niftools_addon
2. Download latest release or clone repository
3. Copy the entire folder to: `converter/src/pynifly/`
4. Your structure should be:
   ```
   converter/src/pynifly/
   ├── pynifly.py
   ├── niflytools.py
   ├── nifdefs.py
   ├── pynmathutils.py
   ├── xmltools.py
   ├── bgsmaterial.py
   └── NiflyDLL/
       └── x64/
           └── NiflyDLL.dll
   ```

**Option 2: Copy from Blender Addon**
If you have Blender with NifTools addon installed:
1. Find: `[Blender]/scripts/addons/io_scene_nifly/`
2. Copy entire folder to: `converter/src/pynifly/`

**Verify Installation:**
```powershell
# Check if PyNifly is installed
Test-Path "converter\src\pynifly\pynifly.py"
Test-Path "converter\src\pynifly\NiflyDLL\x64\NiflyDLL.dll"
```
Both should return `True`

### io_scene_nifly
The full `io_scene_nifly/` Blender addon folder is not needed. Only the PyNifly components listed above are required.

## Setup for Development

### 1. Clone Repository
```bash
git clone https://github.com/Owen-C137/Genesis-Model2Bo3-.git
cd Genesis-Model2Bo3-
```

### 2. Install PyNifly (Required)
See [External Dependencies](#external-dependencies) section above for detailed instructions.

Quick version:
```bash
# Download PyNifly from https://github.com/niftools/blender_niftools_addon
# Copy to converter/src/pynifly/
```

### 3. Install Python Dependencies
```bash
cd converter
pip install -r requirements.txt
```

### 4. Run from Source
```bash
python run_gui.py
```

### 5. Build Standalone Executable
```bash
pyinstaller Model2Bo3.spec --clean
```

Output: `converter/dist/Model2Bo3.exe`

## What Gets Tracked in Git

✅ **Included:**
- All source code (`converter/src/` - EXCEPT pynifly)
- Documentation (README, FEATURES, SETTINGS_GUIDE, REPO_STRUCTURE)
- Build configuration (Model2Bo3.spec)
- Assets (genesis.ico, genesis_text.png)
- Requirements file (requirements.txt)

❌ **Excluded (User Must Provide):**
- `converter/src/pynifly/` (external library - see setup instructions)
- `EXAMPLES/` (example output files)
- `io_scene_nifly/` (external Blender addon)
- `converter/output/` (user output files)
- `converter/test_output/` (test files)
- `converter/build/` (PyInstaller build artifacts)
- `converter/dist/` (built executables)
- `converter/config/settings.json` (user-specific settings)
- `__pycache__/` (Python bytecode)
- Test scripts (`test_*.py`)
- Output files (`*.XMODEL_EXPORT`, `*.XMODEL_BIN`, `*_materials.json`)

## Building Releases

To create a release build:

1. **Update version info** in source files
2. **Clean build artifacts:**
   ```bash
   cd converter
   Remove-Item build, dist -Recurse -Force -ErrorAction SilentlyContinue
   ```
3. **Build executable:**
   ```bash
   pyinstaller Model2Bo3.spec --clean
   ```
4. **Test the executable:**
   ```bash
   cd dist
   .\Model2Bo3.exe
   ```
5. **Package for distribution:**
   - Include `Model2Bo3.exe`
   - Include documentation (README.md, FEATURES.md, SETTINGS_GUIDE.md)
   - Include example files (optional)

## Contributing

### Before Committing

1. **Test your changes** with `python run_gui.py`
2. **Build executable** to ensure no build errors
3. **Update documentation** if adding features
4. **Don't commit:**
   - Output files (*.XMODEL_EXPORT, *.XMODEL_BIN)
   - Test scripts you created
   - Your personal settings.json
   - Build artifacts (build/, dist/)

### Commit Message Format
```
<type>: <description>

Examples:
feat: Add Skyrim NIF format support
fix: Correct normal map inversion for layered materials
docs: Update SETTINGS_GUIDE with B.A.E extraction steps
build: Update PyInstaller spec for new dependencies
```

## Dependencies

### Python Packages (via pip)
- PyQt6 - GUI framework
- Pillow (PIL) - Image processing
- PyFFI - NIF file parsing (fallback)
- numpy - Numerical operations

### Bundled Libraries
- PyNifly - NIF parsing with Fallout 4 support (in `src/pynifly/`)

### External Tools (Not Included)
- **Bethesda Archive Extractor (B.A.E)** - For extracting FO4 textures
- **export2bin.exe** - BO3 modtools (optional, for BIN compilation)

## License & Credits

**Model2Bo3** - Universal Game Model to Black Ops 3 Converter

**Technologies:**
- PyNifly - NIF file parsing
- PyFFI - Fallback NIF parsing
- PyQt6 - User interface
- Pillow - Image processing

**Game Assets:**
- Fallout 4 © Bethesda Softworks
- Skyrim © Bethesda Softworks
- Call of Duty: Black Ops 3 © Activision

## Support

For issues, feature requests, or questions:
- Check documentation first (README.md, FEATURES.md, SETTINGS_GUIDE.md)
- Review .gitignore if files aren't tracking correctly
- Ensure external dependencies are installed

---

**Note:** This is the source repository structure. End users receive a standalone `Model2Bo3.exe` that includes all necessary components.
