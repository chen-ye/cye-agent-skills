#!/data/data/com.termux/files/usr/bin/python
import subprocess
import concurrent.futures
import sys
import shutil

def get_aapt_path():
    """Finds the aapt executable."""
    return shutil.which("aapt")

def get_label(package_name):
    """Retrieves the friendly application label for a given package name."""
    try:
        # 1. Get the APK path
        # Using 'cmd package path' is generally more reliable on newer Android versions
        path_cmd = ["cmd", "package", "path", package_name]
        # Run command, capture output, suppress errors
        path_proc = subprocess.run(path_cmd, capture_output=True, text=True, check=True)
        path_output = path_proc.stdout.strip()
        
        if not path_output:
            return package_name, "Unknown (No Path)"

        # Output format is "package:/data/app/..."
        # We need to handle cases where there might be multiple paths (split APKs), taking the first/base one usually works
        path = path_output.splitlines()[0].replace("package:", "").strip()
        
        # 2. Use aapt to dump badging and grep for label
        # We invoke via shell for the pipe to grep, or we could parse in python. 
        # Python parsing is safer against shell injection, though package names are generally safe.
        aapt = get_aapt_path()
        if not aapt:
            return package_name, "Error: aapt not found"

        aapt_proc = subprocess.run([aapt, "dump", "badging", path], capture_output=True, text=True, errors='ignore')
        
        if aapt_proc.returncode != 0:
             return package_name, "Unknown (aapt failed)"

        for line in aapt_proc.stdout.splitlines():
            if line.startswith("application-label:"):
                # Format: application-label:'Friendly Name'
                # Extract content inside single quotes
                label = line.split(":", 1)[1].strip().strip("'")
                return package_name, label
        
        return package_name, package_name # Fallback to ID if label not found

    except subprocess.CalledProcessError:
        return package_name, "Unknown (Command Error)"
    except Exception as e:
        return package_name, f"Error: {str(e)}"

def main():
    if not get_aapt_path():
        print("Error: 'aapt' is not installed. Please run 'pkg install aapt' first.")
        sys.exit(1)

    try:
        # Get list of third-party packages
        list_cmd = ["cmd", "package", "list", "packages", "-3"]
        proc = subprocess.run(list_cmd, capture_output=True, text=True, check=True)
        packages = [line.replace("package:", "").strip() for line in proc.stdout.splitlines() if line.strip()]
        
        if not packages:
            print("No third-party packages found.")
            return

        print(f"Analyzing {len(packages)} packages...")

        # Run in parallel
        # Adjust max_workers based on device capabilities, 10 is usually a safe balance for IO
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(get_label, packages)

        # Print results in a clean format: "Friendly Name (package.id)"
        # Sorting by Friendly Name for readability
        sorted_results = sorted(list(results), key=lambda x: x[1].lower())
        
        for pkg, label in sorted_results:
             print(f"{label} ({pkg})")

    except subprocess.CalledProcessError as e:
        print(f"Failed to list packages: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
