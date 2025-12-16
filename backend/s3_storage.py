"""
AWS S3 Storage Integration for AI Video Clipper
Handles upload/download of videos and clips to/from S3
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from pathlib import Path
from typing import Optional, List, Dict
import mimetypes

logger = logging.getLogger(__name__)


class S3Storage:
    """
    S3 storage handler for video uploads and clip outputs
    
    Environment Variables:
        AWS_S3_BUCKET: S3 bucket name
        AWS_REGION: AWS region (default: ap-southeast-1)
        AWS_ACCESS_KEY_ID: Access key (optional if using IAM role)
        AWS_SECRET_ACCESS_KEY: Secret key (optional if using IAM role)
    """
    
    def __init__(self):
        self.bucket_name = os.getenv('AWS_S3_BUCKET', '')
        self.region = os.getenv('AWS_REGION', 'ap-southeast-1')
        self.enabled = bool(self.bucket_name)
        
        if self.enabled:
            try:
                # Try to use IAM role first, then fall back to credentials
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.region
                )
                # Test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ S3 Storage enabled: {self.bucket_name}")
            except NoCredentialsError:
                logger.warning("⚠️ AWS credentials not found, S3 disabled")
                self.enabled = False
            except ClientError as e:
                logger.warning(f"⚠️ S3 connection failed: {e}")
                self.enabled = False
        else:
            logger.info("📁 Using local storage (S3 not configured)")
    
    def upload_file(self, local_path: str, s3_key: str, 
                    content_type: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to S3
        
        Args:
            local_path: Path to local file
            s3_key: S3 object key (path in bucket)
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            S3 URL if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            if content_type is None:
                content_type = mimetypes.guess_type(local_path)[0] or 'application/octet-stream'
            
            extra_args = {
                'ContentType': content_type
            }
            
            self.s3_client.upload_file(
                local_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"📤 Uploaded to S3: {s3_key}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            return None
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local destination path
        
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            
            logger.info(f"📥 Downloaded from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ S3 download failed: {e}")
            return False
    
    def generate_presigned_url(self, s3_key: str, 
                                expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)
        
        Returns:
            Presigned URL or None
        """
        if not self.enabled:
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3"""
        if not self.enabled:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"🗑️ Deleted from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ S3 delete failed: {e}")
            return False
    
    def list_files(self, prefix: str = '') -> List[Dict]:
        """
        List files in S3 with given prefix
        
        Args:
            prefix: S3 key prefix (folder path)
        
        Returns:
            List of file metadata dicts
        """
        if not self.enabled:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag']
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"❌ S3 list failed: {e}")
            return []
    
    def upload_video(self, local_path: str, job_id: str) -> Optional[str]:
        """
        Upload a video file with proper organization
        
        Args:
            local_path: Path to video file
            job_id: Job identifier for organization
        
        Returns:
            S3 URL or None
        """
        filename = Path(local_path).name
        s3_key = f"uploads/{job_id}/{filename}"
        return self.upload_file(local_path, s3_key, 'video/mp4')
    
    def upload_clip(self, local_path: str, job_id: str) -> Optional[str]:
        """
        Upload a generated clip
        
        Args:
            local_path: Path to clip file
            job_id: Job identifier
        
        Returns:
            S3 URL or None
        """
        filename = Path(local_path).name
        s3_key = f"outputs/{job_id}/{filename}"
        return self.upload_file(local_path, s3_key, 'video/mp4')
    
    def sync_outputs_to_s3(self, job_id: str, local_output_dir: str) -> List[str]:
        """
        Sync all output clips for a job to S3
        
        Args:
            job_id: Job identifier
            local_output_dir: Local outputs directory path
        
        Returns:
            List of S3 URLs for uploaded files
        """
        if not self.enabled:
            return []
        
        uploaded = []
        output_path = Path(local_output_dir) / job_id
        
        if not output_path.exists():
            return []
        
        for file_path in output_path.glob('*.mp4'):
            s3_url = self.upload_clip(str(file_path), job_id)
            if s3_url:
                uploaded.append(s3_url)
        
        logger.info(f"📤 Synced {len(uploaded)} clips to S3 for job {job_id}")
        return uploaded
    
    def get_storage_stats(self) -> Dict:
        """Get S3 bucket storage statistics"""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            # Get bucket size using CloudWatch (requires additional permissions)
            # For now, calculate from listing
            uploads = self.list_files('uploads/')
            outputs = self.list_files('outputs/')
            
            upload_size = sum(f['size'] for f in uploads)
            output_size = sum(f['size'] for f in outputs)
            
            return {
                'enabled': True,
                'bucket': self.bucket_name,
                'region': self.region,
                'uploads_count': len(uploads),
                'uploads_size_bytes': upload_size,
                'outputs_count': len(outputs),
                'outputs_size_bytes': output_size,
                'total_size_bytes': upload_size + output_size
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get S3 stats: {e}")
            return {
                'enabled': True,
                'bucket': self.bucket_name,
                'error': str(e)
            }


# Singleton instance
_s3_storage = None

def get_s3_storage() -> S3Storage:
    """Get singleton S3Storage instance"""
    global _s3_storage
    if _s3_storage is None:
        _s3_storage = S3Storage()
    return _s3_storage
