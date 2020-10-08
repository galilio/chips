#-*- encoding: utf-8
import etcd3
from etcd3 import events
import signal
import json
from datetime import datetime

from chipmunks import config
from chipmunks.log import logger
from chipmunks.monitor import Monitor
from chipmunks.nginx import Nginx

class Chipmunks():
    def __init__(self, etcd_cli = None, ngx_cfg = {}, prefix = '/chipmunks/'):
        self.client = etcd_cli
        self.prefix = prefix

        ngx = Nginx(**ngx_cfg)
        self.monitor = Monitor(ngx)

        self.cancel = None
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGHUP, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def run(self):
        '''
        connect to etcd.
        init all data and then watch for it.
        '''
        logger.info('chipmunks watch etced started at %s', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        svcs = {v.key.decode('UTF-8'): val.decode('UTF-8') for val, v in self.client.get_prefix(self.prefix)}
        logger.info('persisted services "%s"', json.dumps(svcs))
        self.monitor.init_svcs(svcs)

        event_generator, self.cancel = self.client.watch_prefix(self.prefix)
        for event in event_generator:
            if isinstance(event, events.PutEvent):
                key, value = event.key.decode('utf-8'), event.value.decode('utf-8')
                logger.info('get etcd put event: %s: %s', key, value)
                self.monitor.add_svc(key, value)
            elif isinstance(event, events.DeleteEvent):
                key = event.key.decode('utf-8')
                logger.info('get etcd delete event %s', key)
                self.monitor.del_svc(key)
            else:
                logger.error("receive etcd unknown type of event(neither Put nor Delete)")

    def stop(self, *args):
        logger.info('stop watch etcd3 at %s', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        if self.cancel:
            self.cancel()