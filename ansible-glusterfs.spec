%define name ansible-glusterfs
%define version 0
%define release 2

Name:		%{name}
Version:	%{version}
Release:	%{?release}
Summary:	Ansible modules to setup GlusterFS

Group:		Applications/System
License:	GPLv3
URL:		http://www.redhat.com/storage
Source0:	%{name}-%{version}.%{release}.tar.gz
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}.%{release}-buildroot
Requires:	ansible >= 1.9 python >= 2.6

%description
This package provides ansible modules to setup and configure GluterFS. With
these modules you can:
- Configure backend to setup GlusterFS
  * Setup backend with lvm thinpool support
  * Create Filesystem
  * Mount the filesystem
- Tool to generate the playbooks, group_vars/host_vars

%prep
%setup -n %{name}-%{version}.%{release}

%build
# Nothing to build, just copy the files.

%install
mkdir -p %{buildroot}/%{python_sitelib}/ansible/modules/extras/system/lvm/
mkdir -p %{buildroot}/usr/bin
install -m 755 lvm/modules/*.py \
    %{buildroot}/%{python_sitelib}/ansible/modules/extras/system/lvm/
install -m 755 tools/playbook-gen.py %{buildroot}/usr/bin

# Install our playbooks in /usr/share
mkdir -p %{buildroot}/usr/share/ansible/ansible-glusterfs/doc
cp -r lvm/playbooks/ %{buildroot}/usr/share/ansible/ansible-glusterfs/doc

# Install the templates into /usr/share/ansible/ansible-glusterfs/templates
cp -r tools/templates/ %{buildroot}/usr/share/ansible/ansible-glusterfs/

# Documentation
cp -r doc/* %{buildroot}/usr/share/ansible/ansible-glusterfs/doc

%clean
rm -rf %{buildroot}

%files
%{python_sitelib}/ansible/modules/extras/system/lvm/
/usr/share/ansible/ansible-glusterfs/
/usr/bin/playbook-gen.py

%doc README.md

%changelog
* Tue Jun 2 2015 Nandaja Varma <nvarma@redhat.com> 0.2
- Added tool to generate the playbooks

* Tue May 12 2015 Sachidananda Urs <sac@redhat.com> 0.1
- First release.
