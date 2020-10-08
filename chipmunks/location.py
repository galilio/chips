from os import path

from jinja2 import Template

from chipmunks import config
from chipmunks.log import logger

def __load_jinja_template(template_path):
    if not path.exists(template_path):
        raise Exception(template_path + ' Not Exists.')

    with open(template_path, 'r') as f:
        template = f.read()
    
    return Template(template)

upstream_template_path = path.join(path.dirname(__file__), 'nginx_upstream.jinja')
location_template_path = path.join(path.dirname(__file__), 'nginx_location.jinja')
full_template_path = path.join(path.dirname(__file__), 'nginx_full.jinja')

location_tpl = __load_jinja_template(location_template_path)
upstream_tpl = __load_jinja_template(upstream_template_path)

t_full = __load_jinja_template(full_template_path)

def generate_to_fp(svc_obj, template, fp):
    logger.debug('generate configure of %s', svc_obj.name)

    auth_backends = svc_obj.auth_backend or config.get('auth.backend')
    need_auth = auth_backends and not svc_obj.auth_bypass and not svc_obj.is_authorize_backend

    if need_auth:
        logger.info('use auth backends: %s', auth_backends)

    params = {'svc': svc_obj,
        'auth': {
            'backend': auth_backends,
            'bypass': not need_auth
        }
    }

    if config.getboolean('template.debug', False):
        logger.debug(template.render(params))

    template.stream(params).dump(fp)


def generate(svc_obj, template, output, auth = None):
    config_path = path.dirname(output)
    if not path.exists(config_path):
        logger.error('%s not exists.', config_path)
        raise Exception(config_path + ' Not Exists.')

    with open(output, 'w+') as f:
        generate_to_fp(svc_obj, template, f)
