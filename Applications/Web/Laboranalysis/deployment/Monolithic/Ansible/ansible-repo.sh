
#!/bin/sh

# Add ansible repository
echo 'deb http://ppa.launchpad.net/ansible/ansible/ubuntu trusty main' \
>>   /etc/apt/sources.list.d/ansible.list

# Add ansible repository key
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367