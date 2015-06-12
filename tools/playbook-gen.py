#!/usr/bin/python
import sys
import os
import argparse
import ConfigParser
import yaml


class PlaybookGen(object):

    def __init__(self):
        self.helper = HelperMethods()
        self.group_name = 'rhs_servers'
        self.args = self.parse_arguments()
        self.dest_dir = self.helper.get_file_dir_path(
            '.',
            self.args.dest_dir or 'playbooks')
        self.force = self.args.force
        self.config_file = self.args.config_file.name
        self.parse_read_config()
        self.hosts = self.helper.get_host_names(self.config_parse)
        self.varfile, self.var_file_name = self.helper.validate_params(
            self.config_parse, self.hosts, self.group_name, self.dest_dir,
            self.force)
        self.create_inventory_file()
        if not self.varfile:
            print "Provide either configuration specific to each hosts " \
                "or provide common configurations for all. Exiting!"
            sys.exit(0)
        if self.varfile == 'group_vars':
            GroupVarsGen(
                self.config_parse,
                self.dest_dir,
                self.group_name,
                self.var_file_name[0],
                self.varfile)
        else:
            HostVarsGen(self.config_parse, self.var_file_name, self.hosts,
                    self.varfile)
        self.helper.move_templates_to_playbooks()
        print "To setup backend as per your configurations, as root run:\n" \
            "ansible-playbook -i %s/ansible_hosts " \
            "%s/setup-backend.yml" % (self.args.dest_dir, self.args.dest_dir)

    def parse_arguments(self):
        parser = argparse.ArgumentParser(version='1.0')
        parser.add_argument('-c', dest='config_file',
                            help="Configuration file",
                            type=argparse.FileType('rt'),
                            required=True)
        parser.add_argument('-d', dest='dest_dir',
                            help="Directory to save backend setup playbooks.",
                            default='playbooks')
        parser.add_argument('-f', dest='force', const='y',
                            default='n',
                            action='store',
                            nargs='?',
                            help="Force files and directories to be "
                            "overwritten if already exists.")
        try:
            return parser.parse_args()
        except IOError as msg:
            parser.error(str(msg))

    def parse_read_config(self):
        self.config_parse = self.helper.call_config_parser()
        try:
            self.config_parse.read(self.config_file)
        except AttributeError as msg:
            print "Sorry! Looks like the format of configuration " \
                    "file is not something we could read! \nTry removing " \
                    "whitespaces or unwanted characters in the configuration " \
                    "file."
            sys.exit(0)

    def create_inventory_file(self):
        self.inventory_file = self.helper.get_file_dir_path(
            self.dest_dir,
            'ansible_hosts')
        self.helper.parse_config_write(
            self.group_name,
            self.hosts,
            self.inventory_file)


