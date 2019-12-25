# Python applications
**This directory contains Python applications which developed for interactive console using or deploying to the full-fledged OS or Docker-engined server environment.**

## Directory structure
The root of the directory contains two directories: 

* **Console**
* **Web**

### Console directory
> Contains code which intended to run in a interactive console session

### Web directory
> Contains code which intended to run after server deployment

## Secrets
All secrets, passwords, authentication, authorization keys an so on, stored in **'credentials.py'** files which added to *.gitinore* for convenience's sake. Instead of this file, there is its fake double, named **'creds.py'** which contains the same content with bulk secret strings to provide a way for file structure clarification. Therefore,  after cloning this repo, change all 'creds.py' names to 'credentials.py'.
>Or replace python imports:

    from creds import a, b, c
Then, fill these files with your own secrets.  

## Requirements
All requirements stored in **requirements.txt**, which may be installed using:

    pip install -r requirements.txt
