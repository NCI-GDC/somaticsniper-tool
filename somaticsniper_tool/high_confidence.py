#!/usr/bin/env python3
import logging
from textwrap import dedent

from somaticsniper_tool import utils

logger = logging.getLogger(__name__)


class HighConfidence:

    COMMAND = dedent(
        """
        perl {high_confidence}
        --snp-file {input_file}
        """
    ).strip()

    def __init__(self, timeout, high_confidence: str, input_file: str):
        self.timeout = timeout
        self.high_confidence = high_confidence
        self.input_file = input_file

    def run(self, _utils=utils):
        cmd = self.COMMAND.format(
            high_confidence=self.high_confidence, input_file=self.input_file
        )
        popen_return = _utils.run_subprocess_command(cmd, self.timeout)
        logger.info(cmd)
        logger.debug(popen_return.stdout)
        logger.debug(popen_return.stderr)


# __END__
