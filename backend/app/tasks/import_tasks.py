"""
Celery tasks for file import and processing.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.import_job import ImportJob
from app.parsers.factory import FileParserFactory
from app.ai.factory import AIProviderFactory
from app.schemas.import_job import ImportJobStatus


@celery_app.task(bind=True, name="process_file_import")
def process_file_import(
    self,
    job_id: int,
    file_path: str,
    filename: str,
    apply_ai_mapping: bool = True,
    apply_quality_check: bool = True,
    target_fields: Optional[list] = None,
    parser_options: Optional[dict] = None
):
    """
    Process file import asynchronously.

    Args:
        job_id: Import job database ID
        file_path: Path to uploaded file
        filename: Original filename
        apply_ai_mapping: Whether to apply AI mapping
        apply_quality_check: Whether to apply quality check
        target_fields: Target fields for mapping
        parser_options: Parser-specific options

    Returns:
        Dictionary with processing results
    """
    db: Session = SessionLocal()

    try:
        # Update job status to processing
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise ValueError(f"Import job {job_id} not found")

        job.status = ImportJobStatus.PROCESSING
        db.commit()

        # Create AI provider if needed
        ai_provider = None
        if apply_ai_mapping or apply_quality_check:
            ai_provider = AIProviderFactory.create()

        # Create appropriate parser
        file_path_obj = Path(file_path)
        parser = FileParserFactory.create_parser(
            file_path=file_path_obj,
            ai_provider=ai_provider
        )

        if parser is None:
            raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")

        # Parse file
        parser_options = parser_options or {}
        parser_options['apply_ai_mapping'] = apply_ai_mapping
        parser_options['target_fields'] = target_fields

        # Use asyncio to run async parser
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        parse_result = loop.run_until_complete(
            parser.parse(file_path=file_path_obj, **parser_options)
        )

        if not parse_result.success:
            job.status = ImportJobStatus.FAILED
            job.errors = parse_result.errors
            db.commit()
            return {
                'success': False,
                'job_id': job_id,
                'errors': parse_result.errors
            }

        # Update job with results
        job.status = ImportJobStatus.COMPLETED
        job.total_rows = parse_result.row_count
        job.processed_rows = parse_result.row_count
        job.warnings = parse_result.warnings
        job.errors = parse_result.errors
        job.result_data = {
            'columns': parse_result.columns,
            'data_sample': parse_result.data[:10] if parse_result.data else [],
            'metadata': parse_result.metadata
        }
        db.commit()

        # Clean up temp file
        try:
            os.remove(file_path)
        except Exception:
            pass

        return {
            'success': True,
            'job_id': job_id,
            'total_rows': parse_result.row_count,
            'warnings': parse_result.warnings
        }

    except Exception as e:
        # Update job status to failed
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if job:
            job.status = ImportJobStatus.FAILED
            job.errors = [str(e)]
            db.commit()

        return {
            'success': False,
            'job_id': job_id,
            'errors': [str(e)]
        }

    finally:
        db.close()


@celery_app.task(bind=True, name="import_parsed_data")
def import_parsed_data(
    self,
    job_id: int,
    column_mapping: Optional[dict] = None,
    validate_only: bool = False
):
    """
    Import parsed data into database tables.

    Args:
        job_id: Import job ID
        column_mapping: Manual column mapping override
        validate_only: Only validate, don't import

    Returns:
        Dictionary with import results
    """
    db: Session = SessionLocal()

    try:
        from app.services.import_service import ImportService

        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise ValueError(f"Import job {job_id} not found")

        if job.status != ImportJobStatus.COMPLETED:
            raise ValueError(f"Job {job_id} is not ready for import (status: {job.status})")

        # Extract data from job result
        if not job.result_data or 'data_sample' not in job.result_data:
            # Try to get full data if only sample was stored
            # For now, use the sample data
            data = job.result_data.get('data_sample', [])
        else:
            data = job.result_data['data_sample']

        if not data:
            raise ValueError("No data available for import")

        # Import data using ImportService
        result = ImportService.import_order_data(
            db=db,
            data=data,
            column_mapping=column_mapping
        )

        return {
            'success': result['success'],
            'job_id': job_id,
            'imported_rows': result['imported_rows'],
            'skipped_rows': result['skipped_rows'],
            'error_rows': result['error_rows'],
            'warnings': result['warnings'],
            'errors': result['errors']
        }

    except Exception as e:
        return {
            'success': False,
            'job_id': job_id,
            'imported_rows': 0,
            'skipped_rows': 0,
            'error_rows': 0,
            'errors': [str(e)]
        }

    finally:
        db.close()
