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

### Deployment process:

* **Install Debian 9 (stretch)**

* **Install some packages**

        root@server:~# apt install git mc aptitude dirmngr -y

* **Clone this repository**

        root@server:~# git clone https://github.com/fgm-public/Python

* **Copy application files into /etc/ansible**

        root@server:~# cp -r Python\Applications\Web\Laboranalysis\laboranalysis Python\Applications\Web\Laboranalysis\deployment\Ansible\roles\laboranalysis\files

* **Change dir to 'Python/Applications/Web/Laboranalysis/deployment/Ansible'**

        root@server:~# cd Python/Applications/Web/Laboranalysis/deployment/Ansible

* **Run 'ansible.addrepo' script**

        root@server:~# /bin/sh Python/Applications/Web/Laboranalysis/deployment/Ansible/ansible.addrepo

* **Update package manager cache**

        root@server:~# aptitude update

* **Install Ansible**

        root@server:~# aptitude install ansible

* **Copy roles and playbooks directories into /etc/ansible**

        root@server:~# cp -r {roles,playbooks} /etc/ansible

* **Change dir to playbooks and run 'deploy-laboranalysis.yml' playbook**

        root@server:~# ansible-playbook deploy-laboranalysis.yml