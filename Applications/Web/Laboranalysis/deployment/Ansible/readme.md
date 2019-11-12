# Ansible stuff
**This directory contains Ansible CM playbooks and roles for laboranalysis Python application deployment.**

## Directory structure
The root of the directory contains two directories: 

* **playbooks**
* **roles**

### playbooks directory
> Contains Ansible playbooks which runs directly

### roles directory
> Contains Ansible roles which include into playbooks and runs indirectly

### Application server Ansible CM configuration directory structure

    /etc/ansible/
    |
    ├──ansible.cfg
    |
    ├──playbooks/
    |  └──deploy-laboranalysis.yml
    |
    └──roles/
        ├──backports
        ├──basedep
        ├──gunicorn
        ├──laboranalysis
        ├──mongodep
        └──pip
