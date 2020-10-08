# chipmunks
![Chipmunks Logo](/chipmunks-tail.png)

Chipmunks（以下简称munks）是用python开发的基于nginx的轻量级微服务网关。

munks可以为你监控集群中所有docker节点中服务，并生成nginx配置文件，将到指定服务的访问请求转发到对应的docker节点指定端口上。

## Why

munks是休闲时候为了不让自己手生的练习之作。在使用python开发时，推行微服务架构其实是不太容易的。python没有java这样完整的微服务生态，非常感谢当时有[nameko](http://github.com/nameko)，解决了基本的服务注册发现和RPC机制（nameko的实现也相当精彩，感兴趣的可以看看）。nameko也有自己的问题，比如服务终端了无法及时发现，导致RPC一直等待。

想为python写一个微服务网关的想法由来已久，我是一个会让工作填满所有时间的人，所以也没有太多的空闲时间来做，趁着2020国庆长假，将这个想法落地了。

## What

munks的整个结构非常简单。如下图所示：

![Munks archtech](/archtech.drawio.png)

munks由绿色的agent和黄色的monitor组成。

agent用于和集群（无论是k8s or swarm或其他形式的集群）中的docker节点交互，监控docker中container的生命周期，并将信息保存到指定的etcd集群中。

monitor利用了etcd3支持watch prefix的特性，监听了/chipmunks这个key prefix，并解析具体的key内容生成了nginx所需要的location的配置文件。

你只需要在nginx的配置文件中include对应的文件即可。

## How

### 0. Requirements

* Docker (in K8S or Swarm)
* etcd3
* Python3.2+

### 1. Install munks agent

当前这个阶段Munks并不打算上到pipy仓库中，主要基于为大家负责的出发点。该项目并没有在生产环境有应用，我尽量让我的考虑更加周全，但是未经验证就上到仓库的确是太草率了。

所以注定了这个教程不会给出非常具体的指令，在使用这个工具的时候你需要明确知道你在做什么。

如果你有自己的私服，相信也应该知道如何加入进去，如果你还没有，但是比较感兴趣，可以试试nexus。

首先你需要clone本项目到docker节点上，然后通过pip进行安装即可。

#### Install Munks Service

如果你使用systemd，那么下面的service文件可以帮你快速的建立起启动脚本

##### Agent Service
```
[Unit]
Description=chipmunks service
After=docker.target
  
[Service]
Type=simple

## replace with munks install location
## chip-agents configure file。
ExecStart=/usr/local/bin/munks agent -c /etc/chips-agent.conf
Restart=on-abort
TimeoutSec=600
  
[Install]
WantedBy=multi-user.target
```

使用systemd相关命令enable并且start。

#### Munks agent 的配置文件实例

最简化配置munks可以只配置etc3即可。如果需要更详细的个性化配置，可以参考cli.py
```
[etcd3]
port = 2379
host = 192.168.77.100
```


### 2. Install Munks monitor

在你的nginx前端机上，同样安装munks。方法也就不在详细给出。

同样如果你使用systemd，那么下面的service文件可以帮出你建立启动脚本

##### Monitor Service
```
[Unit]
Description=chipmunks service
After=docker.target
  
[Service]
Type=simple

## replace with munks install location
## chip-agents configure file。
ExecStart=/usr/local/bin/munks chips -c /etc/chips.conf
Restart=on-abort
TimeoutSec=600
  
[Install]
WantedBy=multi-user.target
```

#### 配置monitor

最简化配置monitor你配置etcd和nginx相关配置，如下

```
[etcd3]
host=192.168.77.100

[nginx]
config_path=devops/chipmunks/vagrant-env.d
pid_path=/usr/local/var/run/nginx.pid 
```

其中config_path为nginx配置文件的路径，该了路径需要配置到nginx中，同时需要nginx pid文件的路径，我们需要读取pid文件并发消息给nginx process让nginxreload配置文件。


### 3. 配置nginx
munks将在config_path中生成两类文件：location.conf和upstream.conf。
需要在nginx中配置include相应的文件即可。

在http段include *.upstream.conf。

在server段include *.location.conf。

如果你不清楚上面的在说什么，说明你对nginx也不太熟悉，可以先了解一下nginx的配置先。

## vagrant

如果你仅仅想试试munks，并且比较了解vagrant，我也提供了vagrant的脚本，帮你快速的建立起docker swarm模式的集群并且安装好munks。

相关的文件可以参考vagrant目录。

## About Logo

Logo是一只松鼠尾巴，特别强调一下是因为Logo是我自己画的，担心大家认不出来。

至于为什么是松鼠尾巴，那是在国庆旅途中，延川到壶口段，本来有点迷糊长时间车程，突然跃出到公路上的一只小松鼠，点亮了后续旅程，小孩子也兴奋起来，大人也开始活跃起来。

回家后仍然记得那只松鼠，干脆在作为munks的Logo吧。
