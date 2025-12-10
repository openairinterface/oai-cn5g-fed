<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">OpenAirInterface 5G Core Network Deployment: How to debug the Network Functions? </font></b>
    </td>
  </tr>
</table>

Currently there is no special tool for debugging the problems of core network components. Though there are certain methods which we use in our team to diagnose an issue.

This page content expects you to read [deployment pre-requisites](./DEPLOY_PRE_REQUISITES.md) and try to deploy a [mini](./DEPLOY_SA5G_MINI_WITH_GNBSIM.md) or [basic](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md) normal deployment.

**TABLE OF CONTENTS**

1.  [Building images in debug mode](#1-building-images-in-debug-mode)
2.  [Debugger deployment of core network functions](#2-debugger-deployment-of-core-network-functions)
3.  [Basic debugging](#3-basic-debugging)
4.  [How to report an issue?](#4-how-to-report-an-issue)

# 1. Building images in debug mode

By default all the Dockerfiles present in any network function repository (AMF, SMF, NRF, UPF, UDR, UDM, AUSF) produce `info` level logs. This is done to reduce the image size and have a better performance. If a user wants debug information to get more logs then make below changes in `dockerfile` of any network function.

This way user will have more logs and can have better understanding. To build any core network image in debug mode follow the below steps **after cloning the network function repository**, the example is for AMF, 

```bash
# clone amf repository 
git clone -b <prefered_branch or develop> https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf.git
cd oai-cn5g-amf/docker/
# Depending on the environment where the image will be used choose the correct dockerfile
vi/vim/nano/subl Dockerfile.amf.ubuntu
# replace the line RUN ./build_amf --clean --Verbose --build-type Release --jobs with below 
# RUN ./build_amf --clean --Verbose --build-type Debug --jobs
```

The same can be done for bare-metal deployment of any core network function, just build with `Debug` tag in `./build_amf`. There will be no change in running the core network function. Everything will be the same, now when the network function is started there will be extra logs with `[debug]` tag apart from the normal `[info ]`

## 1.1 Building the image with code inside (Only for development purpose)

If you are interested in doing development you can leave the code inside the container. This is good for developers, they can code in docker-environment. They can even mount the code as a volume so that they can use their preferred editor (though vim/nano/vi are the best).

### 1.1.1 Building a Developer Image

The example below is only for AMF, you need to repeat it for all network functions.

``` bash
git clone -b <prefered_branch or develop> https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf.git
docker build -f oai-cn5g-amf/docker/Dockerfile.amf.ubuntu --target oai-amf-builder --tag oai-amf-builder:develop --no-cache oai-cn5g-amf/
```

This will build your image and later you can use this image with the command below,

``` bash
docker run --privileged -d --name oai-amf-development oai-amf-builder:develop sleep infinity
docker exec -it oai-amf-development bash
# You will be inside the container
```

But in this approach you have to code inside the container using vi/vim/nano no graphical interface, but if you want a graphical interface then you can mount the code

### 1.1.2 Mounting Code As Volume

The example below is only for AMF you need to repeat it for all network functions.

``` bash
git clone -b <prefered_branch or develop> https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf.git /openair-amf
docker run --privileged -d --name oai-amf-development --volume openair-amf:/openair-amf  ubuntu:bionic sleep infinity
docker exec -it oai-amf-development bash
# below command is same for all network functions
sudo apt update && apt install psmisc software-properties-common git vim nano vi gnupg
# now you can peform the build
cd /openair-amf/build/scripts
/build_amf --install-deps --force
/build_amf --clean --Verbose --build-type Debug --jobs
```

Now you are ready, start developing and testing.

# 2. Debugger deployment of core network functions

It is really important to safely keep the logs and configuration of core network components in case of an error. If they are deployed in bare-metal the logs and the configuration can be easily retrieved based on how the core network is started. Here are some tips related to running/deploying core network in different environments,

# 2.1 Deploying as a process (bare-metal deployment preferred by developers)

1. In case of all-in-one deployment process, there can be conflicting dependencies between different components of core network. These conflicts have to be resolved on a case by case basis by the user. You can follow the wiki of each network function for bare-metal installation. For amf follow [this](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf/-/wikis/Installation).
2. Once all the core-network components are build in debug mode with their dependencies, store the logs in a file rather than printing on the terminal.
3. All the configuration files should be stored in one place so that it is easy to retrieve.

```bash
# storing logs and configuration in your preferred location
nohup /usr/local/bin/amf -c /tmp/oai-cn-5g/config/amf.conf -o >> /tmp/oai-cn-5g/logs/amf.log 2>&1
```

The command above will launch the network function in the background, and all the logs can be seen using `tail -100f /tmp/oai-cn-5g/logs/amf.log`. In case you want to stop the component, kill its process process using `pkill <component-name>` or `ps -eaf`

# 2.2 Docker environment (Recommended)

Using docker environment for deployment and development is the preferred way because there, it is easy to have dedicated working environment for each network component. It is lightweight and easy to manage. The docker-compose provided in [tutorials](./DEPLOY_HOME.md) is good for learning how the OAI core network works and how to use it. But if the user wants to change some parameters which are not variable or not allowed using docker-compose then it is hard to use the docker-compose approach. If the user wants to provide their own configuration file then it is better to change the docker-compose. Follow the steps below to create a new developer/debugger specific docker-compose,

## 2.2.1 Prerequisites

1. Build the docker-images in debug mode following the [previous section](#1-building-images-in-debug-mode)
2. Create a new folder `oai-docker-compose`
3. In the `oai-docker-compose` folder create `confs`, `logs`, `entrypoints` and `healthchecks` folders
4. In the `confs` folder copy the configuration files for each component you want to use [example](../docker-compose/conf)
5. Create empty log files for the component you want to use in the `logs` folder using the `touch` command
6. Copy [oai_db1.sql](../docker-compose/database/oai_db1.sql), make a user database depending on the IMSI, LTKEY and Opc. New user entry can be added after this [line](../docker-compose/database/oai_db1.sql#L193)

```
# Create the directory structure
mkdir ~/oai-docker-compose
mkdir -p ~/oai-docker-compose/confs
mkdir -p ~/oai-docker-compose/logs
mkdir -p ~/oai-docker-compose/entrypoints
mkdir -p ~/oai-docker-compose/healthchecks

# Create empty log files
touch ~/oai-docker-compose/logs/amf.log
touch ~/oai-docker-compose/logs/smf.log
touch ~/oai-docker-compose/logs/nrf.log
touch ~/oai-docker-compose/logs/upf.log
```

### 2.2.2 Create entrypoint files

The example of amf entrypoint.sh is below, for other network functions it is analogous.

```bash
#!/bin/bash
set -eumb

echo "Running amf to check logs use tail -100f ~/oai-docker-compose/logs/amf.log"
exec nohup /usr/local/bin/amf -c /openair-amf/etc/config.yaml -o >> /openair-amf/etc/amf.log 2>&1
```

In the example above, replace amf with nrf, smf to create entrypoints for nrf and smf. For spgwu it is slightly different.

```
echo "Running spgwu to check logs use tail -100f ~/oai-docker-compose/logs/spgw_u.log"
exec nohup /usr/local/bin/upf -c /oai-upf/etc/config.yaml -o >> /oai-upf/etc/spgw_u.log 2>&1
```

Create entry-points for all the network functions which are required.

# 2.2.3 Health checks

The healthchecks can be directly used from [here](../docker-compose/healthscripts), copy them in the `healthchecks` folder.

# 2.2.4 Creating docker-compose

To run this docker-compose the network `demo-oai-public-net` should be created.

```yaml
services:
    oai-nrf:
        container_name: oai-nrf
        image: oai-nrf:develop
        entrypoint: ["/openair-nrf/bin/nrf-entrypoint.sh"]
        restart: always
        volumes:
            - ./confs/basic_nrf_config.yaml:/openair-nrf/etc/config.yaml
            - ./entrypoints/nrf-entrypoint.sh:/openair-nrf/bin/nrf-entrypoint.sh
            - ./logs/nrf.log:/openair-nrf/etc/nrf.log:rw
        networks:
            public_net:
                ipv4_address: 192.168.70.130
    mysql:
        container_name: mysql
        image: mysql:8.0
        restart: always
        volumes:
            - ./oai_db.sql:/docker-entrypoint-initdb.d/oai_db.sql
            - ./healthchecks/mysql-healthcheck.sh:/tmp/mysql-healthcheck.sh
        depends_on:
            - oai-nrf
        environment:
            - TZ=Europe/Paris
            - MYSQL_DATABASE=oai_db
            - MYSQL_USER=test
            - MYSQL_PASSWORD=test
            - MYSQL_ROOT_PASSWORD=linux
        healthcheck:
            test: /bin/bash -c "/tmp/mysql-healthcheck.sh"
            interval: 10s
            timeout: 5s
            retries: 5
        networks:
            public_net:
                ipv4_address: 192.168.70.131
    oai-amf:
        container_name: oai-amf
        image: oai-amf:develop
        entrypoint: ["/openair-amf/bin/amf-entrypoint.sh"]
        restart: always
        depends_on:
            - mysql
        volumes:
            - ./confs/basic_nrf_config.yaml:/openair-amf/etc/config.yaml
            - ./entrypoints/amf-entrypoint.sh:/openair-amf/bin/amf-entrypoint.sh
            - ./logs/amf.log:/openair-amf/etc/amf.log:rw
        networks:
            public_net:
                ipv4_address: 192.168.70.132
    oai-smf:
        container_name: oai-smf
        entrypoint: ["/openair-smf/bin/smf-entrypoint.sh"]
        restart: always
        image: oai-smf:develop
        depends_on:
            - oai-amf
        volumes:
            - ./entrypoints/smf.sh:/openair-smf/bin/smf-entrypoint.sh
            - ./confs/basic_nrf_config.yaml:/openair-smf/etc/config.yaml
            - ./logs/smf.log:/openair-smf/etc/smf.log:rw
        networks:
            public_net:
                ipv4_address: 192.168.70.133
    oai-upf:
        container_name: "oai-upf"
        image: oai-upf:develop
        entrypoint: ["/openair-upf/bin/spgwu-entrypoint.sh"]
        restart: always
        depends_on:
            - oai-smf
        cap_add:
            - NET_ADMIN
            - SYS_ADMIN
        cap_drop:
            - ALL
        privileged: true
        volumes:
            - ./entrypoints/upf.sh:/openair-upf/bin/upf-entrypoint.sh
            - ./confs/basic_nrf_config.yaml:/openair-upf/etc/config.yaml
            - ./logs/spgw_u.log:/openair-upf/etc/spgw_u.log:rw
        networks:
            public_net:
                ipv4_address: 192.168.70.134
networks:
    public_net:
        external:
           name: demo-oai-public-net
```


## 2.2.5 Playing with docker-compose

```
# start docker-compose
docker-compose -p <project-name> -f <file-name> up -d
# if changes are made in the conf files located in ./confs/, restart the container/service
docker-compose -p <project-name> -f <file-name> restart <service-name>
# force recreate a service
docker-compose -p <project-name> -f <file-name> up -d <service-name> --force-create
# in case the code is present inside the container and some changes are made, then just restart the container, never remove it
docker-compose -p <project-name> -f <file-name> restart <service-name>
# stop the containers/service
docker-compose -p <project-name> -f <file-name> stop <service-name>
# remove the deployment
docker-compose -p <project-name> -f <file-name> down -t 0
```

Network components configuration is present in `~/oai-docker-compose/confs/` the logs are present in `~/oai-docker-compose/logs/`. There will be only one log file and it will contain huge amount of logs. If needed this can also be rotated to avoid having one bulky file. To make it rotate, make changes in the entrypoint.sh script.

# 3. Basic debugging

1. Building the images in debug mode will provide more information about UE attach-detach process.
2. Capture packets to understand message flow between the components and encapsulation-decapsulation.
3. Check the UE subscription information is available in the Mysql database and the OPC is correctly configured in AMF.


# 4. How to report an issue?

To report an issue regarding any-component of CN5G or attach-detach procedure follow the procedure below,

1. Share the testing scenario, what the test is trying to achieve.
2. Share Debug logs of the 5GCN components and packet capture/tcpdump of the 5GCN components. Depending on where the packets are captured, take care of the interface on which packets are captured. Also it will be nice to capture packets using a filter `ngap || http || pfcp || gtp`
3. If you have an issue with testing then you can send an email at openair5g-cn@lists.eurecom.fr with the configuration files, log files in debug mode and pcaps with appropriate filters.
4. You can also report an issue or create a bug directly on GitLab, to create an account on our GitLab please follow [this procedure].(../CONTRIBUTING.md)
