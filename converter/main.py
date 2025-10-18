"""
Fallout 4 to Black Ops 3 Converter
Main entry point for the application

Usage:
    GUI Mode (default):
        python main.py
    
    CLI Mode:
        python main.py --input "path/to/file.nif" --output "output/folder"
        python main.py --batch "folder/with/nifs" --output "output/folder"
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def cli_mode(input_path: str, output_dir: str, batch: bool = False):
    """Run converter in command-line mode"""
    from src.parsers.nif_parser import NIFParser
    from src.parsers.hkx_parser import HKXParser
    from src.exporters.xmodel_writer import XModelWriter
    from src.exporters.xanim_writer import XAnimWriter
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect files
    files = []
    if batch:
        # Batch mode - process all files in directory
        for ext in ['*.nif', '*.hkx']:
            files.extend(Path(input_path).glob(ext))
    else:
        # Single file mode
        files = [Path(input_path)]
    
    if not files:
        print("❌ No files found to convert!")
        return 1
    
    print(f"🔄 Converting {len(files)} file(s)...\n")
    
    nif_parser = NIFParser()
    hkx_parser = HKXParser()
    xmodel_writer = XModelWriter()
    xanim_writer = XAnimWriter()
    
    success_count = 0
    
    for filepath in files:
        try:
            ext = filepath.suffix.lower()
            base_name = filepath.stem
            
            print(f"Processing: {filepath.name}")
            
            if ext == '.nif':
                # Convert NIF to XMODEL_EXPORT
                nif_data = nif_parser.parse(str(filepath))
                output_path = os.path.join(output_dir, f"{base_name}.XMODEL_EXPORT")
                
                if xmodel_writer.write(nif_data, output_path):
                    success_count += 1
                    print(f"  ✓ Exported to: {output_path}\n")
                else:
                    print(f"  ✗ Failed to export\n")
                    
            elif ext == '.hkx':
                # Convert HKX to XANIM_EXPORT
                hkx_data = hkx_parser.parse(str(filepath))
                output_path = os.path.join(output_dir, f"{base_name}.XANIM_EXPORT")
                
                if xanim_writer.write(hkx_data, output_path):
                    success_count += 1
                    print(f"  ✓ Exported to: {output_path}\n")
                else:
                    print(f"  ✗ Failed to export\n")
            else:
                print(f"  ⚠ Unsupported file type: {ext}\n")
                
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
    
    print(f"\n{'='*50}")
    print(f"✓ Conversion complete!")
    print(f"  Success: {success_count}/{len(files)} files")
    print(f"  Output: {output_dir}")
    print(f"{'='*50}")
    
    return 0 if success_count > 0 else 1


def gui_mode():
    """Run converter in GUI mode"""
    from PyQt6.QtWidgets import QApplication
    from src.gui.main_window import MainWindow
    
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Fallout 4 to Black Ops 3 Converter")
    app.setOrganizationName("FO4toBO3")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert Fallout 4 models and animations to Black Ops 3 formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch GUI (default)
  python main.py
  
  # Convert single file via CLI
  python main.py --input "model.nif" --output "output/"
  
  # Convert all files in a folder
  python main.py --batch "C:/FO4/Meshes/Weapons" --output "output/"
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input file path (.nif or .hkx)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./output',
        help='Output directory path (default: ./output)'
    )
    
    parser.add_argument(
        '--batch', '-b',
        type=str,
        help='Batch mode: convert all files in specified directory'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Force GUI mode (default if no CLI arguments)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.input or args.batch:
        # CLI mode
        if args.batch:
            return cli_mode(args.batch, args.output, batch=True)
        else:
            return cli_mode(args.input, args.output, batch=False)
    else:
        # GUI mode (default)
        return gui_mode()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
