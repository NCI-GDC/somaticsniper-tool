#!/usr/bin/env python3

from textwrap import dedent

from somaticsniper_tool import utils


class HighConfidence:

    COMMAND = dedent(
        """
        perl {high_confidence}
        --snp-file {input_file}
        """
    ).strip()

    def __init__(self, high_confidence: str, input_file: str):
        self.high_confidence = high_confidence
        self.input_file = input_file

    def run(self, _utils=utils):
        cmd = self.COMMAND.format(
            high_confidence=self.high_confidence, input_file=self.input_file
        )
        _utils.run_subprocess_command(cmd)


# __END__
