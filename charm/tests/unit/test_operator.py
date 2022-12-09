# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#

"""Unit tests for Namespace Node Affinity/Charm."""

import pytest
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.testing import Harness

from charm import NamespaceNodeAffinityOperator


@pytest.fixture(scope="function")
def harness() -> Harness:
    """Create and return Harness for testing."""
    harness = Harness(NamespaceNodeAffinityOperator)

    return harness


class TestCharm:
    """Test class for NamespaceNodeAffinityOperator."""

    def test_not_leader(self, harness: Harness):
        """Test not a leader scenario."""
        harness.begin_with_initial_hooks()
        assert harness.charm.model.unit.status == WaitingStatus("Waiting for leadership")

    def test_install(self, harness: Harness):
        """Test install hook."""
        harness.set_leader(True)
        harness.begin_with_initial_hooks()
        assert False, "not yet implemented"
