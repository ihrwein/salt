# -*- coding: utf-8 -*-
'''
Test module for syslog_ng
'''

# Import Salt Testing libs
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath, TestsLoggingHandler
from salttesting.mock import NO_MOCK, NO_MOCK_REASON, MagicMock, patch

from salt.modules import syslog_ng

syslog_ng.__salt__ = {}

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

    def test_set_install_prefix(self):
        valid_prefix = "/home/tibi/install/syslog-ng"
        prefixes = (valid_prefix, "/usr")
        set_prefix = syslog_ng.set_install_prefix(prefixes)
        self.assertEqual(set_prefix, valid_prefix)

    def test_version(self):
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : VERSION_OUTPUT})
        mock_args = ["syslog-ng", "-V"]
        self._mock_test(expected="3.6.0alpha0",
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.version,
                        func_to_call_args=tuple()
                        )

    def test_ctl_fails_when_syslog_ng_doesnt_run(self):
        mock_args = ["syslog-ng-ctl", "stats"]
        mock = MagicMock(return_value={"retcode" : 1, 'stdout' : ""})
        assert_func = lambda x: len(x) == len(STATS_OUTPUT)
        self._mock_test(expected="",
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.ctl,
                        func_to_call_args=("stats",),
                        assert_func=assert_func
                        )

    def test_ctl_stats(self):
        mock_args = ["syslog-ng-ctl", "stats"]
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : ""})
        self._mock_test(expected="",
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.ctl,
                        func_to_call_args=("stats",)
                        )

    def test_modules(self):
        mock_args = ["syslog-ng", "-V"]
        mock = MagicMock(return_value={"retcode" : 0, 'stdout' : VERSION_OUTPUT})
        self._mock_test(expected=_MODULES,
                        mock_func=mock,
                        mock_func_args=mock_args,
                        func_to_call=syslog_ng.modules,
                        func_to_call_args=tuple()
                        )

    def _mock_test(self, expected, mock_func, mock_func_args,
                          func_to_call, func_to_call_args,
                          assert_func=None):
        # self.assertEqual cannot be passed as a default value
        if assert_func is None:
            assert_func = self.assertEqual

        with patch.dict(syslog_ng.__salt__, {'cmd.run_all' : mock_func}):
            got = func_to_call(*func_to_call_args)
            self.assertEqual(expected, got)
            mock_func.assert_called_once_with(
                mock_func_args
            )

if __name__ == '__main__':
    from integration import run_tests
    run_tests(SyslogNGTestCase, needs_daemon=False)