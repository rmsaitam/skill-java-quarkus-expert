import json

import pytest

import validate_report as vr


def run(text, **kwargs):
    report = vr.Report()
    vr.validate_report(text, report, **kwargs)
    return report


def codes(report):
    return {issue.code for issue in report.errors}


def warning_codes(report):
    return {issue.code for issue in report.warnings}


def replace_once(text, old, new):
    assert old in text
    return text.replace(old, new, 1)


def test_valid_fixture_passes(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")

    report = run(text)

    assert report.ok
    assert report.errors == []


def test_missing_artifact_marker(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace("<!-- java-quarkus:artifact type=implementation version=1 -->", "")

    assert "missing-artifact-marker" in codes(run(text))


def test_wrong_artifact_type(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "type=implementation", "type=review")

    assert "wrong-artifact-type" in codes(run(text))


def test_duplicate_section_marker(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(
        text,
        "<!-- java-quarkus:section id=tests -->",
        "<!-- java-quarkus:section id=analysis -->\n<!-- java-quarkus:section id=tests -->",
    )

    assert "duplicate-section" in codes(run(text))


def test_missing_section_marker(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace("<!-- java-quarkus:section id=evidence -->", "")

    assert "missing-section" in codes(run(text))


def test_coverage_below_gate(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "Coverage: 88%", "Coverage: 70%")
    text = replace_once(text, "value=88", "value=70")
    text = replace_once(text, "reported 88%", "reported 70%")

    assert "coverage-below-gate" in codes(run(text))


def test_missing_metadata_field(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace("- Build Tool: maven\n", "")

    assert "missing-metadata" in codes(run(text))


def test_namespace_mismatch_for_quarkus3(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "Namespace: jakarta", "Namespace: javax")
    text = replace_once(text, "namespace=jakarta", "namespace=javax")

    assert "namespace-mismatch" in codes(run(text))


def test_invalid_build_tool(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "Build Tool: maven", "Build Tool: make")
    text = replace_once(text, "build=maven", "build=make")

    assert "invalid-build-tool" in codes(run(text))


def test_changes_count_mismatch(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "Changes Applied: 1", "Changes Applied: 2")

    assert "count-mismatch" in codes(run(text))


def test_invalid_change_id(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "id=CHG-001", "id=CHG-1")

    assert "invalid-change-id" in codes(run(text))


def test_missing_change_entry(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace("<!-- java-quarkus:change id=CHG-001 status=implemented -->", "")

    assert "missing-change" in codes(run(text))


def test_missing_test_entry(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace(
        "<!-- java-quarkus:test id=T-001 framework=junit mockito=true context=unit -->", ""
    )

    assert "missing-test" in codes(run(text))


def test_mockito_required(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "mockito=true", "mockito=false")

    assert "mockito-required" in codes(run(text))


def test_unit_context_required(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "context=unit", "context=integration")

    assert "unit-context-required" in codes(run(text))


def test_junit_required_in_tests_section(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "The tests use JUnit 5", "The tests use the framework")

    assert "junit-required" in codes(run(text))


def test_configurations_require_explicit_no_changes(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "No changes.", "Nothing to report.")

    assert "missing-config-declaration" in codes(run(text))


def test_config_entry_requires_property(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(
        text,
        "No changes.",
        "<!-- java-quarkus:config id=CFG-001 file=application.properties -->\n- Reason: Bound the timeout.",
    )

    assert "missing-config-property" in codes(run(text))


def test_missing_coverage_marker(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace("<!-- java-quarkus:coverage value=88 gate=80 tool=jacoco -->", "")

    assert "missing-coverage-marker" in codes(run(text))


def test_insufficient_validation_checkboxes(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    for line in [
        "- [x] `./mvnw verify` produced the JaCoCo report.\n",
        "- [x] JaCoCo reported 88% coverage, above the 80% gate.\n",
        "- [x] No blocking work was added to an event-loop method.\n",
    ]:
        text = text.replace(line, "")

    assert "insufficient-validation" in codes(run(text))


def test_missing_evidence(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = text.replace(
        "<!-- java-quarkus:evidence id=EV-001 command=./mvnw test status=passed -->", ""
    )

    assert "missing-evidence" in codes(run(text))


def test_traceability_gap(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "| CHG-001 | T-001 | EV-001 |", "| CHG-002 | T-001 | EV-001 |")

    assert "traceability-gap" in codes(run(text))


def test_placeholder_is_rejected(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "- Design: The resource maps", "- Design: TODO finish mapping: The resource maps")

    assert "placeholder" in codes(run(text))


def test_secret_is_rejected(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "- No new dependency was introduced.", "- token = ghp_abcdefghijklmnopqrstuvwxyz0123456789")

    assert "secret" in codes(run(text))


def test_approval_verdict_is_rejected(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "- No new dependency was introduced.", "LGTM")

    assert "approval-verdict" in codes(run(text))


def test_suppression_requires_approval(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    text = replace_once(text, "- No new dependency was introduced.", "Added @SuppressWarnings for the warning.")

    assert "suppression-without-approval" in codes(run(text))


def test_custom_min_coverage_gate(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")

    report = run(text, min_coverage=95)

    assert "coverage-below-gate" in codes(report)


def test_strict_mode_promotes_warnings(fixtures):
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    report = run(text, strict=True)
    assert report.ok

    invalid = replace_once(text, "The detector read `pom.xml`", "The detector guessed")
    strict_report = run(invalid, strict=True)

    assert "unverified-stack" in warning_codes(strict_report)
    assert not strict_report.ok


def test_json_cli_output(fixtures, tmp_path, capsys):
    path = tmp_path / "report.md"
    path.write_text((fixtures / "valid_report.md").read_text(encoding="utf-8"), encoding="utf-8")

    code = vr.main([str(path), "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"


def test_cli_fails_on_invalid_report(fixtures, tmp_path, capsys):
    path = tmp_path / "report.md"
    text = (fixtures / "valid_report.md").read_text(encoding="utf-8")
    path.write_text(replace_once(text, "Coverage: 88%", "Coverage: 70%"), encoding="utf-8")

    assert vr.main([str(path)]) == 1
    assert "[ERROR]" in capsys.readouterr().out
