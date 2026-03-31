from argparse import Namespace

import run_test


def test_build_pytest_command_supports_public_baseline_filter():
    args = Namespace(
        mark=None,
        file=None,
        html=False,
        reruns=0,
        verbose=False,
        public_baseline=True,
    )

    command = run_test.build_pytest_command(args)

    assert command == ["pytest", "-v", "-m", "not private_env"]


def test_build_pytest_command_combines_marker_with_public_baseline():
    args = Namespace(
        mark="jsonplaceholder",
        file="tests/test_jsonplaceholder_api.py",
        html=True,
        reruns=2,
        verbose=True,
        public_baseline=True,
    )

    command = run_test.build_pytest_command(args)

    assert command[:2] == ["pytest", "-vv"]
    assert command[2:4] == ["-m", "(jsonplaceholder) and not private_env"]
    assert "tests/test_jsonplaceholder_api.py" in command
    assert "--html" in command
    assert "--reruns" in command
