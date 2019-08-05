#! /usr/bin/env python2
"""A script containing subroutines to delete all the stacks in a deployment
instance and associated resources like S3 buckets.

This script contains functions to delete:
* all stacks associated with a deployment instance
* all objects associated with a S3 bucket
* all S3 buckets associated with a deployment instance

To run the cleanup script:

- Just pass any dev instance as an argument.

Example: python stack_cleanup.py <dev-instance>

NOTE: The <dev-instance> must exist in account_config.yaml.
"""

import boto3
import time
import argparse
from edl.cloudformation import stack_manager
import logging

logging.basicConfig(level=logging.INFO)

WAIT_TIME = 1

parser = argparse.ArgumentParser(description="Delete Stack and Resources.")
parser.add_argument("instance", type=str)

ARGS = parser.parse_args()
STACK_MANAGER = stack_manager.StackManager(ARGS.instance)

s3_resource = boto3.resource("s3", stack_manager.DEFAULT_REGION)


def delete_all_stacks(stack_list):
    all_stacks = list(stack_list)
    for name in stack_list:
        for region in stack_manager.REGIONS:
            if region in name:
                print("Deleting Stack {}".format(name))
                STACK_MANAGER._regional_clients[region].delete_stack(name)
                all_stacks.remove(name)
    """ Deleting stacks without region suffix """
    if all_stacks:
        for name in all_stacks:
            print("Deleting Stack {}".format(name))
            STACK_MANAGER._client.delete_stack(name)


def delete_all_buckets(bucket_list):
    for bucket in bucket_list:
        print("Deleting all objects from bucket: {}".format(bucket))
        delete_all_objects(bucket)
        time.sleep(WAIT_TIME)
        print("Deleting bucket: {}".format(bucket))
        s3_resource.Bucket(bucket).delete()


def delete_all_objects(bucket_name):
    res = []
    bucket = s3_resource.Bucket(bucket_name)
    for obj_version in bucket.object_versions.all():
        res.append({"Key": obj_version.object_key, "VersionId": obj_version.id})
    if len(res) > 0:
        bucket.delete_objects(Delete={"Objects": res})
    else:
        print("Bucket is EMPTY")


def wrap_hifen(instance):
    return "-{}-".format(instance)


def list_all_stacks(instance):
    stack_list = []
    for region in stack_manager.REGIONS:
        stack_state_dict = STACK_MANAGER._regional_clients[region]._get_stacks()
        regional_list = [
            name for name in stack_state_dict.keys() if wrap_hifen(instance) in name
        ]
        stack_list.extend(regional_list)
    return stack_list


def list_all_buckets(instance):
    list_response = STACK_MANAGER._client._s3_client.list_buckets()
    bucket_list = [
        s["Name"] for s in list_response["Buckets"] if wrap_hifen(instance) in s["Name"]
    ]
    return bucket_list


def run():
    print("\nLISTING ALL STACKS FOR INSTANCE: {}\n".format(ARGS.instance))
    stack_list = list_all_stacks(ARGS.instance)
    for stack in stack_list:
        print(stack)

    print("\nLISTING ALL BUCKETS FOR INSTANCE: {}\n".format(ARGS.instance))
    bucket_list = list_all_buckets(ARGS.instance)
    for bucket in bucket_list:
        print(bucket)

    user_input = raw_input(
        "\nWould you like to delete all stacks and buckets "
        "for '{}' instance? (Y/N): ".format(ARGS.instance)
    )

    if user_input == "Y" or user_input == "y":
        """ Deleting Stacks """
        delete_all_stacks(stack_list)

        """ Deleting Buckets """
        delete_all_buckets(bucket_list)
        print("\nAll the stacks and buckets have been deleted as per selection!")
    elif user_input == "N" or user_input == "n":
        print("\nNone of the stacks or buckets have been deleted as per selection!")
    else:
        print("\nInvalid Choice! Please type 'Y' or 'N'")


if __name__ == "__main__":

    run()
