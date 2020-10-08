#-*- encoding: utf-8

from os import path

from chipmunks import config
from chipmunks.log import logger
from chipmunks import location

class ConfigurationExist(Exception):
    def __init__(self, path):
        self.args = [path]

# interface to etcd watcher
class MonitorMixin(object):
    def init_svcs(self, svc_strs):
        self.services = {}
        for key in svc_strs:
            val = svc_strs[key]
            svc = self.parse_svc(key, val)
            if not svc:
                continue
    
            self.update_svc(svc)

        for key in self.services:
            self.ngx_add_svc(self.services[key], reload = False)

        self.ngx.reload()

    def add_svc(self, key, val):
        svc = self.parse_svc(key, val)
        if not svc:
            return

        self.update_svc(svc)
        self.ngx_add_svc(self.services[svc.name])
        return True

    # interface to etcd watcher
    def del_svc(self, key):
        svc_name, node_id, container_id = self.keydecoder.decode(key, extra = True)
        if not svc_name:
            logger.error("'%s' can't decode as service-name,", key)
            return False

        if svc_name not in self.services:
            logger.error("'%s' not exists.", svc_name)
            return False

        svc = self.services[svc_name]
        svc.delete_host(node_id, container_id)
        if len(svc.hosts) <= 0:
            logger.info("all hosts get down, rm service %s", svc.name)
            del self.services[svc_name]
            self.ngx_del_svc(svc_name)
        else:
            self.ngx_add_svc(svc)
        return True

class Monitor(MonitorMixin):
    def __init__(self, ngx, decoder = None, key_decoder = None):
        self.ngx = ngx
        self.ngx.clear()
        self.services = {}

        if not decoder:
            logger.info('no decoder specified, use default JsonDecoder')
            from chipmunks.coder import coder
            self.decoder = coder

        if not key_decoder:
            logger.info('no key decoder specified, use default.')
            from chipmunks.coder import key_coder
            self.keydecoder = key_coder

    def ngx_del_svc(self, svc_name, reload = True):
        self.ngx.delete(svc_name)

        if reload:
            self.ngx.reload()

    def ngx_add_svc(self, svc, reload = True):
        self.ngx_del_svc(svc.name, reload = reload)

        self.ngx.add(svc)
        if reload:
            self.ngx.reload()
    
    def parse_svc(self, key, val):
        svc_name, node_id, container_id = self.keydecoder.decode(key, extra = True)
        if not svc_name:
            logger.error('parse svc name from key fault: %s', key)
            return None
        
        svc = self.decoder.decode(val)
        svc.add_host(**svc.host, node_id = node_id, container_id = container_id)
        svc.name = svc_name
        return svc

    def update_svc(self, svc):
        if svc.name in self.services:
            self.services[svc.name].merge(svc)
        else:
            self.services[svc.name] = svc
