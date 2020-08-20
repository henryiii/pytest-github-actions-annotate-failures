from __future__ import print_function
import os
import pytest
from collections import OrderedDict

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    report = outcome.get_result()

    # enable only in a workflow of GitHub Actions
    # ref: https://help.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables#default-environment-variables
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return

    if report.when == "call" and report.failed:
        # collect information to be annotated
        filesystempath, lineno, _ = report.location

        # try to convert to absolute path in GitHub Actions
        workspace = os.environ.get('GITHUB_WORKSPACE')
        if workspace:
            full_path = os.path.abspath(filesystempath)
            rel_path = os.path.relpath(full_path, workspace)
            if not rel_path.startswith('..'):
                filesystempath = rel_path

        # 0-index to 1-index
        lineno += 1


        # get the name of the current failed test, with parametrize info
        title = report.head_line or item.name

        # get the error message and line number from the actual error
        try:
            longrepr = report.longrepr.reprcrash.message
            lineno = report.longrepr.reprcrash.lineno

        except AttributeError:
            longrepr = None

        print(_error_workflow_command(filesystempath, lineno, longrepr, title))


def _error_workflow_command(filesystempath, lineno, longrepr, title):
    # Build collection of arguments. Ordering is strict for easy testing
    details_dict = OrderedDict()
    details_dict["file"] = filesystempath
    if lineno is not None:
        details_dict["line"] = lineno
    if title:
        details_dict["title"] = '"{}"'.format(title)

    details = ",".join("{}={}".format(k,v) for k,v in details_dict.items())
    
    if longrepr is None:
        return '\n::error {}'.format(details)
    else:
        longrepr = _escape(longrepr)
        return '\n::error {}::{}'.format(details, longrepr)

def _escape(s):
    return s.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
