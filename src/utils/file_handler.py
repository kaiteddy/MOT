"""
File handling utilities for the MOT OCR system.
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import magic
from PIL import Image
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class FileHandler:
    """Handle file operations for the MOT OCR system."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.results_dir = Path(settings.results_dir)
        self.max_file_size = settings.max_file_size
        self.allowed_extensions = settings.allowed_extensions
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def is_valid_image_file(self, filename: str) -> bool:
        """
        Check if the file has a valid image extension.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if valid image file, False otherwise
        """
        if not filename:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.allowed_extensions
    
    async def save_upload_file(self, upload_file: UploadFile, request_id: str) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            upload_file: FastAPI UploadFile object
            request_id: Unique request identifier
            
        Returns:
            Path to saved file
            
        Raises:
            ValueError: If file validation fails
        """
        if not upload_file.filename:
            raise ValueError("No filename provided")
        
        # Generate unique filename
        file_ext = Path(upload_file.filename).suffix.lower()
        unique_filename = f"{request_id}_{uuid.uuid4().hex}{file_ext}"
        file_path = self.upload_dir / unique_filename
        
        try:
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await upload_file.read()
                await f.write(content)
            
            # Validate file type by content
            if not self._validate_image_content(file_path):
                await self.cleanup_file(str(file_path))
                raise ValueError("Invalid image file content")
            
            # Validate and potentially resize image
            await self._process_image(file_path)
            
            logger.info(f"Saved upload file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            # Cleanup on error
            if file_path.exists():
                await self.cleanup_file(str(file_path))
            raise ValueError(f"Failed to save file: {str(e)}")
    
    def _validate_image_content(self, file_path: Path) -> bool:
        """
        Validate image file content using python-magic.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid image, False otherwise
        """
        try:
            # Check MIME type
            mime_type = magic.from_file(str(file_path), mime=True)
            valid_mime_types = [
                'image/jpeg', 'image/png', 'image/bmp', 
                'image/tiff', 'image/webp', 'image/gif'
            ]
            
            if mime_type not in valid_mime_types:
                logger.warning(f"Invalid MIME type: {mime_type}")
                return False
            
            # Try to open with PIL
            with Image.open(file_path) as img:
                img.verify()
            
            return True
            
        except Exception as e:
            logger.warning(f"Image validation failed: {str(e)}")
            return False
    
    async def _process_image(self, file_path: Path):
        """
        Process and potentially resize image.
        
        Args:
            file_path: Path to the image file
        """
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ['RGB', 'L']:
                    img = img.convert('RGB')
                
                # Check if resizing is needed
                max_width = settings.image_max_width
                max_height = settings.image_max_height
                
                if img.size[0] > max_width or img.size[1] > max_height:
                    # Calculate new size maintaining aspect ratio
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # Save resized image
                    img.save(file_path, format='JPEG', quality=95, optimize=True)
                    logger.info(f"Resized image: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {str(e)}")
            raise ValueError(f"Image processing failed: {str(e)}")
    
    async def cleanup_file(self, file_path: str):
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")
    
    async def save_result(self, request_id: str, result_data: dict) -> str:
        """
        Save extraction result to file.
        
        Args:
            request_id: Request identifier
            result_data: Result data to save
            
        Returns:
            Path to saved result file
        """
        import json
        
        result_filename = f"{request_id}_result.json"
        result_path = self.results_dir / result_filename
        
        try:
            async with aiofiles.open(result_path, 'w') as f:
                await f.write(json.dumps(result_data, indent=2, default=str))
            
            logger.info(f"Saved result file: {result_path}")
            return str(result_path)
            
        except Exception as e:
            logger.error(f"Failed to save result: {str(e)}")
            raise ValueError(f"Failed to save result: {str(e)}")
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"error": "File not found"}
            
            stat = path.stat()
            
            info = {
                "filename": path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "extension": path.suffix.lower()
            }
            
            # Add image-specific info if it's an image
            if self.is_valid_image_file(path.name):
                try:
                    with Image.open(path) as img:
                        info.update({
                            "width": img.size[0],
                            "height": img.size[1],
                            "mode": img.mode,
                            "format": img.format
                        })
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    async def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old files from upload and results directories.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
        """
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        directories = [self.upload_dir, self.results_dir]
        
        for directory in directories:
            try:
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        
                        if file_age > max_age_seconds:
                            file_path.unlink()
                            logger.debug(f"Cleaned up old file: {file_path}")
                            
            except Exception as e:
                logger.warning(f"Failed to cleanup directory {directory}: {str(e)}")
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics for upload and results directories.
        
        Returns:
            Dictionary with storage statistics
        """
        def get_dir_size(directory: Path) -> tuple:
            """Get directory size and file count."""
            total_size = 0
            file_count = 0
            
            try:
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
            except Exception:
                pass
            
            return total_size, file_count
        
        upload_size, upload_files = get_dir_size(self.upload_dir)
        results_size, results_files = get_dir_size(self.results_dir)
        
        return {
            "upload_directory": {
                "path": str(self.upload_dir),
                "size_bytes": upload_size,
                "file_count": upload_files
            },
            "results_directory": {
                "path": str(self.results_dir),
                "size_bytes": results_size,
                "file_count": results_files
            },
            "total_size_bytes": upload_size + results_size,
            "total_files": upload_files + results_files
        }
