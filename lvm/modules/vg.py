#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Ansible module to create or remove a Physical Volume.
(c) 2015 Nandaja Varma <nvarma@redhat.com>, Anusha Rao <aroa@redhat.com>
This file is part of Ansible
Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Ansible. If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: pv
short_description: Create or remove a Physical Volume.
description:
    - Creates or removes n-number of Physical Volumes on n-number i
      of remote hosts

options:
    action:
        required: true
        choices: [create, remove]
        description: Specifies the pv operation that is to be executed,
                     either a physical volume creation or deletion.
    disks:
        required: true
        description: Disks from which the Physical Volumes are to be created,
                     or Physical Volumes that are to be removed needs to be
                     specified here.
    options:
        required: false
        description: Extra options that needs to be passed while creating the
                     Physical Volumes can be given here. Check the man page of
                     pvcreate for more info.

author: Anusha Rao
'''

EXAMPLES = '''
'''
#!/usr/bin/python

from ansible.module_utils.basic import *
import json
import re
from ast import literal_eval
import sys
import os
class VgOps(object):
    def __init__(self, module):
        self.module = module
        self.disks = literal_eval(self.validated_params('disks'))
        self.vg_pattern = module.params['vg_pattern']
        self.options = module.params['options'] or ''
        self.action = self.validated_params('action')
        output = map(self.vg_create_or_remove, self.disks)
        self.get_output(output)

    def get_output(self, output):
        if self.action == 'remove':
            for each in output:
                if each[0][0]:
                    self.module.fail_json(msg = each[0][2])
                else:
                    self.module.exit_json(msg = each[0][1])
        else:
            for each in output:
                if each[0]:
                    self.module.fail_json(msg = each[2])
                else:
                    self.module.exit_json(msg = each[1])

    def validated_params(self, opt):
        value = self.module.params[opt]
        if value is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.exit_json(msg=msg)
        return value


    def vg_create_or_remove(self, disk):
        op = 'vg' + self.action
        if op == 'vgcreate':
            vg_name = self.generate_name()

            opts = " %s %s %s" % (vg_name, self.options, disk)
            return self.run_command(op, opts)
        elif op == 'vgremove':
            vgs = self.get_vgs(disk).strip().split('\n')
            output = []
            for each in vgs:
                opts = " " + each
                output.append(self.run_command(op, opts))
            return output

    def get_vgs(self, disk):
        opts = " --noheadings -o vg_name %s" % disk
        rc, output, err = self.run_command('pvs', opts)
        return output

    def run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts
        return self.module.run_command(cmd)


    def generate_name(self):
        absent, out, err  = self.run_command('vgdisplay', ' ' + self.vg_pattern)
        if absent:
            return self.vg_pattern
        else:
            for i in range(1, 100):
                new_vgname = self.vg_pattern + str(i)
                absent, out, err  = self.run_command('vgdisplay', ' ' + new_vgname)
                if absent:
                    return new_vgname

if __name__ == '__main__':
       module = AnsibleModule(
              argument_spec = dict(
                     action = dict(choices = ["create", "remove"]),
                     vg_pattern = dict(type = 'str', required = True),
                     disks = dict(),
                     options = dict(type='str'),
              ),
       )

       vgops = VgOps(module)
