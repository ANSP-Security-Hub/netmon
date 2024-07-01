import os
import sys

from dotenv import load_dotenv

load_dotenv()

VERBOSE = bool(os.getenv("VERBOSE"))


def log_on_verbose(error):
    if VERBOSE:
        print(error)  # , flush=True, file=sys.stderr)
