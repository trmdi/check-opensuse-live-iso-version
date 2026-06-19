#!/usr/bin/env python3
import re
import sys
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

def get_packages_filtered(input_data):
    base_url = "https://openqa.opensuse.org/"
    start_url = "https://openqa.opensuse.org/group_overview/1?only_tagged=1"

    # --- Step 1: Get the first published build link ---
    try:
        response = requests.get(start_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return json.dumps({"error": f"Failed to fetch group overview: {str(e)}"}, indent=2)

    soup = BeautifulSoup(response.text, 'html.parser')
    build_rows = soup.find_all('div', class_='build-row')

    build_link = None
    for row in build_rows:
        tag_span = row.find('span', class_='tag')
        if tag_span and 'published' in tag_span.get_text(strip=True).lower():
            build_label = row.find('div', class_='build-label')
            if build_label:
                link_element = build_label.find('a')
                if link_element and link_element.get('href'):
                    build_link = urljoin(start_url, link_element['href'])
                    break

    if not build_link:
        return json.dumps({"error": "No published builds found."}, indent=2)

    # --- Step 2: Extract build id parameter ---
    parsed_url = urlparse(build_link)
    query_params = parse_qs(parsed_url.query)
    build_id_list = query_params.get('build')

    if not build_id_list:
        return json.dumps({"error": "Could not find 'build' parameter in the link."}, indent=2)

    build_id = build_id_list[0]

    # --- Step 3: Open the new build overview link ---
    target_url = f"https://openqa.opensuse.org/tests/overview?distri=aeon&distri=microos&distri=opensuse&version=Tumbleweed&build={build_id}&groupid=1"

    try:
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return json.dumps({"error": f"Failed to fetch build overview: {str(e)}"}, indent=2)

    file_contents_cache = {}
    soup_overview = BeautifulSoup(response.text, 'html.parser')
    results_array = []

    # --- Step 4: Process each JSON object from the input ---
    for item in input_data:
        table_id = item.get("tableID")
        package_name = item.get("package")

        # Prepare the clean dictionary for final output mapping (excluding tableID)
        output_item = {
            "flavor": item.get("flavor"),
            "package": package_name,
            "build_id": build_id,
            "download_link": item.get("download_link")
        }

        if not table_id or not package_name:
            output_item["version"] = "missing tableID or package fields"
            results_array.append(output_item)
            continue

        table = soup_overview.find('td', id=table_id)
        if not table:
            output_item["version"] = f"table {table_id} not found"
            results_array.append(output_item)
            continue

        # Find the core live test suite row link
        a_tag = table.find('a')
        test_link = urljoin(base_url, a_tag.get('href')) if a_tag else None

        if not test_link:
            output_item["version"] = "matching live x86_64 test row link not found"
            results_array.append(output_item)
            continue

        info_file_url = f"{test_link.rstrip('/')}/file/textinfo-info.txt"

        # --- Step 5: Fetch textinfo file ---
        if info_file_url not in file_contents_cache:
            try:
                file_response = requests.get(info_file_url, timeout=10)
                file_response.raise_for_status()
                file_contents_cache[info_file_url] = file_response.text
            except requests.RequestException:
                file_contents_cache[info_file_url] = None

        file_text = file_contents_cache[info_file_url]
        if file_text is None:
            output_item["version"] = "failed to fetch log file"
            results_array.append(output_item)
            continue

        # --- Step 6: Parse the package version ---
        pattern = re.compile(rf"^{re.escape(package_name)}-(.+)", re.MULTILINE)
        match = pattern.search(file_text)

        if match:
            remainder = match.group(1).strip()
            # Strip out common architectures (.x86_64, .noarch, etc.)
            version = re.sub(r'\.(x86_64|noarch|i586|aarch64|ppc64le|s390x)$', '', remainder)
            output_item["version"] = version
        else:
            output_item["version"] = "not found"

        results_array.append(output_item)

    return json.dumps(results_array, indent=2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            raw_input = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid input JSON string format."}, indent=2))
            sys.exit(1)
    else:
        # Test script input fallback structure
        raw_input = [
            {
                "flavor": "KDE LiveCD x86_64",
                "tableID": "res_KDE-Live_x86_64_kde-live@64bit-4G",
                "package": "plasma6-desktop",
                "download_link": "https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-KDE-Live-x86_64-Current.iso?mirrorlist"
            },
            {
                "flavor": "GNOME LiveCD x86_64",
                "tableID": "res_GNOME-Live_x86_64_gnome-live@64bit-4G",
                "package": "gnome-shell",
                "download_link": "https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-GNOME-Live-x86_64-Current.iso?mirrorlist"
            },
            {
                "flavor": "Xfce LiveCD x86_64",
                "tableID": "res_XFCE-Live_x86_64_xfce-live@64bit-3G",
                "package": "xfce4-session",
                "download_link": "https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-XFCE-Live-x86_64-Current.iso?mirrorlist"
            }
        ]

    output_json = get_packages_filtered(raw_input)
    print(output_json)
