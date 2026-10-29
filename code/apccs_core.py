"""APCCS Batch 1 only. Python 3.11+, POSIX, standard library.

Default workspace: /mnt/data. Override APCCS_VAULT_ROOT before import only
for an isolated installation/test. The parent of the vault is the counted
workspace. Cooperating callers are serialized; OS quotas are not provided.
"""
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid
import zipfile
from zoneinfo import ZoneInfo

ROOT = Path(os.environ.get('APCCS_VAULT_ROOT', '/mnt/data/apccs_central_vault')).absolute()
WORKSPACE = ROOT.parent
CATEGORIES = ('code', 'engines', 'rules', 'state', 'conversations', 'changes',
              'legal', 'research', 'evidence', 'reports', 'imports', 'exports', 'audit')
ARCHIVE_NAME = 'APCCS_MASTER_BUILD.zip'
LOG_NAME = 'MASTER_CONVERSATION_AND_CHANGE_HISTORY.md'
MANIFEST_NAME = 'RECOVERY_MANIFEST.json'
PACK_AT = 790
STOP_AT = 800
RESERVE = 10


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _count():
    count = 0
    def fail(error):
        raise error
    for directory, subdirs, files in os.walk(WORKSPACE, followlinks=False, onerror=fail):
        count += len(files)
        for name in list(subdirs):
            if Path(directory, name).is_symlink():
                count += 1
                subdirs.remove(name)
    return count


def _boot():
    if ROOT.is_symlink() or ROOT.resolve() != ROOT:
        raise ValueError('Vault path must not contain symlinks')
    ROOT.mkdir(parents=True, exist_ok=True)
    for name in CATEGORIES:
        folder = ROOT / name
        if folder.is_symlink():
            raise ValueError('Category symlinks are forbidden')
        folder.mkdir(exist_ok=True)


def verify_safe_path(target_path):
    raw = Path(target_path)
    if '..' in raw.parts:
        raise ValueError('Parent traversal rejected')
    root = ROOT.resolve()
    resolved = (ROOT / raw).resolve()
    for name in CATEGORIES:
        category = ROOT / name
        if category.is_symlink():
            raise ValueError('Category symlink rejected')
        allowed = category.resolve()
        if allowed.is_relative_to(root) and resolved.is_relative_to(allowed):
            return resolved
    raise ValueError('Path outside the 13 approved categories')


@contextlib.contextmanager
def _locked():
    _boot()
    path = verify_safe_path('state/batch1.lock')
    if not path.exists() and _count() + RESERVE >= STOP_AT:
        raise RuntimeError('Insufficient reserve to bootstrap safely')
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _db():
    path = verify_safe_path('state/prompt_engine.db')
    if not path.exists() and _count() + RESERVE >= STOP_AT:
        raise RuntimeError('Insufficient file reserve to initialize database')
    db = sqlite3.connect(path, timeout=120)
    db.execute('PRAGMA busy_timeout=120000')
    db.execute('PRAGMA foreign_keys=ON')
    if db.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower() != 'wal':
        db.close()
        raise RuntimeError('WAL unavailable')
    db.execute('PRAGMA synchronous=FULL')
    def authorize(action, first, second, database, trigger):
        forbidden = (sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_DROP_INDEX,
                     sqlite3.SQLITE_DROP_VIEW, sqlite3.SQLITE_DROP_TRIGGER,
                     sqlite3.SQLITE_ALTER_TABLE)
        return sqlite3.SQLITE_DENY if action in forbidden else sqlite3.SQLITE_OK
    db.set_authorizer(authorize)
    try:
        db.execute('CREATE TABLE IF NOT EXISTS engine_registry_v2 ('
                   'engine_id TEXT PRIMARY KEY, name TEXT NOT NULL, rules_text TEXT NOT NULL, '
                   'version TEXT NOT NULL, sha256 TEXT NOT NULL, state TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS verbatim_turns ('
                   'id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, correlation TEXT NOT NULL, '
                   'badge TEXT NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS engine_rules_hashes ('
                   'engine_id TEXT PRIMARY KEY REFERENCES engine_registry_v2(engine_id), '
                   'rules_sha256 TEXT NOT NULL)')
        db.commit()
        return db
    except BaseException:
        db.close()
        raise


def _rows(db):
    rows = []
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'history' in tables:
        for number, timestamp, correlation, badge, kind, body in db.execute('SELECT * FROM history ORDER BY id'):
            rows.append((number, timestamp, correlation, badge, kind, body))
    offset = max((row[0] for row in rows), default=0)
    for number, timestamp, correlation, badge, role, text in db.execute('SELECT * FROM verbatim_turns ORDER BY id'):
        rows.append((offset + number, timestamp, correlation, badge, role, text))
    return rows


def _log_bytes(db):
    sections = ['# MASTER CONVERSATION AND CHANGE HISTORY\n']
    for number, stamp, correlation, badge, role, text in _rows(db):
        sections.append(f'\n## Entry {number:04d} / CHG-{number:04d}\n'
                        f'Timestamp: {stamp} [America/Vancouver]\n'
                        f'Correlation ID: {correlation}\nBadge: {badge}\nRole: {role}\n'
                        f'UTF-8 bytes: {len(text.encode())}\nSHA-256: {sha256(text.encode())}\n'
                        f'BEGIN VERBATIM\n{text}\nEND VERBATIM\n')
    return ''.join(sections).encode()


def _checkpoint(db, extras=None):
    """Commit before calling. Old derived members retained by content hash."""
    target = verify_safe_path('exports/' + ARCHIVE_NAME)
    temporary = verify_safe_path('exports/' + uuid.uuid4().hex + '.tmp')
    members = {}
    if target.exists():
        with zipfile.ZipFile(target) as old:
            if len(old.namelist()) != len(set(old.namelist())) or old.testzip() is not None:
                raise ValueError('Existing archive is corrupt or has duplicate members')
            for name in old.namelist():
                if Path(name).is_absolute() or '..' in Path(name).parts:
                    raise ValueError('Unsafe archive member')
                members[name] = old.read(name)
    backup = sqlite3.connect(':memory:')
    try:
        db.backup(backup)
        updates = {LOG_NAME: _log_bytes(db), 'state/prompt_engine.db': backup.serialize()}
    finally:
        backup.close()
    reserved = set(updates) | {MANIFEST_NAME}
    for name, data in (extras or {}).items():
        if name in reserved or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Reserved or unsafe member')
        if name in members and members[name] != data:
            raise ValueError('Refusing to overwrite a user artifact')
        updates[name] = data
    for name, data in updates.items():
        if name in members and members[name] != data:
            old = members[name]
            members.setdefault('recovery/versions/' + sha256(old) + '/' + name, old)
        members[name] = data
    if MANIFEST_NAME in members:
        old = members.pop(MANIFEST_NAME)
        members.setdefault('recovery/versions/' + sha256(old) + '/' + MANIFEST_NAME, old)
    manifest = dict(schema=1, timezone='America/Vancouver',
        checkpoint_timestamp=dt.datetime.now(ZoneInfo('America/Vancouver')).isoformat(),
        latest_change=max((r[0] for r in _rows(db)), default=0),
        files={name: dict(size=len(data), sha256=sha256(data)) for name, data in members.items()},
        recovery='Verify all hashes; extract database to an EMPTY vault only. Never replace a live database.')
    members[MANIFEST_NAME] = json.dumps(manifest, indent=2).encode()
    try:
        with zipfile.ZipFile(temporary, 'x', zipfile.ZIP_DEFLATED) as out:
            for name, data in members.items():
                out.writestr(name, data)
        with temporary.open('rb') as handle:
            os.fsync(handle.fileno())
        with zipfile.ZipFile(temporary) as check:
            if check.testzip() is not None:
                raise RuntimeError('Checkpoint ZIP verification failed')
        os.replace(temporary, target)
        directory = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
    return str(target)


def _ceiling(db, max_files):
    if type(max_files) is not int or not 16 <= max_files <= 1024:
        raise ValueError('max_files must be an integer in 16..1024')
    before = _count()
    packed = 0
    trigger = min(PACK_AT, max_files - RESERVE)
    if before + RESERVE >= min(STOP_AT, max_files):
        directory = verify_safe_path('changes/loose_logs')
        candidates = []
        if directory.exists():
            for path in directory.iterdir():
                if path.suffix == '.log' and path.is_file() and not path.is_symlink():
                    candidates.append((path, path.read_bytes()))
        if candidates:
            extras = {'packed_logs/' + sha256(data) + '/' + path.name: data for path, data in candidates}
            archive = _checkpoint(db, extras)
            with zipfile.ZipFile(archive) as saved:
                for path, data in candidates:
                    name = 'packed_logs/' + sha256(data) + '/' + path.name
                    if saved.read(name) != data or path.read_bytes() != data:
                        raise RuntimeError('Log changed; source retained')
                    path.unlink()
                    packed += 1
    count = _count()
    return dict(file_count=count, percentage=count * 100 / max_files,
                max_files=max_files, pack_trigger=trigger, stop_at=min(STOP_AT, max_files),
                reserve=RESERVE, packed_logs=packed, count_before=before,
                status='OK' if count + RESERVE < min(STOP_AT, max_files) else 'BLOCKED')


def _admit(db):
    result = _ceiling(db, 1024)
    if result['status'] != 'OK':
        raise RuntimeError('File ceiling reserve exhausted')


def check_file_ceiling(max_files=1024):
    with _locked(), contextlib.closing(_db()) as db:
        return _ceiling(db, max_files)


def init_master_db():
    """Caller owns returned connection and must close it; never replaces DB."""
    with _locked():
        db = _db()
        try:
            _admit(db)
            return db
        except BaseException:
            db.close()
            raise


def _engine_hash(engine_id, name, rules_text, version):
    raw = json.dumps([engine_id, name, rules_text, version], ensure_ascii=False, separators=(',', ':')).encode()
    return sha256(raw)


def load_or_mount_engine(engine_id, name, rules_text, version, rules_sink=None):
    """Approved host contract: optional unary sink; return verified rule text/hash.

    Sink invocation means delivery to the host callable, not proof of UI
    injection. Host owns the local Terminal/Web UI chat-box integration.
    """
    if not all(isinstance(x, str) and x for x in (engine_id, name, rules_text, version)):
        raise ValueError('All engine fields must be nonempty strings')
    if rules_sink is not None and not callable(rules_sink):
        raise TypeError('rules_sink must be callable or None')
    engine_hash = _engine_hash(engine_id, name, rules_text, version)
    rules_hash = sha256(rules_text.encode('utf-8'))
    with _locked(), contextlib.closing(_db()) as db:
        _admit(db)
        with db:
            row = db.execute('SELECT name,rules_text,version,sha256,state FROM engine_registry_v2 WHERE engine_id=?', (engine_id,)).fetchone()
            if row:
                if row[3] != engine_hash or _engine_hash(engine_id, *row[:3]) != row[3]:
                    raise ValueError('Installed engine differs or failed SHA-256 verification')
                status = 'ALREADY_INSTALLED_MOUNTED_ZERO_DUPLICATES'
                state = json.loads(row[4])
                loaded_rules = row[1]
            else:
                legacy = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='engines'").fetchone()
                if legacy and db.execute('SELECT 1 FROM engines WHERE name=?', (name,)).fetchone():
                    raise ValueError('Legacy engine exists; explicit ID mapping required; refusing reinstall')
                db.execute('INSERT INTO engine_registry_v2 VALUES (?,?,?,?,?,?)',
                           (engine_id, name, rules_text, version, engine_hash, '{}'))
                status, state, loaded_rules = 'INSTALLED', {}, rules_text
            if sha256(loaded_rules.encode('utf-8')) != rules_hash:
                raise ValueError('Stored rule text hash mismatch')
            stored_hash = db.execute('SELECT rules_sha256 FROM engine_rules_hashes WHERE engine_id=?', (engine_id,)).fetchone()
            if stored_hash:
                if stored_hash[0] != rules_hash:
                    raise ValueError('Persisted rules SHA-256 mismatch')
            else:
                db.execute('INSERT INTO engine_rules_hashes VALUES (?,?)', (engine_id, rules_hash))
    if rules_sink is not None:
        rules_sink(loaded_rules)
    return dict(status=status, state=state, rules_text=loaded_rules,
                sha256=rules_hash, rules_sha256=rules_hash, engine_sha256=engine_hash,
                delivery='HOST_SINK_CALLED' if rules_sink is not None else 'RETURNED_FOR_HOST_INJECTION')


def record_turn_and_checkpoint(text, role='user', badge='GRAY', correlation_id=None):
    if not isinstance(text, str) or badge not in ('GREEN', 'GRAY', 'RED'):
        raise ValueError('Invalid text or badge')
    if not isinstance(role, str) or not role:
        raise ValueError('Nonempty role required')
    with _locked(), contextlib.closing(_db()) as db:
        _admit(db)
        stamp = dt.datetime.now(ZoneInfo('America/Vancouver')).isoformat()
        correlation = correlation_id or str(uuid.uuid4())
        with db:
            db.execute('INSERT INTO verbatim_turns(timestamp,correlation,badge,role,text) VALUES (?,?,?,?,?)',
                       (stamp, correlation, badge, role, text))
        number = max(row[0] for row in _rows(db))
        archive = _checkpoint(db)
        return dict(entry=f'Entry {number:04d}', change=f'CHG-{number:04d}',
                    timestamp=stamp, correlation_id=correlation, archive=archive)


def recover_checkpoint():
    """Repair archive after a committed turn whose publication was interrupted."""
    with _locked(), contextlib.closing(_db()) as db:
        _admit(db)
        return _checkpoint(db)


def package_artifacts(artifacts):
    """Add immutable source/audit members without replacing user artifacts."""
    with _locked(), contextlib.closing(_db()) as db:
        _admit(db)
        return _checkpoint(db, artifacts)


# Batch 2 additions. The complete Batch 1 prefix above is unchanged.
import base64
import concurrent.futures
import hmac
import math
import queue
import re
import threading
import time


def _b2_number(value, label):
    if type(value) not in (int, float):
        raise ValueError(label + ' must be a finite number')
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(label + ' must be a finite number')
    return value


def _b2_key(secret):
    if isinstance(secret, str):
        secret = secret.encode('utf-8')
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ValueError('HS256 key must contain at least 32 bytes')
    return secret


def _b2_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def _b2_b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _b2_unb64(value):
    if not isinstance(value, str) or re.fullmatch(r'[A-Za-z0-9_-]+', value) is None:
        raise ValueError('Invalid base64url')
    try:
        data = base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError('Invalid base64url') from error
    if _b2_b64(data) != value:
        raise ValueError('Noncanonical base64url')
    return data


