#!/usr/bin/env python3
"""Read-only scan for AWS resources that keep costing money."""
import argparse
import sys

import boto3
from botocore.exceptions import ClientError

CHECKS = []


def check(label, why):
    def deco(fn):
        CHECKS.append((label, why, fn))
        return fn
    return deco


@check("EC2 instance", "billed every second while running")
def ec2_instances(s, r):
    c = s.client("ec2", region_name=r)
    pages = c.get_paginator("describe_instances").paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
    for p in pages:
        for res in p["Reservations"]:
            for i in res["Instances"]:
                yield i["InstanceId"], i["InstanceType"]


@check("EBS volume", "unattached volumes are billed per GB-month")
def ebs_volumes(s, r):
    c = s.client("ec2", region_name=r)
    pages = c.get_paginator("describe_volumes").paginate(
        Filters=[{"Name": "status", "Values": ["available"]}])
    for p in pages:
        for v in p["Volumes"]:
            yield v["VolumeId"], f'{v["Size"]} GB, not attached'


@check("Elastic IP", "public IPv4 addresses are billed hourly")
def elastic_ips(s, r):
    c = s.client("ec2", region_name=r)
    for a in c.describe_addresses()["Addresses"]:
        if "AssociationId" not in a:
            yield a.get("AllocationId", a["PublicIp"]), f'{a["PublicIp"]}, not associated'


@check("NAT gateway", "billed hourly plus per GB processed")
def nat_gateways(s, r):
    c = s.client("ec2", region_name=r)
    pages = c.get_paginator("describe_nat_gateways").paginate(
        Filter=[{"Name": "state", "Values": ["available"]}])
    for p in pages:
        for n in p["NatGateways"]:
            yield n["NatGatewayId"], n["VpcId"]


@check("Load balancer", "billed hourly while it exists")
def load_balancers(s, r):
    c = s.client("elbv2", region_name=r)
    for p in c.get_paginator("describe_load_balancers").paginate():
        for lb in p["LoadBalancers"]:
            yield lb["LoadBalancerName"], lb["Type"]


@check("RDS instance", "billed hourly while running")
def rds_instances(s, r):
    c = s.client("rds", region_name=r)
    for p in c.get_paginator("describe_db_instances").paginate():
        for db in p["DBInstances"]:
            yield db["DBInstanceIdentifier"], f'{db["DBInstanceClass"]} {db["DBInstanceStatus"]}'


@check("EKS cluster", "control plane is billed hourly")
def eks_clusters(s, r):
    c = s.client("eks", region_name=r)
    for p in c.get_paginator("list_clusters").paginate():
        for name in p["clusters"]:
            yield name, "control plane"


def regions(s, all_regions, one):
    if not all_regions:
        return [one]
    return [x["RegionName"] for x in s.client("ec2", region_name=one).describe_regions()["Regions"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--all-regions", action="store_true")
    args = ap.parse_args()

    s = boto3.Session()
    findings, skipped = [], []
    for r in regions(s, args.all_regions, args.region):
        for label, why, fn in CHECKS:
            try:
                for rid, detail in fn(s, r):
                    findings.append((r, label, rid, detail, why))
            except ClientError as e:
                skipped.append((r, label, e.response["Error"]["Code"]))

    if findings:
        print("RESOURCES THAT MAY BE COSTING MONEY")
        for r, label, rid, detail, why in findings:
            print(f"  [{r}] {label}: {rid} ({detail}) - {why}")
    else:
        print("Nothing billable found.")
    for r, label, code in skipped:
        print(f"  skipped [{r}] {label}: {code}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
