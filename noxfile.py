# -*- coding: utf-8 -*-
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import difflib
import filecmp
import os
import pathlib
import re
import shutil
import tempfile
from typing import Dict, List
import warnings

import nox

BLACK_VERSION = "black==22.3.0"
ISORT_VERSION = "isort==5.12.0"
LINT_PATHS = ["docs", "bigframes", "tests", "noxfile.py", "setup.py"]

DEFAULT_PYTHON_VERSION = "3.10"

UNIT_TEST_PYTHON_VERSIONS = ["3.9", "3.10", "3.11"]
UNIT_TEST_STANDARD_DEPENDENCIES = [
    "mock",
    "asyncmock",
    "pytest",
    "pytest-cov",
    "pytest-asyncio",
]
UNIT_TEST_EXTERNAL_DEPENDENCIES: List[str] = []
UNIT_TEST_LOCAL_DEPENDENCIES: List[str] = []
UNIT_TEST_DEPENDENCIES: List[str] = []
UNIT_TEST_EXTRAS: List[str] = []
UNIT_TEST_EXTRAS_BY_PYTHON: Dict[str, List[str]] = {}

SYSTEM_TEST_PYTHON_VERSIONS = ["3.9", "3.10", "3.11"]
SYSTEM_TEST_STANDARD_DEPENDENCIES = [
    "jinja2",
    "mock",
    "openpyxl",
    "pytest",
    "pytest-cov",
    "pytest-retry",
    "pytest-timeout",
    "pytest-xdist",
    "google-cloud-testutils",
    "tabulate",
    "xarray",
]
SYSTEM_TEST_EXTERNAL_DEPENDENCIES = [
    "google-cloud-bigquery",
]
SYSTEM_TEST_LOCAL_DEPENDENCIES: List[str] = []
SYSTEM_TEST_DEPENDENCIES: List[str] = []
SYSTEM_TEST_EXTRAS: List[str] = ["tests"]
SYSTEM_TEST_EXTRAS_BY_PYTHON: Dict[str, List[str]] = {}

CURRENT_DIRECTORY = pathlib.Path(__file__).parent.absolute()

# Sessions are executed in the order so putting the smaller sessions
# ahead to fail fast at presubmit running.
# 'docfx' is excluded since it only needs to run in 'docs-presubmit'
nox.options.sessions = [
    "lint",
    "lint_setup_py",
    "mypy",
    "format",
    "docs",
    "unit",
    "unit_prerelease",
    "system",
    "system_noextras",
    "system_prerelease",
    "cover",
    "third_party_notices",
]

# Error if a python version is missing
nox.options.error_on_missing_interpreters = True


