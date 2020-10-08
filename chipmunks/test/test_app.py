#-*- encoding: utf-8

import unittest

import etcd3

from os import path
import sys
import json
import time
from threading import Thread

sys.path.append(path.dirname(path.dirname(path.dirname(__file__))))

from chipmunks.chips import Chipmunks

class TestApp(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.app = Chipmunks(etcd_cli = etcd3.client(), ngx_cfg = {'configuration_path': path.join(path.dirname(__file__), 'mconf.d')})
        self.svc = {
                'hosts': [{
                    'host': '127.0.0.1',
                    'port': 9232,
                    'node_id': '1231',
                    'container_id': '2cvcaf'
                }]
            }
        self.svc2 = {
                'hosts': [{
                    'host': '127.0.0.1',
                    'port': 9234,
                    'node_id': '1231',
                    'container_id': '2cv2323f'
                }]
        }
        self.thread = Thread(target = self.app.run, args = ())
    
    def test_etcd_message(self):
        self.thread.start()
        time.sleep(1)
        cli = etcd3.client()
        cli.put('/chipmunks/1231/test-service/2cv2323f', json.dumps(self.svc2))
        cli.put('/chipmunks/1231/test-service/2cvcaf', json.dumps(self.svc))

        time.sleep(1)
        self.assertTrue(self.app.monitor.ngx.exists('test-service'))
        cli.delete('/chipmunks/1231/test-service/2cv2323f')
        time.sleep(1)
        self.assertTrue(self.app.monitor.ngx.exists('test-service'))
        time.sleep(1)
        cli.delete('/chipmunks/1231/test-service/2cvcaf')
        time.sleep(1)
        self.assertFalse(self.app.monitor.ngx.exists('test-service'))
        self.app.stop()
        self.thread.join()

if __name__ == '__main__':
    unittest.main()