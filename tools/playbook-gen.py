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
                self.var_file_name[0])
        else:
            HostVarsGen(self.config_parse, self.var_file_name, self.hosts)
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
        self.config_parse.read(self.config_file)

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

    def move_templates_to_playbooks(self):
        self.templates_path = '/usr/share/ansible/ansible-gluster/templates'
        if not os.path.isdir(self.templates_path):
            print "Templates file not found at %s. Check your ansible-gluster " \
                    "installation and try again." % self.templates_path
            sys.exit(0)
        self.exec_cmds('cp %s/*' % self.templates_path, self.dirname)

    def mk_dir(self, dirlists):
        for each in dirlists:
            if not os.path.isdir(each):
                self.exec_cmds('mkdir', each)
            elif self.force == 'n':
                print "Directory '%s' already exists. " \
                    "Use -f option to overwrite" % each.split('/')[-1]
                sys.exit(0)
            else:
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
            self.move_templates_to_playbooks()

    def insufficient_param_count(self, section, count):
        print "Please provide %s names for %s devices " \
            "else leave the field empty" % (section, count)
        return False

    def write_unassociated_data(self, section, options, yamlfile):
        data = {}
        data[section] = options
        self.write_yaml(data, yamlfile, False)

    def write_device_data(self, devices, yamlfile):
        options = devices
        self.yamlfile = yamlfile
        self.write_unassociated_data('bricks', options, self.yamlfile)
        return len(options)

    def write_optional_data(self, group_options, device_count):
        self.ret = True
        self.group_options = group_options
        self.device_count = device_count
        self.write_vg_data()
        self.write_pool_data()
        self.write_lv_data()
        self.write_lvols_data()
        self.write_mountpoints_data()
        self.write_mntpath_data()
        return self.ret

    def get_var_file_write_options(self, section, section_name):
        if section in self.group_options:
            options = (
                self.varfile == 'group_vars') and self.config_get_options(
                self.config_parse,
                section) or self.config_get_options(
                self.config_parse,
                section).split(',')
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

    def write_vg_data(self):
        self.vgs = self.get_var_file_write_options('vgs', 'volume group')
        if self.vgs:
            self.write_unassociated_data('vgs', self.vgs, self.yamlfile)
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
        return ConfigParser.ConfigParser(allow_no_value=True)

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

    def __init__(self, config_parse, dirname, group_name, filename):
        self.group_vars_file_path = filename
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
            options = self.config_get_options(self.config_parse, 'devices')
            self.device_count = self.helper.write_device_data(
                options,
                self.group_vars_file_path)
        else:
            print "Not creating group vars since no " \
                "common option for devices provided"
            sys.exit(0)
        group_options.remove('devices')
        return self.helper.write_optional_data(
            group_options,
            self.device_count)


class HostVarsGen(object):

    def __init__(self, config_parse, filenames, hosts):
        self.helper = HelperMethods()
        self.config_parse = config_parse
        self.filenames = filenames
        self.hosts = hosts
        ret = self.create_host_vars()
        if not ret:
            print "Error: Failed creation of hostvars!"
        else:
            print "Host vars for each hosts created!\n" \


    def create_host_vars(self):
        self.ret = True
        for each in self.hosts:
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
                device_names.split(','),
                self.varfilepath[0])
            other_options = self.helper.config_get_options(
                self.config_parse,
                each)
            group_sections = [x for x in other_options if x != 'devices']
            self.ret &= self.helper.write_optional_data(
                group_sections,
                self.device_count)
        return self.ret


if __name__ == '__main__':
    PlaybookGen()
