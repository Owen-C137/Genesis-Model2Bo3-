"""
Main Window for Model2Bo3 Converter
Clean, minimal interface with settings in separate window
"""

import os
import sys
import io
import contextlib
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QFileDialog, QProgressBar, QTextEdit,
    QGroupBox, QMessageBox, QListWidgetItem, QToolBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QAction, QIcon, QPixmap
from .settings_window import SettingsWindow


class OutputRedirector:
    """Redirects stdout/stderr to a signal"""
    def __init__(self, signal):
        self.signal = signal
        self.buffer = []
        
    def write(self, text):
        if text and text.strip():
            # Send each line immediately
            self.signal.emit(0, 1, text.rstrip())
    
    def flush(self):
        pass


class ConversionWorker(QThread):
    """Background worker for file conversion"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool, str)  # success, message
    file_complete = pyqtSignal(str, bool)  # filename, success
    
    def __init__(self, files: list, output_dir: str, config: dict = None):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.config = config or {}
        self.is_running = True
    
    def run(self):
        """Convert all files"""
        # Redirect stdout/stderr to capture all print statements
        stdout_redirector = OutputRedirector(self.progress)
        stderr_redirector = OutputRedirector(self.progress)
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            sys.stdout = stdout_redirector
            sys.stderr = stderr_redirector
            
            self._run_conversion()
            
        finally:
            # Restore original stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def _run_conversion(self):
        """Actual conversion logic with redirected output"""
        import logging
        
        # Disable PIL debug logging (too verbose)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        
        from ..parsers.nif_parser import NIFParser
        # from ..parsers.hkx_parser import HKXParser  # TODO: Animation support not fully implemented yet
        from ..exporters.xmodel_writer import XModelWriter
        # from ..exporters.xanim_writer import XAnimWriter  # TODO: Animation support not fully implemented yet
        from ..utils.texture_copier import TextureCopier
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        nif_parser = NIFParser()
        # hkx_parser = HKXParser()  # TODO: Animation support not fully implemented yet
        xmodel_writer = XModelWriter()
        # xanim_writer = XAnimWriter()  # TODO: Animation support not fully implemented yet
        
        # Apply prefixes from config
        xmodel_writer.material_prefix = self.config.get('export_options', {}).get('material_prefix', '')
        xmodel_writer.filename_prefix = self.config.get('export_options', {}).get('filename_prefix', '')
        
        # Apply custom transforms if not using auto-detection
        if not self.config.get('export_options', {}).get('use_auto_transforms', True):
            xmodel_writer.auto_scale = self.config.get('export_options', {}).get('custom_scale', 1.0)
            xmodel_writer.auto_rotation_x = self.config.get('export_options', {}).get('bone_rotation_x', 0)
            xmodel_writer.auto_rotation_y = self.config.get('export_options', {}).get('bone_rotation_y', 90)
            xmodel_writer.auto_rotation_z = self.config.get('export_options', {}).get('bone_rotation_z', 90)
            xmodel_writer.mesh_rotation_x = self.config.get('export_options', {}).get('mesh_rotation_x', 180)
            xmodel_writer.mesh_rotation_y = self.config.get('export_options', {}).get('mesh_rotation_y', 180)
            xmodel_writer.mesh_rotation_z = self.config.get('export_options', {}).get('mesh_rotation_z', -90)
        
        success_count = 0
        fail_count = 0
        
        for i, filepath in enumerate(self.files):
            if not self.is_running:
                break
            
            filename = os.path.basename(filepath)
            ext = os.path.splitext(filepath)[1].lower()
            
            self.progress.emit(i, len(self.files), f"Processing: {filename}")
            
            try:
                # Get filename prefix from config
                filename_prefix = self.config.get('export_options', {}).get('filename_prefix', '')
                
                if ext == '.nif':
                    # Parse NIF
                    data = nif_parser.parse(filepath)
                    
                    # Generate output filename
                    base_name = os.path.splitext(filename)[0]
                    if filename_prefix:
                        base_name = filename_prefix + base_name
                    
                    # Extract relative folder structure from the input path
                    # Try to preserve structure after "Meshes/" if it exists
                    relative_subdir = self._extract_relative_path(filepath)
                    
                    # Create output directory preserving structure
                    if relative_subdir:
                        output_subdir = os.path.join(self.output_dir, relative_subdir)
                    else:
                        output_subdir = self.output_dir
                    
                    os.makedirs(output_subdir, exist_ok=True)
                    
                    output_path = os.path.join(output_subdir, f"{base_name}.XMODEL_EXPORT")
                    
                    # Write XMODEL_EXPORT
                    xmodel_writer.write(data, output_path)
                    
                    # Write materials JSON
                    materials_json_path = os.path.join(output_subdir, f"{base_name}_materials.json")
                    xmodel_writer.write_materials_json(data, materials_json_path)
                    
                    # Auto-copy textures if enabled
                    if self.config.get('fallout4', {}).get('auto_copy_textures', False):
                        texture_path = self.config.get('fallout4', {}).get('texture_path', '')
                        if texture_path and os.path.exists(texture_path):
                            self._copy_model_textures(materials_json_path, base_name, texture_path, output_subdir)
                    
                    self.file_complete.emit(filename, True)
                    success_count += 1
                    
                    # Auto-compile to BIN if enabled
                    if self.config.get('auto_compile_to_bin', False):
                        bin_created = self._compile_to_bin(output_path, 'XMODEL')
                        # Clean up EXPORT file if BIN was created and cleanup is enabled
                        if bin_created and self.config.get('ui_preferences', {}).get('clean_old_exports', False):
                            try:
                                os.remove(output_path)
                                self.progress.emit(0, 1, f"  🗑️ Removed {os.path.basename(output_path)}")
                            except Exception as e:
                                self.progress.emit(0, 1, f"  ⚠️ Could not remove EXPORT: {e}")
                    
                elif ext == '.hkx':
                    # HKX animation support - Coming soon!
                    self.file_complete.emit(filename, False)
                    self.progress.emit(i, len(self.files), f"⚠️ Skipped: {filename} - Animation support coming soon!")
                    fail_count += 1
                    continue
                
            except Exception as e:
                self.file_complete.emit(filename, False)
                self.progress.emit(i, len(self.files), f"❌ Error: {filename} - {str(e)}")
                fail_count += 1
        
        # Final message
        if fail_count == 0:
            message = f"✅ Successfully converted {success_count} file(s)!"
        else:
            message = f"⚠️ Converted {success_count} file(s), {fail_count} failed."
        
        self.finished.emit(fail_count == 0, message)
    
    def _compile_to_bin(self, export_path: str, file_type: str) -> bool:
        """
        Compile EXPORT file to BIN format using export2bin.exe
        
        Args:
            export_path: Path to the EXPORT file
            file_type: Either 'XMODEL' or 'XANIM'
            
        Returns:
            True if BIN file was successfully created, False otherwise
        """
        import subprocess
        
        export2bin_path = self.config.get('export2bin_path', '')
        
        if not export2bin_path or not os.path.exists(export2bin_path):
            self.progress.emit(0, 1, f"⚠️ export2bin.exe not found - skipping BIN compilation")
            return False
        
        try:
            # Get the absolute path to the EXPORT file
            export_path = os.path.abspath(export_path)
            export_dir = os.path.dirname(export_path)
            export_filename = os.path.basename(export_path)
            
            # Debug: Show what we're running
            self.progress.emit(0, 1, f"  🔧 Running: export2bin.exe {export_filename} (in {export_dir})")
            
            # Run export2bin.exe from the EXPORT file's directory (so BIN is created there)
            result = subprocess.run(
                [export2bin_path, export_filename],  # Use just the filename, not full path
                cwd=export_dir,  # Run from the EXPORT file's directory
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if BIN file was created
            bin_extension = '.XMODEL_BIN' if file_type == 'XMODEL' else '.XANIM_BIN'
            bin_path = export_path.replace('.XMODEL_EXPORT', bin_extension).replace('.XANIM_EXPORT', bin_extension)
            
            # Debug: Show what we're looking for
            self.progress.emit(0, 1, f"  🔍 Looking for: {bin_path}")
            
            # Also check in the export2bin.exe directory (it might create the file there)
            bin_filename = os.path.basename(bin_path)
            bin_path_in_exe_dir = os.path.join(os.path.dirname(export2bin_path), bin_filename)
            
            # List all files in the output directory to see what was created
            output_dir = os.path.dirname(export_path)
            files_in_dir = [f for f in os.listdir(output_dir) if f.endswith('.XMODEL_BIN') or f.endswith('.XANIM_BIN')]
            if files_in_dir:
                self.progress.emit(0, 1, f"  📁 BIN files in output dir: {', '.join(files_in_dir)}")
            
            if os.path.exists(bin_path):
                # BIN file created in the correct location
                self.progress.emit(0, 1, f"  ✅ Compiled to {os.path.basename(bin_path)}")
                return True
            elif os.path.exists(bin_path_in_exe_dir):
                # BIN file created in export2bin.exe directory, move it to the correct location
                import shutil
                shutil.move(bin_path_in_exe_dir, bin_path)
                self.progress.emit(0, 1, f"  ✅ Compiled to {os.path.basename(bin_path)} (moved from bin directory)")
                return True
            elif result.returncode == 0:
                # export2bin succeeded but file not where we expected
                self.progress.emit(0, 1, f"  ⚠️ export2bin.exe ran but BIN file not found at expected location")
                if result.stdout:
                    self.progress.emit(0, 1, f"     stdout: {result.stdout.strip()}")
                if result.stderr:
                    self.progress.emit(0, 1, f"     stderr: {result.stderr.strip()}")
                return False
            else:
                self.progress.emit(0, 1, f"  ⚠️ export2bin.exe failed (exit code {result.returncode})")
                if result.stdout:
                    self.progress.emit(0, 1, f"     stdout: {result.stdout.strip()}")
                if result.stderr:
                    self.progress.emit(0, 1, f"     stderr: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.progress.emit(0, 1, f"  ⚠️ export2bin.exe timed out")
            return False
        except Exception as e:
            self.progress.emit(0, 1, f"  ⚠️ Compilation error: {str(e)}")
            return False
    
    def _extract_relative_path(self, filepath: str) -> str:
        """
        Extract the relative folder structure from the input file path.
        Tries to find common Fallout 4 folder markers and extract the path after them.
        
        For example:
        - "path/Meshes/Interiors/Vault/Floors/file.nif" → "Interiors/Vault/Floors"
        - "path/Actors/Character/file.nif" → "Actors/Character"
        
        Args:
            filepath: Full path to the input file
            
        Returns:
            Relative folder path, or empty string if no markers found
        """
        # Normalize path separators
        filepath = filepath.replace('\\', '/')
        
        # Common Fallout 4 folder markers to look for
        markers = ['Meshes/', 'meshes/', 'MESHES/']
        
        for marker in markers:
            if marker in filepath:
                # Split on the marker and get everything after it
                parts = filepath.split(marker, 1)
                if len(parts) > 1:
                    # Get the folder part (exclude the filename)
                    relative_path = parts[1]
                    folder_only = os.path.dirname(relative_path)
                    return folder_only.replace('/', os.sep)
        
        # If no marker found, return empty string (files go to root output)
        return ''
    
    def _copy_model_textures(self, materials_json_path: str, model_name: str, texture_base_path: str, output_subdir: str = None):
        """
        Copy textures for a model based on its materials JSON
        
        Args:
            materials_json_path: Path to the materials JSON file
            model_name: Name of the model (for folder structure)
            texture_base_path: Base path to Fallout 4 textures folder
            output_subdir: Output subdirectory (if None, uses self.output_dir)
        """
        from ..utils.texture_copier import TextureCopier
        
        try:
            # Use provided output_subdir or fall back to self.output_dir
            base_output = output_subdir if output_subdir else self.output_dir
            
            # Create texture copier
            copier = TextureCopier(texture_base_path)
            
            # Check if PNG conversion is enabled
            convert_to_png = self.config.get('fallout4', {}).get('auto_convert_to_png', False)
            invert_normals = self.config.get('fallout4', {}).get('auto_invert_normals', False)
            
            # Copy textures (creates textures/material_name/ structure)
            successful, failed = copier.copy_textures_for_model(
                materials_json_path, 
                base_output, 
                model_name,
                convert_to_png=convert_to_png,
                invert_normals=invert_normals
            )
            
            if successful > 0 or failed > 0:
                self.progress.emit(0, 1, f"  📦 Textures: {successful} copied, {failed} failed")
                
        except Exception as e:
            self.progress.emit(0, 1, f"  ⚠️ Texture copy error: {str(e)}")


class DropZoneWidget(QListWidget):
    """Custom list widget that accepts drag and drop"""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: 2px dashed #555;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
        """)
        self.setMinimumHeight(300)
        
        # Add placeholder text
        self.setPlaceholderText("Drag and drop .nif files here...")
    
    def setPlaceholderText(self, text: str):
        """Set placeholder text when list is empty"""
        if self.count() == 0:
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self.addItem(item)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop"""
        files = []
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if os.path.isfile(filepath):
                ext = os.path.splitext(filepath)[1].lower()
                if ext in ['.nif']:  # Only .nif files supported currently
                    files.append(filepath)
        
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    """Main application window - Clean interface"""
    
    def __init__(self):
        super().__init__()
        self.files = []
        self.output_dir = "./output"
        self.worker = None
        self.config = self.load_config()
        
        self.init_ui()
    
    def load_config(self):
        """Load configuration from settings.json"""
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'settings.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Load output directory from config if present
                self.output_dir = config.get('output_directory', './output')
                return config
        except:
            return {}
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Model2Bo3 Converter")
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'genesis.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 900, 700)
        
        # Create toolbar
        self.create_toolbar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title - Image instead of text
        title_image = QLabel()
        # Get path to genesis_text.png (in converter root directory)
        converter_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        image_path = os.path.join(converter_root, 'genesis_text.png')
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Scale image to reasonable size while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
            title_image.setPixmap(scaled_pixmap)
            title_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_image)
        else:
            # Fallback to text if image not found
            title = QLabel("Model2Bo3 Converter")
            title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            print(f"⚠️ genesis_text.png not found at: {image_path}")
        
        # Subtitle
        subtitle = QLabel("Convert game models to Black Ops 3 format")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 11pt; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Drop zone group
        drop_group = QGroupBox("📁 Files to Convert")
        drop_layout = QVBoxLayout()
        
        self.file_list = DropZoneWidget()
        self.file_list.files_dropped.connect(self.add_files)
        drop_layout.addWidget(self.file_list)
        
        # File list controls
        file_controls = QHBoxLayout()
        
        self.add_button = QPushButton("➕ Add Files")
        self.add_button.setMinimumHeight(35)
        self.add_button.clicked.connect(self.browse_files)
        file_controls.addWidget(self.add_button)
        
        self.clear_button = QPushButton("🗑️ Clear All")
        self.clear_button.setMinimumHeight(35)
        self.clear_button.clicked.connect(self.clear_files)
        file_controls.addWidget(self.clear_button)
        
        drop_layout.addLayout(file_controls)
        drop_group.setLayout(drop_layout)
        layout.addWidget(drop_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)
        
        # Status log
        log_group = QGroupBox("📝 Status Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #444;
                border-radius: 3px;
            }
        """)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Convert button
        self.convert_button = QPushButton("🚀 Start Conversion")
        self.convert_button.setMinimumHeight(55)
        self.convert_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                font-size: 15pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        layout.addWidget(self.convert_button)
        
        central_widget.setLayout(layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 11pt;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QLabel {
                color: #ffffff;
            }
            QToolBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #444;
                spacing: 3px;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #444;
            }
        """)
        
        self.log("✅ Ready! Drag and drop files or click 'Add Files' to begin.")
        self.log(f"📂 Output directory: {self.output_dir}")
    
    def create_toolbar(self):
        """Create toolbar with menu options"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # Settings action
        settings_action = QAction("⚙️ Settings", self)
        settings_action.setStatusTip("Open converter settings")
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # Output directory action
        output_action = QAction("📂 Output Directory", self)
        output_action.setStatusTip("Change output directory")
        output_action.triggered.connect(self.browse_output)
        toolbar.addAction(output_action)
        
        toolbar.addSeparator()
        
        # Help action
        help_action = QAction("❓ Help", self)
        help_action.setStatusTip("View documentation")
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
        
        # About action
        about_action = QAction("ℹ️ About", self)
        about_action.setStatusTip("About this converter")
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
    
    def open_settings(self):
        """Open settings window"""
        settings_window = SettingsWindow(self.config, self)
        settings_window.settings_changed.connect(self.on_settings_changed)
        settings_window.exec()
    
    def on_settings_changed(self, new_config: dict):
        """Handle settings changes from settings window"""
        self.config = new_config
        
        # Update output directory if changed
        new_output = new_config.get('output_directory', './output')
        if new_output != self.output_dir:
            self.output_dir = new_output
            self.log(f"📂 Output directory updated: {self.output_dir}")
        
        # Save config
        self.save_config()
        
        self.log("⚙️ Settings saved successfully!")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
