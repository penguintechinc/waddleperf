# ⚙️ MariaDB Galera Cluster Restrictions vs. Normal MariaDB

MariaDB Galera Cluster provides synchronous multi-master replication for high availability, but this advanced functionality imposes a number of restrictions and requirements that a standard, single-node MariaDB server does not.

---

## 🛑 Key Restrictions and Limitations

### 1. Storage Engine and Schema Limitations

| Restriction | Galera Requirement | Normal MariaDB Behavior |
| :--- | :--- | :--- |
| **Storage Engine** | Must use **InnoDB** (or XtraDB). | Supports various engines (InnoDB, MyISAM, MEMORY) with no replication limitations. |
| **Primary Keys** | All replicated tables **must have an explicit primary key**. | Primary keys are recommended but not mandatory for basic functionality. |
| **DELETE Operations** | Not supported on tables without a primary key. | Supported on any table. |
| **System Tables** | Writes to system tables (e.g., `mysql.*`) are **not replicated**. (DDL statements like `CREATE USER` are replicated as special cases.) | System tables are managed locally on the single server. |

### 2. Performance and Transaction Limitations

| Restriction | Galera Behavior | Normal MariaDB Behavior |
| :--- | :--- | :--- |
| **Write Performance** | Writes are generally **slower** due to the synchronous replication and certification overhead. | Writes are faster as they commit locally without network latency delay. |
| **Write Scaling** | **Does not scale writes** linearly. Write performance may decrease as nodes are added. | Single server performance is limited only by hardware. |
| **Large Transactions** | Extremely large transactions (many rows/large size) are discouraged, as they can cause performance issues and cluster-wide lag. | Large transactions are handled locally, limited only by local resources. |
| **Auto-Increment** | Values are **non-sequential** (have gaps) across the cluster, as each node pre-allocates ID ranges. | Values are sequential on the single server. |
| **Network** | Requires a **stable, low-latency private network** for communication between nodes. | Only requires network access for clients and application servers. |

### 3. Unsupported SQL Operations

| Unsupported Operation | Impact in Galera | Alternative/Workaround |
| :--- | :--- | :--- |
| **Explicit Locking** | Statements like `LOCK TABLES`, `UNLOCK TABLES`, and `GET_LOCK()` are **not supported**. | Use proper transaction management and row-level locking (InnoDB) instead. |
| **Query/Slow Logs to Table** | Directing logs to a table (`log_output=TABLE`) is **not supported**. | Must be set to log to a file (`log_output=FILE`). |
| **Binary Log Format** | Must be set to **ROW** format. | Supports ROW, STATEMENT, or MIXED formats. |
| **Query Cache** | Must be **disabled** or used with extreme caution due to consistency issues. | Can be enabled on a single server for read-intensive workloads. |

### 4. Cluster Health and Quorum

* **Quorum Protection:** If a cluster loses a majority of its nodes (loses quorum), the remaining nodes will **stop accepting write queries** to prevent data inconsistency (split-brain).
    * *Example:* In a 3-node cluster, if two nodes fail, the remaining single node stops writing.
* **DDL Operations (Schema Changes):** By default, DDLs (`ALTER TABLE`) use **Total Order Isolation (TOI)** which blocks the entire cluster until the operation is complete. Alternatives like Rolling Schema Upgrade (RSU) exist but require careful management.

### 5. Additional Galera-Specific Limitations

| Limitation | Details | Impact |
| :--- | :--- | :--- |
| **XA Transactions** | Distributed transactions (XA/Two-Phase Commit) are **not supported**. | Cannot use XA START/END/PREPARE/COMMIT commands. |
| **FLUSH PRIVILEGES** | Not replicated across nodes. | Must execute on all nodes manually or restart cluster after permission changes. |
| **Metadata Locks** | DDL does NOT wait for metadata locks from parallel DML transactions. | DDL executes immediately even if table is in use, which differs from standalone MariaDB. |
| **Binary Log Format Changes** | Changing `binlog_format` at runtime will **crash all nodes** in the cluster. | Never use `SET GLOBAL binlog_format` - always configure in my.cnf. |
| **SAVEPOINT Support** | SAVEPOINT inside transactions may cause issues with Galera certification. | Minimize use of SAVEPOINTs; prefer smaller atomic transactions. |
| **LOAD DATA INFILE** | Can cause issues with very large data loads. | Break large loads into smaller batches or use INSERT statements. |
| **Flashback** | Not supported due to incompatible binary log format. | Use regular backup/restore procedures instead. |

### 6. Deadlock Behavior Differences

| Aspect | Galera Behavior | Normal MariaDB Behavior |
| :--- | :--- | :--- |
| **Deadlock Detection** | Can occur during **certification** (commit time) in addition to execution time. | Deadlocks only detected during execution (traditional InnoDB deadlock detection). |
| **Certification Conflicts** | Transactions may fail at commit with certification conflicts if they modified the same rows on different nodes. | No certification conflicts - only traditional deadlocks during execution. |
| **Error Codes** | Can return `ER_LOCK_DEADLOCK` (1213) during commit phase. | Deadlocks only occur during transaction execution, never at commit. |
| **Retry Logic** | Applications **must** implement retry logic for certification failures. | Retry logic for deadlocks is recommended but certification conflicts don't exist. |

---

## ✅ Best Practices for WaddlePerf with Galera

