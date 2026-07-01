import boto3
import yaml
from botocore.exceptions import ClientError
from botocore.config import Config


REQUIRED_VIDEOS = [
    "front_stereo_camera_left.mp4",
    "back_stereo_camera_left.mp4",
    "left_stereo_camera_left.mp4",
    "right_stereo_camera_left.mp4",
]

CAMERA_VIEWS = [
    "front_stereo_camera_left",
    "back_stereo_camera_left",
    "left_stereo_camera_left",
    "right_stereo_camera_left",
]


def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


class CssClient:
    def __init__(self, config):
        self.bucket = config["bucket"]
        self.endpoint_url = config.get("endpoint_url")
        self.base_prefix = config["base_prefix"].strip("/")
        self.location = config["location"]
        self.data_subdir = config.get("data_subdir", "data").strip("/")
        self.profile = config.get("profile")

        if self.profile:
            session = boto3.Session(profile_name=self.profile)
        else:
            session = boto3.Session()

        self.s3 = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name="us-east-1",
            config=Config(
                s3={
                    "addressing_style": "path",
                    "payload_signing_enabled": False,
                },
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def sequence_prefix(self, sequence_name):
        return f"{self.base_prefix}/{self.location}/{self.data_subdir}/{sequence_name}"

    def key(self, sequence_name, filename):
        return f"{self.sequence_prefix(sequence_name)}/{filename}"

    def metadata_key(self, sequence_name):
        return self.key(sequence_name, "hoi_metadata.yaml")

    def exists(self, key):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ["404", "NoSuchKey", "NotFound"]:
                return False
            raise

    def upload_file(self, local_path, sequence_name, filename):
        key = self.key(sequence_name, filename)
        self.s3.upload_file(str(local_path), self.bucket, key)
        return key

    def upload_yaml_text(self, sequence_name, yaml_text):
        key = self.metadata_key(sequence_name)
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=yaml_text.encode("utf-8"),
            ContentType="application/x-yaml",
        )
        return key

    def presigned_url(self, sequence_name, filename, expires_seconds=3600):
        key = self.key(sequence_name, filename)
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def list_sequences(self):
        root_prefix = f"{self.base_prefix}/{self.location}/{self.data_subdir}/"
        paginator = self.s3.get_paginator("list_objects_v2")

        sequence_names = set()

        for page in paginator.paginate(
            Bucket=self.bucket,
            Prefix=root_prefix,
            Delimiter="/",
        ):
            for item in page.get("CommonPrefixes", []):
                prefix = item["Prefix"].rstrip("/")
                sequence_names.add(prefix.split("/")[-1])

        results = []

        for sequence_name in sorted(sequence_names):
            missing_videos = []

            for video in REQUIRED_VIDEOS:
                if not self.exists(self.key(sequence_name, video)):
                    missing_videos.append(video)

            has_metadata = self.exists(self.metadata_key(sequence_name))

            results.append({
                "sequence_name": sequence_name,
                "location": self.location,
                "missing_videos": missing_videos,
                "has_metadata": has_metadata,
                "ready": len(missing_videos) == 0 and not has_metadata,
            })

        return results
