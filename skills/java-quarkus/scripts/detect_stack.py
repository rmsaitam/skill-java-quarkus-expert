from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXIT_OK = 0
EXIT_STRICT = 1
EXIT_CONFIG = 2
EXIT_PARSE = 3

DESCRIPTORS = ("pom.xml", "build.gradle.kts", "build.gradle")


class ConfigError(Exception):
    pass


class ParseError(Exception):
    pass


def item(code: str, message: str, source: str) -> dict:
    return {"code": code, "message": message, "source": source}


def find_descriptor(root: Path) -> str:
    for name in DESCRIPTORS:
        if (root / name).is_file():
            return name
    raise ConfigError(
        "No pom.xml, build.gradle or build.gradle.kts found. Provide the build descriptor "
        "or the exact Java and Quarkus versions before continuing."
    )


def detect_namespace(version: str | None) -> str:
    match = re.match(r"^(\d+)", (version or "").strip())
    if not match:
        return "unknown"
    major = int(match.group(1))
    if major >= 3:
        return "jakarta"
    if major == 2:
        return "javax"
    return "unknown"


def infer_execution_model(extensions: list[str]) -> str:
    reactive = any(
        name == "quarkus-rest"
        or name.startswith("quarkus-rest-")
        or "resteasy-reactive" in name
        or "smallrye-reactive-messaging" in name
        or "hibernate-reactive" in name
        for name in extensions
    )
    imperative = any(
        name in {"quarkus-resteasy", "quarkus-resteasy-jackson"} for name in extensions
    )
    if reactive and imperative:
        return "mixed"
    if reactive:
        return "reactive-capable"
    if imperative:
        return "imperative"
    return "unknown"


def normalize_extensions(values: list[str]) -> list[str]:
    return sorted({value.strip() for value in values if value.strip()})


