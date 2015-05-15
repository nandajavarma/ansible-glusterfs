%define name ansible-glusterfs
%define version 0
%define release 1

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

%prep
%setup -n %{name}-%{version}.%{release}

%build
# Nothing to build, just copy the files.

%install
mkdir -p %{buildroot}/%{python_sitelib}/ansible/modules/extras/system/lvm/
cp -r lvm/modules/*.py \
    %{buildroot}/%{python_sitelib}/ansible/modules/extras/system/lvm/

# Install our playbooks in /usr/share
mkdir -p %{buildroot}/usr/share/ansible/ansible-glusterfs/lvm
cp -r lvm/playbooks/ %{buildroot}/usr/share/ansible/ansible-glusterfs/lvm

# Documentation
cp -r doc %{buildroot}/usr/share/ansible/ansible-glusterfs/

%clean
rm -rf %{buildroot}

%files
%{python_sitelib}/ansible/modules/extras/system/lvm/
/usr/share/ansible/ansible-glusterfs/

%doc README.md

%changelog
* Tue May 12 2015 Sachidananda Urs <sac@redhat.com> 0.1
- First release.