def _b2_object(value):
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = item
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON constant')
    try:
        decoded = json.loads(value.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid JSON') from error
    if not isinstance(decoded, dict):
        raise ValueError('JSON object required')
    return decoded


def _b2_dates(payload):
    if 'exp' not in payload or 'nbf' not in payload:
        raise ValueError('exp and nbf are required')
    exp = _b2_number(payload['exp'], 'exp')
    nbf = _b2_number(payload['nbf'], 'nbf')
    if exp <= nbf:
        raise ValueError('exp must follow nbf')
    return exp, nbf


def generate_jwt(payload_dict, secret, exp_seconds=3600):
    """Fixed HS256 JWT. Supplied exp/nbf are preserved; absent claims default."""
    key = _b2_key(secret)
    duration = _b2_number(exp_seconds, 'exp_seconds')
    now = _b2_number(time.time(), 'clock')
    if duration <= 0 or not isinstance(payload_dict, dict):
        raise ValueError('Positive lifetime and dict payload required')
    payload = dict(payload_dict)
    payload.setdefault('nbf', now)
    payload.setdefault('exp', now + duration)
    _b2_dates(payload)
    signed = (_b2_b64(_b2_json({'alg': 'HS256', 'typ': 'JWT'})) + '.' + _b2_b64(_b2_json(payload))).encode('ascii')
    token = signed.decode() + '.' + _b2_b64(hmac.new(key, signed, hashlib.sha256).digest())
    if len(token) > 16384:
        raise ValueError('JWT exceeds size limit')
    return token


def verify_jwt(token_str, secret):
    key = _b2_key(secret)
    now = _b2_number(time.time(), 'clock')
    if not isinstance(token_str, str) or len(token_str) > 16384:
        raise ValueError('Invalid JWT')
    parts = token_str.split('.')
    if len(parts) != 3:
        raise ValueError('Three JWT segments required')
    header = _b2_object(_b2_unb64(parts[0]))
    if header != {'alg': 'HS256', 'typ': 'JWT'}:
        raise ValueError('Only the fixed HS256 JWT header is accepted')
    expected = hmac.new(key, (parts[0] + '.' + parts[1]).encode('ascii'), hashlib.sha256).digest()
    if not hmac.compare_digest(_b2_unb64(parts[2]), expected):
        raise ValueError('JWT signature mismatch')
    payload = _b2_object(_b2_unb64(parts[1]))
    exp, nbf = _b2_dates(payload)
    if now >= exp:
        raise ValueError('JWT expired')
    if now < nbf:
        raise ValueError('JWT not yet valid')
    return payload


class TokenBucketRateLimiter:
    """Default: capacity 120, refill 120/minute; allow returns (bool, seconds).

    Host authenticates channel identities. Buckets are bounded and never
    silently evicted, preventing quota reset by reopening a known channel.
    """
    def __init__(self, rate_per_minute=120, capacity=None, max_channels=20, clock=time.monotonic):
        self.rate = _b2_number(rate_per_minute, 'rate_per_minute') / 60
        self.capacity = _b2_number(rate_per_minute if capacity is None else capacity, 'capacity')
        if self.rate <= 0 or self.capacity <= 0 or type(max_channels) is not int or max_channels < 1:
            raise ValueError('Positive quota and channel bound required')
        self.clock, self.max_channels = clock, max_channels
        self._lock, self._buckets = threading.Lock(), {}

    def allow(self, channel_id, tokens=1):
        tokens = _b2_number(tokens, 'tokens')
        if not isinstance(channel_id, str) or not channel_id or not 0 < tokens <= self.capacity:
            raise ValueError('Valid channel identity and debit required')
        with self._lock:
            now = _b2_number(self.clock(), 'monotonic clock')
            if channel_id not in self._buckets:
                if len(self._buckets) >= self.max_channels:
                    raise ValueError('Channel quota registry full')
                self._buckets[channel_id] = (self.capacity, now)
            balance, previous = self._buckets[channel_id]
            if now < previous:
                raise ValueError('Monotonic clock moved backwards')
            balance = min(self.capacity, balance + (now - previous) * self.rate)
            allowed = balance >= tokens
            if allowed:
                balance -= tokens
            self._buckets[channel_id] = (balance, now)
            return bool(allowed), 0.0 if allowed else float((tokens - balance) / self.rate)


class QueueClosedError(RuntimeError):
    """Operation submitted after shutdown."""


class StaleFencingToken(ValueError):
    """Stored fencing token is equal to or newer than the proposal."""


_B2_REGISTRY = {}
_B2_REGISTRY_LOCK = threading.RLock()
_B2_CONTEXT = threading.local()


def _b2_path(db_path):
    _boot()
    path = verify_safe_path(db_path if db_path is not None else 'state/prompt_engine.db')
    if not path.is_relative_to((ROOT / 'state').resolve()):
        raise ValueError('Database must be in vault/state')
    if _count() + RESERVE >= STOP_AT:
        raise RuntimeError('File reserve exhausted; invoke check_file_ceiling first')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _b2_schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS b2c_tokens (channel_id TEXT PRIMARY KEY, max_token INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b2c_checkpoints (channel_id TEXT PRIMARY KEY, token INTEGER NOT NULL, checkpoint BLOB NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b2c_chain_state (id INTEGER PRIMARY KEY CHECK(id=1), '
               'anchor_step INTEGER NOT NULL, anchor_hash TEXT NOT NULL, head_step INTEGER NOT NULL, head_hash TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b2c_chain_steps (step_id INTEGER PRIMARY KEY, parent_hash TEXT NOT NULL, artifact BLOB NOT NULL, step_hash TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b2c_recovery_versions (sha256 TEXT PRIMARY KEY, content TEXT NOT NULL)')
    legacy = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='b2_fenced_checkpoints'").fetchone()
    if legacy:
        for channel, token, checkpoint in db.execute('SELECT resource,token,checkpoint FROM b2_fenced_checkpoints').fetchall():
            current = db.execute('SELECT max_token FROM b2c_tokens WHERE channel_id=?', (channel,)).fetchone()
            if current is None:
                db.execute('INSERT INTO b2c_tokens VALUES (?,?)', (channel, token))
                db.execute('INSERT INTO b2c_checkpoints VALUES (?,?,?)', (channel, token, checkpoint))


def _b2_connect(path, read_only=False):
    if read_only:
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, isolation_level=None, timeout=120)
    else:
        db = sqlite3.connect(path, isolation_level=None, timeout=120)
    db.execute('PRAGMA busy_timeout=120000')
    db.execute('PRAGMA foreign_keys=ON')
    if read_only:
        db.execute('PRAGMA query_only=ON')
    else:
        if db.execute('PRAGMA journal_mode=WAL').fetchone()[0] != 'wal':
            db.close()
            raise RuntimeError('WAL required')
        db.execute('PRAGMA synchronous=FULL')
    def guard(action, first, second, database, trigger):
        forbidden = (sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_VIEW,
                     sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH)
        return sqlite3.SQLITE_DENY if action in forbidden else sqlite3.SQLITE_OK
    db.set_authorizer(guard)
    return db


class _B2Backend:
    def __init__(self, path):
        self.path, self.refs = path, 0
        self.jobs = queue.Queue(256)
        self.condition = threading.Condition()
        self.read_slots = threading.BoundedSemaphore(20)
        self.active_reads, self.closed = 0, False
        self.ready = concurrent.futures.Future()
        self.thread = threading.Thread(target=self.run, name='apccs-canonical-writer', daemon=True)
        self.thread.start()
        self.ready.result(timeout=130)

    def run(self):
        db = None
        _B2_CONTEXT.in_callback = True
        try:
            db = _b2_connect(self.path)
            db.execute('BEGIN IMMEDIATE')
            _b2_schema(db)
            db.commit()
            self.ready.set_result(True)
            while True:
                job = self.jobs.get()
                if job is None:
                    self.jobs.task_done()
                    break
                future, callback = job
                try:
                    if future.set_running_or_notify_cancel():
                        db.execute('BEGIN IMMEDIATE')
                        result = callback(db)
                        db.commit()
                        future.set_result(result)
                except BaseException as error:
                    db.rollback()
                    future.set_exception(error)
                finally:
                    self.jobs.task_done()
        except BaseException as error:
            if not self.ready.done():
                self.ready.set_exception(error)
            else:
                while True:
                    try:
                        job = self.jobs.get_nowait()
                    except queue.Empty:
                        break
                    if job is not None and not job[0].done():
                        job[0].set_exception(error)
                    self.jobs.task_done()
        finally:
            if db is not None:
                db.close()
            _B2_CONTEXT.in_callback = False

    def submit(self, callback):
        if getattr(_B2_CONTEXT, 'in_callback', False):
            raise RuntimeError('Recursive queue use from a callback is forbidden')
        with self.condition:
            if self.closed:
                raise QueueClosedError('Queue closed')
            future = concurrent.futures.Future()
            self.jobs.put((future, callback), timeout=10)
            return future

    def read(self, callback):
        if getattr(_B2_CONTEXT, 'in_callback', False):
            raise RuntimeError('Recursive reads from a callback are forbidden')
        with self.read_slots:
            with self.condition:
                if self.closed:
                    raise QueueClosedError('Queue closed')
                self.active_reads += 1
            db = None
            _B2_CONTEXT.in_callback = True
            try:
                db = _b2_connect(self.path, read_only=True)
                db.execute('BEGIN')
                result = callback(db)
                db.commit()
                return result
            finally:
                if db is not None:
                    db.close()
                _B2_CONTEXT.in_callback = False
                with self.condition:
                    self.active_reads -= 1
                    self.condition.notify_all()

    def close(self):
        with self.condition:
            self.closed = True
            while self.active_reads:
                self.condition.wait()
            self.jobs.put(None)
        self.thread.join()


class SingleWriterDBQueue:
    """One shared writer backend per database/process, and up to 20 REAL reads.

    Each read has its own read-only SQLite connection/snapshot. Writes are
    queued on one worker. Multiple handles mount the same backend. External
    processes still require SQLite locking; arbitrary external exclusive locks
    and OS failures cannot have an unconditional no-BUSY guarantee. Callbacks
    are trusted host Python, not a security sandbox.
    """
    def __init__(self, db_path=None):
        if getattr(_B2_CONTEXT, 'in_callback', False):
            raise RuntimeError('Cannot construct a queue inside a callback')
        self.path = _b2_path(db_path)
        self._closed = False
        with _B2_REGISTRY_LOCK:
            key = str(self.path)
            backend = _B2_REGISTRY.get(key)
            if backend is None:
                backend = _B2Backend(self.path)
                _B2_REGISTRY[key] = backend
            backend.refs += 1
            self._backend = backend

    def _open(self):
        if self._closed:
            raise QueueClosedError('Queue handle closed')

    def submit_transaction(self, callback):
        self._open()
        if not callable(callback):
            raise TypeError('Callable write transaction required')
        return self._backend.submit(callback)

    def transaction(self, callback):
        return self.submit_transaction(callback).result()

    def execute(self, sql, parameters=()):
        return self.transaction(lambda db: db.execute(sql, parameters).rowcount)

    def read_transaction(self, callback):
        self._open()
        if not callable(callback):
            raise TypeError('Callable read transaction required')
        return self._backend.read(callback)

    def query(self, sql, parameters=()):
        return self.read_transaction(lambda db: db.execute(sql, parameters).fetchall())

    def close(self):
        if getattr(_B2_CONTEXT, 'in_callback', False):
            raise RuntimeError('Cannot close a queue inside a callback')
        with _B2_REGISTRY_LOCK:
            if not self._closed:
                self._closed = True
                self._backend.refs -= 1
                if self._backend.refs == 0:
                    del _B2_REGISTRY[str(self.path)]
                    self._backend.close()

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *exception):
        self.close()


def _b2_channel(channel_id):
    if not isinstance(channel_id, str) or not channel_id or len(channel_id) > 200 or channel_id.startswith('__'):
        raise ValueError('Nonempty public channel identity <=200 characters required')
    return channel_id


def _b2_token(proposed_token):
    if type(proposed_token) is not int or not 1 <= proposed_token <= 9223372036854775807:
        raise ValueError('Positive signed-64-bit fencing token required')
    return proposed_token


def _b2_advance(db, channel_id, proposed_token):
    row = db.execute('SELECT max_token FROM b2c_tokens WHERE channel_id=?', (channel_id,)).fetchone()
    maximum = row[0] if row else 0
    legacy = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='b2_fenced_checkpoints'").fetchone()
    if legacy:
        old = db.execute('SELECT token FROM b2_fenced_checkpoints WHERE resource=?', (channel_id,)).fetchone()
        if old:
            maximum = max(maximum, old[0])
    if proposed_token <= maximum:
        raise StaleFencingToken('proposed_token must exceed current_max_token')
    if row:
        changed = db.execute('UPDATE b2c_tokens SET max_token=? WHERE channel_id=? AND max_token<?',
                             (proposed_token, channel_id, proposed_token)).rowcount
        if changed != 1:
            raise StaleFencingToken('Atomic fencing comparison failed')
    else:
        db.execute('INSERT INTO b2c_tokens VALUES (?,?)', (channel_id, proposed_token))
    return True


def verify_and_advance_fencing_token(db_path, channel_id, proposed_token):
    """Atomic ratchet reservation. Protected writes must recheck at storage.

    Use write_fenced_checkpoint for an atomic ratchet-plus-checkpoint write;
    a reservation followed by an unrelated unfenced write is not protected.
    """
    _b2_channel(channel_id)
    _b2_token(proposed_token)
    with SingleWriterDBQueue(db_path) as dbq:
        return dbq.transaction(lambda db: _b2_advance(db, channel_id, proposed_token))


def write_fenced_checkpoint(db_path, channel_id, proposed_token, checkpoint):
    _b2_channel(channel_id)
    _b2_token(proposed_token)
    if not isinstance(checkpoint, bytes):
        raise ValueError('Checkpoint bytes required')
    def operation(db):
        _b2_advance(db, channel_id, proposed_token)
        row = db.execute('SELECT token FROM b2c_checkpoints WHERE channel_id=?', (channel_id,)).fetchone()
        if row:
            db.execute('UPDATE b2c_checkpoints SET token=?,checkpoint=? WHERE channel_id=?', (proposed_token, checkpoint, channel_id))
        else:
            db.execute('INSERT INTO b2c_checkpoints VALUES (?,?,?)', (channel_id, proposed_token, checkpoint))
        return proposed_token
    with SingleWriterDBQueue(db_path) as dbq:
        return dbq.transaction(operation)


def _b2_digest(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None:
        raise ValueError('Lowercase SHA-256 hex required')
    return value


def mount_verified_step(db_path, step_id, artifact_bytes, expected_hash):
    """Explicitly pin trusted checkpoint bytes/hash without resetting a chain.

    step_id is the completed instruction checkpoint: Batch 1 is 5, Batch 2 is 10.
    Original Batch 2 candidate-chain tables are retained as historical records;
    this canonical API uses its own b2c namespace and explicit trusted anchor.
    """
    _b2_token(step_id)
    if step_id > 1000:
        raise ValueError('Project contains only 1,000 instruction checkpoints')
    _b2_digest(expected_hash)
    if not isinstance(artifact_bytes, bytes) or not hmac.compare_digest(sha256(artifact_bytes), expected_hash):
        raise ValueError('Trusted checkpoint hash mismatch')
    def operation(db):
        row = db.execute('SELECT anchor_step,anchor_hash FROM b2c_chain_state WHERE id=1').fetchone()
        if row:
            if row != (step_id, expected_hash):
                raise ValueError('Existing anchor differs; refusing reset')
            return 'ALREADY_MOUNTED'
        db.execute('INSERT INTO b2c_chain_state VALUES (1,?,?,?,?)', (step_id, expected_hash, step_id, expected_hash))
        return 'MOUNTED'
    with SingleWriterDBQueue(db_path) as dbq:
        return dbq.transaction(operation)


def _b2_step_hash(step_id, parent_hash, artifact_bytes):
    document = dict(step_id=step_id, parent_hash=parent_hash, artifact_sha256=sha256(artifact_bytes))
    return sha256(b'APCCS_LUMEN_V2\0' + _b2_json(document))


def _b2_verified_head(db):
    state = db.execute('SELECT anchor_step,anchor_hash,head_step,head_hash FROM b2c_chain_state WHERE id=1').fetchone()
    if state is None:
        raise ValueError('Mount a trusted previous checkpoint first')
    number, previous = state[:2]
    for step, parent, artifact, digest in db.execute('SELECT step_id,parent_hash,artifact,step_hash FROM b2c_chain_steps ORDER BY step_id'):
        if step <= number or parent != previous or _b2_step_hash(step, parent, artifact) != digest:
            raise ValueError('Stored step chain is corrupt')
        number, previous = step, digest
    if (number, previous) != state[2:]:
        raise ValueError('Stored chain head is corrupt')
    return number, previous


def _b2_publish_recovery(dbq):
    """SQLite is authoritative; reconcile RECOVER after a publication failure."""
    with _locked():
        state = dbq.read_transaction(_b2_verified_head)
        completed = state[0]
        path = ROOT / 'RECOVER.md'
        if path.is_symlink():
            raise ValueError('Recovery symlink forbidden')
        old = path.read_text(encoding='utf-8') if path.exists() else '# APCCS Recovery\nLAST_COMPLETED_INSTRUCTION: 0 of 1,000\n'
        matches = re.findall(r'^LAST_COMPLETED_INSTRUCTION:\s*(\d+) of 1,000\s*$', old, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError('Recovery checkpoint field must occur exactly once')
        if int(matches[0]) > completed:
            return str(path)
        def remember(db):
            digest = sha256(old.encode())
            row = db.execute('SELECT content FROM b2c_recovery_versions WHERE sha256=?', (digest,)).fetchone()
            if row is None:
                db.execute('INSERT INTO b2c_recovery_versions VALUES (?,?)', (digest, old))
            elif row[0] != old:
                raise ValueError('Recovery version hash collision')
        dbq.transaction(remember)
        text = re.sub(r'^LAST_COMPLETED_INSTRUCTION:.*$', f'LAST_COMPLETED_INSTRUCTION: {completed} of 1,000', old, flags=re.MULTILINE)
        fields = {'MUSE_VERIFICATION': 'PENDING for this canonical revision',
                  'ACTIVE_CANARY': 'T = Y -> lighthouse', 'Canary Receipt': 'T = Y -> lighthouse',
                  'BATCH_2_STARTED': 'true', 'BATCH_2_LOCAL_TESTS': 'GREEN; Muse audit pending',
                  'NEXT_BATCH': 'HELD; await Muse acceptance and explicit dispatch',
                  'BATCH_3_STARTED': 'false', 'BATCH2_STEP_HASH': state[1]}
        for key, value in fields.items():
            if re.search('^' + key + ':', text, re.MULTILINE):
                text = re.sub('^' + key + ':.*$', key + ': ' + value, text, flags=re.MULTILINE)
            else:
                text += '\n' + key + ': ' + value + '\n'
        temporary = ROOT / ('.recover_' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('x', encoding='utf-8') as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory = os.open(ROOT, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)
        return str(path)


def refresh_recovery_from_db(db_path):
    with SingleWriterDBQueue(db_path) as dbq:
        return _b2_publish_recovery(dbq)


def compute_and_verify_step_hash(db_path, step_id, parent_hash, artifact_bytes):
    """Verify/extend the chain atomically, then publish RECOVER (step 10 -> 10/1000).

    If publication fails after commit, refresh_recovery_from_db repairs it.
    Canonical chain uses a versioned hash domain; old chains are not modified.
    """
    _b2_token(step_id)
    if step_id > 1000:
        raise ValueError('Project contains only 1,000 instruction checkpoints')
    _b2_digest(parent_hash)
    if not isinstance(artifact_bytes, bytes):
        raise ValueError('Artifact bytes required')
    digest = _b2_step_hash(step_id, parent_hash, artifact_bytes)
    def operation(db):
        number, previous = _b2_verified_head(db)
        if step_id <= number or not hmac.compare_digest(parent_hash, previous):
            raise ValueError('Step must extend the previous verified checkpoint')
        _b2_advance(db, '__lumen__', step_id)
        db.execute('INSERT INTO b2c_chain_steps VALUES (?,?,?,?)', (step_id, parent_hash, artifact_bytes, digest))
        changed = db.execute('UPDATE b2c_chain_state SET head_step=?,head_hash=? WHERE id=1 AND head_step=? AND head_hash=?',
                            (step_id, digest, number, previous)).rowcount
        if changed != 1:
            raise ValueError('Atomic chain comparison failed')
        return digest
    with SingleWriterDBQueue(db_path) as dbq:
        result = dbq.transaction(operation)
        _b2_publish_recovery(dbq)
        return result


# Batch 3 additions. All earlier canonical source bytes above are unchanged.
import ast
import io
import tokenize
from collections import Counter


class AuditResult(dict):
    """JSON-compatible gate result with meaningful Boolean rejection semantics."""
    def __bool__(self):
        return bool(self['passed'])


class AuditRejected(ValueError):
    """Quarantine or release rejected without publishing the candidate."""


_B3_UNKNOWN = object()


def _b3_result(gate, findings, **details):
    return AuditResult(gate=gate, passed=not findings, status='GREEN' if not findings else 'RED', findings=findings, **details)


def _b3_source(source):
    if isinstance(source, Path):
        path = source.resolve()
        if not path.is_relative_to(WORKSPACE.resolve()):
            raise ValueError('Audit path outside approved workspace')
        raw = path.read_bytes()
    elif isinstance(source, bytes):
        raw = source
    elif isinstance(source, str):
        if '\n' not in source and len(source) <= 240 and Path(source).is_file():
            return _b3_source(Path(source))
        raw = source.encode('utf-8')
    else:
        raise TypeError('Audit source must be bytes, text, or a workspace Path')
    if len(raw) > 4 * 1024 * 1024 or b'\0' in raw:
        raise ValueError('Binary/oversized input requires independent review')
    return raw.decode('utf-8')


def _b3_value(node, values=None, depth=0):
    """Bounded literal folding only; never runs candidate expressions."""
    values = values or {}
    if depth > 12:
        return _B3_UNKNOWN
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return values.get(node.id, _B3_UNKNOWN)
    if isinstance(node, (ast.List, ast.Tuple)):
        items = [_b3_value(v, values, depth + 1) for v in node.elts]
        return items if all(v is not _B3_UNKNOWN for v in items) else _B3_UNKNOWN
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _b3_value(node.left, values, depth + 1), _b3_value(node.right, values, depth + 1)
        if type(left) is type(right) and isinstance(left, (str, bytes)) and len(left) + len(right) <= 65536:
            return left + right
    if isinstance(node, ast.JoinedStr):
        parts = []
        for item in node.values:
            value = _b3_value(item.value if isinstance(item, ast.FormattedValue) else item, values, depth + 1)
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                return _B3_UNKNOWN
            parts.append(str(value))
        if sum(map(len, parts)) <= 65536:
            return ''.join(parts)
    return _B3_UNKNOWN


def _b3_bindings(tree):
    values, names = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                names[item.asname or item.name.split('.')[0]] = item.name
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                names[item.asname or item.name] = (node.module or '') + '.' + item.name
    for _ in range(3):
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value_node = node.value
                value = _b3_value(value_node, values)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        if value is not _B3_UNKNOWN:
                            values[target.id] = value
                        qualified = _b3_name(value_node, names, values)
                        if qualified:
                            names[target.id] = qualified
    return values, names


def _b3_name(node, names=None, values=None, depth=0):
    names, values = names or {}, values or {}
    if depth > 12 or node is None:
        return ''
    if isinstance(node, ast.Name):
        return names.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return _b3_name(node.value, names, values, depth + 1) + '.' + node.attr
    if isinstance(node, ast.Subscript):
        key = _b3_value(node.slice, values)
        if isinstance(key, str):
            return _b3_name(node.value, names, values, depth + 1) + '.' + key
    if isinstance(node, ast.Call):
        name = _b3_name(node.func, names, values, depth + 1)
        if name == 'getattr' and len(node.args) >= 2:
            key = _b3_value(node.args[1], values)
            if isinstance(key, str):
                return _b3_name(node.args[0], names, values, depth + 1) + '.' + key
        if name in ('globals', 'locals', 'vars'):
            return name
    return ''


def scan_for_fake_padding(source):
    """Reject long hash stuffing, repeated identical comments, and filler math.

    These are explicit conservative syntactic heuristics, not a proof that
    arbitrary prose/code is semantically useful. Normal Markdown headings,
    operator multiplication and legitimate hash-domain strings are allowed.
    """
    findings = []
    try:
        text = _b3_source(source)
    except (ValueError, UnicodeError) as error:
        return _b3_result(1, [dict(code='UNSCANNABLE_INPUT', detail=str(error))])
    for number, line in enumerate(text.splitlines(), 1):
        if re.search(r'#{32,}', line):
            findings.append(dict(code='HASH_STUFFING', line=number))
        if re.search(r'X{128,}', line):
            findings.append(dict(code='EXPANDED_X_FILLER', line=number))
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        try:
            comments = [t for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type == tokenize.COMMENT]
            counts = Counter(t.string.strip() for t in comments)
            for token in comments:
                if counts[token.string.strip()] >= 8:
                    findings.append(dict(code='REPEATED_COMMENT_STUFFING', line=token.start[0]))
                    break
        except (tokenize.TokenError, IndentationError, SyntaxError):
            findings.append(dict(code='UNSCANNABLE_COMMENT_TOKENS'))
    else:
        comment_lines = [(number, line.strip()) for number, line in enumerate(text.splitlines(), 1) if line.lstrip().startswith('#')]
        counts = Counter(line for number, line in comment_lines)
        for number, line in comment_lines:
            if counts[line] >= 8:
                findings.append(dict(code='REPEATED_COMMENT_STUFFING', line=number))
                break
    if tree is not None:
        values, _ = _b3_bindings(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                left, right = _b3_value(node.left, values), _b3_value(node.right, values)
                for filler, amount in ((left, right), (right, left)):
                    if isinstance(filler, (str, bytes)) and filler and set(filler) in ({'X'}, {88}) and (amount is _B3_UNKNOWN or type(amount) is int and amount > 0):
                        findings.append(dict(code='X_MULTIPLICATION_FILLER', line=node.lineno))
                    if isinstance(filler, (str, bytes)) and filler and (set(filler).issubset({'#', ' ', '\n', '\r', '\t'}) and '#' in filler if isinstance(filler, str) else set(filler).issubset({35, 32, 10, 13, 9}) and 35 in filler) and (amount is _B3_UNKNOWN or type(amount) is int and amount >= 32):
                        findings.append(dict(code='HASH_MULTIPLICATION_FILLER', line=node.lineno))
    return _b3_result(1, findings)


def verify_ast_structure(source):
    """Parse without execution; reject dynamic evaluation and empty code stubs.

    Documented Exception subclasses are functional marker types and are not
    treated as empty implementations. Ordinary empty classes are rejected.
    """
    try:
        text = _b3_source(source)
        tree = ast.parse(text)
    except (ValueError, UnicodeError, SyntaxError) as error:
        return _b3_result(2, [dict(code='AST_PARSE_REJECTED', detail=str(error))])
    findings = []
    module_body = tree.body[1:] if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str) else tree.body
    if not module_body or all(isinstance(n, ast.Pass) or isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and n.value.value is Ellipsis for n in module_body):
        findings.append(dict(code='EMPTY_MODULE_STUB'))
    values, names = _b3_bindings(tree)
    forbidden = {'eval', 'exec', 'compile', '__import__'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _b3_name(node.func, names, values)
            if name.split('.')[-1] in forbidden:
                findings.append(dict(code='DYNAMIC_EXECUTION_ENTRY', line=node.lineno))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body[1:] if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str) else node.body
            marker = isinstance(node, ast.ClassDef) and bool(ast.get_docstring(node)) and any(_b3_name(base, names, values).split('.')[-1].endswith(('Error', 'Exception')) for base in node.bases)
            def empty(statement):
                return (isinstance(statement, ast.Pass) or
                        isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and statement.value.value is Ellipsis or
                        isinstance(statement, ast.Return) and (statement.value is None or isinstance(statement.value, ast.Constant) and statement.value.value is None))
            if not marker and (not body or all(empty(statement) for statement in body)):
                findings.append(dict(code='EMPTY_CODE_STUB', line=node.lineno, symbol=node.name))
            if len(body) == 1 and isinstance(body[0], ast.Raise):
                raised = body[0].exc
                if _b3_name(raised.func if isinstance(raised, ast.Call) else raised, names, values).endswith('NotImplementedError'):
                    findings.append(dict(code='UNIMPLEMENTED_STUB', line=node.lineno, symbol=node.name))
    return _b3_result(2, findings)


def _b3_symbols(tree):
    counts = Counter()
    def walk(node, prefix=''):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                counts[name] += 1
                walk(child, name + '.')
            else:
                walk(child, prefix)
    walk(tree)
    return counts


def check_symbol_regression(current_source, prior_source):
    """Compare qualified functions/classes/methods; also reject redefinitions."""
    try:
        current = _b3_symbols(ast.parse(_b3_source(current_source)))
        prior = _b3_symbols(ast.parse(_b3_source(prior_source)))
    except (ValueError, UnicodeError, SyntaxError) as error:
        return _b3_result(3, [dict(code='SYMBOL_PARSE_REJECTED', detail=str(error))])
    removed = sorted(set(prior) - set(current))
    duplicates = sorted(name for name, count in current.items() if count > 1)
    findings = [dict(code='SYMBOL_REMOVED', symbol=name) for name in removed]
    findings.extend(dict(code='SYMBOL_REDEFINED', symbol=name) for name in duplicates)
    return _b3_result(3, findings, prior_symbols=len(prior), current_symbols=len(current), removed=removed, duplicates=duplicates)


def scan_destructive_ops(source):
    """Conservative known-pattern scan; findings never echo credential values.

    Literal/constant-concatenated SQL and common destructive OS entry points
    are checked. This is not general runtime taint analysis or a code sandbox.
    """
    try:
        text = _b3_source(source)
    except (ValueError, UnicodeError) as error:
        return _b3_result(4, [dict(code='UNSCANNABLE_INPUT', detail=str(error))])
    findings = []
    patterns = [
        (r'(?i)\bdrop\s+table\b', 'DESTRUCTIVE_SQL'),
        (r'(?i)\btruncate\s+table\b', 'DESTRUCTIVE_SQL'),
        (r'(?i)\bdd\b[^\n]{0,180}\bof\s*=\s*/dev/(?:sd|hd|vd|nvme|mmc|disk)', 'RAW_DEVICE_WRITE'),
        (r'(?i)(?:^|[\s\x22\x27])(?:mkfs(?:\.[a-z0-9]+)?|wipefs|shred)\s+[^\n]{0,100}/dev/', 'RAW_DEVICE_WIPE'),
        (r'(?i)\brm\s+(?=[^\n]*(?:-[a-z]*r|--recursive))(?=[^\n]*\s/)[^\n]+', 'ABSOLUTE_RECURSIVE_DELETE'),
        (r'(?i)\bformat\s+[a-z]:', 'RAW_VOLUME_FORMAT'),
        (r'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]+', 'CREDENTIAL_SK'),
        (r'(?<![A-Z0-9])AKIA[A-Z0-9]+', 'CREDENTIAL_AKIA'),
        (r'(?<![A-Za-z0-9])ghp_[A-Za-z0-9]+', 'CREDENTIAL_GHP')]
    def inspect(value, line=0):
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')
        if not isinstance(value, str):
            return
        for pattern, code in patterns:
            if re.search(pattern, value):
                findings.append(dict(code=code, line=line, detail='Matched forbidden pattern; value redacted'))
    inspect(text)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _b3_result(4, findings)
    values, names = _b3_bindings(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Constant, ast.BinOp, ast.JoinedStr)):
            inspect(_b3_value(node, values), getattr(node, 'lineno', 0))
        if isinstance(node, ast.Call):
            name = _b3_name(node.func, names, values)
            if name in ('open', 'io.open', 'os.open', 'Path', 'pathlib.Path') and node.args:
                device = _b3_value(node.args[0], values)
                if isinstance(device, str) and device.startswith('/dev/'):
                    findings.append(dict(code='RAW_DEVICE_ACCESS', line=node.lineno))
            if name in ('os.system', 'os.popen', 'shutil.rmtree'):
                findings.append(dict(code='UNSAFE_OS_ENTRY', line=node.lineno))
            if name.startswith('subprocess.'):
                shell = any(k.arg == 'shell' and _b3_value(k.value, values) is not False for k in node.keywords)
                if shell:
                    findings.append(dict(code='SHELL_EXECUTION', line=node.lineno))
                if node.args:
                    command = _b3_value(node.args[0], values)
                    if isinstance(command, list):
                        inspect(' '.join(str(v) for v in command), node.lineno)
                        if command and str(command[0]).split('/')[-1] in ('dd', 'mkfs', 'wipefs', 'shred', 'diskpart'):
                            findings.append(dict(code='RAW_DISK_TOOL', line=node.lineno))
                    elif isinstance(command, str):
                        inspect(command, node.lineno)
    return _b3_result(4, findings)


def _b3_names(files):
    if not isinstance(files, dict) or not files or len(files) > 64:
        raise ValueError('Bundle requires 1..64 named files')
    total = 0
    for name, data in files.items():
        if not isinstance(name, str) or not name or '\\' in name or Path(name).is_absolute() or '..' in Path(name).parts or ':' in name or '\0' in name or Path(name).as_posix() != name:
            raise ValueError('Unsafe bundle member')
        if re.search(r'(?<![A-Za-z0-9])(?:sk-|AKIA|ghp_)[A-Za-z0-9_-]+', name):
            raise ValueError('Credential-shaped filename rejected without echoing it')
        if not isinstance(data, bytes) or len(data) > 4 * 1024 * 1024:
            raise ValueError('File bytes and per-file size limit required')
        if Path(name).suffix.lower() in ('.pyc', '.pyo', '.pth', '.so', '.dll', '.exe', '.sh', '.bat', '.cmd', '.ps1'):
            raise ValueError('Additional executable payloads are not canonical bundle members')
        total += len(data)
    if total > 16 * 1024 * 1024:
        raise ValueError('Bundle exceeds total size limit')


def _b3_zip_files(data):
    import io as memory_io
    with zipfile.ZipFile(memory_io.BytesIO(data)) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or len(names) > 64 or sum(i.file_size for i in bundle.infolist()) > 16 * 1024 * 1024:
            raise AuditRejected('Unsafe ZIP directory or size')
        files = {name: bundle.read(name) for name in names}
    _b3_names(files)
    return files


class StagingInbox:
    """Quarantine outside ROOT. Only an authenticated all-five-gate promotion
    may publish ONE derived Master ZIP. No OS-wide sandbox claim is made:
    the host must route AI output here and deny direct filesystem bypasses.

    Gate 5 has no default definition. A trusted host must supply its named
    policy/verifier and keep release_key outside AI control. Production use
    without either stays HELD; temporary test-policy approvals are fixtures.
    """
    def __init__(self, release_key=None, staging_root=None):
        workspace = WORKSPACE.resolve()
        path = Path(staging_root) if staging_root is not None else workspace / '01_STAGING_INBOX'
        if path.is_symlink():
            raise ValueError('Staging symlink forbidden')
        self.root = path.resolve()
        if not self.root.is_relative_to(workspace) or self.root.is_relative_to(ROOT.resolve()):
            raise ValueError('Quarantine must be inside workspace but outside Master Vault')
        if release_key is not None and (not isinstance(release_key, bytes) or len(release_key) < 32):
            raise ValueError('Host release key must contain at least 32 bytes')
        self.key = release_key
        if _count() + RESERVE >= STOP_AT:
            raise RuntimeError('Workspace file reserve exhausted')
        self.root.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS b3_cases ('
                       'case_id TEXT PRIMARY KEY, build_id TEXT NOT NULL, bundle_hash TEXT NOT NULL, '
                       'baseline_hash TEXT NOT NULL, baseline BLOB NOT NULL, destination TEXT NOT NULL, '
                       'status TEXT NOT NULL, audit_json TEXT, receipt TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS b3_authority (id INTEGER PRIMARY KEY CHECK(id=1), key_sha256 TEXT NOT NULL)')
            if self.key is not None:
                fingerprint = sha256(self.key)
                authority = db.execute('SELECT key_sha256 FROM b3_authority WHERE id=1').fetchone()
                if authority is not None and not hmac.compare_digest(authority[0], fingerprint):
                    raise AuditRejected('Existing host authority differs; refusing replacement')
                if authority is None:
                    with db:
                        db.execute('INSERT INTO b3_authority VALUES (1,?)', (fingerprint,))


    def _connect(self):
        path = self.root / 'quarantine.db'
        if path.is_symlink():
            raise ValueError('Quarantine database symlink forbidden')
        db = sqlite3.connect(path, timeout=120)
        db.execute('PRAGMA busy_timeout=120000')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA foreign_keys=ON')
        return contextlib.closing(db)

    @contextlib.contextmanager
    def _lock(self):
        descriptor = os.open(self.root / 'quarantine.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _case(self, db, case_id):
        if not isinstance(case_id, str) or re.fullmatch(r'[0-9a-f]{32}', case_id) is None:
            raise ValueError('Invalid case identity')
        row = db.execute('SELECT build_id,bundle_hash,baseline_hash,baseline,destination,status,audit_json,receipt FROM b3_cases WHERE case_id=?', (case_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown quarantine case')
        return row

    def stage(self, files, baseline_archive, master_path=None, build_id='BATCH3_CANDIDATE'):
        _b3_names(files)
        if not isinstance(baseline_archive, bytes):
            raise ValueError('Trusted prior Master ZIP bytes required')
        baseline = _b3_zip_files(baseline_archive)
        if {n for n in files if n.endswith('.py')} != {'code/apccs_core.py', 'code/test_apccs_core.py'}:
            raise AuditRejected('Exactly one canonical core and one test file required')
        destination = verify_safe_path(master_path if master_path is not None else 'exports/APCCS_MASTER_BUILD.zip')
        if not destination.is_relative_to((ROOT / 'exports').resolve()) or destination.name != ARCHIVE_NAME:
            raise ValueError('Only a derived Master ZIP destination is supported')
        if not isinstance(build_id, str) or not build_id:
            raise ValueError('Build identity required')
        baseline_hash = sha256(baseline_archive)
        files = dict(files)
        history = 'history/previous_build_' + baseline_hash + '.zip'
        if history in files and files[history] != baseline_archive:
            raise AuditRejected('Prior-build history differs')
        files[history] = baseline_archive
        for name, data in baseline.items():
            protected = name.startswith(('state/', 'engines/', 'conversations/', 'history/')) or name == LOG_NAME
            if protected and files.get(name) != data:
                raise AuditRejected('Existing protected member must remain byte-identical')
        _b3_names(files)
        case_id = uuid.uuid4().hex
        target = self.root / (case_id + '.zip')
        with self._lock(), self._connect() as db:
            if _count() + RESERVE >= STOP_AT:
                raise RuntimeError('Workspace file reserve exhausted')
            with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as bundle:
                for name in sorted(files):
                    bundle.writestr(name, files[name])
            try:
                digest = sha256(target.read_bytes())
                with db:
                    db.execute('INSERT INTO b3_cases VALUES (?,?,?,?,?,?,?,?,?)',
                               (case_id, build_id, digest, baseline_hash, baseline_archive, str(destination), 'STAGED', None, None))
            except BaseException:
                target.unlink(missing_ok=True)
                raise
        return dict(case_id=case_id, bundle_path=str(target), bundle_sha256=digest, status='STAGED')

    def _evaluate(self, row, case_id, gate5_verifier=None, gate5_policy_id=None):
        path = self.root / (case_id + '.zip')
        if path.is_symlink() or sha256(path.read_bytes()) != row[1] or sha256(row[3]) != row[2]:
            raise AuditRejected('Candidate or baseline bytes changed')
        files, baseline = _b3_zip_files(path.read_bytes()), _b3_zip_files(row[3])
        findings = {1: [], 2: [], 3: [], 4: []}
        for name, data in files.items():
            unchanged = name in baseline and baseline[name] == data
            trusted_history = name == 'history/previous_build_' + row[2] + '.zip' and data == row[3]
            if unchanged or trusted_history:
                continue
            if name.startswith(('state/', 'engines/', 'conversations/', 'history/')) or name == LOG_NAME:
                findings[4].append(dict(file=name, code='PROTECTED_RECORD_CHANGED'))
                continue
            for gate, scanner in ((1, scan_for_fake_padding), (4, scan_destructive_ops)):
                result = scanner(data)
                findings[gate].extend(dict(file=name, **issue) for issue in result['findings'])
            if name.endswith('.py'):
                result = verify_ast_structure(data)
                findings[2].extend(dict(file=name, **issue) for issue in result['findings'])
                if name in baseline:
                    result = check_symbol_regression(data, baseline[name])
                    findings[3].extend(dict(file=name, **issue) for issue in result['findings'])
        for name in baseline:
            if name.endswith('.py') and name not in files:
                findings[3].append(dict(file=name, code='SOURCE_FILE_REMOVED'))
        gates = {str(g): dict(passed=not issues, status='GREEN' if not issues else 'RED', findings=issues) for g, issues in findings.items()}
        context = dict(case_id=case_id, build_id=row[0], bundle_sha256=row[1], baseline_sha256=row[2], destination=row[4])
        if gate5_verifier is None or not gate5_policy_id:
            gates['5'] = dict(passed=False, status='GRAY', reason='GATE_5_NOT_DEFINED')
        elif re.fullmatch(r'[A-Za-z0-9._-]{1,128}', str(gate5_policy_id)) is None:
            raise ValueError('Nonsecret Gate 5 policy identifier required')
        elif not callable(gate5_verifier):
            raise TypeError('Trusted Gate 5 verifier must be callable')
        else:
            decision = gate5_verifier(dict(context))
            if type(decision) is not bool:
                raise ValueError('Gate 5 verifier must return a Boolean')
            gates['5'] = dict(passed=decision, status='GREEN' if decision else 'RED', policy_id=str(gate5_policy_id))
        context['gates'] = gates
        context['release_ready'] = all(g['passed'] for g in gates.values()) and self.key is not None
        context['host_key_configured'] = self.key is not None
        return context

    def audit(self, case_id, gate5_verifier=None, gate5_policy_id=None):
        with self._lock(), self._connect() as db:
            row = self._case(db, case_id)
            if row[5] == 'PROMOTED':
                raise AuditRejected('Already promoted case is immutable')
            result = self._evaluate(row, case_id, gate5_verifier, gate5_policy_id)
            raw = _b2_json(result)
            receipt = hmac.new(self.key, raw, hashlib.sha256).hexdigest() if result['release_ready'] else None
            with db:
                db.execute('UPDATE b3_cases SET status=?,audit_json=?,receipt=? WHERE case_id=?',
                           ('AUDITED' if result['release_ready'] else 'HELD', raw.decode(), receipt, case_id))
            return result

    def _finish(self, db, case_id):
        with db:
            db.execute('UPDATE b3_cases SET status=? WHERE case_id=?', ('PROMOTED', case_id))

    def promote(self, case_id):
        with self._lock(), self._connect() as db:
            row = self._case(db, case_id)
            if self.key is None or row[6] is None or row[7] is None:
                raise AuditRejected('Five passing gates and host authentication required')
            raw = row[6].encode()
            expected = hmac.new(self.key, raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(row[7], expected):
                raise AuditRejected('Audit receipt authentication failed')
            receipt = json.loads(raw)
            if not receipt.get('release_ready') or set(receipt.get('gates', {})) != {'1', '2', '3', '4', '5'} or not all(g.get('passed') is True for g in receipt['gates'].values()):
                raise AuditRejected('Every gate must pass')
            identity = (receipt.get('case_id'), receipt.get('bundle_sha256'), receipt.get('baseline_sha256'), receipt.get('destination'))
            if identity != (case_id, row[1], row[2], row[4]):
                raise AuditRejected('Audit receipt identity mismatch')
            fresh = self._evaluate(row, case_id)
            if not all(fresh['gates'][str(g)]['passed'] for g in range(1, 5)):
                raise AuditRejected('Static gates changed since audit')
            destination = verify_safe_path(row[4])
            if destination.name != ARCHIVE_NAME or not destination.is_relative_to((ROOT / 'exports').resolve()):
                raise AuditRejected('Unsafe Master destination')
            current = sha256(destination.read_bytes()) if destination.exists() else None
            if row[5] in ('PROMOTED', 'PREPARED') and current == row[1]:
                self._finish(db, case_id)
                return dict(status='ALREADY_PROMOTED' if row[5] == 'PROMOTED' else 'RECOVERED_PROMOTION', destination=str(destination))
            if row[5] not in ('AUDITED', 'PREPARED') or current != row[2]:
                raise AuditRejected('Master advanced or baseline differs; re-audit required')
            with db:
                db.execute('UPDATE b3_cases SET status=? WHERE case_id=?', ('PREPARED', case_id))
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.parent / ('.quarantine_' + case_id + '.tmp')
            if temporary.is_symlink():
                raise AuditRejected('Promotion temporary symlink forbidden')
            try:
                if temporary.exists() and sha256(temporary.read_bytes()) != row[1]:
                    temporary.unlink()
                if not temporary.exists():
                    with temporary.open('xb') as out:
                        out.write((self.root / (case_id + '.zip')).read_bytes())
                        out.flush()
                        os.fsync(out.fileno())
                os.replace(temporary, destination)
                descriptor = os.open(destination.parent, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                self._finish(db, case_id)
            finally:
                temporary.unlink(missing_ok=True)
            return dict(status='PROMOTED', destination=str(destination))


B4_AUTHORIZATION = 'APCCS-CORR-20261028-013'
B4_PREFIX_BYTES = 69306
B4_PREFIX_HASH = '5401dfdd4c84ad9aea3792f65751997c36ffde54ced7a557047cd1e2d01b551c'


def _b4_control():
    path = WORKSPACE / '01_STAGING_INBOX' / 'release_control'
    if path.is_symlink():
        raise AuditRejected('Control symlink forbidden')
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextlib.contextmanager
def _b4_serial():
    path = _b4_control() / 'release.lock'
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _b4_write(path, data):
    path = Path(path)
    if path.is_symlink():
        raise AuditRejected('Publication symlink forbidden')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / ('.publish_' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _b4_not_halted():
    if (_b4_control() / 'ANDON.json').exists():
        raise AuditRejected('ANDON active: promotion and staging locked')


def trigger_andon_cord(reason):
    """Persistent, process-shared STOP. No automatic reset is provided."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('Nonempty failure reason required')
    with _b4_serial():
        path = _b4_control() / 'ANDON.json'
        if not path.exists():
            event = dict(status='RED', halted=True, staging_locked=True,
                         reason_sha256=sha256(reason.encode()),
                         timestamp=dt.datetime.now(ZoneInfo('America/Vancouver')).isoformat())
            _b4_write(path, _b2_json(event))
        return json.loads(path.read_text())


def require_owner_approval(chg_id, summary, owner_decision=None):
    """Exact YES is a host-supplied decision, never inferred from candidate text."""
    if not isinstance(chg_id, str) or re.fullmatch(r'CHG-[0-9]{4,}', chg_id) is None:
        raise ValueError('CHG identifier required')
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError('Nonempty change summary required')
    approved = type(owner_decision) is str and owner_decision == 'YES'
    return dict(chg_id=chg_id, summary_sha256=sha256(summary.encode()),
                approved=approved, status='GREEN' if approved else 'GRAY')


def _b4_candidate_files(candidate_bytes):
    if isinstance(candidate_bytes, bytes):
        files = _b3_zip_files(candidate_bytes)
    elif isinstance(candidate_bytes, dict):
        files = dict(candidate_bytes)
        _b3_names(files)
    else:
        raise TypeError('Candidate must be ZIP bytes or a named bytes mapping')
    required = {'code/apccs_core.py', 'code/test_apccs_core.py'}
    if not required.issubset(files):
        raise AuditRejected('Both canonical source and tests required')
    return files


def _b4_quotes(db_path, quotes):
    if quotes is None:
        return 0
    if not isinstance(quotes, (list, tuple)) or any(not isinstance(q, str) or not q for q in quotes):
        raise AuditRejected('Quotes must be nonempty exact strings')
    if not quotes:
        return 0
    if db_path is None:
        raise AuditRejected('Citation database required')
    path = Path(db_path).resolve(strict=True)
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=120)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        found = set()
        for (name,) in tables:
            escaped = '"' + name.replace('"', '""') + '"'
            for row in db.execute('SELECT * FROM ' + escaped):
                for cell in row:
                    if isinstance(cell, str):
                        found.update(q for q in quotes if q in cell)
        if any(q not in found for q in quotes):
            raise AuditRejected('At least one exact citation is absent')
        return len(quotes)
    finally:
        db.close()


def generate_audit_receipt(candidate_bytes, test_report_dict, sqlite_db_path=None,
                           cited_quotes=None, host_release_verifier=None):
    """Gate 5 recomputes exact file identities and calls an external host authority.

    Host callback receives a copy of the bound context and must return literal
    True. Candidate-supplied callables are untrusted: only the external host
    controller may configure this dependency. No default approval exists.
    """
    try:
        files = _b4_candidate_files(candidate_bytes)
        report = json.loads(json.dumps(test_report_dict, allow_nan=False))
        if not isinstance(report, dict) or report.get('failed_assertions') != [] or report.get('all_unit_tests_passed') is not True:
            raise AuditRejected('Passing exact test report required')
        identities = {}
        for name, hash_key in (('code/apccs_core.py', 'module_sha256'), ('code/test_apccs_core.py', 'test_sha256')):
            identity = dict(sha256=sha256(files[name]), size=len(files[name]))
            if report.get(hash_key) != identity['sha256'] or report.get('files', {}).get(name) != identity:
                raise AuditRejected('Test report hash or byte count mismatch')
            identities[name] = identity
        if 'audit/pass_tests.json' in files:
            embedded = json.loads(files['audit/pass_tests.json'])
            if embedded != report:
                raise AuditRejected('Embedded and supplied test reports differ')
        quote_count = _b4_quotes(sqlite_db_path, cited_quotes)
        context = dict(authorization=B4_AUTHORIZATION, files=identities,
                       report_sha256=sha256(_b2_json(report)),
                       quotes_sha256=sha256(_b2_json(cited_quotes or [])),
                       quote_count=quote_count)
        context['candidate_sha256'] = sha256(_b2_json({n: dict(size=len(b), sha256=sha256(b)) for n, b in sorted(files.items())}))
        if not callable(host_release_verifier) or host_release_verifier(json.loads(json.dumps(context))) is not True:
            raise AuditRejected('External host release authorization required')
        return dict(passed=True, status='GREEN', gate=5, **context)
    except Exception:
        trigger_andon_cord('Gate 5 receipt failed')
        raise


def _b4_checkpoint_id(cp_id):
    if not isinstance(cp_id, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,80}', cp_id) is None:
        raise ValueError('Safe checkpoint identifier required')
    return cp_id


def _b4_master():
    return verify_safe_path('exports/APCCS_MASTER_BUILD.zip')


def _b4_snapshot(cp_id):
    _b4_checkpoint_id(cp_id)
    destination = _b4_control() / ('snapshot_' + cp_id + '.json')
    master = _b4_master()
    if not master.is_file() or master.is_symlink():
        raise AuditRejected('Existing regular Master required for snapshot')
    data = master.read_bytes()
    digest = sha256(data)
    blob = _b4_control() / ('rollback_' + digest + '.zip')
    if blob.exists():
        if blob.is_symlink() or sha256(blob.read_bytes()) != digest:
            raise AuditRejected('Rollback blob changed')
    else:
        _b4_write(blob, data)
    record = dict(cp_id=cp_id, destination=str(master), sha256=digest, size=len(data), blob=blob.name)
    if destination.exists():
        existing = json.loads(destination.read_text())
        if existing != record:
            raise AuditRejected('Checkpoint identity already bound to different bytes')
    else:
        _b4_write(destination, _b2_json(record))
    return record


def create_rollback_snapshot(cp_id):
    """Capture the authoritative Master ZIP, byte for byte, outside the ZIP."""
    try:
        with _b4_serial():
            return _b4_snapshot(cp_id)
    except Exception:
        trigger_andon_cord('Snapshot failed')
        raise


def reverse_to_checkpoint(cp_id):
    """Owner-invoked reversal. Capture current Master before atomic restoration.

    Restore is permitted during ANDON for recovery; it does not clear STOP.
    The authority scope is the Master ZIP, not unrelated live database files.
    """
    try:
        with _b4_serial():
            _b4_checkpoint_id(cp_id)
            record = json.loads((_b4_control() / ('snapshot_' + cp_id + '.json')).read_text())
            if record['cp_id'] != cp_id or record['destination'] != str(_b4_master()):
                raise AuditRejected('Snapshot destination binding differs')
            blob = _b4_control() / record['blob']
            if blob.parent != _b4_control() or blob.is_symlink():
                raise AuditRejected('Invalid rollback blob')
            data = blob.read_bytes()
            if sha256(data) != record['sha256'] or len(data) != record['size']:
                raise AuditRejected('Rollback snapshot integrity failed')
            master = _b4_master()
            if master.read_bytes() == data:
                return dict(status='ALREADY_RESTORED', cp_id=cp_id, sha256=record['sha256'])
            _b4_snapshot('before_reverse_' + sha256(master.read_bytes())[:32])
            _b4_write(master, data)
            return dict(status='RESTORED', cp_id=cp_id, sha256=record['sha256'])
    except Exception:
        trigger_andon_cord('Rollback failed')
        raise


class ReleaseStagingInbox(StagingInbox):
    """Batch 4 host entrypoint. Legacy APIs stay byte-identical for compatibility.

    The host must expose this entrypoint, not legacy writers, to AI channels.
    All new staging/publication holds the shared ANDON lock. Previous archives
    are preserved externally, never recursively included in the new Master.
    """
    def stage(self, files, baseline_archive, master_path=None, build_id='BATCH4_CANDIDATE'):
        try:
            with _b4_serial():
                _b4_not_halted()
                _b3_names(files)
                baseline = _b3_zip_files(baseline_archive)
                if any(n.lower().endswith('.zip') for n in files):
                    raise AuditRejected('Nested archives forbidden')
                if {n for n in files if n.endswith('.py')} != {'code/apccs_core.py', 'code/test_apccs_core.py'}:
                    raise AuditRejected('Only two canonical Python files required')
                for name, value in baseline.items():
                    if name.lower().endswith('.zip'):
                        continue
                    if (name.startswith(('state/', 'engines/', 'conversations/', 'history/')) or name == LOG_NAME) and files.get(name) != value:
                        raise AuditRejected('Existing protected records changed')
                destination = verify_safe_path(master_path or 'exports/APCCS_MASTER_BUILD.zip')
                if destination != _b4_master():
                    raise AuditRejected('Only canonical Master destination supported')
                case_id = uuid.uuid4().hex
                target = self.root / (case_id + '.zip')
                with self._lock(), self._connect() as db:
                    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
                        for name, data in sorted(files.items()):
                            archive.writestr(name, data)
                    digest = sha256(target.read_bytes())
                    with db:
                        db.execute('INSERT INTO b3_cases VALUES (?,?,?,?,?,?,?,?,?)',
                                   (case_id, build_id, digest, sha256(baseline_archive), baseline_archive, str(destination), 'STAGED', None, None))
                return dict(case_id=case_id, bundle_path=str(target), bundle_sha256=digest, status='STAGED')
        except Exception:
            trigger_andon_cord('Staging failed')
            raise

    def _evaluate(self, row, case_id, gate5_verifier=None, gate5_policy_id=None):
        result = super()._evaluate(row, case_id)
        if gate5_verifier is not None:
            path = self.root / (case_id + '.zip')
            files = _b3_zip_files(path.read_bytes())
            receipt = gate5_verifier(files)
            if not isinstance(receipt, dict) or receipt.get('passed') is not True or receipt.get('gate') != 5:
                raise AuditRejected('Concrete Gate 5 receipt required')
            report = json.loads(files['audit/pass_tests.json'])
            expected_files = {name: dict(size=len(files[name]), sha256=sha256(files[name])) for name in ('code/apccs_core.py', 'code/test_apccs_core.py')}
            candidate_hash = sha256(_b2_json({n: dict(size=len(b), sha256=sha256(b)) for n, b in sorted(files.items())}))
            if receipt.get('files') != expected_files or receipt.get('candidate_sha256') != candidate_hash or receipt.get('report_sha256') != sha256(_b2_json(report)) or receipt.get('authorization') != B4_AUTHORIZATION:
                raise AuditRejected('Gate 5 receipt is not bound to this candidate')
            result['gates']['5'] = receipt
            result['release_ready'] = all(g['passed'] for g in result['gates'].values()) and self.key is not None
        return result

    def audit(self, case_id, gate5_verifier=None, gate5_policy_id='INST-0016'):
        try:
            with _b4_serial():
                _b4_not_halted()
                result = super().audit(case_id, gate5_verifier, gate5_policy_id)
                if not result['release_ready']:
                    raise AuditRejected('All five gates and host authority required')
                return result
        except Exception:
            trigger_andon_cord('Audit gate failed')
            raise

    def promote(self, case_id, owner_decision=None):
        try:
            with _b4_serial():
                _b4_not_halted()
                approval = require_owner_approval('CHG-0020', 'Promote immutable case ' + case_id, owner_decision)
                if not approval['approved']:
                    return dict(status='GRAY', reason='EXPLICIT_OWNER_YES_REQUIRED', case_id=case_id)
                with self._connect() as db:
                    row = self._case(db, case_id)
                if row[5] not in ('PROMOTED', 'PREPARED'):
                    _b4_snapshot('before_' + case_id)
                result = super().promote(case_id)
                result['checkpoint'] = 'before_' + case_id
                return result
        except Exception:
            trigger_andon_cord('Promotion failed')
            raise


B5_PREFIX_BYTES = 84183
B5_PREFIX_SHA256 = '814276a84126ed2615a8d69589afbe34339a8b9a751fb8b57de49614c45b25f2'
B5_CODEBOOK = (('T', 'X', 'motorcycle'), ('T', 'Y', 'lighthouse'),
               ('T', 'Z', 'anvil'), ('T', 'W', 'compass'), ('M', 'K', 'submarine'))


class CanaryTripwireEngine:
    """Persistent per-channel probes. Receipts detect omission/replay, not model truth.

    One pending probe per channel; each of five pairs is used once, starting
    with the active Batch 5 pair. Exhaustion requires a new channel. Host code
    must intercept every worker reply and enforce channel locks at dispatch.
    SQLite transactions serialize concurrent processes, not just threads.
    """
    def __init__(self, db_path=None, initial_index=4):
        if type(initial_index) is not int or not 0 <= initial_index < len(B5_CODEBOOK):
            raise ValueError('Codebook index must be 0..4')
        self.path = verify_safe_path(db_path or 'state/canary_tripwire.db')
        if self.path.is_symlink():
            raise ValueError('Canary database symlink forbidden')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initial_index = initial_index
        with self._transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS b5_channels (channel_id TEXT PRIMARY KEY, initial_index INTEGER NOT NULL, used INTEGER NOT NULL, locked INTEGER NOT NULL, pending TEXT, checkpoint INTEGER NOT NULL, next_task TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS b5_turns (probe_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL REFERENCES b5_channels(channel_id), challenge TEXT NOT NULL, prompt TEXT NOT NULL, output TEXT, status TEXT NOT NULL, reason TEXT, recorded TEXT NOT NULL)')

    @contextlib.contextmanager
    def _transaction(self):
        if self.path.is_symlink():
            raise ValueError('Canary database symlink forbidden')
        db = sqlite3.connect(self.path, timeout=120, isolation_level=None)
        try:
            db.execute('PRAGMA busy_timeout=120000')
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _channel_id(self, channel_id):
        value = 'default' if channel_id is None else channel_id
        if not isinstance(value, str) or re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', value) is None:
            raise ValueError('Safe channel identifier required')
        return value

    def _channel(self, db, channel_id):
        row = db.execute('SELECT initial_index,used,locked,pending,checkpoint,next_task FROM b5_channels WHERE channel_id=?', (channel_id,)).fetchone()
        if row is None:
            if db.execute('SELECT count(*) FROM b5_channels').fetchone()[0] >= 20:
                raise AuditRejected('Twenty channel identities already recorded; host archival required')
            db.execute('INSERT INTO b5_channels VALUES (?,?,0,0,NULL,0,?)',
                       (channel_id, self.initial_index, 'Host must supply the next authorized task'))
            row = (self.initial_index, 0, 0, None, 0, 'Host must supply the next authorized task')
        return row

    def set_checkpoint(self, channel_id, checkpoint, next_task):
        """Trusted host records accepted state; candidate output cannot advance it."""
        channel_id = self._channel_id(channel_id)
        if type(checkpoint) is not int or not 0 <= checkpoint <= 1000:
            raise ValueError('Instruction checkpoint must be 0..1000')
        if not isinstance(next_task, str) or not next_task.strip() or len(next_task.encode()) > 16384:
            raise ValueError('Bounded next task required')
        with self._transaction() as db:
            row = self._channel(db, channel_id)
            if checkpoint < row[4]:
                raise AuditRejected('Last good checkpoint cannot move backwards')
            db.execute('UPDATE b5_channels SET checkpoint=?,next_task=? WHERE channel_id=?', (checkpoint, next_task, channel_id))
        return dict(channel_id=channel_id, checkpoint=checkpoint, next_task=next_task)

    def channel_state(self, channel_id=None):
        channel_id = self._channel_id(channel_id)
        with self._transaction() as db:
            row = self._channel(db, channel_id)
            return dict(channel_id=channel_id, used=row[1], locked=bool(row[2]),
                        pending=json.loads(row[3]) if row[3] else None,
                        checkpoint=row[4], next_task=row[5])

    def attach(self, prompt_text, channel_id=None):
        if not isinstance(prompt_text, str) or len(prompt_text.encode()) > 1024 * 1024:
            raise ValueError('Worker prompt must be text of at most one MiB')
        channel_id = self._channel_id(channel_id)
        failure = None
        result = None
        with self._transaction() as db:
            row = self._channel(db, channel_id)
            if row[2]:
                raise AuditRejected('Channel locked; spawn a new channel')
            if row[3]:
                raise AuditRejected('Channel already has an outstanding probe')
            if row[1] >= len(B5_CODEBOOK):
                db.execute('UPDATE b5_channels SET locked=1 WHERE channel_id=?', (channel_id,))
                failure = 'Codebook exhausted; spawn a new channel'
            else:
                variable, value, response = B5_CODEBOOK[(row[0] + row[1]) % len(B5_CODEBOOK)]
                probe = dict(probe_id=uuid.uuid4().hex, channel_id=channel_id,
                             challenge=variable+'='+value, response=response)
                probe['ack_line'] = 'Canary check: '+variable+' = '+value+' -> '+response+' [probe_id='+probe['probe_id']+']'
                raw = json.dumps(probe, sort_keys=True)
                db.execute('UPDATE b5_channels SET used=used+1,pending=? WHERE channel_id=?', (raw, channel_id))
                db.execute('INSERT INTO b5_turns VALUES (?,?,?,?,NULL,?,NULL,?)',
                           (probe['probe_id'], channel_id, probe['challenge'], prompt_text, 'PENDING',
                            dt.datetime.now(ZoneInfo('America/Vancouver')).isoformat()))
                result = prompt_text + '\n\nCANARY PROBE — reply with this exact line once, outside code blocks:\n' + probe['ack_line']
        if failure:
            raise AuditRejected(failure)
        return result

    def _cutoff(self, db, channel_id, reason, ai_output=None):
        row = self._channel(db, channel_id)
        if row[3]:
            probe = json.loads(row[3])
            db.execute('UPDATE b5_turns SET output=?,status=?,reason=? WHERE probe_id=?',
                       (ai_output, 'QUARANTINED', reason, probe['probe_id']))
        else:
            db.execute('INSERT INTO b5_turns VALUES (?,?,?,?,?,?,?,?)',
                       (uuid.uuid4().hex, channel_id, 'NONE', '', ai_output, 'QUARANTINED', reason,
                        dt.datetime.now(ZoneInfo('America/Vancouver')).isoformat()))
        db.execute('UPDATE b5_channels SET locked=1,pending=NULL WHERE channel_id=?', (channel_id,))
        return dict(status='RED', locked=True, quarantined=True, channel_id=channel_id,
                    reason=reason, clean_output='')

    def cutoff(self, channel_id, reason):
        channel_id = self._channel_id(channel_id)
        if not isinstance(reason, str) or not reason.strip() or len(reason.encode()) > 4096:
            raise ValueError('Bounded cutoff reason required')
        with self._transaction() as db:
            return self._cutoff(db, channel_id, reason)

    def verify(self, ai_output, expected_challenge=None):
        if not isinstance(ai_output, str) or len(ai_output.encode()) > 1024 * 1024:
            raise ValueError('Worker output must be text of at most one MiB')
        with self._transaction() as db:
            rows = db.execute('SELECT channel_id,pending FROM b5_channels WHERE pending IS NOT NULL AND locked=0').fetchall()
            matches = []
            for channel, raw in rows:
                probe = json.loads(raw)
                if expected_challenge is None:
                    matches.append((channel, probe))
                elif isinstance(expected_challenge, dict):
                    if all(expected_challenge.get(k) == probe[k] for k in ('channel_id', 'challenge', 'probe_id')):
                        matches.append((channel, probe))
                elif isinstance(expected_challenge, str) and expected_challenge in (probe['challenge'], probe['ack_line']):
                    matches.append((channel, probe))
            if len(matches) != 1:
                raise AuditRejected('Expected probe must identify exactly one pending channel')
            channel, probe = matches[0]
            lines = ai_output.splitlines(keepends=True)
            valid_indices = []
            fenced = False
            for index, line in enumerate(lines):
                stripped = line.rstrip('\r\n')
                if stripped.lstrip().startswith(('```', '~~~')):
                    fenced = not fenced
                if not fenced and stripped == probe['ack_line']:
                    valid_indices.append(index)
            all_matches = sum(line.rstrip('\r\n') == probe['ack_line'] for line in lines)
            if len(valid_indices) != 1 or all_matches != 1:
                return dict(passed=False, **self._cutoff(db, channel, 'CANARY_MISSING_WRONG_DUPLICATED_OR_QUOTED', ai_output))
            index = valid_indices[0]
            clean = ''.join(line for n, line in enumerate(lines) if n != index)
            db.execute('UPDATE b5_turns SET output=?,status=? WHERE probe_id=?', (ai_output, 'VERIFIED', probe['probe_id']))
            db.execute('UPDATE b5_channels SET pending=NULL WHERE channel_id=?', (channel,))
            return dict(passed=True, status='GREEN', clean_output=clean, channel_id=channel,
                        challenge=probe['challenge'], probe_id=probe['probe_id'])

    def spawn_baton(self, channel_id):
        channel_id = self._channel_id(channel_id)
        with self._transaction() as db:
            row = self._channel(db, channel_id)
            schema = B5_BATON_SCHEMA.encode('utf-8')
            if len(schema) != 500:
                raise AuditRejected('Baton schema must be exactly 500 bytes')
            directory = verify_safe_path(ROOT/'changes'/'channel_batons'/sha256(channel_id.encode()))
            if _count() + RESERVE >= STOP_AT:
                raise AuditRejected('Workspace file reserve exhausted')
            payload = dict(channel_id=channel_id, last_good_checkpoint=row[4], next_task=row[5],
                           source_channel_locked=bool(row[2]), canary_used=row[1],
                           created=dt.datetime.now(ZoneInfo('America/Vancouver')).isoformat(),
                           instruction='Start a new channel; do not unlock or reuse the old channel. Preserve accepted state; do not advance a batch without explicit dispatch.')
            text = 'APCCS CLEAN THREAD BATON\n'+json.dumps(payload,ensure_ascii=False,indent=2)+'\nSCHEMA_STUB_BYTES: 500\n'+schema.decode()+'\nEND_SCHEMA_STUB\n'
            path = directory/'SPAWN_NEW_THREAD_BATON.txt'
            _b4_write(path,text.encode())
            return dict(path=str(path), schema_bytes=500, sha256=sha256(path.read_bytes()),
                        last_good_checkpoint=row[4], next_task=row[5])


def attach_canary_probe(prompt_text, channel_id=None):
    return CanaryTripwireEngine().attach(prompt_text, channel_id)


def verify_canary_ack(ai_output, expected_challenge=None):
    return CanaryTripwireEngine().verify(ai_output, expected_challenge)


def cutoff_rotted_channel(channel_id, reason):
    return CanaryTripwireEngine().cutoff(channel_id, reason)


def generate_spawn_baton(channel_id):
    return CanaryTripwireEngine().spawn_baton(channel_id)


B5_BATON_SCHEMA = '{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"APCCS clean thread baton","type":"object","required":["channel_id","last_good_checkpoint","next_task"],"properties":{"channel_id":{"type":"string","minLength":1},"last_good_checkpoint":{"type":"integer","minimum":0,"maximum":1000},"next_task":{"type":"string","minLength":1},"source_channel_locked":{"type":"boolean"}},"description":"Host supplied accepted state; preserve verified records and request explicit next batch dispatch."}'

# Batch 6: append-only extension of the verified 96,709-byte prefix.
import ast as _b6_ast
import math as _b6_math


def track_turn_count(channel_id, turn_number):
    """Persist monotone turn numbers; at 14 create one baton and stop dispatch.

    Call before each host dispatch. No background thread or chatbot launch is
    implied. A failed baton write rolls back the count so a retry is possible.
    """
    if type(turn_number) is not int or turn_number < 1:
        raise ValueError('Positive integer turn required')
    engine = CanaryTripwireEngine()
    channel_id = engine._channel_id(channel_id)
    with engine._transaction() as db:
        engine._channel(db, channel_id)
        db.execute('CREATE TABLE IF NOT EXISTS b6_turn_counts (channel_id TEXT PRIMARY KEY, turn_number INTEGER NOT NULL, baton TEXT)')
        row = db.execute('SELECT turn_number,baton FROM b6_turn_counts WHERE channel_id=?', (channel_id,)).fetchone()
        previous, baton = row if row else (0, None)
        if turn_number < previous:
            raise AuditRejected('Turn count cannot move backwards')
        if turn_number >= 14 and baton is None:
            # The existing baton method opens its own writer transaction; avoid
            # nested writers by constructing the same trusted-state payload here.
            state = engine._channel(db, channel_id)
            path = verify_safe_path(ROOT/'changes'/'channel_batons'/sha256(channel_id.encode())/'SPAWN_NEW_THREAD_BATON.txt')
            if _count() + RESERVE >= STOP_AT:
                raise AuditRejected('Workspace file reserve exhausted')
            payload = dict(channel_id=channel_id, last_good_checkpoint=state[4],
                           next_task=state[5], turn_number=turn_number,
                           reason='TURN_14_MEMORY_BELT_RELAY', source_channel_locked=True)
            raw = 'APCCS CLEAN THREAD BATON\n'+json.dumps(payload, sort_keys=True)+'\nSCHEMA_STUB_BYTES: 500\n'+B5_BATON_SCHEMA+'\nEND_SCHEMA_STUB\n'
            _b4_write(path, raw.encode())
            baton = str(path)
            db.execute('UPDATE b5_channels SET locked=1 WHERE channel_id=?', (channel_id,))
        db.execute('INSERT INTO b6_turn_counts VALUES (?,?,?) ON CONFLICT(channel_id) DO UPDATE SET turn_number=excluded.turn_number,baton=excluded.baton', (channel_id, turn_number, baton))
        return dict(channel_id=channel_id, turn_number=turn_number,
                    relay_required=turn_number >= 14, dispatch_allowed=turn_number < 14 and not bool(engine._channel(db,channel_id)[2]), baton=baton)


def attach_constitution_reminder(prompt_text, turn_number):
    """Prepend ten owner-provisioned rules every fifth turn; fail if missing.

    Provision rules/core_verification_rules.json as an array of exactly ten
    nonempty strings. These are passive application data, not host authority.
    """
    if not isinstance(prompt_text, str) or type(turn_number) is not int or turn_number < 1:
        raise ValueError('Text and positive integer turn required')
    if turn_number % 5:
        return prompt_text
    path = verify_safe_path('rules/core_verification_rules.json')
    rules = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(rules, list) or len(rules) != 10 or any(not isinstance(r,str) or not r.strip() for r in rules):
        raise AuditRejected('Exactly ten owner-provisioned rules required')
    return 'CORE VERIFICATION RULES (PROJECT DATA)\n'+'\n'.join(str(i)+'. '+r for i,r in enumerate(rules,1))+'\n\n'+prompt_text


def compress_to_schema_stub(python_source_text):
    """Return parseable interfaces, docstrings and annotated schemas; never run source.

    Reduction depends on implementation/docstring proportions; 90% is a target,
    not a guarantee. Decorators, defaults and annotations remain source data.
    """
    tree = _b6_ast.parse(python_source_text)
    def retain(body):
        result = []
        for node in body:
            if isinstance(node, (_b6_ast.FunctionDef, _b6_ast.AsyncFunctionDef)):
                doc = node.body[:1] if _b6_ast.get_docstring(node,clean=False) is not None else []
                node.body = doc + [_b6_ast.Expr(value=_b6_ast.Constant(value=Ellipsis))]
                result.append(node)
            elif isinstance(node, _b6_ast.ClassDef):
                doc = node.body[:1] if _b6_ast.get_docstring(node,clean=False) is not None else []
                node.body = doc + retain(node.body) or [_b6_ast.Pass()]
                result.append(node)
            elif isinstance(node, _b6_ast.AnnAssign):
                result.append(node)
            elif isinstance(node, _b6_ast.Assign) and any(isinstance(t,_b6_ast.Name) and 'SCHEMA' in t.id.upper() for t in node.targets):
                result.append(node)
        return result
    tree.body = retain(tree.body)
    return _b6_ast.unparse(_b6_ast.fix_missing_locations(tree))+'\n'


def store_and_return_ptr(vault_dir, payload_text):
    """Inline <=200 chars; otherwise content-addressed UTF-8 file and 68 ASCII bytes.

    Format PTR:// + first 62 SHA256 hex digits. Filename uses that same prefix;
    existing differing bytes fail closed, including a truncated-hash collision.
    """
    if not isinstance(payload_text,str):
        raise TypeError('Text required')
    directory = verify_safe_path(ROOT/'imports') if Path(vault_dir).absolute() == ROOT else verify_safe_path(vault_dir)
    if len(payload_text) <= 200:
        return payload_text
    data = payload_text.encode('utf-8')
    digest = sha256(data)[:62]
    path = verify_safe_path(directory/'tool_outputs'/(digest+'.txt'))
    with _b4_serial():
        if path.exists():
            if path.read_bytes() != data:
                raise AuditRejected('Pointer collision or corrupt stored output')
        else:
            if _count() + RESERVE >= STOP_AT:
                raise AuditRejected('Workspace file reserve exhausted')
            _b4_write(path,data)
    return 'PTR://'+digest


class MultiConstraintGovernor:
    """Validate immutable policy and reject out-of-policy host measurements.

    Host must call enforce before dispatch; this object cannot kill subprocesses,
    intercept independent browser calls, or measure context size itself.
    """
    DEFAULTS = dict(max_compile_chars_per_turn=7500, max_input_context_fill_pct=35,
                    swarm_channel_scale_mode='AUTO_1_TO_20', patch_emission_mode='SURGICAL_DIFF',
                    sandbox_step_timeout_sec=20, turn_relay_ceiling=14,
                    browser_cache_ceiling_kb=250, maker_checker_strictness='ZERO_TRUST',
                    circuit_breaker_strikes=2, sqlite_writer_concurrency=1)

    def __init__(self, **parameters):
        if set(parameters) - set(self.DEFAULTS):
            raise ValueError('Unknown policy parameter')
        for key,value in parameters.items():
            if type(value) is not type(self.DEFAULTS[key]) or value != self.DEFAULTS[key]:
                raise ValueError('Policy parameter mismatch: '+key)
        self._policy = tuple(self.DEFAULTS.items())

    @property
    def parameters(self):
        return dict(self._policy)

    def enforce(self, *, compile_chars, input_context_fill_pct, channels,
                patch_mode, elapsed_sec, turn_number, browser_cache_kb,
                checker_mode, strikes, sqlite_writers):
        values = dict(compile_chars=compile_chars, input_context_fill_pct=input_context_fill_pct,
                      channels=channels, elapsed_sec=elapsed_sec, turn_number=turn_number,
                      browser_cache_kb=browser_cache_kb, strikes=strikes, sqlite_writers=sqlite_writers)
        for key,value in values.items():
            if type(value) not in (int,float) or not _b6_math.isfinite(value) or value < 0:
                raise AuditRejected('Invalid measurement: '+key)
        for key in ('compile_chars','channels','turn_number','strikes','sqlite_writers'):
            if type(values[key]) is not int:
                raise AuditRejected('Integer measurement required: '+key)
        checks = (compile_chars <= 7500, input_context_fill_pct <= 35,
                  1 <= channels <= 20, patch_mode == 'SURGICAL_DIFF', elapsed_sec <= 20,
                  1 <= turn_number < 14, browser_cache_kb <= 250,
                  checker_mode == 'ZERO_TRUST', strikes < 2, sqlite_writers <= 1)
        failed = [key for key,ok in zip(dict(self._policy),checks) if not ok]
        if failed:
            raise AuditRejected('Governor rejected: '+', '.join(failed))
        return dict(allowed=True, parameters=self.parameters)

# Batch 7. Append-only APIs; host dispatch must use their returned decisions.
import socket as _b7_socket
import threading as _b7_threading
import subprocess as _b7_subprocess
import sys as _b7_sys
import tempfile as _b7_tempfile


def _b7_integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(label+' must be an integer >= '+str(minimum))
    return value


def _b7_identifier(value):
    if not isinstance(value,str) or re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value) is None:
        raise ValueError('Bounded identifier required')
    return value


def _b7_safe_path(value):
    raw = Path(value)
    candidate = raw if raw.is_absolute() else ROOT/raw
    if '..' in raw.parts:
        raise ValueError('Parent traversal rejected')
    for part in (candidate, *candidate.parents):
        if part.is_symlink():
            raise ValueError('Symlink path rejected')
    return verify_safe_path(candidate)


class ChannelAutoscaler:
    """Deterministic headroom heuristic, not a benchmark-derived optimum.

    CPU headroom is 0..100 percent of the supplied logical CPUs. Memory is
    available MiB after the host's reserve. Idle/starved plans retain one
    logical channel but authorize zero dispatches. No worker is spawned.
    """
    def __init__(self, memory_per_channel_mb=256):
        self.memory_per_channel_mb = _b7_integer(memory_per_channel_mb,'Memory per channel',1)

    def plan(self, queue_depth, cpu_headroom_pct, available_memory_mb, cpu_count=None):
        _b7_integer(queue_depth,'Queue depth')
        cpus = (os.cpu_count() or 1) if cpu_count is None else _b7_integer(cpu_count,'CPU count',1)
        for value,label,ceiling in ((cpu_headroom_pct,'CPU headroom',100),
                                    (available_memory_mb,'Available memory',float('inf'))):
            if type(value) not in (int,float) or not _b6_math.isfinite(value) or not 0 <= value <= ceiling:
                raise ValueError('Invalid '+label)
        cpu_slots = int(cpus*cpu_headroom_pct/100)
        memory_slots = int(available_memory_mb/self.memory_per_channel_mb)
        dispatch_slots = min(20, queue_depth, cpu_slots, memory_slots)
        return dict(channels=max(1,dispatch_slots), dispatch_slots=dispatch_slots,
                    dispatch_allowed=dispatch_slots > 0, queue_depth=queue_depth,
                    cpu_slots=cpu_slots, memory_slots=memory_slots)

    def calculate(self, queue_depth, cpu_headroom_pct, available_memory_mb, cpu_count=None):
        """Return 1..20; use plan.dispatch_allowed before dispatching work."""
        return self.plan(queue_depth,cpu_headroom_pct,available_memory_mb,cpu_count)['channels']


_B7_LANES = {}
_B7_LANE_LOCK = _b7_threading.RLock()


class ChannelLane(dict):
    """A loopback port reservation and isolated staging directory.

    Keep this handle alive. close() releases the port, not staged records.
    This reserves a port; transfer to a server needs a host-managed socket
    handoff. Closing then rebinding has an unavoidable OS scheduling race.
    """
    def __init__(self, index, path, sock):
        super().__init__(channel_index=index, staging_dir=str(path),host='127.0.0.1',port=8501+index)
        self._socket = sock
        self._pid = os.getpid()
        self._registry_key = (str(ROOT),index)

    def close(self):
        with _B7_LANE_LOCK:
            self._socket.close()
            if _B7_LANES.get(self._registry_key) is self:
                del _B7_LANES[self._registry_key]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


def allocate_channel_lane(ch_idx):
    """Reserve zero-based lane 0..19 and port 8501+index; fail on occupancy.

    Cooperating calls are idempotent; OS bind excludes competing processes.
    Directories use imports/channel_lanes/ch_NN/staging; no git operations.
    Existing content is mounted without replacement. No engine is installed.
    """
    _b7_integer(ch_idx,'Channel index')
    if ch_idx >= 20:
        raise ValueError('Channel index must be 0..19')
    key = (str(ROOT),ch_idx)
    with _B7_LANE_LOCK:
        cached = _B7_LANES.get(key)
        if cached is not None and cached._pid == os.getpid() and cached._socket.fileno() >= 0:
            _b7_safe_path(cached['staging_dir'])
            return cached
        path = _b7_safe_path(ROOT/'imports'/'channel_lanes'/('ch_'+format(ch_idx,'02d'))/'staging')
        sock = _b7_socket.socket(_b7_socket.AF_INET,_b7_socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1',8501+ch_idx))
            if _count()+RESERVE >= STOP_AT:
                raise AuditRejected('Workspace file reserve exhausted')
            path.mkdir(parents=True,exist_ok=True)
            lane = ChannelLane(ch_idx,path,sock)
            _B7_LANES[key] = lane
            return lane
        except BaseException:
            sock.close()
            raise


@contextlib.contextmanager
def _b7_transaction(path):
    path = _b7_safe_path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(path,timeout=20,isolation_level=None)
    try:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def skip_verified_modules(modules=None):
    """Return skip/build lists after fresh, hash-pinned unittest discovery.

    No arguments loads state/verified_modules.json, an array of entries:
    module_id, path, sha256, test_path, test_sha256. Empty registry skips none.
    Missing/malformed evidence never grants a skip. Test files must be named
    test_*.py. Both artifacts are hashed before and after running >=1 tests.
    Tests run in /tmp with an isolated APCCS_VAULT_ROOT and a 20-second timeout.
    This is not an OS sandbox: host-approved test code must be trustworthy.
    The tested module must stay immutable between this decision and dispatch.
    """
    if modules is None:
        registry = _b7_safe_path('state/verified_modules.json')
        modules = json.loads(registry.read_text()) if registry.exists() else []
    if not isinstance(modules,list) or len(modules)>1000:
        raise ValueError('Bounded module list required')
    seen, skipped, build, evidence = set(), [], [], {}
    for item in modules:
        if not isinstance(item,dict):
            raise ValueError('Module entry must be an object')
        identity = _b7_identifier(item.get('module_id'))
        if identity in seen:
            raise ValueError('Duplicate module identity')
        seen.add(identity)
        reason = 'MISSING_OR_INVALID_EVIDENCE'
        try:
            path = _b7_safe_path(item['path'])
            test = _b7_safe_path(item['test_path'])
            if path == test or not test.name.startswith('test_') or test.suffix != '.py':
                raise ValueError('Separate unittest file required')
            pins = (item['sha256'],item['test_sha256'])
            if any(not isinstance(pin,str) or re.fullmatch('[0-9a-f]{64}',pin) is None for pin in pins):
                raise ValueError('SHA256 pins required')
            if (sha256(path.read_bytes()),sha256(test.read_bytes())) != pins:
                reason = 'HASH_MISMATCH'
            else:
                with _b7_tempfile.TemporaryDirectory(prefix='apccs_b7_module_',dir='/tmp') as scratch:
                    environment = dict(os.environ,APCCS_VAULT_ROOT=str(Path(scratch)/'vault'),PYTHONDONTWRITEBYTECODE='1')
                    # File-backed output bounds memory; only its tail is read.
                    with open(Path(scratch)/'test_output.txt','w+b') as output:
                        run = _b7_subprocess.run([_b7_sys.executable,'-B','-m','unittest','discover',
                            '-s',str(test.parent),'-p',test.name],cwd=scratch,env=environment,
                            stdout=output,stderr=_b7_subprocess.STDOUT,timeout=20,check=False)
                        size = output.tell()
                        output.seek(max(0,size-65536))
                        tail = output.read().decode('utf-8',errors='replace')
                    after = (sha256(path.read_bytes()),sha256(test.read_bytes()))
                    passed = run.returncode == 0 and re.search(r'Ran [1-9][0-9]* tests? in ',tail) is not None and '\nOK\n' in tail
                    reason = 'VERIFIED' if passed and after == pins else 'TEST_FAILED_OR_ARTIFACT_CHANGED'
                    evidence[identity] = dict(returncode=run.returncode,tests_passed=passed,
                                              hashes_unchanged=after==pins,output_tail=tail)
        except _b7_subprocess.TimeoutExpired:
            reason = 'TEST_TIMEOUT'
        except (KeyError,OSError,ValueError,TypeError):
            reason = 'MISSING_OR_INVALID_EVIDENCE'
        (skipped if reason=='VERIFIED' else build).append(identity)
        evidence.setdefault(identity,{})['reason'] = reason
    return dict(skip=skipped,build=build,evidence=evidence)


class TaskQueueScheduler:
    """Persistent one-turn leases; blocker repair, then spine, then skin.

    Delta decisions always use skip_verified_modules, never a task's claimed
    verified flag. One task is leased per scheduler per turn. Advancing a turn
    expires unfinished work. Host must stop the worker at that boundary.
    Andon allows blocker-repair tasks only; it is never cleared by this API.
    """
    def __init__(self, db_path='state/b7_scheduler.db'):
        self.path = _b7_safe_path(db_path)
        with _b7_transaction(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS b7_tasks (task_id TEXT PRIMARY KEY, body TEXT NOT NULL, status TEXT NOT NULL, lease_turn INTEGER)')
            db.execute('CREATE TABLE IF NOT EXISTS b7_scheduler_state (singleton INTEGER PRIMARY KEY, current_turn INTEGER NOT NULL, dispatched INTEGER NOT NULL)')
            db.execute('INSERT OR IGNORE INTO b7_scheduler_state VALUES (1,0,0)')

    def enqueue(self, task):
        if not isinstance(task,dict) or set(task) != {'task_id','module_id','layer','andon_blocker','estimated_turns'}:
            raise ValueError('Exact task fields required')
        _b7_identifier(task['task_id']); _b7_identifier(task['module_id'])
        if task['layer'] not in ('spine','skin') or type(task['andon_blocker']) is not bool:
            raise ValueError('Spine/skin layer and Boolean blocker required')
        if type(task['estimated_turns']) is not int or task['estimated_turns'] != 1:
            raise AuditRejected('Split work into one-turn tasks before enqueue')
        body = json.dumps(task,sort_keys=True,separators=(',',':'))
        with _b7_transaction(self.path) as db:
            prior = db.execute('SELECT body FROM b7_tasks WHERE task_id=?',(task['task_id'],)).fetchone()
            if prior and prior[0] != body:
                raise AuditRejected('Existing task identity cannot be overwritten')
            db.execute('INSERT OR IGNORE INTO b7_tasks VALUES (?,?,?,NULL)',(task['task_id'],body,'QUEUED'))
        return dict(task_id=task['task_id'],mounted=prior is not None)

    def schedule(self, turn_number, modules=None):
        _b7_integer(turn_number,'Turn number',1)
        delta = skip_verified_modules(modules)
        with _b7_transaction(self.path) as db:
            current,dispatched = db.execute('SELECT current_turn,dispatched FROM b7_scheduler_state WHERE singleton=1').fetchone()
            if turn_number < current:
                raise AuditRejected('Scheduler turn cannot move backwards')
            if turn_number > current:
                db.execute("UPDATE b7_tasks SET status='TIMED_OUT' WHERE status='LEASED' AND lease_turn<?",(turn_number,))
                db.execute('UPDATE b7_scheduler_state SET current_turn=?,dispatched=0 WHERE singleton=1',(turn_number,))
                dispatched = 0
            rows = db.execute("SELECT body FROM b7_tasks WHERE status='QUEUED' ORDER BY rowid").fetchall()
            tasks = [json.loads(row[0]) for row in rows]
            tasks = [task for task in tasks if task['module_id'] not in delta['skip']]
            andon = (_b4_control()/'ANDON.json').exists()
            if andon:
                tasks = [task for task in tasks if task['andon_blocker']]
            tasks.sort(key=lambda task:(not task['andon_blocker'],task['layer']!='spine'))
            selected = tasks[0] if tasks and not dispatched else None
            if selected:
                db.execute("UPDATE b7_tasks SET status='LEASED',lease_turn=? WHERE task_id=?",(turn_number,selected['task_id']))
                db.execute('UPDATE b7_scheduler_state SET dispatched=1 WHERE singleton=1')
            return dict(task=selected,turn_number=turn_number,expires_before_turn=turn_number+1,
                        skipped_modules=delta['skip'],andon_active=andon)

    def complete(self, task_id, turn_number):
        _b7_identifier(task_id); _b7_integer(turn_number,'Turn number',1)
        with _b7_transaction(self.path) as db:
            current = db.execute('SELECT current_turn FROM b7_scheduler_state WHERE singleton=1').fetchone()[0]
            changed = db.execute("UPDATE b7_tasks SET status='DONE' WHERE task_id=? AND status='LEASED' AND lease_turn=? AND ?=?",(task_id,turn_number,turn_number,current)).rowcount
            if changed != 1:
                raise AuditRejected('Missing, stale or already completed turn lease')
        return dict(task_id=task_id,status='DONE',turn_number=turn_number)


def _b7_schema(schema, depth=0):
    if depth>20 or not isinstance(schema,dict):
        raise ValueError('Bounded object schema required')
    kind = schema.get('type')
    if kind not in ('object','array','string','integer','number','boolean','null'):
        raise ValueError('Explicit supported schema type required')
    allowed = {'type','enum'}
    if kind=='object':
        allowed |= {'properties','required','additionalProperties'}
        properties = schema.get('properties',{})
        required = schema.get('required',[])
        if not isinstance(properties,dict) or len(properties)>1000 or not all(isinstance(k,str) for k in properties):
            raise ValueError('Bounded named properties required')
        if not isinstance(required,list) or any(not isinstance(k,str) for k in required) or len(set(required))!=len(required) or not set(required)<=set(properties):
            raise ValueError('Required fields must be declared, unique names')
        if type(schema.get('additionalProperties',False)) is not bool:
            raise ValueError('Boolean additionalProperties required')
        for child in properties.values(): _b7_schema(child,depth+1)
    if kind=='array':
        allowed |= {'items'}
        _b7_schema(schema.get('items'),depth+1)
    if set(schema)-allowed:
        raise ValueError('Unsupported schema keyword')
    if 'enum' in schema and (not isinstance(schema['enum'],list) or not schema['enum']):
        raise ValueError('Nonempty enum required')
    # Also reject NaN, non-JSON values and recursive structures.
    json.dumps(schema,allow_nan=False)
    return schema


def _b7_schema_accepts(value, schema):
    kind = schema['type']
    valid = {'object':type(value) is dict,'array':type(value) is list,
             'string':type(value) is str,'integer':type(value) is int,
             'number':type(value) in (int,float),'boolean':type(value) is bool,
             'null':value is None}[kind]
    if not valid or kind=='number' and not _b6_math.isfinite(value):
        return False
    if 'enum' in schema:
        encoded = json.dumps(value,sort_keys=True,allow_nan=False)
        if encoded not in [json.dumps(v,sort_keys=True,allow_nan=False) for v in schema['enum']]:
            return False
    if kind=='object':
        props = schema.get('properties',{})
        if not set(schema.get('required',[]))<=set(value): return False
        if not schema.get('additionalProperties',False) and set(value)-set(props): return False
        return all(_b7_schema_accepts(v,props[k]) for k,v in value.items() if k in props)
    if kind=='array':
        return all(_b7_schema_accepts(v,schema['items']) for v in value)
    return True


def _b7_schema_compatible(producer, consumer):
    # Conservative compatibility: object extensions are permitted only when
    # explicitly allowed by the consumer. Complex subtyping is rejected.
    if producer['type'] != consumer['type']:
        return producer['type']=='integer' and consumer['type']=='number' and set(consumer)=={'type'}
    if 'enum' in consumer:
        if 'enum' not in producer:
            return False
        permitted = {json.dumps(v,sort_keys=True,allow_nan=False) for v in consumer['enum']}
        if any(json.dumps(v,sort_keys=True,allow_nan=False) not in permitted for v in producer['enum']):
            return False
    if producer['type']=='object':
        pp,cp = producer.get('properties',{}),consumer.get('properties',{})
        if not set(consumer.get('required',[]))<=set(producer.get('required',[])):
            return False
        if not consumer.get('additionalProperties',False) and (producer.get('additionalProperties',False) or set(pp)-set(cp)):
            return False
        if producer.get('additionalProperties',False) and set(cp)-set(pp):
            return False
        return all(_b7_schema_compatible(pp[k],cp[k]) for k in set(pp)&set(cp))
    if producer['type']=='array':
        return _b7_schema_compatible(producer['items'],consumer['items'])
    return True


def verify_channel_contract(producer_contract, consumer_contract, payload):
    """Validate before downstream consumption; fail closed, never return payload.

    Contracts are objects with exactly contract_id, version (positive integer),
    schema. IDs and versions must match. Supported schema subset: explicit
    JSON types, properties/required/additionalProperties, array items, enum.
    Default additionalProperties is false (deliberately stricter than JSON
    Schema). Unknown keywords/references are rejected, not silently ignored.
    Compatibility is directional plus validation of this exact JSON payload.
    No source text is evaluated and no receiving channel is launched.
    """
    try:
        for contract in (producer_contract,consumer_contract):
            if not isinstance(contract,dict) or set(contract)!={'contract_id','version','schema'}:
                raise ValueError('Exact contract fields required')
            _b7_identifier(contract['contract_id'])
            _b7_integer(contract['version'],'Contract version',1)
            _b7_schema(contract['schema'])
        if (producer_contract['contract_id'],producer_contract['version']) != (consumer_contract['contract_id'],consumer_contract['version']):
            raise ValueError('Contract identity/version mismatch')
        raw = json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)
        if len(raw.encode())>1024*1024:
            raise ValueError('Payload exceeds one MiB')
        # Round-trip rejects non-string object keys and non-JSON tuple types.
        if json.loads(raw)!=payload:
            raise ValueError('JSON-native payload required')
        ps,cs = producer_contract['schema'],consumer_contract['schema']
        if not _b7_schema_compatible(ps,cs):
            raise ValueError('Incompatible producer/consumer schemas')
        if not _b7_schema_accepts(payload,ps) or not _b7_schema_accepts(payload,cs):
            raise ValueError('Payload violates channel contract')
        return dict(passed=True,status='GREEN',payload_sha256=sha256(raw.encode()),
                    contract_id=producer_contract['contract_id'],version=producer_contract['version'])
    except (ValueError,TypeError,RecursionError,OverflowError) as error:
        return dict(passed=False,status='RED',reason=str(error))

# Batch 8: read-only sensors and additive lossless storage operations.
import shutil as _b8_shutil
import heapq as _b8_heapq
import zlib as _b8_zlib
import base64 as _b8_base64
import stat as _b8_stat
import time as _b8_time


def _b8_scan_entries(scan_root, max_entries):
    _b7_integer(max_entries,'Scan entry limit',1)
    root = Path(scan_root).absolute()
    if root.is_symlink() or root.resolve()!=root or not root.is_dir():
        raise ValueError('Existing directory without symlink components required')
    entries, errors, visited = [], [], 0
    stack = [root]
    complete = True
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as items:
                for item in items:
                    if visited >= max_entries:
                        complete = False
                        stack.clear()
                        break
                    visited += 1
                    try:
                        info = item.stat(follow_symlinks=False)
                        entries.append((Path(item.path),info))
                        if _b8_stat.S_ISDIR(info.st_mode):
                            stack.append(Path(item.path))
                    except OSError as error:
                        if len(errors)<100: errors.append(dict(path=item.path,error=str(error)))
                        complete = False
        except OSError as error:
            if len(errors)<100: errors.append(dict(path=str(directory),error=str(error)))
            complete = False
    return root,entries,errors,complete


def scan_device_storage(scan_root=None, top_n=10, max_entries=100000):
    """Read current runtime filesystem, not a remote/phone device.

    MB/GB are decimal; MiB/GiB are binary. Counted files include symlinks,
    which are never followed. Hardlinked bytes are counted once per inode.
    Bounded scans explicitly report incomplete traversal/errors.
    """
    _b7_integer(top_n,'Top file limit',1)
    if top_n>1000: raise ValueError('Top file limit must be <=1000')
    root,entries,errors,complete = _b8_scan_entries(scan_root or WORKSPACE,max_entries)
    usage = _b8_shutil.disk_usage(root)
    try:
        filesystem = os.statvfs(root)
        inodes = dict(total=filesystem.f_files,free=filesystem.f_ffree,
                      available=filesystem.f_favail,reported=filesystem.f_files>0)
    except (OSError,AttributeError):
        inodes = dict(total=None,free=None,available=None,reported=False)
    files = [(path,info) for path,info in entries if not _b8_stat.S_ISDIR(info.st_mode)]
    unique,allocated,logical = set(),0,0
    for path,info in files:
        identity = (info.st_dev,info.st_ino)
        if identity not in unique:
            unique.add(identity)
            logical += info.st_size
            allocated += getattr(info,'st_blocks',0)*512
    largest = _b8_heapq.nlargest(top_n,files,key=lambda row:row[1].st_size)
    return dict(scope='CURRENT_RUNTIME_FILESYSTEM',scan_root=str(root),
                disk_total_bytes=usage.total,disk_used_bytes=usage.used,disk_free_bytes=usage.free,
                free_mb=usage.free/1_000_000,free_gb=usage.free/1_000_000_000,
                free_mib=usage.free/1048576,free_gib=usage.free/1073741824,
                file_count=len(files),directory_count=len(entries)-len(files),
                unique_file_inodes=len(unique),scanned_unique_logical_bytes=logical,
                scanned_unique_allocated_bytes=allocated,inodes=inodes,
                largest_files=[dict(path=str(path),bytes=info.st_size,
                                    symlink=_b8_stat.S_ISLNK(info.st_mode)) for path,info in largest],
                complete=complete,errors=errors,entry_limit=max_entries)


def _b8_read_memory(meminfo_path):
    values = {}
    try:
        for line in Path(meminfo_path).read_text().splitlines():
            fields = line.split()
            if len(fields)>=2 and fields[0].endswith(':') and fields[1].isdigit():
                values[fields[0][:-1]] = int(fields[1])*1024
    except OSError:
        return None,None,'UNAVAILABLE'
    # MemFree alone excludes reclaimable memory; do not invent availability.
    return values.get('MemTotal'),values.get('MemAvailable'),'PROC_MEMINFO'


def scan_compute_headroom(meminfo_path='/proc/meminfo', cgroup_root='/sys/fs/cgroup'):
    """Read CPU count/affinity, Linux MemAvailable and cgroup v2 bounds.

    CPU count is capacity, not a measurement of CPU idle percentage. Profiles
    budget half effective cores plus256MiB/channel. Unknown RAM means no
    dispatch. cgroup v1 and platform-specific non-Linux memory are unverified.
    """
    detected = os.cpu_count()
    cores = detected if type(detected) is int and detected>0 else 1
    try:
        affinity = len(os.sched_getaffinity(0))
        cores = min(cores,affinity)
    except (AttributeError,OSError):
        affinity = None
    total,available,source = _b8_read_memory(meminfo_path)
    if total is not None and available is not None:
        available=min(total,available)
    cgroup = Path(cgroup_root)
    bounds,errors = {},[]
    try:
        limit_raw=(cgroup/'memory.max').read_text().strip()
        if limit_raw!='max':
            limit=int(limit_raw); current=int((cgroup/'memory.current').read_text().strip())
            if min(limit,current)<0: raise ValueError('Negative cgroup memory')
            bounds.update(memory_limit_bytes=limit,memory_current_bytes=current)
            available=min(available,max(0,limit-current)) if available is not None else max(0,limit-current)
            total=min(total,limit) if total is not None else limit
            source += '+CGROUP_V2'
    except (OSError,ValueError) as error:
        errors.append('cgroup memory: '+str(error))
    try:
        quota,period=(cgroup/'cpu.max').read_text().split()
        if quota!='max':
            quota,period=int(quota),int(period)
            if quota<0 or period<=0: raise ValueError('Invalid CPU quota')
            bounds['cpu_quota_cores']=quota/period
            cores=min(cores,quota//period)
    except (OSError,ValueError) as error:
        errors.append('cgroup cpu: '+str(error))
    memory_slots=available//(256*1048576) if available is not None else 0
    cpu_slots=max(1,cores//2) if cores>0 else 0
    slots=min(20,cpu_slots,memory_slots)
    return dict(scope='CURRENT_RUNTIME',cpu_count=detected,effective_whole_cores=cores,
                affinity_cores=affinity,total_memory_bytes=total,available_memory_bytes=available,
                available_memory_mb=available/1_000_000 if available is not None else None,
                available_memory_mib=available/1048576 if available is not None else None,
                memory_source=source,cgroup_bounds=bounds,measurement_notes=errors,
                cpu_idle_pct=None,profile='CONSERVATIVE_HALF_CORES_256MIB',
                recommended_channels=max(1,slots),dispatch_slots=slots,
                dispatch_allowed=slots>0 and available is not None)


def list_safe_cleanup_candidates(scan_root=None, snapshot_age_days=7, max_entries=100000):
    """List only. Never delete, truncate or change permissions.

    Entire master ROOT is LOCKED, as are symlinks, hardlinks and unknown files.
    GREEN applies only to regular files in workspace tmp/temp/cache folders.
    YELLOW applies to old workspace snapshots/rollback_snapshots. Even GREEN
    entries require owner approval; the grade is a suggestion, not authority.
    """
    if type(snapshot_age_days) not in (int,float) or not _b6_math.isfinite(snapshot_age_days) or snapshot_age_days<0:
        raise ValueError('Nonnegative finite snapshot age required')
    root,entries,errors,complete = _b8_scan_entries(scan_root or WORKSPACE,max_entries)
    vault=ROOT.resolve(); workspace=WORKSPACE.resolve()
    green=[workspace/name for name in ('tmp','temp','cache')]
    yellow=[workspace/name for name in ('snapshots','rollback_snapshots')]
    now=_b8_time.time();candidates=[]
    for path,info in entries:
        if _b8_stat.S_ISDIR(info.st_mode): continue
        grade,reason='LOCKED','Unknown or protected record'
        if path.is_relative_to(vault):
            reason='Master Vault: all records protected'
        elif not _b8_stat.S_ISREG(info.st_mode) or info.st_nlink>1:
            reason='Symlink, special file or shared inode'
        elif any(path.is_relative_to(folder) for folder in green):
            grade,reason='GREEN','Allowlisted workspace temp/cache; confirm no active use'
        elif any(path.is_relative_to(folder) for folder in yellow) and now-info.st_mtime>=snapshot_age_days*86400:
            grade,reason='YELLOW','Old snapshot; retention and recovery review required'
        candidates.append(dict(path=str(path),bytes=info.st_size,grade=grade,reason=reason,
                               requires_owner_approval=True,deletion_authorized=False))
    return dict(scan_root=str(root),candidates=candidates,complete=complete,errors=errors,
                files_deleted=0)


def _b8_publish_new(path, data):
    """Atomically add a file without replacing an existing inode or its bytes."""
    path=_b7_safe_path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data: raise AuditRejected('Existing object differs; refuse overwrite')
        return False
    temporary=path.parent/('.b8_'+uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        try:
            os.link(temporary,path,follow_symlinks=False)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes()!=data:
                raise AuditRejected('Concurrent object conflict')
            return False
        descriptor=os.open(path.parent,os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
        return True
    finally:
        temporary.unlink(missing_ok=True)


_B8_EXTRACTOR = '''import base64
import hashlib
import os
from pathlib import Path
import sys
import uuid
import zlib


def extract(destination):
    root = Path(destination).absolute()
    for part in (root, *root.parents):
        if part.is_symlink():
            raise ValueError('Symlink destination forbidden')
    root.mkdir(parents=True, exist_ok=True)
    target = root / NAME
    if target.exists() or target.is_symlink():
        raise FileExistsError('Existing destination is never overwritten')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(base64.b85decode(PAYLOAD), SIZE + 1)
    if len(raw) != SIZE or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Invalid compressed payload or size')
    if hashlib.sha256(raw).hexdigest() != DIGEST:
        raise ValueError('Checksum mismatch')
    temporary = root / ('.extract_' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target, follow_symlinks=False)
        descriptor = os.open(root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)
    return str(target)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python archive.py DESTINATION_DIRECTORY')
    print(extract(sys.argv[1]))
'''


def shrink_via_zlib(module_path, archive_path=None, *, inactive=False):
    """Add standalone Python self-extractor; preserve original module bytes.

    Trusted host must explicitly attest inactive=True; loaded modules in this
    process are rejected. Extraction writes data only, never runs the module.
    Compression is lossless, but small/incompressible modules can grow after
    extractor/encoding overhead. No disk-space reclaim is claimed.
    """
    if inactive is not True:
        raise AuditRejected('Host must confirm the module is inactive')
    source=_b7_safe_path(module_path)
    if not source.is_relative_to(ROOT/'code') or source.suffix!='.py' or not source.is_file():
        raise ValueError('Existing code-category Python module required')
    for module in list(_b7_sys.modules.values()):
        location=getattr(module,'__file__',None)
        if isinstance(location,str) and Path(location).resolve()==source:
            raise AuditRejected('Module is loaded in this process')
    if source.stat().st_size>64*1024*1024:
        raise ValueError('Module exceeds64MiB limit')
    raw=source.read_bytes();digest=sha256(raw)
    compressed=_b8_zlib.compress(raw,level=9)
    payload=_b8_base64.b85encode(compressed)
    header='NAME = '+repr(source.name)+'\nSIZE = '+str(len(raw))+'\nDIGEST = '+repr(digest)+'\nPAYLOAD = '+repr(payload)+'\n\n'
    archive=(header+_B8_EXTRACTOR).encode()
    target=_b7_safe_path(archive_path or ROOT/'exports'/'shrunk_modules'/(digest+'.py'))
    if not target.is_relative_to(ROOT/'exports') or target==source:
        raise ValueError('Archive must be in exports, separate from source')
    with _b4_serial():
        if _count()+RESERVE>=STOP_AT and not target.exists():
            raise AuditRejected('Workspace file reserve exhausted')
        added=_b8_publish_new(target,archive)
    if sha256(source.read_bytes())!=digest:
        raise AuditRejected('Source changed during packing')
    return dict(path=str(target),source=str(source),sha256=digest,original_bytes=len(raw),
                zlib_bytes=len(compressed),archive_bytes=len(archive),added=added,
                source_preserved=True,reclaimed_bytes=0,
                extract_command=['python',str(target),'DESTINATION_DIRECTORY'])


def deduplicate_shared_store(projects=None, store_dir=None):
    """Add one SHA256 object per identical payload plus project-reference manifest.

    projects maps project identifiers to source path lists; default is passive
    state/shared_projects.json (missing means no inputs). Original files are
    never deleted/replaced/hardlinked. Thus the shared object store deduplicates
    newly stored copies, but original-project disk space is not reclaimed.
    Existing objects are verified byte-for-byte and corruption fails closed.
    """
    if projects is None:
        registry=_b7_safe_path('state/shared_projects.json')
        projects=json.loads(registry.read_text()) if registry.exists() else {}
    if not isinstance(projects,dict) or len(projects)>1000:
        raise ValueError('Bounded project mapping required')
    store=_b7_safe_path(store_dir or ROOT/'exports'/'shared_cas')
    if not store.is_relative_to(ROOT/'exports'):
        raise ValueError('Shared store must be in exports')
    references,objects,original_bytes=[],{},0
    for project,paths in sorted(projects.items()):
        _b7_identifier(project)
        if not isinstance(paths,list) or len(paths)>10000:
            raise ValueError('Bounded source path list required')
        seen=set()
        for value in paths:
            source=_b7_safe_path(value)
            if source.is_relative_to(store) or not source.is_file() or source.stat().st_size>64*1024*1024:
                raise ValueError('Bounded regular source outside shared store required')
            if str(source) in seen: raise ValueError('Repeated source path within project')
            seen.add(str(source))
            raw=source.read_bytes();digest=sha256(raw)
            # Only digests/paths are retained; large file bytes are not all held.
            if digest in objects and (objects[digest]['size']!=len(raw) or _b7_safe_path(objects[digest]['source']).read_bytes()!=raw):
                raise AuditRejected('Hash collision or changed source conflict')
            objects.setdefault(digest,dict(source=str(source),size=len(raw)))
            original_bytes+=len(raw)
            references.append(dict(project_id=project,source=str(source),sha256=digest,size=len(raw)))
            if len(references)>10000: raise ValueError('At most10000 references per call')
    if not references:
        return dict(manifest=None,object_count=0,objects_added=0,reclaimed_bytes=0,references=[])
    added=0
    manifest_bytes=json.dumps(dict(version=1,references=references),sort_keys=True,indent=2).encode()+b'\n'
    manifest=store/'manifests'/(sha256(manifest_bytes)+'.json')
    with _b4_serial():
        new_files=sum(not (store/'objects'/digest).exists() for digest in objects)+int(not manifest.exists())
        if new_files and _count()+new_files+RESERVE>=STOP_AT:
            raise AuditRejected('Insufficient file reserve for CAS publication')
        for digest,details in sorted(objects.items()):
            source=_b7_safe_path(details['source']);raw=source.read_bytes()
            if sha256(raw)!=digest: raise AuditRejected('Source changed during deduplication')
            added+=int(_b8_publish_new(store/'objects'/digest,raw))
        # Recheck all project references, including duplicate-content originals.
        for reference in references:
            if sha256(_b7_safe_path(reference['source']).read_bytes())!=reference['sha256']:
                raise AuditRejected('Project source changed before manifest publication')
        _b8_publish_new(manifest,manifest_bytes)
    unique_bytes=sum(item['size'] for item in objects.values())
    return dict(manifest=str(manifest),object_count=len(objects),objects_added=added,
                original_reference_bytes=original_bytes,unique_object_bytes=unique_bytes,
                duplicate_copy_bytes_avoided=original_bytes-unique_bytes,reclaimed_bytes=0,
                references=references,source_files_preserved=True)

# Batch 9: compaction, small independent runtime, profiles, durable pages, entities.
import selectors as _b9_selectors
from decimal import Decimal as _B9Decimal


def _b9_db_digest(db):
    schema=db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name").fetchall()
    records=[]
    for name, in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"):
        quoted='"'+name.replace('"','""')+'"'
        columns={row[1].lower() for row in db.execute('PRAGMA table_info('+quoted+')')}
        rowid=next((key for key in ('_rowid_','rowid','oid') if key not in columns),None)
        try:
            rows=db.execute('SELECT '+(rowid+',*' if rowid else '*')+' FROM '+quoted).fetchall()
        except sqlite3.OperationalError:
            rows=db.execute('SELECT * FROM '+quoted).fetchall()
        records.append((name,sorted(repr(row) for row in rows)))
    return sha256(repr((schema,records,db.execute('PRAGMA user_version').fetchone(),
                        db.execute('PRAGMA application_id').fetchone())).encode())


def compact_sqlite_db(db_path='state/prompt_engine.db', *, quiesced=False):
    """Checkpoint(TRUNCATE), VACUUM, verify records/schema/rowids; restore on failure.

    Host must quiesce every writer/reader and explicitly pass quiesced=True.
    The cooperating release lock is not an OS-wide database maintenance lease.
    An online SQLite backup in /tmp permits rollback if VACUUM renumbers hidden
    rowids. No original user table is deleted or recreated by application SQL.
    Physical file bytes necessarily change during successful compaction.
    """
    if quiesced is not True: raise AuditRejected('Explicit quiesced database required')
    path=_b7_safe_path(db_path)
    if not path.is_file(): raise ValueError('Existing SQLite database required')
    with _b4_serial(),_b7_tempfile.TemporaryDirectory(prefix='apccs_b9_vacuum_',dir='/tmp') as scratch:
        db=sqlite3.connect(path,timeout=0,isolation_level=None)
        backup=sqlite3.connect(str(Path(scratch)/'before.db'),isolation_level=None)
        backed=False;mutated=False
        try:
            db.execute('PRAGMA busy_timeout=0')
            if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
                raise AuditRejected('Database integrity check failed before compaction')
            before_hash=_b9_db_digest(db)
            before=path.stat().st_size
            before_wal=Path(str(path)+'-wal').stat().st_size if Path(str(path)+'-wal').exists() else 0
            db.backup(backup);backed=True
            checkpoint=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
            if checkpoint[0]!=0:
                raise AuditRejected('WAL checkpoint busy; maintenance refused')
            mutated=True
            db.execute('VACUUM')
            final_checkpoint=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
            if final_checkpoint[0]!=0 or db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
                raise AuditRejected('Post-compaction checkpoint/integrity failure')
            if _b9_db_digest(db)!=before_hash:
                raise AuditRejected('VACUUM changed record identity or schema')
            after=path.stat().st_size
            return dict(status='GREEN',path=str(path),checkpoint=list(checkpoint),
                        final_checkpoint=list(final_checkpoint),before_db_bytes=before,
                        before_wal_bytes=before_wal,after_db_bytes=after,
                        reclaimed_db_bytes=max(0,before-after),records_preserved=True,
                        logical_digest=before_hash)
        except BaseException:
            if backed and mutated:
                backup.backup(db)
                db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                if _b9_db_digest(db)!=before_hash:
                    raise AuditRejected('Compaction rollback verification failed')
            raise
        finally:
            backup.close();db.close()


_B9_MICROKERNEL = '''import json
import os
from pathlib import Path
import sqlite3
import sys


def request(vault, command):
    root = Path(vault).absolute()
    if root.resolve() != root or root.is_symlink():
        raise ValueError('Vault symlink forbidden')
    state = root / 'state'
    if state.is_symlink() or state.resolve() != state:
        raise ValueError('State directory symlink forbidden')
    if command.get('op') == 'status':
        databases = []
        for name in ('prompt_engine.db', 'batch2.db'):
            path = root / 'state' / name
            if path.is_symlink():
                raise ValueError('Database symlink forbidden')
            if path.exists():
                connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
                try:
                    count = connection.execute("SELECT count(*) FROM sqlite_schema WHERE type='table'").fetchone()[0]
                    databases.append(dict(name=name, tables=count))
                finally:
                    connection.close()
        return dict(status='READY', databases=databases, pid=os.getpid(),
                    kernel_bytes=Path(__file__).stat().st_size,
                    full_core_loaded='apccs_core' in sys.modules, channels=1)
    if command.get('op') == 'read_checkpoint':
        path = root / 'state' / 'microkernel_checkpoint.json'
        if path.is_symlink():
            raise ValueError('Checkpoint symlink forbidden')
        return dict(checkpoint=json.loads(path.read_text()) if path.exists() else None)
    raise ValueError('Unsupported microkernel operation')


def main():
    vault = sys.argv[1]
    if len(sys.argv) == 3 and sys.argv[2] == 'serve':
        print(json.dumps(request(vault, dict(op='status'))), flush=True)
        for line in sys.stdin:
            try:
                command = json.loads(line)
                result = request(vault, command)
            except (ValueError, OSError, sqlite3.Error) as error:
                result = dict(error=str(error))
            print(json.dumps(result), flush=True)
    else:
        print(json.dumps(request(vault, dict(op='status'))))


if __name__ == '__main__':
    main()
'''


class FeatherweightSession:
    """Independent microkernel child. Caller must stop the full host for only-mode."""
    def __init__(self,path):
        self.process=_b7_subprocess.Popen([_b7_sys.executable,'-I','-B',str(path),str(ROOT),'serve'],
            stdin=_b7_subprocess.PIPE,stdout=_b7_subprocess.PIPE,stderr=_b7_subprocess.DEVNULL)
        self._pending=b''
        try:
            self.receipt=self._read()
            if self.receipt.get('full_core_loaded') or self.receipt.get('kernel_bytes',35000)>=35000:
                raise AuditRejected('Microkernel startup verification failed')
        except BaseException:
            self.close();raise

    def _read(self):
        selector=_b9_selectors.DefaultSelector()
        try:
            selector.register(self.process.stdout,_b9_selectors.EVENT_READ)
            while b'\n' not in self._pending:
                if not selector.select(20): raise TimeoutError('Microkernel response timeout')
                chunk=os.read(self.process.stdout.fileno(),65536)
                if not chunk: raise AuditRejected('Microkernel process closed')
                self._pending+=chunk
                if len(self._pending)>1048576: raise AuditRejected('Microkernel response too large')
            line,self._pending=self._pending.split(b'\n',1)
            return json.loads(line)
        finally:
            selector.close()

    def request(self,command):
        self.process.stdin.write(json.dumps(command).encode()+b'\n');self.process.stdin.flush()
        return self._read()

    def close(self):
        if self.process.stdin: self.process.stdin.close()
        try: self.process.wait(timeout=3)
        except _b7_subprocess.TimeoutExpired:
            self.process.terminate()
            try: self.process.wait(timeout=3)
            except _b7_subprocess.TimeoutExpired:
                self.process.kill();self.process.wait()
        if self.process.stdout:self.process.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        self.close();return False


def enable_featherweight_mode(*, launch=False):
    """Publish a real <35000-byte standalone kernel; optionally start its session.

    Kernel mounts existing state read-only and reads recovery checkpoints. It
    imports no canonical core and provides no arbitrary code/tool execution.
    The full canonical file remains byte-identical on disk. Python/stdlib RAM
    and total vault storage are not limited to35KB. This calling process still
    has the full core loaded; host must retire it and route work to the kernel
    to make that kernel the sole active application runtime.
    """
    if type(launch) is not bool: raise ValueError('Boolean launch flag required')
    raw=_B9_MICROKERNEL.encode()
    if len(raw)>=35000: raise AuditRejected('Microkernel exceeds35KB source budget')
    path=_b7_safe_path(ROOT/'exports'/'featherweight'/('kernel_'+sha256(raw)+'.py'))
    with _b4_serial():
        _b8_publish_new(path,raw)
    if launch:return FeatherweightSession(path)
    return dict(path=str(path),kernel_bytes=len(raw),kernel_sha256=sha256(raw),
                channels=1,active_in_this_process=False,host_restart_required=True,
                launch_command=[_b7_sys.executable,'-I','-B',str(path),str(ROOT),'serve'])


def select_hardware_profile(storage=None, compute=None):
    """Select capacity tier from current sensor receipts; no workers launched.

    Tier thresholds: Featherweight fallback; Mobile >=512MB free/3 dispatch
    slots, High-Velocity >=2GB/8 slots, Max Swarm >=8GB/20 slots. Sensors must
    provide numeric free bytes and available dispatch slots; unknown means
    Featherweight with dispatch disabled. Channels is the named tier size.
    """
    storage=scan_device_storage() if storage is None else storage
    compute=scan_compute_headroom() if compute is None else compute
    if not isinstance(storage,dict) or not isinstance(compute,dict):
        raise ValueError('Sensor receipt objects required')
    free=storage.get('disk_free_bytes');slots=compute.get('dispatch_slots')
    valid=type(free) is int and free>=0 and type(slots) is int and slots>=0
    allowed=valid and compute.get('dispatch_allowed') is True and slots>0 and free>0
    name,channels='Featherweight',1
    if allowed:
        for label,size,threshold in [('Standard Mobile',3,512_000_000),('High-Velocity',8,2_000_000_000),('Max Swarm',20,8_000_000_000)]:
            if slots>=size and free>=threshold:name,channels=label,size
    return dict(profile=name,channels=channels,dispatch_allowed=bool(allowed),
                dispatch_slots=channels if allowed else 0,featherweight_required=name=='Featherweight',
                disk_free_bytes=free,headroom_dispatch_slots=slots,profile_applied=False)


def _b9_pages(text):
    pages=[];current=[];size=0
    for character in text:
        weight=len(character.encode('utf-8'))
        if size+weight>1200:
            pages.append(''.join(current));current=[];size=0
        current.append(character);size+=weight
    if current or not pages:pages.append(''.join(current))
    return pages


def search_paginated_chunks(results=None, search_id='default', acknowledge=None,
                            db_path='state/b9_search_pages.db'):
    """Persist all text, return next unacknowledged page with durable cursor.

    No tokenizer dependency: each page <=1200 UTF8 bytes, a conservative byte
    budget, not a claim of1200 measured model tokens. Character/whitespace
    boundaries are preserved exactly; concatenation reconstructs the source.
    acknowledge is {index,sha256} for the currently pending page. Acknowledging
    commits its cursor and returns the next page; stale/mismatched ACKs fail.
    An ID's source is immutable. Inputs >16MiB are rejected, never truncated.
    """
    _b7_identifier(search_id)
    if results is not None and (not isinstance(results,str) or len(results.encode())>16*1024*1024):
        raise ValueError('Text source of at most16MiB required')
    with _b7_transaction(db_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS b9_searches (search_id TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL, total_pages INTEGER NOT NULL, next_page INTEGER NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS b9_pages (search_id TEXT NOT NULL, page_index INTEGER NOT NULL, body TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(search_id,page_index))')
        row=db.execute('SELECT source_sha256,total_pages,next_page FROM b9_searches WHERE search_id=?',(search_id,)).fetchone()
        if row is None:
            if results is None: raise AuditRejected('Unknown search snapshot')
            pages=_b9_pages(results);digest=sha256(results.encode())
            db.execute('INSERT INTO b9_searches VALUES (?,?,?,0)',(search_id,digest,len(pages)))
            db.executemany('INSERT INTO b9_pages VALUES (?,?,?,?)',[(search_id,i,page,sha256(page.encode())) for i,page in enumerate(pages)])
            row=(digest,len(pages),0)
        if results is not None and sha256(results.encode())!=row[0]:
            raise AuditRejected('Existing search snapshot cannot be overwritten')
        pages=db.execute('SELECT page_index,body,sha256 FROM b9_pages WHERE search_id=? ORDER BY page_index',(search_id,)).fetchall()
        if len(pages)!=row[1] or any(i!=index or sha256(body.encode())!=digest for index,(i,body,digest) in enumerate(pages)) or sha256(''.join(p[1] for p in pages).encode())!=row[0]:
            raise AuditRejected('Search snapshot integrity failure')
        cursor=row[2]
        if acknowledge is not None:
            if not isinstance(acknowledge,dict) or set(acknowledge)!={'index','sha256'} or type(acknowledge['index']) is not int or cursor>=len(pages) or acknowledge['index']!=cursor or acknowledge['sha256']!=pages[cursor][2]:
                raise AuditRejected('Stale or invalid page acknowledgment')
            cursor+=1
            db.execute('UPDATE b9_searches SET next_page=? WHERE search_id=?',(cursor,search_id))
        done=cursor==len(pages)
        return dict(search_id=search_id,source_sha256=row[0],total_pages=len(pages),
                    checkpoint=cursor,done=done,page_index=None if done else cursor,
                    text='' if done else pages[cursor][1],page_sha256=None if done else pages[cursor][2],
                    token_budget=1200,token_measure='UTF8_BYTE_UPPER_BOUND',
                    page_utf8_bytes=0 if done else len(pages[cursor][1].encode()))


def detect_potluck_entities(text):
    """Deterministic explicit dates/money/ports/task markers, with exact spans.

    Date ambiguity is labeled; no inferred intent or relative-date resolution.
    Financial values use Decimal text. Action items require TODO/ACTION/NEXT
    STEP or unchecked checkbox markers. This does not perform semantic NLP.
    """
    if not isinstance(text,str) or len(text.encode())>16*1024*1024:
        raise ValueError('Bounded text required')
    output=dict(dates=[],dollar_amounts=[],ports=[],action_items=[])
    patterns=[(r'\b\d{4}-\d{2}-\d{2}\b','ISO'),
              (r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b','MONTH_NAME'),
              (r'\b\d{1,2}/\d{1,2}/\d{4}\b','AMBIGUOUS_NUMERIC')]
    for pattern,kind in patterns:
        for match in re.finditer(pattern,text,re.IGNORECASE):
            raw=match.group();normalized=None
            try:
                if kind=='ISO':normalized=dt.date.fromisoformat(raw).isoformat()
                elif kind=='MONTH_NAME':
                    parts=raw.replace(',','').split();month=('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec').index(parts[0][:3].lower())+1
                    normalized=dt.date(int(parts[2]),month,int(parts[1])).isoformat()
                else:
                    first,second,year=map(int,raw.split('/'))
                    valid=[]
                    for month,day in ((first,second),(second,first)):
                        try:valid.append(dt.date(year,month,day).isoformat())
                        except ValueError:continue
                    if not valid:continue
                    if len(set(valid))==1:normalized=valid[0]
            except ValueError:continue
            output['dates'].append(dict(raw=raw,start=match.start(),end=match.end(),format=kind,iso_date=normalized))
    money=r'(?<![\w$])(?:(?:CAD|USD)\s*)?(?:US\$|C\$|\$)\s*-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?(?!(?:\d|[.,]\d))'
    for match in re.finditer(money,text,re.IGNORECASE):
        raw=match.group();number=re.search(r'-?[\d,]+(?:\.\d+)?',raw).group().replace(',','')
        currency='CAD' if 'CAD' in raw.upper() or raw.upper().startswith('C$') else 'USD' if 'USD' in raw.upper() or raw.upper().startswith('US$') else 'UNSPECIFIED_DOLLAR'
        output['dollar_amounts'].append(dict(raw=raw,start=match.start(),end=match.end(),amount=str(_B9Decimal(number)),currency=currency))
    found={}
    for match in re.finditer(r'\bports?\s*[:=]?\s*(\d{1,5}(?:\s*,\s*\d{1,5})*)(?!\d)',text,re.IGNORECASE):
        for number in re.finditer(r'\d+',match.group(1)):
            start=match.start(1)+number.start();end=match.start(1)+number.end();value=int(number.group())
            if 0<=value<=65535:found[(start,end)]=dict(raw=text[start:end],start=start,end=end,port=value)
    for match in re.finditer(r'(?:https?://[A-Za-z0-9.-]+|localhost|127\.0\.0\.1):(\d{1,5})(?!\d)',text,re.IGNORECASE):
        value=int(match.group(1));start,end=match.span(1)
        if 0<=value<=65535:found[(start,end)]=dict(raw=text[start:end],start=start,end=end,port=value)
    output['ports']=[found[key] for key in sorted(found)]
    action=r'^[ \t]*(?:[-*][ \t]*)?(?:\[[ \t]*\][ \t]*|(?:TODO|ACTION(?: ITEM)?|NEXT STEP)[ \t]*:[ \t]*)([^\r\n]+)'
    for match in re.finditer(action,text,re.IGNORECASE|re.MULTILINE):
        start,end=match.span(1)
        output['action_items'].append(dict(raw=text[start:end],start=start,end=end,action=match.group(1).strip()))
    output['dates'].sort(key=lambda row:row['start'])
    return output

# Batch 10: evidence-based mirrors, plain-text recovery, timed tests and CP-050.
import signal as _b10_signal


_B10_MIRRORS=('Local Disk','Master ZIP','Browser Export','Shared Google Drive Folder')


def sync_four_mirrors(mirrors=None, expected_sha256=None):
    """Track four mirror observations; never invent browser/Drive access.

    Mapping values may contain path, provider_url and host_receipt. Paths are
    locally hashed copies; remote mirror freshness remains HOST_ATTESTED or
    UNVERIFIED because standard-library code has no connected-app authority.
    Tracking does not perform uploads, browser exports or overwrite a mirror.
    """
    if mirrors is None:
        path=_b7_safe_path('state/four_mirrors.json')
        mirrors=json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(mirrors,dict) or set(mirrors)-set(_B10_MIRRORS):
        raise ValueError('Only the four named mirror observations are allowed')
    if expected_sha256 is not None and (not isinstance(expected_sha256,str) or re.fullmatch('[0-9a-f]{64}',expected_sha256) is None):
        raise ValueError('Expected SHA256 required')
    observations=[]
    for name in _B10_MIRRORS:
        entry=mirrors.get(name,{})
        if not isinstance(entry,dict):raise ValueError('Mirror observation must be an object')
        item=dict(mirror=name,state='UNVERIFIED',sha256=None,bytes=None,
                  remote_freshness='NOT_APPLICABLE' if name in _B10_MIRRORS[:2] else 'UNVERIFIED')
        if entry.get('path') is not None:
            try:
                path=_b7_safe_path(entry['path']);data=path.read_bytes()
                item.update(path=str(path),sha256=sha256(data),bytes=len(data),state='VERIFIED_LOCAL_BYTES')
                if expected_sha256 and item['sha256']!=expected_sha256:item['state']='MISMATCH'
            except (OSError,ValueError,TypeError) as error:item.update(state='UNAVAILABLE',reason=str(error))
        if name in _B10_MIRRORS[2:] and entry.get('host_receipt'):
            item['remote_freshness']='HOST_ATTESTED_NOT_INDEPENDENTLY_VERIFIED'
            item['host_receipt']=str(entry['host_receipt'])[:4096]
        if entry.get('provider_url'):item['provider_url']=str(entry['provider_url'])[:4096]
        observations.append(item)
    with _b7_transaction('state/b10_mirrors.db') as db:
        db.execute('CREATE TABLE IF NOT EXISTS b10_mirror_events (event_sha256 TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        payload=json.dumps(observations,sort_keys=True)
        db.execute('INSERT OR IGNORE INTO b10_mirror_events VALUES (?,?)',(sha256(payload.encode()),payload))
    hashes=[item['sha256'] for item in observations]
    return dict(observations=observations,all_local_copies_match=all(hashes) and len(set(hashes))==1 and all(item['state']=='VERIFIED_LOCAL_BYTES' for item in observations),
                all_remote_mirrors_verified=False,external_writes=0)


_B10_HANDOFF_LOADER='''import hashlib
import json
import os
from pathlib import Path
import sys
import uuid


def mount(destination):
    root = Path(destination).absolute()
    if root.resolve() != root or root.is_symlink():
        raise ValueError('Symlink destination forbidden')
    verified = []
    for name, record in FILES.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError('Unsafe handoff member')
        raw = record['text'].encode('utf-8')
        if hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('Handoff checksum mismatch')
        target = root / relative
        for part in (target, *target.parents):
            if part.is_symlink():
                raise ValueError('Symlink handoff destination forbidden')
        if target.exists() and target.read_bytes() != raw:
            raise ValueError('Existing record differs; refuse replacement')
        verified.append((target, raw))
    mounted = 0
    added = 0
    for target, raw in verified:
        if target.exists():
            mounted += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / ('.handoff_' + uuid.uuid4().hex)
        try:
            with temporary.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target, follow_symlinks=False)
                added += 1
            except FileExistsError:
                if target.is_symlink() or target.read_bytes() != raw:
                    raise ValueError('Concurrent handoff conflict')
                mounted += 1
        finally:
            temporary.unlink(missing_ok=True)
    return dict(verified=len(verified), added=added, mounted=mounted)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python HANDOFF.py EMPTY_OR_IDENTICAL_DESTINATION')
    print(json.dumps(mount(sys.argv[1]), sort_keys=True))
'''


def export_plain_text_handoff(files=None, destination=None):
    """Plain Python literals plus independent SHA256 mount/verify code; no encoding.

    Default exports canonical source/tests as UTF8 text. Existing destinations
    mount only if byte-identical. This is source recovery, not execution of the
    recovered core or restored databases. Authentication of the handoff itself
    remains the host's responsibility; checksums detect altered payload text.
    """
    files=['code/apccs_core.py','code/test_apccs_core.py'] if files is None else files
    if not isinstance(files,list) or not files or len(files)>1000:raise ValueError('Bounded nonempty file list required')
    records={}
    for value in files:
        path=_b7_safe_path(value);name=path.relative_to(ROOT).as_posix()
        if name in records:raise ValueError('Duplicate handoff member')
        raw=path.read_bytes()
        if len(raw)>16*1024*1024:raise ValueError('Text member exceeds16MiB')
        records[name]=dict(text=raw.decode('utf-8'),sha256=sha256(raw))
    text='FILES = '+repr(records)+'\n\n'+_B10_HANDOFF_LOADER
    raw=text.encode();digest=sha256(raw)
    target=_b7_safe_path(destination or ROOT/'exports'/'plain_handoffs'/(digest+'.py'))
    if not target.is_relative_to(ROOT/'exports'):raise ValueError('Handoff output must be in exports')
    with _b4_serial():_b8_publish_new(target,raw)
    return dict(path=str(target),sha256=digest,bytes=len(raw),members=len(records),text=text,
                restored_code_executed=False)


def _b10_test_groups(source):
    tree=_b6_ast.parse(source)
    groups=[node.name for node in tree.body if isinstance(node,_b6_ast.ClassDef) and any(isinstance(child,_b6_ast.FunctionDef) and child.name.startswith('test_') for child in node.body)]
    if not groups or len(groups)!=len(set(groups)) or len(groups)>50:
        raise ValueError('Unique installed unittest classes required')
    return groups


def run_all_installed_unit_tests(test_path='code/test_apccs_core.py', *, timeout_sec=4.9):
    """Run actual installed unittest classes in isolated parallel processes.

    Total elapsed includes source copy, child startup, all assertions and temp
    cleanup. >=5seconds or a timeout fails; no cached receipt or fast substitute
    is counted. Installed tests must implement --installed-worker and return
    executed IDs/observations. Each instruction1..50 needs a passed test ID.
    Host-approved test code is not an OS sandbox. Runtime depends on hardware.
    """
    if type(timeout_sec) not in (int,float) or not 0<timeout_sec<5:
        raise ValueError('Deadline must be positive and strictly below5seconds')
    started=_b8_time.monotonic();deadline=started+timeout_sec
    source_path=Path(__file__);test_path=_b7_safe_path(test_path)
    source=source_path.read_bytes();tests=test_path.read_bytes();groups=_b10_test_groups(tests.decode())
    workers=[];results=[];failures=[];observations={};ids=[]
    with _b7_tempfile.TemporaryDirectory(prefix='apccs_b10_alltests_',dir='/tmp') as scratch:
        directory=Path(scratch)
        (directory/'apccs_core.py').write_bytes(source);(directory/'test_apccs_core.py').write_bytes(tests)
        try:
            for index,group in enumerate(groups):
                output=directory/(str(index)+'.json')
                process=_b7_subprocess.Popen([_b7_sys.executable,'-B',str(directory/'test_apccs_core.py'),
                    '--installed-worker',group,str(output)],cwd=directory,
                    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',APCCS_SELFTEST_WORKER='1'),
                    stdout=_b7_subprocess.DEVNULL,stderr=_b7_subprocess.DEVNULL,start_new_session=True)
                workers.append((group,process,output))
            for group,process,output in workers:
                process.wait(timeout=max(.001,deadline-_b8_time.monotonic()))
                if not output.exists():
                    failures.append(dict(test=group,traceback='Worker produced no test receipt'));continue
                result=json.loads(output.read_text());results.append(result)
                failures.extend(result.get('failed_assertions',[]));observations.update(result.get('observations',{}));ids.extend(result.get('executed_test_ids',[]))
                if process.returncode!=0 or not result.get('passed') or result.get('skipped',0):
                    failures.append(dict(test=group,traceback='Worker failed or skipped installed tests'))
        except _b7_subprocess.TimeoutExpired:
            failures.append(dict(test='INST-0048',traceback='Installed tests exceeded deadline'))
        finally:
            for group,process,output in workers:
                if process.poll() is None:
                    try:os.killpg(process.pid,_b10_signal.SIGKILL)
                    except ProcessLookupError:continue
                process.wait()
    elapsed=_b8_time.monotonic()-started
    coverage=sorted({int(match.group(1)) for identity in ids for match in [re.search(r'\.test_(\d{2})(?:_|$)',identity)] if match and 1<=int(match.group(1))<=50})
    if coverage!=list(range(1,51)):failures.append(dict(test='INST-0048',traceback='Not every installed instruction1..50 executed'))
    if elapsed>=5:failures.append(dict(test='INST-0048',traceback='Total elapsed including cleanup >=5seconds'))
    unchanged=source_path.read_bytes()==source and test_path.read_bytes()==tests
    if not unchanged:failures.append(dict(test='INST-0048',traceback='Installed source/tests changed during run'))
    return dict(passed=not failures,all_unit_tests_passed=not failures,tests_run=sum(r.get('tests_run',0) for r in results),
                failed_assertions=failures,elapsed_seconds=elapsed,under_5_seconds=elapsed<5,
                executed_test_ids=ids,instruction_coverage=coverage,groups=results,observations=observations,
                core_sha256=sha256(source),test_sha256=sha256(tests),scratch_removed=not Path(scratch).exists(),
                installed_files_unchanged=unchanged,canary='Canary check: M = K -> submarine')


def print_owner_scorecard(test_report=None, completed=50):
    """Return readable table and print it; never relabel legacy GRAY evidence."""
    _b7_integer(completed,'Completed instruction count')
    if completed>50:raise ValueError('Loaded catalog ends at50')
    if test_report is None:test_report=json.loads(_b7_safe_path('audit/pass_tests.json').read_text())
    if not isinstance(test_report,dict):raise ValueError('Test receipt required')
    observations=test_report.get('observations',{})
    rows=['Instruction | Test result','------------|------------']
    for number in range(1,completed+1):
        item=observations.get('INST-'+str(number).zfill(4),{})
        status=item.get('status','UNVERIFIED')
        if number in test_report.get('instruction_coverage',[]) and not item:status='PASS (installed test)'
        rows.append(str(number).rjust(3)+'/1000 | '+str(status))
    rows.extend(['','Completed: '+str(completed)+'/1000',
                 'Tests executed: '+str(test_report.get('tests_run','UNVERIFIED')),
                 'Failed assertions: '+str(len(test_report.get('failed_assertions',[]))),
                 'Workspace file count: '+str(_count()),
                 'Accepted checkpoint: '+str(test_report.get('accepted_checkpoint','UNVERIFIED'))])
    text='\n'.join(rows)+'\n';print(text,end='');return text


def lock_checkpoint_50(archive_path,test_report):
    """Seal CP-050 local-test evidence into Master; Muse acceptance stays separate.

    Requires actual host-provided runner receipt for matching canonical bytes,
    all50 instructions, no failures, all assertions executed within5seconds.
    Receipt authenticity is a trusted-host boundary, not a signed attestation.
    Existing unequal CP-050 lock is immutable and cannot be replaced.
    """
    path=_b7_safe_path(archive_path)
    if not isinstance(test_report,dict) or test_report.get('passed') is not True or test_report.get('failed_assertions')!=[] or test_report.get('instruction_coverage')!=list(range(1,51)) or test_report.get('under_5_seconds') is not True or not 0<=test_report.get('elapsed_seconds',5)<5:
        raise AuditRejected('Complete passing under-five-second installed test receipt required')
    with _b4_serial():
        with zipfile.ZipFile(path) as saved:
            names=saved.namelist()
            if len(names)!=len(set(names)) or saved.testzip() is not None:raise AuditRejected('Invalid Master archive')
            if any(Path(name).is_absolute() or '..' in Path(name).parts or name.endswith('.zip') for name in names):raise AuditRejected('Unsafe or nested Master member')
            members={name:saved.read(name) for name in names}
        if sha256(members['code/apccs_core.py'])!=test_report.get('core_sha256') or sha256(members['code/test_apccs_core.py'])!=test_report.get('test_sha256'):
            raise AuditRejected('Tested source/test digest differs from Master')
        if 'audit/CP-050_LOCK.json' not in members and 'RECOVERY_MANIFEST.json' in members:
            previous=members['RECOVERY_MANIFEST.json']
            members['history/pre_CP050_manifest_'+sha256(previous)+'.json']=previous
        excluded={'audit/CP-050_LOCK.json','RECOVERY_MANIFEST.json'}
        lock=dict(checkpoint='CP-050',locally_verified_instructions=50,total_instructions=1000,
                  verification_scope='LOCAL_INSTALLED_TESTS_PENDING_MUSE_ACCEPTANCE',
                  core_sha256=test_report['core_sha256'],test_sha256=test_report['test_sha256'],
                  tests_run=test_report['tests_run'],elapsed_seconds=test_report['elapsed_seconds'],
                  instruction_coverage=test_report['instruction_coverage'],
                  member_hashes={name:sha256(raw) for name,raw in sorted(members.items()) if name not in excluded})
        raw=(json.dumps(lock,sort_keys=True,indent=2)+'\n').encode()
        if 'audit/CP-050_LOCK.json' in members:
            if members['audit/CP-050_LOCK.json']!=raw:raise AuditRejected('CP-050 is already locked to different evidence')
            return lock
        members['audit/CP-050_LOCK.json']=raw
        manifest=dict(build_id='B10_CP050_20261028',files={name:dict(size=len(data),sha256=sha256(data)) for name,data in sorted(members.items()) if name!='RECOVERY_MANIFEST.json'})
        members['RECOVERY_MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
        temporary=path.parent/('.cp050_'+uuid.uuid4().hex)
        try:
            with zipfile.ZipFile(temporary,'x',zipfile.ZIP_DEFLATED) as output:
                for name,data in members.items():output.writestr(name,data)
            with temporary.open('rb') as stream:os.fsync(stream.fileno())
            os.replace(temporary,path)
        finally:temporary.unlink(missing_ok=True)
    print('CP-050: 50/1000 local installed tests verified; Muse acceptance pending.')
    return lock

# Batch 11: validated manifests, immutable rulebooks and transactional engine state.
import unicodedata as _b11_unicode


_B11_MANAGED={'engine_registry_v2','engine_rules_hashes','b11_manifests','b11_rulebooks',
              'b11_sessions','b11_session_history','b11_upgrade_rollbacks'}


def _b11_semver(value):
    if not isinstance(value,str) or len(value)>128:
        raise ValueError('Bounded semantic version string required')
    match=re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?',value)
    if match is None:raise ValueError('Semantic version must be MAJOR.MINOR.PATCH with optional prerelease/build')
    prerelease=match.group(4).split('.') if match.group(4) else []
    if any(part.isdigit() and len(part)>1 and part.startswith('0') for part in prerelease):
        raise ValueError('Numeric prerelease identifiers cannot have leading zeros')
    return tuple(map(int,match.group(1,2,3))),prerelease


def _b11_compare_versions(left,right):
    main_a,pre_a=_b11_semver(left);main_b,pre_b=_b11_semver(right)
    if main_a!=main_b:return 1 if main_a>main_b else -1
    if not pre_a or not pre_b:return 0 if pre_a==pre_b else 1 if not pre_a else -1
    for a,b in zip(pre_a,pre_b):
        if a==b:continue
        if a.isdigit() and b.isdigit():return 1 if int(a)>int(b) else -1
        if a.isdigit()!=b.isdigit():return -1 if a.isdigit() else 1
        return 1 if a>b else -1
    return 0 if len(pre_a)==len(pre_b) else 1 if len(pre_a)>len(pre_b) else -1


def validate_engine_manifest(manifest_dict):
    """Validate data only; entry_point is a reference, never imported/executed.

    Required six keys, schema_version=1, strict SemVer2.0 and module:callable
    identifier syntax. Additional JSON-native metadata is retained. New Batch11
    load/switch/upgrade paths call this validator; untouched legacy APIs still
    require their host to opt into the validated adapter.
    """
    errors=[]
    required={'engine_id','name','version','rules_text','schema_version','entry_point'}
    if not isinstance(manifest_dict,dict):return dict(passed=False,status='RED',errors=['Manifest object required'])
    missing=sorted(required-set(manifest_dict))
    if missing:return dict(passed=False,status='RED',errors=['Missing keys: '+', '.join(missing)])
    try:_b7_identifier(manifest_dict['engine_id'])
    except ValueError as error:errors.append(str(error))
    name=manifest_dict['name'];rules=manifest_dict['rules_text'];entry=manifest_dict['entry_point']
    if not isinstance(name,str) or not name.strip() or len(name)>256:errors.append('Nonempty name <=256 characters required')
    if not isinstance(rules,str) or not rules.strip():errors.append('Nonempty rules text required')
    else:
        try:
            if len(rules.encode())>1048576:errors.append('Rules exceed one MiB')
        except UnicodeError:errors.append('Rules must encode as UTF8')
    try:_b11_semver(manifest_dict['version'])
    except ValueError as error:errors.append(str(error))
    if type(manifest_dict['schema_version']) is not int or manifest_dict['schema_version']!=1:errors.append('Supported schema_version is integer1')
    if not isinstance(entry,str) or len(entry)>256 or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*',entry) is None:
        errors.append('entry_point must be module:callable identifiers')
    try:
        serialized=json.dumps(manifest_dict,sort_keys=True,allow_nan=False)
        if json.loads(serialized)!=manifest_dict:errors.append('JSON-native manifest values required')
    except (ValueError,TypeError,RecursionError):errors.append('Finite JSON-native metadata required')
    if errors:return dict(passed=False,status='RED',errors=errors)
    return dict(passed=True,status='GREEN',errors=[],manifest=json.loads(serialized),
                manifest_sha256=sha256(serialized.encode()))


def compile_engine_rulebook(engine_id,rules_text):
    """Pure deterministic compiler; NFC, whitespace, numbering and duplicate removal.

    Raw original rules remain in the engine registry. The numbered normalized
    representation is for mounting/delivery; no rule text is interpreted as code.
    Identical normalized clauses appear once, preserving first-occurrence order.
    """
    _b7_identifier(engine_id)
    if not isinstance(rules_text,str) or not rules_text.strip() or len(rules_text.encode())>1048576:
        raise ValueError('Nonempty rules text of at most one MiB required')
    clauses=[];seen=set()
    for line in _b11_unicode.normalize('NFC',rules_text).splitlines():
        text=re.sub(r'^\s*(?:[0-9]+[.)]|[-*•])\s+','',line)
        text=' '.join(text.split())
        if not text or text in seen:continue
        seen.add(text);clauses.append(dict(number=len(clauses)+1,text=text,sha256=sha256(text.encode())))
    if not clauses:raise ValueError('No nonempty clauses after normalization')
    numbered='\n'.join(str(clause['number'])+'. '+clause['text'] for clause in clauses)
    return dict(engine_id=engine_id,clauses=clauses,numbered_rules=numbered,
                rulebook_sha256=sha256(numbered.encode()),raw_rules_sha256=sha256(rules_text.encode()))


def _b11_table_snapshot(db,table_name):
    if not isinstance(table_name,str) or not table_name or '\x00' in table_name or len(table_name)>256:
        raise ValueError('Bounded table name required')
    row=db.execute("SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",(table_name,)).fetchone()
    if row is None:raise AuditRejected('Protected user table is missing')
    quoted='"'+table_name.replace('"','""')+'"'
    columns=db.execute('PRAGMA table_info('+quoted+')').fetchall()
    names={item[1].lower() for item in columns}
    alias=next((name for name in ('_rowid_','rowid','oid') if name not in names),None)
    try:rows=db.execute('SELECT '+(alias+',*' if alias else '*')+' FROM '+quoted).fetchall()
    except sqlite3.OperationalError:rows=db.execute('SELECT * FROM '+quoted).fetchall()
    digest=sha256(repr((row[0],columns,sorted(repr(item) for item in rows))).encode())
    return dict(snapshot_version=1,table_name=table_name,row_count=len(rows),sha256=digest)


def capture_user_data_snapshot(db_path,table_name):
    """Read-only schema/row/multiplicity/hidden-rowid snapshot for the guard."""
    path=_b7_safe_path(db_path)
    if not path.is_file():raise ValueError('Existing database required')
    with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        return _b11_table_snapshot(db,table_name)


def verify_user_data_untouched(db_path,table_name,before_snapshot):
    """Detect any current schema/row/rowid change relative to captured evidence.

    This is a verifier, not an OS-wide prohibition on independent writers.
    Batch11 managed operations additionally deny user-table writes and verify
    all protected snapshots inside the same SQLite write transaction.
    """
    if not isinstance(before_snapshot,dict) or before_snapshot.get('snapshot_version')!=1 or before_snapshot.get('table_name')!=table_name or not isinstance(before_snapshot.get('sha256'),str) or re.fullmatch('[0-9a-f]{64}',before_snapshot['sha256']) is None:
        raise ValueError('Matching captured table snapshot required')
    try:current=capture_user_data_snapshot(db_path,table_name)
    except (AuditRejected,sqlite3.Error) as error:return dict(passed=False,status='RED',reason=str(error),table_name=table_name)
    passed=current==before_snapshot
    return dict(passed=passed,status='GREEN' if passed else 'RED',table_name=table_name,
                before=before_snapshot,current=current)


def _b11_schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS engine_registry_v2 (engine_id TEXT PRIMARY KEY, name TEXT NOT NULL, rules_text TEXT NOT NULL, version TEXT NOT NULL, sha256 TEXT NOT NULL, state TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS engine_rules_hashes (engine_id TEXT PRIMARY KEY REFERENCES engine_registry_v2(engine_id), rules_sha256 TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b11_manifests (engine_id TEXT PRIMARY KEY REFERENCES engine_registry_v2(engine_id), manifest TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b11_rulebooks (engine_id TEXT NOT NULL, rulebook_sha256 TEXT NOT NULL, compiled TEXT NOT NULL, PRIMARY KEY(engine_id,rulebook_sha256))')
    db.execute('CREATE TABLE IF NOT EXISTS b11_sessions (session_id TEXT PRIMARY KEY, engine_id TEXT NOT NULL REFERENCES engine_registry_v2(engine_id), version TEXT NOT NULL, rulebook_sha256 TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b11_session_history (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, engine_id TEXT NOT NULL, version TEXT NOT NULL, rulebook_sha256 TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS b11_upgrade_rollbacks (rollback_id TEXT PRIMARY KEY, engine_id TEXT NOT NULL, from_version TEXT NOT NULL, to_version TEXT NOT NULL, prior_snapshot TEXT NOT NULL, new_engine_sha256 TEXT NOT NULL)')


@contextlib.contextmanager
def _b11_transaction(db_path):
    path=_b7_safe_path(db_path);path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=20,isolation_level=None)
    try:
        db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
        _b11_schema(db)
        names=[row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if row[0] not in _B11_MANAGED]
        before={name:_b11_table_snapshot(db,name) for name in names}
        def authorize(action,first,second,database,trigger):
            if action in (sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_DROP_INDEX,sqlite3.SQLITE_DROP_VIEW,sqlite3.SQLITE_DROP_TRIGGER,sqlite3.SQLITE_ALTER_TABLE):return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_DELETE:return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_UPDATE and first in {'b11_rulebooks','b11_session_history','b11_upgrade_rollbacks'}:return sqlite3.SQLITE_DENY
            if action in (sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE) and first not in _B11_MANAGED:return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        db.set_authorizer(authorize)
        yield db
        current_names=[row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if row[0] not in _B11_MANAGED]
        if current_names!=names or any(_b11_table_snapshot(db,name)!=snapshot for name,snapshot in before.items()):raise AuditRejected('Protected user data changed; operation rolled back')
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()


def _b11_engine(db,engine_id):
    row=db.execute('SELECT name,rules_text,version,sha256,state FROM engine_registry_v2 WHERE engine_id=?',(engine_id,)).fetchone()
    if row is None:raise AuditRejected('Engine is not installed; switch never installs it')
    if _engine_hash(engine_id,row[0],row[1],row[2])!=row[3]:raise AuditRejected('Installed engine hash mismatch')
    rules=db.execute('SELECT rules_sha256 FROM engine_rules_hashes WHERE engine_id=?',(engine_id,)).fetchone()
    if rules is None or rules[0]!=sha256(row[1].encode()):raise AuditRejected('Installed rulebook hash mismatch')
    stored=db.execute('SELECT manifest FROM b11_manifests WHERE engine_id=?',(engine_id,)).fetchone()
    manifest=json.loads(stored[0]) if stored else dict(engine_id=engine_id,name=row[0],version=row[2],rules_text=row[1],schema_version=1,entry_point='apccs_core:load_or_mount_engine')
    verdict=validate_engine_manifest(manifest)
    if not verdict['passed'] or any(manifest[key]!=value for key,value in [('engine_id',engine_id),('name',row[0]),('version',row[2]),('rules_text',row[1])]):raise AuditRejected('Installed manifest invalid or differs from registry')
    return row,manifest


def _b11_store_book(db,engine_id,rules_text):
    book=compile_engine_rulebook(engine_id,rules_text);raw=json.dumps(book['clauses'],sort_keys=True)
    prior=db.execute('SELECT compiled FROM b11_rulebooks WHERE engine_id=? AND rulebook_sha256=?',(engine_id,book['rulebook_sha256'])).fetchone()
    if prior is not None and prior[0]!=raw:raise AuditRejected('Immutable compiled rulebook differs')
    db.execute('INSERT OR IGNORE INTO b11_rulebooks VALUES (?,?,?)',(engine_id,book['rulebook_sha256'],raw))
    return book


def _b11_other_engines(db,engine_id,session_id=None):
    return (db.execute('SELECT * FROM engine_registry_v2 WHERE engine_id<>? ORDER BY engine_id',(engine_id,)).fetchall(),
            db.execute('SELECT * FROM engine_rules_hashes WHERE engine_id<>? ORDER BY engine_id',(engine_id,)).fetchall(),
            db.execute('SELECT * FROM b11_manifests WHERE engine_id<>? ORDER BY engine_id',(engine_id,)).fetchall(),
            db.execute('SELECT * FROM b11_sessions WHERE session_id<>? ORDER BY session_id',(session_id,)).fetchall() if session_id is not None else db.execute('SELECT * FROM b11_sessions ORDER BY session_id').fetchall())


def load_engine_from_manifest(db_path,manifest_dict,rules_sink=None):
    """Validated adapter to install once or mount exact existing engine state.

    Legacy load_or_mount_engine remains unchanged. Hosts wanting mandatory
    manifest validation must call this adapter rather than bypassing it.
    """
    verdict=validate_engine_manifest(manifest_dict)
    if not verdict['passed']:raise AuditRejected('; '.join(verdict['errors']))
    if rules_sink is not None and not callable(rules_sink):raise TypeError('Unary rules sink required')
    manifest=verdict['manifest'];engine_id=manifest['engine_id'];manifest_json=json.dumps(manifest,sort_keys=True)
    with _b11_transaction(db_path) as db:
        others=_b11_other_engines(db,engine_id)
        existing=db.execute('SELECT name,rules_text,version,sha256,state FROM engine_registry_v2 WHERE engine_id=?',(engine_id,)).fetchone()
        if existing:
            row,installed=_b11_engine(db,engine_id)
            if any(installed[key]!=manifest[key] for key in ('engine_id','name','version','rules_text','schema_version','entry_point')):raise AuditRejected('Existing engine differs; refusing reinstall or implicit upgrade')
            state=row[4];status='MOUNTED_EXISTING'
        else:
            legacy=db.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='engines'").fetchone()
            if legacy:
                columns={item[1].lower() for item in db.execute('PRAGMA table_info(engines)')}
                if ('name' in columns and db.execute('SELECT 1 FROM engines WHERE name=?',(manifest['name'],)).fetchone()) or ('engine_id' in columns and db.execute('SELECT 1 FROM engines WHERE engine_id=?',(engine_id,)).fetchone()):
                    raise AuditRejected('Legacy engine exists; explicit mapping required, never reinstall')
            state='{}';status='INSTALLED_VALIDATED'
            db.execute('INSERT INTO engine_registry_v2 VALUES (?,?,?,?,?,?)',(engine_id,manifest['name'],manifest['rules_text'],manifest['version'],_engine_hash(engine_id,manifest['name'],manifest['rules_text'],manifest['version']),state))
            db.execute('INSERT INTO engine_rules_hashes VALUES (?,?)',(engine_id,sha256(manifest['rules_text'].encode())))
        db.execute('INSERT OR IGNORE INTO b11_manifests VALUES (?,?)',(engine_id,manifest_json))
        book=_b11_store_book(db,engine_id,manifest['rules_text'])
        if rules_sink is not None:rules_sink(book['numbered_rules'])
        if _b11_other_engines(db,engine_id)!=others or db.execute('SELECT state FROM engine_registry_v2 WHERE engine_id=?',(engine_id,)).fetchone()[0]!=state:raise AuditRejected('Engine user state or unrelated engine changed')
    return dict(status=status,engine_id=engine_id,rulebook=book,state_json=state,
                delivery='HOST_SINK_CALLED' if rules_sink else 'RETURNED_FOR_HOST')


def switch_active_chat_engine(db_path,session_id,engine_id,rules_sink=None):
    """Persist active engine and append history only on a real session change.

    Sink receives the numbered rulebook inside the transaction. Sink failure
    rolls SQLite back; UI side effects themselves require host reconciliation.
    No actual chatbot UI injection is claimed by the library.
    """
    _b7_identifier(session_id);_b7_identifier(engine_id)
    if rules_sink is not None and not callable(rules_sink):raise TypeError('Unary rules sink required')
    with _b11_transaction(db_path) as db:
        others=_b11_other_engines(db,engine_id,session_id);row,manifest=_b11_engine(db,engine_id)
        book=_b11_store_book(db,engine_id,row[1]);desired=(engine_id,row[2],book['rulebook_sha256'])
        other_sessions=db.execute('SELECT * FROM b11_sessions WHERE session_id<>? ORDER BY session_id',(session_id,)).fetchall()
        current=db.execute('SELECT engine_id,version,rulebook_sha256 FROM b11_sessions WHERE session_id=?',(session_id,)).fetchone()
        changed=current!=desired
        if changed:
            db.execute('INSERT INTO b11_sessions VALUES (?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET engine_id=excluded.engine_id,version=excluded.version,rulebook_sha256=excluded.rulebook_sha256',(session_id,*desired))
            db.execute('INSERT INTO b11_session_history(session_id,engine_id,version,rulebook_sha256) VALUES (?,?,?,?)',(session_id,*desired))
        if rules_sink is not None:rules_sink(book['numbered_rules'])
        if _b11_other_engines(db,engine_id,session_id)!=others or db.execute('SELECT state FROM engine_registry_v2 WHERE engine_id=?',(engine_id,)).fetchone()[0]!=row[4]:raise AuditRejected('Engine user state or unrelated engine changed')
        if db.execute('SELECT * FROM b11_sessions WHERE session_id<>? ORDER BY session_id',(session_id,)).fetchall()!=other_sessions:raise AuditRejected('Another session changed; switch rolled back')
    return dict(status='SWITCHED' if changed else 'MOUNTED_HISTORY_UNCHANGED',session_id=session_id,
                engine_id=engine_id,version=row[2],rulebook=book,history_appended=changed,
                delivery='HOST_SINK_CALLED' if rules_sink else 'RETURNED_FOR_HOST')


def upgrade_engine_if_newer(db_path,engine_id,new_version,new_rules_text):
    """Strict SemVer upgrade with prior version/state/manifest rollback in same commit.

    Old/identical precedence never updates rules. Build metadata does not affect
    precedence. Invalid legacy versions require explicit mapping, not guessing.
    Existing sessions stay pinned until next switch/mount; history is immutable.
    """
    _b7_identifier(engine_id);_b11_semver(new_version);compile_engine_rulebook(engine_id,new_rules_text)
    with _b11_transaction(db_path) as db:
        others=_b11_other_engines(db,engine_id);row,manifest=_b11_engine(db,engine_id)
        comparison=_b11_compare_versions(new_version,row[2])
        if comparison<=0:
            if comparison==0 and new_rules_text!=row[1]:raise AuditRejected('Same semantic version cannot replace installed rules')
            return dict(status='MOUNTED_UNCHANGED' if comparison==0 else 'SKIPPED_OLDER_VERSION',engine_id=engine_id,version=row[2],upgraded=False)
        updated=dict(manifest,version=new_version,rules_text=new_rules_text)
        verdict=validate_engine_manifest(updated)
        if not verdict['passed']:raise AuditRejected('Updated engine manifest invalid')
        prior=dict(engine_id=engine_id,registry=dict(zip(('name','rules_text','version','sha256','state'),row)),
                   rules_sha256=sha256(row[1].encode()),manifest=manifest)
        prior_raw=json.dumps(prior,sort_keys=True)
        new_hash=_engine_hash(engine_id,row[0],new_rules_text,new_version)
        rollback_id=sha256((prior_raw+'\n'+new_hash).encode())
        existing=db.execute('SELECT prior_snapshot,new_engine_sha256 FROM b11_upgrade_rollbacks WHERE rollback_id=?',(rollback_id,)).fetchone()
        if existing and existing!=(prior_raw,new_hash):raise AuditRejected('Immutable rollback snapshot conflict')
        db.execute('INSERT OR IGNORE INTO b11_upgrade_rollbacks VALUES (?,?,?,?,?,?)',(rollback_id,engine_id,row[2],new_version,prior_raw,new_hash))
        _b11_store_book(db,engine_id,new_rules_text)
        db.execute('UPDATE engine_registry_v2 SET rules_text=?,version=?,sha256=? WHERE engine_id=?',(new_rules_text,new_version,new_hash,engine_id))
        db.execute('UPDATE engine_rules_hashes SET rules_sha256=? WHERE engine_id=?',(sha256(new_rules_text.encode()),engine_id))
        db.execute('INSERT INTO b11_manifests VALUES (?,?) ON CONFLICT(engine_id) DO UPDATE SET manifest=excluded.manifest',(engine_id,json.dumps(updated,sort_keys=True)))
        if _b11_other_engines(db,engine_id)!=others or db.execute('SELECT state FROM engine_registry_v2 WHERE engine_id=?',(engine_id,)).fetchone()[0]!=row[4]:raise AuditRejected('Engine user state or unrelated engine changed')
    return dict(status='UPGRADED',engine_id=engine_id,from_version=row[2],version=new_version,
                upgraded=True,rollback_id=rollback_id,engine_sha256=new_hash)

# Authorized Batch11 timer amendment. Earlier core bytes remain intact.
_B11_LEGACY_STRICT_TEST_RUNNER=run_all_installed_unit_tests


def _b11_test_budget(test_count):
    _b7_integer(test_count,'Installed test count')
    return max(15.0,test_count*0.35)


def _b11_installed_plan(test_path,directory):
    output=directory/'installed_plan.json'
    result=_b7_subprocess.run([_b7_sys.executable,'-B',str(test_path),'--installed-plan',str(output)],
        cwd=directory,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),
        stdout=_b7_subprocess.DEVNULL,stderr=_b7_subprocess.PIPE,timeout=15,check=False)
    if result.returncode or not output.exists():raise AuditRejected('Installed test inventory failed')
    plan=json.loads(output.read_text())
    if not isinstance(plan,dict) or not isinstance(plan.get('groups'),dict) or not plan['groups']:
        raise AuditRejected('Nonempty installed test inventory required')
    ids=[identity for group in plan['groups'].values() for identity in group]
    if plan.get('test_count')!=len(ids) or not ids or len(ids)!=len(set(ids)):
        raise AuditRejected('Invalid installed test inventory')
    return plan


def _b11_scaled_test_runner(test_path='code/test_apccs_core.py', *, timeout_sec=None):
    """Public override: real installed test count determines full-suite budget.

    Default max(15.0,test_count*0.35) seconds, including discovery and cleanup.
    Functional failures, skips, missing results and incomplete execution remain
    failures; no receipt is edited to manufacture an empty failure list.
    """
    if timeout_sec is not None and (type(timeout_sec) not in (int,float) or not _b6_math.isfinite(timeout_sec) or timeout_sec<=0):
        raise ValueError('Positive finite optional timeout required')
    started=_b8_time.monotonic();source_path=Path(__file__);test_path=_b7_safe_path(test_path)
    source=source_path.read_bytes();tests=test_path.read_bytes();workers=[];results=[];failures=[];observations={};ids=[];plan=None;budget=None
    with _b7_tempfile.TemporaryDirectory(prefix='apccs_scaled_tests_',dir='/tmp') as scratch:
        directory=Path(scratch);copied=directory/'test_apccs_core.py'
        (directory/'apccs_core.py').write_bytes(source);copied.write_bytes(tests)
        try:
            plan=_b11_installed_plan(copied,directory)
            budget=_b11_test_budget(plan['test_count']) if timeout_sec is None else float(timeout_sec)
            deadline=started+budget
            for index,group in enumerate(plan['groups']):
                output=directory/(str(index)+'.json')
                process=_b7_subprocess.Popen([_b7_sys.executable,'-B',str(copied),'--installed-worker',group,str(output)],cwd=directory,
                    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',APCCS_SELFTEST_WORKER='1'),
                    stdout=_b7_subprocess.DEVNULL,stderr=_b7_subprocess.DEVNULL,start_new_session=True)
                workers.append((group,process,output))
            for group,process,output in workers:
                process.wait(timeout=max(.001,deadline-_b8_time.monotonic()))
                if not output.exists():failures.append(dict(test=group,traceback='Missing actual test receipt'));continue
                result=json.loads(output.read_text());results.append(result)
                failures.extend(result.get('failed_assertions',[]));ids.extend(result.get('executed_test_ids',[]));observations.update(result.get('observations',{}))
                if process.returncode or not result.get('passed') or result.get('skipped',0) or result.get('scratch_removed') is not True:
                    failures.append(dict(test=group,traceback='Actual worker failure, skip or unclean scratch'))
        except (_b7_subprocess.TimeoutExpired,OSError,ValueError,AuditRejected) as error:
            failures.append(dict(test='INST-0048',traceback=str(error)))
        finally:
            for group,process,output in workers:
                if process.poll() is None:
                    try:os.killpg(process.pid,_b10_signal.SIGKILL)
                    except ProcessLookupError:continue
                process.wait()
    elapsed=_b8_time.monotonic()-started
    expected=[identity for group in plan['groups'].values() for identity in group] if plan else []
    if Counter(ids)!=Counter(expected) or sum(r.get('tests_run',0) for r in results)!=len(expected) or not expected:
        failures.append(dict(test='INST-0048',traceback='Installed tests did not all execute exactly once'))
    if budget is not None and elapsed>=budget:failures.append(dict(test='INST-0048',traceback='Scaled full-suite budget exceeded'))
    unchanged=source_path.read_bytes()==source and test_path.read_bytes()==tests
    if not unchanged:failures.append(dict(test='INST-0048',traceback='Installed files changed during run'))
    coverage=sorted({int(m.group(1)) for identity in ids for m in [re.search(r'\.test_(\d{2,4})(?:_|$)',identity)] if m and 1<=int(m.group(1))<=1000})
    return dict(passed=not failures,all_unit_tests_passed=not failures,failed_assertions=failures,
                tests_run=sum(r.get('tests_run',0) for r in results),installed_test_count=plan['test_count'] if plan else None,
                wall_clock_budget_seconds=budget,elapsed_seconds=elapsed,under_budget=budget is not None and elapsed<budget,
                under_5_seconds=elapsed<5,timer_formula='max(15.0, test_count * 0.35)',executed_test_ids=ids,instruction_coverage=coverage,
                groups=results,observations=observations,core_sha256=sha256(source),test_sha256=sha256(tests),
                scratch_removed=not Path(scratch).exists(),installed_files_unchanged=unchanged)


run_all_installed_unit_tests=_b11_scaled_test_runner


# Batch12: isolated namespace state and passive local-upload handling.
def _b12_prefix(engine_id):
    _b7_identifier(engine_id)
    return 'eng_'+sha256(engine_id.encode())+'_'


def get_engine_namespace(engine_id):
    """Reserve full-hash SQL namespace; explicitly reject an ownership collision."""
    prefix=_b12_prefix(engine_id)
    with _b7_transaction('state/b12_namespace_directory.db') as db:
        db.execute('CREATE TABLE IF NOT EXISTS b12_directory (engine_id TEXT PRIMARY KEY, namespace TEXT UNIQUE NOT NULL)')
        owner=db.execute('SELECT engine_id FROM b12_directory WHERE namespace=?',(prefix,)).fetchone()
        if owner and owner[0]!=engine_id:raise AuditRejected('Namespace hash ownership collision')
        prior=db.execute('SELECT namespace FROM b12_directory WHERE engine_id=?',(engine_id,)).fetchone()
        if prior and prior[0]!=prefix:raise AuditRejected('Existing engine namespace changed')
        db.execute('INSERT OR IGNORE INTO b12_directory VALUES (?,?)',(engine_id,prefix))
    return prefix


@contextlib.contextmanager
def _b12_namespace_transaction(db_path,engine_id):
    prefix=get_engine_namespace(engine_id);kv=prefix+'kv';checkpoints=prefix+'checkpoints'
    with _b7_transaction(db_path) as db:
        _b11_engine(db,engine_id)
        db.execute('CREATE TABLE IF NOT EXISTS b12_namespace_owners (namespace TEXT PRIMARY KEY, engine_id TEXT UNIQUE NOT NULL)')
        owner=db.execute('SELECT engine_id FROM b12_namespace_owners WHERE namespace=?',(prefix,)).fetchone()
        if owner is not None and owner[0]!=engine_id:raise AuditRejected('Database namespace owner mismatch')
        existing={row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        if owner is None and ({kv,checkpoints}&existing):raise AuditRejected('Unowned namespace tables already exist')
        db.execute('CREATE TABLE IF NOT EXISTS "'+kv+'" (key TEXT PRIMARY KEY, value_json TEXT NOT NULL, sha256 TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS "'+checkpoints+'" (checkpoint INTEGER PRIMARY KEY, body TEXT NOT NULL, sha256 TEXT NOT NULL)')
        own={kv,checkpoints,'b12_namespace_owners'}
        before={name:_b11_table_snapshot(db,name) for name in existing if name not in own}
        def authorize(action,first,second,database,trigger):
            if action in (sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_DROP_INDEX,sqlite3.SQLITE_DROP_VIEW,sqlite3.SQLITE_DROP_TRIGGER,sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_DELETE):return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_INSERT and first not in own:return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_UPDATE and first!=kv:return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        db.set_authorizer(authorize)
        db.execute('INSERT OR IGNORE INTO b12_namespace_owners VALUES (?,?)',(prefix,engine_id))
        yield db,prefix
        if any(_b11_table_snapshot(db,name)!=snapshot for name,snapshot in before.items()):raise AuditRejected('Another engine or user table changed')


def set_engine_namespace_value(db_path,engine_id,key,value):
    """Explicitly set one key in the selected engine namespace only."""
    _b7_identifier(key);raw=json.dumps(value,sort_keys=True,allow_nan=False)
    with _b12_namespace_transaction(db_path,engine_id) as (db,prefix):
        db.execute('INSERT INTO "'+prefix+'kv" VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,sha256=excluded.sha256',(key,raw,sha256(raw.encode())))
    return dict(namespace=prefix,key=key,sha256=sha256(raw.encode()))


def get_engine_namespace_value(db_path,engine_id,key):
    _b7_identifier(key);prefix=_b12_prefix(engine_id);path=_b7_safe_path(db_path)
    with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        owner=db.execute('SELECT engine_id FROM b12_namespace_owners WHERE namespace=?',(prefix,)).fetchone()
        if owner!=(engine_id,):raise AuditRejected('Namespace owner not verified')
        row=db.execute('SELECT value_json,sha256 FROM "'+prefix+'kv" WHERE key=?',(key,)).fetchone()
        if row is None:return None
        if sha256(row[0].encode())!=row[1]:raise AuditRejected('Namespace value checksum mismatch')
        return json.loads(row[0])


def record_engine_namespace_checkpoint(db_path,engine_id,checkpoint):
    """Trusted host engine checkpoint; never changes global accepted instructions."""
    _b7_integer(checkpoint,'Engine checkpoint')
    if checkpoint>1000:raise ValueError('Checkpoint must be0..1000')
    with _b12_namespace_transaction(db_path,engine_id) as (db,prefix):
        row,manifest=_b11_engine(db,engine_id);book=compile_engine_rulebook(engine_id,row[1])
        payload=dict(engine_id=engine_id,version=row[2],rulebook_sha256=book['rulebook_sha256'],checkpoint=checkpoint)
        raw=json.dumps(payload,sort_keys=True);digest=sha256(raw.encode())
        latest=db.execute('SELECT max(checkpoint) FROM "'+prefix+'checkpoints"').fetchone()[0]
        if latest is not None and checkpoint<latest:raise AuditRejected('Engine checkpoint cannot move backward')
        prior=db.execute('SELECT body,sha256 FROM "'+prefix+'checkpoints" WHERE checkpoint=?',(checkpoint,)).fetchone()
        if prior and prior!=(raw,digest):raise AuditRejected('Immutable engine checkpoint differs')
        db.execute('INSERT OR IGNORE INTO "'+prefix+'checkpoints" VALUES (?,?,?)',(checkpoint,raw,digest))
    return payload


def check_engine_dependencies(manifest_dict,installed_engines):
    """Check passive dependency inventory; do not import modules or install anything.

    dependencies: IDs or {engine_id,min_version,max_version,optional}. Maximum
    version is exclusive. Missing version evidence fails a version constraint.
    Transitive dependencies/cycles are checked from supplied inventory metadata.
    """
    verdict=validate_engine_manifest(manifest_dict)
    if not verdict['passed']:return dict(passed=False,status='RED',errors=verdict['errors'],warnings=[])
    if isinstance(installed_engines,(list,tuple,set)):
        inventory={_b7_identifier(identity):{} for identity in installed_engines}
    elif isinstance(installed_engines,dict):inventory=dict(installed_engines)
    else:raise ValueError('Installed engine inventory required')
    errors=[];warnings=[];checked=set();root=manifest_dict['engine_id']
    def visit(identity,manifest,stack):
        if identity in stack:errors.append('Dependency cycle: '+' -> '.join(stack+[identity]));return
        if identity in checked:return
        if len(stack)>=20:errors.append('Dependency depth exceeds20');return
        dependencies=manifest.get('dependencies',[])
        if not isinstance(dependencies,list) or len(dependencies)>1000:errors.append('Bounded dependency list required for '+identity);return
        for item in dependencies:
            requirement={'engine_id':item} if isinstance(item,str) else item
            if not isinstance(requirement,dict) or set(requirement)-{'engine_id','min_version','max_version','optional'}:
                errors.append('Invalid dependency requirement');continue
            try:dependency=_b7_identifier(requirement.get('engine_id'))
            except ValueError:errors.append('Invalid dependency identity');continue
            optional=requirement.get('optional',False)
            if type(optional) is not bool:errors.append('Boolean optional flag required');continue
            destination=warnings if optional else errors
            data=manifest_dict if dependency==root else inventory.get(dependency)
            if data is None or data is False or isinstance(data,dict) and data.get('enabled') is False:
                destination.append('Missing dependency: '+dependency);continue
            if isinstance(data,str):data={'version':data}
            if not isinstance(data,dict):destination.append('Unverified dependency metadata: '+dependency);continue
            try:
                if 'min_version' in requirement and _b11_compare_versions(data.get('version'),requirement['min_version'])<0:destination.append('Dependency below minimum: '+dependency);continue
                if 'max_version' in requirement and _b11_compare_versions(data.get('version'),requirement['max_version'])>=0:destination.append('Dependency exceeds maximum: '+dependency);continue
            except ValueError:destination.append('Unverified semantic version: '+dependency);continue
            visit(dependency,data,stack+[identity])
        checked.add(identity)
    visit(root,manifest_dict,[])
    return dict(passed=not errors,status='GREEN' if not errors else 'RED',errors=errors,warnings=warnings,checked=sorted(checked))


def activate_engine_with_dependencies(db_path,session_id,engine_id,rules_sink=None):
    """Validate actual installed dependency inventory and switch in one transaction."""
    _b7_identifier(session_id);_b7_identifier(engine_id)
    if rules_sink is not None and not callable(rules_sink):raise TypeError('Unary rules sink required')
    with _b11_transaction(db_path) as db:
        others=_b11_other_engines(db,engine_id,session_id);row,manifest=_b11_engine(db,engine_id)
        inventory={}
        for identity, in db.execute('SELECT engine_id FROM engine_registry_v2').fetchall():
            try:inventory[identity]=_b11_engine(db,identity)[1]
            except (AuditRejected,ValueError):continue
        dependencies=check_engine_dependencies(manifest,inventory)
        if not dependencies['passed']:raise AuditRejected('; '.join(dependencies['errors']))
        book=_b11_store_book(db,engine_id,row[1]);desired=(engine_id,row[2],book['rulebook_sha256'])
        current=db.execute('SELECT engine_id,version,rulebook_sha256 FROM b11_sessions WHERE session_id=?',(session_id,)).fetchone()
        if current!=desired:
            db.execute('INSERT INTO b11_sessions VALUES (?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET engine_id=excluded.engine_id,version=excluded.version,rulebook_sha256=excluded.rulebook_sha256',(session_id,*desired))
            db.execute('INSERT INTO b11_session_history(session_id,engine_id,version,rulebook_sha256) VALUES (?,?,?,?)',(session_id,*desired))
        if rules_sink is not None:rules_sink(book['numbered_rules'])
        if _b11_other_engines(db,engine_id,session_id)!=others or db.execute('SELECT state FROM engine_registry_v2 WHERE engine_id=?',(engine_id,)).fetchone()[0]!=row[4]:raise AuditRejected('Unrelated engine/session state changed')
    return dict(status='ACTIVE_DEPENDENCIES_VERIFIED',engine_id=engine_id,session_id=session_id,dependencies=dependencies)


def _b12_upload_name(name):
    if not isinstance(name,str) or not name or len(name)>1024 or '\\' in name or any(ord(c)<32 for c in name):raise ValueError('Safe upload name required')
    path=Path(name)
    if not path.parts or path.is_absolute() or any(part in ('..','.') or ':' in part or part.endswith((' ','.')) for part in path.parts) or path.as_posix()!=name.rstrip('/'):
        raise ValueError('Noncanonical or escaping upload path')
    if _b11_unicode.normalize('NFC',name)!=name:raise ValueError('Noncanonical Unicode upload path')
    return path


def _b12_reject_constant(value):
    raise ValueError('Nonfinite JSON constant: '+value)


def unpack_local_upload(upload_path,staging_dir):
    """Inspect first; stage passive bytes only. Never run a script or overwrite data.

    Supports ZIP/TXT/MD/JSON, <=256members,16MiB/member,64MiB total, ratio<=200.
    ZIP scripts may be staged as data. Every path, size and existing-file
    conflict is checked before publication. Publication is atomic per file.
    """
    source=_b7_safe_path(upload_path);stage=_b7_safe_path(staging_dir)
    if not stage.is_relative_to(ROOT/'imports') or source.is_relative_to(stage):raise ValueError('Separate imports staging directory required')
    if not source.is_file() or source.stat().st_size>64*1024*1024:raise ValueError('Bounded existing upload file required')
    suffix=source.suffix.lower();entries=[]
    if suffix=='.zip':
        with zipfile.ZipFile(source) as archive:
            members=archive.infolist()
            if len(members)>256:raise AuditRejected('Too many ZIP members')
            seen=set();total=0
            for member in members:
                if member.orig_filename!=member.filename:raise AuditRejected('NUL-altered ZIP name')
                relative=_b12_upload_name(member.filename);canonical=relative.as_posix().casefold()
                if canonical in seen:raise AuditRejected('Duplicate or case-colliding ZIP path')
                seen.add(canonical)
                kind=_b8_stat.S_IFMT(member.external_attr>>16)
                if member.flag_bits&1 or kind not in (0,_b8_stat.S_IFREG,_b8_stat.S_IFDIR):raise AuditRejected('Encrypted or special ZIP entry')
                if member.is_dir():continue
                total+=member.file_size
                if member.file_size>16*1024*1024 or total>64*1024*1024 or member.file_size>200*max(1,member.compress_size):raise AuditRejected('ZIP size/ratio limit exceeded')
                entries.append((relative,archive.read(member)))
    elif suffix in ('.txt','.md','.json'):
        raw=source.read_bytes()
        if len(raw)>16*1024*1024:raise ValueError('Text upload exceeds16MiB')
        text=raw.decode('utf-8')
        if suffix=='.json':json.loads(text,parse_constant=_b12_reject_constant)
        entries=[(_b12_upload_name(source.name),raw)]
    else:raise ValueError('Supported upload types: ZIP,TXT,MD,JSON')
    if not entries:raise AuditRejected('No regular upload files')
    planned={relative for relative,raw in entries}
    if any(parent in planned for relative in planned for parent in relative.parents if parent!=Path('.')):raise AuditRejected('ZIP file/directory path collision')
    for relative,raw in entries:
        target=_b7_safe_path(stage/relative)
        if target.exists() and (not target.is_file() or target.read_bytes()!=raw):raise AuditRejected('Existing staged record differs')
        for parent in target.parents:
            if parent==stage.parent:break
            if parent.exists() and not parent.is_dir():raise AuditRejected('Staging parent is a file')
    added=0
    with _b4_serial():
        if _count()+len(entries)+RESERVE>=STOP_AT:raise AuditRejected('Staging file reserve exhausted')
        for relative,raw in entries:added+=int(_b8_publish_new(stage/relative,raw))
    return dict(staging_dir=str(stage),files=[dict(path=str(stage/path),bytes=len(raw),sha256=sha256(raw),execution_authorized=False) for path,raw in entries],added=added,mounted=len(entries)-added,executed_files=0)


def deduplicate_uploaded_artifact(db_path,file_bytes,filename):
    """One immutable SQLite blob per SHA256; filenames are immutable aliases."""
    if not isinstance(file_bytes,bytes) or len(file_bytes)>64*1024*1024:raise ValueError('Bytes payload <=64MiB required')
    relative=_b12_upload_name(filename)
    if len(relative.parts)!=1:raise ValueError('Filename must be a basename')
    digest=sha256(file_bytes)
    with _b7_transaction(db_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS b12_upload_objects (sha256 TEXT PRIMARY KEY, size INTEGER NOT NULL, payload BLOB NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS b12_upload_names (filename TEXT PRIMARY KEY, sha256 TEXT NOT NULL REFERENCES b12_upload_objects(sha256))')
        owned={'b12_upload_objects','b12_upload_names'}
        before={name:_b11_table_snapshot(db,name) for name, in db.execute("SELECT name FROM sqlite_schema WHERE type='table'").fetchall() if name not in owned}
        def authorize(action,first,second,database,trigger):
            if action in (sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_DROP_INDEX,sqlite3.SQLITE_DROP_VIEW,sqlite3.SQLITE_DROP_TRIGGER,sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_DELETE,sqlite3.SQLITE_UPDATE):return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_INSERT and first not in owned:return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        db.set_authorizer(authorize)
        old=db.execute('SELECT size,payload FROM b12_upload_objects WHERE sha256=?',(digest,)).fetchone()
        if old and old!=(len(file_bytes),file_bytes):raise AuditRejected('Upload hash collision or corrupt object')
        alias=db.execute('SELECT sha256 FROM b12_upload_names WHERE filename=?',(filename,)).fetchone()
        if alias and alias[0]!=digest:raise AuditRejected('Filename already belongs to different bytes')
        db.execute('INSERT OR IGNORE INTO b12_upload_objects VALUES (?,?,?)',(digest,len(file_bytes),file_bytes))
        db.execute('INSERT OR IGNORE INTO b12_upload_names VALUES (?,?)',(filename,digest))
        if any(_b11_table_snapshot(db,name)!=snapshot for name,snapshot in before.items()):raise AuditRejected('User records changed during upload')
    return dict(status='MOUNTED_EXISTING' if old else 'STORED_NEW',sha256=digest,filename=filename,bytes=len(file_bytes),new_blob=old is None)


def probe_loaded_engine_health(db_path,engine_id):
    """Read-only coherent readiness probe; never invent a checkpoint or repair data."""
    _b7_identifier(engine_id);path=_b7_safe_path(db_path);prefix=_b12_prefix(engine_id)
    try:
        if not path.is_file():raise AuditRejected('Engine database missing')
        with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,isolation_level=None)) as db:
            db.execute('BEGIN')
            if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)] or db.execute('PRAGMA foreign_key_check').fetchall():raise AuditRejected('Database integrity check failed')
            row,manifest=_b11_engine(db,engine_id);book=compile_engine_rulebook(engine_id,row[1])
            stored=db.execute('SELECT compiled FROM b11_rulebooks WHERE engine_id=? AND rulebook_sha256=?',(engine_id,book['rulebook_sha256'])).fetchone()
            if stored is None or stored[0]!=json.dumps(book['clauses'],sort_keys=True):raise AuditRejected('Compiled rulebook integrity mismatch')
            tables={name for name, in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
            required={prefix+'kv',prefix+'checkpoints','b12_namespace_owners'}
            if not required<=tables:return dict(ready=False,status='GRAY',engine_id=engine_id,reason='Namespace tables or checkpoint not initialized',last_checkpoint=None)
            if db.execute('SELECT engine_id FROM b12_namespace_owners WHERE namespace=?',(prefix,)).fetchone()!=(engine_id,):raise AuditRejected('Namespace owner mismatch')
            for raw,digest in db.execute('SELECT value_json,sha256 FROM "'+prefix+'kv"'):
                if sha256(raw.encode())!=digest:raise AuditRejected('Namespace value integrity mismatch')
                json.loads(raw,parse_constant=_b12_reject_constant)
            checkpoint=db.execute('SELECT checkpoint,body,sha256 FROM "'+prefix+'checkpoints" ORDER BY checkpoint DESC LIMIT 1').fetchone()
            if checkpoint is None:return dict(ready=False,status='GRAY',engine_id=engine_id,reason='No trusted engine checkpoint recorded',last_checkpoint=None)
            payload=json.loads(checkpoint[1],parse_constant=_b12_reject_constant)
            if not isinstance(payload,dict) or type(checkpoint[0]) is not int or not 0<=checkpoint[0]<=1000:raise AuditRejected('Invalid engine checkpoint schema')
            if sha256(checkpoint[1].encode())!=checkpoint[2] or payload.get('engine_id')!=engine_id or payload.get('checkpoint')!=checkpoint[0]:raise AuditRejected('Engine checkpoint integrity mismatch')
            sessions=db.execute('SELECT version,rulebook_sha256 FROM b11_sessions WHERE engine_id=?',(engine_id,)).fetchall()
            stale=any(version!=row[2] or digest!=book['rulebook_sha256'] for version,digest in sessions)
            checkpoint_current=payload.get('version')==row[2] and payload.get('rulebook_sha256')==book['rulebook_sha256']
            ready=bool(sessions) and not stale and checkpoint_current
            return dict(ready=ready,status='GREEN' if ready else 'GRAY',engine_id=engine_id,version=row[2],namespace=prefix,
                        active_sessions=len(sessions),stale_sessions=stale,table_integrity='ok',rulebook_hash=book['rulebook_sha256'],
                        last_checkpoint=checkpoint[0],checkpoint_scope='ENGINE_NAMESPACE_TRUSTED_HOST',checkpoint_current=checkpoint_current)
    except (sqlite3.Error,AuditRejected,ValueError,TypeError,KeyError) as error:
        return dict(ready=False,status='RED',engine_id=engine_id,reason=str(error),last_checkpoint=None)

# Batch13: draft planning, immutable scope and proof-carrying recovery.
_B13_TABLES={'b13_drafts','b13_draft_history','b13_locks','b13_batches'}


def _b13_json(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    raw.encode('utf-8')
    if json.loads(raw)!=value:raise ValueError('JSON-native planning values required')
    if len(raw.encode())>4*1024*1024:raise ValueError('Plan data exceeds4MiB')
    return raw


def _b13_id(value):
    if type(value) is int:
        if not 1<=value<=1000:raise ValueError('Integer instruction ID must be1..1000')
        return str(value)
    return _b7_identifier(value)


def _b13_items(notes):
    if isinstance(notes,dict):items=notes.get('instructions',[])
    elif isinstance(notes,list):items=notes
    elif isinstance(notes,str):
        items=[dict(id=match.group(1),text=match.group(2)) for match in re.finditer(r'^\s*([0-9]+)[.)][ \t]+([^\r\n]+)',notes,re.MULTILINE)]
    else:raise ValueError('Notes must be text, instruction list or JSON object')
    if not isinstance(items,list) or len(items)>1000:raise ValueError('At most1000 explicit instruction items required')
    result=[];seen=set()
    for index,item in enumerate(items):
        if isinstance(item,str):identity=str(index+1);text=item
        elif isinstance(item,dict) and set(item)=={'id','text'}:identity=_b13_id(item['id']);text=item['text']
        else:raise ValueError('Instruction item must be text or exact{id,text} object')
        if not isinstance(text,str) or not text.strip():raise ValueError('Nonempty instruction text required')
        if identity in seen:raise ValueError('Duplicate plan instruction ID')
        seen.add(identity);result.append(dict(id=identity,text=text))
    return result


@contextlib.contextmanager
def _b13_plan_transaction(db,project,write=False):
    _b7_identifier(project);owned=not isinstance(db,sqlite3.Connection)
    if owned:
        path=_b7_safe_path(db)
        if not write and not path.is_file():raise ValueError('Existing plan database required')
        if write:path.parent.mkdir(parents=True,exist_ok=True)
        connection=sqlite3.connect(path if write else path.as_uri()+'?mode=ro',uri=not write,timeout=20,isolation_level=None)
    else:
        connection=db
        if connection.in_transaction:raise ValueError('Commit caller transaction before plan operation')
        location=next((row[2] for row in connection.execute('PRAGMA database_list') if row[1]=='main'),'')
        if location:_b7_safe_path(location)
    try:
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        if write:
            connection.execute('CREATE TABLE IF NOT EXISTS b13_drafts (project TEXT PRIMARY KEY, revision INTEGER NOT NULL, notes_json TEXT NOT NULL, style_json TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS b13_draft_history (project TEXT NOT NULL, revision INTEGER NOT NULL, notes_json TEXT NOT NULL, style_json TEXT NOT NULL, PRIMARY KEY(project,revision))')
            connection.execute('CREATE TABLE IF NOT EXISTS b13_locks (project TEXT PRIMARY KEY, payload TEXT NOT NULL, lock_sha256 TEXT NOT NULL, read_only INTEGER NOT NULL CHECK(read_only=1))')
            connection.execute('CREATE TABLE IF NOT EXISTS b13_batches (project TEXT NOT NULL, lock_sha256 TEXT NOT NULL, batch_size INTEGER NOT NULL, batch_number INTEGER NOT NULL, body TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(project,lock_sha256,batch_size,batch_number))')
        names=[name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if name not in _B13_TABLES]
        before={name:_b11_table_snapshot(connection,name) for name in names}
        other_drafts=connection.execute('SELECT * FROM b13_drafts WHERE project<>? ORDER BY project',(project,)).fetchall() if write else None
        immutable_before={name:Counter(connection.execute('SELECT * FROM '+name).fetchall()) for name in ('b13_locks','b13_draft_history','b13_batches')} if write else {}
        if owned and write:
            def authorize(action,first,second,database,trigger):
                if action in (sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_DROP_INDEX,sqlite3.SQLITE_DROP_VIEW,sqlite3.SQLITE_DROP_TRIGGER,sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_DELETE):return sqlite3.SQLITE_DENY
                if action==sqlite3.SQLITE_INSERT and first not in _B13_TABLES:return sqlite3.SQLITE_DENY
                if action==sqlite3.SQLITE_UPDATE and first!='b13_drafts':return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            connection.set_authorizer(authorize)
        yield connection
        current=[name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if name not in _B13_TABLES]
        if current!=names or any(_b11_table_snapshot(connection,name)!=snapshot for name,snapshot in before.items()):raise AuditRejected('User records changed during planning transaction')
        if write and connection.execute('SELECT * FROM b13_drafts WHERE project<>? ORDER BY project',(project,)).fetchall()!=other_drafts:raise AuditRejected('Another project draft changed')
        if write and any(rows-Counter(connection.execute('SELECT * FROM '+name).fetchall()) for name,rows in immutable_before.items()):raise AuditRejected('Immutable plan/history/batch record changed')
        connection.commit()
    except BaseException:
        connection.rollback();raise
    finally:
        if owned:connection.close()


def _b13_locked(connection,project):
    row=connection.execute('SELECT payload,lock_sha256,read_only FROM b13_locks WHERE project=?',(project,)).fetchone()
    if row is None:raise AuditRejected('Project plan is not locked')
    if row[2]!=1 or sha256(row[0].encode())!=row[1]:raise AuditRejected('Locked plan integrity failure')
    payload=json.loads(row[0])
    required={'schema_version','project','revision','notes','management_style','instructions'}
    if not isinstance(payload,dict) or set(payload)!=required or type(payload.get('schema_version')) is not int or payload['schema_version']!=1 or type(payload.get('revision')) is not int or payload['revision']<1 or payload.get('project')!=project or _b13_json(payload)!=row[0] or _b13_items(payload['notes'])!=payload['instructions']:
        raise AuditRejected('Locked plan schema mismatch')
    return payload,row[1]


def save_plan_discussion_draft(db,project,notes,style):
    """Preserve notes/style and append revisions only before project lock-down.

    notes accepts free text, explicit item list, or {instructions:[{id,text}],...}.
    Strings in an explicit list receive stable1-based IDs. No task text invented.
    Identical repeated draft mounts without another revision. Raw notes retained.
    """
    if not isinstance(notes,(str,list,dict)) or isinstance(notes,str) and not notes.strip():raise ValueError('Nonempty planning notes required')
    if not isinstance(style,(str,dict)) or not style:raise ValueError('Management style text or object required')
    raw_notes=_b13_json(notes);raw_style=_b13_json(style)
    _b13_items(notes)
    with _b13_plan_transaction(db,project,True) as connection:
        if connection.execute('SELECT 1 FROM b13_locks WHERE project=?',(project,)).fetchone():raise AuditRejected('Locked project plan is read-only')
        previous=connection.execute('SELECT revision,notes_json,style_json FROM b13_drafts WHERE project=?',(project,)).fetchone()
        if previous and previous[1:]==(raw_notes,raw_style):return dict(project=project,revision=previous[0],status='MOUNTED_IDENTICAL_DRAFT')
        revision=previous[0]+1 if previous else 1
        connection.execute('INSERT INTO b13_draft_history VALUES (?,?,?,?)',(project,revision,raw_notes,raw_style))
        connection.execute('INSERT INTO b13_drafts VALUES (?,?,?,?) ON CONFLICT(project) DO UPDATE SET revision=excluded.revision,notes_json=excluded.notes_json,style_json=excluded.style_json',(project,revision,raw_notes,raw_style))
        if connection.execute('SELECT revision,notes_json,style_json FROM b13_drafts WHERE project=?',(project,)).fetchone()!=(revision,raw_notes,raw_style) or connection.execute('SELECT notes_json,style_json FROM b13_draft_history WHERE project=? AND revision=?',(project,revision)).fetchone()!=(raw_notes,raw_style):raise AuditRejected('Draft write changed by a trigger')
    return dict(project=project,revision=revision,status='DRAFT_SAVED')


def lock_project_plan(db,project):
    """Seal explicit plan once; own APIs never update/delete lock or locked draft.

    Read-only is per-plan API policy, not an OS-wide ban on independent SQL.
    Each use verifies the checksum; proof bundles preserve the trusted old hash.
    """
    with _b13_plan_transaction(db,project,True) as connection:
        if connection.execute('SELECT 1 FROM b13_locks WHERE project=?',(project,)).fetchone():
            payload,digest=_b13_locked(connection,project)
            return dict(project=project,lock_sha256=digest,read_only=True,status='MOUNTED_EXISTING_LOCK',instruction_count=len(payload['instructions']))
        draft=connection.execute('SELECT revision,notes_json,style_json FROM b13_drafts WHERE project=?',(project,)).fetchone()
        if draft is None:raise AuditRejected('No project draft to lock')
        notes=json.loads(draft[1]);items=_b13_items(notes)
        if not items:raise AuditRejected('Explicit instruction items required; discussion is not converted into invented tasks')
        payload=dict(schema_version=1,project=project,revision=draft[0],notes=notes,management_style=json.loads(draft[2]),instructions=items)
        raw=_b13_json(payload);digest=sha256(raw.encode())
        connection.execute('INSERT INTO b13_locks VALUES (?,?,?,1)',(project,raw,digest))
        if connection.execute('SELECT payload,lock_sha256,read_only FROM b13_locks WHERE project=?',(project,)).fetchone()!=(raw,digest,1):raise AuditRejected('Plan seal changed by a trigger')
    return dict(project=project,lock_sha256=digest,read_only=True,status='PLAN_LOCKED',instruction_count=len(items))


def generate_batches_from_locked_plan(db,project,batch_size=5):
    """Persist deterministic slices; final short batch is not padded with new tasks."""
    _b7_integer(batch_size,'Batch size',1)
    if batch_size>1000:raise ValueError('Batch size must be<=1000')
    with _b13_plan_transaction(db,project,True) as connection:
        payload,digest=_b13_locked(connection,project);batches=[]
        for offset in range(0,len(payload['instructions']),batch_size):
            number=offset//batch_size+1;items=payload['instructions'][offset:offset+batch_size]
            batch=dict(project=project,lock_sha256=digest,batch_size=batch_size,batch_number=number,
                       batch_id=digest+':'+str(batch_size)+':'+str(number),instructions=items)
            raw=_b13_json(batch);batch_hash=sha256(raw.encode())
            existing=connection.execute('SELECT body,sha256 FROM b13_batches WHERE project=? AND lock_sha256=? AND batch_size=? AND batch_number=?',(project,digest,batch_size,number)).fetchone()
            if existing and existing!=(raw,batch_hash):raise AuditRejected('Existing immutable plan batch differs')
            connection.execute('INSERT OR IGNORE INTO b13_batches VALUES (?,?,?,?,?,?)',(project,digest,batch_size,number,raw,batch_hash))
            batches.append(dict(batch,sha256=batch_hash))
        stored=connection.execute('SELECT batch_number,body,sha256 FROM b13_batches WHERE project=? AND lock_sha256=? AND batch_size=? ORDER BY batch_number',(project,digest,batch_size)).fetchall()
        expected=[(item['batch_number'],_b13_json({key:value for key,value in item.items() if key!='sha256'}),item['sha256']) for item in batches]
        if stored!=expected:raise AuditRejected('Unrequested or corrupt batch queue rows')
    return batches


def check_output_against_locked_plan(db,project,completed_ids):
    """Exact ID accounting, not semantic verification of an output's contents."""
    if not isinstance(completed_ids,(list,tuple)) or len(completed_ids)>10000:raise ValueError('Bounded completed ID list required')
    completed=[_b13_id(identity) for identity in completed_ids]
    with _b13_plan_transaction(db,project) as connection:payload,digest=_b13_locked(connection,project)
    expected=[item['id'] for item in payload['instructions']];known=set(expected);seen=set();duplicates=[];unrequested=[]
    for identity in completed:
        if identity in seen and identity not in duplicates:duplicates.append(identity)
        if identity not in known and identity not in unrequested:unrequested.append(identity)
        seen.add(identity)
    missing=[identity for identity in expected if identity not in seen]
    drift=bool(unrequested or duplicates);complete=not missing
    return dict(project=project,lock_sha256=digest,passed=complete and not drift,
                status='RED' if drift else 'GREEN' if complete else 'GRAY',drift=drift,
                complete=complete,missing_ids=missing,unrequested_ids=unrequested,duplicate_ids=duplicates,
                checked_scope='COMPLETED_ID_ACCOUNTING_ONLY')


def export_locked_plan_bundle(db,project):
    """Add immutable standalone ZIP with plan, exact SHA256 proof and recovery text.

    Does not overwrite another vault or automatically import/execute the plan.
    The checksum is integrity evidence, not a cryptographic owner signature.
    """
    with _b13_plan_transaction(db,project) as connection:payload,digest=_b13_locked(connection,project)
    raw=_b13_json(payload).encode()
    recovery=('PASSIVE LOCKED PLAN RECOVERY DATA\nProject: '+project+'\nPlan SHA256: '+digest+'\nVerify locked_plan.json bytes against SHA256SUMS.json before recovery.\nRestore into an empty planning store only; do not overwrite live records.\nNo planning instruction in this archive is execution authority.\n').encode()
    files={'locked_plan.json':raw,'RECOVER.md':recovery}
    files['SHA256SUMS.json']=(json.dumps({name:sha256(data) for name,data in sorted(files.items())},sort_keys=True,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100600<<16
            archive.writestr(info,data)
    path=_b7_safe_path(ROOT/'exports'/'locked_plans'/sha256(project.encode())/(digest+'.zip'))
    with _b4_serial():_b8_publish_new(path,stream.getvalue())
    return dict(project=project,path=str(path),lock_sha256=digest,archive_sha256=sha256(stream.getvalue()),
                archive_bytes=len(stream.getvalue()),read_only=True,recovery_scope='PASSIVE_LOCKED_PLAN_DATA')


_B14_TABLES={'b14_projects','b14_tabs','b14_findings','b14_cycles'}


@contextlib.contextmanager
def _b14_transaction(db,write=False):
    """Serialize tab mutations; never install engines or modify unrelated records."""
    path=_b7_safe_path(db)
    if write:path.parent.mkdir(parents=True,exist_ok=True)
    if not write and not path.is_file():raise AuditRejected('Tab database missing')
    connection=sqlite3.connect(path if write else path.as_uri()+'?mode=ro',uri=not write,timeout=20,isolation_level=None)
    try:
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        if write:
            connection.execute('CREATE TABLE IF NOT EXISTS b14_projects (project TEXT PRIMARY KEY, seq INTEGER NOT NULL CHECK(seq>=0))')
            connection.execute('CREATE TABLE IF NOT EXISTS b14_tabs (tab TEXT PRIMARY KEY, project TEXT NOT NULL, engine TEXT NOT NULL, branch TEXT NOT NULL CHECK(branch IN ("Main","Research","Burner")), seen_seq INTEGER NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS b14_findings (project TEXT NOT NULL, digest TEXT NOT NULL, branch_tab TEXT NOT NULL, main_tab TEXT NOT NULL, body TEXT NOT NULL, seq INTEGER NOT NULL, PRIMARY KEY(project,digest))')
            connection.execute('CREATE TABLE IF NOT EXISTS b14_cycles (tab TEXT NOT NULL, seq INTEGER NOT NULL, PRIMARY KEY(tab,seq))')
        names=[name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if name not in _B14_TABLES]
        before={name:_b11_table_snapshot(connection,name) for name in names}
        if write:
            def authorize(action,first,second,database,trigger):
                if action in (sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE):
                    if trigger or first not in _B14_TABLES or action==sqlite3.SQLITE_DELETE:return sqlite3.SQLITE_DENY
                if action in (sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_DROP_INDEX,sqlite3.SQLITE_DROP_VIEW,sqlite3.SQLITE_DROP_TRIGGER,sqlite3.SQLITE_ALTER_TABLE):return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            connection.set_authorizer(authorize)
        yield connection
        if names!=[name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if name not in _B14_TABLES] or any(_b11_table_snapshot(connection,name)!=value for name,value in before.items()):raise AuditRejected('Unrelated records changed')
        connection.commit()
    except BaseException:
        connection.rollback();raise
    finally:connection.close()


def _b14_tab(connection,tab):
    _b7_identifier(tab)
    row=connection.execute('SELECT project,engine,branch,seen_seq FROM b14_tabs WHERE tab=?',(tab,)).fetchone()
    if row is None:raise AuditRejected('Tab not registered')
    seq=connection.execute('SELECT seq FROM b14_projects WHERE project=?',(row[0],)).fetchone()
    if seq is None:raise AuditRejected('Project sequence missing')
    return dict(tab=tab,project=row[0],engine=row[1],branch=row[2],seen_seq=row[3],current_seq=seq[0])


def _b14_claim(connection,tab,expected):
    state=_b14_tab(connection,tab)
    if type(expected) is not int or expected<0:raise ValueError('Nonnegative integer sequence required')
    if expected!=state['current_seq']:raise AuditRejected('Stale tab write rejected')
    cursor=connection.execute('UPDATE b14_projects SET seq=seq+1 WHERE project=? AND seq=?',(state['project'],expected))
    if cursor.rowcount!=1:raise AuditRejected('Concurrent tab write rejected')
    connection.execute('UPDATE b14_tabs SET seen_seq=? WHERE tab=?',(expected+1,tab))
    return expected+1


def register_chat_tab_session(db,tab,engine,branch):
    """Register a named lane; tab may be {id,project}; string tab uses default project."""
    if isinstance(tab,dict):
        if set(tab)!={'id','project'}:raise ValueError('Tab descriptor requires id and project')
        tab_id=tab['id'];project=tab['project']
    else:tab_id=tab;project='default'
    for value in (tab_id,project,engine):_b7_identifier(value)
    aliases={'main':'Main','research':'Research','research branch':'Research','burner':'Burner'}
    if not isinstance(branch,str) or branch.lower() not in aliases:raise ValueError('Main, Research or Burner lane required')
    branch=aliases[branch.lower()]
    with _b14_transaction(db,True) as connection:
        _b11_engine(connection,engine)
        old=connection.execute('SELECT project,engine,branch FROM b14_tabs WHERE tab=?',(tab_id,)).fetchone()
        if old is not None:
            if old!=(project,engine,branch):raise AuditRejected('Tab identity already mounted with different metadata')
            return dict(_b14_tab(connection,tab_id),status='MOUNTED_EXISTING')
        connection.execute('INSERT OR IGNORE INTO b14_projects VALUES (?,0)',(project,))
        seq=connection.execute('SELECT seq FROM b14_projects WHERE project=?',(project,)).fetchone()[0]
        connection.execute('INSERT INTO b14_tabs VALUES (?,?,?,?,?)',(tab_id,project,engine,branch,seq))
        return dict(_b14_tab(connection,tab_id),status='REGISTERED')


def run_burner_question_cycle(db,tab,question,answer):
    """Keep ephemeral text in call memory only; persist a text-free cycle receipt."""
    if any(not isinstance(value,str) or not value.strip() or len(value)>1000000 for value in (question,answer)):raise ValueError('Bounded nonempty question and answer required')
    with _b14_transaction(db,True) as connection:
        state=_b14_tab(connection,tab)
        if state['branch']!='Burner':raise AuditRejected('Burner lane required')
        seq=_b14_claim(connection,tab,state['seen_seq'])
        connection.execute('INSERT INTO b14_cycles VALUES (?,?)',(tab,seq))
        return dict(tab=tab,project=state['project'],seq=seq,purged=True,persisted_text=False)


def promote_branch_finding_to_main(db,branch,main,summary):
    """Require explicit caller verification, content hash and evidence; no raw branch chat."""
    required={'text','verified','verifier','evidence','sha256'}
    if not isinstance(summary,dict) or set(summary)!=required:raise ValueError('Structured verified summary required')
    text=summary['text']
    if not isinstance(text,str) or not text.strip() or len(text)>12000:raise ValueError('Compact nonempty summary required')
    digest=sha256(text.encode())
    if summary['verified'] is not True or summary['sha256']!=digest:raise AuditRejected('Summary not verified or hash differs')
    _b7_identifier(summary['verifier'])
    if not isinstance(summary['evidence'],list) or not summary['evidence'] or any(not isinstance(item,str) or not item.strip() or len(item)>1024 for item in summary['evidence']):raise ValueError('Verification evidence references required')
    body=_b13_json(summary)
    with _b14_transaction(db,True) as connection:
        source=_b14_tab(connection,branch);target=_b14_tab(connection,main)
        if source['branch']!='Research' or target['branch']!='Main' or source['project']!=target['project'] or source['engine']!=target['engine']:raise AuditRejected('Compatible Research to Main lanes required')
        prior=connection.execute('SELECT body,seq FROM b14_findings WHERE project=? AND digest=?',(source['project'],digest)).fetchone()
        if prior:
            if prior[0]!=body:raise AuditRejected('Conflicting verification for existing finding')
            return dict(status='MOUNTED_EXISTING',sha256=digest,seq=prior[1],promoted=False)
        seq=_b14_claim(connection,branch,source['seen_seq'])
        connection.execute('INSERT INTO b14_findings VALUES (?,?,?,?,?,?)',(source['project'],digest,branch,main,body,seq))
        return dict(status='PROMOTED',sha256=digest,seq=seq,promoted=True)


def create_tab_handoff_script(db,source):
    """Passive compact JSON resume packet; engine rules referenced by validated hash."""
    with _b14_transaction(db) as connection:
        state=_b14_tab(connection,source);row,manifest=_b11_engine(connection,state['engine'])
        book=compile_engine_rulebook(state['engine'],row[1]);prefix=_b12_prefix(state['engine'])
        tables={name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        checkpoint=None
        if prefix+'checkpoints' in tables:
            item=connection.execute('SELECT checkpoint,body,sha256 FROM "'+prefix+'checkpoints" ORDER BY checkpoint DESC LIMIT 1').fetchone()
            if item:
                payload=json.loads(item[1]);checkpoint=item[0]
                if sha256(item[1].encode())!=item[2] or payload.get('engine_id')!=state['engine'] or payload.get('checkpoint')!=checkpoint or payload.get('version')!=row[2] or payload.get('rulebook_sha256')!=book['rulebook_sha256']:raise AuditRejected('Checkpoint integrity or engine version mismatch')
        packet=dict(schema_version=1,kind='PASSIVE_TAB_RESUME',project=state['project'],source_tab=source,branch=state['branch'],active_engine=state['engine'],engine_version=row[2],rulebook_sha256=book['rulebook_sha256'],rulebook_ref='SQLITE_ENGINE_REGISTRY',last_checkpoint=checkpoint,checkpoint_status='KNOWN' if checkpoint is not None else 'UNKNOWN',expected_seq=state['current_seq'],action='Mount existing database and engine; use expected_seq for atomic guarded writes')
        raw=_b13_json(packet)
        return dict(packet=packet,resume_text=raw,sha256=sha256(raw.encode()),bytes=len(raw.encode()))


def guard_tab_write_conflict(db,tab,expected_seq):
    """Atomically claim the next project revision; stale claims roll back unchanged.

    This claim is consumed, not a lease authorizing later unguarded SQL. Actual
    writes must compare-and-swap within their own transaction as tab APIs do.
    """
    with _b14_transaction(db,True) as connection:
        seq=_b14_claim(connection,tab,expected_seq)
        return dict(allowed=True,tab=tab,previous_seq=expected_seq,seq=seq)


_B15_TARGET=102400
_B15_HARD_CEILING=256000
_B15_TABLES={'b15_view_snapshots','b15_chat_history'}


def track_browser_cache_bytes(current,ceiling=102400):
    """Account host-reported UTF8/serialized bytes, not an unmeasured browser heap."""
    if type(current) is not int or current<0:raise ValueError('Nonnegative integer byte count required')
    if type(ceiling) is not int or not 1<=ceiling<=_B15_HARD_CEILING:raise ValueError('Target must be within 250KiB hard ceiling')
    target=min(ceiling,_B15_TARGET)
    hard=current>=_B15_HARD_CEILING;flush=current>=target
    return dict(current_bytes=current,target_bytes=target,hard_ceiling_bytes=_B15_HARD_CEILING,
                status='RED' if hard else 'YELLOW' if flush else 'GREEN',flush_required=flush,
                blocked=hard,within_target=current<target,headroom_bytes=max(0,target-current),
                accounting_scope='HOST_REPORTED_VIEW_BYTES')


@contextlib.contextmanager
def _b15_cache_transaction(db,write=False):
    path=_b7_safe_path(db)
    if write:path.parent.mkdir(parents=True,exist_ok=True)
    if not write and not path.is_file():raise AuditRejected('History database missing')
    connection=sqlite3.connect(path if write else path.as_uri()+'?mode=ro',uri=not write,timeout=20,isolation_level=None)
    try:
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        if write:
            connection.execute('CREATE TABLE IF NOT EXISTS b15_view_snapshots (sha256 TEXT PRIMARY KEY, body TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS b15_chat_history (session TEXT NOT NULL, seq INTEGER NOT NULL, message_id TEXT NOT NULL, role TEXT NOT NULL, body TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(session,seq), UNIQUE(session,message_id))')
        names=[name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if name not in _B15_TABLES]
        before={name:_b11_table_snapshot(connection,name) for name in names} if write else {}
        if write:
            def authorize(action,first,second,database,trigger):
                if action in (sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE):
                    if trigger or first not in _B15_TABLES or action!=sqlite3.SQLITE_INSERT:return sqlite3.SQLITE_DENY
                if action in (sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_DROP_INDEX,sqlite3.SQLITE_DROP_VIEW,sqlite3.SQLITE_DROP_TRIGGER,sqlite3.SQLITE_ALTER_TABLE):return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            connection.set_authorizer(authorize)
        yield connection
        if names!=[name for name, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if name not in _B15_TABLES] or any(_b11_table_snapshot(connection,name)!=value for name,value in before.items()):raise AuditRejected('User records changed during cache flush')
        connection.commit()
    except BaseException:
        connection.rollback();raise
    finally:connection.close()


def _b15_messages(payload):
    if 'messages' not in payload:return None,[]
    session=_b7_identifier(payload.get('session'))
    messages=payload['messages']
    if not isinstance(messages,list) or len(messages)>10000:raise ValueError('Bounded message list required')
    seen=set();result=[]
    for item in messages:
        if not isinstance(item,dict) or set(item)!={'id','role','text'}:raise ValueError('Messages require id,role,text')
        identity=item['id']
        if type(identity) is int and identity>=0:identity=str(identity)
        _b7_identifier(identity)
        if identity in seen:raise ValueError('Duplicate message id in payload')
        seen.add(identity)
        if item['role'] not in ('user','assistant','system','tool'):raise ValueError('Unsupported message role')
        if not isinstance(item['text'],str):raise ValueError('Message text required')
        result.append((identity,item['role'],item['text'],sha256(item['text'].encode())))
    return session,result


def flush_view_cache_to_sqlite(db,payload):
    """Commit exact JSON dictionary before returning an empty replacement UI view.

    Optional {session,messages:[{id,role,text}]} also appends immutable indexed
    history. Caller must replace its view with returned view_state after commit.
    """
    if not isinstance(payload,dict):raise ValueError('JSON dictionary required')
    raw=_b13_json(payload);digest=sha256(raw.encode());session,messages=_b15_messages(payload)
    with _b15_cache_transaction(db,True) as connection:
        old=connection.execute('SELECT body FROM b15_view_snapshots WHERE sha256=?',(digest,)).fetchone()
        if old is not None and old[0]!=raw:raise AuditRejected('Cache content hash collision')
        if old is None:connection.execute('INSERT INTO b15_view_snapshots VALUES (?,?)',(digest,raw))
        seq=connection.execute('SELECT COALESCE(MAX(seq),0) FROM b15_chat_history WHERE session=?',(session,)).fetchone()[0] if session else 0
        added=0
        for identity,role,text,text_hash in messages:
            prior=connection.execute('SELECT role,body,sha256 FROM b15_chat_history WHERE session=? AND message_id=?',(session,identity)).fetchone()
            if prior is not None:
                if prior!=(role,text,text_hash):raise AuditRejected('Existing message differs; overwrite rejected')
            else:
                seq+=1;added+=1
                connection.execute('INSERT INTO b15_chat_history VALUES (?,?,?,?,?,?)',(session,seq,identity,role,text,text_hash))
    return dict(committed=True,snapshot_sha256=digest,stored_bytes=len(raw.encode()),view_state={},view_bytes=2,below_target=True,history_messages_added=added,caller_must_replace_view=True)


def paginate_chat_history_window(db,session,window=20):
    """Indexed keyset page, at most20 bounded previews; full text stays on disk.

    session may be {id,before} using the previous page next_cursor. Rows are
    chronological within each page; latest page is returned for a string id.
    """
    if type(window) is not int or not 1<=window<=20:raise ValueError('Window must be1..20')
    before=None
    if isinstance(session,dict):
        if set(session)!={'id','before'}:raise ValueError('Cursor requires id,before')
        before=session['before'];session=session['id']
        if type(before) is not int or before<1:raise ValueError('Positive before cursor required')
    _b7_identifier(session)
    with _b15_cache_transaction(db) as connection:
        exists=connection.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='b15_chat_history'").fetchone()
        if exists is None:return dict(session=session,messages=[],next_cursor=None,view_bytes=2,older_on_disk=False)
        bound=' AND seq<?' if before is not None else ''
        params=(session,before,window) if before is not None else (session,window)
        rows=connection.execute('SELECT seq,message_id,role,substr(body,1,4096),length(CAST(body AS BLOB)),sha256 FROM b15_chat_history WHERE session=?'+bound+' ORDER BY seq DESC LIMIT ?',params).fetchall()
        messages=[]
        for seq,identity,role,preview,total,digest in reversed(rows):
            excerpt=preview.encode()[:2048].decode('utf-8',errors='ignore')
            while len(json.dumps(excerpt,ensure_ascii=False).encode())>3072:excerpt=excerpt[:len(excerpt)//2]
            messages.append(dict(seq=seq,id=identity,role=role,text=excerpt,total_text_bytes=total,sha256=digest,truncated=len(excerpt.encode())<total,sqlite_ref=dict(table='b15_chat_history',session=session,seq=seq)))
        earliest=rows[-1][0] if rows else None
        older=bool(earliest and connection.execute('SELECT 1 FROM b15_chat_history WHERE session=? AND seq<? LIMIT 1',(session,earliest)).fetchone())
        result=dict(session=session,messages=messages,next_cursor=dict(id=session,before=earliest) if older else None,older_on_disk=older)
        encoded=_b13_json(result).encode()
        if len(encoded)>=_B15_TARGET:raise AuditRejected('Serialized view exceeds100KiB target')
        result['view_bytes']=len(_b13_json(dict(result,view_bytes=_B15_TARGET)).encode())
        return result


def intercept_binary_chat_dump(bytes,filename):
    """Route binary, ZIP or oversized text to immutable disk; never encode as chat."""
    if not isinstance(bytes,(type(b''),bytearray,memoryview)):raise ValueError('Byte payload required')
    raw=memoryview(bytes).tobytes()
    name=_b12_upload_name(filename)
    if len(name.parts)!=1 or len(filename)>128:raise ValueError('Single bounded filename required')
    binary_suffix=name.suffix.lower() not in ('','.txt','.md','.json','.csv','.log','.py','.html','.xml','.yaml','.yml')
    try:
        text=raw.decode('utf-8')
        controls=any(ord(character)<32 and character not in '\n\r\t' for character in text)
    except UnicodeDecodeError:text=None;controls=True
    binary=binary_suffix or controls or raw.startswith((b'PK',b'\x1f\x8b',b'%PDF-',b'\x89PNG')) or zipfile.is_zipfile(io.BytesIO(raw))
    if not binary and len(raw)<_B15_TARGET:return dict(allow_chat=True,blocked=False,text=text,bytes=len(raw))
    digest=sha256(raw);path=_b7_safe_path(ROOT/'imports/chat_blobs'/digest/filename)
    path.parent.mkdir(parents=True,exist_ok=True)
    _b8_publish_new(path,raw)
    return dict(allow_chat=False,blocked=True,reason='BINARY_OR_ARCHIVE' if binary else 'VIEW_BUDGET',path=str(path),sha256=digest,bytes=len(raw),chat_reference='Stored on disk: '+filename+' [sha256:'+digest+']')


def sweep_expired_ring_buffer(staging,max_age=600):
    """Purge only unlocked scratch-suffix files in the dedicated external ring.

    Uses no-follow directory descriptors and nonblocking advisory file locks.
    Hardlinks, read-only files, symlinks and lock-marked directories are retained.
    Cooperating producers must use the same advisory locks during writes.
    """
    if type(max_age) not in (int,float) or not math.isfinite(max_age) or max_age<600:raise ValueError('Expiry must be at least600seconds')
    allowed=WORKSPACE/'01_STAGING_INBOX'/'ring_buffer';candidate=Path(staging).absolute()
    if '..' in Path(staging).parts or not candidate.is_relative_to(allowed) or candidate.is_relative_to(ROOT) or allowed.is_relative_to(ROOT):raise ValueError('Dedicated external ring_buffer staging required')
    for item in (candidate,*candidate.parents):
        if item.is_symlink():raise ValueError('Symlink staging path rejected')
    descriptors=[];deleted=[];retained=[];now=_b8_time.time();visited=0
    try:
        root_fd=os.open(WORKSPACE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);descriptors.append(root_fd)
        for part in candidate.relative_to(WORKSPACE).parts:
            if any(marker in os.listdir(root_fd) for marker in ('.lock','.locked','LOCKED')):raise AuditRejected('Locked staging ancestor')
            root_fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=root_fd);descriptors.append(root_fd)
        def walk(directory,relative,depth):
            nonlocal visited
            if depth>16:raise AuditRejected('Ring nesting limit exceeded')
            names=sorted(os.listdir(directory))
            if any(name in names for name in ('.lock','.locked','LOCKED')):
                retained.append(dict(path=relative,reason='LOCKED_DIRECTORY'));return
            if not os.fstat(directory).st_mode&0o222:
                retained.append(dict(path=relative,reason='READ_ONLY_DIRECTORY'));return
            for name in names:
                visited+=1
                if visited>10000:raise AuditRejected('Ring entry limit exceeded')
                rel=str(Path(relative)/name)
                try:
                    info=os.stat(name,dir_fd=directory,follow_symlinks=False)
                    if _b8_stat.S_ISDIR(info.st_mode):
                        child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
                        try:walk(child,rel,depth+1)
                        finally:os.close(child)
                        continue
                    if not _b8_stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or not info.st_mode&0o222 or Path(name).suffix.lower() not in ('.tmp','.scratch','.cache','.buffer') or name+'.lock' in names:
                        retained.append(dict(path=rel,reason='PROTECTED_OR_NON_SCRATCH'));continue
                    if now-info.st_mtime<=max_age:
                        retained.append(dict(path=rel,reason='NOT_EXPIRED'));continue
                    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
                    try:
                        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                        except BlockingIOError:
                            retained.append(dict(path=rel,reason='ACTIVE_LOCK'));continue
                        fresh=os.fstat(fd);entry=os.stat(name,dir_fd=directory,follow_symlinks=False)
                        if (fresh.st_dev,fresh.st_ino,fresh.st_mtime_ns,fresh.st_size,fresh.st_nlink)!=(info.st_dev,info.st_ino,info.st_mtime_ns,info.st_size,1) or (entry.st_dev,entry.st_ino)!=(fresh.st_dev,fresh.st_ino):
                            retained.append(dict(path=rel,reason='CHANGED_DURING_SCAN'));continue
                        os.unlink(name,dir_fd=directory);deleted.append(rel)
                    finally:os.close(fd)
                except (FileNotFoundError,PermissionError) as error:retained.append(dict(path=rel,reason=type(error).__name__))
        walk(root_fd,'.',0)
        return dict(deleted=deleted,retained=retained,deleted_count=len(deleted),scope=str(candidate),max_age_seconds=max_age,vault_touched=False)
    finally:
        for descriptor in reversed(descriptors):os.close(descriptor)


_B16_TABLES={'b16_docs','b16_search_choices','b16_ledger'}

def _b16_owned(name):return name in _B16_TABLES or name=='b16_fts' or name.startswith('b16_fts_')


@contextlib.contextmanager
def _b16_transaction(db,write=False):
    path=_b7_safe_path(db)
    if write:path.parent.mkdir(parents=True,exist_ok=True)
    if not write and not path.is_file():raise AuditRejected('Search database missing')
    connection=sqlite3.connect(path if write else path.as_uri()+'?mode=ro',uri=not write,timeout=20,isolation_level=None)
    try:
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        if write:
            connection.execute('CREATE TABLE IF NOT EXISTS b16_docs (doc TEXT PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,sha256 TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS b16_search_choices (id INTEGER PRIMARY KEY,query TEXT NOT NULL,results_json TEXT NOT NULL,decision TEXT NOT NULL,created_at TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS b16_ledger (project TEXT NOT NULL,seq INTEGER NOT NULL,event_date TEXT NOT NULL,event_type TEXT NOT NULL,summary TEXT NOT NULL,ref TEXT NOT NULL,event_hash TEXT NOT NULL,PRIMARY KEY(project,seq),UNIQUE(project,event_hash))')
        names=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if not _b16_owned(n)]
        before={n:_b11_table_snapshot(connection,n) for n in names} if write else {}
        yield connection
        if names!=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if not _b16_owned(n)] or any(_b11_table_snapshot(connection,n)!=v for n,v in before.items()):raise AuditRejected('Unrelated SQLite records changed')
        connection.commit()
    except BaseException:
        connection.rollback();raise
    finally:connection.close()


def init_and_index_fts5(db,doc,title,body):
    """Store exact source and maintain an optional local FTS5 index."""
    _b7_identifier(doc)
    if not isinstance(title,str) or not isinstance(body,str) or len(title.encode())>1000000 or len(body.encode())>16000000:raise ValueError('Bounded UTF-8 title/body required')
    digest=sha256((title+'\0'+body).encode())
    with _b16_transaction(db,True) as connection:
        try:connection.execute('CREATE VIRTUAL TABLE IF NOT EXISTS b16_fts USING fts5(doc UNINDEXED,title,body)')
        except sqlite3.OperationalError as error:raise AuditRejected('SQLite FTS5 extension unavailable') from error
        prior=connection.execute('SELECT title,body,sha256 FROM b16_docs WHERE doc=?',(doc,)).fetchone()
        if prior is not None:
            if prior!=(title,body,digest):raise AuditRejected('Document identity already contains different text')
            indexed=connection.execute('SELECT title,body FROM b16_fts WHERE doc=?',(doc,)).fetchone()
            if indexed!=(title,body):raise AuditRejected('FTS5 index is missing or differs from source')
            return dict(status='MOUNTED_EXISTING',doc=doc,sha256=digest,indexed=True,fts5=True)
        connection.execute('INSERT INTO b16_docs VALUES (?,?,?,?)',(doc,title,body,digest))
        connection.execute('INSERT INTO b16_fts(doc,title,body) VALUES (?,?,?)',(doc,title,body))
        if connection.execute('SELECT title,body FROM b16_fts WHERE doc=?',(doc,)).fetchone()!=(title,body):raise AuditRejected('FTS5 indexing verification failed')
        return dict(status='INDEXED',doc=doc,sha256=digest,indexed=True,fts5=True)


def locate_exact_source_quote(db,doc,quote):
    """Return exact zero-based character offsets and one-based source lines."""
    _b7_identifier(doc)
    if not isinstance(quote,str) or not quote:raise ValueError('Nonempty exact quote required')
    with _b16_transaction(db) as connection:
        row=connection.execute('SELECT body,sha256 FROM b16_docs WHERE doc=?',(doc,)).fetchone()
        if row is None:raise AuditRejected('Source document not indexed')
        if sha256((connection.execute('SELECT title FROM b16_docs WHERE doc=?',(doc,)).fetchone()[0]+'\0'+row[0]).encode())!=row[1]:raise AuditRejected('Source document hash mismatch')
        offsets=[];start=0
        while True:
            offset=row[0].find(quote,start)
            if offset<0:break
            end=offset+len(quote);line=row[0].count('\n',0,offset)+1;end_line=row[0].count('\n',0,end)+1
            offsets.append(dict(start=offset,end=end,start_line=line,end_line=end_line))
            start=offset+max(1,len(quote))
        return dict(doc=doc,quote=quote,found=bool(offsets),occurrences=offsets,sha256=row[1],offset_unit='unicode_code_points',line_base=1)


def record_search_with_save_choice(db,query,results,decision):
    """Record an explicit save/discard decision; persist results only on save."""
    if not isinstance(query,str) or not query.strip() or len(query.encode())>100000:raise ValueError('Bounded nonempty query required')
    if decision not in ('save','discard'):raise ValueError('Explicit save or discard decision required')
    result_json=_b13_json(results)
    if len(result_json.encode())>4000000:raise ValueError('Search result set exceeds4MiB')
    stored=result_json if decision=='save' else '[]'
    with _b16_transaction(db,True) as connection:
        cursor=connection.execute('INSERT INTO b16_search_choices(query,results_json,decision,created_at) VALUES (?,?,?,?)',(query,stored,decision,dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')))
        return dict(id=cursor.lastrowid,decision=decision,results_saved=decision=='save',result_count=len(results) if isinstance(results,(list,dict)) else None,query_sha256=sha256(query.encode()))


def _b16_date(value):
    if not isinstance(value,str) or len(value)!=10:raise ValueError('ISO date YYYY-MM-DD required')
    try:parsed=dt.date.fromisoformat(value)
    except ValueError as error:raise ValueError('Valid ISO calendar date required') from error
    if parsed.isoformat()!=value:raise ValueError('Canonical ISO date required')
    return value


def _b16_hash(value):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Lowercase SHA-256 hex required')
    return value


def prevent_duplicate_ledger_entry(db,project,event_hash):
    """Check a project-scoped event hash without modifying or repairing rows."""
    _b7_identifier(project);_b16_hash(event_hash)
    with _b16_transaction(db) as connection:
        row=connection.execute('SELECT seq,event_date,event_type,summary,ref FROM b16_ledger WHERE project=? AND event_hash=?',(project,event_hash)).fetchone()
        return dict(duplicate=row is not None,project=project,hash=event_hash,entry=dict(seq=row[0],date=row[1],type=row[2],summary=row[3],ref=row[4]) if row else None)


def append_chronological_ledger(db,project,date,type,summary,ref):
    """Append one deterministic event if its event date does not precede history."""
    _b7_identifier(project);date=_b16_date(date)
    for label,value,limit in (('type',type,128),('summary',summary,12000),('ref',ref,2048)):
        if not isinstance(value,str) or not value.strip() or len(value.encode())>limit:raise ValueError('Bounded nonempty '+label+' required')
    identity=dict(project=project,date=date,type=type,summary=summary,ref=ref)
    event_hash=sha256(_b13_json(identity).encode())
    with _b16_transaction(db,True) as connection:
        existing=connection.execute('SELECT seq,event_date,event_type,summary,ref FROM b16_ledger WHERE project=? AND event_hash=?',(project,event_hash)).fetchone()
        if existing:return dict(status='MOUNTED_DUPLICATE',duplicate=True,seq=existing[0],date=existing[1],hash=event_hash)
        latest=connection.execute('SELECT event_date FROM b16_ledger WHERE project=? ORDER BY seq DESC LIMIT 1',(project,)).fetchone()
        if latest and date<latest[0]:raise AuditRejected('Chronological ledger cannot append an earlier date')
        seq=connection.execute('SELECT COALESCE(MAX(seq),0)+1 FROM b16_ledger WHERE project=?',(project,)).fetchone()[0]
        connection.execute('INSERT INTO b16_ledger VALUES (?,?,?,?,?,?,?)',(project,seq,date,type,summary,ref,event_hash))
        return dict(status='APPENDED',duplicate=False,seq=seq,date=date,hash=event_hash)


_B17_TABLES={'b17_trash','b17_draft_versions'}
_B17_HOLD=86400


@contextlib.contextmanager
def _b17_transaction(db,write=False):
    path=_b7_safe_path(db)
    if write:path.parent.mkdir(parents=True,exist_ok=True)
    if not write and not path.is_file():raise AuditRejected('Privacy database missing')
    connection=sqlite3.connect(path if write else path.as_uri()+'?mode=ro',uri=not write,timeout=20,isolation_level=None)
    try:
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        if write:
            connection.execute('CREATE TABLE IF NOT EXISTS b17_trash (item TEXT PRIMARY KEY,original_path TEXT NOT NULL,payload BLOB NOT NULL,deleted_at TEXT NOT NULL,expires_at TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ("HELD","RESTORED","PURGED")))')
            connection.execute('CREATE TABLE IF NOT EXISTS b17_draft_versions (draft TEXT NOT NULL,revision INTEGER NOT NULL,sha256 TEXT NOT NULL,body BLOB NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(draft,revision))')
        names=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if n not in _B17_TABLES]
        before={n:_b11_table_snapshot(connection,n) for n in names} if write else {}
        yield connection
        if names!=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if n not in _B17_TABLES] or any(_b11_table_snapshot(connection,n)!=v for n,v in before.items()):raise AuditRejected('Unrelated records changed')
        connection.commit()
    except BaseException:connection.rollback();raise
    finally:connection.close()


def _b17_time(value):
    if not isinstance(value,str):raise ValueError('Timezone-aware ISO timestamp required')
    try:parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as error:raise ValueError('Valid ISO timestamp required') from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:raise ValueError('Timestamp must include timezone')
    return parsed.astimezone(dt.timezone.utc)


def soft_delete_with_24h_hold(db,item,deleted_at):
    """Move bounded file bytes into an SQLite hold; original removed only after commit."""
    path=_b7_safe_path(item);_b7_identifier(path.name);stamp=_b17_time(deleted_at);key=str(path.relative_to(ROOT))
    if not path.exists():
        with _b17_transaction(db) as connection:
            held=connection.execute('SELECT payload,deleted_at,expires_at,status FROM b17_trash WHERE item=?',(key,)).fetchone()
            if held and held[3]=='HELD' and held[1]==stamp.isoformat():return dict(status='ALREADY_HELD',item=key,sha256=sha256(held[0]),expires_at=held[2])
    if not path.is_file() or path.is_symlink():raise ValueError('Existing regular vault file required')
    if path.stat().st_size>16000000:raise ValueError('Soft-delete hold is limited to16MiB')
    payload=path.read_bytes();digest=sha256(payload)
    with _b17_transaction(db,True) as connection:
        old=connection.execute('SELECT original_path,payload,deleted_at,expires_at,status FROM b17_trash WHERE item=?',(key,)).fetchone()
        expires=(stamp+dt.timedelta(seconds=_B17_HOLD)).isoformat()
        if old:
            if old[0]!=key or old[1]!=payload or old[4]!='HELD':raise AuditRejected('Existing trash identity conflicts')
            return dict(status='ALREADY_HELD',item=key,sha256=digest,expires_at=old[3])
        connection.execute('INSERT INTO b17_trash VALUES (?,?,?,?,?,?)',(key,key,payload,stamp.isoformat(),expires,'HELD'))
    path.unlink()
    return dict(status='HELD',item=key,sha256=digest,deleted_at=stamp.isoformat(),expires_at=expires,purged=False)


def restore_or_purge_trash_item(db,item,action,now):
    """Restore to the original vault path or purge only after the exact 24-hour hold."""
    target_path=_b7_safe_path(item);key=str(target_path.relative_to(ROOT))
    if action not in ('restore','purge'):raise ValueError('Explicit restore or purge required')
    current=_b17_time(now)
    with _b17_transaction(db,True) as connection:
        row=connection.execute('SELECT original_path,payload,deleted_at,expires_at,status FROM b17_trash WHERE item=?',(key,)).fetchone()
        if row is None:raise AuditRejected('Trash item not found')
        if row[4]!='HELD':raise AuditRejected('Trash item already finalized')
        target=_b7_safe_path(row[0]);expiry=_b17_time(row[3])
        if action=='purge' and current<expiry:raise AuditRejected('24-hour hold has not elapsed')
        if action=='restore' and current>expiry:raise AuditRejected('Restore window expired; purge is the only action')
        if action=='restore':
            if target.exists():raise AuditRejected('Restore target occupied; refusing overwrite')
            target.parent.mkdir(parents=True,exist_ok=True);_b4_write(target,row[1]);status='RESTORED'
        else:
            status='PURGED'
        connection.execute('UPDATE b17_trash SET status=?,payload=CASE WHEN ?=\'PURGED\' THEN X\'\' ELSE payload END WHERE item=?',(status,status,key))
        return dict(status=status,item=key,sha256=sha256(row[1]),expires_at=row[3],restored=action=='restore',purged=action=='purge')


def apply_in_place_draft_correction(db,draft,patch):
    """Archive exact prior bytes, then atomically replace a hash-guarded text draft."""
    path=_b7_safe_path(draft);_b7_identifier(path.name)
    if not isinstance(patch,dict) or set(patch)!={'expected_sha256','replacements'}:raise ValueError('Expected hash and replacements required')
    if not path.is_file() or path.is_symlink():raise ValueError('Existing draft file required')
    before=path.read_bytes()
    if len(before)>4000000:raise ValueError('Draft exceeds4MiB')
    if sha256(before)!=patch['expected_sha256']:raise AuditRejected('Draft changed since patch was prepared')
    try:text=before.decode('utf-8')
    except UnicodeDecodeError as error:raise ValueError('UTF-8 text draft required') from error
    replacements=patch['replacements']
    if not isinstance(replacements,list) or not replacements or len(replacements)>1000:raise ValueError('Bounded replacement list required')
    result=text
    for change in replacements:
        if not isinstance(change,dict) or set(change)!={'old','new'} or not isinstance(change['old'],str) or not change['old'] or not isinstance(change['new'],str):raise ValueError('Exact old/new text required')
        if result.count(change['old'])!=1:raise AuditRejected('Each correction must match exactly once')
        result=result.replace(change['old'],change['new'],1)
    after=result.encode()
    if after==before:raise ValueError('Correction makes no change')
    temporary=verify_safe_path('state/draft_'+uuid.uuid4().hex+'.tmp')
    with _b17_transaction(db,True) as connection:
        revision=connection.execute('SELECT COALESCE(MAX(revision),0)+1 FROM b17_draft_versions WHERE draft=?',(str(path.relative_to(ROOT)),)).fetchone()[0]
        connection.execute('INSERT INTO b17_draft_versions VALUES (?,?,?,?,?)',(str(path.relative_to(ROOT)),revision,sha256(before),before,dt.datetime.now(dt.timezone.utc).isoformat()))
    try:
        _b4_write(temporary,after)
        if sha256(path.read_bytes())!=patch['expected_sha256']:raise AuditRejected('Draft changed before atomic publication')
        os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)
    return dict(status='CORRECTED_IN_PLACE',draft=str(path.relative_to(ROOT)),revision=revision,prior_sha256=sha256(before),current_sha256=sha256(after),prior_archived=True)


_B17_PHONE=r'(?<!\d)(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]?\d{4}(?!\d)'
_B17_EMAIL=r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'
_B17_POSTAL=r'(?i)\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d\b'
_B17_STREET=r"(?i)\b\d{1,6}\s+[A-Z0-9][A-Z0-9 .'-]{1,60}\s(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|court|ct|way)\b"


def redact_personal_identifiers(text,custom=None):
    """Mask common phone, email, Canadian postal and street address patterns."""
    if not isinstance(text,str):raise ValueError('Text required')
    if custom is None:custom=[]
    if not isinstance(custom,(list,tuple,set)) or any(not isinstance(x,str) or not x for x in custom):raise ValueError('Custom names must be nonempty strings')
    result=re.sub(_B17_EMAIL,'[REDACTED]',text);result=re.sub(_B17_PHONE,'[REDACTED]',result);result=re.sub(_B17_POSTAL,'[REDACTED]',result);result=re.sub(_B17_STREET,'[REDACTED]',result)
    for name in sorted(set(custom),key=len,reverse=True):result=re.sub(re.escape(name),'[REDACTED]',result,flags=re.IGNORECASE)
    return result


def verify_owner_privacy_mask(bundle):
    """Check public ZIP/dict/text for obvious personal data and identity metadata."""
    issues=[];parts=[]
    if isinstance(bundle,dict):
        if bundle.get('pseudonym')!='Donald Duck':issues.append('PSEUDONYM_MUST_BE_DONALD_DUCK')
        parts.append(json.dumps(bundle,ensure_ascii=False,sort_keys=True))
    elif isinstance(bundle,(str,Path)):
        path=Path(bundle)
        if path.is_file() and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    parts.append(info.filename)
                    if info.extra:issues.append('ZIP_EXTRA_METADATA')
                    if info.comment:issues.append('ZIP_COMMENT_METADATA')
                    if info.file_size>20000000:issues.append('BUNDLE_MEMBER_TOO_LARGE');continue
                    raw=archive.read(info)
                    try:parts.append(raw.decode('utf-8'))
                    except UnicodeDecodeError:issues.append('BINARY_MEMBER_REQUIRES_REVIEW')
        elif path.is_file():parts.append(path.read_text(encoding='utf-8'))
        else:parts.append(str(bundle))
    else:raise ValueError('Dictionary, text or ZIP path required')
    joined='\n'.join(parts)
    for label,pattern in [('EMAIL',_B17_EMAIL),('PHONE',_B17_PHONE),('POSTAL',_B17_POSTAL),('STREET_ADDRESS',_B17_STREET)]:
        if re.search(pattern,joined):issues.append('PERSONAL_'+label)
    forbidden=r'(?i)\b(?:owner_email|owner_name|account_id|username|author_email|source_path|absolute_path|gps|latitude|longitude)\s*["\']?\s*[:=]'
    if re.search(forbidden,joined):issues.append('PRIVATE_METADATA_FIELD')
    if 'Donald Duck' not in joined:issues.append('PSEUDONYM_MISSING')
    return dict(passed=not issues,status='GREEN' if not issues else 'RED',issues=sorted(set(issues)),pseudonym='Donald Duck',scope='HEURISTIC_PUBLIC_BUNDLE_SCAN')


_B18_TABLES={'b18_helpful_inquiries','b18_alerts'}
_B18_LEVELS={'BEGINNER','NOVICE','EXPERT'}


def format_guidance_by_level(topic,level='BEGINNER'):
    """Produce deterministic level-specific scaffolding without claiming facts."""
    if not isinstance(topic,str) or not topic.strip() or len(topic)>500:raise ValueError('Topic must be nonempty and <=500 characters')
    if not isinstance(level,str) or level.upper() not in _B18_LEVELS:raise ValueError('Level must be BEGINNER, NOVICE or EXPERT')
    level=level.upper()
    templates={
      'BEGINNER':('Start with a plain-language explanation of {topic}.','Define unfamiliar terms and give one small example.','Checklist: goal; steps; expected result; one safe next action.'),
      'NOVICE':('Explain {topic} with its key parts and how they relate.','Show a short worked example, then common errors and checks.','Checklist: prerequisites; ordered steps; validation; recovery.'),
      'EXPERT':('Frame {topic} by assumptions, interfaces, tradeoffs and failure modes.','Give a concise implementation or decision outline with measurable checks.','Checklist: invariants; edge cases; evidence; rollback; unresolved risks.')}
    explanation,example,checklist=templates[level]
    return dict(topic=topic.strip(),level=level,explanation=explanation.format(topic=topic.strip()),example_guidance=example,checklist=checklist,deterministic=True,source_claims_added=False)


def predict_next_workflow_step(stage,workflow_map):
    """Return an explicit deterministic next stage and choices from caller map."""
    if not isinstance(stage,str) or not stage.strip() or len(stage)>256:raise ValueError('Stage required')
    if not isinstance(workflow_map,dict):raise ValueError('Workflow map dictionary required')
    options=workflow_map.get(stage)
    if not isinstance(options,list) or not options or any(not isinstance(option,str) or not option.strip() for option in options):return dict(status='GRAY',stage=stage,options=[],next_step=None,reason='No explicit transition configured')
    choices=sorted(set(options),key=lambda value:(value.casefold(),value))
    if len(choices)!=len(options):raise ValueError('Duplicate workflow choices')
    return dict(status='GREEN',stage=stage,options=choices,next_step=choices[0] if len(choices)==1 else None,owner_choice_required=len(choices)>1,deterministic=True)


@contextlib.contextmanager
def _b18_transaction(db,write=False):
    path=_b7_safe_path(db)
    if write:path.parent.mkdir(parents=True,exist_ok=True)
    if not write and not path.is_file():raise AuditRejected('Alert database missing')
    connection=sqlite3.connect(path if write else path.as_uri()+'?mode=ro',uri=not write,timeout=20,isolation_level=None)
    try:
        connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        if write:
            connection.execute('CREATE TABLE IF NOT EXISTS b18_alerts (id INTEGER PRIMARY KEY,severity TEXT NOT NULL,code TEXT NOT NULL,msg TEXT NOT NULL,created_at TEXT NOT NULL,acknowledged INTEGER NOT NULL CHECK(acknowledged IN (0,1)))')
            connection.execute('CREATE TABLE IF NOT EXISTS b18_helpful_inquiries (id INTEGER PRIMARY KEY,category TEXT NOT NULL,msg TEXT NOT NULL,created_at TEXT NOT NULL,public_exposure INTEGER NOT NULL CHECK(public_exposure=0),status TEXT NOT NULL CHECK(status="LOCAL_ONLY"))')
        names=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if n not in _B18_TABLES]
        before={n:_b11_table_snapshot(connection,n) for n in names} if write else {}
        yield connection
        if names!=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if n not in _B18_TABLES] or any(_b11_table_snapshot(connection,n)!=v for n,v in before.items()):raise AuditRejected('Unrelated records changed')
        connection.commit()
    except BaseException:connection.rollback();raise
    finally:connection.close()


def emit_system_alert(db,severity,code,msg):
    """Append an alert with a single safe acknowledgement action, never execute UI."""
    if severity not in ('Critical','Warning','Info'):raise ValueError('Critical, Warning or Info required')
    _b7_identifier(code)
    if not isinstance(msg,str) or not msg.strip() or len(msg)>4000:raise ValueError('Alert message required and bounded')
    actions={'Critical':{'label':'Acknowledge','action':'acknowledge_only'},'Warning':{'label':'Review','action':'open_local_diagnostics'},'Info':{'label':'Dismiss','action':'dismiss'}}
    with _b18_transaction(db,True) as connection:
        cursor=connection.execute('INSERT INTO b18_alerts(severity,code,msg,created_at,acknowledged) VALUES (?,?,?,?,0)',(severity,code,msg,dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')))
        return dict(id=cursor.lastrowid,severity=severity,code=code,action=actions[severity],one_click=True,external_effect=False)


def submit_discreet_help_inquiry(db,category,msg):
    """Store help-only inquiry locally; no public feed, network or send action."""
    if category not in ('Bug','Engine'):raise ValueError('Bug or Engine category required')
    if not isinstance(msg,str) or not msg.strip() or len(msg)>12000:raise ValueError('Inquiry message required and bounded')
    with _b18_transaction(db,True) as connection:
        cursor=connection.execute('INSERT INTO b18_helpful_inquiries(category,msg,created_at,public_exposure,status) VALUES (?,?,?,?,?)',(category,msg,dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),0,'LOCAL_ONLY'))
        return dict(id=cursor.lastrowid,category=category,status='LOCAL_ONLY',public_exposure=False,transmitted=False)


def _b18_version(value):
    if not isinstance(value,str):raise ValueError('Semantic version string required')
    match=re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?',value)
    if not match:raise ValueError('Canonical major.minor.patch version required')
    major,minor,patch,pre=match.groups();parts=tuple(map(int,(major,minor,patch)))
    prerelease=tuple((0,int(piece)) if piece.isdigit() else (1,piece) for piece in pre.split('.')) if pre else None
    return parts,prerelease


def check_available_engine_updates(local,remote):
    """Compare installed/available metadata; never fetch, install, or opt in."""
    if not isinstance(local,dict) or not isinstance(remote,dict) or not isinstance(local.get('engine_id'),str) or local.get('engine_id')!=remote.get('engine_id'):raise ValueError('Matching engine metadata required')
    _b7_identifier(local['engine_id']);lv,lp=_b18_version(local.get('version'));rv,rp=_b18_version(remote.get('version'))
    if rv!=lv:newer=rv>lv
    elif lp is None:newer=False
    elif rp is None:newer=True
    else:newer=rp<lp
    return dict(engine_id=local['engine_id'],local_version=local['version'],available_version=remote['version'],update_available=newer,upgrade_performed=False,user_opt_in_required=newer,install_authorized=False,remote_metadata_only=True)


import secrets as _b19_secrets

_B19_MAGIC=b'APCCS-ENC-1\x00'
_B19_ROUNDS=200000


def verify_clean_device_recovery_bundle(zip):
    """Validate recovery member set, paths, hashes and mandatory core/recovery files."""
    path=Path(zip)
    if not path.is_file():raise ValueError('Recovery ZIP path required')
    required={'code/apccs_core.py','audit/pass_tests.json','RECOVER.md','RECOVERY_MANIFEST.json'}
    try:
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist()
            if len(names)!=len(set(names)) or archive.testzip() is not None:raise AuditRejected('Duplicate or corrupt ZIP member')
            if any(Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name for name in names):raise AuditRejected('Unsafe ZIP member path')
            missing=sorted(required-set(names))
            if missing:raise AuditRejected('Recovery bundle missing required members: '+','.join(missing))
            manifest=json.loads(archive.read('RECOVERY_MANIFEST.json'))
            if not isinstance(manifest,dict) or not isinstance(manifest.get('files'),dict):raise AuditRejected('Recovery manifest schema invalid')
            bad=[]
            for name,record in manifest['files'].items():
                if name not in names or not isinstance(record,dict) or set(record)<{'size','sha256'}:bad.append(name);continue
                raw=archive.read(name)
                if len(raw)!=record['size'] or sha256(raw)!=record['sha256']:bad.append(name)
            if bad:raise AuditRejected('Recovery manifest digest mismatch')
            source=archive.read('code/apccs_core.py')
            if not archive.read('RECOVER.md').strip():raise AuditRejected('Recovery summary empty')
            tests=json.loads(archive.read('audit/pass_tests.json'))
            return dict(passed=True,status='GREEN',members=len(names),required_members=sorted(required),manifest_files=len(manifest['files']),core_sha256=sha256(source),tests_passed=tests.get('passed') is True)
    except (zipfile.BadZipFile,KeyError,json.JSONDecodeError) as error:raise AuditRejected('Recovery ZIP structure invalid') from error


def export_optional_encrypted_backup(data,passphrase=None):
    """Create plain one-click bytes or password-authenticated backup envelope.

    Encryption uses PBKDF2-HMAC-SHA256 plus HMAC-derived counter stream and
    encrypt-then-MAC. This standard-library construction is not a reviewed
    general-purpose cryptographic library; use only for this portable feature,
    not high-value secrets. Cleartext output occurs only when explicitly no
    passphrase is supplied and is visibly tagged as unencrypted.
    """
    if not isinstance(data,(bytes,bytearray,memoryview)):raise ValueError('Backup bytes required')
    raw=bytes(data)
    if len(raw)>100000000:raise ValueError('Backup exceeds100MB')
    if passphrase is None:return _B19_MAGIC+b'PLN1'+len(raw).to_bytes(8,'big')+hashlib.sha256(raw).digest()+raw
    if not isinstance(passphrase,str) or len(passphrase)<12 or len(passphrase)>4096:raise ValueError('Passphrase must contain12..4096 characters')
    salt=_b19_secrets.token_bytes(16);nonce=_b19_secrets.token_bytes(16);key=hashlib.pbkdf2_hmac('sha256',passphrase.encode(),salt,_B19_ROUNDS,dklen=64)
    stream=bytearray();counter=0
    while len(stream)<len(raw):stream.extend(hmac.new(key[:32],b'APCCS-STREAM'+nonce+counter.to_bytes(8,'big'),hashlib.sha256).digest());counter+=1
    cipher=bytes(a^b for a,b in zip(raw,stream));header=_B19_MAGIC+b'ENC1'+_B19_ROUNDS.to_bytes(4,'big')+salt+nonce+len(cipher).to_bytes(8,'big')+cipher
    tag=hmac.new(key[32:],header,hashlib.sha256).digest()
    return header+tag


def _b19_open_backup(envelope,passphrase=None):
    raw=bytes(envelope)
    if not raw.startswith(_B19_MAGIC) or len(raw)<len(_B19_MAGIC)+4:raise ValueError('Unknown backup format')
    offset=len(_B19_MAGIC);kind=raw[offset:offset+4];offset+=4
    if kind==b'PLN1':
        if passphrase is not None:raise ValueError('Plain backup takes no passphrase')
        if len(raw)<offset+40:raise AuditRejected('Truncated plain backup')
        size=int.from_bytes(raw[offset:offset+8],'big');digest=raw[offset+8:offset+40];data=raw[offset+40:]
        if len(data)!=size or not hmac.compare_digest(hashlib.sha256(data).digest(),digest):raise AuditRejected('Plain backup checksum mismatch')
        return data
    if kind!=b'ENC1' or not isinstance(passphrase,str) or len(raw)<offset+4+16+16+8+32:raise ValueError('Encrypted backup and passphrase required')
    rounds=int.from_bytes(raw[offset:offset+4],'big');offset+=4
    if rounds!=_B19_ROUNDS:raise AuditRejected('Unsupported KDF work factor')
    salt=raw[offset:offset+16];nonce=raw[offset+16:offset+32];size=int.from_bytes(raw[offset+32:offset+40],'big');cipher=raw[offset+40:-32];tag=raw[-32:]
    if size!=len(cipher) or size>100000000:raise AuditRejected('Encrypted backup length mismatch')
    key=hashlib.pbkdf2_hmac('sha256',passphrase.encode(),salt,rounds,dklen=64)
    if not hmac.compare_digest(hmac.new(key[32:],raw[:-32],hashlib.sha256).digest(),tag):raise AuditRejected('Backup authentication failed')
    stream=bytearray();counter=0
    while len(stream)<size:stream.extend(hmac.new(key[:32],b'APCCS-STREAM'+nonce+counter.to_bytes(8,'big'),hashlib.sha256).digest());counter+=1
    return bytes(a^b for a,b in zip(cipher,stream))


def load_state_with_slot_fallback(slot_a,slot_b):
    """Validate SHA-256 sealed slot JSON and choose highest sequence; fallback older."""
    candidates=[];errors=[]
    for name,value in (('slot_a',slot_a),('slot_b',slot_b)):
        try:
            raw=Path(value).read_bytes() if isinstance(value,(str,Path)) else bytes(value)
            obj=json.loads(raw)
            if not isinstance(obj,dict) or set(obj)!={'sequence','payload','sha256'} or type(obj['sequence']) is not int or obj['sequence']<0:raise ValueError('Slot schema invalid')
            body=_b13_json(dict(sequence=obj['sequence'],payload=obj['payload']))
            if not hmac.compare_digest(sha256(body.encode()),obj['sha256']):raise AuditRejected('Slot checksum mismatch')
            candidates.append((obj['sequence'],name,obj['payload'],obj['sha256']))
        except (OSError,ValueError,TypeError,UnicodeError,json.JSONDecodeError,AuditRejected) as error:errors.append(dict(slot=name,reason=str(error)))
    if not candidates:return dict(status='RED',loaded=False,payload=None,sequence=None,errors=errors)
    candidates.sort(key=lambda row:(row[0],row[1]),reverse=True);chosen=candidates[0]
    return dict(status='GREEN' if not errors else 'YELLOW',loaded=True,payload=chosen[2],sequence=chosen[0],source_slot=chosen[1],sha256=chosen[3],fallback=bool(errors),errors=errors)


def batch_mount_multiple_engines(db,manifests):
    """Validate then register multiple engines in one atomic SQLite transaction."""
    if not isinstance(manifests,list) or not manifests or len(manifests)>100:raise ValueError('One to100 engine manifests required')
    ids=[]
    for manifest in manifests:
        verdict=validate_engine_manifest(manifest)
        if not verdict['passed']:raise ValueError('Invalid manifest: '+'; '.join(verdict['errors']))
        ids.append(manifest['engine_id'])
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate engine IDs in batch')
    path=_b7_safe_path(db);path.parent.mkdir(parents=True,exist_ok=True);connection=sqlite3.connect(path,timeout=20,isolation_level=None)
    try:
        connection.execute('PRAGMA foreign_keys=ON');connection.execute('BEGIN IMMEDIATE');_b11_schema(connection)
        names=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if n not in _B11_MANAGED and n not in {'b12_namespace_owners'} and not n.startswith('eng_'+ '')]
        before={n:_b11_table_snapshot(connection,n) for n in names}
        original=set(row[0] for row in connection.execute('SELECT engine_id FROM engine_registry_v2'))
        duplicates=original.intersection(ids)
        if duplicates:raise AuditRejected('Engine already installed: '+','.join(sorted(duplicates)))
        for manifest in manifests:load_engine_from_manifest_in_transaction(connection,manifest)
        current=[n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name") if n not in _B11_MANAGED and n not in {'b12_namespace_owners'} and not n.startswith('eng_'+'')]
        if any(_b11_table_snapshot(connection,n)!=v for n,v in before.items()):raise AuditRejected('User rows changed')
        if set(row[0] for row in connection.execute('SELECT engine_id FROM engine_registry_v2'))!=original|set(ids):raise AuditRejected('Batch engine set differs from request')
        connection.commit();return dict(status='MOUNTED',engine_ids=ids,installed_count=len(ids),atomic=True)
    except BaseException:connection.rollback();raise
    finally:connection.close()


def load_engine_from_manifest_in_transaction(db,manifest):
    verdict=validate_engine_manifest(manifest)
    if not verdict['passed']:raise AuditRejected('Invalid engine manifest')
    identity=manifest['engine_id'];name=manifest['name'];rules=manifest['rules_text'];version=manifest['version'];digest=_engine_hash(identity,name,rules,version)
    db.execute('INSERT INTO engine_registry_v2(engine_id,name,rules_text,version,sha256,state) VALUES (?,?,?,?,?,?)',(identity,name,rules,version,digest,'installed'))
    db.execute('INSERT INTO engine_rules_hashes(engine_id,rules_sha256) VALUES (?,?)',(identity,sha256(rules.encode())))
    book=_b11_store_book(db,identity,rules)
    db.execute('INSERT INTO b11_manifests(engine_id,manifest) VALUES (?,?)',(identity,json.dumps(manifest,sort_keys=True,separators=(',',':'))))
    namespace=_b12_prefix(identity);kv=namespace+'kv';checkpoints=namespace+'checkpoints'
    db.execute('CREATE TABLE IF NOT EXISTS b12_namespace_owners (namespace TEXT PRIMARY KEY,engine_id TEXT UNIQUE NOT NULL)')
    owner=db.execute('SELECT engine_id FROM b12_namespace_owners WHERE namespace=?',(namespace,)).fetchone()
    if owner and owner[0]!=identity:raise AuditRejected('Namespace collision in batch transaction')
    db.execute('INSERT OR IGNORE INTO b12_namespace_owners VALUES (?,?)',(namespace,identity))
    db.execute('CREATE TABLE IF NOT EXISTS "'+kv+'" (key TEXT PRIMARY KEY,value_json TEXT NOT NULL,sha256 TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS "'+checkpoints+'" (checkpoint INTEGER PRIMARY KEY,body TEXT NOT NULL,sha256 TEXT NOT NULL)')
    return dict(engine_id=identity,version=version,rulebook_sha256=book['rulebook_sha256'],namespace=namespace)


def verify_q1_part1_coherence(db,vault):
    """Read-only integrated state, scope, test, canary and recovery consistency check."""
    path=_b7_safe_path(db);root=Path(vault).absolute()
    if root!=ROOT and not root.is_relative_to(ROOT):raise ValueError('Vault must be the mounted APCCS vault')
    if not path.is_file() or not root.is_dir():return dict(passed=False,status='RED',checks={'database':False,'vault':False})
    checks={};issues=[]
    try:
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as connection:
            checks['database_integrity']=connection.execute('PRAGMA integrity_check').fetchone()==('ok',)
            tables={n for n, in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
            checks['engine_schema']='engine_registry_v2' in tables and 'engine_rules_hashes' in tables
            if checks['engine_schema']:
                engines=connection.execute('SELECT engine_id FROM engine_registry_v2 ORDER BY engine_id').fetchall()
                checks['engines']=all(_b11_engine(connection,row[0])[0][4]=='installed' for row in engines)
            else:checks['engines']=False
            if 'b13_locks' in tables:
                valid=True
                for project,payload,digest,readonly in connection.execute('SELECT project,payload,lock_sha256,read_only FROM b13_locks'):
                    valid=valid and readonly==1 and sha256(payload.encode())==digest
                checks['locked_plans']=valid
            else:checks['locked_plans']=True
        recover=root/'RECOVER.md';report=root/'audit/pass_tests.json';checks['recovery_files']=recover.is_file() and report.is_file()
        if checks['recovery_files']:
            content=recover.read_text(encoding='utf-8');test_report=json.loads(report.read_text(encoding='utf-8'))
            checks['canary']=bool(re.search(r'Canary:\s*T\s*=\s*Z\s*->\s*anvil',content))
            checks['audit']=test_report.get('passed') is True and test_report.get('failed_assertions')==[]
            checks['slots']=all((root/'state'/slot).exists() for slot in ('slot_a.json','slot_b.json')) if any((root/'state'/slot).exists() for slot in ('slot_a.json','slot_b.json')) else True
        else:checks.update(canary=False,audit=False,slots=False)
    except (sqlite3.Error,AuditRejected,ValueError,TypeError,json.JSONDecodeError,OSError) as error:issues.append(str(error))
    passed=all(checks.values()) and not issues
    return dict(passed=passed,status='GREEN' if passed else 'RED',checks=checks,issues=issues,scope='LOCAL_READ_ONLY_Q1_PART1_COHERENCE')



def export_q1_part1_schema_map(source):
    """Return compact, deterministic AST directory of functions/classes."""
    text=_b3_source(source);tree=ast.parse(text);entries=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
            args=node.args if not isinstance(node,ast.ClassDef) else None
            signature=None
            if args is not None:
                all_args=args.posonlyargs+args.args+args.kwonlyargs
                signature=node.name+'('+','.join(arg.arg for arg in all_args)+')'
            else:signature=node.name
            entries.append(dict(kind='class' if isinstance(node,ast.ClassDef) else 'function',name=node.name,signature=signature,line=node.lineno,doc=ast.get_docstring(node) or ''))
    entries.sort(key=lambda item:(item['line'],item['kind'],item['name']))
    return dict(schema_version=1,symbol_count=len(entries),symbols=entries,source_sha256=sha256(text.encode()),compact=True)


def verify_1_to_100_symbol_continuity(source):
    """Verify explicit instruction coverage 1..100 and unique top-level symbols."""
    text=_b3_source(source);tree=ast.parse(text)
    ids={int(value) for value in re.findall(r'INST[-_](?:00)?(\d{1,4})',text) if 1<=int(value)<=100}
    if not ids:
        ids={int(value) for value in re.findall(r"INST-'\s*\+\s*str\((\d+)\)",text) if 1<=int(value)<=100}
    missing=sorted(set(range(1,101))-ids)
    names=[node.name for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
    duplicates=sorted(name for name,count in Counter(names).items() if count>1)
    return dict(passed=not missing and not duplicates,status='GREEN' if not missing and not duplicates else 'RED',verified_count=len(ids),missing_instruction_ids=missing,duplicate_symbols=duplicates,scope='EXPLICIT_SOURCE_MARKER_CONTINUITY')


def compact_pass_tests_manifest(pass_tests):
    """Validate and deterministically reduce pass-tests data for quick audit."""
    if isinstance(pass_tests,(str,Path)):
        raw=Path(pass_tests).read_bytes()
        if len(raw)>10000000:raise ValueError('Pass-tests manifest exceeds10MB')
        data=json.loads(raw)
    elif isinstance(pass_tests,dict):data=pass_tests
    else:raise ValueError('Pass-tests object or JSON file required')
    if not isinstance(data,dict) or type(data.get('passed')) is not bool or not isinstance(data.get('failed_assertions'),list):raise ValueError('Valid pass_tests schema required')
    coverage=data.get('instruction_coverage',[])
    if not isinstance(coverage,list) or any(type(value) is not int for value in coverage):raise ValueError('Integer instruction coverage required')
    compact=dict(passed=data['passed'],failed_assertions=data['failed_assertions'],instruction_coverage=coverage,tests_run=data.get('tests_run'),core_sha256=data.get('core_sha256'),test_sha256=data.get('test_sha256'),elapsed_seconds=data.get('elapsed_seconds'),wall_clock_budget_seconds=data.get('wall_clock_budget_seconds'))
    canonical=json.dumps(compact,sort_keys=True,separators=(',',':'),allow_nan=False)
    return dict(manifest=compact,canonical_json=canonical,sha256=sha256(canonical.encode()),bytes=len(canonical.encode()),fast=True)


def generate_cp100_scorecard(db):
    """Render a plain-English scorecard from installed pass_tests evidence."""
    path=_b7_safe_path(db);report_path=ROOT/'audit/pass_tests.json'
    if not report_path.is_file():raise AuditRejected('Installed pass_tests.json missing')
    report=json.loads(report_path.read_text(encoding='utf-8'));coverage=set(report.get('instruction_coverage',[]));rows=['INSTRUCTIONS 1–100 | 10% milestone','Instruction | Result']
    for number in range(1,101):rows.append(f'{number:03d} | '+('GREEN — passing evidence' if number in coverage and report.get('passed') is True else 'GRAY — not verified'))
    rows.append(f'Tests run: {report.get("tests_run","unknown")}')
    rows.append('Failed assertions: '+str(len(report.get('failed_assertions',[]))))
    rows.append('Database integrity: '+('ok' if path.is_file() else 'missing'))
    return '\n'.join(rows)+'\n'


def lock_checkpoint_cp100(vault):
    """Add immutable CP-100 digest seal to an existing Master ZIP and RECOVER."""
    root=Path(vault).absolute();archive_path=_b7_safe_path(root/'exports/APCCS_MASTER_BUILD.zip')
    if not archive_path.is_file():raise AuditRejected('Existing Master archive required')
    with _b4_serial():
        with zipfile.ZipFile(archive_path) as source:
            if source.testzip() is not None or len(source.namelist())!=len(set(source.namelist())):raise AuditRejected('Master ZIP invalid')
            members={name:source.read(name) for name in source.namelist()}
        if 'audit/CP-100_LOCK.json' in members:raise AuditRejected('CP-100 is immutable and already exists')
        required=('code/apccs_core.py','code/test_apccs_core.py','audit/pass_tests.json','RECOVER.md','RECOVERY_MANIFEST.json')
        if any(name not in members for name in required):raise AuditRejected('Master archive missing canonical recovery members')
        report=json.loads(members['audit/pass_tests.json']);coverage=report.get('instruction_coverage',[])
        if report.get('passed') is not True or report.get('failed_assertions')!=[] or coverage!=list(range(1,101)):raise AuditRejected('Passing coverage1..100 required for CP-100')
        excluded={'audit/CP-100_LOCK.json','RECOVERY_MANIFEST.json'}
        seal=dict(checkpoint='CP-100',locally_verified_instructions=100,total_instructions=1000,verification_scope='LOCAL_TEST_EVIDENCE_PENDING_MUSE_ACCEPTANCE',core_sha256=sha256(members['code/apccs_core.py']),test_sha256=sha256(members['code/test_apccs_core.py']),tests_run=report['tests_run'],failed_assertions=[],member_hashes={n:sha256(raw) for n,raw in sorted(members.items()) if n not in excluded})
        members['audit/CP-100_LOCK.json']=(json.dumps(seal,sort_keys=True,indent=2)+'\n').encode()
        recover=members['RECOVER.md'].decode('utf-8');members['RECOVER.md']=(recover+'\nCP-100 local seal recorded; Muse acceptance is separate.\n').encode()
        manifest=dict(build_id='B20_CP100_20261028',files={n:dict(size=len(raw),sha256=sha256(raw)) for n,raw in sorted(members.items()) if n!='RECOVERY_MANIFEST.json'})
        members['RECOVERY_MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
        temp=archive_path.parent/('.cp100_'+uuid.uuid4().hex)
        try:
            with zipfile.ZipFile(temp,'x',zipfile.ZIP_DEFLATED) as output:
                for name,raw in members.items():output.writestr(name,raw)
            with temp.open('rb') as stream:os.fsync(stream.fileno())
            os.replace(temp,archive_path)
        finally:temp.unlink(missing_ok=True)
    return seal
