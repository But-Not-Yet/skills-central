"""Isolated-HERMES_HOME probe template — production boot chain + sandbox guards.

Copy, then edit: HERMES_AGENT root if needed; the fake plugin directory name
and its register() body; the package-under-test import; the scenario asserts.

Two boot-order rules (both learned the hard way):
  1. PM dependency activation must run BEFORE any hermes import — third-party
deps come from the PM generation, not the interpreter. Otherwise:
     ModuleNotFoundError: No module named 'ruamel' (hermes_yaml hard-imports it)
  2. The sandbox HERMES_HOME must be set BEFORE the first get_hermes_home() call
(it reads env per call, no cache — verified).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERMES_AGENT = "/home/alonzo/.hermes/hermes-agent"

# 1) Production boot step: PM dependency selection BEFORE any hermes import.
sys.path.insert(0, HERMES_AGENT)
from pm.environments import activate_dependencies  # noqa: E402

activate_dependencies(Path(HERMES_AGENT))

# 2) Sandbox home + fake plugin (edit the directory name / body for your case).
td = tempfile.mkdtemp(prefix="hermes_probe_")
os.environ["HERMES_HOME"] = td
os.environ.pop("TIERED_INNER", None)  # drop service env that leaks into shells
plug = os.path.join(td, "plugins", "hermes-lcm-x")
os.makedirs(plug)
with open(os.path.join(plug, "__init__.py"), "w", encoding="utf-8") as fh:
    fh.write('''
from agent.context_engine import ContextEngine
class FakeEngine(ContextEngine):
    @property
    def name(self):
        return "lcm-x"
    def update_from_response(self, usage):
        pass
    def should_compress(self, prompt_tokens=None):
        return False
    def compress(self, messages, current_tokens=None, focus_topic=None, force=False):
        return messages
def register(ctx):
    ctx.register_context_engine(FakeEngine())
''')

sys.path.insert(0, os.path.expanduser("~/.hermes/plugins"))  # package under test
from hermes_constants import get_hermes_home  # noqa: E402

# <-- import your module under test here, e.g.:
# from tiered.engine import TieredEngine

home = str(get_hermes_home())
assert home == td, f"ABORT: HERMES_HOME not sandboxed ({home})"

# <-- run the load / scenario here, e.g.: eng = TieredEngine.create()

loaded_from_sandbox = [
    getattr(m, "__file__", "")
    for m in sys.modules.values()
    if getattr(m, "__file__", None) and td in str(getattr(m, "__file__", ""))
]
assert loaded_from_sandbox, "ABORT: sandbox module was NOT the one loaded"
print("sandbox modules loaded:", loaded_from_sandbox[:2])

shutil.rmtree(td)
print("PROBE DONE")