class HelperMethods(object):

    def validate_params(self, config_parse, hosts, group_name, dirname, force):
        self.force = force
        self.group_name = group_name
        self.hosts = hosts
        self.config_parse = config_parse
        self.dirname = dirname
        self.create_required_files_and_dirs()
        return self.varfile, self.filepath

    def template_files_create(self, temp_file):
        if not os.path.isdir(temp_file):
            return False
        self.exec_cmds('cp %s/*' % temp_file, self.dirname)
        return True

    def move_templates_to_playbooks(self):
        templates_path = '/usr/share/ansible/ansible-glusterfs/templates'
        templates_path_bk = self.get_file_dir_path('.', 'templates')
        if not (self.template_files_create(templates_path) or
            self.template_files_create(templates_path_bk)):
            print "Template files not found at %s or %s. " \
                    "Check your ansible-gluster " \
                    "installation and try " \
                    "again." % (templates_path, templates_path_bk)
            sys.exit(0)

    def mk_dir(self, dirlists):
        for each in dirlists:
            if not os.path.isdir(each):
                self.exec_cmds('mkdir', each)
            elif self.force == 'n':
                print "Directory '%s' already exists. " \
                    "Use -f option to overwrite" % each.split('/')[-1]
                sys.exit(0)
            else:
                self.exec_cmds('rm -rf', each)
                self.exec_cmds('mkdir', each)
                continue

    def touch_files(self, filelists):
        for each in filelists:
            try:
                os.remove(each)
            except OSError:
                pass
            self.exec_cmds('touch', each)

    def create_required_files_and_dirs(self):
        options = self.config_get_sections(self.config_parse)
        set_options = set(options)
        set_host_options = set(self.hosts)
        other_sections = [x for x in options if x != 'hosts']
        if not other_sections:
            self.varfile = None
            self.filepath = None
        elif set_options.intersection(set_host_options):
            if set_host_options.issubset(set_options):
                self.varfile = 'host_vars'
                self.filepath = [self.get_file_dir_path(
                    self.dirname,
                    self.varfile +
                    '/' + x) for x in self.hosts]
            else:
                print "Give configurations for all the hosts. Exiting!"
                sys.exit(0)
        else:
            self.varfile = 'group_vars'
            self.filepath = [
                self.get_file_dir_path(
                    self.dirname,
                    self.varfile +
                    '/' +
                    self.group_name)]
        if self.varfile:
            dirlist = [self.dirname,
                       self.get_file_dir_path(self.dirname, self.varfile)]
            self.mk_dir(dirlist)
            self.touch_files(self.filepath)

    def insufficient_param_count(self, section, count):
        print "Please provide %s names for %s devices " \
            "else leave the field empty" % (section, count)
        return False

    def write_unassociated_data(self, section, options, yamlfile):
        data = {}
        data[section] = options
        self.write_yaml(data, yamlfile, False)

    def write_device_data(self, devices, yamlfile):
        self.bricks = devices
        self.yamlfile = yamlfile
        self.write_unassociated_data('bricks', self.bricks, self.yamlfile)
        return len(self.bricks)

    def write_optional_data(self, group_options, device_count, varfile, config):
        self.ret = True
        self.varfile = varfile
        self.config_parse = config
        self.group_options = group_options
        self.device_count = device_count
        self.write_disk_type()
        self.ret and self.write_vg_data()
        self.ret and self.write_pool_data()
        self.ret and self.write_lv_data()
        self.ret and self.write_lvols_data()
        self.ret and self.write_mountpoints_data()
        self.ret and self.write_mntpath_data()
        return self.ret

    def get_options(self, section):
        return (self.varfile == 'group_vars') and self.config_get_options(
                self.config_parse,
                section) or filter(None, self.config_section_map(
                self.config_parse, self.section,
                section).split(','))

    def get_var_file_write_options(self, section, section_name):
        if section in self.group_options:
            options = self.get_options(section)
            if len(options) < self.device_count:
                return self.insufficient_param_count(
                    section_name,
                    self.device_count)
        else:
            options = []
            pattern = {'vgs': 'RHS_vg',
                       'pools': 'RHS_pool',
                       'lvs': 'RHS_lv',
                       'mountpoints': '/rhs/brick'
                       }[section]
            for i in range(1, self.device_count + 1):
                options.append(pattern + str(i))
        return options

    def plain_yaml_write(self, keys, values):
        for key, value in zip(keys, values):
            self.write_unassociated_data(key, value, self.yamlfile)

    def write_data_alignment(self):
        if self.disktype == 'jbod':
            self.dataalign = 256
        else:
            self.dataalign = { 'raid6': int(self.stripesize) * int(self.diskcount),
                                'raid10': int(self.stripesize) * int(self.diskcount)
                              }[self.disktype]
        self.write_unassociated_data('dalign', int(self.dataalign),
                self.yamlfile)

    def write_stripe_size(self):
        try:
            self.stripesize = self.config_get_options(self.config_parse,
                    'stripesize')[0]
            if self.disktype == 'raid10' and self.stripsize != 256:
                print "Warning: We recommend a stripe unit size of 256KB " \
                        "for RAID 10"
        except:
            if self.disktype == 'raid10':
                self.stripesize = 256
            else:
                print "Please provide the stripe unit size since you have " \
                        "mentioned the disk type to be RAID 6"
                sys.exit()

    def write_disk_type(self):
        if 'disktype' in self.group_options:
            self.disktype = self.config_get_options(self.config_parse,
                    'disktype')[0]
            if self.disktype not in ['raid10', 'raid6', 'jbod']:
                print "Unsupported disk type!"
                sys.exit(0)
        else:
            self.disktype = 'jbod'
        if self.disktype != 'jbod':
            if 'diskcount' in self.group_options:
                self.diskcount = self.config_get_options(self.config_parse,
                        'diskcount')[0]
                self.write_stripe_size()
            else:
                print "Since you have specified your diskcount to be %s, " \
                        "Please provide number of data disks!" % self.disktype
                sys.exit()
        else:
            self.diskcount = 0
            self.stripesize = 0
        disk_data_keys = ['disktype', 'diskcount', 'stripesize']
        disk_data_values = [self.disktype, int(self.diskcount), int(self.stripesize)]
        self.plain_yaml_write(disk_data_keys, disk_data_values)
        self.write_data_alignment()

    def write_vg_data(self):
        self.vgs = self.get_var_file_write_options('vgs', 'volume group')
        if self.vgs:
            self.write_unassociated_data('vgs', self.vgs, self.yamlfile)
            data = []
            for i, j in zip(self.bricks, self.vgs):
                vgnames = {}
                vgnames['brick'] = i
                vgnames['vg'] = j
                data.append(vgnames)
            data_dict = dict(vgnames=data)
            self.write_yaml(data_dict, self.yamlfile, True)
        else:
            self.ret &= False

    def write_pool_data(self):
        self.pools = self.get_var_file_write_options('pools', 'logical pool')
        if self.pools:
            data = []
            for i, j in zip(self.pools, self.vgs):
                pools = {}
                pools['pool'] = i
                pools['vg'] = j
                data.append(pools)
            data_dict = dict(pools=data)
            self.write_yaml(data_dict, self.yamlfile, True)
        else:
            self.ret &= False

    def write_lv_data(self):
        self.lvs = self.get_var_file_write_options('lvs', 'logical volume')
        if self.lvs:
            data = []
            for i, j, k in zip(self.pools, self.vgs, self.lvs):
                pools = {}
                pools['pool'] = i
                pools['vg'] = j
                pools['lv'] = k
                data.append(pools)
            data_dict = dict(lvpools=data)
            self.write_yaml(data_dict, self.yamlfile, True)
        else:
            self.ret &= False

    def write_lvols_data(self):
        self.lvols = ['/dev/' + i + '/' + j for i, j in
                      zip(self.vgs, self.lvs)]
        if self.lvols:
            data_dict = {}
            data_dict['lvols'] = self.lvols
            self.write_yaml(data_dict, self.yamlfile, False)
        else:
            self.ret &= False

    def write_mountpoints_data(self):
        self.mntpts = self.get_var_file_write_options(
            'mountpoints',
            'volume group')
        if self.mntpts:
            data_dict = {}
            data_dict['mountpoints'] = self.mntpts
            self.write_yaml(data_dict, self.yamlfile, True)
        else:
            self.ret &= False

    def write_mntpath_data(self):
        self.devices = []
        for i, j in zip(self.vgs, self.lvs):
            self.devices.append('/dev/%s/%s' % (i, j))
        data = []
        for i, j in zip(self.mntpts, self.devices):
            mntpath = {}
            mntpath['path'] = i
            mntpath['device'] = j
            data.append(mntpath)
        data_dict = dict(mntpath=data)
        self.write_yaml(data_dict, self.yamlfile, True)

    def get_host_names(self, config_parse):
        try:
            return self.config_get_options(config_parse, 'hosts')
        except:
            print "Cannot find the section hosts in the config." \
                " The generator can't proceed. Exiting!"
            sys.exit(0)

    def write_yaml(self, data_dict, yml_file, data_flow):
        with open(yml_file, 'a+') as outfile:
            if not data_flow:
                outfile.write(
                    yaml.dump(
                        data_dict,
                        default_flow_style=data_flow))
            else:
                outfile.write(yaml.dump(data_dict))

    def config_section_map(self, config_parse, section, option):
        try:
            return config_parse.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as e:
            print e

    def config_get_options(self, config_parse, section):
        try:
            return config_parse.options(section)
        except ConfigParser.NoSectionError as e:
            print e

    def config_get_sections(self, config_parse):
        try:
            return config_parse.sections()
        except ConfigParser.Error as e:
            print e

    def get_file_dir_path(self, basedir, newdir):
        return os.path.join(os.path.realpath(basedir), newdir)

    def exec_cmds(self, cmd, opts):
        try:
            os.system(cmd + ' ' + opts)
        except:
            print "Command %s failed. Exiting!" % cmd
            sys.exit()

    def call_config_parser(self):
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.optionxform = str
        return config

    def parse_config_write(self, section, options, filename):
        config = self.call_config_parser()
        config.add_section(section)
        for option in options:
            config.set(section, option)
        try:
            with open(filename, 'wb') as file:
                config.write(file)
        except:
            print "Failed to create file %s. Exiting!" % filename
            sys.exit(0)


