Motivation
 
To replace the existing rhs-system-init.sh script with ansible based solution.
 
Advantages of ansible modules:
Backend setup can be done from one's laptop/desktop (saves time as the number of machines increase)
Flexibility on which drives to use (Earlier if the machine had combination of sd? and vd? init script used to fail)
Flexibility in naming the LVs and VGs.
 
To start using the module, ansible has to be installed on the machine from where
the playbooks are executed.

0. Bootstrapping (Setting up passwordless ssh)
 
On All the nodes on which to setup the GluterFS backend, setup a passwordless ssh login.

  # ssh-copy-id root@hostname
 
1. Installing the glusterfs-ansible module
 
  yum install ./ansible-glusterfs-*-*.rpm
 
The above step will take care of installing the dependencies.
 
2. Setting up the playbooks and inventory
 
Upon installing ansible-glusterfs, copy the glusterfs.conf.sample from
/usr/share/ansible/ansible-glusterfs/doc/ and edit the host details in the conf
file. Configuration file is self explanatory and has abundant documentation.
 
Run the following command:
 
$ playbook-gen.py -c gluster.conf
 
This will generate the necessary inventory files, host and group variables in
the directory where the playbook-gen was run in a directory named `playbooks'
 
 
3. Executing playbooks
 
  $ cd playbooks
  $ ansible-playbook setup-backend.yml -i ansible_hosts
 
  The above command will execute the setup-backend.yml playbook with the
  hosts from the ansible_hosts.
