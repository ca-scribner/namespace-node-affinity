#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#

"""A Juju Charm for Namespace Node Affinity."""

import logging
import tempfile
from pathlib import Path
from subprocess import check_call

from ops.charm import CharmBase
from ops.framework import StoredState


SSL_CONFIG_FILE = "src/templates/ssl.conf.j2"


class NamespaceNodeAffinityOperator(CharmBase):
    """A Juju Charm for Namespace Node Affinity."""

    _stored = StoredState()

    def __init__(self, *args):
        """Initialize charm."""
        super().__init__(*args)

        # convenience variables and base settings
        self.logger = logging.getLogger(__name__)
        self._namespace = self.model.name
        self._lightkube_field_manager = "lightkube"
        self._name = self.model.app.name

        # generate certs
        self._stored.set_default(**self._gen_certs())

        # setup context to be used for updating K8S resources
        self._context = {
            # TODO: add context
            # "app_name": self._name,
            # "namespace": self._namespace,
            # "service": self._name,
            # "webhook_port": self._webhook_port,
            # "ca_bundle": b64encode(self._stored.ca.encode("ascii")).decode("utf-8"),
        }
        self._k8s_resource_handler = None

        # setup events
        self.framework.observe(self.on.config_changed, self.main)
        self.framework.observe(self.on.install, self.main)
        self.framework.observe(self.on.leader_elected, self.main)
        self.framework.observe(self.on.remove, self.main)
        self.framework.observe(self.on.upgrade_charm, self.main)

    def main(self, event):
        """Entrypoint for most charm events."""
        raise NotImplementedError

    def _gen_certs(self):
        """Generate certificates."""
        # TODO: Refactor this into a python-based method that can be imported from Chisme
        # generate SSL configuration based on template
        model = self.model.name

        ssl_conf = Path(SSL_CONFIG_FILE).read_text()
        ssl_conf = ssl_conf.replace("{{ model }}", str(model))
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir + "/seldon-cert-gen-ssl.conf").write_text(ssl_conf)

            # execute OpenSSL commands
            check_call(["openssl", "genrsa", "-out", tmp_dir + "/seldon-cert-gen-ca.key", "2048"])
            check_call(
                ["openssl", "genrsa", "-out", tmp_dir + "/seldon-cert-gen-server.key", "2048"]
            )
            check_call(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-new",
                    "-sha256",
                    "-nodes",
                    "-days",
                    "3650",
                    "-key",
                    tmp_dir + "/seldon-cert-gen-ca.key",
                    "-subj",
                    "/CN=127.0.0.1",
                    "-out",
                    tmp_dir + "/seldon-cert-gen-ca.crt",
                    ]
            )
            check_call(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-sha256",
                    "-key",
                    tmp_dir + "/seldon-cert-gen-server.key",
                    "-out",
                    tmp_dir + "/seldon-cert-gen-server.csr",
                    "-config",
                    tmp_dir + "/seldon-cert-gen-ssl.conf",
                    ]
            )
            check_call(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-sha256",
                    "-in",
                    tmp_dir + "/seldon-cert-gen-server.csr",
                    "-CA",
                    tmp_dir + "/seldon-cert-gen-ca.crt",
                    "-CAkey",
                    tmp_dir + "/seldon-cert-gen-ca.key",
                    "-CAcreateserial",
                    "-out",
                    tmp_dir + "/seldon-cert-gen-cert.pem",
                    "-days",
                    "365",
                    "-extensions",
                    "v3_ext",
                    "-extfile",
                    tmp_dir + "/seldon-cert-gen-ssl.conf",
                    ]
            )

            ret_certs = {
                "cert": Path(tmp_dir + "/seldon-cert-gen-cert.pem").read_text(),
                "key": Path(tmp_dir + "/seldon-cert-gen-server.key").read_text(),
                "ca": Path(tmp_dir + "/seldon-cert-gen-ca.crt").read_text(),
            }

            # cleanup temporary files
            check_call(["rm", "-f", tmp_dir + "/seldon-cert-gen-*"])

        return ret_certs

    # todo: add remove method
    # def _on_remove(self, event):
    #     raise NotImplementedError
