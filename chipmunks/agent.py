#-*- encoding: utf-8
import docker
import etcd3
import json
import threading

from chipmunks.log import logger
from chipmunks.coder import key_coder, coder

class SwarmContainerMixin(object):
    def get_service_name(self, container):
        if 'com.docker.swarm.service.name' not in container.labels:
            return None

        return container.labels['com.docker.swarm.service.name']

class LabelMixin(object):
    def get_auth_backend(self, container):
        self.auth_backend = container.labels.get('com.chipmunks.auth_backend', None)

class Container(SwarmContainerMixin, LabelMixin):
    def __init__(self, container):
        self.name = container.name
        self.image = container.image.tags
        self.id = container.id

        port_mappings = container.ports
        self.port = 0
        for key in port_mappings:
            ports = port_mappings[key]
            for port in ports:
                logger.debug('%s -> %s', key, port['HostPort'])
                if '0.0.0.0' == port['HostIp']:
                    self.port = int(port['HostPort'])

        self.is_running = 'running' == container.status
        self.svc_name = self.get_service_name(container)
        self.auth_backend = self.get_auth_backend(container)

    def __str__(self):
        return '{id} - {name}  {svc_name} {is_running}'.format(**self.__dict__)

    @classmethod
    def load_all(cls, client):
        logger.debug('load all containers.')

        ret = {}

        containers = client.containers.list()
        for container  in containers:
            logger.debug('get container %s %s', container.id, container.name)
            obj = cls(container)
            ret[obj.id] = obj
        
        return ret
    
class ContainerMixin(object):
    def container_kill(self, cli, id = None, **kwargs):
        self.remove_container(id)

    def container_start(self, cli, id = None, **kwargs):
        container = cli.containers.list(filters = {'id': id})
        if len(container) <= 0:
            logger.error('container started but not found %s', id)
            return
        
        for ctn in container:
            self.add_container(id, Container(ctn))

class SWarmNodeMinxin(object):
    def node_update(self, cli, **kwargs):
        node_id = kwargs.get('Actor')['ID']
        state = kwargs.get('Actor')['Attributes']['state.new']
        if 'down' == state:
            if self.notifier:
                self.notifier.cleanup(node_id)

class NeedSwarmException(Exception):
    def __init__(self, *args):
        self.args = ['''docker need run under swarm mode.
        Please referer https://docs.docker.com/engine/swarm/ to initialize and configure swarm.
        ''']

class Monitor(ContainerMixin, SWarmNodeMinxin):
    '''
    node container status monitor.
    process docker events result.
    add or del container.
    '''
    def __init__(self, containers = None):
        self.lock = threading.Lock() # lock object.
        if containers == None:
            self.containers = {}
        else:
            self.containers = containers
    
    def __str__(self):
        return '\n'.join([key for key in self.containers])

    def set_notifier(self, notifier):
        self.notifier = notifier
        if self.notifier:
            self.notifier.cleanup()

        self.lock.acquire()
        for key in self.containers:
            container = self.containers[key]
            self.notifier.add_service(container)
        self.lock.release()

    def add_container(self, id, container):
        if id in self.containers:
            logger.info('add container but already exists. try replace %s', id)

        self.lock.acquire()
        self.containers[id] = container
        if self.notifier:
            self.notifier.add_service(container)
        self.lock.release()

    def remove_container(self, id):
        self.lock.acquire()
        container = None
        if id in self.containers:
            container = self.containers[id]
            del self.containers[id]
        else:
            logger.error('remove container but not exists %s, just ignore.')
        if self.notifier:
            self.notifier.del_service(container)
        self.lock.release()

class Notifier(object):
    '''
    notifier container status changed use etcd3
    '''
    def __init__(self, etcd, node = None):
        self.etcd = etcd
        if node:
            self.node = node
        else:
            self.node = {'id': None, 'ip': None}

    def cleanup(self, node_id = None):
        key_prefix = key_coder.encode(node_id or self.node['id'])
        self.etcd.delete_prefix(key_prefix)

    def to_svc(self, container):
        return {'name':  container.name,
            'host': {
                'ip':  self.node['ip'],
                'port':  container.port,
            },
            'auth_backend':  container.auth_backend
        }

    def add_service(self, container):
        svc = self.to_svc(container)
        key = self.get_key(container)
        self.etcd.put(key, coder.encode(svc))

    def get_key(self, container):
        return key_coder.encode(self.node['id'], container.svc_name, container.id)

    def del_service(self, container):
        key = self.get_key(container)
        self.etcd.delete(key)

class Agent:
    '''
    App to watch docker container status.
    1. load all container oneshot.
    2. watch container changes from event.
    '''
    def __init__(self, docker, etcd):
        '''
        kwargs:
            docker:
                base_url: host
                tls_verify: False
                tls: tls configure object.
        '''
        self.cli = docker

        node_id, node_ip = self.ensure_node_id()
        logger.info('current node is %s[%s]', node_id, node_ip)
        notifier = Notifier(etcd, node = {'id': node_id, 'ip': node_ip})
        
        self.monitor = Monitor(Container.load_all(self.cli))
        self.monitor.set_notifier(notifier)

        self.events = self.cli.events()

    def ensure_node_id(self):
        info = self.cli.info()
        if not 'Swarm' in info:
            raise NeedSwarmException()

        swarm = info['Swarm']
        if 'active' != swarm['LocalNodeState']:
            raise NeedSwarmException()
    
        return swarm['NodeID'], swarm['NodeAddr']

    def process_event(self, event):
        mtd = getattr(self.monitor, '{Type}_{Action}'.format(**event), None)
        if mtd:
            mtd(self.cli, **event)
        else:
            logger.debug('no processor to handle %s_%s', event['Type'], event['Action'])

    def run(self):
        '''
        watch docker event.
        '''
        for event in self.events:
            event_obj = json.loads(event.decode('utf-8')) # docker event encoded in json-format.
            logger.debug('docker event: {}'.format(event_obj))
            self.process_event(event_obj)
            

    def stop(self):
        if self.events:
            self.events.close()
        pass