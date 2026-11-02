import urllib.request
import urllib.error
import json
import re
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def get_package_info(package_name, version=None):
    if version:
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode())

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"HTTP Error: {e.code} - {e.reason}")

    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")

    except Exception as e:
        print(f"Error: {e}")

    return None


def parse_package(package_input):
    """
    Supports:
    requests == 2.31.0
    django>=4.2
    flask
    numpy~=1.26
    """

    match = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*(.*)$", package_input)

    if not match:
        return None, None

    package_name = match.group(1)
    version_spec = match.group(2).strip()

    return package_name, version_spec or None


def check_dependencies(packages, target_python="3.11"):
    found = []
    not_found = []
    incompatible = []
    compatible = []
    errors = []

    target_version = Version(target_python)

    for package_input in packages:
        package_name, version_spec = parse_package(package_input)

        if not package_name:
            errors.append(package_input)
            continue

        print(f"Checking: {package_input}")

        # Extract exact version if specified
        exact_version = None

        if version_spec:
            exact_match = re.match(r"^==\s*([0-9][A-Za-z0-9.+!-]*)$", version_spec)
            if exact_match:
                exact_version = exact_match.group(1)

        data = get_package_info(package_name, exact_version)

        if not data:
            not_found.append(package_input)
            continue

        found.append(package_input)

        info = data.get("info", {})
        requires_python = info.get("requires_python") or ""

        try:
            python_spec = SpecifierSet(requires_python)

            if requires_python and not python_spec.contains(
                target_version, prereleases=True
            ):
                incompatible.append(
                    {"package": package_input, "required_python": requires_python}
                )
            else:
                compatible.append(
                    {
                        "package": package_input,
                        "required_python": requires_python or "Not specified",
                    }
                )

        except Exception:
            errors.append(package_input)

    # Highest minimum Python requirement
    highest_requirement = None
    highest_version = None

    for item in incompatible + compatible:
        spec = item["required_python"]

        if spec == "Not specified":
            continue

        for part in spec.split(","):
            part = part.strip()

            match = re.match(r">=?\s*(\d+(?:\.\d+)*)", part)

            if match:
                version = Version(match.group(1))

                if highest_version is None or version > highest_version:
                    highest_version = version
                    highest_requirement = item

    # Report
    print("\n" + "=" * 60)
    print("PYTHON DEPENDENCY COMPATIBILITY REPORT")
    print("=" * 60)

    print(f"\nTarget Python version: {target_python}")
    print(f"Total packages checked: {len(packages)}")
    print(f"Found on PyPI: {len(found)}")
    print(f"Not found on PyPI: {len(not_found)}")
    print(f"Compatible: {len(compatible)}")
    print(f"Incompatible: {len(incompatible)}")
    print(f"Errors: {len(errors)}")

    print("\n--- NOT FOUND ON PYPI ---")
    for package in not_found:
        print(package)

    print("\n--- INCOMPATIBLE WITH PYTHON 3.11 ---")
    for item in incompatible:
        print(f"{item['package']} (requires Python {item['required_python']})")

    print("\n--- HIGHEST PYTHON REQUIREMENT ---")
    if highest_requirement:
        print(f"{highest_requirement['package']} (>= {highest_version})")
    else:
        print("No minimum Python requirement found.")

    print("\n--- COMPATIBLE PACKAGES ---")
    for item in compatible:
        print(f"{item['package']} (Python: {item['required_python']})")

    print("\n--- INVALID INPUT / ERRORS ---")
    for item in errors:
        print(item)

    print("=" * 60)


if __name__ == "__main__":
    print("Enter package dependencies (one per line).")
    print("Example: requests == 2.31.0")
    print("Type 'done' when finished.\n")

    packages = []

    while True:
        package = input("Package: ").strip()

        if package.lower() == "done":
            break

        if package:
            packages.append(package)

    check_dependencies(packages, target_python="3.11")
