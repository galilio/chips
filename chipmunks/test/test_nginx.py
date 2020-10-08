import unittest

from os import path
import sys
import configparser

sys.path.append(path.dirname(path.dirname(path.dirname(__file__))))

class TestNginx(unittest.TestCase):

    def test_nginx_load(self):    
        from chipmunks.nginx import Nginx

        ngx = Nginx()
        self.assertEqual(len(ngx.services()), 0)
    
    def test_nginx_load_custom_config(self):
        from chipmunks.nginx import Nginx

        ngx = Nginx(path.join(path.dirname(__file__), 'conf.d'))

        self.assertTrue(ngx.exists('ucenter_generated'))
        self.assertFalse(ngx.exists('ucenter'))

    def test_nginx_reload(self):
        '''
        update nginx configuration and call reload find changes.
        '''
        from chipmunks.nginx import Nginx
        ngx = Nginx()
        ngx.reload()

    def test_add_delete(self):
        from chipmunks.nginx import Nginx, ServiceDuplicated
        from chipmunks import location
        from chipmunks.domain import Service

        output = path.join(path.dirname(__file__), 'conf.d')
        ngx = Nginx(output)

        svc = Service(name = 'test')
        svc.add_host('127.0.0.1', 8081)
        svc.add_host('127.0.0.2', 8082)
        conf = path.join(output, 'test.conf')

        ngx.add(svc)

        self.assertTrue(ngx.exists('test'))

        with self.assertRaises(ServiceDuplicated):
            ngx.add(svc)
        
        ngx.delete('test')
        self.assertFalse(ngx.exists('test'))
        self.assertFalse(path.exists(conf))


if __name__ == '__main__':
    unittest.main()