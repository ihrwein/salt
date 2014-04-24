# -*- coding: utf-8 -*-
'''
Test module for syslog_ng
'''

# Import Salt Testing libs
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath, TestsLoggingHandler
from salttesting.mock import NO_MOCK, NO_MOCK_REASON, MagicMock, patch

from salt.modules import syslog_ng

@skipIf(NO_MOCK, NO_MOCK_REASON)
@skipIf(syslog_ng.__virtual__() is False, 'Syslog-ng must be installed')
class SyslogNGTestCase(TestCase):

    def test_set_install_prefix(self):
        valid_prefix = "/home/tibi/install/syslog-ng"
        prefixes = (valid_prefix, "/usr")
        set_prefix = syslog_ng.set_install_prefix(prefixes)
        self.assertEqual(set_prefix, valid_prefix)

    def test_version(self):
        expected_version = "3.6.0alpha0"
        got_version = syslog_ng.version()
        self.assertEqual(expected_version, got_version)

if __name__ == '__main__':
    from integration import run_tests
    run_tests(SyslogNGTestCase, needs_daemon=False)