# Docker stuff (SECOND stage of deployment)
**This directory contains docker and docker-compose files for laboranalysis Python application deployment(Microservices variant)**

## Directory structure
The root contains two directories and one 'yml' file: 

* **flask**
* **nginx**
* **docker-compose.yml**

### flask directory
> Contains dockerfile, list of required python modules and web application distro

### nginx directory
> Contains dockerfile and nginx config file

### Deployment process:

To start the second stage of deployment you must successfully complete the first deployment stage. If not so, go to [https://github.com/fgm-public/Python/Applications/Web/Laboranalysis/deployment/Microservices/Ansible](https://github.com/fgm-public/Python/tree/master/Applications/Web/Laboranalysis/deployment/Microservices/Ansible) for further instructions.

* **Copy web application files into flask container build directory**

        root@server:~# cp -r Python/Applications/Web/Laboranalysis/laboranalysis/flask_app/. Python/Applications/Web/Laboranalysis/deployment/Microservices/Docker/flask/laboranalysis

* **Set location to directory which contains docker-compose.yml file**

        root@server:~# cd Python/Applications/Web/Laboranalysis/deployment/Microservices/Docker

* **Start containers build and run process**

        docker-compose up -d

