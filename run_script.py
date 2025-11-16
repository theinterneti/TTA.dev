import asyncio
import importlib.util
import os
import sys

import toml


def setup_monorepo_path():
    """
    Reads the pyproject.toml to configure the PYTHONPATH for the monorepo.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    try:
        with open(pyproject_path) as f:
            pyproject_data = toml.load(f)

        workspace_members = (
            pyproject_data.get("tool", {})
            .get("uv", {})
            .get("workspace", {})
            .get("members", [])
        )

        for member in workspace_members:
            # For a 'src' layout, the 'src' directory itself should be on the path.
            package_src_path = os.path.join(project_root, member, "src")
            if os.path.isdir(package_src_path):
                if package_src_path not in sys.path:
                    sys.path.insert(0, package_src_path)
            # For non-src layouts, add the package directory itself.
            else:
                package_path = os.path.join(project_root, member)
                if os.path.isdir(package_path) and package_path not in sys.path:
                    sys.path.insert(0, package_path)

    except FileNotFoundError:
        print(
            f"Warning: pyproject.toml not found at {pyproject_path}. Path setup may be incomplete."
        )
    except Exception as e:
        print(f"Warning: Error processing pyproject.toml: {e}")


def main():
    """
    A wrapper to run scripts from the project root, ensuring correct path setup.
    """
    if len(sys.argv) < 2:
        print("Usage: python run_script.py <path_to_script>")
        sys.exit(1)

    script_path = sys.argv[1]

    # Configure the path for the monorepo
    setup_monorepo_path()

    try:
        # Dynamically import and run the script's main function
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        if spec is None:
            print(f"Error: Could not load script from {script_path}")
            sys.exit(1)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "main") and asyncio.iscoroutinefunction(module.main):
            asyncio.run(module.main())
        elif hasattr(module, "main"):
            module.main()
        else:
            print(f"Error: No main() function found in {script_path}")

    except FileNotFoundError:
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while running the script: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
