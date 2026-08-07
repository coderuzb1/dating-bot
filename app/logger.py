import logging
import sys

import colorlog


def setup_logger() -> None:
    handler = colorlog.StreamHandler(sys.stdout)

    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
    )
