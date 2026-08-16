import logging

import pytest

from robotpy import main


@pytest.fixture(autouse=True)
def restore_global_state():
    handlers = logging.root.handlers[:]
    level = logging.root.level
    robot_py_path = main.robot_py_path
    yield
    logging.root.handlers[:] = handlers
    logging.root.setLevel(level)
    main.robot_py_path = robot_py_path


def test_command_arguments_are_dispatched(tmp_path):
    received = {}

    class Command:
        def __init__(self, parser):
            parser.add_argument("--count", required=True, type=int)

        def run(self, count):
            received["count"] = count

    exit_code = main._run(
        ["--main", str(tmp_path), "sample", "--count", "3"],
        [("sample", Command)],
    )

    assert exit_code == 0
    assert received == {"count": 3}


def test_run_parameter_without_parser_argument_uses_default():
    received = []

    class Command:
        def __init__(self, parser):
            pass

        def run(self, mode="default-mode"):
            received.append(mode)

    exit_code = main._run(["sample"], [("sample", Command)])

    assert exit_code == 0
    assert received == ["default-mode"]


def test_nested_subcommand_is_dispatched():
    received = []

    class Echo:
        """Echo a value."""

        def __init__(self, parser):
            parser.add_argument("value")

        def run(self, value):
            received.append(value)

    class Tools:
        """Tool commands."""

        subcommands = [("echo", Echo)]

    exit_code = main._run(["tools", "echo", "hello"], [("tools", Tools)])

    assert exit_code == 0
    assert received == ["hello"]


def test_missing_top_level_command_prints_root_help(capsys):
    class Command:
        def __init__(self, parser):
            pass

        def run(self):
            raise AssertionError("command should not run")

    with pytest.raises(SystemExit) as excinfo:
        main._run([], [("sample", Command)])

    assert excinfo.value.code == 1
    output = capsys.readouterr().out
    assert "usage:" in output
    assert "sample" in output


def test_missing_nested_subcommand_prints_group_help(capsys):
    class Echo:
        """Echo a value."""

        def __init__(self, parser):
            pass

        def run(self):
            raise AssertionError("command should not run")

    class Tools:
        """Tool commands."""

        subcommands = [("echo", Echo)]

    with pytest.raises(SystemExit) as excinfo:
        main._run(["tools"], [("tools", Tools)])

    assert excinfo.value.code == 1
    output = capsys.readouterr().out
    assert "usage:" in output
    assert "echo" in output


def test_special_arguments_are_injected(tmp_path):
    received = {}

    class Command:
        def __init__(self, parser):
            parser.add_argument("--label", required=True)

        def run(
            self,
            label,
            options,
            main_file,
            project_path,
            load_robot_class,
        ):
            received.update(
                label=label,
                verbose=options.verbose,
                ignore_plugin_errors=options.ignore_plugin_errors,
                main_file=main_file,
                project_path=project_path,
                load_robot_class=load_robot_class,
            )

    exit_code = main._run(
        [
            "--main",
            str(tmp_path),
            "--verbose",
            "--ignore-plugin-errors",
            "inspect",
            "--label",
            "robot",
        ],
        [("inspect", Command)],
    )

    assert exit_code == 0
    assert received == {
        "label": "robot",
        "verbose": True,
        "ignore_plugin_errors": True,
        "main_file": tmp_path / "robot.py",
        "project_path": tmp_path,
        "load_robot_class": main._load_robot_class,
    }


@pytest.mark.parametrize(
    ("return_value", "expected_exit_code"),
    [(None, 0), (True, 0), (False, 1), (7, 7)],
)
def test_command_return_value_is_normalized(return_value, expected_exit_code):
    class Command:
        def __init__(self, parser):
            pass

        def run(self):
            return return_value

    assert main._run(["sample"], [("sample", Command)]) == expected_exit_code


def test_positional_only_run_argument_is_rejected():
    class Command:
        def __init__(self, parser):
            pass

        def run(self, value, /):
            raise AssertionError("command should not run")

    with pytest.raises(
        ValueError,
        match="subcommands may only have keyword or normal arguments",
    ):
        main._run(["sample"], [("sample", Command)])


def test_no_registered_commands_is_an_argument_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main._run([], [])

    assert excinfo.value.code == 2
    assert "No entry points defined" in capsys.readouterr().err
