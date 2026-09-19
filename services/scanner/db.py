import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from services.scanner.state_machine import validate_state_transition

def init_db(db_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    return conn

def create_tables(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                target_domains TEXT NOT NULL,
                policy_json TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_state_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                from_status TEXT NOT NULL,
                to_status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans (scan_id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crawl_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                url TEXT NOT NULL,
                discovery_source TEXT NOT NULL,
                depth INTEGER NOT NULL,
                decision TEXT NOT NULL,
                status_code INTEGER,
                content_type TEXT,
                rejection_reason TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (scan_id) REFERENCES scans (scan_id)
            );
        """)

def create_scan_record(
    conn: sqlite3.Connection,
    scan_id: str,
    target_domains: List[str],
    policy_dict: Dict[str, Any]
) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    status = "draft"
    domains_str = ",".join(target_domains)
    policy_json = json.dumps(policy_dict, default=str)

    with conn:
        conn.execute(
            """
            INSERT INTO scans (scan_id, created_at, updated_at, status, target_domains, policy_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (scan_id, now, now, status, domains_str, policy_json)
        )
        conn.execute(
            """
            INSERT INTO scan_state_history (scan_id, from_status, to_status, timestamp, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_id, "none", status, now, "Scan job created")
        )

    return get_scan_record(conn, scan_id)

def get_scan_record(conn: sqlite3.Connection, scan_id: str) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
    row = cur.fetchone()
    if not row:
        return None

    scan_dict = dict(row)
    scan_dict["policy_json"] = json.loads(scan_dict["policy_json"])
    scan_dict["target_domains"] = scan_dict["target_domains"].split(",") if scan_dict["target_domains"] else []
    return scan_dict

def update_scan_status(
    conn: sqlite3.Connection,
    scan_id: str,
    new_status: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    record = get_scan_record(conn, scan_id)
    if not record:
        raise ValueError(f"Scan job with ID '{scan_id}' not found.")

    current_status = record["status"]
    validate_state_transition(current_status, new_status)

    now = datetime.now().isoformat()

    with conn:
        conn.execute(
            "UPDATE scans SET status = ?, updated_at = ? WHERE scan_id = ?",
            (new_status, now, scan_id)
        )
        conn.execute(
            """
            INSERT INTO scan_state_history (scan_id, from_status, to_status, timestamp, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_id, current_status, new_status, now, reason or "Status transition")
        )

    return get_scan_record(conn, scan_id)

def cancel_scan_job(
    conn: sqlite3.Connection,
    scan_id: str,
    reason: str = "User initiated cancellation"
) -> Dict[str, Any]:
    return update_scan_status(conn, scan_id, "cancelled", reason)

def emergency_stop_scan_job(
    conn: sqlite3.Connection,
    scan_id: str,
    reason: str = "Emergency stop triggered"
) -> Dict[str, Any]:
    return update_scan_status(conn, scan_id, "blocked", reason)

def is_scan_active(conn: sqlite3.Connection, scan_id: str) -> bool:
    record = get_scan_record(conn, scan_id)
    if not record:
        return False
    return record["status"] in ("queued", "running")

def get_scan_history(conn: sqlite3.Connection, scan_id: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM scan_state_history WHERE scan_id = ? ORDER BY history_id ASC", (scan_id,))
    return [dict(row) for row in cur.fetchall()]

def save_crawl_coverage_records(
    conn: sqlite3.Connection,
    scan_id: str,
    items: List[Dict[str, Any]]
) -> None:
    record = get_scan_record(conn, scan_id)
    if not record:
        raise ValueError(f"Scan job with ID '{scan_id}' not found.")

    with conn:
        for item in items:
            decision_val = item.get("decision")
            if hasattr(decision_val, "value"):
                decision_val = decision_val.value
            else:
                decision_val = str(decision_val) if decision_val is not None else ""

            ts = item.get("timestamp")
            if hasattr(ts, "isoformat"):
                ts = ts.isoformat()
            elif not ts:
                ts = datetime.now().isoformat()
            else:
                ts = str(ts)

            conn.execute(
                """
                INSERT INTO crawl_coverage (
                    scan_id, url, discovery_source, depth, decision, status_code, content_type, rejection_reason, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    item.get("url"),
                    item.get("discovery_source"),
                    item.get("depth", 0),
                    decision_val,
                    item.get("status_code"),
                    item.get("content_type"),
                    item.get("rejection_reason"),
                    ts
                )
            )

def get_scan_coverage_summary(conn: sqlite3.Connection, scan_id: str) -> Dict[str, Any]:
    record = get_scan_record(conn, scan_id)
    if not record:
        raise ValueError(f"Scan job with ID '{scan_id}' not found.")

    cur = conn.cursor()
    cur.execute("SELECT * FROM crawl_coverage WHERE scan_id = ? ORDER BY id ASC", (scan_id,))
    rows = cur.fetchall()

    items = []
    visited_count = 0
    skipped_count = 0
    blocked_count = 0

    for row in rows:
        item = dict(row)
        item.pop("id", None)
        item.pop("scan_id", None)
        decision = item.get("decision")
        if decision == "visited":
            visited_count += 1
        elif decision == "skipped":
            skipped_count += 1
        elif decision == "blocked":
            blocked_count += 1

        items.append(item)

    return {
        "scan_id": scan_id,
        "total_discovered": len(items),
        "visited_count": visited_count,
        "skipped_count": skipped_count,
        "blocked_count": blocked_count,
        "items": items
    }

