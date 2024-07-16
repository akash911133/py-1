import json
from unittest.mock import mock_open, patch

import pytest

from python_workflows.helm_chart_codebase_discovery.main import (
    get_variable,
    resolve_variable_reference,
    load_chart_yaml,
    extract_resource_info,
    process_module_files,
)


# Mock Data
mock_chart_yaml = """
charts:
  - chart: nginx
    repository: https://charts.helm.sh/stable
"""

mock_terraform_file = """
resource "helm_release" "nginx" {
  name    = "nginx"
  version = "${var.nginx_version}"
}
"""

mock_variables = {
    "variable": {
        "nginx_version": {
            "default": "1.2.3"
        }
    }
}


# Helper Functions
def mock_open_helper(file_data):
    m_open = mock_open(read_data=file_data)
    m_open.return_value.__iter__ = lambda self: iter(self.readline, '')
    return m_open


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


def test_resolve_variable_reference():
    variables = [{"nginx_version": {"default": "1.2.3"}}]
    result = resolve_variable_reference("${var.nginx_version}", variables)
    assert result == {"resolved_value": "1.2.3", "variable_name": "nginx_version"}

    result = resolve_variable_reference("1.2.3", variables)
    assert result == "1.2.3"


def test_load_chart_yaml():
    with patch("builtins.open", mock_open_helper(mock_chart_yaml)):
        result = load_chart_yaml("dummy_chart.yaml")
        assert result == [{"chart": "nginx", "repository": "https://charts.helm.sh/stable"}]


def test_extract_resource_info():
    with patch("builtins.open", mock_open_helper(mock_terraform_file)) as m_terraform, \
            patch("python_workflows.helm_chart_codebase_discovery.main.load_chart_yaml", return_value=[{"chart": "nginx", "repository": "https://charts.helm.sh/stable"}]):

        result = extract_resource_info("dummy_file.tf", "dummy_chart.yaml", [{"nginx_version": {"default": "1.2.3"}}])
        expected = [{
            "chart": "nginx",
            "repository": "https://charts.helm.sh/stable",
            "version": "1.2.3",
            "variable_name": "nginx_version"
        }]
        assert result == expected


def test_process_module_files():
    with patch("builtins.open", mock_open_helper(mock_terraform_file)), \
         patch("python_workflows.helm_chart_codebase_discovery.main.load_chart_yaml", return_value=[{"chart": "nginx", "repository": "https://charts.helm.sh/stable"}]), \
         patch("python_workflows.helm_chart_codebase_discovery.main.extract_resource_info", return_value=[{
             "chart": "nginx",
             "repository": "https://charts.helm.sh/stable",
             "version": "1.2.3",
             "variable_name": "nginx_version"
         }]):

        result = process_module_files(["dummy_file.tf"], "dummy_chart.yaml", [{"nginx_version": {"default": "1.2.3"}}])
        expected = [{
            "chart": "nginx",
            "repository": "https://charts.helm.sh/stable",
            "version": "1.2.3",
            "variable_name": "nginx_version"
        }]
        assert result == expected


if __name__ == "__main__":
    pytest.main()



# import json
# from unittest.mock import mock_open, patch
#
# import pytest
#
# from python_workflows.helm_chart_codebase_discovery.main import (
#     get_variable,
#     resolve_variable_reference,
#     load_chart_yaml,
#     extract_resource_info,
#     process_module_files,
# )
#
#
# # Mock Data
# mock_chart_yaml = """
# charts:
#   - chart: nginx
#     repository: https://charts.helm.sh/stable
# """
#
# mock_terraform_file = """
# resource "helm_release" "nginx" {
#   name    = "nginx"
#   version = "${var.nginx_version}"
# }
# """
#
# mock_variables = {
#     "variable": {
#         "nginx_version": {
#             "default": "1.2.3"
#         }
#     }
# }
#
#
# # Helper Functions
# def mock_open_helper(file_data):
#     m_open = mock_open(read_data=file_data)
#     m_open.return_value.__iter__ = lambda self: iter(self.readline, '')
#     return m_open
#
#
# # Tests
# def test_get_variable():
#     with patch("builtins.open", mock_open_helper(json.dumps(mock_variables))):
#         result = get_variable("dummy_file.tf")
#         assert result == mock_variables["variable"]
#
#
# def test_resolve_variable_reference():
#     variables = [{"nginx_version": {"default": "1.2.3"}}]
#     result = resolve_variable_reference("${var.nginx_version}", variables)
#     assert result == {"resolved_value": "1.2.3", "variable_name": "nginx_version"}
#
#     result = resolve_variable_reference("1.2.3", variables)
#     assert result == "1.2.3"
#
#
# def test_load_chart_yaml():
#     with patch("builtins.open", mock_open_helper(mock_chart_yaml)):
#         result = load_chart_yaml("dummy_chart.yaml")
#         assert result == [{"chart": "nginx", "repository": "https://charts.helm.sh/stable"}]
#
#
# def test_extract_resource_info():
#     with patch("builtins.open", mock_open_helper(mock_terraform_file)) as m_terraform, \
#             patch("python_workflows.helm_chart_codebase_discovery.main.load_chart_yaml", return_value=[{"chart": "nginx", "repository": "https://charts.helm.sh/stable"}]):
#
#         result = extract_resource_info("dummy_file.tf", "dummy_chart.yaml", [{"nginx_version": {"default": "1.2.3"}}])
#         expected = [{
#             "chart": "nginx",
#             "repository": "https://charts.helm.sh/stable",
#             "version": "1.2.3",
#             "variable_name": "nginx_version"
#         }]
#         assert result == expected
#
#
# def test_process_module_files():
#     with patch("builtins.open", mock_open_helper(mock_terraform_file)), \
#          patch("python_workflows.helm_chart_codebase_discovery.main.load_chart_yaml", return_value=[{"chart": "nginx", "repository": "https://charts.helm.sh/stable"}]), \
#          patch("python_workflows.helm_chart_codebase_discovery.main.extract_resource_info", return_value=[{
#              "chart": "nginx",
#              "repository": "https://charts.helm.sh/stable",
#              "version": "1.2.3",
#              "variable_name": "nginx_version"
#          }]):
#
#         result = process_module_files(["dummy_file.tf"], "dummy_chart.yaml", [{"nginx_version": {"default": "1.2.3"}}])
#         expected = [{
#             "chart": "nginx",
#             "repository": "https://charts.helm.sh/stable",
#             "version": "1.2.3",
#             "variable_name": "nginx_version"
#         }]
#         assert result == expected
#
#
# if __name__ == "__main__":
#     pytest.main()
