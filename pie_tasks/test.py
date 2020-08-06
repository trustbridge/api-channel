from pprint import pprint

import requests

from pie_docker_compose import *
from pie_env_ext import *
from pie_tasks.api import INSTANCE_ENVIRONMENT

ROOT_DIR = Path('.').absolute()

ENV_DIR = ROOT_DIR / 'docker'
DOCKER_COMPOSE = DockerCompose(ROOT_DIR / 'docker/api.docker-compose.yml')


@task
def start():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('up', options=['-d', 'test_callback_server'])


@task
def stop():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('stop', options=['test_callback_server'])


@task
def subscribe():
    """Subscribe to start receiving messages (should be executed on foreign endpoint)"""
    with INSTANCE_ENVIRONMENT():
        bind_port = env.get('API_BIND_HOST_PORT')
        test_bind_port = env.get('TEST_CALLBACK_SERVER_BIND_HOST_PORT')
        url = f'http://localhost:{bind_port}/messages/subscriptions/by_jurisdiction'
        callback_url = f'http://host.docker.internal:{test_bind_port}/callback'
        jurisdiction = env.get('JURISDICTION')

        data = {
            'hub.mode': 'subscribe',
            'hub.callback': callback_url,
            'hub.topic': jurisdiction
        }
        print(f"url: {url}")
        print("data:")
        pprint(data)
        response = requests.post(url, data=data)
        if response.status_code != 202:
            print(f"subscribe failed, status:{response.status_code}, text:{response.text}")
            return
        print(f'subscribed')


@task
def send_message():
    """Expect to see a request to /messages/incoming on the other end (foreign endpoint)"""
    with INSTANCE_ENVIRONMENT():
        bind_port = env.get('API_BIND_HOST_PORT')
        msg = {
            'sender': 'AU',
            'receiver': 'SG',
            'subject': 'AU.123.sgblah',
            'obj': 'QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n',
            'predicate': 'UN.CEFACT.Trade.CertificateOfOrigin.created'
        }
        response = requests.post(f'http://localhost:{bind_port}/messages', json=msg)
        if response.status_code != 200:
            print(f"Failed to send message, status:{response.status_code}, text:{response.text}")
            return
        data = response.json()
        print('Message sent, id:%s' % data['id'])
