import json
import os
from glob import glob
from typing import Any, Dict, List

import hcl2

TF_MODULE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../modules/")
TF_EKS_INPUTS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../templates/eks/")


def get_variable(input_file: str) -> Dict[str, Any]:
    with open(input_file, "r") as file:
        config = hcl2.load(file)
    return config.get("variable", {})


def resolve_variable_reference(value: str, variables: List[Dict[str, Dict[str, Any]]]) -> str:
    if value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1].strip().split(".")[1]

        for var in variables:
            for key, val in var.items():
                if key.lower() == var_name.lower():
                    return val.get("default", value)
        return value
    return value


def extract_resource_info(terraform_file: str, variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    with open(terraform_file, "r") as file:
        terraform_config = hcl2.load(file)

    resources = terraform_config.get("resource", [])
    resource_info: List[Dict[str, Any]] = []

    for resource in resources:
        if "helm_release" in resource:
            helm_releases = resource["helm_release"]
            for instance_name, instance_attrs in helm_releases.items():
                if all(key in instance_attrs for key in ["chart", "repository", "version"]):
                    chart = instance_attrs["chart"]
                    repository = instance_attrs["repository"]
                    version = resolve_variable_reference(instance_attrs["version"], variables)  # Resolve version
                    resource_info.append({"chart": chart, "repository": repository, "version": version})

    return resource_info


def process_module_files(module_files: List[str], variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    module_list: List[Dict[str, Any]] = []

    for file in module_files:
        data = extract_resource_info(file, variables)
        module_list.extend(data)

    return module_list


def main() -> None:
    module_files: List[str] = []

    eks_base_files = glob(f"{TF_MODULE_PATH}/eks_base/*.tf")
    post_config_files = glob(f"{TF_MODULE_PATH}/eks_post_config/*.tf")
    module_files.extend(eks_base_files)
    module_files.extend(post_config_files)

    eks_inputs_files = f"{TF_EKS_INPUTS_PATH}/inputs.tf"
    variables = get_variable(input_file=eks_inputs_files)

    output_list = process_module_files(module_files, variables)
    print(json.dumps(output_list, indent=2))


if __name__ == "__main__":
    main()
