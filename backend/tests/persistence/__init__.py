from pathlib import Path
import unittest


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    return loader.discover(str(Path(__file__).parent), pattern="test_*.py")
