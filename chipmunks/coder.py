#-*- encoding: utf8
import re
import json

from chipmunks.log import logger
from chipmunks.domain import Service

class InvalidServiceName(Exception):
    def __init__(self, name):
        self.args = name

class PathKeyCoder:
    def __init__(self, prefix = 'chipmunks'):
        self.prefix = 'chipmunks'
        self.key_name_p = re.compile(r'/{}/([a-z0-9]+)/([a-zA-Z_][a-zA-Z\-_0-9]*)/([a-z0-9]+)'.format(self.prefix))
        self.service_name_p = re.compile(r'[a-zA-Z_][a-zA-Z_\-0-9]*')
        

    def decode(self, key, extra = False):
        m = self.key_name_p.match(key)
        if not m:
            return None
        
        if extra:
            return m.group(2), m.group(1), m.group(3)
        
        return m.group(2)

    def encode(self, node, svc_name = None, container = None):
        if svc_name and not self.service_name_p.match(svc_name):
            raise InvalidServiceName(svc_name)
    
        if not svc_name:
            return '/{prefix}/{node_id}/'.format(prefix = self.prefix, node_id = node)
        elif container:
            return '/{prefix}/{node_id}/{svc_name}/{container}'.format(prefix = self.prefix, svc_name = svc_name, node_id= node, container = container)
        else:
            return '/{prefix}/{node_id}/{svc_name}/'.format(prefix = self.prefix, svc_name = svc_name, node_id = node)

class JsonCoder:
    def __init__(self):
        pass

    def decode(self, svc):
        logger.debug("try decode %s", svc)
        mapper = json.loads(svc)
        return Service(**mapper)

    def encode(self, svc):
        return json.dumps(svc)

coder = JsonCoder()

key_coder = PathKeyCoder()