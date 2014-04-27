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
from time import strftime

__virtualname__ = 'syslog_ng'

__INSTALL_PREFIX = ""
__SYSLOG_NG_BINARY_PATH = ""
__SYSLOG_NG_CTL_BINARY_PATH = ""
__SYSLOG_NG_CONFIG_DIR = ""

__SALT_GENERATED_CONFIG_HEADER  = """#Generated by salt on
#{0}
"""

def __virtual__():
    '''
    Initializes the module and returns "syslog-ng", if it is available
    '''
    # Only load module if syslog-ng binary is present
    global __SYSLOG_NG_BINARY_PATH, __SYSLOG_NG_CTL_BINARY_PATH, __INSTALL_PREFIX

    _load_module_config()

    __SYSLOG_NG_BINARY_PATH = salt.utils.which('syslog-ng')
    __SYSLOG_NG_CTL_BINARY_PATH = salt.utils.which('syslog-ng-ctl')
    return __virtualname__ if __SYSLOG_NG_BINARY_PATH else False

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def _append_to_path(item):
    """
    Appends an item to the PATH environment variable
    """
    os.environ["PATH"] += os.pathsep + item

def _format_generated_config_header():
    """
    Formats a header, which is prepended to all appended config
    """
    now = strftime("%Y-%m-%d %H:%M:%S")
    return __SALT_GENERATED_CONFIG_HEADER.format(now)

def append_config(config, to_file="syslog-ng.conf"):
    """
    Appends a configuration snippet to syslog-ng.conf, or creates a new file.
    """
    config_file_path = os.path.join(__SYSLOG_NG_CONFIG_DIR, to_file)
    with open(config_file_path, "a+") as config_file:
        header = _format_generated_config_header()
        config_file.write(header)
        config_file.write(config)

def append_config_from_file(from_file, to_file="syslog-ng.conf"):
    """
    Appends the content of from_file to to_file.

    From_file needs to be located on the minion, so before using this command
    you need to copy it from the master.
    """
    config = ""
    with open(from_file, "r") as config_file:
        config = config_file.read()
    append_config(config=config, to_file=to_file)

def _load_module_config():
    """
    Loads the syslog-ng module configuration from the minion configuration.
    """
    # load installation prefix, if exists
    prefix = __opts__.get("syslog_ng.prefix", "")
    if prefix:
        set_prefix(prefix)

    # load configuration directory, where syslog-ng.conf is located,
    # like /etc/syslog-ng
    config_dir = __opts__.get("syslog_ng.config_dir", "")
    if config_dir:
        set_config_dir(config_dir)

def _is_config_dir(dir):
    """
    :return True, if the given directory contains a syslog-ng.conf file
            False, otherwise
    """
    conf_file = os.path.join(dir, "syslog-ng.conf")
    return os.path.exists(dir) and os.path.isdir(dir) and os.path.exists(conf_file)

def set_config_dir(directory):
    """
    Sets the configuration directory.
    """
    global __SYSLOG_NG_CONFIG_DIR
    if _is_config_dir(directory):
        __SYSLOG_NG_CONFIG_DIR = directory
        return True
    else:
        return False

def get_config_dir():
    """
    Returns the configuration directory, which contains syslog-ng.conf.
    """
    return __SYSLOG_NG_CONFIG_DIR

def set_prefix(prefix):
    """
    Sets the install prefix.
    """
    global __INSTALL_PREFIX
    __INSTALL_PREFIX = prefix
    _append_to_path(os.path.join(prefix, "sbin"))
    _append_to_path(os.path.join(prefix, "bin"))

def get_prefix():
    """
    Returns the install prefix.
    """
    return __INSTALL_PREFIX

def config_test():
    """
    Runs syntax check against syslog-ng.conf
    """
    ret = _run_command("syslog-ng", options=("--syntax-only"))
    return ret.get("retcode", "None")

def _run_command(cmd, options=()):
    cmd_with_params = [cmd]
    cmd_with_params.extend(options)

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
