from unittest.mock import mock_open, patch

import pytest
from python_workflows.helm_chart_codebase_discovery.main import (
    extract_resource_info,
    get_variable,
    process_module_files,
    resolve_variable_reference,
)


@pytest.fixture
def variables():
    return [
        {
            "nginx_version": {"default": "v1.2.3"},
            "repository_url": {"default": "https://example.com/charts"},
        }
    ]


@pytest.fixture
def terraform_config():
    return """
    resource "helm_release" "nginx_release" {
        chart      = "nginx"
        repository = "https://example.com/charts"
        version    = "${var.nginx_version}"
    }
    """


@patch("python_workflows.helm_chart_codebase_discovery.main.open", new_callable=mock_open)
def test_get_variable(mock_open):
    mock_file_content = """
    variable "CERTMANAGER_VERSION" {
        default = "v1.10.0"
    }
    """
    mock_open.return_value.read.return_value = mock_file_content
    variables = get_variable("inputs.tf")
    version = variables[0]["CERTMANAGER_VERSION"]["default"]
    assert "CERTMANAGER_VERSION" in variables[0]
    assert version == "v1.10.0"


def test_resolve_variable_reference(variables):
    resolved_value = resolve_variable_reference("${var.nginx_version}", variables)
    assert resolved_value == "v1.2.3"

    non_variable_value = resolve_variable_reference("test_string", variables)
    assert non_variable_value == "test_string"


@patch("builtins.open", new_callable=mock_open)
def test_extract_resource_info(mock_open, terraform_config, variables):
    mock_open.return_value.read.return_value = terraform_config
    resource_info = extract_resource_info("fake_terraform.tf", variables)

    assert len(resource_info) == 1
    assert "chart" in resource_info[0]
    assert "repository" in resource_info[0]
    assert "version" in resource_info[0]
    assert resource_info[0]["version"] == "v1.2.3"


@patch("builtins.open", new_callable=mock_open)
def test_process_module_files(mock_open, terraform_config, variables):
    mock_open.return_value.read.return_value = terraform_config
    module_files = ["fake_terraform.tf"]

    module_list = process_module_files(module_files, variables)

    assert module_list[0]["version"] == "v1.2.3"
    assert module_list[0]["repository"] == "https://example.com/charts"
    assert module_list[0]["chart"] == "nginx"
