import trimesh
import sys
from pathlib import Path


def stl_to_3mf(input_path, output_path=None):
    """
    Convert STL file to 3MF format

    Args:
        input_path: Path to input STL file
        output_path: Path to output 3MF file (optional)
    """
    try:
        input_file = Path(input_path)

        # Create output filename if not provided
        if output_path is None:
            output_path = input_file.parent / f"{input_file.stem}.3mf"

        print(f"Loading STL file: {input_path}")

        # Load the STL file
        mesh = trimesh.load(str(input_path))

        print("Mesh loaded successfully")
        print(f" - Vertices: {len(mesh.vertices)}")
        print(f" - Faces: {len(mesh.faces)}")

        # Export to 3MF
        print(f"Converting to 3MF: {output_path}")
        mesh.export(str(output_path))

        print(f"✓ Successfully converted to: {output_path}")
        return True

    except Exception as e:
        print(f"✗ Error converting file: {e}")
        return False


# Example usage
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use command line argument
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        stl_to_3mf(input_file, output_file)
    else:
        # Or specify directly
        print("Usage: python convert_stl.py <input.stl> [output.3mf]")