"""
Celery tasks for syncing device master data from Supabase to local DB.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.device_master_service import DeviceMasterService
from app.services.supabase_service import SupabaseService


@celery_app.task(bind=True, name="sync_device_master_from_supabase")
def sync_device_master_from_supabase(self):
    """
    Sync device master data from Supabase to local PostgreSQL.

    Fetches all device attributes from Supabase and updates local DB.
    This allows the system to work with the latest device data.

    Returns:
        Dictionary with sync results
    """
    db: Session = SessionLocal()

    try:
        # Initialize services
        supabase_service = SupabaseService()

        # Check if Supabase is available
        if not supabase_service.is_available():
            return {
                'success': False,
                'error': 'Supabase is not available',
                'synced_count': 0,
                'timestamp': datetime.now().isoformat()
            }

        # Fetch all device attributes from Supabase
        devices = supabase_service.fetch_all_devices()

        if not devices:
            return {
                'success': False,
                'error': 'No devices fetched from Supabase',
                'synced_count': 0,
                'timestamp': datetime.now().isoformat()
            }

        # Clear existing data (optional - or use upsert)
        # For now, we'll use upsert approach (INSERT ... ON CONFLICT UPDATE)

        synced_count = 0
        errors = []

        for device in devices:
            try:
                # Upsert device data
                upsert_query = text("""
                    INSERT INTO device_attributes (brand, device_name, size_category, attribute_value, created_at, updated_at)
                    VALUES (:brand, :device_name, :size_category, :attribute_value, :created_at, :updated_at)
                    ON CONFLICT (brand, device_name)
                    DO UPDATE SET
                        size_category = EXCLUDED.size_category,
                        attribute_value = EXCLUDED.attribute_value,
                        updated_at = EXCLUDED.updated_at
                """)

                db.execute(upsert_query, {
                    'brand': device.get('brand'),
                    'device_name': device.get('device_name'),
                    'size_category': device.get('size_category'),
                    'attribute_value': device.get('attribute_value'),
                    'created_at': device.get('created_at', datetime.now()),
                    'updated_at': datetime.now()
                })

                synced_count += 1

            except Exception as e:
                errors.append(f"Failed to sync {device.get('brand')} {device.get('device_name')}: {str(e)}")

        db.commit()

        return {
            'success': True,
            'synced_count': synced_count,
            'total_fetched': len(devices),
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'synced_count': 0,
            'timestamp': datetime.now().isoformat()
        }

    finally:
        db.close()


@celery_app.task(bind=True, name="get_device_sync_status")
def get_device_sync_status(self):
    """
    Get current status of device master data.

    Returns:
        Dictionary with local DB status and Supabase availability
    """
    db: Session = SessionLocal()

    try:
        # Count local devices
        result = db.execute(text("SELECT COUNT(*) FROM device_attributes"))
        local_count = result.scalar()

        # Get last updated timestamp
        result = db.execute(text("SELECT MAX(updated_at) FROM device_attributes"))
        last_updated = result.scalar()

        # Check Supabase availability
        supabase_service = SupabaseService()
        supabase_available = supabase_service.is_available()

        supabase_count = 0
        if supabase_available:
            try:
                devices = supabase_service.fetch_all_devices()
                supabase_count = len(devices) if devices else 0
            except Exception:
                supabase_available = False

        return {
            'success': True,
            'local_db': {
                'count': local_count,
                'last_updated': last_updated.isoformat() if last_updated else None
            },
            'supabase': {
                'available': supabase_available,
                'count': supabase_count
            },
            'sync_needed': supabase_available and (supabase_count > local_count),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

    finally:
        db.close()
