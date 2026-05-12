from pathlib import Path

from pytest_bdd import scenarios

from tests.bdd.given_steps import *  # noqa: F403, F401
from tests.bdd.when_steps import *  # noqa: F403, F401
from tests.bdd.then_steps import *  # noqa: F403, F401

scenarios(Path(__file__).resolve().parent / "features")
