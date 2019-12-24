# Docker stuff (SECOND stage of deployment)
**This directory contains docker and docker-compose files for laboranalysis Python application deployment (Microservices variant)**

## Directory structure
The root contains six directories and one 'yml' file: 

* **analyze**
* **flask**
* **harvest**
* **nginx**
* **notify**
* **python**
* **docker-compose.yml**

### analyze directory
> Contains dockerfile, list of required python modules and analyze application distro

### flask directory
> Contains dockerfile, list of required python modules and web application distro

### harvest directory
> Contains dockerfile, list of required python modules and harvest application distro

### nginx directory
> Contains dockerfile and nginx config file

### notify directory
> Contains dockerfile, list of required python modules and notify application distro

### python directory
> Contains dockerfile and list of required python modules

### docker-compose.yml
> Instructions to promote all necessary infrastructure to laboranalysis application functioning

### Deployment process:

To start the second stage of deployment you must successfully complete the first deployment stage. If not so, go to [https://github.com/fgm-public/Python/Applications/Web/Laboranalysis/deployment/Microservices/Ansible](https://github.com/fgm-public/Python/tree/master/Applications/Web/Laboranalysis/deployment/Microservices/Ansible) for further instructions.

Don't forget to add your credentials to the flask, harvest, analyze and notify applications folders!
Here [https://github.com/fgm-public/Python/Applications/Web/Laboranalysis/deployment/Microservices/Ansible](https://github.com/fgm-public/Python/tree/master/Applications) it described in more detail.

* **Set location to directory which contains docker-compose.yml file**

        root@server:~# cd Python/Applications/Web/Laboranalysis/deployment/Microservices/Docker

* **Start containers build and run process**

        docker-compose up
