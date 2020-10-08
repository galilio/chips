#-*- encoding: utf-8
import configparser
from os import path

from chipmunks import config

def mock_config():
    cfg = configparser.ConfigParser()
    cfg.add_section('template')
    cfg.add_section('nginx')
    cfg.add_section('auth')
    cfg.set('template', 'debug', 'true')
    cfg.set('nginx', 'config_path', path.dirname(__file__))
    cfg.set('auth', 'backend', '/auth')
    config.update(cfg)