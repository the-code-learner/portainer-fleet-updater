import tempfile
import unittest

from fleet_updater.portainer import reported_agent_version
from fleet_updater.state import SettingsStore


class AgentVersionTests(unittest.TestCase):
    def test_nested_agent_version(self):
        self.assertEqual(reported_agent_version({"Agent": {"Version": "2.33.0"}}), "2.33.0")

    def test_flat_agent_version(self):
        self.assertEqual(reported_agent_version({"AgentVersion": "2.32.1"}), "2.32.1")


class SettingsStoreTests(unittest.TestCase):
    def test_managed_stack_ids_are_persisted_and_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SettingsStore(tmp)
            self.assertEqual(store.managed_stack_ids(), set())
            saved = store.set_managed_stack_ids([3, 2, 3, 1])
            self.assertEqual(saved, [1, 2, 3])
            self.assertEqual(store.managed_stack_ids(), {1, 2, 3})


if __name__ == "__main__":
    unittest.main()
