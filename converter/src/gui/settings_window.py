"""
Settings Window for Fallout 4 to Black Ops 3 Converter
Tabbed interface for different file format settings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QCheckBox, QGroupBox,
    QDoubleSpinBox, QSpinBox, QTabWidget, QWidget,
    QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsWindow(QDialog):
    """Settings dialog with tabbed interface for different formats"""
    
    settings_changed = pyqtSignal(dict)  # Emit when settings are saved
    
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()  # Work with a copy
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings UI"""
        self.setWindowTitle("Converter Settings")
        self.setGeometry(200, 200, 700, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Tab widget for different format settings
        self.tabs = QTabWidget()
        
        # Fallout 4 settings tab
        self.fallout4_tab = self.create_fallout4_tab()
        self.tabs.addTab(self.fallout4_tab, "📦 Fallout 4 (NIF/HKX)")
        
        # General settings tab
        self.general_tab = self.create_general_tab()
        self.tabs.addTab(self.general_tab, "⚙️ General")
        
        # Placeholder for future formats
        future_tab = QWidget()
        future_layout = QVBoxLayout()
        future_label = QLabel("🔮 Future format support coming soon!\n\n• OBJ → BO3\n• FBX → BO3\n• And more...")
        future_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        future_label.setStyleSheet("color: #888; font-size: 12pt; padding: 50px;")
        future_layout.addWidget(future_label)
        future_layout.addStretch()
        future_tab.setLayout(future_layout)
        self.tabs.addTab(future_tab, "🚀 Coming Soon")
        
        layout.addWidget(self.tabs)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("💾 Save Settings")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #333;
                color: #ffffff;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0d47a1;
            }
            QTabBar::tab:hover {
                background-color: #444;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
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
            }
            QPushButton:hover {
                background-color: #444;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
        """)
    
    def create_fallout4_tab(self):
        """Create Fallout 4 specific settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Prefix settings
        prefix_group = QGroupBox("Naming Prefixes")
        prefix_layout = QVBoxLayout()
        
        # Material prefix
        material_layout = QHBoxLayout()
        material_label = QLabel("Material Prefix:")
        material_label.setFixedWidth(150)
        material_layout.addWidget(material_label)
        
        self.material_prefix_input = QLineEdit()
        self.material_prefix_input.setPlaceholderText("e.g., zm_asylum_ (optional)")
        self.material_prefix_input.setText(self.config.get('export_options', {}).get('material_prefix', ''))
        material_layout.addWidget(self.material_prefix_input)
        prefix_layout.addLayout(material_layout)
        
        # Filename prefix
        filename_layout = QHBoxLayout()
        filename_label = QLabel("Filename Prefix:")
        filename_label.setFixedWidth(150)
        filename_layout.addWidget(filename_label)
        
        self.filename_prefix_input = QLineEdit()
        self.filename_prefix_input.setPlaceholderText("e.g., zm_asylum_ (optional)")
        self.filename_prefix_input.setText(self.config.get('export_options', {}).get('filename_prefix', ''))
        filename_layout.addWidget(self.filename_prefix_input)
        prefix_layout.addLayout(filename_layout)
        
        prefix_group.setLayout(prefix_layout)
        layout.addWidget(prefix_group)
        
        # Texture path settings
        texture_group = QGroupBox("Texture Auto-Copy")
        texture_layout = QVBoxLayout()
        
        # Texture source path
        texture_path_layout = QHBoxLayout()
        texture_path_label = QLabel("Texture Folder:")
        texture_path_label.setFixedWidth(150)
        texture_path_layout.addWidget(texture_path_label)
        
        self.texture_path_input = QLineEdit()
        self.texture_path_input.setPlaceholderText("Path to Fallout 4 Textures folder (optional)")
        self.texture_path_input.setText(self.config.get('fallout4', {}).get('texture_path', ''))
        texture_path_layout.addWidget(self.texture_path_input)
        
        texture_browse_btn = QPushButton("Browse...")
        texture_browse_btn.setFixedWidth(100)
        texture_browse_btn.clicked.connect(self.browse_texture_path)
        texture_path_layout.addWidget(texture_browse_btn)
        
        texture_layout.addLayout(texture_path_layout)
        
        # Auto-copy checkbox
        self.auto_copy_textures = QCheckBox("Automatically find and copy textures to output folder")
        self.auto_copy_textures.setChecked(self.config.get('fallout4', {}).get('auto_copy_textures', False))
        texture_layout.addWidget(self.auto_copy_textures)
        
        # Auto-convert to PNG checkbox
        self.auto_convert_to_png = QCheckBox("Auto convert copied textures to PNG (converts DDS, TGA, etc.)")
        self.auto_convert_to_png.setChecked(self.config.get('fallout4', {}).get('auto_convert_to_png', False))
        texture_layout.addWidget(self.auto_convert_to_png)
        
        # Auto-invert normals checkbox
        self.auto_invert_normals = QCheckBox("Auto invert normal maps (_n textures) after PNG conversion")
        self.auto_invert_normals.setChecked(self.config.get('fallout4', {}).get('auto_invert_normals', False))
        texture_layout.addWidget(self.auto_invert_normals)
        
        # Info label
        texture_info = QLabel("ℹ️ When enabled, textures will be organized as:\n   output/modelname/materialname/textures.png (or .dds if not converted)\n   Normal maps will be inverted (Ctrl+I) for BO3 compatibility")
        texture_info.setStyleSheet("color: #888; font-size: 9pt; padding: 5px 20px;")
        texture_layout.addWidget(texture_info)
        
        texture_group.setLayout(texture_layout)
        layout.addWidget(texture_group)
        
        # Transform settings
        transform_group = QGroupBox("Transform Settings")
        transform_layout = QVBoxLayout()
        
        # Auto transforms checkbox
        self.use_auto_transforms = QCheckBox("Use automatic scale and rotation detection (recommended)")
        self.use_auto_transforms.setChecked(self.config.get('export_options', {}).get('use_auto_transforms', True))
        self.use_auto_transforms.stateChanged.connect(self.on_auto_transforms_changed)
        transform_layout.addWidget(self.use_auto_transforms)
        
        # Custom scale
        scale_layout = QHBoxLayout()
        scale_label = QLabel("Custom Scale:")
        scale_label.setFixedWidth(150)
        scale_layout.addWidget(scale_label)
        
        self.scale_input = QDoubleSpinBox()
        self.scale_input.setRange(0.01, 10.0)
        self.scale_input.setSingleStep(0.01)
        self.scale_input.setDecimals(3)
        self.scale_input.setValue(self.config.get('export_options', {}).get('custom_scale', 0.472))
        self.scale_input.setEnabled(not self.use_auto_transforms.isChecked())
        scale_layout.addWidget(self.scale_input)
        scale_layout.addStretch()
        transform_layout.addLayout(scale_layout)
        
        # Bone rotation
        bone_rot_label = QLabel("Bone Rotation (degrees):")
        transform_layout.addWidget(bone_rot_label)
        
        bone_rot_layout = QHBoxLayout()
        bone_rot_layout.addSpacing(20)
        
        bone_x_label = QLabel("X:")
        bone_x_label.setFixedWidth(20)
        bone_rot_layout.addWidget(bone_x_label)
        self.bone_rot_x = QSpinBox()
        self.bone_rot_x.setRange(-360, 360)
        self.bone_rot_x.setSingleStep(90)
        self.bone_rot_x.setValue(self.config.get('export_options', {}).get('bone_rotation_x', 0))
        self.bone_rot_x.setEnabled(not self.use_auto_transforms.isChecked())
        bone_rot_layout.addWidget(self.bone_rot_x)
        
        bone_y_label = QLabel("Y:")
        bone_y_label.setFixedWidth(20)
        bone_rot_layout.addWidget(bone_y_label)
        self.bone_rot_y = QSpinBox()
        self.bone_rot_y.setRange(-360, 360)
        self.bone_rot_y.setSingleStep(90)
        self.bone_rot_y.setValue(self.config.get('export_options', {}).get('bone_rotation_y', 90))
        self.bone_rot_y.setEnabled(not self.use_auto_transforms.isChecked())
        bone_rot_layout.addWidget(self.bone_rot_y)
        
        bone_z_label = QLabel("Z:")
        bone_z_label.setFixedWidth(20)
        bone_rot_layout.addWidget(bone_z_label)
        self.bone_rot_z = QSpinBox()
        self.bone_rot_z.setRange(-360, 360)
        self.bone_rot_z.setSingleStep(90)
        self.bone_rot_z.setValue(self.config.get('export_options', {}).get('bone_rotation_z', 90))
        self.bone_rot_z.setEnabled(not self.use_auto_transforms.isChecked())
        bone_rot_layout.addWidget(self.bone_rot_z)
        
        bone_rot_layout.addStretch()
        transform_layout.addLayout(bone_rot_layout)
        
        # Mesh rotation
        mesh_rot_label = QLabel("Mesh Rotation (degrees):")
        transform_layout.addWidget(mesh_rot_label)
        
        mesh_rot_layout = QHBoxLayout()
        mesh_rot_layout.addSpacing(20)
        
        mesh_x_label = QLabel("X:")
        mesh_x_label.setFixedWidth(20)
        mesh_rot_layout.addWidget(mesh_x_label)
        self.mesh_rot_x = QSpinBox()
        self.mesh_rot_x.setRange(-360, 360)
        self.mesh_rot_x.setSingleStep(90)
        self.mesh_rot_x.setValue(self.config.get('export_options', {}).get('mesh_rotation_x', 180))
        self.mesh_rot_x.setEnabled(not self.use_auto_transforms.isChecked())
        mesh_rot_layout.addWidget(self.mesh_rot_x)
        
        mesh_y_label = QLabel("Y:")
        mesh_y_label.setFixedWidth(20)
        mesh_rot_layout.addWidget(mesh_y_label)
        self.mesh_rot_y = QSpinBox()
        self.mesh_rot_y.setRange(-360, 360)
        self.mesh_rot_y.setSingleStep(90)
        self.mesh_rot_y.setValue(self.config.get('export_options', {}).get('mesh_rotation_y', 180))
        self.mesh_rot_y.setEnabled(not self.use_auto_transforms.isChecked())
        mesh_rot_layout.addWidget(self.mesh_rot_y)
        
        mesh_z_label = QLabel("Z:")
        mesh_z_label.setFixedWidth(20)
        mesh_rot_layout.addWidget(mesh_z_label)
        self.mesh_rot_z = QSpinBox()
        self.mesh_rot_z.setRange(-360, 360)
        self.mesh_rot_z.setSingleStep(90)
        self.mesh_rot_z.setValue(self.config.get('export_options', {}).get('mesh_rotation_z', -90))
        self.mesh_rot_z.setEnabled(not self.use_auto_transforms.isChecked())
        mesh_rot_layout.addWidget(self.mesh_rot_z)
        
        mesh_rot_layout.addStretch()
        transform_layout.addLayout(mesh_rot_layout)
        
        transform_group.setLayout(transform_layout)
        layout.addWidget(transform_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Output directory
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Output Directory:")
        dir_label.setFixedWidth(150)
        dir_layout.addWidget(dir_label)
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(self.config.get('output_directory', './output'))
        self.output_dir_input.setReadOnly(True)
        dir_layout.addWidget(self.output_dir_input)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(self.browse_button)
        
        output_layout.addLayout(dir_layout)
        
        # Auto-compile to BIN
        self.auto_compile_checkbox = QCheckBox("Automatically compile EXPORT files to BIN after conversion")
        self.auto_compile_checkbox.setChecked(self.config.get('auto_compile_to_bin', False))
        output_layout.addWidget(self.auto_compile_checkbox)
        
        # Clean EXPORT files after BIN compilation
        self.clean_old_checkbox = QCheckBox("Delete EXPORT files after successful BIN compilation (keeps only .BIN files)")
        self.clean_old_checkbox.setChecked(self.config.get('ui_preferences', {}).get('clean_old_exports', False))
        output_layout.addWidget(self.clean_old_checkbox)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # export2bin path
        export2bin_group = QGroupBox("export2bin.exe Path (for auto-compile)")
        export2bin_layout = QHBoxLayout()
        
        self.export2bin_input = QLineEdit()
        self.export2bin_input.setPlaceholderText("Path to export2bin.exe (optional)")
        self.export2bin_input.setText(self.config.get('export2bin_path', ''))
        export2bin_layout.addWidget(self.export2bin_input)
        
        self.browse_export2bin_button = QPushButton("Browse...")
        self.browse_export2bin_button.clicked.connect(self.browse_export2bin)
        export2bin_layout.addWidget(self.browse_export2bin_button)
        
        export2bin_group.setLayout(export2bin_layout)
        layout.addWidget(export2bin_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def on_auto_transforms_changed(self, state):
        """Enable/disable manual transform controls"""
        is_auto = (state == Qt.CheckState.Checked.value)
        
        self.scale_input.setEnabled(not is_auto)
        self.bone_rot_x.setEnabled(not is_auto)
        self.bone_rot_y.setEnabled(not is_auto)
        self.bone_rot_z.setEnabled(not is_auto)
        self.mesh_rot_x.setEnabled(not is_auto)
        self.mesh_rot_y.setEnabled(not is_auto)
        self.mesh_rot_z.setEnabled(not is_auto)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)
    
    def browse_export2bin(self):
        """Browse for export2bin.exe"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select export2bin.exe",
            "",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if filepath:
            self.export2bin_input.setText(filepath)
    
    def browse_texture_path(self):
        """Browse for Fallout 4 textures directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Fallout 4 Textures Folder",
            self.texture_path_input.text()
        )
        if directory:
            self.texture_path_input.setText(directory)
    
    def save_settings(self):
        """Save all settings to config"""
        # Export options
        if 'export_options' not in self.config:
            self.config['export_options'] = {}
        
        self.config['export_options']['material_prefix'] = self.material_prefix_input.text()
        self.config['export_options']['filename_prefix'] = self.filename_prefix_input.text()
        self.config['export_options']['use_auto_transforms'] = self.use_auto_transforms.isChecked()
        self.config['export_options']['custom_scale'] = self.scale_input.value()
        self.config['export_options']['bone_rotation_x'] = self.bone_rot_x.value()
        self.config['export_options']['bone_rotation_y'] = self.bone_rot_y.value()
        self.config['export_options']['bone_rotation_z'] = self.bone_rot_z.value()
        self.config['export_options']['mesh_rotation_x'] = self.mesh_rot_x.value()
        self.config['export_options']['mesh_rotation_y'] = self.mesh_rot_y.value()
        self.config['export_options']['mesh_rotation_z'] = self.mesh_rot_z.value()
        
        # Fallout 4 specific settings
        if 'fallout4' not in self.config:
            self.config['fallout4'] = {}
        
        self.config['fallout4']['texture_path'] = self.texture_path_input.text()
        self.config['fallout4']['auto_copy_textures'] = self.auto_copy_textures.isChecked()
        self.config['fallout4']['auto_convert_to_png'] = self.auto_convert_to_png.isChecked()
        self.config['fallout4']['auto_invert_normals'] = self.auto_invert_normals.isChecked()
        
        # UI preferences
        if 'ui_preferences' not in self.config:
            self.config['ui_preferences'] = {}
        
        self.config['ui_preferences']['clean_old_exports'] = self.clean_old_checkbox.isChecked()
        
        # General settings
        self.config['output_directory'] = self.output_dir_input.text()
        self.config['auto_compile_to_bin'] = self.auto_compile_checkbox.isChecked()
        self.config['export2bin_path'] = self.export2bin_input.text()
        
        # Emit signal and close
        self.settings_changed.emit(self.config)
        self.accept()
