#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Copyright: (c) 2022, Robin Gierse <robin.gierse@tribe29.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: host

short_description: discovery services in Checkmk.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.0.1"

description:
- discovery services within Checkmk.

extends_documentation_fragment: [tribe29.checkmk.common]

options:
    host_name:
        description: The host who's services you want to manage.
        required: true
        type: str
    state:
        description: The action to perform during discovery.
        type: str
        default: new
        choices: [new, remove, fix_all, refresh, only_host_labels]

author:
    - Robin Gierse (@robin-tribe29)
'''

EXAMPLES = r'''
# Create a single host.
- name: "Add newly discovered services on host."
  tribe29.checkmk.discovery:
    server_url: "http://localhost/"
    site: "local"
    automation_user: "automation"
    automation_secret: "$SECRET"
    host_name: "my_host"
    state: "new"
- name: "Add newly discovered services, update labels and remove vanished services on host."
  tribe29.checkmk.discovery:
    server_url: "http://localhost/"
    site: "local"
    automation_user: "automation"
    automation_secret: "$SECRET"
    host_name: "my_host"
    state: "fix_all"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
http_code:
    description: The HTTP code the Checkmk API returns.
    type: int
    returned: always
    sample: '200'
message:
    description: The output message that the module generates.
    type: str
    returned: always
    sample: 'Host created.'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

import pprint


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        server_url=dict(type='str', required=True),
        site=dict(type='str', required=True),
        automation_user=dict(type='str', required=True),
        automation_secret=dict(type='str', required=True, no_log=True),
        host_name=dict(type='str', required=True),
        state=dict(type='str', choices=['new', 'remove', 'fix_all', 'refresh', 'only_host_labels']),
    )

    result = dict(changed=False, failed=False, http_code='', msg='')

    module = AnsibleModule(argument_spec=module_args,
                           supports_check_mode=False)

    if module.params['state'] is None:
        module.params['state'] = 'new'

    changed = False
    failed = False
    http_code = ''
    server_url = module.params['server_url']
    site = module.params['site']
    automation_user = module.params['automation_user']
    automation_secret = module.params['automation_secret']
    host_name = module.params['host_name']
    state = module.params['state']

    http_code_mapping = {
        # http_code: (changed, failed, "Message")
        200: (True, False, "Discovery successful."),
        # 204: (True, False, "Changes activated."),
        400: (False, True, "Bad Request."),
        403: (False, True, "Forbidden: Configuration via WATO is disabled."),
        404: (False, True, "Not Found: Host could not be found."),
        406: (False, True, "Not Acceptable."),
        415: (False, True, "Unsupported Media Type."),
    }

    # Declare headers including authentication to send to the Checkmk API
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + automation_user + ' ' + automation_secret
    }

    api_endpoint = '/objects/host/' + host_name + '/actions/discover_services/invoke'
    params = {
        'mode': state,
    }
    url = server_url + site + "/check_mk/api/1.0" + api_endpoint

    response, info = fetch_url(module, url, module.jsonify(params), headers=headers, method='POST')
    http_code = info['status']

    # Kudos to Lars G.!
    if http_code in http_code_mapping.keys():
        changed, failed, msg = http_code_mapping[http_code]
    else:
        changed, failed, msg = (False, True, 'Error calling API')

    result['msg'] = msg
    result['changed'] = changed
    result['failed'] = failed
    result['http_code'] = http_code

    if result['failed']:
        module.fail_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
