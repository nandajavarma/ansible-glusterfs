#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Ansible module to create or remove a Physical Volume.
(c) 2015 Nandaja Varma <nvarma@redhat.com>
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
author: Nandaja Varma
'''
EXAMPLES = '''
'''
from ansible.module_utils.basic import *
import json
from ast import literal_eval
from math import floor
error = False

class LvOps(object):

    def __init__(self, module):
        self.dataalign = 1280 #in KB
        self.module = module
        self.action = self.validated_params('action')
        self.vgname = self.validated_params('vgname')
        rc, output, err = { 'create': self.create,
                            'convert': self.convert,
                            'change': self.change,
                            'remove': self.remove
                          }[self.action]()
        if rc:
            self.module.fail_json(msg=err)
        else:
            self.module.exit_json(msg=output)

    def compute(self):
        global error
        option = " --noheadings -o pv_name %s" % self.vgname
        rc, pv_name, err = self.run_command('vgs', option)
        if  rc:
            error = True
            return 0, 0
        else:
            option = " --noheading --units m  -o pv_size %s" % pv_name
            rc, pv_size, err = self.run_command('pvs', option)
            if not rc:
                pv_size = floor(float(pv_size.strip(' m\t\r\n')) - 4)
                KB_PER_GB=1048576
                if pv_size > 1000000:
                    METADATA_SIZE_GB=16
                    metadatasize = floor(METADATA_SIZE_GB * KB_PER_GB)
                else:
                    METADATA_SIZE_MB = pv_size / 200
                    metadatasize = floor(floor(METADATA_SIZE_MB) * 1024)
                pool_sz = floor(pv_size * 1024) - metadatasize
                return metadatasize, pool_sz

    def validated_params(self, opt):
        value = self.module.params[opt]
        if value is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.exit_json(msg=msg)
        return value

    def run_command(self, op, options):
        cmd = self.module.get_bin_path(op, True) + options
        return self.module.run_command(cmd)

    def create(self):
        lvtype = self.validated_params('lvtype')
        lvname = self.validated_params('lvname')
        compute = self.module.params['compute'] or ''
        if lvtype in ['virtual']:
            poolname = self.validated_params('poolname')
        else:
            poolname = ''
        if compute == 'rhs':
            metadatasize, pool_sz = self.compute()
        if not error:
            options = {'thin': ' -L %sK' % metadatasize,
                       'thick': ' -L %sK' % pool_sz,
                       'virtual': ' -L %sK -T /dev/%s/%s'
                                    %( pool_sz, self.vgname, poolname)
                      }[lvtype] + " -n %s %s" % (lvname, self.vgname)
            return self.run_command('lvcreate', options)
        err = "%s Volume Group Does Not Exist!" %self.vgname
        return 1, 0, err


    def convert(self):
        thinpool = self.validated_params('thinpool')
        poolmetadata = self.module.params['poolmetadata'] or ''
        poolmetadataspare = self.module.params['poolmetadataspare'] or ''
        options = ' -c %s --yes -ff --thinpool %s --poolmetadata %s ' \
        '--poolmetadataspare %s' % (self.dataalign, thinpool, \
                                            poolmetadata, poolmetadataspare)
        return self.run_command('lvconvert', options)


    def change(self):
        poolname = self.validated_params('poolname')
        zero = self.module.params['zero'] or ''
        options = ' -Z %s %s/%s' % (zero, self.vgname, poolname)
        return self.run_command('lvchange', options)

    def remove(self):
        lvname = self.validated_params('lvname')
        opt = ' -ff --yes %s/%s' % (self.vgname, lvname)
        return self.run_command('lvremove', opt)


def main():
    module = AnsibleModule(
           argument_spec = dict(
                  action = dict(choices = ["create", "convert", "change"]),
                  lvname = dict(),
                  lvtype = dict(),
                  vgname = dict(),
                  thinpool = dict(),
                  poolmetadata = dict(),
                  poolmetadataspare = dict(),
                  poolname = dict(),
                  zero = dict(),
                  compute = dict()
           ),
    )

    lvops = LvOps(module)

if __name__ == '__main__':
    main()
