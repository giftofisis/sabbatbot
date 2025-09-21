# GBPBot - update_versions.py
# Version: 1.0.2
# Last Updated: 2025-09-21
# Notes:
# - Auto-updates version headers in all core GBPBot files
# - Updates version_tracker.py with current versions
# - Auto-increments patch number by default
# - Adds a CHANGE LOG entry in each file when version changes
# - Automatically tracks all .py files in root, cogs/, and utils/

# CHANGE LOG
# -----------------------
# [2025-09-21] v1.0.2
# - Added automatic tracking for utils/ folder
# - Maintains auto CHANGE LOG entries in each file
# - Fully compatible with Railway deploys

import re
import os
from datetime import datetime

# --- CONFIG ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
COGS_DIR = os.path.join(ROOT_DIR, "cogs")      # cogs folder
UTILS_DIR = os.path.join(ROOT_DIR, "utils")    # utils folder
VERSION_HEADER_PATTERN = re.compile(r"(# Version:\s*)([\d\.]+)")
CHANGELOG_PATTERN = re.compile(r"# CHANGE LOG")
VERSION_TRACKER_FILE = "version_tracker.py"

# --- HELPER FUNCTIONS ---
def parse_version(version_str):
    return [int(x) for x in version_str.split(".")]

def bump_patch(version_str):
    parts = parse_version(version_str)
    parts[-1] += 1
    return ".".join(str(x) for x in parts)

def get_file_version(file_path):
    if not os.path.exists(file_path):
        return "0.0.1"
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = VERSION_HEADER_PATTERN.match(line)
            if match:
                return match.group(2)
    return "0.0.1"

def update_file_version(file_path, new_version):
    lines = []
    found = False
    changelog_found = False
    today = datetime.now().strftime("%Y-%m-%d")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if VERSION_HEADER_PATTERN.match(line):
                    lines.append(f"# Version: {new_version}\n")
                    found = True
                elif CHANGELOG_PATTERN.match(line):
                    lines.append(line)
                    lines.append(f"# [{today}] v{new_version} - Auto-updated version\n")
                    changelog_found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.insert(0, f"# Version: {new_version}\n")
    if not changelog_found:
        lines.append("\n# CHANGE LOG\n")
        lines.append(f"# [{today}] v{new_version} - Auto-updated version\n")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def update_version_tracker(versions_dict):
    with open(VERSION_TRACKER_FILE, "w", encoding="utf-8") as f:
        f.write("# GBPBot - version_tracker.py\n")
        f.write("# Auto-generated\n")
        f.write("# Do not edit manually\n\n")
        f.write("VERSIONS = {\n")
        for file, version in versions_dict.items():
            f.write(f'    "{file}": "{version}",\n')
        f.write("}\n")

def discover_files():
    py_files = [f for f in os.listdir(ROOT_DIR) if f.endswith(".py")]
    
    # Add cogs
    if os.path.exists(COGS_DIR):
        for f in os.listdir(COGS_DIR):
            if f.endswith(".py"):
                py_files.append(os.path.join("cogs", f))
    
    # Add utils
    if os.path.exists(UTILS_DIR):
        for f in os.listdir(UTILS_DIR):
            if f.endswith(".py"):
                py_files.append(os.path.join("utils", f))
    
    return py_files

# --- MAIN SCRIPT ---
def main(auto_bump=True):
    files_to_track = discover_files()
    versions = {}
    
    for file in files_to_track:
        current_version = get_file_version(file)
        new_version = bump_patch(current_version) if auto_bump else current_version
        update_file_version(file, new_version)
        versions[file] = new_version
        print(f"{file}: {current_version} -> {new_version}")
    
    # Ensure version_tracker.py is updated last
    versions[VERSION_TRACKER_FILE] = get_file_version(VERSION_TRACKER_FILE)
    update_version_tracker(versions)
    print("version_tracker.py updated!")

if __name__ == "__main__":
    main()
