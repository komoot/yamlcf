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
    """
    :param line: a line that is printed to stdout
    """
    print(line)


def load(file_name):
    """
    Loads the given file name as yaml document
    :param file_name:
    :return: a yaml document as string with resolved aliases
    """
    with open(file_name, 'r') as f:
        yaml_doc = yaml.load(f)
        yaml.Dumper.ignore_aliases = lambda *args : True
        return yaml.dump(yaml_doc)


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


def show_summary(stack_name):
    r = cf_client.describe_stacks(StackName=stack_name)
    outputs = r['Stacks'][0].get('Outputs')
    if outputs:
        for o in outputs:
            print("{}: {}".format(o['OutputKey'], o['OutputValue']))


def check_finished(_waiter, stack_name):
    r = _waiter._operation_method(StackName=stack_name)
    acceptors = list(_waiter.config.acceptors)
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


def wait_for(waiter_name, stack_name, e_id):
    waiter = cf_client.get_waiter(waiter_name)
    while waiter:
        events = retrieve_events(stack_name, e_id)
        print_events(events)
        if len(events) > 0:
            e_id = events[-1]['EventId']

        if check_finished(waiter, stack_name):
            log("----------------\nsuccessful")
            waiter = None

        time.sleep(1)

def print_events(events):
    for event in events:
        description = event.get('ResourceStatusReason', '')
        log("{t} {ResourceType:<30} {ResourceStatus:<20} {description}".format(t=event['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'), description=description, **event))


def create_update_policy(allow_replace, allow_delete):
    actions = ['Update:Modify']
    if allow_delete:
        actions.append('Update:Delete')
    if allow_replace:
        actions.append('Update:Replace')

    return json.dumps({
        "Statement": [{
            "Effect": "Allow",
            "Action": actions,
            "Principal": "*",
            "Resource": "*"
        }]
    })



parser = argparse.ArgumentParser(description='Yet another cloudformation tool')
parser.add_argument('command', metavar='command', help='create, update, delete, dump')
parser.add_argument('yaml_file', metavar='stack.cf.yaml', help='stack json or yaml file')
parser.add_argument('--stack-name', metavar='stack name', required=False, help='use the given stack name, don\'t guess from filename')
parser.add_argument('--on-failure', default='ROLLBACK', help='behavior for create failures: ROLLBACK, DELETE or DO_NOTHING')
parser.add_argument('--allow-update-replace', default=False, action='store_true', help='allows replacement of resources on update')
parser.add_argument('--allow-update-delete', default=False, action='store_true', help='allows deletion of resources on update')
parser.add_argument('--force', '-f', default=False, action='store_true', help='force deletion or replacement on update or delete without asking')
parser.add_argument('-p', '--parameter', dest='parameters', nargs='*', help='optional stack parameters as key=value')

args = parser.parse_args()

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

parameters = []
if args.parameters:
    for p in args.parameters:
        key, value = p.split('=', 1)
        parameters.append({'ParameterKey': key, 'ParameterValue': value})

stack_document = None

if args.command == "delete":
    cf_client.delete_stack(StackName=stack_name)
    wait_for('stack_delete_complete', stack_name, last_shown_event_id)

elif args.command == "info":
    response = cf_client.describe_stacks(StackName=stack_name)
    stack = response['Stacks'][0]
    log("Description: {}".format(stack['Description']))
    log("Created at:  {}".format(stack['CreationTime']))
    log("Status:      {}".format(stack['StackStatus']))
    log("")
    show_summary(stack_name)

elif args.command == "update":
    stack_document = load(args.yaml_file)
    try:
        response = cf_client.update_stack(
            StackName=stack_name,
            TemplateBody=stack_document,
            Parameters=parameters,
            StackPolicyDuringUpdateBody=create_update_policy(args.force or args.allow_update_replace, args.force or args.allow_update_delete),
            Capabilities=[
                'CAPABILITY_IAM',
            ])
        wait_for('stack_update_complete', stack_name, last_shown_event_id)
    except botocore.exceptions.ClientError as e:
        message = e.response.get('Error', {}).get('Message')
        if message == "No updates are to be performed.":
            log(message)
        else:
            raise e

elif args.command == "create":
    stack_document = load(args.yaml_file)
    response = cf_client.create_stack(
        StackName=stack_name,
        TemplateBody=stack_document,
        Parameters=parameters,
        OnFailure=args.on_failure,
        Capabilities=[
            'CAPABILITY_IAM',
        ])
    wait_for('stack_create_complete', stack_name, last_shown_event_id)
    show_summary(stack_name)


elif args.command == "dump":
    log(load(args.yaml_file))

