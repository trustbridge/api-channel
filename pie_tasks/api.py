import shutil
from pathlib import Path

from pie_docker import *
from pie_docker_compose import *
from pie_env_ext import *

from .utils import requires_compose_project_name


ROOT_DIR = Path('.').absolute()
ENV_DIR = ROOT_DIR / 'docker'
DOCKER_COMPOSE = DockerCompose(ROOT_DIR / 'docker/api.docker-compose.yml')


def INSTANCE_ENVIRONMENT():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    return env.from_files(
        ENV_DIR / 'api.env',
        ENV_DIR / f'api_{COMPOSE_PROJECT_NAME}.env',
        ENV_DIR / f'api_{COMPOSE_PROJECT_NAME}_local.env')


@task
def build(no_cache=False):
    options = []
    if no_cache:
        options.append('--no-cache')
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('build', options=options)


@task
def start():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('up', options=['-d', 'api'])


@task
def stop():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down')


@task
def restart():
    stop()
    start()


@task
def reset():
    """Removes the minio data and resets the elasticmq queue"""
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    p=Path(f'docker/volumes/{COMPOSE_PROJECT_NAME}')
    if p.exists():
        shutil.rmtree(p)
    # no action needed to reset elasticmq, just stop and start, I believe


@task
def destroy():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down', options=['-v', '--rmi local'])


@task
def test():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.service('tests').cmd('run', options=['--rm'])


@task
def docker_compose_config():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('config')


@task
def logs():
    try:
        with INSTANCE_ENVIRONMENT():
            DOCKER_COMPOSE.cmd('logs', options=['--tail=40', '-f'])
    except KeyboardInterrupt:
        pass

@task
def show_env():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    Docker().cmd('exec', [f'{COMPOSE_PROJECT_NAME}_api_1', 'env'])
    Docker().cmd('exec', [f'{COMPOSE_PROJECT_NAME}_api_1', 'pip list'])


@task
def bash():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    Docker().cmd('exec', ['-it', f'{COMPOSE_PROJECT_NAME}_api_1', 'bash'])
