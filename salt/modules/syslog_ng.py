# -*- coding: utf-8 -*-
'''
Wrapper module for syslog-ng
'''

import os
import os.path
import logging
import salt
import salt.config
import salt.utils
import salt.loader
from salt.exceptions import CommandExecutionError

__virtualname__ = 'syslog_ng'

__SYSLOG_NG_SEARCH_PATH = ("/usr", "/usr/local", "/home/tibi/install/syslog-ng")
__INSTALL_PREFIX = ""
__SYSLOG_NG_BINARY_PATH = ""
__SYSLOG_NG_CTL_BINARY_PATH = ""

def __virtual__():
    '''
    Only load module if syslog-ng binary is present
    '''
    global __SYSLOG_NG_BINARY_PATH, __SYSLOG_NG_CTL_BINARY_PATH
    __SYSLOG_NG_BINARY_PATH = salt.utils.which('syslog-ng')
    __SYSLOG_NG_CTL_BINARY_PATH = salt.utils.which('syslog-ng-ctl')
    return __virtualname__ if __SYSLOG_NG_BINARY_PATH else False

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class SyslogNGError(Exception): pass

def _set_install_prefix(prefix):
    global __INSTALL_PREFIX
    global __SYSLOG_NG_BINARY_PATH
    global __SYSLOG_NG_CTL_BINARY_PATH
    __INSTALL_PREFIX = prefix
    __SYSLOG_NG_BINARY_PATH = os.path.join(__INSTALL_PREFIX, "sbin/syslog-ng")
    __SYSLOG_NG_CTL_BINARY_PATH = os.path.join(__INSTALL_PREFIX, "sbin/syslog-ng-ctl")

def _check_install_path(path):
    if os.path.exists(path):
        syslog_ng_bin_path = os.path.join(path, "sbin/syslog-ng")
        syslog_ng_ctl_bin_path = os.path.join(path, "sbin/syslog-ng-ctl")
        for binary_file in (syslog_ng_bin_path, syslog_ng_ctl_bin_path):
            if not os.path.isfile(binary_file):
                log.debug("Syslog-ng binary file: {0} is not a file or does not exist".format(binary_file))
            else:
                log.debug("Found syslog-ng installed in {0}".format(path))
                return True
        return False

def set_install_prefix(prefixes=()):
    """
    Set the install prefix of syslog-ng.

    Usually it is /usr, but if you installed it under a specific location, you have to set it with this method.

    :param prefixes: the list of prefixes. The first matching will be the used prefix.
    :return: the first matching prefix, it it is valid. If none of them matching, then False.
    """
    if not isinstance(prefixes, tuple):
        prefixes = tuple(prefixes)

    for path in prefixes:
        if _check_install_path(path):
            _set_install_prefix(path)
            return path
    log.error("Unable to find syslog-ng under the given prefixes")
    return False

def new_source():
    pass

def new_destination():
    pass

def config_test():
    ret = _run_command("syslog-ng", options=("--syntax-only"))
    return ret.get("retcode", "None")

def install_prefix():
    return __INSTALL_PREFIX

def _run_command(cmd, options=()):
    cmd_with_params = [cmd]
    cmd_with_params.extend(options)
    #cmd_with_params = " ".join(cmd_with_params)
    #log.debug("Cmd to run: " + cmd_with_params)

    try:
        return __salt__['cmd.run_all'](cmd_with_params)
    except Exception as err:
        log.error(str(err))
        raise CommandExecutionError("Unable to run command: " + str(type(err)))

def version():
    """
    Returns the version of the installed syslog-ng.
    """
    ret = _run_command("syslog-ng", options=("-V", ))
    if ret["retcode"] != 0:
        return "-1"

    lines = ret["stdout"].split("\n")
    # The format of the first line in the output is:
    # syslog-ng 3.6.0alpha0
    version_line_index = 0
    version_column_index = 1
    return lines[version_line_index].split()[version_column_index]

def modules():
    """
    Returns the available modules.
    """
    ret = _run_command("syslog-ng", options=("-V", ))
    if ret["retcode"] != 0:
        return ""

    lines = ret["stdout"].split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Available-Modules"):
            label, modules = line.split()
            return modules
    return None

def ctl(command="stats"):
    """
        command = (stats, verbose, debug, trace, stop, reload)
    """
    commands = ("stats", "verbose", "debug", "trace", "stop", "reload")
    if command not in commands:
        return "The given command '{0}' is not among the supported ones. Please run syslog-ng-ctl for help."

    ret = _run_command("syslog-ng-ctl", options=(command,))
    if ret["retcode"] == 0:
        return ret.get("stdout", "")
    else:
        return ret.get("stderr","")
