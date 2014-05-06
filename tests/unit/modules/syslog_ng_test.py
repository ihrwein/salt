# -*- coding: utf-8 -*-
'''
Test module for syslog_ng
'''

# Import Salt Testing libs
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath, TestsLoggingHandler
from salttesting.mock import NO_MOCK, NO_MOCK_REASON, MagicMock, patch
import uuid
from salt.modules import syslog_ng
import os

syslog_ng.__salt__ = {}
syslog_ng.__opts__ = {}

_VERSION = "3.6.0alpha0"
_MODULES = ("syslogformat,json-plugin,basicfuncs,afstomp,afsocket,cryptofuncs,"
            "afmongodb,dbparser,system-source,affile,pseudofile,afamqp,"
            "afsocket-notls,csvparser,linux-kmsg-format,afuser,confgen,afprog")

VERSION_OUTPUT = """syslog-ng {0}
Installer-Version: {0}
Revision:
Compile-Date: Apr  4 2014 20:26:18
Error opening plugin module; module='afsocket-tls', error='/home/tibi/install/syslog-ng/lib/syslog-ng/libafsocket-tls.so: undefined symbol: tls_context_setup_session'
Available-Modules: {1}
Enable-Debug: on
Enable-GProf: off
Enable-Memtrace: off
Enable-IPv6: on
Enable-Spoof-Source: off
Enable-TCP-Wrapper: off
Enable-Linux-Caps: off""".format(_VERSION, _MODULES)

STATS_OUTPUT = """SourceName;SourceId;SourceInstance;State;Type;Number
center;;received;a;processed;0
destination;#anon-destination0;;a;processed;0
destination;#anon-destination1;;a;processed;0
source;s_gsoc2014;;a;processed;0
center;;queued;a;processed;0
global;payload_reallocs;;a;processed;0
global;sdata_updates;;a;processed;0
global;msg_clones;;a;processed;0"""

@skipIf(NO_MOCK, NO_MOCK_REASON)
@skipIf(syslog_ng.__virtual__() is False, 'Syslog-ng must be installed')
class SyslogNGTestCase(TestCase):

    def test_version(self):
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : VERSION_OUTPUT})
        mock_args = "syslog-ng -V"
        self._mock_test(expected="3.6.0alpha0",
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.version,
                        func_to_call_args=tuple()
                        )

    def test_ctl_fails_when_syslog_ng_doesnt_run(self):
        mock_args = "syslog-ng-ctl stats"
        mock = MagicMock(return_value={"retcode" : 1, 'stdout' : ""})
        assert_func = lambda x, y: len(x) == len(STATS_OUTPUT)
        self._mock_test(expected="",
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.ctl,
                        func_to_call_args=("stats",),
                        assert_func=assert_func
                        )

    def test_ctl_stats(self):
        mock_args = "syslog-ng-ctl stats"
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : ""})
        self._mock_test(expected="",
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.ctl,
                        func_to_call_args=("stats",)
                        )

    def test_modules(self):
        mock_args = "syslog-ng -V"
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : VERSION_OUTPUT})
        self._mock_test(expected=_MODULES,
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.modules,
                        func_to_call_args=tuple()
                        )

    def test_prefix(self):
        expected = "/home/foo/bar/install"
        with patch.dict(syslog_ng.__opts__, {"syslog_ng.prefix" : expected}):
            prefix_before_set = syslog_ng.get_prefix()
            syslog_ng.set_prefix(expected)
            prefix_after_set = syslog_ng.get_prefix()
            self.assertEqual(prefix_before_set, "")
            self.assertEqual(expected, prefix_after_set)

    def test_start(self):
        expected = 0
        mock_args = "syslog-ng -Fevd"
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : ""})
        self._mock_test(expected=expected,
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.start,
                        func_to_call_args=("-Fevd",)
                        )

    @patch("salt.modules.syslog_ng._is_config_dir")
    def test_config_dir(self, mock):
        mock.return_value = True
        expected = "/etc/syslog-ng"
        syslog_ng.set_config_dir(expected)
        got = syslog_ng.get_config_dir()
        self.assertEqual(expected, got)

    def test_config_dir_fails(self):
        expected = "/foo/bar/ssfsdfsdfsdfsdfsdf/sgeh"
        syslog_ng.set_config_dir(expected)
        got = syslog_ng.get_config_dir()
        self.assertNotEqual(expected, got)

    def test_append_config_creates_file(self):
        filename = "syslog-ng-test-{0}.conf".format(uuid.uuid4().hex[:6])
        config = """rewrite r_set_syslog_tag {
                        set-tag(".syslog");
                    };"""
        syslog_ng.append_config(config, to_file=filename)
        with open(filename, "r") as conf_file:
            content = conf_file.read()
            self.assertTrue(content.endswith(config))
        os.remove(filename)

    def test_append_config_from_file(self):
        from_file = "syslog-ng-test-{0}.conf".format(uuid.uuid4().hex[:6])
        to_file = "syslog-ng-test-{0}.conf".format(uuid.uuid4().hex[:6])
        config = """parser p_json {
        json-parser(marker("@json:") prefix(".json."));
        };
        """
        with open(from_file, "w") as f:
            f.write(config)

        syslog_ng.append_config_from_file(from_file=from_file, to_file=to_file)
        with open(to_file, "r") as conf_file:
            content = conf_file.read()
            self.assertTrue(content.endswith(config))
        os.remove(to_file)
        os.remove(from_file)

    def _mock_test(self, expected, mock_func, mock_func_args,
                          func_to_call, func_to_call_args,
                          assert_func=None):
        # self.assertEqual cannot be passed as a default value
        if assert_func is None:
            assert_func = self.assertEqual

        with patch.dict(syslog_ng.__salt__, {'cmd.run_all' : mock_func}):
            got = func_to_call(*func_to_call_args)
            assert_func(expected, got)
            mock_func.assert_called_once_with(
                mock_func_args
            )

if __name__ == '__main__':
    from integration import run_tests
    run_tests(SyslogNGTestCase, needs_daemon=False)