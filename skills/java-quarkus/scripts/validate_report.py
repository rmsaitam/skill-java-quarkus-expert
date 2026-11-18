from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_MIN_COVERAGE = 80

ARTIFACT_MARKER_RE = re.compile(r"<!--\s*java-quarkus:artifact\s+([^>]*?)-->")
MARKER_RE = re.compile(r"<!--\s*java-quarkus:([a-z-]+)\s+([^>]*?)-->")
METADATA_RE = re.compile(r"^-\s+([^:]+):\s*(.+?)\s*$", re.M)
COVERAGE_VALUE_RE = re.compile(r"^(\d{1,3})\s*%\s*$")
ID_RE = re.compile(r"^(CHG|T|CFG|EV)-(\d{3})$")

REQUIRED_SECTIONS = (
    "analysis",
    "stack",
    "design",
    "implementation",
    "tests",
    "validation",
    "configurations",
    "evidence",
    "assumptions",
    "traceability",
)

METADATA_FIELDS = (
    "Status",
    "Date",
    "Reviewer",
    "Artifact",
    "Java Version",
    "Quarkus Version",
    "Build Tool",
    "Namespace",
    "Execution Model",
    "Changes Applied",
    "Tests Run",
    "Coverage",
    "Coverage Tool",
    "Review Language",
)

ALLOWED_STATUSES = ("draft", "final")
ALLOWED_BUILD_TOOLS = ("maven", "gradle", "gradle-kts")
ALLOWED_EXECUTION_MODELS = ("imperative", "reactive", "mixed")
ALLOWED_CHANGE_STATUSES = ("implemented", "needs-review", "blocked", "alternative")
ALLOWED_EVIDENCE_STATUSES = ("passed", "partial", "failed")

FENCED_CODE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


@dataclass
class Issue:
    code: str
    message: str
    location: str = ""


@dataclass
class Report:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    strict: bool = False

    def error(self, code: str, message: str, location: str = "") -> None:
        self.errors.append(Issue(code, message, location))

    def warning(self, code: str, message: str, location: str = "") -> None:
        self.warnings.append(Issue(code, message, location))

    @property
    def ok(self) -> bool:
        return not self.errors and not (self.strict and self.warnings)

    def to_dict(self, path: str = "") -> dict:
        return {
            "path": path,
            "status": "PASS" if self.ok else "FAIL",
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
        }


