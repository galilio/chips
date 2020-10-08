#-*- encoding: utf-8
import unittest
import docker
import sys
from os import path
from threading import Thread
import time
import etcd3

sys.path.append(path.dirname(path.dirname(path.dirname(__file__))))

from chipmunks.agent import Container, Agent
import logging
from chipmunks.log import logger

logger.setLevel(logging.DEBUG)

class TestDocks(unittest.TestCase):
    def setUp(self):
        self.cli = docker.from_env()
        self.etcd3 = etcd3.client()
        
    def test_container(self):
        containers = Container.load_all(self.cli)
        for id in containers:
            ct = containers[id]
            print(ct)

    def test_monitor(self):
        agent = Agent(self.cli, self.etcd3)

        thread = Thread(target = agent.run, args = ())
        thread.start()
        for idx in range(50):
            print(agent.monitor)
            print('--------------')
            time.sleep(1)
        agent.stop()
        thread.join()
    

if __name__ == '__main__':
    unittest.main()