import argparse
import os
from pathlib import Path


def file_path(string):
    """Checks that the string is a valid path to a file."""
    if os.path.isfile(string):
        return Path(string)
    else:
        raise argparse.ArgumentTypeError(f"{string} is not a valid path to a file")