def normalize_version(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().strip("'\"")
    match = re.match(r"^v?\d+(?:\.\d+)*(?:[.-][0-9A-Za-z.-]+)?$", cleaned)
    return cleaned if match else None


def parse_major(version: str | None) -> int | None:
    match = re.match(r"^(\d+)", (version or "").strip())
    return int(match.group(1)) if match else None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return None


def load_gradle_properties(path: Path) -> dict[str, str]:
    properties: dict[str, str] = {}
    if not path.is_file():
        return properties
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        match = re.match(r"^([A-Za-z0-9._-]+)\s*[:=]\s*(.*)$", stripped)
        if match:
            properties[match.group(1)] = match.group(2).strip()
    return properties


def detect_test_dependencies(raw_names: list[str]) -> list[str]:
    joined = " ".join(raw_names).lower()
    detected = []
    if "junit5" in joined or "junit-jupiter" in joined or "quarkus-junit" in joined:
        detected.append("junit5")
    if "mockito" in joined:
        detected.append("mockito")
    if "rest-assured" in joined or "restassured" in joined:
        detected.append("restAssured")
    if "jacoco" in joined:
        detected.append("jacoco")
    return sorted(detected)


def parse_pom(path: Path) -> dict:
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ParseError(f"Invalid XML in {path}: {exc}") from exc

    root = tree.getroot()
    properties: dict[str, str] = {}
    for element in root.iter():
        if local_name(element.tag) == "properties":
            for child in element:
                properties[local_name(child.tag)] = (child.text or "").strip()

    java_version = (
        properties.get("maven.compiler.release")
        or properties.get("maven.compiler.source")
        or properties.get("java.version")
        or properties.get("quarkus.java.version")
    )
    quarkus_version = properties.get("quarkus.platform.version") or properties.get(
        "quarkus.version"
    )

    raw_names: list[str] = []
    for element in root.iter():
        if local_name(element.tag) not in {"dependency", "plugin"}:
            continue
        artifact_id = child_text(element, "artifactId")
        if not artifact_id:
            continue
        raw_names.append(artifact_id)
        if artifact_id in {"quarkus-bom", "quarkus-camel-bom", "quarkus-maven-plugin"}:
            version = child_text(element, "version")
            if version and not version.startswith("${") and not quarkus_version:
                quarkus_version = version

    if not java_version:
        for element in root.iter():
            if local_name(element.tag) in {"release", "source", "target"}:
                value = (element.text or "").strip()
                if value.isdigit():
                    java_version = value
                    break

    extensions = normalize_extensions(
        [
            name
            for name in raw_names
            if (name.startswith("quarkus-") or name.startswith("camel-quarkus-"))
            and name != "quarkus-maven-plugin"
        ]
    )
    extensions = sorted(set(extensions) | {name for name in extensions if "jacoco" in name})

    return {
        "javaVersion": normalize_version(java_version),
        "javaSource": "maven" if java_version else None,
        "quarkusVersion": normalize_version(quarkus_version),
        "extensions": extensions,
        "testDependencies": detect_test_dependencies(raw_names),
        "rawNames": raw_names,
    }


def parse_gradle(path: Path, properties: dict[str, str]) -> dict:
    text = path.read_text(encoding="utf-8")

    java_match = re.search(
        r"sourceCompatibility\s*=\s*(?:JavaVersion\.VERSION_)?['\"]?(\d+(?:\.\d+)*)",
        text,
    )
    if not java_match:
        java_match = re.search(r"JavaLanguageVersion\.of\((\d+)\)", text)
    java_version = (
        java_match.group(1) if java_match else properties.get("javaVersion") or properties.get("java.version")
    )

    quarkus_version = properties.get("quarkusPlatformVersion") or properties.get(
        "quarkus.platform.version"
    )
    if not quarkus_version:
        version_match = re.search(
            r"quarkusPlatformVersion\s*=\s*['\"]([^'\"]+)['\"]", text
        ) or re.search(r"id\s+['\"]io\.quarkus['\"]\s+version\s+['\"]([^'\"]+)['\"]", text)
        if version_match:
            quarkus_version = version_match.group(1)

    raw_names: list[str] = []
    for match in re.finditer(r"['\"]([A-Za-z0-9_.-]+):([^:'\"]+)['\"]", text):
        raw_names.append(match.group(2))

    extensions = normalize_extensions(
        [
            name
            for name in raw_names
            if name.startswith("quarkus-") or name.startswith("camel-quarkus-")
        ]
    )

    return {
        "javaVersion": normalize_version(java_version),
        "javaSource": "gradle" if java_version else None,
        "quarkusVersion": normalize_version(quarkus_version),
        "extensions": extensions,
        "testDependencies": detect_test_dependencies(raw_names),
        "rawNames": raw_names,
    }


def scan_config_keys(root: Path) -> list[str]:
    keys: set[str] = set()
    for name in ("application.properties", "application.yaml", "application.yml"):
        path = root / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.match(r"^([A-Za-z0-9._-]+)\s*[:=]", stripped)
            if match:
                keys.add(match.group(1))
    return sorted(keys)


def has_mixed_namespace_imports(root: Path) -> bool:
    jakarta = False
    javax = False
    for path in root.rglob("*.java"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        jakarta = jakarta or bool(re.search(r"^import\s+jakarta\.", text, re.M))
        javax = javax or bool(re.search(r"^import\s+javax\.", text, re.M))
        if jakarta and javax:
            return True
    return False


def detect_stack(root: Path) -> dict:
    root = Path(root).resolve()
    descriptor = find_descriptor(root)
    descriptor_path = root / descriptor

    if descriptor == "pom.xml":
        parsed = parse_pom(descriptor_path)
        build_tool = "maven"
    else:
        properties = load_gradle_properties(root / "gradle.properties")
        parsed = parse_gradle(descriptor_path, properties)
        build_tool = "gradle-kts" if descriptor.endswith(".kts") else "gradle"

    java_version = parsed["javaVersion"]
    quarkus_version = parsed["quarkusVersion"]
    namespace = detect_namespace(quarkus_version)
    extensions = parsed["extensions"]
    test_dependencies = parsed["testDependencies"]
    config_keys = scan_config_keys(root)

    warnings: list[dict] = []
    blockers: list[dict] = []
    if not java_version:
        blockers.append(
            item("missing-java-version", "Java version not found in the build descriptor.", descriptor)
        )
    if not quarkus_version:
        blockers.append(
            item("missing-quarkus-version", "Quarkus version not found in the build descriptor.", descriptor)
        )
    if has_mixed_namespace_imports(root):
        warnings.append(
            item(
                "mixed-namespace-imports",
                "Both jakarta.* and javax.* imports are present in Java sources.",
                "src",
            )
        )
    if namespace == "unknown" and quarkus_version:
        warnings.append(
            item("unknown-namespace", "The Quarkus major version does not map to a namespace.", descriptor)
        )

    capabilities = {
        "jacoco": "jacoco" in test_dependencies or any("jacoco" in name for name in extensions),
        "mockito": "mockito" in test_dependencies,
        "restAssured": "restAssured" in test_dependencies,
        "faultTolerance": any("fault-tolerance" in name for name in extensions),
        "devServicesCapable": any("quarkus-junit5" in name for name in extensions)
        or "junit5" in test_dependencies,
    }

    return {
        "projectRoot": str(root),
        "buildTool": build_tool,
        "descriptor": descriptor,
        "java": {"version": java_version, "source": parsed["javaSource"]},
        "quarkus": {"version": quarkus_version, "major": parse_major(quarkus_version)},
        "namespace": namespace,
        "extensions": extensions,
        "testDependencies": test_dependencies,
        "capabilities": capabilities,
        "executionModel": infer_execution_model(extensions),
        "configKeys": config_keys,
        "warnings": warnings,
        "blockers": blockers,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="detect_stack.py",
        description="Detect Java, Quarkus, extensions and test capabilities from a project build.",
    )
    parser.add_argument("root", nargs="?", default=".", help="Project root directory.")
    parser.add_argument("--output", help="Write the JSON result to this path.")
    parser.add_argument("--json", action="store_true", help="Print the JSON result to stdout.")
    parser.add_argument("--strict", action="store_true", help="Fail when warnings are present.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = detect_stack(Path(args.root))
    except ConfigError as exc:
        print(f"[ERROR] config: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except ParseError as exc:
        print(f"[ERROR] parse: {exc}", file=sys.stderr)
        return EXIT_PARSE

    payload = json.dumps(data, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    if args.json or not args.output:
        print(payload)

    if data["blockers"]:
        return EXIT_CONFIG
    if args.strict and data["warnings"]:
        return EXIT_STRICT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
