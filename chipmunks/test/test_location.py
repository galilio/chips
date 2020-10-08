import unittest

from os import path
import sys
import configparser

sys.path.append(path.dirname(path.dirname(path.dirname(__file__))))

from chipmunks import config
from chipmunks.domain import Service

from chipmunks.test.mock import mock_config

class TestLocationGenerate(unittest.TestCase):
    def setUp(self):
        mock_config()
    
    def test_generate(self):
        test_content = '''# chip-generated
upstream test {
    server 127.0.0.1:80;
}

location /test {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffers 16 4k;
    proxy_buffer_size 2k;
    proxy_pass http://test;
}'''

        from chipmunks import location
        from io import StringIO
        svc = Service(name = 'test', auth_bypass = True)
        svc.add_host('127.0.0.1', port = 80)

        fp = StringIO()
        location.generate_to_fp(svc, location.t_full, fp)
        self.assertEqual(fp.getvalue(), test_content)
    
    def test_auth(self):
        test_content = '''# chip-generated
upstream test {
    server 127.0.0.1:80;
    server 192.168.0.1:8080;
}

location /test {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffers 16 4k;
    proxy_buffer_size 2k;
    proxy_pass http://test;
}'''
        from chipmunks import location
        from io import StringIO
        svc = Service(name = 'test', port = 80)
        svc.add_host('127.0.0.1', port = 80)
        svc.add_host('192.168.0.1')
        
        fp = StringIO()
        location.generate_to_fp(svc, location.t_full, fp)
        self.assertEqual(fp.getvalue(), test_content)
    
    def test_authorize_location(self):
        test_content = '''# chip-generated
upstream test {
    server 127.0.0.1:80;
}

location /test {
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
    proxy_pass http://test;
}'''
        from chipmunks import location
        from io import StringIO
        svc = Service(name = 'test', authorize = True)
        svc.add_host('127.0.0.1', port = 80)

        fp = StringIO()
        location.generate_to_fp(svc, location.t_full, fp)
        self.assertEqual(fp.getvalue(), test_content)

if __name__ == '__main__':
    unittest.main()