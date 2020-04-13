#!/usr/bin/env python
''' Automated SNS/Lambda-based notification service via apprise. '''

# pylint: disable=C0116,C0301,C0411,W0511

import json
import time

import apprise

from crimsoncore import LambdaCore

from aws_xray_sdk.core import patch_all
patch_all()

LAMBDA_NAME = 'notification'
LAMBDA = LambdaCore(LAMBDA_NAME)
LAMBDA.init_s3()
LAMBDA.init_ssm()

def lambda_handler(event, context):
    start_time = str(int(time.time() * 1000))
    log_name = f'{LAMBDA_NAME}_{start_time}.log'
    LAMBDA.change_logfile(log_name)

    try:
        payload = json.loads(event.get('Records')[0].get('Sns').get('Message'))

        notification = apprise.Apprise()
        # todo: add support for multiple parameter types, depending on the message properties themselves
        notification.add(LAMBDA.get_ssm_parameter('alert', encrypted=True, include_environment=False, include_stack_name=False))

        title = payload.get('title', 'new').capitalize() + ' notification'
        message = payload.get('message', 'Notification text missing.')
        notification.notify(title=title, body=message)

        LAMBDA.logger.info('Dispatched notification via apprise')
    except Exception:
        LAMBDA.logger.error('Fatal error during script runtime', exc_info=True)

        # do our best to fire off the emergency flare
        error_log_dest = f'logs/{LAMBDA_NAME}/{log_name}'
        with open(f'{LAMBDA.config.get_log_path()}/{log_name}', 'r') as file:
            LAMBDA.archive_log_file(error_log_dest, file.read())

        # Because we're in the notification lambda...we can't dispatch a panic notification.  :(
        # just raise it and hope someone notices, I guess.

        raise
    finally:
        LAMBDA.change_logfile(f'{LAMBDA_NAME}_interim.log')
