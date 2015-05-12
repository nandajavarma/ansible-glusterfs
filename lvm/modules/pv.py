#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Ansible module to create or remove a Physical Volume.
(c) 2015
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

authors: Anusha Rao
         Nandaja Varma
'''

EXAMPLES = '''
#Create Physical Volumes /dev/sdb and /dev/sdc with
#dataalignment 1280k
    - pv: action=create disks='["/dev/sdb", "/dev/sdc"]'
          options="--dataalignment 1280k"
#Remove Physical Volumes /dev/sdb and /dev/sdc
    - pv: action=remove disks='["/dev/sdb", "/dev/sdc"]'
'''
from ansible.module_utils.basic import *
import json
import sys
from ast import literal_eval


class PvOps(object):

    def __init__(self, module):
        self.module = module
        self.disks = literal_eval(self.validated_params('disks'))
        self.options = module.params['options'] or ''
        self.action = self.validated_params('action')
        self.create_or_remove()

    def validated_params(self, opt):
        value = self.module.params[opt]
        if value is None:
            print "Please provide %s option in the playbook!" % opt
            sys.exit(1)
        return value

    def run_command(self, op, options):
        cmd = self.module.get_bin_path(op, True) + options
        rc, output, err = self.module.run_command(cmd)
        if op == 'pvdisplay':
            ret = 1
            if self.action == 'create' and not rc:
                print "%s Physical Volume Exists!" % options
            elif self.action == 'remove' and rc:
                print "%s Physical Volume Does Not Exist!" % options
            else:
                ret = 0
            return ret
        elif rc:
            self.module.fail_json(msg="Failed executing pv command.",
                                  rc=rc, err=err)
        print output

    def create_or_remove(self):
        for each in self.disks:
            presence_check = self.run_command('pvdisplay', ' ' + each)
            if not presence_check:
                op = 'pv' + self.action
                args = {'pvcreate': " %s %s" %(self.options, each),
                        'pvremove': " %s" % each
                       }[op]
                self.run_command(op, args)

if __name__ == '__main__':
       module = AnsibleModule(
              argument_spec = dict(
                     action = dict(choices = ["create", "remove"]),
                     disks = dict(),
                     options = dict(type='str'),
              ),
       )

       pvops = PvOps(module)

