import os

import boto3
from moto import mock_aws

import scan

os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def findings(region="us-east-1"):
    s = boto3.Session()
    out = []
    for label, why, fn in scan.CHECKS:
        for rid, detail in fn(s, region):
            out.append((label, rid, detail))
    return out


@mock_aws
def test_clean_account_has_no_findings():
    assert findings() == []


@mock_aws
def test_unattached_volume_is_found():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vol = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)
    result = findings()
    assert ("EBS volume", vol["VolumeId"], "8 GB, not attached") in result


@mock_aws
def test_unassociated_elastic_ip_is_found():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    addr = ec2.allocate_address(Domain="vpc")
    labels = [label for label, _, _ in findings()]
    assert "Elastic IP" in labels
    assert addr["AllocationId"] in [rid for _, rid, _ in findings()]
