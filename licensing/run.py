"""WSGI entry point; defaults to loopback unless run in the Docker container."""
import os
from waitress import serve
from licensing.app import create_app

if __name__ == '__main__':
    options = {}
    proxy = os.environ.get('LED_TRUSTED_PROXY')
    if proxy:
        options.update(trusted_proxy=proxy, trusted_proxy_count=1,
                       trusted_proxy_headers={'x-forwarded-for', 'x-forwarded-proto'})
    serve(create_app(), host=os.environ.get('LED_BIND', '127.0.0.1'),
          port=int(os.environ.get('PORT', '8000')), threads=4,
          max_request_body_size=16384, **options)
