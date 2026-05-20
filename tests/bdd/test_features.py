from __future__ import annotations

from pytest_bdd import scenarios

from tests.bdd.given_steps import *  # noqa
from tests.bdd.when_steps import *  # noqa
from tests.bdd.then_steps import *  # noqa

scenarios(str(Path(__file__).resolve().parent / "features"))
