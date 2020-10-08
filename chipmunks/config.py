# -*- encoding: utf-8
from os import path
import configparser

def __get_platform_config_path(config_filename):
    import os
    if 'posix' == os.name:
        return path.join('/etc', 'chipmunks', config_filename)
    raise Exception('Not supported platform ' + os.name)

def __load_config_from_file(config_file):
    cfg = configparser.ConfigParser()
    if not config_file:
        config_file = __get_platform_config_path('config.ini')
    cfg.read(config_file)
    return cfg

__config = configparser.ConfigParser()

def load(config_file):
    global __config
    __config = __load_config_from_file(config_file)

def update(cfg):
    global __config
    __config = cfg

def __call(method, path, default = None):
    parts = path.split('.')
    try:
        val = method(*parts)
        if not val:
            val = default
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        val = default
    
    return val

def get(path, default = None):
    return __call(__config.get, path, default)

def getboolean(path, default = None):
    return __call(__config.getboolean, path, default)

def getint(path, default = None):
    return __call(__config.getint, path, default)

def getfloat(path, default = None):
    return __call(__config.getfloat, path, default)