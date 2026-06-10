# ACID vs BASE — Detailed Notes

> A comprehensive reference covering both models, their internals, trade-offs, and when to choose each.

---

## Table of Contents

1. [Why Two Models?](#why-two-models)
2. [ACID — Deep Dive](#acid--deep-dive)
   - [Atomicity](#1-atomicity)
   - [Consistency](#2-consistency)
   - [Isolation](#3-isolation)
   - [Durability](#4-durability)
3. [BASE — Deep Dive](#base--deep-dive)
   - [Basically Available](#1-basically-available)
   - [Soft State](#2-soft-state)
   - [Eventually Consistent](#3-eventually-consistent)
4. [CAP Theorem — The Foundation](#cap-theorem--the-foundation)
5. [ACID vs BASE — Side-by-Side](#acid-vs-base--side-by-side)
6. [Isolation Levels in ACID](#isolation-levels-in-acid)
   - [Read Phenomena](#read-phenomena)
   - [Isolation Level Matrix](#isolation-level-matrix)
7. [Consistency Models in BASE](#consistency-models-in-base)
8. [Internal Mechanisms](#internal-mechanisms)
   - [How ACID is Implemented](#how-acid-is-implemented)
   - [How BASE is Implemented](#how-base-is-implemented)
9. [Database Examples](#database-examples)
10. [When to Choose ACID vs BASE](#when-to-choose-acid-vs-base)
11. [Hybrid Approaches](#hybrid-approaches)
12. [Spring Boot / JPA Context](#spring-boot--jpa-context)
13. [Quick-Reference Summary](#quick-reference-summary)

---

## Why Two Models?

In the 1970s–80s, relational databases designed for **single-node, disk-bound** workloads established ACID as the gold standard for transactional integrity.

By the 2000s, internet-scale systems (Google, Amazon, Facebook) hit the physical limits of single-node RDBMS:

- Data volumes exceeded terabytes → petabytes
- Write throughput requirements far exceeded what one machine could sustain
- Global distribution required geographically distributed storage

To scale **horizontally** across commodity machines and data centres, engineers had to make principled trade-offs on consistency. This led to the **BASE** model, articulated by Eric Brewer (2000) in conjunction with the **CAP Theorem**.

---

## ACID — Deep Dive

ACID stands for **Atomicity, Consistency, Isolation, Durability**. These four properties collectively guarantee that database transactions are processed reliably.

---

### 1. Atomicity

> "All or nothing."

A transaction is an **indivisible unit**. Every operation within the transaction either commits together, or the entire transaction is rolled back — leaving the database exactly as it was before.

**Example — Bank Transfer:**

```
BEGIN TRANSACTION
  UPDATE accounts SET balance = balance - 10000 WHERE id = 'A';   -- Step 1
  UPDATE accounts SET balance = balance + 10000 WHERE id = 'B';   -- Step 2
COMMIT
```

If Step 2 fails (e.g., network error, constraint violation), Step 1 is **automatically undone**. Money never vanishes.

**How it works internally:**

- The database engine maintains an **Undo Log** (rollback journal).
- Before modifying any data page, the original value is written to the undo log.
- On failure or explicit `ROLLBACK`, the engine replays the undo log in reverse.

**Edge case — Savepoints:**

```sql
SAVEPOINT sp1;
UPDATE orders SET status = 'processing' WHERE id = 101;
-- Only rollback to sp1, not the full transaction
ROLLBACK TO SAVEPOINT sp1;
```

---

### 2. Consistency

> "Every transaction brings the database from one valid state to another."

Consistency ensures that all **database integrity rules** are respected at the end of every transaction. These include:

| Rule Type | Example |
|---|---|
| Domain constraints | `age INT CHECK (age >= 0)` |
| Entity integrity | Primary key must be NOT NULL and unique |
| Referential integrity | Foreign key must reference an existing row |
| User-defined constraints | `CHECK`, `TRIGGER`, `ASSERTION` |

**Important nuance:**

- The **database** enforces schema-level consistency rules automatically.
- **Application-level consistency** (e.g., "total debits must equal total credits") is the developer's responsibility. ACID does not automatically guarantee business logic correctness.

**Example of consistency violation prevention:**

```sql
-- This will be rejected if order_id = 999 does not exist in the orders table
INSERT INTO order_items (order_id, product_id, qty)
VALUES (999, 42, 1);  -- FK violation → transaction aborted
```

---

### 3. Isolation

> "Concurrent transactions do not see each other's intermediate state."

Isolation governs how and when changes made by one transaction become visible to others. Without isolation, concurrent transactions can produce incorrect results even if each is individually correct.

#### Read Phenomena (Anomalies)

**Dirty Read:**
Transaction T2 reads data written by T1 before T1 commits. If T1 rolls back, T2 used data that never officially existed.

```
T1: UPDATE balance SET amount = 500 WHERE id = 1;  -- not committed
T2: SELECT amount FROM balance WHERE id = 1;        -- reads 500 (dirty!)
T1: ROLLBACK;
-- T2 acted on data that never existed
```

**Non-Repeatable Read:**
T2 reads the same row twice, but T1 modifies and commits between the two reads.

```
T2: SELECT amount FROM balance WHERE id = 1;  -- returns 1000
T1: UPDATE balance SET amount = 800 WHERE id = 1; COMMIT;
T2: SELECT amount FROM balance WHERE id = 1;  -- returns 800 (changed!)
```

**Phantom Read:**
T2 executes a range query twice, but T1 inserts/deletes rows in that range between the reads.

```
T2: SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- returns 5
T1: INSERT INTO orders (status) VALUES ('pending'); COMMIT;
T2: SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- returns 6 (phantom!)
```

#### Isolation Level Matrix

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Performance |
|---|---|---|---|---|
| **Read Uncommitted** | ✅ Possible | ✅ Possible | ✅ Possible | Highest |
| **Read Committed** | ❌ Prevented | ✅ Possible | ✅ Possible | High |
| **Repeatable Read** | ❌ Prevented | ❌ Prevented | ✅ Possible | Medium |
| **Serializable** | ❌ Prevented | ❌ Prevented | ❌ Prevented | Lowest |

**Implementation mechanisms:**

- **Pessimistic Locking:** Acquire read/write locks before accessing data. Blocks concurrent access. Used in older RDBMS.
- **MVCC (Multi-Version Concurrency Control):** Each transaction sees a consistent **snapshot** of the data taken at its start time. Writers don't block readers. Used in PostgreSQL, MySQL InnoDB, Oracle.

---

### 4. Durability

> "Committed data survives any failure."

Once a `COMMIT` succeeds, the changes are permanent — they survive system crashes, power failures, or OS restarts.

**How it works internally — Write-Ahead Logging (WAL):**

1. Before modifying any data page on disk, the change is written to a **sequential log file (WAL)**.
2. Only after the WAL entry is flushed to durable storage is the `COMMIT` acknowledged to the client.
3. Actual data page updates happen asynchronously (for performance).
4. On recovery after a crash, the database replays the WAL to restore all committed transactions.

**WAL flow:**

```
Client COMMIT
    ↓
WAL entry flushed to disk (fdatasync)
    ↓
COMMIT acknowledged to client ✓
    ↓
Data page updated in background (async)
```

**Durability levels (PostgreSQL `synchronous_commit`):**

| Setting | Durability | Performance |
|---|---|---|
| `on` (default) | Full — WAL on primary flushed | Normal |
| `remote_write` | WAL sent to replica but not flushed | Faster |
| `off` | WAL not immediately flushed | Fastest (small data loss window) |

---

## BASE — Deep Dive

BASE stands for **Basically Available, Soft State, Eventually Consistent**. Coined by Eric Brewer and Dan Pritchett (Amazon, 2008), it describes the consistency model adopted by large-scale distributed systems.

---

### 1. Basically Available

> "The system guarantees availability, even if some nodes are degraded or partitioned."

In a distributed system, network partitions are inevitable. When a partition occurs, a system must choose between:

- **Consistency** — refuse requests that can't be fulfilled correctly (ACID approach)
- **Availability** — respond to every request, even if the data might be stale

BASE systems choose **availability**. They continue serving reads and writes even when some nodes are unreachable. Responses may be stale or approximate, but the system never goes down.

**Example — Amazon DynamoDB:**
During a network partition, DynamoDB continues accepting writes to all available nodes. It resolves conflicts after the partition heals using **vector clocks** or **last-write-wins**.

---

### 2. Soft State

> "The state of the system may change over time, even without new input."

In an ACID system, state changes only when a transaction explicitly changes it. In BASE systems, the state is in flux because:

- **Replication is asynchronous** — replicas may lag behind.
- **Anti-entropy processes** run in the background to reconcile differences.
- **TTLs (Time-to-Live)** expire cached data automatically.
- **Compaction** and **tombstone cleanup** may alter physical state.

The system is not "resting" between transactions — it is continuously converging toward a consistent state.

---

### 3. Eventually Consistent

> "Given no new updates, all replicas will converge to the same value — eventually."

This is the core consistency guarantee: consistency is not instantaneous but **eventual**. After a write is performed, there is a time window during which different nodes may return different values for the same key.

**Formal definition:**
If no new updates are made to an object, eventually all reads will return the last written value.

**Example — Cassandra Write:**

```
Write: user_id=42, email='new@example.com'
→ Written to Node A immediately
→ Replicated to Node B after ~50ms
→ Replicated to Node C after ~120ms

During this window:
  Read from A → new@example.com  ✓
  Read from B → old@example.com  (stale, soft state)
  Read from C → old@example.com  (stale, soft state)
```

**Tunable consistency (Cassandra):**

```
Write Consistency = QUORUM (majority of replicas must acknowledge)
Read Consistency  = QUORUM (majority of replicas must respond)
→ Overlap guarantees you always read the latest write
```

---

## CAP Theorem — The Foundation

The **CAP Theorem** (Brewer, 2000) states that a distributed system can only guarantee **two of three** properties simultaneously:

| Property | Definition |
|---|---|
| **C**onsistency | Every read returns the most recent write |
| **A**vailability | Every request receives a response (not an error) |
| **P**artition Tolerance | System continues operating when network partitions occur |

Since **network partitions are unavoidable** in any real distributed system, the practical choice is always between **CP** and **AP**:

```
                    CAP Triangle

                  Consistency
                      /\
                     /  \
                    /    \
          ACID-RDBMs      NoSQL (CP)
          (CA systems)    e.g., HBase, Zookeeper
                    \    /
                     \  /
                      \/
                  Partition
                  Tolerance
                  (PA systems)
            NoSQL (AP): Cassandra,
            DynamoDB, CouchDB
```

| System Type | CAP Choice | Model |
|---|---|---|
| Traditional RDBMS (single node) | CA (no partitions) | ACID |
| HBase, Zookeeper, MongoDB (w/ primary) | CP | ACID-like |
| Cassandra, DynamoDB, CouchDB | AP | BASE |

---

## ACID vs BASE — Side-by-Side

| Dimension | ACID | BASE |
|---|---|---|
| **Consistency guarantee** | Strong — immediate | Weak — eventual |
| **Availability** | May sacrifice for consistency | Always available |
| **Partition handling** | Reject operations | Accept, reconcile later |
| **State** | Stable between transactions | Continuously evolving |
| **Concurrency model** | Locking / MVCC | Optimistic / conflict resolution |
| **Transactions** | Multi-row, multi-table ACID tx | Single-row atomic; limited multi-row |
| **Scalability** | Vertical (scale-up) preferred | Horizontal (scale-out) designed for |
| **Complexity** | Database handles it | Application must handle stale reads |
| **Latency** | Higher (locking, fsync) | Lower (async replication) |
| **Use cases** | Financial, medical, ERP, e-commerce | Social, analytics, IoT, search, cache |

---

## Isolation Levels in ACID

### Read Phenomena

| Phenomenon | Description | Prevents With |
|---|---|---|
| **Dirty Read** | Reading uncommitted data | Read Committed+ |
| **Non-Repeatable Read** | Same row, different values in same TX | Repeatable Read+ |
| **Phantom Read** | Range query returns different rows | Serializable |
| **Lost Update** | Two TXs update same row; one overwrites | Repeatable Read (with `FOR UPDATE`) |
| **Write Skew** | Two TXs read same data and make inconsistent decisions | Serializable |

### Isolation Level Matrix

| Level | Standard | PostgreSQL | MySQL InnoDB | Oracle |
|---|---|---|---|---|
| Read Uncommitted | Yes | Treated as Read Committed | Yes | Not supported |
| Read Committed | Yes | Default | Available | Default |
| Repeatable Read | Yes | Available | **Default** | Not standard |
| Serializable | Yes | Available | Available | Serializable |

---

## Consistency Models in BASE

BASE systems offer a **spectrum** of consistency models, not a binary:

| Model | Description | Example |
|---|---|---|
| **Strong consistency** | All nodes see the same value instantly | Single-master with sync replication |
| **Linearizability** | Operations appear instantaneous to all observers | Zookeeper, etcd |
| **Sequential consistency** | All nodes see ops in the same order (not necessarily real-time) | — |
| **Causal consistency** | Causally related ops are seen in order; concurrent ops may vary | MongoDB sessions |
| **Read-your-writes** | You always see your own writes | Cassandra (LOCAL_QUORUM) |
| **Monotonic reads** | Once you read a value, you never see an older value | Session-level guarantee |
| **Eventual consistency** | All replicas converge; no ordering guarantee | Cassandra (ONE), DynamoDB |

---

## Internal Mechanisms

### How ACID is Implemented

| Property | Mechanism |
|---|---|
| **Atomicity** | Undo Log — records "before images" of every modified row; replayed on rollback |
| **Consistency** | Constraint engine — checks FK, CHECK, NOT NULL before commit |
| **Isolation** | MVCC — each TX sees snapshot at start time; OR 2PL locking |
| **Durability** | Write-Ahead Log (WAL) — change logged to disk before data page updated |

**PostgreSQL WAL lifecycle:**

```
1. Transaction modifies a tuple
2. WAL record written to WAL buffer (in-memory)
3. On COMMIT: WAL buffer flushed to WAL file (fdatasync)
4. Checkpoint: dirty data pages written to heap files
5. On crash recovery: WAL replayed from last checkpoint
```

---

### How BASE is Implemented

| Concept | Mechanism |
|---|---|
| **Replication** | Async replication to multiple nodes (eventual convergence) |
| **Conflict resolution** | Last-Write-Wins (LWW), Vector Clocks, CRDTs |
| **Availability** | Consistent hashing + virtual nodes (no SPOF) |
| **Tunable consistency** | Quorum reads/writes (R + W > N for strong consistency) |
| **Anti-entropy** | Background Merkle tree comparison and repair |
| **Compaction** | SSTables merged to remove stale versions |

**Quorum formula (Cassandra/Dynamo):**

```
N = total replicas
W = write quorum (nodes that must acknowledge write)
R = read quorum (nodes that must respond to read)

For strong consistency: R + W > N
For eventual consistency: R + W ≤ N (faster, stale reads possible)

Example: N=3, W=2, R=2 → 2+2 > 3 → Strong consistency
Example: N=3, W=1, R=1 → 1+1 ≤ 3 → Eventual consistency (fastest)
```

---

## Database Examples

| Database | Model | Notes |
|---|---|---|
| **PostgreSQL** | ACID | MVCC isolation; WAL durability; all 4 isolation levels |
| **MySQL InnoDB** | ACID | Repeatable Read default; MVCC; supports Serializable |
| **Oracle** | ACID | Read Committed default; strong MVCC implementation |
| **SQL Server** | ACID | Supports snapshot isolation (RCSI) in addition to standard levels |
| **MongoDB** | Hybrid | ACID multi-document transactions (v4.0+); single-doc atomic always |
| **Cassandra** | BASE (AP) | Tunable consistency; LWT (Lightweight Transactions) for limited ACID |
| **DynamoDB** | Hybrid | Eventually consistent by default; strongly consistent reads opt-in; ACID transactions available |
| **Redis** | BASE | Single-threaded atomic ops; optional persistence; MULTI/EXEC pseudo-transactions |
| **HBase** | BASE (CP) | Strong consistency per row; no cross-row transactions |
| **CouchDB** | BASE (AP) | MVCC per document; conflict revision tree |
| **CockroachDB** | Distributed ACID | Serializable isolation across geo-distributed nodes |
| **Google Spanner** | Distributed ACID | External consistency via TrueTime; globally distributed ACID |

---

## When to Choose ACID vs BASE

### Choose ACID when:

- **Financial transactions** — money transfers, payments, ledgers (correctness is non-negotiable)
- **Medical records** — patient data must never be lost or incorrect
- **Order management** — inventory deductions, order creation, payment — must be atomic
- **User authentication** — password changes, session management
- **Regulatory compliance** — GDPR, HIPAA, SOX require audit trails and data integrity
- **Multi-entity operations** — when a single business operation spans multiple tables/rows and all must succeed

### Choose BASE when:

- **Social media feeds** — slightly stale feeds are acceptable
- **Product catalogues** — reads vastly outnumber writes; eventual consistency is fine
- **Analytics and time-series** — high write throughput; strong consistency not needed
- **Session/cache data** — TTL-based; ephemeral by nature
- **IoT telemetry** — millions of writes/second; approximate reads acceptable
- **Search indexes** — Elasticsearch; near-real-time is sufficient
- **Content delivery** — CDN-level caching; staleness is expected

---

## Hybrid Approaches

Modern systems blur the ACID/BASE boundary:

### 1. ACID on a per-document basis (MongoDB)

```javascript
// Single document — always atomic
db.orders.updateOne({ _id: 101 }, { $set: { status: "shipped" } })

// Multi-document — ACID transaction (v4.0+)
const session = client.startSession();
session.withTransaction(async () => {
  await orders.updateOne({ _id: 101 }, { $set: { status: "shipped" } }, { session });
  await inventory.updateOne({ productId: 42 }, { $inc: { qty: -1 } }, { session });
});
```

### 2. Tunable consistency (Cassandra)

```cql
-- Eventual (fast, may be stale)
SELECT * FROM orders WHERE id = 101;   -- Consistency ONE

-- Strong (slower, always latest)
SELECT * FROM orders WHERE id = 101 USING CONSISTENCY QUORUM;
```

### 3. NewSQL — Distributed ACID (CockroachDB / Spanner)

```sql
-- Full ACID transaction across geographically distributed nodes
BEGIN;
  INSERT INTO transfers (from_acct, to_acct, amount) VALUES (1, 2, 500);
  UPDATE accounts SET balance = balance - 500 WHERE id = 1;
  UPDATE accounts SET balance = balance + 500 WHERE id = 2;
COMMIT;
-- Serializable isolation guaranteed across data centres
```

---

## Spring Boot / JPA Context

### ACID with Spring `@Transactional`

```java
@Service
public class TransferService {

    @Transactional                              // Atomicity + Isolation
    public void transfer(Long from, Long to, BigDecimal amount) {
        Account sender   = accountRepo.findById(from).orElseThrow();
        Account receiver = accountRepo.findById(to).orElseThrow();

        if (sender.getBalance().compareTo(amount) < 0)
            throw new InsufficientFundsException();  // Triggers rollback

        sender.debit(amount);
        receiver.credit(amount);

        accountRepo.save(sender);    // Both saved or neither
        accountRepo.save(receiver);
    }
}
```

### Isolation level configuration

```java
@Transactional(isolation = Isolation.SERIALIZABLE)   // Strongest
@Transactional(isolation = Isolation.READ_COMMITTED)  // Default in most DBs
@Transactional(isolation = Isolation.REPEATABLE_READ)
```

### BASE with Spring and Redis/Cassandra

```java
@Service
public class ProductCacheService {

    @Cacheable(value = "products", key = "#id")     // Eventual consistency via Redis
    public Product getProduct(Long id) {
        return productRepository.findById(id).orElseThrow();
    }

    @CacheEvict(value = "products", key = "#product.id")
    public void updateProduct(Product product) {
        productRepository.save(product);
        // Cache evicted; next read re-fetches from DB
        // Brief window of stale data is acceptable
    }
}
```

---

## Quick-Reference Summary

```
╔══════════════════════════════════════════════════════════════════════╗
║                        ACID vs BASE                                  ║
╠══════════════════╦═══════════════════════╦════════════════════════════╣
║ Property         ║ ACID                  ║ BASE                       ║
╠══════════════════╬═══════════════════════╬════════════════════════════╣
║ Consistency      ║ Immediate / Strong    ║ Eventual / Weak            ║
║ Availability     ║ May be sacrificed     ║ Always available           ║
║ Partitions       ║ Reject ops            ║ Accept, reconcile later    ║
║ State            ║ Stable                ║ Soft / Evolving            ║
║ Transactions     ║ Full multi-row ACID   ║ Row-level atomic           ║
║ Scalability      ║ Vertical              ║ Horizontal                 ║
║ Latency          ║ Higher                ║ Lower                      ║
║ Complexity       ║ DB manages it         ║ App must handle staleness  ║
╠══════════════════╬═══════════════════════╬════════════════════════════╣
║ Best for         ║ Finance, Medical, ERP ║ Social, IoT, Analytics     ║
║ Examples         ║ PostgreSQL, Oracle    ║ Cassandra, DynamoDB        ║
╚══════════════════╩═══════════════════════╩════════════════════════════╝
```

**The golden rule:**
> Choose ACID when **correctness is non-negotiable**.
> Choose BASE when **scale and availability outweigh the cost of occasional staleness**.
> Use **NewSQL (CockroachDB, Spanner)** or **hybrid modes** when you need both.

---

*References: Brewer (2000) CAP Theorem, Pritchett (2008) BASE, SQL ISO/IEC 9075, PostgreSQL Documentation, Cassandra Architecture Guide.*
