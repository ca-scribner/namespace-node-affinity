# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#

"""Unit tests for Namespace Node Affinity/Charm."""
from base64 import b64encode

import pytest
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.testing import Harness

from charm import NamespaceNodeAffinityOperator, TAGGED_IMAGE, K8S_RESOURCE_FILES


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

    def test_context(self, harness: Harness):
        """Test context property."""
        model_name = "test-model"
        image = TAGGED_IMAGE
        ca_bundle = "abc123"

        harness.set_model_name(model_name)

        harness.begin()
        harness.charm._stored.ca = ca_bundle

        expected_context = {
            "app_name": "namespace-node-affinity",  # Can we set this somehow?
            "namespace": model_name,
            "image": image,
            "ca_bundle": b64encode(ca_bundle.encode("ascii")).decode("utf-8"),
        }

        assert harness.charm._context == expected_context

    def test_k8s_resource_handler(self, harness: Harness):
        """Tests whether the k8s_resource_handler is instantiated and cached properly."""
        harness.begin()
        logger = "logger"
        harness.charm.logger = logger
        context = harness.charm._context
        field_manager = "field_manager"
        harness.charm._lightkube_field_manager = field_manager
        k8s_resource_files = K8S_RESOURCE_FILES

        krh = harness.charm.k8s_resource_handler
        assert krh.log == logger
        assert krh.context == context
        assert krh._field_manager == field_manager
        assert krh.template_files == k8s_resource_files

        krh2 = harness.charm.k8s_resource_handler
        assert krh is krh2

    @pytest.mark.parametrize(
        "cert_data_dict, should_certs_refresh",
        [
            # Cases where we should generate a new cert
            # No cert data, we should refresh certs
            ({}, True),
            # We are missing one of the required cert data fields, we should refresh certs
            ({"ca": "x", "key": "x"}, True),
            ({"cert": "x", "key": "x"}, True),
            ({"cert": "x", "ca": "x"}, True),
            # Cases where we should not generate a new cert
            # Cert data already exists, we should not refresh certs
            ({"cert": "x", "ca": "x", "key": "x", }, False),
        ]
    )
    def test_gen_certs_if_missing(self, cert_data_dict, should_certs_refresh, harness: Harness, mocker):
        """Test _gen_certs_if_missing.

        This tests whether _gen_certs_if_missing:
        * generates a new cert if there is no existing one
        * does not generate a new cert if there is an existing one
        """
        # Arrange
        # Mock away gen_certs so the class does not generate any certs unless we want it to
        mocked_gen_certs = mocker.patch("charm.NamespaceNodeAffinityOperator._gen_certs", autospec=True)
        harness.begin()
        mocked_gen_certs.reset_mock()

        # Set any provided cert data to _stored
        for k, v in cert_data_dict.items():
            setattr(harness.charm._stored, k, v)

        # Act
        harness.charm._gen_certs_if_missing()

        # Assert that we have/have not called refresh_certs, as expected
        assert mocked_gen_certs.called == should_certs_refresh

