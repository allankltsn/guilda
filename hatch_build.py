"""Hatch build hook: embeds the payload allowlist into the wheel under guilda/_data."""
from pathlib import Path
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class PayloadBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        root = Path(self.root)
        sys.path.insert(0, str(root))
        from guilda import payload

        build_data["force_include"].update(payload.wheel_force_include(root))