<h2>Model2Bo3 Converter</h2>

<h3>Quick Start:</h3>
<ol>
<li>Drag and drop model files into the drop zone</li>
<li>Click "Start Conversion" to convert all files</li>
<li>Find converted files in the output directory</li>
</ol>

<h3>Settings:</h3>
<ul>
<li><b>Fallout 4 Tab:</b> Configure prefixes and source-specific settings</li>
<li><b>General Tab:</b> Set output directory and export2bin.exe path</li>
<li><b>Auto Transforms:</b> Recommended - automatically detects scale and rotation</li>
</ul>

<h3>Supported Files:</h3>
<ul>
<li><b>.nif</b> → .XMODEL_EXPORT → .XMODEL_BIN (3D models)</li>
</ul>

<h3>Coming Soon:</h3>
<ul>
<li><b>.hkx animations</b> - Currently in development</li>
</ul>

<h3>For More Information:</h3>
<p>See README.md in the converter folder</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Help - Converter Guide")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
<h2>Model2Bo3 Converter</h2>
<p><b>Version:</b> 2.0</p>

<p>Converts game models to Black Ops 3 format:</p>
<ul>
<li>.nif models → .XMODEL_EXPORT (Fallout 4, Skyrim, etc.)</li>
<li>.hkx animations → .XANIM_EXPORT (coming soon)</li>
</ul>

