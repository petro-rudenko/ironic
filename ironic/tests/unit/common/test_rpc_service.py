#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from unittest import mock

from oslo_config import cfg
import oslo_messaging
from oslo_service import service as base_service

from ironic.common import context
from ironic.common import rpc
from ironic.common import rpc_service
from ironic.conductor import manager
from ironic.objects import base as objects_base
from ironic.tests import base

CONF = cfg.CONF


@mock.patch.object(base_service.Service, '__init__', lambda *_, **__: None)
class TestRPCService(base.TestCase):

    def setUp(self):
        super(TestRPCService, self).setUp()
        host = "fake_host"
        mgr_module = "ironic.conductor.manager"
        mgr_class = "ConductorManager"
        self.rpc_svc = rpc_service.RPCService(host, mgr_module, mgr_class)

    @mock.patch.object(manager.ConductorManager, 'prepare_host', autospec=True)
    @mock.patch.object(oslo_messaging, 'Target', autospec=True)
    @mock.patch.object(objects_base, 'IronicObjectSerializer', autospec=True)
    @mock.patch.object(rpc, 'get_server', autospec=True)
    @mock.patch.object(manager.ConductorManager, 'init_host', autospec=True)
    @mock.patch.object(context, 'get_admin_context', autospec=True)
    def test_start(self, mock_ctx, mock_init_method,
                   mock_rpc, mock_ios, mock_target, mock_prepare_method):
        mock_rpc.return_value.start = mock.MagicMock()
        self.rpc_svc.handle_signal = mock.MagicMock()
        self.assertFalse(self.rpc_svc._started)
        self.assertFalse(self.rpc_svc._failure)
        self.rpc_svc.start()
        mock_ctx.assert_called_once_with()
        mock_target.assert_called_once_with(topic=self.rpc_svc.topic,
                                            server="fake_host")
        mock_ios.assert_called_once_with(is_server=True)
        mock_prepare_method.assert_called_once_with(self.rpc_svc.manager)
        mock_init_method.assert_called_once_with(self.rpc_svc.manager,
                                                 mock_ctx.return_value)
        self.assertIs(rpc.GLOBAL_MANAGER, self.rpc_svc.manager)
        self.assertTrue(self.rpc_svc._started)
        self.assertFalse(self.rpc_svc._failure)
        self.rpc_svc.wait_for_start()  # should be no-op

    @mock.patch.object(manager.ConductorManager, 'prepare_host', autospec=True)
    @mock.patch.object(oslo_messaging, 'Target', autospec=True)
    @mock.patch.object(objects_base, 'IronicObjectSerializer', autospec=True)
    @mock.patch.object(rpc, 'get_server', autospec=True)
    @mock.patch.object(manager.ConductorManager, 'init_host', autospec=True)
    @mock.patch.object(context, 'get_admin_context', autospec=True)
    def test_start_no_rpc(self, mock_ctx, mock_init_method,
                          mock_rpc, mock_ios, mock_target,
                          mock_prepare_method):
        CONF.set_override('rpc_transport', 'none')
        self.rpc_svc.start()

        self.assertIsNone(self.rpc_svc.rpcserver)
        mock_ctx.assert_called_once_with()
        mock_target.assert_not_called()
        mock_rpc.assert_not_called()
        mock_ios.assert_called_once_with(is_server=True)
        mock_prepare_method.assert_called_once_with(self.rpc_svc.manager)
        mock_init_method.assert_called_once_with(self.rpc_svc.manager,
                                                 mock_ctx.return_value)
        self.assertIs(rpc.GLOBAL_MANAGER, self.rpc_svc.manager)

    @mock.patch.object(manager.ConductorManager, 'prepare_host', autospec=True)
    @mock.patch.object(oslo_messaging, 'Target', autospec=True)
    @mock.patch.object(objects_base, 'IronicObjectSerializer', autospec=True)
    @mock.patch.object(rpc, 'get_server', autospec=True)
    @mock.patch.object(manager.ConductorManager, 'init_host', autospec=True)
    @mock.patch.object(context, 'get_admin_context', autospec=True)
    def test_start_failure(self, mock_ctx, mock_init_method, mock_rpc,
                           mock_ios, mock_target, mock_prepare_method):
        mock_rpc.return_value.start = mock.MagicMock()
        self.rpc_svc.handle_signal = mock.MagicMock()
        mock_init_method.side_effect = RuntimeError("boom")
        self.assertFalse(self.rpc_svc._started)
        self.assertFalse(self.rpc_svc._failure)
        self.assertRaises(RuntimeError, self.rpc_svc.start)
        mock_ctx.assert_called_once_with()
        mock_target.assert_called_once_with(topic=self.rpc_svc.topic,
                                            server="fake_host")
        mock_ios.assert_called_once_with(is_server=True)
        mock_prepare_method.assert_called_once_with(self.rpc_svc.manager)
        mock_init_method.assert_called_once_with(self.rpc_svc.manager,
                                                 mock_ctx.return_value)
        self.assertIsNone(rpc.GLOBAL_MANAGER)
        self.assertFalse(self.rpc_svc._started)
        self.assertIn("boom", self.rpc_svc._failure)
        self.assertRaises(SystemExit, self.rpc_svc.wait_for_start)
