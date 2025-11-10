"""
Import job schemas for file upload and processing.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ImportJobStatus(str, Enum):
    """Import job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileUploadRequest(BaseModel):
    """Request for file upload."""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    upload_id: str = Field(..., description="Unique upload ID")
    upload_url: str = Field(..., description="Presigned URL for upload")
    expires_at: datetime = Field(..., description="URL expiration time")


class ImportJobCreateRequest(BaseModel):
    """Request to create import job."""
    upload_id: str = Field(..., description="Upload ID from file upload")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (csv, excel, pdf, txt)")
    apply_ai_mapping: bool = Field(default=True, description="Apply AI column mapping")
    apply_quality_check: bool = Field(default=True, description="Apply AI quality check")
    target_fields: Optional[List[str]] = Field(None, description="Target fields for mapping")
    parser_options: Optional[Dict[str, Any]] = Field(None, description="Parser-specific options")


class ImportJobResponse(BaseModel):
    """Import job details."""
    id: int
    upload_id: str
    filename: str
    file_type: str
    status: ImportJobStatus
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    error_count: Optional[int] = None
    warnings: List[str] = []
    errors: List[str] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParsePreviewRequest(BaseModel):
    """Request to preview file parsing."""
    upload_id: str = Field(..., description="Upload ID")
    filename: str = Field(..., description="Filename")
    file_type: str = Field(..., description="File type")
    preview_rows: int = Field(default=10, ge=1, le=100, description="Number of rows to preview")
    parser_options: Optional[Dict[str, Any]] = Field(None, description="Parser options")
    customer_id: Optional[int] = Field(None, description="Customer company ID for pricing matrix lookup")


class ParsePreviewResponse(BaseModel):
    """Preview of parsed data."""
    success: bool
    columns: List[str]
    data: List[Dict[str, Any]]
    row_count: int
    total_rows_estimate: Optional[int] = None
    warnings: List[str] = []
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class ImportDataRequest(BaseModel):
    """Request to import parsed data into database."""
    job_id: int = Field(..., description="Import job ID")
    column_mapping: Optional[Dict[str, str]] = Field(None, description="Manual column mapping")
    issuer_id: Optional[int] = Field(None, description="Issuer company ID (defaults to first issuer)")
    customer_id: Optional[int] = Field(None, description="Customer company ID (if specified, use existing customer instead of creating new)")
    validate_only: bool = Field(default=False, description="Only validate, don't import")


class ImportDataResponse(BaseModel):
    """Response after data import."""
    success: bool
    imported_rows: int
    skipped_rows: int
    error_rows: int
    warnings: List[str] = []
    errors: List[str] = []
    validation_results: Optional[Dict[str, Any]] = None
