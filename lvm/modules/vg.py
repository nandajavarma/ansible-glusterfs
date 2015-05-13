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
        self.vg_name = module.params['vg_name']
        self.options = module.params['options'] or ''
        self.action = self.validated_params('action')
        self.generate_command()

    def validated_params(self, opt):
        value = self.module.params[opt]
        if value is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.exit_json(msg=msg)
        return value

    
def vg_create_or_remove(self,op,upv_list):
  
    if op == 'vgcreate':
        for u_pv in upv_list:
            has_vg = os.popen("pvs "+u_pv+" --noheadings -ovg_name").read()
            has_vg = has_vg.replace(" ","").replace("\n","")
        if(has_vg):
            continue
        else:
            udisks.append(u_pv)

        for udisk in udisks:
            vg_name = generate_name(self.vg_name)
            cmd = ''
            cmd = module.get_bin_path(op, True)
            cmd += " " + vg_name + " " + udisk + " " + self.options
            run_command(cmd)
    elif op == 'vgremove':
        cmd = module.get_bin_path('vgremove', True)
        cmd += vg_name
        self.run_command(cmd)
            

def run_command(self,cmd):
        rc, output, err = self.module.run_command(cmd)
        

        if self.action == 'create' and not rc:
            self.module.fail_json(msg=
                    "%s Volume Group Exists!" % options)
        elif self.action == 'remove' and rc:
            self.module.fail_json(msg=
                        "%s Volume Group Does Not Exist!" % options)
        else:
            ret = 0
        return ret
        
        self.module.exit_json(msg = output)

def generate_command(self):
        u_disks = get_updated_disks(self.disks)
            #presence_check = self.run_command('pvdisplay', ' ' + each)
            #if not presence_check:
        op = 'vg' + self.action
        args = {'vgcreate': self.vg_create_or_remove,
                'vgremove': self.vg_create_or_remove,
               }[op](op,u_disks)
            #self.run_command(op, args)

def generate_name(vg_name):
    #final_op should have vg_name of the current pvs_list passed to it
    final_op = os.popen("pvs --noheadings -ovg_name").read().replace(' ','')
    final_op = final_op.split('\n')
    final_op = filter(None,final_op)
    if vg_name in final_op:
        if (re.match('.*?([0-9]+)$', vg_name)):
            num = re.match('.*?([0-9]+)$', vg_name).group(1)
            vg_name = vg_name.replace(num,'')
            number = int(num) + 1
            vg_name += str(number)
        else:
            vg_name += '1'
    return vg_name

def get_updated_disks(disks):
    pvsout = os.popen("pvs --noheadings -opv_name").read().replace(' ','')
    pvs_list = pvs_list.split('\n')
    pvs_list.pop()
    upvs_list = list(set(pvs_list) & set(disks))
    return upvs_list


if __name__ == '__main__':
       module = AnsibleModule(
              argument_spec = dict(
                     action = dict(choices = ["create", "remove"]),
                     vg_name = dict(type = 'str', required = True),
                     disks = dict(),
                     options = dict(type='str'),
              ),
       )

       vgops = VgOps(module)
