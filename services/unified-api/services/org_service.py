"""Organization service for WaddlePerf Unified API"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydal import DAL


class OrganizationService:
    """Handle organization CRUD operations with PyDAL"""

    def __init__(self, db: DAL):
        """Initialize service with database instance.

        Args:
            db: PyDAL DAL instance
        """
        self.db = db

    def list_organizations(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all organizations.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of organization records
        """
        rows = self.db(self.db.organizations).select(
            limitby=(offset, offset + limit),
            orderby=self.db.organizations.created_at,
        )
        return [dict(row) for row in rows]

    def get_organization(self, org_id: int) -> Optional[Dict[str, Any]]:
        """Get organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization record or None
        """
        row = self.db.organizations[org_id]
        return dict(row) if row else None

    def create_organization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new organization.

        Args:
            data: Organization data

        Returns:
            Created organization record
        """
        org_id = self.db.organizations.insert(**data)
        return self.get_organization(org_id)

    def update_organization(self, org_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update organization.

        Args:
            org_id: Organization ID
            data: Updated organization data

        Returns:
            Updated organization record or None
        """
        org = self.db.organizations[org_id]
        if not org:
            return None
        data['updated_at'] = datetime.utcnow()
        org.update_record(**data)
        return self.get_organization(org_id)

    def delete_organization(self, org_id: int) -> bool:
        """Delete organization.

        Args:
            org_id: Organization ID

        Returns:
            True if successful, False otherwise
        """
        org = self.db.organizations[org_id]
        if not org:
            return False
        org.delete_record()
        return True

    def list_organizational_units(self, org_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List organizational units for an organization.

        Args:
            org_id: Organization ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of organizational unit records
        """
        rows = self.db(
            self.db.organizational_units.organization_id == org_id
        ).select(
            limitby=(offset, offset + limit),
            orderby=self.db.organizational_units.created_at,
        )
        return [dict(row) for row in rows]

    def get_organizational_unit(self, org_id: int, ou_id: int) -> Optional[Dict[str, Any]]:
        """Get organizational unit by ID.

        Args:
            org_id: Organization ID
            ou_id: Organizational unit ID

        Returns:
            Organizational unit record or None
        """
        row = self.db((self.db.organizational_units.organization_id == org_id) &
                      (self.db.organizational_units.id == ou_id)).select().first()
        return dict(row) if row else None

    def create_organizational_unit(self, org_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create organizational unit.

        Args:
            org_id: Organization ID
            data: OU data

        Returns:
            Created organizational unit record
        """
        data['organization_id'] = org_id
        ou_id = self.db.organizational_units.insert(**data)
        return self.get_organizational_unit(org_id, ou_id)

    def update_organizational_unit(self, org_id: int, ou_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update organizational unit.

        Args:
            org_id: Organization ID
            ou_id: Organizational unit ID
            data: Updated OU data

        Returns:
            Updated organizational unit record or None
        """
        ou = self.db((self.db.organizational_units.organization_id == org_id) &
                     (self.db.organizational_units.id == ou_id)).select().first()
        if not ou:
            return None
        data['updated_at'] = datetime.utcnow()
        ou.update_record(**data)
        return self.get_organizational_unit(org_id, ou_id)

    def delete_organizational_unit(self, org_id: int, ou_id: int) -> bool:
        """Delete organizational unit.

        Args:
            org_id: Organization ID
            ou_id: Organizational unit ID

        Returns:
            True if successful, False otherwise
        """
        ou = self.db((self.db.organizational_units.organization_id == org_id) &
                     (self.db.organizational_units.id == ou_id)).select().first()
        if not ou:
            return False
        ou.delete_record()
        return True
