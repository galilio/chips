#-*- encoding: utf-8
from os import path, listdir, remove, kill
from signal import SIGHUP

import platform

from chipmunks.log import logger
from chipmunks.domain import NginxConfig
'''
load all nginx config with first line chip generated.
when configuration changed update and save to files.
'''

class ConfigurationNotExists(Exception):
    def __init__(self, filename):
        self.args = [filename]

class ServiceDuplicated(Exception):
    def __init__(self, service_name):
        self.args = [service_name]

class Nginx:
    def __init__(self, configuration_path = None, nginx_pid_file = None):
        if not nginx_pid_file:
            nginx_pid_file = self.__get_default_nginx_pid()
            logger.info('nginx_pid_file is empty, use default pid file %s', nginx_pid_file)
        
        if not configuration_path:
            configuration_path = self.__get_default_nginx_conf()
            logger.info('configuration_path is empty, use default configure path %s', configuration_path)

        logger.debug("nginx configuration path is %s", configuration_path)
        logger.debug('nginx pid file is %s', nginx_pid_file)

        self.nginx_pid = self.__get_master_pid_from(nginx_pid_file)
        self.configuration_path = configuration_path
        self.configurations = {}

        self.__load_config()
        self.__dump_config()

    def __dump_config(self):
        for key in self.configurations:
            logger.info('chipmunks generated config %s:%s', key, self.configurations[key])

    def __get_default_nginx_pid(self):
        system = platform.system()
        if system == 'Darwin':
            return '/usr/local/var/run/nginx.pid'
        elif system == 'Linux':
            return '/var/run/nginx.pid'
        else:
            raise Exception('OS {} not supported.'.format(system))
    
    def __get_default_nginx_conf(self):
        system = platform.system()
        if system == 'Darwin':
            return '/usr/local/etc/nginx/servers'
        elif system == 'Linux':
            return '/etc/nginx/conf.d'
        else:
            raise Exception('OS {} not supported.'.format(system))

    def __get_master_pid_from(self, file):
        with open(file, 'r') as f:
            return int(f.read())

    def __load_config(self):
        for config in NginxConfig.load(self.configuration_path):
            self.configurations[config.svc_name] = config

    def exists(self, service_name):
        return service_name in self.configurations

    def services(self):
        return self.configurations.keys()

    def delete(self, service_name):
        logger.debug("delete %s service", service_name)
        if not self.exists(service_name): # not exists, just return.
            logger.error('try delete %s but not exists', service_name)
            return
    
        self.configurations[service_name].delete()
        del self.configurations[service_name] # set service name to empty.

    def add(self, svc):
        if self.exists(svc.name):
            raise ServiceDuplicated(svc.name)

        config = NginxConfig(svc_name = svc.name)
        config.generate(svc, self.configuration_path)
        self.configurations[config.svc_name] = config

    def reload(self):
        try:
            logger.debug("Reload nginx pid %d", self.nginx_pid)
            kill(self.nginx_pid, SIGHUP)
        except Exception as e:
            raise e

    def clear(self):
        configs = self.configurations.keys()
        for service_name in configs:
            try:
                remove(self.configurations[service_name])
            except Exception as e:
                print(e)
                pass

        self.configurations = {}