@nox.session(python=DEFAULT_PYTHON_VERSION)
def lint(session):
    """Run linters.

    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    session.install("flake8", BLACK_VERSION)
    session.run(
        "black",
        "--check",
        *LINT_PATHS,
    )
    session.run("flake8", "bigframes", "tests")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def blacken(session):
    """Run black. Format code to uniform standard."""
    session.install(BLACK_VERSION)
    session.run(
        "black",
        *LINT_PATHS,
    )


@nox.session(python=DEFAULT_PYTHON_VERSION)
def format(session):
    """
    Run isort to sort imports. Then run black
    to format code to uniform standard.
    """
    session.install(BLACK_VERSION, ISORT_VERSION)
    # Use the --fss option to sort imports using strict alphabetical order.
    # See https://pycqa.github.io/isort/docs/configuration/options.html#force-sort-within-sections
    session.run(
        "isort",
        *LINT_PATHS,
    )
    session.run(
        "black",
        *LINT_PATHS,
    )


@nox.session(python=DEFAULT_PYTHON_VERSION)
def lint_setup_py(session):
    """Verify that setup.py is valid (including RST check)."""
    session.install("docutils", "pygments")
    session.run("python", "setup.py", "check", "--restructuredtext", "--strict")


def install_unittest_dependencies(session, *constraints):
    standard_deps = UNIT_TEST_STANDARD_DEPENDENCIES + UNIT_TEST_DEPENDENCIES
    session.install(*standard_deps, *constraints)

    if UNIT_TEST_EXTERNAL_DEPENDENCIES:
        warnings.warn(
            "'unit_test_external_dependencies' is deprecated. Instead, please "
            "use 'unit_test_dependencies' or 'unit_test_local_dependencies'.",
            DeprecationWarning,
        )
        session.install(*UNIT_TEST_EXTERNAL_DEPENDENCIES, *constraints)

    if UNIT_TEST_LOCAL_DEPENDENCIES:
        session.install(*UNIT_TEST_LOCAL_DEPENDENCIES, *constraints)

    if UNIT_TEST_EXTRAS_BY_PYTHON:
        extras = UNIT_TEST_EXTRAS_BY_PYTHON.get(session.python, [])
    elif UNIT_TEST_EXTRAS:
        extras = UNIT_TEST_EXTRAS
    else:
        extras = []

    if extras:
        session.install("-e", f".[{','.join(extras)}]", *constraints)
    else:
        session.install("-e", ".", *constraints)


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS)
def unit(session):
    """Run the unit test suite."""
    constraints_path = str(
        CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    )
    install_unittest_dependencies(session, "-c", constraints_path)

    # Run py.test against the unit tests.
    tests_path = os.path.join("tests", "unit")
    session.run(
        "py.test",
        "--quiet",
        f"--junitxml=unit_{session.python}_sponge_log.xml",
        "--cov=bigframes",
        f"--cov={tests_path}",
        "--cov-append",
        "--cov-config=.coveragerc",
        "--cov-report=term-missing",
        "--cov-fail-under=0",
        tests_path,
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON_VERSION)
def mypy(session):
    """Run type checks with mypy."""
    session.install("-e", ".")

    # Just install the dependencies' type info directly, since "mypy --install-types"
    # might require an additional pass.
    deps = (
        set(
            [
                "mypy",
                "pandas-stubs",
                "types-protobuf",
                "types-python-dateutil",
                "types-requests",
                "types-setuptools",
            ]
        )
        | set(SYSTEM_TEST_STANDARD_DEPENDENCIES)
        | set(UNIT_TEST_STANDARD_DEPENDENCIES)
    )

    session.install(*deps)
    shutil.rmtree(".mypy_cache", ignore_errors=True)
    session.run(
        "mypy",
        "bigframes",
        os.path.join("tests", "system"),
        os.path.join("tests", "unit"),
        "--explicit-package-bases",
        '--exclude="^third_party"',
    )


def install_systemtest_dependencies(session, install_test_extra, *constraints):
    # Use pre-release gRPC for system tests.
    # Exclude version 1.49.0rc1 which has a known issue.
    # See https://github.com/grpc/grpc/pull/30642
    session.install("--pre", "grpcio!=1.49.0rc1")

    session.install(*SYSTEM_TEST_STANDARD_DEPENDENCIES, *constraints)

    if SYSTEM_TEST_EXTERNAL_DEPENDENCIES:
        session.install(*SYSTEM_TEST_EXTERNAL_DEPENDENCIES, *constraints)

    if SYSTEM_TEST_LOCAL_DEPENDENCIES:
        session.install("-e", *SYSTEM_TEST_LOCAL_DEPENDENCIES, *constraints)

    if SYSTEM_TEST_DEPENDENCIES:
        session.install("-e", *SYSTEM_TEST_DEPENDENCIES, *constraints)

    if install_test_extra and SYSTEM_TEST_EXTRAS_BY_PYTHON:
        extras = SYSTEM_TEST_EXTRAS_BY_PYTHON.get(session.python, [])
    elif install_test_extra and SYSTEM_TEST_EXTRAS:
        extras = SYSTEM_TEST_EXTRAS
    else:
        extras = []

    if extras:
        session.install("-e", f".[{','.join(extras)}]", *constraints)
    else:
        session.install("-e", ".", *constraints)


def run_system(
    session,
    prefix_name,
    test_folder,
    *,
    check_cov=False,
    install_test_extra=True,
    print_duration=False,
):
    """Run the system test suite."""
    constraints_path = str(
        CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    )

    # Check the value of `RUN_SYSTEM_TESTS` env var. It defaults to true.
    if os.environ.get("RUN_SYSTEM_TESTS", "true") == "false":
        session.skip("RUN_SYSTEM_TESTS is set to false, skipping")
    # Install pyopenssl for mTLS testing.
    if os.environ.get("GOOGLE_API_USE_CLIENT_CERTIFICATE", "false") == "true":
        session.install("pyopenssl")

    install_systemtest_dependencies(session, install_test_extra, "-c", constraints_path)

    # Run py.test against the system tests.
    pytest_cmd = [
        "py.test",
        "--quiet",
        "-n 20",
        # Any indivisual test taking longer than 10 mins will be terminated.
        "--timeout=600",
        f"--junitxml={prefix_name}_{session.python}_sponge_log.xml",
    ]
    if print_duration:
        pytest_cmd.extend(
            [
                "--durations=0",
            ]
        )
    if check_cov:
        pytest_cmd.extend(
            [
                "--cov=bigframes",
                f"--cov={test_folder}",
                "--cov-append",
                "--cov-config=.coveragerc",
                "--cov-report=term-missing",
                "--cov-fail-under=0",
            ]
        )
    session.run(
        *pytest_cmd,
        test_folder,
        *session.posargs,
    )


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS)
def system(session):
    """Run the system test suite."""
    run_system(
        session=session,
        prefix_name="system",
        test_folder=os.path.join("tests", "system", "small"),
        check_cov=True,
    )


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS[-1])
def system_noextras(session):
    """Run the system test suite."""
    run_system(
        session=session,
        prefix_name="system_noextras",
        test_folder=os.path.join("tests", "system", "small"),
        install_test_extra=False,
    )


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS[-1])
def e2e(session):
    """Run the large tests in system test suite."""
    run_system(
        session=session,
        prefix_name="e2e",
        test_folder=os.path.join("tests", "system", "large"),
        print_duration=True,
    )


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS)
def samples(session):
    """Run the samples test suite."""

    constraints_path = str(
        CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    )

    # TODO(swast): Use `requirements.txt` files from the samples directories to
    # test samples.
    install_test_extra = True
    install_systemtest_dependencies(session, install_test_extra, "-c", constraints_path)

    session.run(
        "py.test",
        "samples",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON_VERSION)
def cover(session):
    """Run the final coverage report.

    This outputs the coverage report aggregating coverage from the unit
    test runs (not system test runs), and then erases coverage data.
    """
    session.install("coverage", "pytest-cov")
    session.run("coverage", "report", "--show-missing", "--fail-under=90")

    session.run("coverage", "erase")


@nox.session(python="3.9")
def docs(session):
    """Build the docs for this library."""

    session.install("-e", ".")
    session.install(
        "sphinx==4.0.1",
        "alabaster",
        "recommonmark",
    )

    shutil.rmtree(os.path.join("docs", "_build"), ignore_errors=True)
    session.run(
        "sphinx-build",
        "-W",  # warnings as errors
        "-T",  # show full traceback on exception
        "-N",  # no colors
        "-b",
        "html",
        "-d",
        os.path.join("docs", "_build", "doctrees", ""),
        os.path.join("docs", ""),
        os.path.join("docs", "_build", "html", ""),
    )


@nox.session(python="3.9")
def docfx(session):
    """Build the docfx yaml files for this library."""

    session.install("-e", ".")
    session.install(
        "sphinx==4.0.1",
        "alabaster",
        "recommonmark",
        "gcp-sphinx-docfx-yaml",
    )

    shutil.rmtree(os.path.join("docs", "_build"), ignore_errors=True)
    session.run(
        "sphinx-build",
        "-T",  # show full traceback on exception
        "-N",  # no colors
        "-D",
        (
            "extensions=sphinx.ext.autodoc,"
            "sphinx.ext.autosummary,"
            "docfx_yaml.extension,"
            "sphinx.ext.intersphinx,"
            "sphinx.ext.coverage,"
            "sphinx.ext.napoleon,"
            "sphinx.ext.todo,"
            "sphinx.ext.viewcode,"
            "recommonmark"
        ),
        "-b",
        "html",
        "-d",
        os.path.join("docs", "_build", "doctrees", ""),
        os.path.join("docs", ""),
        os.path.join("docs", "_build", "html", ""),
    )


def prerelease(session, tests_path):
    constraints_path = str(
        CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    )

    # PyArrow prerelease packages are published to an alternative PyPI host.
    # https://arrow.apache.org/docs/python/install.html#installing-nightly-packages
    session.install(
        "--extra-index-url",
        "https://pypi.fury.io/arrow-nightlies/",
        "--prefer-binary",
        "--pre",
        "--upgrade",
        "pyarrow",
    )
    session.install(
        "--extra-index-url",
        "https://pypi.anaconda.org/scipy-wheels-nightly/simple",
        "--prefer-binary",
        "--pre",
        "--upgrade",
        "pandas",
    )
    session.install(
        "--upgrade",
        "-e",  # Use -e so that py.typed file is included.
        "git+https://github.com/ibis-project/ibis.git#egg=ibis-framework",
    )
    # Workaround https://github.com/googleapis/python-db-dtypes-pandas/issues/178
    session.install("--no-deps", "db-dtypes")

    # Workaround to install pandas-gbq >=0.15.0, which is required by test only.
    session.install("--no-deps", "pandas-gbq")

    session.install(
        *set(UNIT_TEST_STANDARD_DEPENDENCIES + SYSTEM_TEST_STANDARD_DEPENDENCIES),
        "-c",
        constraints_path,
    )

    # Because we test minimum dependency versions on the minimum Python
    # version, the first version we test with in the unit tests sessions has a
    # constraints file containing all dependencies and extras.
    with open(
        CURRENT_DIRECTORY
        / "testing"
        / f"constraints-{UNIT_TEST_PYTHON_VERSIONS[0]}.txt",
        encoding="utf-8",
    ) as constraints_file:
        constraints_text = constraints_file.read()

    # Ignore leading whitespace and comment lines.
    already_installed = frozenset(
        ("db-dtypes", "pandas", "pyarrow", "ibis-framework", "pandas-gbq")
    )
    deps = [
        match.group(1)
        for match in re.finditer(
            r"^\s*(\S+)(?===\S+)", constraints_text, flags=re.MULTILINE
        )
        if match.group(1) not in already_installed
    ]

    # We use --no-deps to ensure that pre-release versions aren't overwritten
    # by the version ranges in setup.py.
    session.install(*deps)
    session.install("--no-deps", "-e", ".")

    # Print out prerelease package versions.
    session.run("python", "-m", "pip", "freeze")

    # Run py.test against the tests.
    session.run(
        "py.test",
        "--quiet",
        "-n 20",
        # Any indivisual test taking longer than 10 mins will be terminated.
        "--timeout=600",
        f"--junitxml={os.path.split(tests_path)[-1]}_prerelease_{session.python}_sponge_log.xml",
        "--cov=bigframes",
        f"--cov={tests_path}",
        "--cov-append",
        "--cov-config=.coveragerc",
        "--cov-report=term-missing",
        "--cov-fail-under=0",
        tests_path,
        *session.posargs,
    )


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS[-1])
def unit_prerelease(session):
    """Run the unit test suite with prerelease dependencies."""
    prerelease(session, os.path.join("tests", "unit"))


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS[-1])
def system_prerelease(session):
    """Run the system test suite with prerelease dependencies."""
    prerelease(session, os.path.join("tests", "system", "small"))


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS)
def notebook(session):
    session.install("-e", ".")
    session.install("pytest", "pytest-xdist", "nbmake")

    # TODO(shobs, b/281857892): Have all the notebooks working
    notebooks = [
        "00 - Summary.ipynb",
    ]
    notebooks = [os.path.join("notebooks", nb) for nb in notebooks]

    # For some reason nbmake exits silently with "no tests ran" message if
    # one of the notebook paths supplied does not exist. Let's make sure that
    # each path exists
    for nb in notebooks:
        assert os.path.exists(nb), nb
    session.run("py.test", "-nauto", "--nbmake", "--nbmake-timeout=600", *notebooks)


@nox.session(python=SYSTEM_TEST_PYTHON_VERSIONS[-1])
def third_party_notices(session):
    session.install("-e", ".")
    session.install("pip-licenses")

    notices_file = "THIRD_PARTY_NOTICES"
    generator_script = "tools/generate_third_party_notices.py"
    _, notices_file_backup = tempfile.mkstemp()

    try:
        shutil.copy(notices_file, notices_file_backup)

        # Generate the latest notices
        session.run("python3", generator_script)

        # Assert that it is unchanged
        if not filecmp.cmp(notices_file_backup, notices_file):
            # Print the diff and fail the test
            with open(notices_file_backup) as f_orig, open(notices_file) as f_new:
                print(
                    "".join(
                        difflib.unified_diff(
                            f_orig.readlines(),
                            f_new.readlines(),
                            fromfile=notices_file_backup,
                            tofile=notices_file,
                        )
                    )
                )

            raise ValueError(
                f"{notices_file} is not up to date. Run {generator_script} to update it."
            )
    finally:
        # TODO(shobs): Currently we are removing the original file and letting
        # file be modified in place, so that developer can easily  review and
        # commit the change. However, reconsider this to be more consistent with
        # other sessions, such as 'lint' which simply fails if any modifications
        # are needed but doesn't actually make the modification.
        os.remove(notices_file_backup)
