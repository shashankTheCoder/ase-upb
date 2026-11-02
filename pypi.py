import json
import ssl
import certifi
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from packaging.specifiers import SpecifierSet
from packaging.version import Version


PYTHON_VERSION = Version("3.11")


def get_pypi_data(url):
    request = Request(url, headers={"User-Agent": "Python-311-Dependency-Checker/1.0"})

    context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(request, timeout=15, context=context) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def get_minimum_requirement(requires_python):
    specifiers = SpecifierSet(requires_python)

    minimum = None
    minimum_text = ""

    for specifier in specifiers:
        if specifier.operator in (">=", ">", "~=", "=="):
            try:
                version = Version(specifier.version)

                if minimum is None or version > minimum:
                    minimum = version
                    minimum_text = str(specifier)
            except Exception:
                pass

    return minimum, minimum_text


def check_dependencies():
    with open("requirements.txt", "r", encoding="utf-8") as file:
        lines = file.readlines()

    total = len(lines)
    not_found = 0
    incompatible = 0

    highest_requirement = None

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "==" not in line:
            continue

        name, version = line.split("==", 1)

        name = name.strip()
        version = version.strip()

        package_url = f"https://pypi.org/pypi/{name}/json"
        package_data = get_pypi_data(package_url)

        if package_data is None:
            not_found += 1
            continue

        release_url = f"https://pypi.org/pypi/{name}/{version}/json"

        release_data = get_pypi_data(release_url)

        if release_data is None:
            not_found += 1
            continue

        requires_python = release_data["info"].get("requires_python")

        if not requires_python:
            continue

        specifiers = SpecifierSet(requires_python)

        if not specifiers.contains(PYTHON_VERSION):
            incompatible += 1

        minimum, minimum_text = get_minimum_requirement(requires_python)

        if minimum is not None:
            if highest_requirement is None or minimum > highest_requirement[0]:
                highest_requirement = (minimum, name, version, minimum_text)

    print("Dependencies checked:", total)
    print("Not found on PyPI:", not_found)
    print("Incompatible with Python 3.11:", incompatible)

    if highest_requirement is not None:
        minimum, name, version, requirement = highest_requirement

        print(f"Highest requirement: {name}=={version} ({requirement})")
    else:
        print("Highest requirement: None found")


if __name__ == "__main__":
    try:
        check_dependencies()

    except FileNotFoundError:
        print("Error: requirements.txt file not found.")

    except (URLError, RuntimeError) as error:
        print("Network error:", error)
