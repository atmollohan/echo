"""Regression tests for project configuration and deployment artifacts.

These tests catch regressions when updating Python versions, dependencies,
Dockerfile, deployment configs, and workflow files.
"""

from __future__ import annotations

import sys
import unittest
from importlib.metadata import version as pkg_version
from pathlib import Path

from packaging.version import Version

from echo_run.backend import PROJECT_ROOT

REQUIRED_PACKAGES: dict[str, str] = {
    "streamlit": "1.40.0",
    "pandas": "2.2.0",
    "numpy": "1.26.0",
    "matplotlib": "3.9.0",
    "tqdm": "4.67.0",
    "papermill": "2.6.0",
}

DEV_PACKAGES: dict[str, str] = {
    "ruff": "0.7.0",
    "mypy": "1.13.0",
    "pytest": "8.0.0",
}


class PythonVersionRegressionTests(unittest.TestCase):
    def test_python_version_is_312_or_higher(self) -> None:
        self.assertGreaterEqual(
            sys.version_info[:2],
            (3, 12),
            f"Echo requires Python >=3.12, got {sys.version}",
        )


class DependencyImportRegressionTests(unittest.TestCase):
    def _check_package(self, package: str, min_version: str) -> None:
        ver = pkg_version(package)
        self.assertGreaterEqual(
            Version(ver),
            Version(min_version),
            f"{package} {ver} < min {min_version}",
        )

    def test_required_packages_import_and_meet_minimum_versions(self) -> None:
        for package, min_version in REQUIRED_PACKAGES.items():
            with self.subTest(package=package):
                self._check_package(package, min_version)

    def test_dev_packages_import_and_meet_minimum_versions(self) -> None:
        for package, min_version in DEV_PACKAGES.items():
            with self.subTest(package=package):
                self._check_package(package, min_version)

    def test_jupyter_notebook_can_be_imported(self) -> None:
        import notebook  # noqa: F401


class PyprojectTomlRegressionTests(unittest.TestCase):
    def test_pyproject_toml_is_valid(self) -> None:
        import tomllib

        path = PROJECT_ROOT / "pyproject.toml"
        self.assertTrue(path.exists())
        with open(path, "rb") as f:
            data = tomllib.load(f)
        self.assertEqual(data["project"]["name"], "echo-lab-protocol")
        self.assertEqual(data["project"]["version"], "0.2.0")


class DockerfileRegressionTests(unittest.TestCase):
    def test_dockerfile_exists_and_has_correct_base(self) -> None:
        path = PROJECT_ROOT / "Dockerfile"
        self.assertTrue(path.exists())
        content = path.read_text()
        self.assertIn("python:3.12-slim", content)

    def test_dockerfile_exposes_8501(self) -> None:
        path = PROJECT_ROOT / "Dockerfile"
        content = path.read_text()
        self.assertIn("EXPOSE 8501", content)


class DeployConfigRegressionTests(unittest.TestCase):
    def test_deploy_directory_exists(self) -> None:
        self.assertTrue((PROJECT_ROOT / "deploy").is_dir())

    def test_docker_compose_is_valid_yaml(self) -> None:
        import yaml

        path = PROJECT_ROOT / "deploy" / "docker-compose.yml"
        self.assertTrue(path.exists())
        with open(path) as f:
            data = yaml.safe_load(f)
        self.assertIn("services", data)
        self.assertIn("echo-protocol", data["services"])

    def test_docker_compose_binds_to_localhost_only(self) -> None:
        import yaml

        path = PROJECT_ROOT / "deploy" / "docker-compose.yml"
        with open(path) as f:
            data = yaml.safe_load(f)
        ports = data["services"]["echo-protocol"].get("ports", [])
        self.assertIn("127.0.0.1:8501:8501", ports)

    def test_setup_script_has_valid_shell_syntax(self) -> None:
        import subprocess

        path = PROJECT_ROOT / "deploy" / "setup.sh"
        self.assertTrue(path.exists())
        result = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"setup.sh has syntax errors:\n{result.stderr}",
        )


class WorkflowFileRegressionTests(unittest.TestCase):
    def test_docker_workflow_exists(self) -> None:
        path = PROJECT_ROOT / ".github" / "workflows" / "docker.yml"
        self.assertTrue(path.exists())

    def test_deploy_workflow_exists(self) -> None:
        path = PROJECT_ROOT / ".github" / "workflows" / "deploy.yml"
        self.assertTrue(path.exists())

    def test_pr_check_workflow_exists(self) -> None:
        path = PROJECT_ROOT / ".github" / "workflows" / "pr-check.yml"
        self.assertTrue(path.exists())

    def test_release_workflow_exists(self) -> None:
        path = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
        self.assertTrue(path.exists())


class EnvFileRegressionTests(unittest.TestCase):
    def test_env_example_exists(self) -> None:
        self.assertTrue((PROJECT_ROOT / ".env.example").exists())


if __name__ == "__main__":
    unittest.main()