### Schema Design
1. **Always define PRIMARY KEYS** on all tables
   ```sql
   CREATE TABLE example (
       id INT PRIMARY KEY AUTO_INCREMENT,
       data VARCHAR(255)
   ) ENGINE=InnoDB;
   ```

2. **Explicitly specify ENGINE=InnoDB**
   ```sql
   CREATE TABLE test_results (
       id BIGINT PRIMARY KEY AUTO_INCREMENT,
       -- columns --
   ) ENGINE=InnoDB;
   ```

3. **Use appropriate data types**
   - Avoid TEXT/BLOB in frequently updated columns
   - Use proper indexes for foreign key columns

### Transaction Management
1. **Keep transactions small and short**
   ```python
   # Good - small transaction
   with db.session.begin():
       result = TestResult(...)
       db.session.add(result)

   # Bad - large transaction
   with db.session.begin():
       for i in range(10000):  # Too many operations
           result = TestResult(...)
           db.session.add(result)
   ```

2. **Commit frequently**
   - Don't hold transactions open across network calls
   - Commit after logical units of work

3. **Implement retry logic for certification failures**
   ```python
   def insert_with_retry(data, max_retries=3):
       for attempt in range(max_retries):
           try:
               db.session.add(data)
               db.session.commit()
               return
           except OperationalError as e:
               if e.orig.args[0] == 1213:  # Deadlock
                   db.session.rollback()
                   if attempt == max_retries - 1:
                       raise
                   time.sleep(0.1 * (attempt + 1))
               else:
                   raise
   ```

### Locking Strategy
1. **Avoid explicit locks**
   ```python
   # Bad - don't use
   db.session.execute("LOCK TABLES users WRITE")

   # Good - use row-level locking
   user = db.session.query(User).with_for_update().filter_by(id=1).first()
   ```

2. **Use optimistic locking when possible**
   ```sql
   -- Add version column
   ALTER TABLE users ADD COLUMN version INT DEFAULT 0;

   -- Update with version check
   UPDATE users SET data = 'new', version = version + 1
   WHERE id = 1 AND version = 5;
   ```

### Query Optimization
1. **Avoid hot spots** - Don't have all nodes updating the same rows
2. **Batch reads** when possible to reduce network overhead
3. **Use read-only transactions** for reporting queries
   ```python
   # Mark as read-only to potentially skip certification
   db.session.execute("SET SESSION TRANSACTION READ ONLY")
   ```

### Monitoring
Monitor these Galera-specific status variables:
```sql
-- Cluster health
SHOW STATUS LIKE 'wsrep_cluster_status';  -- Should be 'Primary'
SHOW STATUS LIKE 'wsrep_ready';           -- Should be 'ON'
SHOW STATUS LIKE 'wsrep_connected';       -- Should be 'ON'

-- Replication health
SHOW STATUS LIKE 'wsrep_local_state_comment';  -- Should be 'Synced'
SHOW STATUS LIKE 'wsrep_cluster_size';         -- Number of nodes

-- Performance metrics
SHOW STATUS LIKE 'wsrep_cert_deps_distance';   -- Average distance between transactions
SHOW STATUS LIKE 'wsrep_flow_control_paused';  -- Time cluster spent paused (should be low)
```

---

## 🔧 Configuration Recommendations

### Required Configuration in my.cnf
```ini
[mysqld]
# Galera Provider
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so

# Cluster Configuration
wsrep_cluster_name="waddleperf_cluster"
wsrep_cluster_address="gcomm://node1,node2,node3"

# Node Configuration
wsrep_node_address="node1_ip"
wsrep_node_name="node1"

# Replication Settings
wsrep_slave_threads=4  # Adjust based on CPU cores
binlog_format=ROW      # REQUIRED - never change at runtime

# InnoDB Settings
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2  # Interleaved lock mode for Galera
innodb_flush_log_at_trx_commit=2  # Performance optimization
```

### Connection String Configuration
```python
# Python SQLAlchemy example
from sqlalchemy import create_engine

# Multiple nodes for failover
nodes = [
    "mariadb-node1:3306",
    "mariadb-node2:3306",
    "mariadb-node3:3306"
]

# Use load balancer or connection pooling
engine = create_engine(
    f"mysql+pymysql://user:pass@{nodes[0]}/waddleperf",
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True  # Check connection before using
)
```

---

## 🚨 Common Pitfalls to Avoid

1. **Changing binlog_format at runtime** → Crashes entire cluster
2. **Missing primary keys** → DELETE operations fail
3. **Using LOCK TABLES** → Not supported, causes errors
4. **Large transactions** → Certification conflicts and performance issues
5. **Not handling certification failures** → Application crashes
6. **Expecting sequential auto_increment** → Gaps are normal
7. **Running FLUSH PRIVILEGES on one node** → Permissions not synced
8. **Using MyISAM tables** → Not replicated
9. **Long-running transactions** → Blocks cluster replication
10. **Hot spot writes** → Certification conflicts across nodes

---

## 📚 Additional Resources

- [MariaDB Galera Cluster Official Documentation](https://mariadb.com/kb/en/galera-cluster/)
- [Galera Cluster Documentation](https://galeracluster.com/library/documentation/)
- [MariaDB Galera Known Limitations](https://mariadb.com/kb/en/mariadb-galera-cluster-known-limitations/)
- [Percona XtraDB Cluster Documentation](https://www.percona.com/doc/percona-xtradb-cluster/LATEST/index.html) (similar to Galera)

---

**Copyright © 2025 Penguin Technologies Inc.**