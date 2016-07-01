#!/usr/bin/env python3

#
# Simple cloudformation cli tool
#

import argparse
import botocore
import botocore.session
import botocore.exceptions
import yaml
import json
import time

def name_from_file(yaml_file):
    """
        Takes a yaml file name and generates a stack-name from it.
    """
    for suffix in [".cf.yaml", ".cf.json", ".yaml", ".json"]:
        if yaml_file.endswith(suffix):
            end_index = len(yaml_file) - len(suffix)
            return yaml_file[:end_index]
    return yaml_file


def log(line):
    print(line)


def load(yaml_file):
    with open(yaml_file, 'r') as f:
        return yaml.load(f)


def to_json(stack_document):
    return json.dumps(stack_document, sort_keys=True, indent=4)


def retrieve_events(stack_name, last_shown_event_id=None, limit=None):
    try:
        r = cf_client.describe_stack_events(StackName=stack_name)
        events = r['StackEvents']
        if limit:
            events = events[0:limit]

        # filter already shown events
        if last_shown_event_id:
            for i in range(0, len(events)):
                if events[i]['EventId'] == last_shown_event_id:
                    events = events[0:i]
                    break

        events.reverse()
        return events
    except botocore.exceptions.ClientError:
        return []


def retrieve_last_event_id(_stack_name):
    _events = retrieve_events(_stack_name, None)
    if len(_events) > 0:
        return _events[-1]['EventId']
    else:
        return None


def check_finished(_waiter, stack_name):
    r = _waiter._operation_method(StackName=stack_name)
    acceptors = list(waiter.config.acceptors)
    current_state = 'waiting'
    for acceptor in acceptors:
        if acceptor.matcher_func(r):
            current_state = acceptor.state
            break
    else:
        # If none of the acceptors matched, we should
        # transition to the failure state if an error
        # response was received.
        if 'Error' in r:
            # Transition to the failure state, which we can
            # just handle here by raising an exception.
            raise ValueError(r['Error'].get('Message', 'Unknown'))
    if current_state == 'success':
        return True
    if current_state == 'failure':
        raise ValueError('Waiter encountered a terminal failure state')


def print_events(events):
    for event in events:
        description = event.get('ResourceStatusReason', '')
        log("{t} {ResourceType:<30} {ResourceStatus:<20} {description}".format(t=event['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'), description=description, **event))


parser = argparse.ArgumentParser(description='Yet another cloudformation tool')
parser.add_argument('command', metavar='command', help='create, update, delete')
parser.add_argument('yaml_file', metavar='stack.cf.yaml', help='stack json or yaml file')
parser.add_argument('--stack-name', metavar='stack name', required=False, help='use the given stack name, don\'t guess from filename')
args = parser.parse_args()

if args.command == "cat":
    log(to_json(load(args.yaml_file)))
    exit(0)

# AWS configuration
session = botocore.session.get_session()
cf_client = session.create_client('cloudformation')

# Stack name detection
if args.stack_name:
    stack_name = args.stack_name
else:
    stack_name = name_from_file(args.yaml_file)
log("Stack name:  {}".format(stack_name))

last_shown_event_id = retrieve_last_event_id(stack_name)

waiter = None
stack_document = None

# Execute given command
if args.command == "delete":
    cf_client.delete_stack(StackName=stack_name)
    waiter = cf_client.get_waiter('stack_delete_complete')

elif args.command == "info":
    response = cf_client.describe_stacks(StackName=stack_name)
    stack = response['Stacks'][0]
    log("Description: {}".format(stack['Description']))
    log("Created at:  {}".format(stack['CreationTime']))
    log("Status:      {}".format(stack['StackStatus']))
    log("")

else:
    stack_document = load(args.yaml_file)
    if args.command == "update":
        try:
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=to_json(stack_document),
                Capabilities=[
                    'CAPABILITY_IAM',
                ])
            waiter = cf_client.get_waiter('stack_update_complete')
        except botocore.exceptions.ClientError as e:
            message = e.response.get('Error', {}).get('Message')
            if message == "No updates are to be performed.":
                log(message)
            else:
                raise e

    elif args.command == "create":
        response = cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=to_json(stack_document),
            Capabilities=[
                'CAPABILITY_IAM',
            ])
        waiter = cf_client.get_waiter('stack_create_complete')


while waiter:
    events = retrieve_events(stack_name, last_shown_event_id)
    print_events(events)
    if len(events) > 0:
        last_shown_event_id = events[-1]['EventId']

    if check_finished(waiter, stack_name):
        log("----------------\nsuccessful")
        waiter = None

    time.sleep(1)

if not stack_document or 'Outputs' in stack_document:
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response['Stacks'][0].get('Outputs')
    if outputs:
        log("-------[ Stack output ]-------")
        log(yaml.dump(outputs, default_flow_style=False))

