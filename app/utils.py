import boto3
import uuid
import os
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_s3(file):
    """Upload a file to S3 and return its public URL (via CloudFront if configured)."""
    if not file or not allowed_file(file.filename):
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"products/{uuid.uuid4().hex}.{ext}"

    s3 = boto3.client(
        's3',
        region_name=current_app.config['AWS_REGION'],
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
    )

    s3.upload_fileobj(
        file,
        current_app.config['S3_BUCKET'],
        filename,
        ExtraArgs={'ContentType': file.content_type}
    )

    cloudfront = current_app.config.get('CLOUDFRONT_DOMAIN')
    if cloudfront:
        return f"https://{cloudfront}/{filename}"
    bucket = current_app.config['S3_BUCKET']
    region = current_app.config['AWS_REGION']
    return f"https://{bucket}.s3.{region}.amazonaws.com/{filename}"

def delete_from_s3(image_url):
    """Delete an image from S3 given its URL."""
    try:
        cloudfront = current_app.config.get('CLOUDFRONT_DOMAIN')
        bucket     = current_app.config['S3_BUCKET']
        if cloudfront and cloudfront in image_url:
            key = image_url.split(cloudfront + '/')[-1]
        else:
            key = '/'.join(image_url.split('/')[-2:])
        s3 = boto3.client(
            's3',
            region_name=current_app.config['AWS_REGION'],
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        )
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception:
        pass   # log in production
