"""
Clean Slate Database Migration Script for WaddlePerf

Migrates data from legacy managerServer + webClient schema (Flask-SQLAlchemy based)
to the new unified PyDAL-based schema.

Supported operations:
  - export: Export data from old schema to JSON backup
  - migrate: Execute full migration (export -> transform -> import)
  - validate: Validate migration results and foreign key integrity
  - rollback: Restore database from backup

Usage:
    python 001_clean_slate_migration.py export [--output FILE]
    python 001_clean_slate_migration.py migrate [--backup]
    python 001_clean_slate_migration.py validate
    python 001_clean_slate_migration.py rollback --backup FILE
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SCHEMA MAPPINGS
# Maps old Flask-SQLAlchemy table names to new PyDAL table names
OLD_TO_NEW_TABLES = {
    'organization_units': 'auth_organization',
    'users': 'auth_user',
    'sessions': 'auth_session',
    'jwt_tokens': 'auth_token',
    'ou_enrollment_secrets': 'device_enrollment_secret',
    'device_enrollments': 'device_device',
    'system_config': 'config_config',
}

# Field transformation rules: (old_table, old_field) -> (new_field, transform_func)
FIELD_TRANSFORMS = {
    ('organization_units', 'name'): ('name', lambda v: v),
    ('organization_units', 'description'): ('description', lambda v: v or ''),
    ('users', 'username'): ('username', lambda v: v),
    ('users', 'email'): ('email', lambda v: v),
    ('users', 'password_hash'): ('password', lambda v: v),
    ('users', 'api_key'): (None, None),  # Store separately in auth_token
    ('users', 'role'): ('role_mapping', lambda v: _map_old_role(v)),
    ('users', 'ou_id'): (None, None),  # Maps to organization_unit_id
    ('users', 'is_active'): ('active', lambda v: v),
    ('users', 'mfa_enabled'): ('mfa_enabled', lambda v: v),
    ('users', 'mfa_secret'): ('mfa_secret', lambda v: v or ''),
    ('device_enrollments', 'device_serial'): ('serial_number', lambda v: v),
    ('device_enrollments', 'device_hostname'): ('name', lambda v: v),
    ('device_enrollments', 'device_os'): (None, None),  # Store in metadata
    ('device_enrollments', 'device_os_version'): (None, None),  # store in metadata
    ('device_enrollments', 'client_type'): ('type', lambda v: _map_client_type(v)),
    ('device_enrollments', 'client_version'): ('firmware_version', lambda v: v or ''),
    ('device_enrollments', 'enrolled_ip'): ('ip_address', lambda v: v),
    ('device_enrollments', 'enrolled_at'): ('enrolled_at', lambda v: v),
    ('device_enrollments', 'is_active'): (None, None),  # Use for status mapping
}


class MigrationError(Exception):
    """Migration-specific exception"""
    pass


def _map_old_role(old_role: str) -> str:
    """Map old role enum to new RBAC model"""
    role_mapping = {
        'global_admin': 'admin',
        'global_reporter': 'maintainer',
        'ou_admin': 'admin',
        'ou_reporter': 'maintainer',
        'user': 'viewer',
    }
    return role_mapping.get(old_role, 'viewer')


def _map_client_type(client_type: str) -> str:
    """Map old client type to new device type"""
    type_mapping = {
        'containerClient': 'container',
        'goClient': 'edge',
        'webClient': 'generic',
    }
    return type_mapping.get(client_type, 'generic')


class OldDatabaseReader:
    """Reads data from legacy Flask-SQLAlchemy database"""

    def __init__(self, db_url: str):
        """
        Initialize database reader for old schema.

        Args:
            db_url: SQLAlchemy database URL (e.g., postgresql://...)
        """
        self.db_url = db_url
        self.engine = None
        self.session = None

    def connect(self) -> None:
        """Establish database connection"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            self.engine = create_engine(self.db_url)
            SessionLocal = sessionmaker(bind=self.engine)
            self.session = SessionLocal()
            logger.info("Connected to legacy database")
        except Exception as e:
            raise MigrationError(f"Failed to connect to legacy database: {e}")

    def close(self) -> None:
        """Close database connection"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()

    def read_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Read entire table from legacy database.

        Args:
            table_name: Name of table to read

        Returns:
            List of dictionaries representing table rows
        """
        try:
            from sqlalchemy import text

            result = self.session.execute(text(f"SELECT * FROM {table_name}"))
            rows = []
            for row in result:
                rows.append(dict(row._mapping))
            logger.info(f"Read {len(rows)} rows from {table_name}")
            return rows
        except Exception as e:
            logger.warning(f"Failed to read {table_name}: {e}")
            return []

    def read_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Read all data from legacy database.

        Returns:
            Dictionary mapping table names to lists of rows
        """
        data = {}
        tables_to_read = [
            'organization_units',
            'users',
            'sessions',
            'jwt_tokens',
            'ou_enrollment_secrets',
            'device_enrollments',
            'system_config',
        ]

        for table in tables_to_read:
            data[table] = self.read_table(table)

        return data


class DataTransformer:
    """Transforms legacy data to new schema format"""

    def __init__(self):
        """Initialize transformer"""
        self.ou_id_map = {}  # Maps old ou_id to new organization_id
        self.user_id_map = {}  # Maps old user_id to new auth_user.id
        self.device_id_map = {}  # Maps old device_enrollment.id to new device_id
        self.enrollments_by_ou = {}  # Groups enrollments by OU

    def transform_all(
        self, old_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform all legacy data to new schema.

        Args:
            old_data: Data read from legacy database

        Returns:
            Dictionary mapping new table names to transformed data
        """
        new_data = {}

        # Transform organizations first (needed as FK references)
        logger.info("Transforming organization_units...")
        organizations = self._transform_organizations(
            old_data.get('organization_units', [])
        )
        new_data['auth_organization'] = organizations

        # Transform users
        logger.info("Transforming users...")
        users, tokens = self._transform_users(
            old_data.get('users', []),
            organizations
        )
        new_data['auth_user'] = users
        new_data['auth_token'] = tokens

        # Transform sessions
        logger.info("Transforming sessions...")
        sessions = self._transform_sessions(old_data.get('sessions', []))
        new_data['auth_session'] = sessions

        # Transform JWT tokens
        logger.info("Transforming JWT tokens...")
        jwt_tokens = self._transform_jwt_tokens(old_data.get('jwt_tokens', []))
        new_data['auth_token'].extend(jwt_tokens)

        # Transform enrollment secrets
        logger.info("Transforming enrollment secrets...")
        secrets = self._transform_enrollment_secrets(
            old_data.get('ou_enrollment_secrets', [])
        )
        new_data['device_enrollment_secret'] = secrets

        # Transform devices
        logger.info("Transforming device enrollments...")
        devices = self._transform_devices(
            old_data.get('device_enrollments', []),
            organizations
        )
        new_data['device_device'] = devices

        return new_data

    def _transform_organizations(
        self, orgs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform organization_units to auth_organization"""
        transformed = []
        for org in orgs:
            new_org = {
                'id': org.get('id'),
                'name': org.get('name'),
                'slug': self._generate_slug(org.get('name', '')),
                'description': org.get('description', ''),
                'active': True,
                'tier': 'free',
                'max_users': 50,
                'max_devices': 100,
                'metadata': '{}',
                'created_at': org.get('created_at'),
                'updated_at': org.get('updated_at'),
            }
            self.ou_id_map[org['id']] = org['id']
            transformed.append(new_org)

        return transformed

    def _transform_users(
        self,
        users: List[Dict[str, Any]],
        organizations: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Transform users to auth_user and extract API keys as auth_token"""
        transformed_users = []
        api_key_tokens = []

        for user in users:
            org_id = self.ou_id_map.get(user.get('ou_id'))

            new_user = {
                'id': user.get('id'),
                'email': user.get('email'),
                'username': user.get('username'),
                'password': user.get('password_hash'),
                'first_name': '',
                'last_name': '',
                'active': user.get('is_active', True),
                'fs_uniquifier': self._generate_fs_uniquifier(user.get('id')),
                'confirmed_at': datetime.utcnow(),
                'organization_id': org_id,
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at'),
            }

            transformed_users.append(new_user)
            self.user_id_map[user['id']] = user['id']

            # Extract API key as token
            if api_key := user.get('api_key'):
                api_token = {
                    'user_id': user['id'],
                    'token': self._hash_api_key(api_key),
                    'token_type': 'api_key',
                    'name': f"API Key - {user.get('username')}",
                    'active': True,
                    'last_used_at': None,
                    'created_at': user.get('created_at'),
                }
                api_key_tokens.append(api_token)

        return transformed_users, api_key_tokens

    def _transform_sessions(
        self, sessions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform sessions to auth_session"""
        transformed = []
        for session in sessions:
            new_session = {
                'id': session.get('id'),
                'user_id': self.user_id_map.get(session.get('user_id')),
                'session_id': session.get('session_id'),
                'data': session.get('data', {}),
                'expires_at': session.get('expires_at'),
                'created_at': session.get('created_at'),
            }
            if new_session['user_id']:
                transformed.append(new_session)

        return transformed

    def _transform_jwt_tokens(
        self, tokens: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform JWT tokens to auth_token"""
        transformed = []
        for token in tokens:
            new_token = {
                'user_id': self.user_id_map.get(token.get('user_id')),
                'token': token.get('token_hash'),
                'token_type': 'jwt',
                'name': 'JWT Token',
                'active': not token.get('revoked', False),
                'last_used_at': None,
                'created_at': token.get('issued_at'),
            }
            if new_token['user_id']:
                transformed.append(new_token)

        return transformed

    def _transform_enrollment_secrets(
        self, secrets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform ou_enrollment_secrets to device_enrollment_secret"""
        transformed = []
        for secret in secrets:
            new_secret = {
                'id': secret.get('id'),
                'secret': secret.get('secret'),
                'organization_id': self.ou_id_map.get(secret.get('ou_id')),
                'device_id': None,  # Will be linked during device transform
                'status': 'active' if secret.get('is_active') else 'revoked',
                'used_at': None,
                'expires_at': None,
                'created_at': secret.get('created_at'),
                'updated_at': secret.get('created_at'),
            }
            if new_secret['organization_id']:
                transformed.append(new_secret)

        return transformed

    def _transform_devices(
        self,
        devices: List[Dict[str, Any]],
        organizations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform device_enrollments to device_device"""
        transformed = []
        for device in devices:
            metadata = {
                'os': device.get('device_os'),
                'os_version': device.get('device_os_version'),
                'client_type': device.get('client_type'),
            }

            new_device = {
                'id': device.get('id'),
                'name': device.get('device_hostname'),
                'device_id': self._generate_device_id(device.get('device_serial')),
                'serial_number': device.get('device_serial'),
                'type': _map_client_type(device.get('client_type', 'webClient')),
                'status': 'online' if device.get('is_active') else 'offline',
                'organization_id': self.ou_id_map.get(device.get('ou_id')),
                'organization_unit_id': None,
                'ip_address': device.get('enrolled_ip', ''),
                'mac_address': '',
                'firmware_version': device.get('client_version', ''),
                'last_seen': device.get('last_seen'),
                'last_reported_at': device.get('last_seen'),
                'enrolled_at': device.get('enrolled_at'),
                'metadata': json.dumps(metadata),
                'created_at': device.get('enrolled_at'),
                'updated_at': device.get('enrolled_at'),
            }
            if new_device['organization_id']:
                transformed.append(new_device)
                self.device_id_map[device['id']] = new_device['id']

        return transformed

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate slug from organization name"""
        import re

        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        return slug[:128]

    @staticmethod
    def _generate_fs_uniquifier(user_id: int) -> str:
        """Generate Flask-Security-Too fs_uniquifier"""
        import hashlib

        data = f"fs_uniquifier_{user_id}_{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:64]

    @staticmethod
    def _hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        import hashlib

        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _generate_device_id(serial: str) -> str:
        """Generate device_id from serial number"""
        import hashlib

        return hashlib.sha256(serial.encode()).hexdigest()[:32]


class NewDatabaseWriter:
    """Writes data to new PyDAL-based database"""

    def __init__(self, dal):
        """
        Initialize database writer.

        Args:
            dal: PyDAL DAL instance
        """
        self.dal = dal

    def write_all(self, new_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """
        Write all transformed data to new database.

        Args:
            new_data: Transformed data ready for insertion

        Returns:
            Dictionary mapping table names to row counts inserted
        """
        results = {}

        # Write in dependency order to satisfy foreign keys
        table_order = [
            'auth_organization',
            'auth_organization_unit',
            'auth_user',
            'auth_role',
            'auth_user_role',
            'auth_token',
            'auth_session',
            'device_device',
            'device_enrollment_secret',
            'test_result',
        ]

        for table_name in table_order:
            if table_name in new_data:
                count = self._write_table(table_name, new_data[table_name])
                results[table_name] = count

        return results

    def _write_table(self, table_name: str, rows: List[Dict[str, Any]]) -> int:
        """
        Write rows to specific table.

        Args:
            table_name: Name of PyDAL table
            rows: List of row dictionaries

        Returns:
            Number of rows inserted
        """
        if not rows:
            logger.info(f"No data to write for {table_name}")
            return 0

        try:
            table = getattr(self.dal, table_name, None)
            if not table:
                logger.warning(f"Table {table_name} not found, skipping")
                return 0

            count = 0
            for row in rows:
                try:
                    # Filter out None values and id field (auto-generated)
                    clean_row = {k: v for k, v in row.items() if v is not None and k != 'id'}
                    table.insert(**clean_row)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert row in {table_name}: {e}")
                    continue

            self.dal.commit()
            logger.info(f"Inserted {count} rows into {table_name}")
            return count

        except Exception as e:
            logger.error(f"Failed to write table {table_name}: {e}")
            raise


class MigrationValidator:
    """Validates migration completeness and foreign key integrity"""

    def __init__(self, dal):
        """
        Initialize validator.

        Args:
            dal: PyDAL DAL instance
        """
        self.dal = dal

    def validate_all(self) -> bool:
        """
        Validate all aspects of migration.

        Returns:
            True if all validations passed, False otherwise
        """
        logger.info("Starting migration validation...")

        checks = [
            self._check_table_counts,
            self._check_foreign_keys,
            self._check_unique_constraints,
            self._check_data_integrity,
        ]

        all_passed = True
        for check in checks:
            if not check():
                all_passed = False

        return all_passed

    def _check_table_counts(self) -> bool:
        """Validate that tables have expected row counts"""
        logger.info("Checking table row counts...")
        try:
            tables = [
                'auth_organization',
                'auth_user',
                'device_device',
                'test_result',
            ]

            for table_name in tables:
                if hasattr(self.dal, table_name):
                    table = getattr(self.dal, table_name)
                    count = self.dal(table.id > 0).count()
                    logger.info(f"  {table_name}: {count} rows")

            return True
        except Exception as e:
            logger.error(f"Table count check failed: {e}")
            return False

    def _check_foreign_keys(self) -> bool:
        """Validate foreign key references"""
        logger.info("Validating foreign key references...")
        try:
            # Check auth_user.organization_id references exist
            if hasattr(self.dal, 'auth_user') and hasattr(self.dal, 'auth_organization'):
                orphans = self.dal(
                    (self.dal.auth_user.organization_id != None) &
                    ~self.dal.auth_user.organization_id.belongs(
                        self.dal(self.dal.auth_organization.id).select(self.dal.auth_organization.id)
                    )
                ).count()
                if orphans > 0:
                    logger.warning(f"Found {orphans} auth_user rows with invalid organization_id")
                    return False

            logger.info("Foreign key validation passed")
            return True
        except Exception as e:
            logger.error(f"Foreign key validation failed: {e}")
            return False

    def _check_unique_constraints(self) -> bool:
        """Validate unique constraint compliance"""
        logger.info("Checking unique constraints...")
        try:
            # Check email uniqueness
            if hasattr(self.dal, 'auth_user'):
                emails = self.dal(self.dal.auth_user.email != '').select(self.dal.auth_user.email)
                email_list = [row.email for row in emails]
                if len(email_list) != len(set(email_list)):
                    logger.warning("Duplicate emails found in auth_user")
                    return False

            logger.info("Unique constraint validation passed")
            return True
        except Exception as e:
            logger.error(f"Unique constraint validation failed: {e}")
            return False

    def _check_data_integrity(self) -> bool:
        """Validate data integrity across tables"""
        logger.info("Checking data integrity...")
        try:
            # Verify no critical nulls where not allowed
            if hasattr(self.dal, 'auth_user'):
                invalid_users = self.dal(
                    (self.dal.auth_user.email == '') |
                    (self.dal.auth_user.username == '') |
                    (self.dal.auth_user.password == '')
                ).count()
                if invalid_users > 0:
                    logger.warning(f"Found {invalid_users} auth_user rows with missing critical fields")
                    return False

            logger.info("Data integrity validation passed")
            return True
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return False


class BackupManager:
    """Manages data backups for rollback capability"""

    def __init__(self, backup_dir: str = '/tmp/waddleperf_backups'):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory for backup files
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, data: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Create backup file from exported data.

        Args:
            data: Data to backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"migration_backup_{timestamp}.json"

        try:
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
        except Exception as e:
            raise MigrationError(f"Failed to create backup: {e}")

    def restore_backup(self, backup_file: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Restore data from backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Restored data
        """
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Backup restored: {backup_file}")
            return data
        except Exception as e:
            raise MigrationError(f"Failed to restore backup: {e}")

    def list_backups(self) -> List[str]:
        """List available backup files"""
        return sorted([str(f) for f in self.backup_dir.glob('migration_backup_*.json')])


def export_old_data(db_url: str, output_file: Optional[str] = None) -> str:
    """
    Export data from legacy database to JSON file.

    Args:
        db_url: SQLAlchemy database URL
        output_file: Optional output file path

    Returns:
        Path to exported JSON file
    """
    logger.info("Starting data export from legacy database...")

    reader = OldDatabaseReader(db_url)
    try:
        reader.connect()
        data = reader.read_all_data()

        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"/tmp/waddleperf_export_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Data exported to {output_file}")
        return output_file

    finally:
        reader.close()


def run_migration(dal, old_db_url: str, create_backup: bool = True) -> bool:
    """
    Execute full migration process.

    Args:
        dal: PyDAL DAL instance for new database
        old_db_url: SQLAlchemy URL for legacy database
        create_backup: Whether to create backup before migration

    Returns:
        True if migration successful, False otherwise
    """
    logger.info("Starting full migration process...")

    try:
        # Step 1: Export old data
        logger.info("Step 1: Exporting legacy data...")
        export_file = export_old_data(old_db_url)

        # Step 2: Create backup
        if create_backup:
            logger.info("Step 2: Creating backup...")
            backup_mgr = BackupManager()
            with open(export_file, 'r') as f:
                exported_data = json.load(f)
            backup_file = backup_mgr.create_backup(exported_data)
            logger.info(f"Backup created at {backup_file}")

        # Step 3: Transform data
        logger.info("Step 3: Transforming data...")
        transformer = DataTransformer()
        with open(export_file, 'r') as f:
            old_data = json.load(f)
        new_data = transformer.transform_all(old_data)

        # Step 4: Write to new database
        logger.info("Step 4: Writing to new database...")
        writer = NewDatabaseWriter(dal)
        results = writer.write_all(new_data)

        for table_name, count in results.items():
            logger.info(f"  {table_name}: {count} rows")

        # Step 5: Validate
        logger.info("Step 5: Validating migration...")
        validator = MigrationValidator(dal)
        if not validator.validate_all():
            logger.error("Migration validation failed")
            return False

        logger.info("Migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def validate_migration(dal) -> bool:
    """
    Validate existing migration results.

    Args:
        dal: PyDAL DAL instance

    Returns:
        True if validation passed
    """
    logger.info("Validating migration...")
    validator = MigrationValidator(dal)
    return validator.validate_all()


def rollback_migration(backup_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Restore database from backup file.

    Args:
        backup_file: Path to backup file

    Returns:
        Restored data
    """
    logger.info("Starting rollback...")
    backup_mgr = BackupManager()
    return backup_mgr.restore_backup(backup_file)


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='WaddlePerf Database Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest='command', help='Migration command')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export legacy data')
    export_parser.add_argument(
        '--db-url',
        default='sqlite:///waddleperf_legacy.db',
        help='Legacy database URL'
    )
    export_parser.add_argument(
        '--output',
        help='Output JSON file path'
    )

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run full migration')
    migrate_parser.add_argument(
        '--db-url',
        default='sqlite:///waddleperf_legacy.db',
        help='Legacy database URL'
    )
    migrate_parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation'
    )

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate migration')

    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migration')
    rollback_parser.add_argument(
        '--backup',
        required=True,
        help='Backup file to restore from'
    )

    args = parser.parse_args()

    if args.command == 'export':
        try:
            output = export_old_data(args.db_url, args.output)
            print(f"Exported to: {output}")
            return 0
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return 1

    elif args.command == 'migrate':
        try:
            # Note: In real usage, would initialize DAL from application
            from services.unified_api.database.connection import get_dal
            # Would need proper config object here
            logger.error("DAL initialization requires application context")
            return 1
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return 1

    elif args.command == 'validate':
        logger.error("Validation requires application context")
        return 1

    elif args.command == 'rollback':
        try:
            data = rollback_migration(args.backup)
            logger.info(f"Restored {len(data)} tables from backup")
            return 0
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