class GroupVarsGen(object):

    def __init__(self, config_parse, dirname, group_name, filename, varfile):
        self.group_vars_file_path = filename
        self.varfile = varfile
        self.helper = HelperMethods()
        self.config_parse = config_parse
        self.dirname = dirname
        self.group_name = group_name
        ret = self.create_group_vars()
        if not ret:
            print "Failed creation of group vars!"
            sys.exit(0)
        else:
            print "Group vars for all the hosts created!"

    def create_group_vars(self):
        options = self.helper.config_get_sections(self.config_parse)
        self.hosts = self.helper.get_host_names(self.config_parse)
        host_options = self.hosts + ['hosts']
        group_options = [val for val in options if val not in host_options]
        if 'devices' in group_options:
            options = self.helper.config_get_options(
                    self.config_parse, 'devices')
            self.device_count = self.helper.write_device_data(
                options,
                self.group_vars_file_path)
        else:
            print "Section 'devices' not specified. "\
                    "Cannot create group vars for this configurations. Exiting!"
            sys.exit(0)
        group_options.remove('devices')
        return self.helper.write_optional_data(
            group_options,
            self.device_count, self.varfile, self.config_parse)


class HostVarsGen(object):

    def __init__(self, config_parse, filenames, hosts, varfile):
        self.helper = HelperMethods()
        self.varfile = varfile
        self.config_parse = config_parse
        self.filenames = filenames
        self.hosts = hosts
        ret = self.create_host_vars()
        if not ret:
            print "Error: Failed creation of hostvars!"
            sys.exit(1)
        else:
            print "Host vars for each hosts created!\n"

    def create_host_vars(self):
        self.ret = True
        for each in self.hosts:
            self.helper.section = each
            self.varfilepath = [
                x for x in self.filenames if x.split('/')[-1] == each]
            device_names = self.helper.config_section_map(
                self.config_parse,
                each,
                'devices')
            if not device_names:
                print "Not creating group vars since no " \
                    "common option for devices provided"
                sys.exit(0)
            self.device_count = self.helper.write_device_data(
                filter(None, device_names.split(',')),
                self.varfilepath[0])
            other_options = self.helper.config_get_options(
                self.config_parse,
                each)
            group_sections = [x for x in other_options if x != 'devices']
            self.ret &= self.helper.write_optional_data(
                group_sections,
                self.device_count, self.varfile, self.config_parse)
        return self.ret


if __name__ == '__main__':
    PlaybookGen()
