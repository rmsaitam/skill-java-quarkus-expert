import json
import shutil

import pytest

import detect_stack as ds


def make_project(tmp_path, *, pom=None, gradle=None, properties=None):
    project = tmp_path / "project"
    project.mkdir()
    if pom:
        shutil.copy(pom, project / "pom.xml")
    if gradle:
        shutil.copy(gradle, project / "build.gradle")
    if properties:
        shutil.copy(properties, project / "application.properties")
    return project


def test_detects_maven_quarkus3_stack(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        pom=fixtures / "pom-quarkus3.xml",
        properties=fixtures / "application.properties",
    )

    data = ds.detect_stack(project)

    assert data["buildTool"] == "maven"
    assert data["descriptor"] == "pom.xml"
    assert data["java"]["version"] == "21"
    assert data["quarkus"]["version"] == "3.33.0"
    assert data["quarkus"]["major"] == 3
    assert data["namespace"] == "jakarta"
    assert "quarkus-rest-jackson" in data["extensions"]
    assert "quarkus-hibernate-orm-panache" in data["extensions"]
    assert data["capabilities"]["mockito"] is True
    assert data["capabilities"]["jacoco"] is True
    assert data["capabilities"]["faultTolerance"] is True
    assert data["executionModel"] == "reactive-capable"
    assert data["warnings"] == []
    assert data["blockers"] == []


def test_detects_gradle_quarkus2_stack(fixtures, tmp_path):
    project = make_project(tmp_path, gradle=fixtures / "build-quarkus2.gradle")

    data = ds.detect_stack(project)

    assert data["buildTool"] == "gradle"
    assert data["java"]["version"] == "11"
    assert data["quarkus"]["version"] == "2.16.12.Final"
    assert data["quarkus"]["major"] == 2
    assert data["namespace"] == "javax"
    assert "quarkus-resteasy-reactive" in data["extensions"]
    assert data["capabilities"]["mockito"] is True
    assert data["capabilities"]["jacoco"] is False


def test_config_keys_are_collected_without_values(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        pom=fixtures / "pom-quarkus3.xml",
        properties=fixtures / "application.properties",
    )

    data = ds.detect_stack(project)

    assert "quarkus.datasource.password" in data["configKeys"]
    assert "payment.gateway.base-url" in data["configKeys"]
    assert "super-secret-value" not in json.dumps(data)


def test_missing_descriptor_raises_config_error(tmp_path):
    with pytest.raises(ds.ConfigError):
        ds.detect_stack(tmp_path)


def test_malformed_pom_raises_parse_error(tmp_path):
    project = make_project(tmp_path)
    (project / "pom.xml").write_text("<project><broken>", encoding="utf-8")

    with pytest.raises(ds.ParseError):
        ds.detect_stack(project)


def test_missing_versions_are_blockers(tmp_path):
    project = make_project(tmp_path)
    (project / "pom.xml").write_text(
        "<project><modelVersion>4.0.0</modelVersion></project>", encoding="utf-8"
    )

    data = ds.detect_stack(project)

    assert any(item["code"] == "missing-java-version" for item in data["blockers"])
    assert any(item["code"] == "missing-quarkus-version" for item in data["blockers"])


def test_mixed_namespace_imports_become_warning(fixtures, tmp_path):
    project = make_project(tmp_path, pom=fixtures / "pom-quarkus3.xml")
    source = project / "src" / "main" / "java"
    source.mkdir(parents=True)
    (source / "A.java").write_text("import jakarta.ws.rs.GET;\n", encoding="utf-8")
    (source / "B.java").write_text("import javax.ws.rs.GET;\n", encoding="utf-8")

    data = ds.detect_stack(project)

    assert any(item["code"] == "mixed-namespace-imports" for item in data["warnings"])


def test_detect_namespace_handles_supported_and_unknown_versions():
    assert ds.detect_namespace("3.33.0") == "jakarta"
    assert ds.detect_namespace("2.16.12.Final") == "javax"
    assert ds.detect_namespace("not-a-version") == "unknown"


def test_infer_execution_model_distinguishes_imperative_and_reactive():
    assert ds.infer_execution_model(["quarkus-rest-jackson"]) == "reactive-capable"
    assert ds.infer_execution_model(["quarkus-resteasy"]) == "imperative"
    assert ds.infer_execution_model([]) == "unknown"


def test_normalize_extensions_deduplicates_and_sorts():
    result = ds.normalize_extensions(
        ["quarkus-rest", "quarkus-junit5", "quarkus-rest", "quarkus-hibernate-orm-panache"]
    )

    assert result == [
        "quarkus-hibernate-orm-panache",
        "quarkus-junit5",
        "quarkus-rest",
    ]


def test_cli_writes_stack_json(fixtures, tmp_path):
    project = make_project(tmp_path, pom=fixtures / "pom-quarkus3.xml")
    output = tmp_path / "stack.json"

    code = ds.main([str(project), "--output", str(output)])

    assert code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["quarkus"]["version"] == "3.33.0"


def test_cli_returns_config_code_for_missing_descriptor(tmp_path):
    assert ds.main([str(tmp_path)]) == ds.EXIT_CONFIG


def test_cli_returns_parse_code_for_invalid_pom(tmp_path):
    project = make_project(tmp_path)
    (project / "pom.xml").write_text("<project>", encoding="utf-8")

    assert ds.main([str(project)]) == ds.EXIT_PARSE


def test_cli_strict_mode_fails_on_warnings(fixtures, tmp_path):
    project = make_project(tmp_path, pom=fixtures / "pom-quarkus3.xml")
    source = project / "src" / "main" / "java"
    source.mkdir(parents=True)
    (source / "A.java").write_text("import jakarta.ws.rs.GET;\n", encoding="utf-8")
    (source / "B.java").write_text("import javax.ws.rs.GET;\n", encoding="utf-8")

    assert ds.main([str(project), "--strict"]) == 1
