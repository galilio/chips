#-*- encoding: utf-8
import os, re
from os import path

from chipmunks import config
from chipmunks.log import logger

from chipmunks.location import generate, location_tpl, upstream_tpl

class Service():
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.host = kwargs.get('host')
        self.auth_backend = kwargs.get('auth_backend', None)
        self.auth_bypass = kwargs.get('auth_bypass', self.auth_backend == None)

        self.hosts = []

        self.is_authorize_backend = kwargs.get('authorize', False)
    
    def __str__(self):
        return '{}@{}:{}'.format(self.name, self.host, self.port)

    def add_host(self, ip = None, port = 8080, node_id = None, container_id = None):
        if not self.hosts:
            self.hosts = []

        self.hosts.append({'ip': ip, 'port': port, 'node_id': node_id, 'container_id': container_id})

    def filter(self, x, node_id, container_id):
        if container_id:
            return x['container_id'] == container_id
        elif node_id:
            return x['node_id'] == node_id

        return False

    def delete_host(self, node_id = None, container_id = None):
        logger.debug('delete host of %s %s', node_id, container_id)
        self.hosts = [x for x in self.hosts if not self.filter(x, node_id, container_id)]

    def merge(self, svc):
        if svc.name != self.name:
            logger.error('merge service failed, service name not match.(%s != %s)', svc.name, self.name)
            return
        if not svc.hosts:
            logger.error('merge empty hosts.')
            return

        for host in svc.hosts:
            self.add_host(**host)

location_pattern = re.compile(r'([a-zA-Z_][a-zA-Z_\-0-9]*)\.location')

class NginxConfig(object):
    def __init__(self, **kwargs):
        self.svc_name = kwargs.get('svc_name')
        self.location_file = kwargs.get('location')
        self.upstream_file = kwargs.get('upstream')
    
    def generate(self, svc, config_dir):
        self.location_file = self.__generate_location(svc, config_dir)
        self.upstream_file = self.__generate_upstream(svc, config_dir)

    def __safe_delete(self, fp):
        try:
            os.remove(fp)
        except:
            logger.error("Delete svc %s file[%s] failed.", self.svc_name, fp)
            return False
        return True

    def delete(self):
        self.__safe_delete(self.location_file)
        self.__safe_delete(self.upstream_file)

    @classmethod
    def load(cls, config_dir):
        for fn in os.listdir(config_dir):
            if path.isdir(fn):
                logger.info('%s is dir, ignore.', fn)
                continue
            
            filename, ext = path.splitext(fn)
            if ext != '.conf':
                logger.info('%s not a nginx configuration file.', fn)
                continue

            m = location_pattern.match(filename)
            if not m:
                logger.info("%s is not location file, ignore.", fn)
                continue

            svc_name = m.group(1)
            location_path = path.join(config_dir, fn)
            upstream_filepath = path.join(config_dir, '{}.upstream.conf'.format(svc_name))
            
            if not path.exists(upstream_filepath):
                logger.info("%s missing upstream file, ignore.", fn)
                continue

            yield cls(svc_name = svc_name, location = location_path, upstream = upstream_filepath)

    def __generate_location(self, svc, config_dir):
        filepath = path.join(config_dir, '{}.location.conf'.format(self.svc_name))
        generate(svc, location_tpl, filepath)
        return filepath

    def __generate_upstream(self, svc, config_dir):
        filepath = path.join(config_dir, '{}.upstream.conf'.format(self.svc_name))
        generate(svc, upstream_tpl, filepath)
        return filepath