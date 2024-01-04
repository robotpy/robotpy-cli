robotpy-cli
===========

New for 2024, this package is used to execute subcommands on a RobotPy project.
This does not actually implement any subcommands itself, but provides a mechanism
to execute those subcommands.

Usage
-----

On Windows:

    py -m robotpy

On Linux/macOS:

    python -m robotpy

See the RobotPy documentation for more information.

How RobotPy subcommands are implemented
---------------------------------------

When a user runs `robotpy` or `python -m robotpy`, they are presented with
several subcommands. Each of these subcommands is implemented as a class
that is registered using python's entry point mechanism in the "robotpy"
group. The registered class must meet the following requirements:

* The docstring of the class is used when the user does --help. The first
  line is treated as the summary, and all other lines are displayed when
  the subcommand specific help is queried.

If the subcommand is a group of commands:

* The class must have a `subcommands` attribute, which is a list of
  (name, subcommand_class) tuples. The subcommand_class must meet the requirements
  for a subcommand.

If it is a subcommand that is executed:

* The constructor must take a single argument, an argparse.ArgumentParser.
  The object may register any arguments or subparsers that it needs.
* The `run` function is called when the subcommand is used by the user.
  The arguments to this function are passed in by name, and the names can
  be any of the options that the subcommand registered. There are two other
  special argument names:
  * `options` - if specified, this is the Namespace returned by parse_args
  * `robot_class` - if specified, the user's robot.py will be loaded and
    it will be inspected for their robot class, which will be passed in
    as this option
  * `main_file` - if specified, the name of the user's robot.py file. This
    is not guaranteed to exist unless robot_class is also an option.
  * `project_path` - if specified, the name of the directory that contains 
    the user's robot.py file. This is not guaranteed to exist unless robot_class
    is also an option.
