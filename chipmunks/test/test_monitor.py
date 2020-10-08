#-*- encoding: utf-8
import unittest

from os import path
import sys
import json
import configparser

sys.path.append(path.dirname(path.dirname(path.dirname(__file__))))

class MonitorTest(unittest.TestCase):
    def test_monitor(self):
        from chipmunks.monitor import Monitor
        from chipmunks.nginx import Nginx

        ngx = Nginx(path.join(path.dirname(__file__), 'mconf.d'))
        monitor = Monitor(ngx)

        svcs = {
            '/chipmunks/nodename/test/containername': json.dumps({
                'host': {
                    'ip': '127.0.0.1',
                    'port': 9232
                },
                'name': 'helloworld',
                'auth_backend': None
            })
        }
        monitor.init_svcs(svcs)
        self.assertTrue(ngx.exists('test'))

        fullpath = ngx.configurations['test']
        self.assertTrue(path.exists(fullpath.location_file))
        monitor.del_svc('/chipmunks/nodename/test/containername')
        self.assertFalse(ngx.exists('test'))
        self.assertFalse(path.exists(fullpath.location_file))

        monitor.del_svc('/chipmunks/nodename/test/containername')
    
    def echo_svc_obj(self):
        print(json.dumps({
                'hosts': [{
                    'ip': '127.0.0.1',
                    'port': 9232
                },
                {
                    'ip': '127.0.0.1',
                    'port': 9234
                }]
            })
        )


if __name__ == '__main__':
    unittest.main()