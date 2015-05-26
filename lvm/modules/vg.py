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
module: vg
short_description: Create or remove a Volume Group.
description:
    - Creates or removes n-number of Volume Groups on n-number
      of remote hosts

options:
    action:
        required: true
        choices: [create, remove]
        description: Specifies the vg operation that is to be executed,
                     either a volume group creation or deletion.
    disks:
        required: true
        description: Physical Volumes on which the Volume Groups are to be
                     created or Volume Groups that are to be removed needs to
                     be specified here.
    options:
        required: false
        description: Extra options that needs to be passed while creating the
                     Volume Groups can be given here. Check the man page of
                     vgcreate for more info.
    vg_pattern:
        required: true for create action
        description: The pattern to be followed while naming the volume
                     groups which are to be created. Pattern followed by
                     the ordinance of the volume group created will be
                     the name of that particulat volume group.
    vg_name:
        required: true for remove action
        description: Names of the Volume Groups that are to be removed

author: Anusha Rao, Nandaja Varma
'''

EXAMPLES = '''
#Create Volume Groups on PVS /dev/sdb and /dev/sdc with
#physical extension size 128k
    - vg: action=create disks='["/dev/sdb", "/dev/sdc"]'
          options="--physicalextentsize 128k"
          vg_pattern="RHS_vg"
#Remove Volume Groups RHS_vg1, RHS_vg2 and RHS_vg3
    - pv: action=remove
          vg_name='["RHS_vg1", "RHS_vg2", "RHS_vg3"]'

'''

from ansible.module_utils.basic import *
import json
import re
from ast import literal_eval
import sys
import os


class VgOps(object):

    def __init__(self, module):
        self.module = module
        self.action = self.validated_params('action')
        if self.action == 'create':
            self.vgs_or_disks = literal_eval(self.validated_params('disks'))
            self.vg_pattern = self.validated_params('vg_pattern')
            self.options = self.module.params['options'] or ''
        else:
            self.vgs_or_disks = literal_eval(self.validated_params('vg_name'))
        output = map(self.vg_create_or_remove, self.vgs_or_disks)
        self.get_output(output)

    def get_output(self, output):
        for each in output:
            if each[0]:
                self.module.fail_json(msg=each[2])
            else:
                self.module.exit_json(msg=each[1], changed=1)

    def validated_params(self, opt):
        value = self.module.params[opt]
        if value is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.fail_json(msg=msg)
        return value

    def vg_create_or_remove(self, vg_or_disk):
        op = 'vg' + self.action
        if op == 'vgcreate':
            vg_name = self.generate_name()
            opts = " %s %s %s" % (vg_name, self.options, vg_or_disk)
            return self.run_command(op, opts)
        elif op == 'vgremove':
            vg_absent = self.run_command('vgdisplay', ' ' + vg_or_disk)
            if not vg_absent[0]:
                opts = " -y -ff " + vg_or_disk
                return self.run_command(op, opts)
            else:
                return vg_absent

    def vg_present(self, vgname):
        absent, out, err = self.run_command('vgdisplay', ' ' + vgname)
        if absent:
            return False
        return True

    def run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts
        return self.module.run_command(cmd)

    def generate_name(self):
        for i in range(1, 100):
            new_vgname = self.vg_pattern + str(i)
            if not self.vg_present(new_vgname):
                return new_vgname

if __name__ == '__main__':
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(choices=["create", "remove"], required=True),
            vg_pattern=dict(type='str'),
            vg_name=dict(type='str'),
            disks=dict(),
            options=dict(type='str'),
        ),
    )

    vgops = VgOps(module)
