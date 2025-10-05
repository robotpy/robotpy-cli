import sys
import textwrap

import pytest

from robotpy import main


class DummyWpilib:
    class RobotBase:
        pass


@pytest.fixture(autouse=True)
def mock_wpilib(monkeypatch):
    monkeypatch.setitem(sys.modules, "wpilib", DummyWpilib)


def test_load_robot_class_exact_case(tmp_path, monkeypatch, capsys):
    # create correct-case file
    robot_py = tmp_path / "robot.py"
    robot_py.write_text(
        textwrap.dedent(
            """
        import wpilib
        class MyRobot(wpilib.RobotBase):
            pass                                 
    """
        )
    )

    monkeypatch.setattr(main, "robot_py_path", robot_py)

    # Should pass (exact case)
    main._load_robot_class()


def test_load_robot_class_wrong_case(tmp_path, monkeypatch, capsys):
    robot_py = tmp_path / "robot.py"
    Robot_py = tmp_path / "Robot.py"
    Robot_py.write_text(
        textwrap.dedent(
            """
        import wpilib
        class MyRobot(wpilib.RobotBase):
            pass
    """
        )
    )

    case_insensitive_fs = robot_py.exists()

    monkeypatch.setattr(main, "robot_py_path", robot_py)

    with pytest.raises(SystemExit):
        main._load_robot_class()
    err = capsys.readouterr().err

    if case_insensitive_fs:
        assert "must be robot.py" in err
    else:
        assert "does not exist" in err
