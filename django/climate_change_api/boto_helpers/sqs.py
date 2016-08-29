import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


QUEUE_EXISTS_DIFFERENT_ATTRIBUTES_TEXT = ('queue already exists with the same name ' +
                                          'and a different value')


def get_queue(**kwargs):
    """ A helper method to get an SQS queue, updating the queue attributes if they've changed """
    sqs = boto3.resource('sqs')
    try:
        queue = sqs.create_queue(**kwargs)
    except ClientError as error:
        if (error.response['Error']['Code'] == 'QueueAlreadyExists' and
           QUEUE_EXISTS_DIFFERENT_ATTRIBUTES_TEXT in error.response['Error']['Message']):
            queue = sqs.get_queue_by_name(QueueName=kwargs['QueueName'])
            queue.set_attributes(Attributes=kwargs['Attributes'])
        else:
            raise
    return queue
