#-*- encoding: utf-8
import sys
import etcd3
import os
import docker
import argparse

def pack_etcd_config(config):
    etcd3_config = {}
    host = config.get('etcd3.host')
    if host:
        etcd3_config['host'] = host
    
    etcd3_config['port'] = config.getint('etcd3.port', 2379)
    etcd3_config['ca_cert'] = config.get('etcd3.ca_cert')
    etcd3_config['cert_key'] = config.get('etcd3.cert_key')
    etcd3_config['cert_cert'] = config.get('etcd3.cert_cert')
    etcd3_config['user'] = config.get('etcd3.user')
    etcd3_config['password'] = config.get('etcd3.password')
    return etcd3_config

def pack_docker_config(config):
    params = {}
    host = config.get('docker.host')
    if host:
        params['base_url'] = host
    else:
        params['base_url'] = os.environ.get('DOCKER_HOST')
    
    cert_path = config.get('docker.cert_path')
    tls_verify = config.getboolean('docker.tls_verify', False)
    enable_tls = cert_path or tls_verify
    if not enable_tls:
        print(params)
        return params

    if not cert_path:
        cert_path = os.path.join(os.path.expanduser('~'), '.docker')
    tls = docker.TLSConfig(
        client_cert = (os.path.join(cert_path, 'cert.pem'),
            os.path.join(cert_path, 'key.pem')),
        ca_cert = os.path.join(cert_path, 'ca.pem'),
        verify = tls_verify,
        assert_hostname = False
    )
    params['tls'] = tls
    return params

def make_chips_app(config):
    from chipmunks.chips import Chipmunks
    etcd3_config = pack_etcd_config(config)
    etcd3_cli = etcd3.client(**etcd3_config)
    nginx_config = {
        'configuration_path': config.get('nginx.config_path'),
        'nginx_pid_file': config.get('nginx.pid_path')
    }

    key_prefix = config.get('chipmunks.prefix', '/chipmunks/')
    return Chipmunks(etcd3_cli, nginx_config, key_prefix)

def make_agent_app(config):
    from chipmunks.agent import Agent
    etcd3_config = pack_etcd_config(config)
    etcd3_cli = etcd3.client(**etcd3_config)

    docker_params = pack_docker_config(config)
    docker_cli = docker.DockerClient(timeout = 60, version = None, **docker_params)

    return Agent(docker_cli, etcd3_cli)

def chips(ctx, config):
    '''
    This program watch etcd3 event and generate nginx configuration file.
    '''
    from chipmunks import config as munks_config 
    munks_config.load(config)

    from chipmunks.log import logger
    from chipmunks.chips import Chipmunks
    import logging

    if ctx.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info('load configuration from %s', config)
    app = make_chips_app(munks_config)
    app.run()

def agent(ctx, config):
    '''
    This program watch docker container changes and send changed through etcd3
    '''
    from chipmunks import config as munks_config
    munks_config.load(config)

    from chipmunks.log import logger
    from chipmunks.agent import Agent
    import logging

    if ctx.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info('load configuration from %s', config)
    app = make_agent_app(munks_config)
    app.run()

def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Enable verbose mode.')
    parser.add_argument('program', type = str, default = 'agent', help = 'Program to Run [chips, agent]')
    parser.add_argument('-c', '--config', type = str, help = 'Config file path')
    return parser

def main():
    parser = setup_parser()
    args = parser.parse_args()

    if args.program == 'agent':
        agent(args, args.config)
    elif args.program == 'chips':
        chips(args, args.config)
    else:
        print("Unknown Command {}".format(args.program))

if __name__ == '__main__':
    main()