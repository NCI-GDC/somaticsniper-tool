#!/usr/bin/env python3

from textwrap import dedent


class HighConfidence:

    COMMAND = dedent(
        """
        perl {script_path}
        --snp-file {input_file}
        """
    ).strip()

    script_path: str = None

    def __init__(self):
        pass

    @classmethod
    def _set_attr(cls, script_path: str):
        setattr(cls, "script_path", script_path)


# __END__
