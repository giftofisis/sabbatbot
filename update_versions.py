# GBPBot - update_versions.py
# Version: 1.0.0
# Last Updated: 2025-09-21
# Notes:
# - Auto-updates version headers in all core GBPBot files
# - Updates version_tracker.py with current versions
# - Auto-increments patch number by default
# - Can be extended for minor/major version bumps

# CHANGE LOG
# -----------------------
# [2025-09-21] v1.0.0
# - Initial version of the update_versions script
# - Reads version from file headers
# - Updates file headers and version_tracker.py
# - Auto-bumps patch version

import re
import os

# --- CONFIG ---
FILES = [
    "bot.py",
    "db.py",
    "onboarding.py",
    "comm


import re
import os

# --- CONFIG ---
FILES = [
    "bot.py",
    "db.py",
    "onboarding.py",
    "commands.py",
    "reminders.py",
    "logger.py"
]
VERSION_HEADER_PATTERN = re.compile(r"(# Version:\s*)([\d\.]+)")
VERSION_TRACKER_FILE = "version_tracker.py"

# --- HELPER FUNCTIONS ---
def parse_version(version_str):
    """Convert version string 'x.y.z' to list of ints."""
    return [int(x) for x in version_str.split(".")]

def bump_patch(version_str):
    """Increment the patch version (last digit)."""
    parts = parse_version(version_str)
    parts[-1] += 1
    return ".".join(str(x) for x in parts)

def get_file_version(file_path):
    """Extract the version from a file header."""
    if not os.path.exists(file_path):
        return "0.0.1"
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = VERSION_HEADER_PATTERN.match(line)
            if match:
                return match.group(2)
    return "0.0.1"

def update_file_version(file_path, new_version):
    """Update the version header in the file, or add it if missing."""
    lines = []
    found = False
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if VERSION_HEADER_PATTERN.match(line):
                    lines.append(f"# Version: {new_version}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        # prepend version header if missing
        lines.insert(0, f"# Version: {new_version}\n")
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def update_version_tracker(versions_dict):
    """Write the VERSIONS dictionary to version_tracker.py"""
    with open(VERSION_TRACKER_FILE, "w", encoding="utf-8") as f:
        f.write("# GBPBot - version_tracker.py\n")
        f.write("# Auto-generated\n")
        f.write("# Do not edit manually\n\n")
        f.write("VERSIONS = {\n")
        for file, version in versions_dict.items():
            f.write(f'    "{file}": "{version}",\n')
        f.write("}\n")

# --- MAIN SCRIPT ---
def main(auto_bump=True):
    versions = {}
    for file in FILES:
        current_version = get_file_version(file)
        new_version = bump_patch(current_version) if auto_bump else current_version
        update_file_version(file, new_version)
        versions[file] = new_version
        print(f"{file}: {current_version} -> {new_version}")
    update_version_tracker(versions)
    print("version_tracker.py updated!")

if __name__ == "__main__":
    main()
