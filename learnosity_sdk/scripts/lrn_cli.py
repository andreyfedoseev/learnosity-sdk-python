#!/usr/bin/env python

import click
import logging
import json

from learnosity_sdk.request import DataApi


DEFAULT_API_DATA_HOST = 'https://data.learnosity.com'
DEFAULT_API_DATA_VERSION = 'v1'


# TODO: use credentials from environment/file
@click.group()
@click.option('--consumer-key', '-k',
              help='API key for desired consumer',
              default='yis0TYCu7U9V4o7M')
# This is a public Learnosity Demos consumer
# XXX: never commit any other secret anywhere!
@click.option('--consumer-secret', '-S',
              help='Secret associated with the consumer key',
              default='74c5fd430cf1242a527f6223aebd42d30464be22')
@click.option('--log-level', '-l', default='info',
              help='log level')
@click.option('--requests-log-level', '-L', default='warning',
              help='log level for the HTTP requests')
@click.pass_context
def cli(ctx, consumer_key, consumer_secret,
        log_level='info',
        requests_log_level='warning',
        ):
    ''' Prepare and send request to Learnosity APIs '''
    ctx.ensure_object(dict)
    ctx.obj['consumer_key'] = consumer_key
    ctx.obj['consumer_secret'] = consumer_secret

    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        level=log_level.upper())

    requests_logger = logging.getLogger('urllib3')
    requests_logger.setLevel(requests_log_level.upper())
    requests_logger.propagate = True

    logger = logging.getLogger()
    ctx.obj['logger'] = logger


@cli.command()
@click.option('--file', '-f', type=click.File('r'),
              default='-')
@click.argument('endpoint_url')
@click.pass_context
def data(ctx, endpoint_url, file, action='get'):
    ''' Make a request to Data API.

    The endpoint_url can be:

    - a full URL: https://data.learnosity.com/v1/itembank/items

    - a REST path, with or without version:

      - /v1/itembank/items

      - /itembank/items

    '''
    ctx.ensure_object(dict)
    consumer_key = ctx.obj['consumer_key']
    consumer_secret = ctx.obj['consumer_secret']
    logger = ctx.obj['logger']

    # TODO: factor this out into a separate function
    if not endpoint_url.startswith('http'):
        if not endpoint_url.startswith('/'):  # Prepend leading / if missing
            endpoint_url = '/' + endpoint_url
        if not endpoint_url.startswith('/v'):  # API version
            endpoint_url = '/' + DEFAULT_API_DATA_VERSION + endpoint_url
        endpoint_url = DEFAULT_API_DATA_HOST + endpoint_url

    data_api = DataApi()

    security = _make_data_security_packet(consumer_key, consumer_secret)

    logger.debug('Reading request json ...')
    data_request = json.load(file)

    logger.debug('Sending %s request to %s ...' %
                 (action.upper(), endpoint_url))
    try: 
        r = data_api.request(endpoint_url, security, consumer_secret,
                             data_request, action)
    except Exception as e:
        logger.error('Exception sending request to %s: %s' %
                     (endpoint_url, e))
        return False

    # TODO: factor this out into a separate function
    if r.status_code != 200:
        logger.error('Error %d sending request to %s: %s' %
                     # TODO: try to extract an error message from r.json()
                     (r.status_code, endpoint_url, r.text))
        return False
    response = r.json()
    if not response['meta']['status']:
        logger.error('Incorrect status for request to %s: %s' %
                     (endpoint_url, response['meta']['message']))
        return False

    data = response['data']

    print(json.dumps(data, indent=True))
    return True


def _make_data_security_packet(consumer_key, consumer_secret, domain='localhost'):
    return {
        'consumer_key': consumer_key,
        'domain': domain,
    }