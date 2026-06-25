#!/usr/bin/env python3
import sys
import json
import urllib.request
import tempfile
import gzip
import re
import os

INDEX_URL = "https://download.opensuse.org/tumbleweed/repo/oss/INDEX.gz?COUNTRY=DE"

DEFAULT_INPUT = [
    {"package": "plasma6-desktop", "display": "Plasma"},
    {"package": "libKF6XmlGui6", "display": "KDE Framework"},
    {"package": "libQt6Core6", "display": "Qt"},
    {"package": "kernel-default", "display": "Kernel"},
    {"package": "gnome-shell", "display": "GNOME"},
    {"package": "xfce4-session", "display": "XFCE"},
    {"package": "openSUSE-release", "display": ""},
]

def main(input_data=None):
    if input_data is None:
        if len(sys.argv) < 2 or not sys.argv[1].strip():
            input_data = DEFAULT_INPUT
        else:
            try:
                input_data = json.loads(sys.argv[1])
            except Exception:
                sys.exit(1)

    if not isinstance(input_data, list):
        sys.exit(1)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".gz") as tmp_file:
            tmp_path = tmp_file.name
            with urllib.request.urlopen(INDEX_URL) as response:
                tmp_file.write(response.read())
    except Exception:
        sys.exit(1)

    try:
        version_map = {}
        pattern = re.compile(r".*/([a-zA-Z0-9_\-]+)-([^-]+-[^-]+)\.[^.]+\.rpm")

        with gzip.open(tmp_path, 'rt', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    pkg_name, pkg_version = match.group(1), match.group(2)
                    if pkg_name not in version_map:
                        version_map[pkg_name] = pkg_version

        output_data = []
        for item in input_data:
            pkg_name = item.get("package")
            if pkg_name:
                output_data.append({
                    "package": pkg_name,
                    "display": item.get("display"),
                    "version": version_map.get(pkg_name, "NOT FOUND")
                })

        print(json.dumps(output_data, indent=2))

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    main()
