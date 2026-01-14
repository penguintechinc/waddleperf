"""Device service for WaddlePerf Unified API"""
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydal import DAL


class DeviceService:
    """Handle device management with PyDAL"""

    def __init__(self, db: DAL):
        """Initialize service with database instance.

        Args:
            db: PyDAL DAL instance
        """
        self.db = db

    def list_devices(self, org_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List devices with optional filtering.

        Args:
            org_id: Filter by organization ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of device records
        """
        if org_id:
            query = self.db.devices.organization_id == org_id
        else:
            query = self.db.devices.id > 0

        rows = self.db(query).select(
            limitby=(offset, offset + limit),
            orderby=self.db.devices.created_at,
        )
        return [dict(row) for row in rows]

    def get_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device record or None
        """
        row = self.db.devices[device_id]
        return dict(row) if row else None

    def get_device_by_device_id(self, device_id_str: str) -> Optional[Dict[str, Any]]:
        """Get device by device_id string.

        Args:
            device_id_str: Device ID string

        Returns:
            Device record or None
        """
        row = self.db(self.db.devices.device_id == device_id_str).select().first()
        return dict(row) if row else None

    def enroll_device(self, enrollment_secret: str, org_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enroll device using enrollment secret.

        Args:
            enrollment_secret: Enrollment secret token
            org_id: Organization ID
            data: Device data

        Returns:
            Created device record or None
        """
        # Verify secret is valid
        secret_row = self.db((self.db.enrollment_secrets.secret_token == enrollment_secret) &
                              (self.db.enrollment_secrets.organization_id == org_id) &
                              (self.db.enrollment_secrets.is_active == True)).select().first()

        if not secret_row:
            return None

        # Check if secret is expired
        if secret_row.expires_at and secret_row.expires_at < datetime.utcnow():
            return None

        # Check max uses
        if secret_row.max_uses and secret_row.current_uses >= secret_row.max_uses:
            return None

        # Create device
        data['organization_id'] = org_id
        if 'device_id' not in data:
            data['device_id'] = secrets.token_hex(16)

        device_id = self.db.devices.insert(**data)

        # Increment secret usage
        secret_row.update_record(current_uses=secret_row.current_uses + 1)

        return self.get_device(device_id)

    def update_device(self, device_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update device.

        Args:
            device_id: Device ID
            data: Updated device data

        Returns:
            Updated device record or None
        """
        device = self.db.devices[device_id]
        if not device:
            return None
        data['updated_at'] = datetime.utcnow()
        device.update_record(**data)
        return self.get_device(device_id)

    def delete_device(self, device_id: int) -> bool:
        """Delete device.

        Args:
            device_id: Device ID

        Returns:
            True if successful, False otherwise
        """
        device = self.db.devices[device_id]
        if not device:
            return False
        device.delete_record()
        return True

    def create_enrollment_secret(self, org_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create enrollment secret.

        Args:
            org_id: Organization ID
            data: Secret data

        Returns:
            Created enrollment secret record
        """
        data['organization_id'] = org_id
        if 'secret_token' not in data:
            data['secret_token'] = secrets.token_urlsafe(32)

        secret_id = self.db.enrollment_secrets.insert(**data)
        return self.get_enrollment_secret(secret_id)

    def get_enrollment_secret(self, secret_id: int) -> Optional[Dict[str, Any]]:
        """Get enrollment secret by ID.

        Args:
            secret_id: Secret ID

        Returns:
            Enrollment secret record or None
        """
        row = self.db.enrollment_secrets[secret_id]
        return dict(row) if row else None

    def list_enrollment_secrets(self, org_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List enrollment secrets for organization.

        Args:
            org_id: Organization ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of enrollment secret records
        """
        rows = self.db(
            self.db.enrollment_secrets.organization_id == org_id
        ).select(
            limitby=(offset, offset + limit),
            orderby=self.db.enrollment_secrets.created_at,
        )
        return [dict(row) for row in rows]

    def update_enrollment_secret(self, secret_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update enrollment secret.

        Args:
            secret_id: Secret ID
            data: Updated secret data

        Returns:
            Updated enrollment secret record or None
        """
        secret = self.db.enrollment_secrets[secret_id]
        if not secret:
            return None
        data['updated_at'] = datetime.utcnow()
        secret.update_record(**data)
        return self.get_enrollment_secret(secret_id)

    def delete_enrollment_secret(self, secret_id: int) -> bool:
        """Delete enrollment secret.

        Args:
            secret_id: Secret ID

        Returns:
            True if successful, False otherwise
        """
        secret = self.db.enrollment_secrets[secret_id]
        if not secret:
            return False
        secret.delete_record()
        return True
