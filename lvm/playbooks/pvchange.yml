---
- hosts: rhs_servers
  remote_user: root
  gather_facts: no

  tasks:
  # Change attributes of physical volumes specified
  - name: Change attributes of Physical Volume(s) on all the nodes
    pv: action=change disks="{{ bricks }}"
        options=" -x n"
