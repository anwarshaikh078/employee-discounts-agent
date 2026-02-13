"""
Google Cloud Storage Integration
Stores PDFs in Google Cloud Storage instead of local filesystem
"""

import os
import logging
from typing import List, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

class CloudStorageManager:
    """Manage PDFs in Google Cloud Storage"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize Cloud Storage Manager
        
        Args:
            bucket_name: GCS bucket name. If None, uses local filesystem
        """
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')
        self.use_cloud = self.bucket_name is not None
        
        if self.use_cloud:
            try:
                from google.cloud import storage
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"✅ Connected to GCS bucket: {self.bucket_name}")
            except ImportError:
                logger.error("google-cloud-storage not installed. Install with: pip install google-cloud-storage")
                self.use_cloud = False
            except Exception as e:
                logger.error(f"❌ Failed to connect to GCS: {e}")
                self.use_cloud = False
    
    def list_pdfs(self, prefix: str = "pdfs/") -> List[str]:
        """
        List all PDFs in Cloud Storage
        
        Args:
            prefix: Folder prefix in bucket
        
        Returns:
            List of blob names
        """
        if not self.use_cloud:
            logger.info("Using local filesystem (Cloud Storage not configured)")
            return self._list_local_pdfs()
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            pdf_files = [blob.name for blob in blobs if blob.name.endswith(('.pdf', '.txt'))]
            logger.info(f"Found {len(pdf_files)} PDFs in GCS")
            return pdf_files
        except Exception as e:
            logger.error(f"Error listing PDFs from GCS: {e}")
            return []
    
    def download_pdf(self, blob_name: str) -> bytes:
        """
        Download PDF from Cloud Storage
        
        Args:
            blob_name: Name of blob in GCS
        
        Returns:
            PDF content as bytes
        """
        if not self.use_cloud:
            # Fall back to local filesystem
            return self._read_local_file(blob_name)
        
        try:
            blob = self.bucket.blob(blob_name)
            content = blob.download_as_bytes()
            logger.info(f"✅ Downloaded: {blob_name}")
            return content
        except Exception as e:
            logger.error(f"Error downloading {blob_name}: {e}")
            return b""
    
    def upload_pdf(self, local_path: str, blob_name: str) -> bool:
        """
        Upload PDF to Cloud Storage
        
        Args:
            local_path: Path to local PDF file
            blob_name: Name in GCS bucket
        
        Returns:
            Success status
        """
        if not self.use_cloud:
            logger.warning("Cloud Storage not configured. File not uploaded.")
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
            logger.info(f"✅ Uploaded: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Error uploading {blob_name}: {e}")
            return False
    
    def delete_pdf(self, blob_name: str) -> bool:
        """
        Delete PDF from Cloud Storage
        
        Args:
            blob_name: Name of blob in GCS
        
        Returns:
            Success status
        """
        if not self.use_cloud:
            logger.warning("Cloud Storage not configured.")
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"✅ Deleted: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {blob_name}: {e}")
            return False
    
    # Local filesystem fallback methods
    def _list_local_pdfs(self) -> List[str]:
        """List local PDF files"""
        from pathlib import Path
        pdf_files = []
        pdf_dir = Path("./pdfs")
        
        if pdf_dir.exists():
            pdf_files = [f.name for f in pdf_dir.glob("*.*") if f.suffix in ['.pdf', '.txt']]
        
        return pdf_files
    
    def _read_local_file(self, file_path: str) -> bytes:
        """Read local file"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading local file: {e}")
            return b""


class CloudLoggingManager:
    """Manage logging with Google Cloud Logging"""
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Cloud Logging
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.use_cloud = self.project_id is not None
        
        if self.use_cloud:
            try:
                from google.cloud import logging as cloud_logging
                self.client = cloud_logging.Client(project=self.project_id)
                self.client.setup_logging()
                logger.info(f"✅ Cloud Logging enabled for project: {self.project_id}")
            except ImportError:
                logger.error("google-cloud-logging not installed")
                self.use_cloud = False
            except Exception as e:
                logger.error(f"Failed to setup Cloud Logging: {e}")
                self.use_cloud = False


# Initialization
def init_cloud_services():
    """Initialize all cloud services"""
    storage = CloudStorageManager()
    logging_service = CloudLoggingManager()
    
    return {
        'storage': storage,
        'logging': logging_service
    }