<p><b>Features:</b></p>
<ul>
<li>Automatic scale and rotation detection</li>
<li>Batch conversion support</li>
<li>Drag and drop interface</li>
<li>Customizable prefixes and transforms</li>
</ul>

<p><i>Ready for expansion to support OBJ, FBX, and more!</i></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About Converter")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def add_files(self, files: list):
        """Add files to the conversion list"""
        # Clear placeholder if exists
        if self.file_list.count() > 0:
            item = self.file_list.item(0)
            if item.flags() == Qt.ItemFlag.NoItemFlags:
                self.file_list.clear()
        
        for filepath in files:
            if filepath not in self.files:
                self.files.append(filepath)
                filename = os.path.basename(filepath)
                ext = os.path.splitext(filepath)[1].lower()
                icon = "🎮" if ext == '.nif' else "🎬"
                self.file_list.addItem(f"{icon} {filename}")
                self.log(f"Added: {filename}")
        
        self.convert_button.setEnabled(len(self.files) > 0)
    
    def browse_files(self):
        """Open file browser to add files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Fallout 4 NIF Files",
            "",
            "NIF Models (*.nif);;All Files (*.*)"
        )
        if files:
            self.add_files(files)
    
    def clear_files(self):
        """Clear all files from the list"""
        self.files.clear()
        self.file_list.clear()
        self.file_list.setPlaceholderText("Drag and drop .nif files here...")
        self.convert_button.setEnabled(False)
        self.log("🗑️ File list cleared.")
    
    def browse_output(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir
        )
        if directory:
            self.output_dir = directory
            self.config['output_directory'] = directory
            self.save_config()
            self.log(f"📂 Output directory: {directory}")
    
    def save_config(self):
        """Save configuration to settings.json"""
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'settings.json')
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def start_conversion(self):
        """Start the conversion process"""
        if not self.files:
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Disable UI during conversion
        self.convert_button.setEnabled(False)
        self.add_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.log(f"\n🚀 Starting conversion of {len(self.files)} file(s)...")
        
        # Start worker thread
        self.worker = ConversionWorker(self.files, self.output_dir, self.config)
        self.worker.progress.connect(self.update_progress)
        self.worker.file_complete.connect(self.file_completed)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar and status"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        if message:
            self.log(message)
    
    def file_completed(self, filename: str, success: bool):
        """Handle individual file completion"""
        status = "✅" if success else "❌"
        self.log(f"{status} {filename}")
    
    def conversion_finished(self, success: bool, message: str):
        """Handle conversion completion"""
        self.log(f"\n{message}")
        self.log(f"📂 Output location: {self.output_dir}\n")
        
        # Re-enable UI
        self.convert_button.setEnabled(True)
        self.add_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Show completion message
        icon = QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning
        QMessageBox(icon, "Conversion Complete", message, parent=self).exec()
    
    def log(self, message: str):
        """Add message to status log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


def main():
    """Main entry point for the GUI application"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
