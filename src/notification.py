#!/usr/bin/env python
'''
#
# cr.imson.co
#
# Automated SNS/Lambda-based notification service via apprise
#
# @author Damian Bushong <katana@odios.us>
#
'''

# pylint: disable=C0116,C0301,C0411,W0511

import json

import apprise

from crimsoncore import LambdaCore

from aws_xray_sdk.core import patch_all
patch_all()

LAMBDA_NAME = 'notification'
LAMBDA = LambdaCore(LAMBDA_NAME)
LAMBDA.init_s3()
LAMBDA.init_ssm()

def lambda_handler(event, context):
    try:
        payload = json.loads(event.get('Records')[0].get('Sns').get('Message'))

        notification = apprise.Apprise()
        notification.add(LAMBDA.get_ssm_parameter('alert', encrypted=True, include_environment=False, include_stack_name=False))

        title = payload.get('title', 'new').capitalize() + ' notification'
        message = payload.get('message', 'Notification text missing.')
        notification_type = payload.get('type', 'info')

        if notification_type == 'error':
            notification_type = apprise.NotifyType.FAILURE
        elif notification_type == 'warning':
            notification_type = apprise.NotifyType.WARNING
        elif notification_type == 'success':
            notification_type = apprise.NotifyType.SUCCESS
        else:
            notification_type = apprise.NotifyType.INFO
        notification.notify(title=title, body=message, notify_type=notification_type)

        LAMBDA.logger.info('Dispatched notification via apprise')
    except Exception as ex:
        LAMBDA.logger.error('Fatal error during script runtime', exc_info=ex)
        # Because we're in the notification lambda...we can't dispatch a panic notification.  :(
        # just raise it and hope someone notices, I guess.

        raise