def parse_attributes(fragment: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for match in re.finditer(r'([A-Za-z][A-Za-z0-9_-]*)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s]+)', fragment):
        attributes[match.group(1)] = match.group(2).strip("\"'")
    return attributes


def marker_records(text: str) -> list[dict]:
    records = []
    for match in MARKER_RE.finditer(text):
        records.append(
            {
                "kind": match.group(1),
                "attributes": parse_attributes(match.group(2)),
                "start": match.start(),
                "end": match.end(),
            }
        )
    return records


def markers_of(text: str, kind: str) -> list[dict]:
    return [record for record in marker_records(text) if record["kind"] == kind]


def strip_markers(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("<!--"))


def strip_code(text: str) -> str:
    return INLINE_CODE_RE.sub("", FENCED_CODE_RE.sub("", text))


def content_lines(text: str) -> list[str]:
    return [line.strip() for line in strip_markers(text).splitlines() if line.strip()]


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for match in METADATA_RE.finditer(text):
        key = match.group(1).strip()
        if key in METADATA_FIELDS and key not in metadata:
            metadata[key] = match.group(2).strip()
    return metadata


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.match(r"^(\d+)$", value.strip())
    return int(match.group(1)) if match else None


def parse_major(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.match(r"^(\d+)", value.strip())
    return int(match.group(1)) if match else None


def parse_coverage(value: str | None) -> int | None:
    if value is None:
        return None
    match = COVERAGE_VALUE_RE.match(value.strip())
    return int(match.group(1)) if match else None


def section_bodies(text: str, report: Report) -> dict[str, str]:
    artifacts = ARTIFACT_MARKER_RE.findall(text)
    if not artifacts:
        report.error("missing-artifact-marker", "The artifact marker is missing.")
    elif len(artifacts) > 1:
        report.error("duplicate-artifact-marker", "The artifact marker appears more than once.")
    else:
        attributes = parse_attributes(artifacts[0])
        if attributes.get("type") != "implementation":
            report.error("wrong-artifact-type", "The artifact type must be implementation.")
        if attributes.get("version") != "1":
            report.error("artifact-version", "The artifact version must be 1.")

    section_markers = markers_of(text, "section")
    found: dict[str, list[int]] = {name: [] for name in REQUIRED_SECTIONS}
    for record in section_markers:
        name = record["attributes"].get("id", "")
        if name in found:
            found[name].append(record["start"])
        else:
            report.error("unknown-section", f"Unknown section marker: {name}.", name)

    for name in REQUIRED_SECTIONS:
        if not found[name]:
            report.error("missing-section", f"Section marker is missing: {name}.", name)
        elif len(found[name]) > 1:
            report.error("duplicate-section", f"Section marker appears twice: {name}.", name)

    section_starts = sorted(
        record["start"] for record in section_markers if record["attributes"].get("id") in found
    )
    bodies: dict[str, str] = {}
    for name in REQUIRED_SECTIONS:
        starts = found[name]
        if len(starts) != 1:
            continue
        start = starts[0]
        marker_end = next(
            record["end"] for record in section_markers if record["start"] == start
        )
        following = [value for value in section_starts if value > start]
        end = min(following) if following else len(text)
        bodies[name] = text[marker_end:end]
        if not content_lines(bodies[name]):
            report.error("empty-section", f"Section has no content: {name}.", name)
    return bodies


def validate_metadata(metadata: dict[str, str], min_coverage: int, report: Report) -> None:
    for name in METADATA_FIELDS:
        if not metadata.get(name):
            report.error("missing-metadata", f"Metadata field is missing: {name}.", name)

    status = metadata.get("Status", "").lower()
    if status and status not in ALLOWED_STATUSES:
        report.error("invalid-status", f"Invalid report status: {status}.", "Status")

    if metadata.get("Date") and not re.match(r"^\d{4}-\d{2}-\d{2}$", metadata["Date"]):
        report.error("invalid-date", "Date must use YYYY-MM-DD.", "Date")

    if metadata.get("Build Tool") and metadata["Build Tool"] not in ALLOWED_BUILD_TOOLS:
        report.error("invalid-build-tool", f"Invalid build tool: {metadata['Build Tool']}.", "Build Tool")

    model = metadata.get("Execution Model", "").lower()
    if model and model not in ALLOWED_EXECUTION_MODELS:
        report.error("invalid-execution-model", f"Invalid execution model: {model}.", "Execution Model")

    if metadata.get("Java Version") and parse_major(metadata["Java Version"]) is None:
        report.error("invalid-java-version", "Java Version must be numeric.", "Java Version")

    major = parse_major(metadata.get("Quarkus Version"))
    namespace = metadata.get("Namespace", "").lower()
    if major is None:
        report.error("invalid-quarkus-version", "Quarkus Version must be numeric.", "Quarkus Version")
    elif major >= 3 and namespace != "jakarta":
        report.error("namespace-mismatch", "Quarkus 3+ requires the jakarta namespace.", "Namespace")
    elif major == 2 and namespace != "javax":
        report.error("namespace-mismatch", "Quarkus 2.x requires the javax namespace.", "Namespace")
    elif namespace not in {"jakarta", "javax"}:
        report.error("invalid-namespace", f"Invalid namespace: {namespace}.", "Namespace")

    coverage = parse_coverage(metadata.get("Coverage"))
    if metadata.get("Coverage") and coverage is None:
        report.error("invalid-coverage", "Coverage must be a percentage such as 88%.", "Coverage")
    elif coverage is not None and coverage < min_coverage:
        report.error(
            "coverage-below-gate",
            f"Coverage {coverage}% is below the {min_coverage}% gate.",
            "Coverage",
        )

    tool = metadata.get("Coverage Tool", "").lower()
    if tool and "jacoco" not in tool:
        report.error("invalid-coverage-tool", "Coverage Tool must be jacoco.", "Coverage Tool")


def bounded_body(text: str, record: dict) -> str:
    following = [
        other["start"]
        for other in marker_records(text)
        if other["start"] > record["start"]
    ]
    end = min(following) if following else len(text)
    return text[record["end"] : end]


def parse_numbered_entries(text: str, kind: str, prefix: str, report: Report) -> list[dict]:
    records = markers_of(text, kind)
    if not records:
        report.error(f"missing-{kind}", f"At least one {kind} entry is required.")
        return []

    entries: list[dict] = []
    seen: set[str] = set()
    for record in records:
        identifier = record["attributes"].get("id", "")
        if not re.match(rf"^{prefix}-\d{{3}}$", identifier):
            report.error(f"invalid-{kind}-id", f"Invalid {kind} id: {identifier}.", identifier)
        if identifier in seen:
            report.error(f"duplicate-{kind}-id", f"Duplicate {kind} id: {identifier}.", identifier)
        seen.add(identifier)
        entries.append(
            {
                "id": identifier,
                "attributes": record["attributes"],
                "body": bounded_body(text, record),
            }
        )
    return entries


def require_fields(entry: dict, fields: dict[str, int], report: Report, prefix: str = "") -> None:
    for name, minimum in fields.items():
        match = re.search(rf"^- {re.escape(name)}:\s*(.+)$", entry["body"], re.M)
        value = match.group(1).strip() if match else ""
        if len(value) < minimum:
            field_code = f"missing-{name.lower().replace(' ', '-')}"
            code = f"missing-{prefix}-{name.lower().replace(' ', '-')}" if prefix else field_code
            report.error(
                code,
                f"Entry {entry['id']} needs a substantive {name} field.",
                entry["id"],
            )


def validate_analysis(body: str, metadata: dict[str, str], changes: list[dict], report: Report) -> None:
    stripped = strip_markers(body)
    if "Análise Breve" not in stripped:
        report.error("missing-analysis-heading", "The analysis section needs the Análise Breve heading.")
    if len(content_lines(body)) < 2:
        report.error("thin-analysis", "The analysis section needs an explanation.")

    declared = parse_int(metadata.get("Changes Applied"))
    if declared is not None and declared != len(changes):
        report.error(
            "count-mismatch",
            f"Changes Applied ({declared}) does not match the {len(changes)} change entries.",
            "Changes Applied",
        )


def validate_stack(body: str, metadata: dict[str, str], report: Report) -> None:
    records = markers_of(body, "stack")
    if len(records) != 1:
        report.error("missing-stack-marker", "Exactly one stack marker is required.", "stack")
        return
    attributes = records[0]["attributes"]
    expected = {
        "java": metadata.get("Java Version", ""),
        "quarkus": metadata.get("Quarkus Version", ""),
        "build": metadata.get("Build Tool", ""),
        "namespace": metadata.get("Namespace", ""),
    }
    for key, value in expected.items():
        if attributes.get(key) != value:
            report.error("stack-mismatch", f"Stack marker {key} does not match metadata.", key)

    if not re.search(r"pom\.xml|build\.gradle", strip_markers(body), re.I):
        report.warning(
            "unverified-stack",
            "The stack section does not name the build descriptor that was detected.",
            "stack",
        )


def validate_changes(text: str, report: Report) -> list[dict]:
    changes = parse_numbered_entries(text, "change", "CHG", report)
    for entry in changes:
        status = entry["attributes"].get("status", "")
        if status not in ALLOWED_CHANGE_STATUSES:
            report.error("invalid-change-status", f"Invalid change status: {status}.", entry["id"])
        require_fields(
            entry,
            {"File": 8, "Change": 15, "Design": 15},
            report,
        )
    return changes


def validate_tests(text: str, body: str, report: Report) -> list[dict]:
    tests = parse_numbered_entries(text, "test", "T", report)
    stripped_body = strip_markers(body)
    if "junit" not in stripped_body.lower():
        report.error("junit-required", "The tests section must mention JUnit.")

    for entry in tests:
        attributes = entry["attributes"]
        if "junit" not in attributes.get("framework", "").lower():
            report.error("junit-required", "A test entry must declare a JUnit framework.", entry["id"])
        if attributes.get("mockito", "").lower() != "true":
            report.error("mockito-required", "A unit test entry must use Mockito.", entry["id"])
        if attributes.get("context", "").lower() != "unit":
            report.error("unit-context-required", "A unit test entry must have context=unit.", entry["id"])
        require_fields(entry, {"File": 8, "Cases": 10, "Coverage": 10}, report)
    return tests


def validate_configurations(text: str, body: str, report: Report) -> list[dict]:
    entries = parse_numbered_entries(text, "config", "CFG", report) if markers_of(text, "config") else []
    stripped = strip_markers(body)
    if not entries and "No changes." not in stripped:
        report.error(
            "missing-config-declaration",
            "The configurations section must say 'No changes.' or declare configuration entries.",
        )
    for entry in entries:
        file_name = entry["attributes"].get("file", "")
        if not re.match(r"application\.(properties|ya?ml)", file_name):
            report.error("invalid-config-file", "A config entry must name application.properties or application.yaml.", entry["id"])
        require_fields(entry, {"Property": 3, "Reason": 10}, report, prefix="config")
    return entries


def validate_validation(body: str, min_coverage: int, report: Report) -> None:
    records = markers_of(body, "coverage")
    if len(records) != 1:
        report.error("missing-coverage-marker", "Exactly one coverage marker is required.", "validation")
        return
    attributes = records[0]["attributes"]
    value = parse_int(attributes.get("value"))
    gate = parse_int(attributes.get("gate"))
    if value is None or gate is None:
        report.error("invalid-coverage", "The coverage marker needs numeric value and gate.", "validation")
        return
    if value < min_coverage or gate < min_coverage:
        report.error(
            "coverage-below-gate",
            f"Coverage marker must satisfy the {min_coverage}% gate.",
            "validation",
        )
    if "jacoco" not in attributes.get("tool", "").lower():
        report.error("invalid-coverage-tool", "The coverage marker must declare tool=jacoco.", "validation")

    checkboxes = len(re.findall(r"^- \[[ xX]\]", body, re.M))
    if checkboxes < 4:
        report.error("insufficient-validation", "The validation section needs at least four checkboxes.")

    stripped = strip_markers(body).lower()
    for token in ("test", "jacoco", f"{min_coverage}%"):
        if token not in stripped:
            report.error("missing-validation-detail", f"Validation evidence must mention {token}.")


def validate_evidence(text: str, report: Report) -> list[dict]:
    entries = parse_numbered_entries(text, "evidence", "EV", report)
    for entry in entries:
        status = entry["attributes"].get("status", "")
        if status not in ALLOWED_EVIDENCE_STATUSES:
            report.error("invalid-evidence-status", f"Invalid evidence status: {status}.", entry["id"])
        require_fields(entry, {"Result": 8}, report)
    if entries and not any(entry["attributes"].get("status") == "passed" for entry in entries):
        report.error("evidence-not-passed", "At least one evidence row must have status=passed.")
    return entries


def validate_traceability(
    body: str,
    changes: list[dict],
    tests: list[dict],
    evidence: list[dict],
    report: Report,
) -> None:
    stripped = strip_markers(body)
    for token in ("Change", "Test", "Evidence"):
        if token not in stripped:
            report.error("missing-traceability-header", f"Traceability table needs a {token} column.")
    for entry in changes + tests + evidence:
        if entry["id"] and entry["id"] not in stripped:
            report.error("traceability-gap", f"Entry {entry['id']} is not linked in traceability.", entry["id"])


def validate_suppressions(text: str, report: Report) -> None:
    stripped = strip_code(text)
    if re.search(r"@SuppressWarnings|NOSONAR", stripped) and "Suppression approved" not in stripped:
        report.error(
            "suppression-without-approval",
            "Suppressions require a proven false positive and recorded approval.",
        )


def validate_approval(text: str, report: Report) -> None:
    if re.search(r"\b(LGTM|Ship it|Approved by|Approval:)\b", text, re.I):
        report.error("approval-verdict", "Do not include an approval verdict in the artifact.")


def scan_placeholders(text: str, report: Report) -> None:
    stripped = strip_code(text)
    if re.search(r"\b(TODO|FIXME|TBD)\b|\bplaceholder\b|\bomitted\b", stripped, re.I):
        report.error("placeholder", "The artifact contains a placeholder.")


def scan_secrets(text: str, report: Report) -> None:
    patterns = (
        r"gh[pousr]_[A-Za-z0-9]{20,}",
        r"\b(AKIA|ASIA)[0-9A-Z]{16}\b",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"(?i)password\s*[:=]\s*(?!\[REDACTED\]|\$\{)[^\s]+",
        r"\b[0-9a-fA-F]{40}\b",
        r"Bearer\s+(?!\[REDACTED\])[A-Za-z0-9._-]{20,}",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        report.error("secret", "The artifact contains a possible secret.")


def validate_report(
    text: str,
    report: Report,
    min_coverage: int = DEFAULT_MIN_COVERAGE,
    strict: bool = False,
) -> None:
    report.strict = strict
    bodies = section_bodies(text, report)
    metadata = parse_metadata(text)
    validate_metadata(metadata, min_coverage, report)

    changes = validate_changes(text, report)
    tests = validate_tests(text, bodies.get("tests", ""), report)
    configurations = validate_configurations(text, bodies.get("configurations", ""), report)
    evidence = validate_evidence(text, report)

    if "analysis" in bodies:
        validate_analysis(bodies["analysis"], metadata, changes, report)
    if "stack" in bodies:
        validate_stack(bodies["stack"], metadata, report)
    if "design" in bodies:
        if len(content_lines(bodies["design"])) < 2:
            report.error("thin-design", "The design section needs at least two content lines.")
    if "implementation" in bodies:
        if not changes:
            report.error("missing-change", "The implementation section needs a change entry.")
    if "assumptions" in bodies:
        if not content_lines(bodies["assumptions"]):
            report.error("empty-section", "The assumptions section needs content.", "assumptions")
    if "validation" in bodies:
        validate_validation(bodies["validation"], min_coverage, report)
    if "traceability" in bodies:
        validate_traceability(bodies["traceability"], changes, tests, evidence, report)

    validate_suppressions(text, report)
    validate_approval(text, report)
    scan_placeholders(text, report)
    scan_secrets(text, report)

    assert configurations is not None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_report.py",
        description="Validate a JAVA-QUARKUS-IMPL.md implementation report.",
    )
    parser.add_argument("paths", nargs="+", help="Report files to validate.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=DEFAULT_MIN_COVERAGE,
        help=f"Minimum coverage percentage (default {DEFAULT_MIN_COVERAGE}).",
    )
    return parser


def format_issue(issue: Issue) -> str:
    location = f" ({issue.location})" if issue.location else ""
    return f"[ERROR] {issue.code}: {issue.message}{location}"


def print_report(path: str, report: Report) -> None:
    if report.ok:
        print(f"PASS: {path}")
    else:
        print(f"FAIL: {path}")
    for issue in report.errors:
        print(format_issue(issue))
    for issue in report.warnings:
        print(f"[WARN] {issue.code}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[tuple[str, Report]] = []
    for value in args.paths:
        path = Path(value)
        report = Report()
        if not path.is_file():
            report.error("missing-report", f"Report not found: {path}.")
        else:
            validate_report(
                path.read_text(encoding="utf-8"),
                report,
                min_coverage=args.min_coverage,
                strict=args.strict,
            )
        results.append((str(path), report))

    all_ok = all(report.ok for _, report in results)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "PASS" if all_ok else "FAIL",
                    "reports": [report.to_dict(path) for path, report in results],
                },
                indent=2,
            )
        )
    else:
        for path, report in results:
            print_report(path, report)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
