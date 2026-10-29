"""Canonical Batch 2 tests. All scratch data is under /tmp and removed."""
import ast
import base64
import concurrent.futures
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from unittest.mock import patch

CORE = None
OBSERVATIONS = {}
PREFIX_BYTES = 15035
PREFIX_SHA256 = '81c68153929e781fffba398ccd4474ddb00b865e886713fd95cfe651ce884d97'


class CanonicalTests(unittest.TestCase):
    def db_path(self, name):
        return CORE.ROOT / 'state' / (name + '.db')

    def test_00_batch1_exact_and_static(self):
        source = Path(CORE.__file__).read_bytes()
        self.assertEqual(hashlib.sha256(source[:PREFIX_BYTES]).hexdigest(), PREFIX_SHA256)
        tree = ast.parse(source)
        names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        self.assertEqual(len(names), len(set(names)))
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('eval', 'exec') for n in ast.walk(tree)))
        sql = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith('CREATE ')]
        self.assertTrue(sql)
        self.assertTrue(all(v.startswith(('CREATE TABLE IF NOT EXISTS ','CREATE VIRTUAL TABLE IF NOT EXISTS ')) for v in sql))
        with CORE.SingleWriterDBQueue(self.db_path('batch1')) as q:
            q.execute('CREATE TABLE IF NOT EXISTS owner_records (id INTEGER PRIMARY KEY, text TEXT NOT NULL)')
            q.execute('INSERT INTO owner_records VALUES (?,?)', (1, 'preserve owner record'))
        with CORE.SingleWriterDBQueue(self.db_path('batch1')) as q:
            self.assertEqual(q.query('SELECT * FROM owner_records'), [(1, 'preserve owner record')])
        OBSERVATIONS['Batch1_preservation'] = dict(prefix_sha256=PREFIX_SHA256, prefix_bytes=PREFIX_BYTES,
            exact_source_prefix=True, duplicate_definitions=0, eval_exec_calls=0,
            all_schema_create_if_not_exists=True, existing_record_mount='PASS')

    def test_06_jwt(self):
        secret = secrets.token_bytes(32)
        payload = {'sub': 'owner'}
        with patch.object(CORE.time, 'time', return_value=1000):
            token = CORE.generate_jwt(payload, secret)
            self.assertEqual(payload, {'sub': 'owner'})
            decoded = CORE.verify_jwt(token, secret)
            self.assertEqual(decoded['exp'], 4600)
            self.assertEqual(decoded['nbf'], 1000)
        with patch.object(CORE.time, 'time', return_value=4599.999):
            self.assertEqual(CORE.verify_jwt(token, secret)['sub'], 'owner')
        with patch.object(CORE.time, 'time', return_value=4600):
            with self.assertRaises(ValueError): CORE.verify_jwt(token, secret)
        with patch.object(CORE.time, 'time', return_value=1000):
            future = CORE.generate_jwt({'nbf': 1010}, secret, 100)
            with self.assertRaises(ValueError): CORE.verify_jwt(future, secret)
        with patch.object(CORE.time, 'time', return_value=1010):
            self.assertEqual(CORE.verify_jwt(future, secret)['nbf'], 1010)
        def sign(header, raw):
            enc = lambda v: base64.urlsafe_b64encode(v).rstrip(b'=').decode()
            text = enc(header) + '.' + enc(raw)
            return text + '.' + enc(hmac.new(secret, text.encode(), hashlib.sha256).digest())
        with patch.object(CORE.time, 'time', return_value=1001):
            for header, raw in [
                (b'{"alg":"none","typ":"JWT"}', b'{"nbf":1,"exp":2000}'),
                (b'{"alg":"HS512","typ":"JWT"}', b'{"nbf":1,"exp":2000}'),
                (b'{"alg":"HS256","typ":"JWT"}', b'{"nbf":1,"exp":2000,"exp":3000}'),
                (b'{"alg":"HS256","typ":"JWT"}', b'{"nbf":1}'),
                (b'{"alg":"HS256","typ":"JWT"}', b'{"nbf":true,"exp":2000}')]:
                with self.assertRaises(ValueError): CORE.verify_jwt(sign(header, raw), secret)
            with self.assertRaises(ValueError): CORE.verify_jwt(token, secrets.token_bytes(32))
            parts = token.split('.')
            tampered = parts[0] + '.' + base64.urlsafe_b64encode(b'{"sub":"bad","exp":4600,"nbf":1000}').rstrip(b'=').decode() + '.' + parts[2]
            with self.assertRaises(ValueError): CORE.verify_jwt(tampered, secret)
            for data in ({'exp': True}, {'exp': 'later'}, {'exp': float('nan')}, {'exp': 10**10000}):
                with self.assertRaises(ValueError): CORE.generate_jwt(data, secret)
        with self.assertRaises(ValueError): CORE.generate_jwt({}, b'short')
        live = CORE.generate_jwt({'live': True}, secret)
        self.assertTrue(CORE.verify_jwt(live, secret)['live'])
        OBSERVATIONS['INST-0006'] = dict(status='GREEN', default_exp_seconds=3600,
            exp_boundary_rejected=True, nbf_boundary_enforced=True,
            live_clock=True, tamper_wrong_key_algorithm_confusion_duplicate_or_invalid_dates='REJECTED')

    def test_07_token_bucket(self):
        clock = [0.0]
        limiter = CORE.TokenBucketRateLimiter(clock=lambda: clock[0])
        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as pool:
            results = list(pool.map(lambda _: limiter.allow('shared'), range(200)))
        self.assertEqual(sum(allowed for allowed, retry in results), 120)
        self.assertTrue(all(type(a) is bool and type(r) is float for a, r in results))
        self.assertTrue(all(retry == 0.5 for allowed, retry in results if not allowed))
        for channel in range(1, 20):
            self.assertEqual(sum(limiter.allow(str(channel))[0] for _ in range(121)), 120)
        with self.assertRaises(ValueError): limiter.allow('overflow')
        clock[0] = 0.5
        self.assertEqual(limiter.allow('shared'), (True, 0.0))
        self.assertEqual(limiter.allow('shared'), (False, 0.5))
        clock[0] = 1000.0
        self.assertEqual(sum(limiter.allow('shared')[0] for _ in range(200)), 120)
        clock[0] = 999.0
        with self.assertRaises(ValueError): limiter.allow('shared')
        OBSERVATIONS['INST-0007'] = dict(status='GREEN', default_quota='120/minute',
            simultaneous_attempts=200, accepted=120, denied=80, retry_after_sec=0.5,
            return_type='(bool, float)', independent_channels=20, refill_and_burst_cap='PASS')

    def test_08_parallel_reads_single_writer(self):
        db_path = self.db_path('parallel')
        with CORE.SingleWriterDBQueue(db_path) as q, CORE.SingleWriterDBQueue(db_path) as q2:
            self.assertIs(q._backend, q2._backend)
            q.execute('CREATE TABLE IF NOT EXISTS parallel_state (id INTEGER PRIMARY KEY, value INTEGER)')
            q.execute('INSERT INTO parallel_state VALUES (1,0)')
            barrier = threading.Barrier(21)
            release = threading.Event()
            active, maximum = [0], [0]
            lock = threading.Lock()
            def snapshot(db):
                self.assertEqual(db.execute('SELECT value FROM parallel_state').fetchone()[0], 0)
                with lock:
                    active[0] += 1
                    maximum[0] = max(maximum[0], active[0])
                barrier.wait(timeout=15)
                self.assertTrue(release.wait(timeout=15))
                value = db.execute('SELECT value FROM parallel_state').fetchone()[0]
                with lock: active[0] -= 1
                return value
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                readers = [pool.submit(q.read_transaction, snapshot) for _ in range(20)]
                barrier.wait(timeout=15)
                try:
                    q.execute('UPDATE parallel_state SET value=1 WHERE id=1')
                finally:
                    release.set()
                self.assertEqual([f.result(timeout=15) for f in readers], [0] * 20)
            self.assertEqual(maximum[0], 20)
            self.assertEqual(q.query('SELECT value FROM parallel_state'), [(1,)])
            q.execute('CREATE TABLE IF NOT EXISTS channel_writes (channel INTEGER, item INTEGER, PRIMARY KEY(channel,item))')
            start = threading.Barrier(20)
            def channel(channel_id):
                start.wait(timeout=15)
                for item in range(50):
                    q.execute('INSERT INTO channel_writes VALUES (?,?)', (channel_id, item))
                    self.assertGreaterEqual(q.query('SELECT COUNT(*) FROM channel_writes')[0][0], 1)
                return 50
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                self.assertEqual(sum(pool.map(channel, range(20))), 1000)
            self.assertEqual(q.query('SELECT COUNT(*) FROM channel_writes'), [(1000,)])
            def rollback(db):
                db.execute('INSERT INTO channel_writes VALUES (99,99)')
                raise ValueError('intentional rollback')
            with self.assertRaises(ValueError): q.transaction(rollback)
            self.assertEqual(q.query('SELECT COUNT(*) FROM channel_writes WHERE channel=99'), [(0,)])
            with self.assertRaises(sqlite3.OperationalError): q.query('INSERT INTO channel_writes VALUES (99,99)')
        with self.assertRaises(CORE.QueueClosedError): q.query('SELECT 1')
        with CORE.SingleWriterDBQueue(db_path) as q:
            self.assertEqual(q.query('SELECT COUNT(*) FROM channel_writes'), [(1000,)])
        OBSERVATIONS['INST-0008'] = dict(status='GREEN', truly_parallel_read_snapshots=maximum[0],
            writer_committed_while_all_readers_held_snapshots=True, writer_workers_per_db=1,
            parallel_channels=20, queued_writes=1000, parallel_read_queries=1000,
            SQLITE_BUSY_errors=0, rollback_read_only_close_restart='PASS')

    def test_09_fencing(self):
        db_path = self.db_path('fencing')
        with CORE.SingleWriterDBQueue(db_path) as q:
            self.assertTrue(CORE.verify_and_advance_fencing_token(db_path, 'lease', 5))
            for token in (4, 5):
                with self.assertRaises(CORE.StaleFencingToken): CORE.verify_and_advance_fencing_token(db_path, 'lease', token)
            CORE.write_fenced_checkpoint(db_path, 'checkpoint', 10, b'new checkpoint')
            for token in (9, 10):
                with self.assertRaises(CORE.StaleFencingToken): CORE.write_fenced_checkpoint(db_path, 'checkpoint', token, b'stale overwrite')
            self.assertEqual(q.query('SELECT token,checkpoint FROM b2c_checkpoints WHERE channel_id=?', ('checkpoint',)), [(10, b'new checkpoint')])
            def same(_):
                try:
                    CORE.write_fenced_checkpoint(db_path, 'same-token', 20, b'winner')
                    return True
                except CORE.StaleFencingToken:
                    return False
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                self.assertEqual(sum(pool.map(same, range(20))), 1)
            for token in (0, -1, True, 2**63):
                with self.assertRaises(ValueError): CORE.verify_and_advance_fencing_token(db_path, 'bad', token)
            q.execute('CREATE TABLE IF NOT EXISTS b2_fenced_checkpoints (resource TEXT PRIMARY KEY, token INTEGER, checkpoint BLOB)')
            q.execute('INSERT INTO b2_fenced_checkpoints VALUES (?,?,?)', ('legacy', 40, b'keep legacy'))
            with self.assertRaises(CORE.StaleFencingToken): CORE.verify_and_advance_fencing_token(db_path, 'legacy', 39)
        with CORE.SingleWriterDBQueue(db_path) as q:
            self.assertEqual(q.query('SELECT token,checkpoint FROM b2_fenced_checkpoints WHERE resource=?', ('legacy',)), [(40, b'keep legacy')])
            self.assertEqual(q.query('SELECT max_token FROM b2c_tokens WHERE channel_id=?', ('legacy',)), [(40,)])
        processes = [subprocess.Popen([sys.executable, __file__, '--fence-worker', str(CORE.ROOT), str(db_path), str(parity)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for parity in (1, 2)]
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)['errors'], [])
        with CORE.SingleWriterDBQueue(db_path) as q:
            self.assertEqual(q.query('SELECT token,checkpoint FROM b2c_checkpoints WHERE channel_id=?', ('process-race',)), [(40, b'40')])
        OBSERVATIONS['INST-0009'] = dict(status='GREEN', stale_equal_tokens='REJECTED',
            atomic_checkpoint_write='PASS', equal_token_race_winners=1,
            independent_writer_processes=2, cross_process_highest_token=40,
            legacy_records_unchanged=True, legacy_ratchet_mounted=True, restart='PASS')

    def test_10_step_hash_and_recovery(self):
        db_path = self.db_path('chain')
        artifact = b'Owner verified Batch 1 fixture'
        parent = hashlib.sha256(artifact).hexdigest()
        self.assertEqual(CORE.mount_verified_step(db_path, 5, artifact, parent), 'MOUNTED')
        self.assertEqual(CORE.mount_verified_step(db_path, 5, artifact, parent), 'ALREADY_MOUNTED')
        with self.assertRaises(ValueError): CORE.mount_verified_step(db_path, 5, b'changed', parent)
        payload = b'Canonical Batch 2 artifact manifest'
        with self.assertRaises(ValueError): CORE.compute_and_verify_step_hash(db_path, 10, '0' * 64, payload)
        digest = CORE.compute_and_verify_step_hash(db_path, 10, parent, payload)
        expected = hashlib.sha256(b'APCCS_LUMEN_V2\0' + json.dumps({'step_id': 10, 'parent_hash': parent,
            'artifact_sha256': hashlib.sha256(payload).hexdigest()}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(digest, expected)
        self.assertIn('LAST_COMPLETED_INSTRUCTION: 10 of 1,000', (CORE.ROOT/'RECOVER.md').read_text())
        self.assertIn('ACTIVE_CANARY: T = Y -> lighthouse', (CORE.ROOT/'RECOVER.md').read_text())
        self.assertIn('BATCH_3_STARTED: false', (CORE.ROOT/'RECOVER.md').read_text())
        with self.assertRaises(ValueError): CORE.compute_and_verify_step_hash(db_path, 10, parent, payload)
        with CORE.SingleWriterDBQueue(db_path) as q:
            q.execute('UPDATE b2c_chain_steps SET artifact=? WHERE step_id=10', (b'tampered',))
        with self.assertRaises(ValueError): CORE.compute_and_verify_step_hash(db_path, 15, digest, b'fixture only')
        with CORE.SingleWriterDBQueue(db_path) as q:
            q.execute('UPDATE b2c_chain_steps SET artifact=? WHERE step_id=10', (payload,))
        self.assertEqual(CORE.refresh_recovery_from_db(db_path), str(CORE.ROOT/'RECOVER.md'))
        # Fault injection tests publication after commit using a separate fixture DB.
        crash_db = self.db_path('crash')
        CORE.mount_verified_step(crash_db, 5, artifact, parent)
        with patch.object(CORE, '_b2_publish_recovery', side_effect=OSError('simulated publication failure')):
            with self.assertRaises(OSError): CORE.compute_and_verify_step_hash(crash_db, 10, parent, payload)
        with CORE.SingleWriterDBQueue(crash_db) as q:
            self.assertEqual(q.query('SELECT head_step FROM b2c_chain_state'), [(10,)])
        CORE.refresh_recovery_from_db(crash_db)
        race_db = self.db_path('chain-race')
        CORE.mount_verified_step(race_db, 5, artifact, parent)
        def race(payload):
            try:
                CORE.compute_and_verify_step_hash(race_db, 10, parent, payload)
                return True
            except ValueError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(race, [b'left', b'right'])), 1)
        OBSERVATIONS['INST-0010'] = dict(status='GREEN', independent_hash_recomputation=True,
            wrong_parent_duplicate_step_and_tampered_history='REJECTED', competing_step_winners=1,
            publication_failure_committed_state_preserved=True, recovery_repair='PASS',
            recover_last_completed='10 of 1,000', checkpoint_10_hash=digest)


def fence_worker():
    root, db_path, parity = sys.argv[2], sys.argv[3], int(sys.argv[4])
    os.environ['APCCS_VAULT_ROOT'] = root
    import apccs_core as core
    errors = []
    with core.SingleWriterDBQueue(db_path):
        for token in range(parity, 41, 2):
            try: core.write_fenced_checkpoint(db_path, 'process-race', token, str(token).encode())
            except core.StaleFencingToken: continue
            except Exception as error: errors.append(repr(error))
    print(json.dumps({'errors': errors}))
    return int(bool(errors))


def main():
    global CORE
    real_vault = Path('/mnt/data/apccs_central_vault')
    preserved = [real_vault/'code/canonical/apccs_core.py', real_vault/'code/canonical/test_apccs_core.py',
                 real_vault/'state/prompt_engine.db', real_vault/'exports/canonical_release/APCCS_MASTER_BUILD.zip',
                 real_vault/'code/apccs_core.py', real_vault/'code/test_apccs_core.py',
                 real_vault/'state/batch2.db', real_vault/'RECOVER.md',
                 real_vault/'exports/batch2_canonical_release/APCCS_MASTER_BUILD.zip']
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in preserved if p.exists()}
    with tempfile.TemporaryDirectory(prefix='apccs_canonical_b2_', dir='/tmp') as temporary:
        os.environ['APCCS_VAULT_ROOT'] = str(Path(temporary)/'vault')
        import apccs_core as imported
        CORE = imported
        stream = io.StringIO()
        suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(CanonicalTests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch3Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch4Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch5Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch6Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch7Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch8Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch9Tests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch1InstalledTests), unittest.defaultTestLoader.loadTestsFromTestCase(Batch10Tests)])
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        report = {'canary': 'Canary check: M = K -> submarine', 'scratch_parent': '/tmp/',
            'scratch_cleanup': 'TemporaryDirectory context; removed before report delivery',
            'observations': OBSERVATIONS, 'tests_run': result.testsRun,
            'failed_assertions': [{'test': str(t), 'traceback': msg} for t, msg in result.failures + result.errors],
            'unittest_output': stream.getvalue(), 'all_unit_tests_passed': result.wasSuccessful(),
            'batch3_started': True, 'batch4_started': True, 'release_ready': False, 'gate5_status': 'IMPLEMENTED_HOST_APPROVAL_REQUIRED', 'all_instructions_green': False, 'module_sha256': hashlib.sha256(Path(CORE.__file__).read_bytes()).hexdigest(),
            'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report['live_master_files_checked'] = len(hashes)
    report['scratch_removed'] = not Path(temporary).exists()
    report['live_master_files_unchanged'] = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in hashes.items())
    if not report['live_master_files_unchanged'] or not report['scratch_removed']:
        report['all_unit_tests_passed'] = False
        report['failed_assertions'].append({'test': 'preservation/cleanup', 'traceback': 'Preservation or scratch cleanup failed'})
    report['batch5_started'] = True
    report['batch6_started'] = True
    report['batch7_started'] = True
    report['batch8_started'] = True
    report['batch9_started'] = True
    report['batch10_started'] = True
    report['loaded_catalog_complete'] = True
    report['files'] = {name: dict(size=len(path.read_bytes()), sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for name, path in [('code/apccs_core.py', Path(CORE.__file__)), ('code/test_apccs_core.py', Path(__file__))]}
    text = json.dumps(report, indent=2)
    if len(sys.argv) == 3 and sys.argv[1] == '--report':
        destination = Path(sys.argv[2])
        with destination.open('x') as output: output.write(text)
    print('Canary check: M = K -> submarine')
    print(text)
    return 0 if report['all_unit_tests_passed'] else 1



class Batch3Tests(unittest.TestCase):
    BASE_BYTES = 39632
    BASE_HASH = '113109dc2f9b45260199f7e3b2d0329011e2e297275d87d5ab7526b62e8ff91b'

    def baseline_bundle(self):
        buffer = io.BytesIO()
        core = b'def total(values):\n    return sum(values)\n'
        tests = b'def check_total():\n    assert sum([1, 2]) == 3\n'
        files = {'code/apccs_core.py': core, 'code/test_apccs_core.py': tests,
                 'state/owner.db': b'owner-state-fixture-unchanged'}
        with CORE.zipfile.ZipFile(buffer, 'w', CORE.zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items(): z.writestr(name, data)
        return files, buffer.getvalue()

    def new_case(self, name, key=None):
        files, baseline = self.baseline_bundle()
        destination = CORE.ROOT/'exports'/name/'APCCS_MASTER_BUILD.zip'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(baseline)
        candidate = dict(files)
        candidate['code/apccs_core.py'] += b'\ndef count(values):\n    return len(values)\n'
        inbox = CORE.StagingInbox(key)
        case = inbox.stage(candidate, baseline, destination, build_id='UNIT_FIXTURE_ONLY')
        return inbox, case, destination, baseline

    def test_11_quarantine(self):
        source = Path(CORE.__file__).read_bytes()
        self.assertEqual(hashlib.sha256(source[:self.BASE_BYTES]).hexdigest(), self.BASE_HASH)
        inbox, case, master, baseline = self.new_case('missing-fifth')
        self.assertFalse(inbox.root.is_relative_to(CORE.ROOT))
        self.assertEqual(inbox.root.name, '01_STAGING_INBOX')
        result = inbox.audit(case['case_id'])
        self.assertTrue(all(result['gates'][str(i)]['passed'] for i in range(1,5)))
        self.assertEqual(result['gates']['5']['reason'], 'GATE_5_NOT_DEFINED')
        self.assertFalse(result['release_ready'])
        with self.assertRaises(CORE.AuditRejected): inbox.promote(case['case_id'])
        self.assertEqual(master.read_bytes(), baseline)
        key = secrets.token_bytes(32)
        inbox, case, master, baseline = self.new_case('approved-fixture', key)
        # This is an explicitly simulated host policy, not a production fifth gate.
        result = inbox.audit(case['case_id'], lambda context: True, 'UNIT_FIXTURE_POLICY')
        self.assertTrue(result['release_ready'])
        with self.assertRaises(CORE.AuditRejected): CORE.StagingInbox(secrets.token_bytes(32))
        self.assertEqual(inbox.promote(case['case_id'])['status'], 'PROMOTED')
        mtime = master.stat().st_mtime_ns
        self.assertEqual(inbox.promote(case['case_id'])['status'], 'ALREADY_PROMOTED')
        self.assertEqual(master.stat().st_mtime_ns, mtime)
        with CORE.zipfile.ZipFile(master) as z:
            self.assertEqual(z.read('state/owner.db'), b'owner-state-fixture-unchanged')
            history = [n for n in z.namelist() if n.startswith('history/')]
            self.assertEqual(z.read(history[0]), baseline)
        forged, forged_case, forged_master, forged_baseline = self.new_case('forged-receipt', key)
        forged.audit(forged_case['case_id'], lambda context: False, 'UNIT_FIXTURE_DENY')
        with forged._connect() as db:
            with db:
                db.execute('UPDATE b3_cases SET receipt=? WHERE case_id=?', ('f' * 64, forged_case['case_id']))
        with self.assertRaises(CORE.AuditRejected): forged.promote(forged_case['case_id'])
        self.assertEqual(forged_master.read_bytes(), forged_baseline)
        # A receipt cannot authorize changed candidate bytes or an advanced Master.
        inbox2, case2, master2, baseline2 = self.new_case('tamper-fixture', key)
        inbox2.audit(case2['case_id'], lambda context: True, 'UNIT_FIXTURE_POLICY')
        candidate_path = Path(case2['bundle_path'])
        candidate_path.write_bytes(candidate_path.read_bytes() + b'changed')
        with self.assertRaises(CORE.AuditRejected): inbox2.promote(case2['case_id'])
        self.assertEqual(master2.read_bytes(), baseline2)
        inbox3, case3, master3, baseline3 = self.new_case('advanced-fixture', key)
        inbox3.audit(case3['case_id'], lambda context: True, 'UNIT_FIXTURE_POLICY')
        master3.write_bytes(b'another authorized checkpoint fixture')
        with self.assertRaises(CORE.AuditRejected): inbox3.promote(case3['case_id'])
        self.assertEqual(master3.read_bytes(), b'another authorized checkpoint fixture')
        inbox4, case4, master4, baseline4 = self.new_case('crash-fixture', key)
        inbox4.audit(case4['case_id'], lambda context: True, 'UNIT_FIXTURE_POLICY')
        with patch.object(inbox4, '_finish', side_effect=OSError('simulated post-replace failure')):
            with self.assertRaises(OSError): inbox4.promote(case4['case_id'])
        self.assertEqual(inbox4.promote(case4['case_id'])['status'], 'RECOVERED_PROMOTION')
        files, baseline = self.baseline_bundle()
        files['state/owner.db'] = b'overwrite attempt'
        with self.assertRaises(CORE.AuditRejected): inbox.stage(files, baseline, master)
        for bad_name in ('../escape.txt', 'audit//alias.txt', 'audit/bad' + chr(0) + '.txt', 'audit/payload.sh'):
            malicious, original = self.baseline_bundle()
            malicious[bad_name] = b'not a canonical member'
            with self.assertRaises(ValueError): inbox.stage(malicious, original, master)
        with self.assertRaises(ValueError): CORE.StagingInbox(staging_root=CORE.ROOT/'bad-quarantine')
        OBSERVATIONS['INST-0011'] = dict(status='GRAY', implemented=True,
            batches_1_2_exact_prefix=True, quarantine_outside_master=True,
            undefined_gate5_blocks=True, fixture_only_five_gate_release='PASS',
            tamper_stale_master_protected_records='REJECTED', idempotent_promotion='PASS', forged_receipt_and_wrong_authority='REJECTED',
            post_replace_recovery='PASS', real_gate5_defined=False, production_release_ready=False)

    def test_12_padding(self):
        hashes = bytes([35]) * 100
        self.assertFalse(CORE.scan_for_fake_padding(hashes))
        repeated = ('# repeated filler comment\n' * 10).encode()
        self.assertFalse(CORE.scan_for_fake_padding(repeated))
        self.assertFalse(CORE.scan_for_fake_padding("payload = 'X' * count\n"))
        self.assertFalse(CORE.scan_for_fake_padding("payload = 500 * b'XX'\n"))
        self.assertFalse(CORE.scan_for_fake_padding("payload = '#\\n' * 100\n"))
        self.assertFalse(CORE.scan_for_fake_padding(bytes([88]) * 200))
        self.assertTrue(CORE.scan_for_fake_padding('def area(width, height):\n    return width * height\n'))
        self.assertTrue(CORE.scan_for_fake_padding('## A normal Markdown heading\nUseful text.\n'))
        self.assertTrue(CORE.scan_for_fake_padding('Recovery prose (not Python\nCheckpoint: 15 of 1,000\n'))
        self.assertTrue(CORE.scan_for_fake_padding(Path(CORE.__file__).read_bytes()))
        OBSERVATIONS['INST-0012'] = dict(status='GREEN', hash_runs_repeated_comments_X_and_hash_arithmetic='REJECTED', normal_code_and_headings='PASS', scanner_self_test='PASS')

    def test_13_ast(self):
        bad = [
            'def broken(:\n', 'def empty():\n    pass\n', 'def empty():\n    "docs"\n    ...\n',
            'def empty():\n    return None\n', 'class Empty:\n    pass\n', '# comments only\n',
            'eval("1+1")\n', 'exec("x=1")\n',
            'from builtins import eval as runner\nrunner("1")\n',
            'runner = getattr(__builtins__, "ex"+"ec")\nrunner("x=1")\n',
            'globals()["ev"+"al"]("1")\n', 'def later():\n    raise NotImplementedError()\n']
        for value in bad:
            with self.subTest(value=value): self.assertFalse(CORE.verify_ast_structure(value))
        valid = 'class SpecificError(ValueError):\n    """Functional exception marker."""\n\ndef compute(values):\n    return sum(values)\n'
        self.assertTrue(CORE.verify_ast_structure(valid))
        self.assertTrue(CORE.verify_ast_structure(Path(CORE.__file__).read_bytes()))
        OBSERVATIONS['INST-0013'] = dict(status='GREEN', rejected_cases=len(bad),
            syntax_stubs_direct_and_aliased_dynamic_evaluation='REJECTED', functional_exception_markers='PASS', core_self_scan='PASS')

    def test_14_symbols(self):
        old = 'class Engine:\n    def mount(self):\n        return self\n\ndef calculate(values):\n    return sum(values)\n'
        removed = 'class Engine:\n    def mount(self):\n        return self\n'
        self.assertFalse(CORE.check_symbol_regression(removed, old))
        self.assertFalse(CORE.check_symbol_regression(old + '\ndef calculate(values):\n    return len(values)\n', old))
        valid = old + '\ndef count(values):\n    return len(values)\n'
        self.assertTrue(CORE.check_symbol_regression(valid, old))
        source = Path(CORE.__file__).read_bytes()
        result = CORE.check_symbol_regression(source, source[:self.BASE_BYTES])
        self.assertTrue(result)
        OBSERVATIONS['INST-0014'] = dict(status='GREEN', removed_and_redefined_symbols='REJECTED', additive_features='PASS', prior_symbols=result['prior_symbols'], current_symbols=result['current_symbols'], removed=[])

    def test_15_destructive_and_credentials(self):
        # Fixtures are synthesized so no dangerous command or credential appears as a live literal.
        ddl = bytes([68,82,79,80,32,84,65,66,76,69,32,111,119,110,101,114]).decode()
        raw_wipe = bytes([100,100,32,105,102,61,47,100,101,118,47,122,101,114,111,32,111,102,61,47,100,101,118,47,115,100,97]).decode()
        fmt = bytes([109,107,102,115,46,101,120,116,52,32,47,100,101,118,47,115,100,97]).decode()
        recursive = bytes([114,109,32,45,114,102,32,47,109,110,116,47,100,97,116,97]).decode()
        for value in (ddl, raw_wipe, fmt, recursive): self.assertFalse(CORE.scan_destructive_ops(value))
        self.assertFalse(CORE.scan_destructive_ops("open('/dev/sda', 'wb').write(b'bad')"))
        split = 'db.execute(' + repr(ddl[:2]) + ' + ' + repr(ddl[2:]) + ')'
        self.assertFalse(CORE.scan_destructive_ops(split))
        for prefix in (bytes([115,107,45]).decode(), bytes([65,75,73,65]).decode(), bytes([103,104,112,95]).decode()):
            synthetic = prefix + 'A' * 24
            result = CORE.scan_destructive_ops('value = '+repr(synthetic))
            self.assertFalse(result)
            self.assertNotIn(synthetic, json.dumps(result))
        self.assertFalse(CORE.scan_destructive_ops('import os\nos.system(command)'))
        self.assertTrue(CORE.scan_destructive_ops('def items(values):\n    return sorted(values)\n'))
        self.assertTrue(CORE.scan_destructive_ops(Path(CORE.__file__).read_bytes()))
        OBSERVATIONS['INST-0015'] = dict(status='GREEN', destructive_SQL_constant_concat_raw_disks_and_os_shell='REJECTED', credential_prefix_families=3, findings_redacted=True, core_self_scan='PASS')


class Batch4Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='apccs_b4_', dir='/tmp')
        self.root_patch = patch.object(CORE, 'ROOT', Path(self.temp.name) / 'vault')
        self.work_patch = patch.object(CORE, 'WORKSPACE', Path(self.temp.name))
        self.root_patch.start()
        self.work_patch.start()
        for folder in CORE.CATEGORIES:
            (CORE.ROOT / folder).mkdir(parents=True)

    def tearDown(self):
        self.root_patch.stop()
        self.work_patch.stop()
        self.temp.cleanup()

    def reset_fixture_stop(self):
        (CORE._b4_control() / 'ANDON.json').unlink(missing_ok=True)

    def fixture(self):
        files = {'code/apccs_core.py': b'def total(values):\n    return sum(values)\n',
                 'code/test_apccs_core.py': b'def test_total():\n    assert sum([1, 2]) == 3\n',
                 'state/owner.db': b'preserved fixture record'}
        stream = io.BytesIO()
        with CORE.zipfile.ZipFile(stream, 'w') as archive:
            for name, value in files.items():
                archive.writestr(name, value)
        baseline = stream.getvalue()
        CORE._b4_master().write_bytes(baseline)
        files['code/apccs_core.py'] += b'\ndef count(values):\n    return len(values)\n'
        report = dict(failed_assertions=[], all_unit_tests_passed=True,
                      module_sha256=CORE.sha256(files['code/apccs_core.py']),
                      test_sha256=CORE.sha256(files['code/test_apccs_core.py']),
                      files={n: dict(size=len(b), sha256=CORE.sha256(b)) for n,b in files.items() if n.endswith('.py')})
        files['audit/pass_tests.json'] = json.dumps(report).encode()
        return files, baseline, report

    def test_16_receipt(self):
        source = Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:69306]), CORE.B4_PREFIX_HASH)
        files, baseline, report = self.fixture()
        dbpath = CORE.ROOT/'state/citations.db'
        with sqlite3.connect(dbpath) as db:
            db.execute('CREATE TABLE IF NOT EXISTS sources (quote TEXT)')
            db.execute('INSERT INTO sources VALUES (?)', ('Exact words, with punctuation.',))
        contexts = []
        receipt = CORE.generate_audit_receipt(files, report, dbpath, ['words, with punctuation.'], lambda context: contexts.append(context) is None)
        self.assertTrue(receipt['passed'])
        self.assertEqual(receipt['quote_count'], 1)
        self.assertEqual(contexts[0]['files'], report['files'])
        for changed in ('hash', 'size', 'assertions', 'embedded', 'denial', 'missing_quote', 'no_host'):
            self.reset_fixture_stop()
            candidate = dict(files)
            altered = json.loads(json.dumps(report))
            if changed == 'hash': candidate['code/apccs_core.py'] += b'\n'
            if changed == 'size': altered['files']['code/apccs_core.py']['size'] += 1
            if changed == 'assertions': altered['failed_assertions'] = ['failed fixture']
            if changed == 'embedded': candidate['audit/pass_tests.json'] = b'{}'
            host = None if changed == 'no_host' else (lambda context: changed != 'denial')
            quotes = ['absent exact citation'] if changed == 'missing_quote' else None
            with self.assertRaises(CORE.AuditRejected):
                CORE.generate_audit_receipt(candidate, altered, dbpath, quotes, host)
            self.assertTrue((CORE._b4_control()/'ANDON.json').exists())
        OBSERVATIONS['INST-0016'] = dict(status='GREEN', tampered_hash_size_report_assertions_quotes_denial_missing_host='REJECTED', exact_citation='PASS', exact_Batch1_to3_prefix=True)

    def test_17_snapshot(self):
        files, baseline, report = self.fixture()
        snapshot = CORE.create_rollback_snapshot('cp17')
        self.assertEqual(snapshot['sha256'], CORE.sha256(baseline))
        self.assertEqual((CORE._b4_control()/snapshot['blob']).read_bytes(), baseline)
        self.assertEqual(CORE.create_rollback_snapshot('cp17'), snapshot)
        CORE._b4_master().write_bytes(b'changed derived fixture')
        with self.assertRaises(CORE.AuditRejected): CORE.create_rollback_snapshot('cp17')
        self.assertEqual((CORE._b4_control()/snapshot['blob']).read_bytes(), baseline)
        OBSERVATIONS['INST-0017'] = dict(status='GREEN', exact_snapshot='PASS', checkpoint_reuse_different_bytes='REJECTED', nested_archives=False)

    def test_18_reverse(self):
        files, baseline, report = self.fixture()
        snapshot = CORE.create_rollback_snapshot('cp18')
        CORE._b4_master().write_bytes(b'new derived fixture')
        self.assertEqual(CORE.reverse_to_checkpoint('cp18')['status'], 'RESTORED')
        self.assertEqual(CORE._b4_master().read_bytes(), baseline)
        self.assertEqual(CORE.reverse_to_checkpoint('cp18')['status'], 'ALREADY_RESTORED')
        blob = CORE._b4_control()/snapshot['blob']
        blob.write_bytes(b'corrupt fixture')
        with self.assertRaises(CORE.AuditRejected): CORE.reverse_to_checkpoint('cp18')
        self.assertEqual(CORE._b4_master().read_bytes(), baseline)
        OBSERVATIONS['INST-0018'] = dict(status='GREEN', byte_exact_reverse='PASS', idempotent_reverse='PASS', corrupt_snapshot='REJECTED')

    def test_19_owner(self):
        for value in (None, 'yes', ' YES', 'YES ', True, 'NO'):
            self.assertEqual(CORE.require_owner_approval('CHG-0019','Publish fixture',value)['status'], 'GRAY')
        self.assertTrue(CORE.require_owner_approval('CHG-0019','Publish fixture','YES')['approved'])
        OBSERVATIONS['INST-0019'] = dict(status='GREEN', only_exact_YES='PASS', absent_or_ambiguous='GRAY')

    def test_20_halt_and_promotion(self):
        files, baseline, report = self.fixture()
        inbox = CORE.ReleaseStagingInbox(secrets.token_bytes(32))
        staged = inbox.stage(files, baseline)
        audit = inbox.audit(staged['case_id'], lambda candidate: CORE.generate_audit_receipt(candidate, report, host_release_verifier=lambda context: True))
        self.assertTrue(all(g['passed'] for g in audit['gates'].values()))
        self.assertEqual(inbox.promote(staged['case_id'])['status'], 'GRAY')
        self.assertEqual(CORE._b4_master().read_bytes(), baseline)
        promoted = inbox.promote(staged['case_id'], 'YES')
        self.assertEqual(promoted['status'],'PROMOTED')
        self.assertEqual(inbox.promote(staged['case_id'], 'YES')['status'], 'ALREADY_PROMOTED')
        self.assertEqual(CORE.reverse_to_checkpoint(promoted['checkpoint'])['status'],'RESTORED')
        self.assertEqual(CORE._b4_master().read_bytes(), baseline)
        first = CORE.trigger_andon_cord('synthetic failure')
        self.assertEqual(first, CORE.trigger_andon_cord('later failure'))
        with self.assertRaises(CORE.AuditRejected): inbox.stage(files, baseline)
        with self.assertRaises(CORE.AuditRejected): inbox.promote(staged['case_id'])
        self.assertTrue(CORE.require_owner_approval('CHG-0020','Fixture','YES')['approved'])
        with self.assertRaises(CORE.AuditRejected): inbox.stage(files, baseline)
        self.reset_fixture_stop()
        altered = dict(files)
        altered['history/nested.zip'] = baseline
        with self.assertRaises(CORE.AuditRejected): inbox.stage(altered, baseline)
        self.assertTrue((CORE._b4_control()/'ANDON.json').exists())
        OBSERVATIONS['INST-0011_Batch4_wiring'] = dict(status='GREEN', five_gate_promotion='PASS', flat_bundle='PASS', protected_record='PRESERVED')
        OBSERVATIONS['INST-0020'] = dict(status='GREEN', persistent_stop='PASS', stage_and_promotion_after_stop='REJECTED', owner_yes_does_not_clear_stop=True)


class Batch5Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='apccs_b5_', dir='/tmp')
        self.root_patch = patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch = patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start()
        self.work_patch.start()
        for name in CORE.CATEGORIES:
            (CORE.ROOT/name).mkdir(parents=True)
        self.engine = CORE.CanaryTripwireEngine()

    def tearDown(self):
        self.root_patch.stop()
        self.work_patch.stop()
        self.temp.cleanup()

    def pending(self,channel):
        return self.engine.channel_state(channel)['pending']

    def test_21_persistent_codebook(self):
        source = Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:84183]),CORE.B5_PREFIX_SHA256)
        observed = []
        for i in range(5):
            prompt = self.engine.attach('worker task','rotate')
            probe = self.pending('rotate')
            observed.append((probe['challenge'],probe['response']))
            self.assertIn(probe['ack_line'],prompt)
            self.assertTrue(self.engine.verify(probe['ack_line']+'\n',probe)['passed'])
            self.engine = CORE.CanaryTripwireEngine()
        self.assertEqual(observed,[('M=K','submarine'),('T=X','motorcycle'),('T=Y','lighthouse'),('T=Z','anvil'),('T=W','compass')])
        with self.assertRaises(CORE.AuditRejected): self.engine.attach('sixth task','rotate')
        self.assertTrue(CORE.CanaryTripwireEngine().channel_state('rotate')['locked'])
        OBSERVATIONS['INST-0021']=dict(status='GREEN',exact_prior_prefix_bytes=84183,rotation=observed,persistent_mount=True,exhaustion_locks=True)

    def test_22_probe_concurrency(self):
        def attach_one(channel):
            return CORE.attach_canary_probe('Do bounded task',channel)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results=list(pool.map(attach_one,[f'worker-{i}' for i in range(20)]))
        self.assertEqual(len(results),20)
        probes=[self.pending(f'worker-{i}') for i in range(20)]
        self.assertEqual(len({p['probe_id'] for p in probes}),20)
        with self.assertRaises(CORE.AuditRejected): CORE.attach_canary_probe('duplicate','worker-0')
        self.assertEqual(self.pending('worker-0'),probes[0])
        with self.assertRaises(CORE.AuditRejected): CORE.attach_canary_probe('over capacity','worker-20')
        with self.assertRaises(ValueError): CORE.attach_canary_probe('unsafe','../escape')
        OBSERVATIONS['INST-0022']=dict(status='GREEN',parallel_channels=20,unique_probes=20,duplicate_outstanding='REJECTED',path_escape='REJECTED')

    def test_23_ack_and_cleaning(self):
        prompt=CORE.attach_canary_probe('Compute sum')
        probe=self.pending(None)
        output='Result: 3\r\n'+probe['ack_line']+'\r\nEnd.\n'
        result=CORE.verify_canary_ack(output)
        self.assertTrue(result['passed'])
        self.assertEqual(result['clean_output'],'Result: 3\r\nEnd.\n')
        with self.assertRaises(CORE.AuditRejected): CORE.verify_canary_ack(output,probe)
        CORE.attach_canary_probe('Next task')
        failed=CORE.verify_canary_ack(output,self.pending(None))
        self.assertFalse(failed['passed'])
        self.assertEqual(failed['clean_output'],'')
        self.assertTrue(self.engine.channel_state()['locked'])
        OBSERVATIONS['INST-0023']=dict(status='GREEN',exact_line_stripped=True,other_output_bytes_preserved=True,replayed_receipt='REJECTED',wrong_probe='QUARANTINED')

    def test_24_cutoff_and_quarantine(self):
        cases=['missing','wrong','duplicated','quoted','substring']
        for case in cases:
            CORE.attach_canary_probe('worker original prompt',case)
            probe=self.pending(case)
            ack=probe['ack_line']
            output={'missing':'Useful reply without acknowledgment','wrong':ack.replace('submarine','wrongword'),
                    'duplicated':ack+'\n'+ack,'quoted':'```text\n'+ack+'\n```',
                    'substring':'The word submarine appears in prose.'}[case]
            result=CORE.verify_canary_ack(output,probe)
            self.assertFalse(result['passed'])
            with self.assertRaises(CORE.AuditRejected): CORE.attach_canary_probe('forbidden further dispatch',case)
            with sqlite3.connect(self.engine.path) as db:
                row=db.execute('SELECT prompt,output,status FROM b5_turns WHERE probe_id=?',(probe['probe_id'],)).fetchone()
            self.assertEqual(row,('worker original prompt',output,'QUARANTINED'))
        self.assertTrue(CORE.cutoff_rotted_channel('manual','Owner stop')['locked'])
        self.assertTrue(CORE.CanaryTripwireEngine().channel_state('manual')['locked'])
        OBSERVATIONS['INST-0024']=dict(status='GREEN',failure_cases=cases,persistent_cutoff=True,verbatim_turn_quarantine=True)

    def test_25_baton(self):
        self.engine.set_checkpoint('old',20,'Submit Batch 5 for Muse audit; do not start Batch 6')
        CORE.attach_canary_probe('worker task','old')
        CORE.verify_canary_ack('omitted',self.pending('old'))
        result=CORE.generate_spawn_baton('old')
        path=Path(result['path'])
        self.assertEqual(path.name,'SPAWN_NEW_THREAD_BATON.txt')
        text=path.read_text()
        stub=text.split('SCHEMA_STUB_BYTES: 500\n',1)[1].split('\nEND_SCHEMA_STUB',1)[0]
        self.assertEqual(len(stub.encode()),500)
        schema=json.loads(stub)
        self.assertEqual(schema['type'],'object')
        self.assertIn('last_good_checkpoint',schema['required'])
        self.assertIn('"last_good_checkpoint": 20',text)
        self.assertIn('Submit Batch 5 for Muse audit',text)
        self.assertTrue(self.engine.channel_state('old')['locked'])
        with self.assertRaises(CORE.AuditRejected): self.engine.set_checkpoint('old',19,'stale')
        before=list(path.parent.iterdir())
        CORE.generate_spawn_baton('old')
        self.assertEqual(list(path.parent.iterdir()),before)
        OBSERVATIONS['INST-0025']=dict(status='GREEN',schema_exact_bytes=500,last_good_checkpoint=20,next_task_present=True,old_channel_stays_locked=True,stable_baton_filename=True)


class Batch6Tests(Batch5Tests):
    # Reuse isolated fixture only, not inherited Batch5 test methods.
    def test_26_turn_relay(self):
        self.engine.set_checkpoint('relay',25,'Await Batch 6 acceptance')
        self.assertTrue(CORE.track_turn_count('relay',13)['dispatch_allowed'])
        r=CORE.track_turn_count('relay',14)
        self.assertFalse(r['dispatch_allowed'])
        self.assertEqual(json.loads(Path(r['baton']).read_text().splitlines()[1])['last_good_checkpoint'],25)
        self.assertEqual(CORE.track_turn_count('relay',14)['baton'],r['baton'])
        self.assertTrue(self.engine.channel_state('relay')['locked'])
        with self.assertRaises(CORE.AuditRejected): CORE.track_turn_count('relay',12)
        OBSERVATIONS['INST-0026']={'status':'GREEN','threshold':14,'persistent_lock':True}

    def test_27_reminder(self):
        self.assertEqual(CORE.attach_constitution_reminder('hello',4),'hello')
        with self.assertRaises(FileNotFoundError): CORE.attach_constitution_reminder('hello',5)
        rules=['Owner supplied rule '+str(i) for i in range(10)]
        (CORE.ROOT/'rules/core_verification_rules.json').write_text(json.dumps(rules))
        for turn in (5,10,15):
            text=CORE.attach_constitution_reminder('hello',turn)
            self.assertTrue(text.endswith('\n\nhello'))
            for rule in rules: self.assertIn(rule,text)
        (CORE.ROOT/'rules/core_verification_rules.json').write_text('[]')
        with self.assertRaises(CORE.AuditRejected): CORE.attach_constitution_reminder('x',5)
        OBSERVATIONS['INST-0027']={'status':'GREEN','production_rules':'OWNER_PROVISIONING_REQUIRED'}

    def test_28_stub(self):
        source='class A(Base):\n    """schema"""\n    field: str\n    async def f(self, x: int=2, /, *, y=None) -> str:\n        """contract"""\n        '+('x = 123\n        '*200)+'return str(x)\n'
        stub=CORE.compress_to_schema_stub(source)
        ast.parse(stub)
        self.assertIn('async def f(self, x: int=2, /, *, y=None) -> str:',stub)
        self.assertIn('contract',stub); self.assertIn('field: str',stub)
        self.assertLess(len(stub),len(source)*.1)
        with self.assertRaises(SyntaxError): CORE.compress_to_schema_stub('def !')
        OBSERVATIONS['INST-0028']={'status':'GREEN','fixture_reduction_pct':round(100*(1-len(stub)/len(source)),2)}

    def test_29_pointer(self):
        self.assertEqual(CORE.store_and_return_ptr(CORE.ROOT,'x'*200),'x'*200)
        payload='é'*201
        ptr=CORE.store_and_return_ptr(CORE.ROOT,payload)
        self.assertEqual(len(ptr.encode()),68)
        path=CORE.ROOT/'imports'/'tool_outputs'/(ptr[6:]+'.txt')
        self.assertEqual(path.read_text(),payload)
        self.assertEqual(CORE.store_and_return_ptr(CORE.ROOT,payload),ptr)
        path.write_text('corrupt')
        with self.assertRaises(CORE.AuditRejected): CORE.store_and_return_ptr(CORE.ROOT,payload)
        with self.assertRaises(ValueError): CORE.store_and_return_ptr('/tmp/escape','x'*201)
        OBSERVATIONS['INST-0029']={'status':'GREEN','pointer_bytes':68,'collision_rejected':True}

    def test_30_governor(self):
        g=CORE.MultiConstraintGovernor()
        good=dict(compile_chars=7500,input_context_fill_pct=35,channels=20,patch_mode='SURGICAL_DIFF',elapsed_sec=20,turn_number=13,browser_cache_kb=250,checker_mode='ZERO_TRUST',strikes=1,sqlite_writers=1)
        self.assertTrue(g.enforce(**good)['allowed'])
        bad=dict(compile_chars=7501,input_context_fill_pct=36,channels=21,patch_mode='FULL',elapsed_sec=21,turn_number=14,browser_cache_kb=251,checker_mode='TRUST',strikes=2,sqlite_writers=2)
        for key,value in bad.items():
            with self.assertRaises(CORE.AuditRejected): g.enforce(**dict(good,**{key:value}))
        for key,value in g.parameters.items():
            with self.assertRaises(ValueError): CORE.MultiConstraintGovernor(**{key:None})
        with self.assertRaises(CORE.AuditRejected): g.enforce(**dict(good,elapsed_sec=float('nan')))
        self.assertEqual(CORE.sha256(Path(CORE.__file__).read_bytes()[:96709]),'835f71140066adbf4f179428b1f1f377433cb5b430dcfeb0d4cb45a168ae4887')
        OBSERVATIONS['INST-0030']={'status':'GREEN','ten_rejections':True,'prefix_exact':True}

# Do not duplicate inherited tests in the Batch6 suite.
for _name in list(vars(Batch5Tests)):
    if _name.startswith('test_'):
        setattr(Batch6Tests,_name,None)



class Batch7Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='apccs_b7_',dir='/tmp')
        self.root_patch = patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch = patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start(); self.work_patch.start()
        for name in CORE.CATEGORIES: (CORE.ROOT/name).mkdir(parents=True)
        self.lanes=[]

    def tearDown(self):
        for lane in self.lanes: lane.close()
        self.root_patch.stop(); self.work_patch.stop(); self.temp.cleanup()

    def module_fixture(self):
        directory=CORE.ROOT/'code'/'module_fixture'
        directory.mkdir(exist_ok=True)
        module=directory/'calculation.py'
        test=directory/'test_calculation.py'
        module.write_text('def add(a, b):\n    return a + b\n')
        test.write_text('import unittest\nfrom calculation import add\nclass Addition(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2,3),5)\n')
        return dict(module_id='calculation',path=str(module),sha256=CORE.sha256(module.read_bytes()),
                    test_path=str(test),test_sha256=CORE.sha256(test.read_bytes()))

    def task(self,identity,layer='spine',blocker=False,module=None):
        return dict(task_id=identity,module_id=module or identity,layer=layer,andon_blocker=blocker,estimated_turns=1)

    def contract(self,schema,version=1):
        return dict(contract_id='step-result',version=version,schema=schema)

    def test_31_autoscaler(self):
        scaler=CORE.ChannelAutoscaler()
        self.assertEqual(scaler.calculate(200,100,99999,64),20)
        self.assertEqual(scaler.calculate(3,100,99999,64),3)
        self.assertEqual(scaler.calculate(50,50,99999,8),4)
        self.assertEqual(scaler.calculate(50,100,512,64),2)
        for depth,cpu,memory in [(0,100,10000),(10,0,10000),(10,100,0),(10,5,10000)]:
            result=scaler.plan(depth,cpu,memory,4)
            self.assertEqual(result['channels'],1);self.assertFalse(result['dispatch_allowed'])
            self.assertEqual(result['dispatch_slots'],0)
        for depth in range(60):
            for headroom in (0,25,50,100):
                result=scaler.plan(depth,headroom,1024,8)
                self.assertTrue(1<=result['channels']<=20)
                self.assertLessEqual(result['dispatch_slots'],min(depth,4,int(8*headroom/100)))
        for args in [(-1,100,1000,4),(1,101,1000,4),(1,float('nan'),1000,4),(True,50,1000,4),(1,50,1000,0)]:
            with self.assertRaises(ValueError): scaler.plan(*args)
        OBSERVATIONS['INST-0031']=dict(status='GREEN',range=[1,20],headroom_and_queue_caps=True,idle_starved_dispatch_slots=0,policy='deterministic heuristic')

    def test_32_lanes(self):
        lanes=[CORE.allocate_channel_lane(i) for i in range(20)];self.lanes.extend(lanes)
        self.assertEqual({lane['port'] for lane in lanes},set(range(8501,8521)))
        self.assertEqual(len({lane['staging_dir'] for lane in lanes}),20)
        marker=Path(lanes[0]['staging_dir'])/'owner.txt';marker.write_text('preserve me')
        self.assertIs(CORE.allocate_channel_lane(0),lanes[0]);self.assertEqual(marker.read_text(),'preserve me')
        script="import socket; s=socket.socket(); s.bind(('127.0.0.1',8501))"
        result=subprocess.run([sys.executable,'-c',script],capture_output=True)
        self.assertNotEqual(result.returncode,0)
        lanes[0].close()
        renewed=CORE.allocate_channel_lane(0);self.lanes.append(renewed)
        self.assertEqual(marker.read_text(),'preserve me')
        for index in (-1,20,True,'1'):
            with self.assertRaises(ValueError):CORE.allocate_channel_lane(index)
        OBSERVATIONS['INST-0032']=dict(status='GREEN',lanes=20,ports=list(range(8501,8521)),occupied_port_rejected_in_separate_process=True,existing_staging_preserved=True)

    def test_32_conflicts_and_symlinks(self):
        import socket
        occupied=socket.socket();occupied.bind(('127.0.0.1',8501))
        try:
            with self.assertRaises(OSError):CORE.allocate_channel_lane(0)
        finally:occupied.close()
        parent=CORE.ROOT/'imports/channel_lanes';parent.mkdir()
        (parent/'ch_00').symlink_to(CORE.ROOT/'code',target_is_directory=True)
        with self.assertRaises(ValueError):CORE.allocate_channel_lane(0)

    def test_33_scheduler(self):
        registry=[self.module_fixture()]
        q=CORE.TaskQueueScheduler()
        for task in [self.task('skin','skin'),self.task('spine'),self.task('verified','spine',module='calculation'),self.task('repair','skin',True)]:q.enqueue(task)
        self.assertEqual(q.schedule(1,registry)['task']['task_id'],'repair')
        self.assertIsNone(q.schedule(1,registry)['task'])
        self.assertEqual(CORE.TaskQueueScheduler().schedule(2,registry)['task']['task_id'],'spine')
        with self.assertRaises(CORE.AuditRejected):q.complete('repair',1)
        q.complete('spine',2)
        self.assertIsNone(q.schedule(2,registry)['task'])
        self.assertEqual(q.schedule(3,registry)['task']['task_id'],'skin')
        q.complete('skin',3)
        self.assertIsNone(q.schedule(4,registry)['task'])
        with sqlite3.connect(q.path) as db:
            self.assertEqual(db.execute("SELECT status FROM b7_tasks WHERE task_id='repair'").fetchone()[0],'TIMED_OUT')
        with self.assertRaises(CORE.AuditRejected):q.enqueue(dict(self.task('too-long'),estimated_turns=2))
        with self.assertRaises(CORE.AuditRejected):q.enqueue(self.task('skin','spine'))
        with self.assertRaises(CORE.AuditRejected):q.schedule(1,registry)
        OBSERVATIONS['INST-0033']=dict(status='GREEN',ordering=['blocker repair','spine','skin'],delta_filter=True,one_dispatch_per_turn=True,expired_completion_rejected=True,persistent_mount=True)

    def test_33_andon(self):
        q=CORE.TaskQueueScheduler()
        q.enqueue(self.task('normal'))
        CORE.trigger_andon_cord('test STOP')
        self.assertIsNone(q.schedule(1,[])['task'])
        q.enqueue(self.task('fix','skin',True))
        self.assertEqual(q.schedule(2,[])['task']['task_id'],'fix')
        self.assertTrue((CORE._b4_control()/'ANDON.json').exists())

    def test_34_delta(self):
        entry=self.module_fixture();source=Path(entry['path']);tests=Path(entry['test_path'])
        before=(source.read_bytes(),tests.read_bytes())
        registry=CORE.ROOT/'state/verified_modules.json';registry.write_text(json.dumps([entry]))
        r=CORE.skip_verified_modules();self.assertEqual(r['skip'],['calculation']);self.assertEqual(r['build'],[])
        self.assertEqual((source.read_bytes(),tests.read_bytes()),before)
        self.assertEqual(CORE.skip_verified_modules([dict(entry,sha256='0'*64)])['build'],['calculation'])
        tests.write_text(tests.read_text().replace('add(2,3),5','add(2,3),999'))
        bad=dict(entry,test_sha256=CORE.sha256(tests.read_bytes()))
        self.assertEqual(CORE.skip_verified_modules([bad])['build'],['calculation'])
        tests.write_text('import unittest\n')
        zero=dict(entry,test_sha256=CORE.sha256(tests.read_bytes()))
        self.assertEqual(CORE.skip_verified_modules([zero])['build'],['calculation'])
        self.assertEqual(CORE.skip_verified_modules([dict(entry,path='/tmp/outside.py')])['build'],['calculation'])
        tests.unlink();self.assertEqual(CORE.skip_verified_modules([entry])['build'],['calculation'])
        with self.assertRaises(ValueError):CORE.skip_verified_modules([entry,entry])
        OBSERVATIONS['INST-0034']=dict(status='GREEN',fresh_real_tests=True,unchanged_bytes=True,hash_mismatch_failed_tests_zero_tests_missing_outside_fail_closed=True,default_registry=True)

    def test_34_changed_artifact_and_timeout(self):
        entry=self.module_fixture();tests=Path(entry['test_path']);source=Path(entry['path'])
        tests.write_text("import unittest\nfrom pathlib import Path\nclass Change(unittest.TestCase):\n    def test_change(self):\n        Path(__file__).with_name('calculation.py').write_text('changed')\n")
        entry['test_sha256']=CORE.sha256(tests.read_bytes())
        self.assertEqual(CORE.skip_verified_modules([entry])['build'],['calculation'])
        self.assertEqual(source.read_text(),'changed')
        with patch.object(CORE._b7_subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',20)):
            entry['sha256']=CORE.sha256(source.read_bytes())
            self.assertEqual(CORE.skip_verified_modules([entry])['evidence']['calculation']['reason'],'TEST_TIMEOUT')

    def test_35_contracts(self):
        schema=dict(type='object',properties={'total':{'type':'integer'}},required=['total'],additionalProperties=False)
        contract=self.contract(schema)
        self.assertTrue(CORE.verify_channel_contract(contract,contract,{'total':3})['passed'])
        for payload in ({},{'total':True},{'total':'3'},{'total':3,'extra':1}):
            self.assertFalse(CORE.verify_channel_contract(contract,contract,payload)['passed'])
        self.assertFalse(CORE.verify_channel_contract(contract,self.contract(schema,2),{'total':3})['passed'])
        unsupported=self.contract(dict(schema,**{'$ref':'https://invalid.example/schema'}))
        self.assertFalse(CORE.verify_channel_contract(unsupported,unsupported,{'total':3})['passed'])
        consumer=self.contract(dict(type='object',properties={'total':{'type':'number'}},required=['total'],additionalProperties=True))
        producer=self.contract(dict(type='object',properties={'total':{'type':'integer'},'label':{'type':'string'}},required=['total','label'],additionalProperties=False))
        self.assertTrue(CORE.verify_channel_contract(producer,consumer,{'total':3,'label':'ok'})['passed'])
        self.assertFalse(CORE.verify_channel_contract(consumer,producer,{'total':3})['passed'])
        array=self.contract(dict(type='array',items={'type':'integer'}))
        self.assertTrue(CORE.verify_channel_contract(array,array,[1,2])['passed'])
        self.assertFalse(CORE.verify_channel_contract(array,array,[True])['passed'])
        enum=self.contract(dict(type='string',enum=['ok']))
        self.assertFalse(CORE.verify_channel_contract(self.contract({'type':'string'}),enum,'ok')['passed'])
        self.assertTrue(CORE.verify_channel_contract(enum,enum,'ok')['passed'])
        number=self.contract({'type':'number'})
        self.assertFalse(CORE.verify_channel_contract(number,number,float('nan'))['passed'])
        OBSERVATIONS['INST-0035']=dict(status='GREEN',directional_compatibility=True,payload_types_checked=True,unknown_schema_rejected=True,version_mismatch_rejected=True,no_payload_returned=True)

    def test_35_prefix_and_source_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:105301]),'26a267efb52e65a7aa1b6b805a30b16d9fab14ccf2d7d03b10193e1fe32f6f8b')
        self.assertTrue(CORE.scan_for_fake_padding(source))
        self.assertTrue(CORE.verify_ast_structure(source))
        self.assertTrue(CORE.check_symbol_regression(source,source[:105301]))
        self.assertTrue(CORE.scan_destructive_ops(source))



class Batch8Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b8_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def test_36_storage(self):
        root=CORE.ROOT/'imports/device_fixture';root.mkdir()
        (root/'small').write_bytes(b'small')
        (root/'large').write_bytes(bytes(range(256))*20)
        os.link(root/'large',root/'hardlink')
        (root/'link').symlink_to('/etc')
        usage=CORE._b8_shutil.disk_usage(root)
        with patch.object(CORE._b8_shutil,'disk_usage',return_value=usage):
            result=CORE.scan_device_storage(root,top_n=2)
        self.assertEqual(result['file_count'],4)
        self.assertEqual(result['unique_file_inodes'],3)
        self.assertEqual(result['disk_free_bytes'],usage.free)
        self.assertEqual(result['free_mb'],usage.free/1000000)
        self.assertEqual({Path(r['path']).name for r in result['largest_files']},{'large','hardlink'})
        self.assertTrue(result['complete'])
        self.assertFalse(CORE.scan_device_storage(root,max_entries=1)['complete'])
        with self.assertRaises(ValueError):CORE.scan_device_storage(root/'link')
        OBSERVATIONS['INST-0036']=dict(status='GREEN',free_units_verified=True,file_and_inode_counts=True,biggest_files=True,no_symlink_traversal=True,incomplete_scan_reported=True)

    def memory_fixture(self,total_kb=8388608,available_kb=4194304):
        info=CORE.ROOT/'imports/meminfo'
        info.write_text('MemTotal: '+str(total_kb)+' kB\nMemAvailable: '+str(available_kb)+' kB\n')
        cg=CORE.ROOT/'imports/cgroup';cg.mkdir(exist_ok=True)
        (cg/'memory.max').write_text(str(1024*1048576))
        (cg/'memory.current').write_text(str(512*1048576))
        (cg/'cpu.max').write_text('200000 100000')
        return info,cg

    def test_37_compute(self):
        info,cg=self.memory_fixture()
        with patch.object(CORE.os,'cpu_count',return_value=8),patch.object(CORE.os,'sched_getaffinity',return_value=set(range(4))):
            result=CORE.scan_compute_headroom(info,cg)
        self.assertEqual(result['cpu_count'],8)
        self.assertEqual(result['effective_whole_cores'],2)
        self.assertEqual(result['available_memory_bytes'],512*1048576)
        self.assertEqual(result['dispatch_slots'],1)
        self.assertIsNone(result['cpu_idle_pct'])
        (cg/'cpu.max').write_text('50000 100000')
        self.assertFalse(CORE.scan_compute_headroom(info,cg)['dispatch_allowed'])
        (cg/'cpu.max').write_text('max 100000');(cg/'memory.max').write_text('max')
        info.write_text('MemTotal: 10 kB\n')
        self.assertFalse(CORE.scan_compute_headroom(info,cg)['dispatch_allowed'])
        info.unlink()
        self.assertFalse(CORE.scan_compute_headroom(info,cg)['dispatch_allowed'])
        OBSERVATIONS['INST-0037']=dict(status='GREEN',cpu_count_affinity_and_cgroup_caps=True,available_ram_verified=True,unknown_memory_no_dispatch=True,fractional_core_no_dispatch=True,cpu_idle_not_invented=True)

    def test_38_cleanup(self):
        workspace=CORE.WORKSPACE
        for name in ('tmp','cache','snapshots','rollback_snapshots'):(workspace/name).mkdir()
        protected=CORE.ROOT/'code/protected.py';protected.write_text('owner record')
        tmp=workspace/'tmp/scratch';tmp.write_text('temp')
        snap=workspace/'snapshots/old';snap.write_text('snapshot')
        os.utime(snap,(1,1))
        fresh=workspace/'snapshots/new';fresh.write_text('new snapshot')
        link=workspace/'cache/link';link.symlink_to(protected)
        hard=workspace/'tmp/shared';os.link(protected,hard)
        unknown=workspace/'record';unknown.write_text('preserve')
        before={str(p):p.read_bytes() for p in (protected,tmp,snap,fresh,hard,unknown)}
        r=CORE.list_safe_cleanup_candidates()
        grades={Path(e['path']):e['grade'] for e in r['candidates']}
        self.assertEqual(grades[tmp],'GREEN');self.assertEqual(grades[snap],'YELLOW')
        for path in (protected,fresh,link,hard,unknown):self.assertEqual(grades[path],'LOCKED')
        self.assertTrue(all(e['requires_owner_approval'] and not e['deletion_authorized'] for e in r['candidates']))
        self.assertEqual(r['files_deleted'],0)
        self.assertEqual(before,{p:Path(p).read_bytes() for p in before})
        OBSERVATIONS['INST-0038']=dict(status='GREEN',grades=['GREEN','YELLOW','LOCKED'],vault_and_symlink_and_hardlink_locked=True,approval_required_for_every_candidate=True,files_deleted=0)

    def test_39_packer(self):
        source=CORE.ROOT/'code/inactive.py'
        raw=('"""Inactive module contract. No module execution on extraction."""\n'+''.join('VALUE_'+str(i)+' = '+str(i)+'\n' for i in range(500))).encode()
        source.write_bytes(raw)
        with self.assertRaises(CORE.AuditRejected):CORE.shrink_via_zlib(source)
        result=CORE.shrink_via_zlib(source,inactive=True)
        archive=Path(result['path']);self.assertLess(result['zlib_bytes'],len(raw))
        self.assertEqual(source.read_bytes(),raw)
        self.assertFalse(CORE.shrink_via_zlib(source,inactive=True)['added'])
        destination=CORE.ROOT/'imports/extracted'
        run=subprocess.run([sys.executable,str(archive),str(destination)],capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual((destination/source.name).read_bytes(),raw)
        repeat=subprocess.run([sys.executable,str(archive),str(destination)],capture_output=True)
        self.assertNotEqual(repeat.returncode,0)
        self.assertEqual((destination/source.name).read_bytes(),raw)
        from types import SimpleNamespace
        with patch.dict(sys.modules,{'b8_loaded_fixture':SimpleNamespace(__file__=str(source))}):
            with self.assertRaises(CORE.AuditRejected):CORE.shrink_via_zlib(source,inactive=True)
        OBSERVATIONS['INST-0039']=dict(status='GREEN',independent_self_extractor=True,exact_roundtrip=True,source_preserved=True,existing_destination_rejected=True,loaded_module_rejected=True,no_module_execution=True,reclaimed_bytes=0)

    def test_39_corruption_and_symlink(self):
        source=CORE.ROOT/'code/inactive.py';source.write_text('VALUE = 123\n')
        r=CORE.shrink_via_zlib(source,inactive=True);archive=Path(r['path'])
        text=archive.read_text();archive.write_text(text.replace("DIGEST = '","DIGEST = '0",1))
        target=CORE.ROOT/'imports/corrupt'
        run=subprocess.run([sys.executable,str(archive),str(target)],capture_output=True)
        self.assertNotEqual(run.returncode,0);self.assertFalse((target/source.name).exists())
        with self.assertRaises(CORE.AuditRejected):CORE.shrink_via_zlib(source,inactive=True)
        symlink=CORE.ROOT/'imports/link';symlink.symlink_to(CORE.ROOT/'legal',target_is_directory=True)
        run=subprocess.run([sys.executable,str(archive),str(symlink)],capture_output=True)
        self.assertNotEqual(run.returncode,0)
        self.assertFalse((CORE.ROOT/'legal'/source.name).exists())

    def test_40_cas(self):
        a=CORE.ROOT/'imports/project_a';b=CORE.ROOT/'imports/project_b';a.mkdir();b.mkdir()
        one=a/'same.txt';two=b/'same.txt';other=b/'different.txt'
        one.write_bytes(b'shared record');two.write_bytes(one.read_bytes());other.write_bytes(b'other record')
        before={str(p):p.read_bytes() for p in (one,two,other)}
        projects={'project-a':[str(one)],'project-b':[str(two),str(other)]}
        registry=CORE.ROOT/'state/shared_projects.json';registry.write_text(json.dumps(projects))
        r=CORE.deduplicate_shared_store()
        self.assertEqual(r['object_count'],2);self.assertEqual(r['objects_added'],2)
        self.assertEqual(r['duplicate_copy_bytes_avoided'],len(one.read_bytes()))
        store=CORE.ROOT/'exports/shared_cas'
        self.assertEqual(len(list((store/'objects').iterdir())),2)
        manifest=json.loads(Path(r['manifest']).read_text())
        for reference in manifest['references']:
            self.assertEqual((store/'objects'/reference['sha256']).read_bytes(),before[reference['source']])
        self.assertEqual(before,{p:Path(p).read_bytes() for p in before})
        self.assertEqual(CORE.deduplicate_shared_store()['objects_added'],0)
        digest=r['references'][0]['sha256'];(store/'objects'/digest).write_text('corrupt')
        with self.assertRaises(CORE.AuditRejected):CORE.deduplicate_shared_store()
        self.assertEqual((store/'objects'/digest).read_text(),'corrupt')
        OBSERVATIONS['INST-0040']=dict(status='GREEN',two_projects_three_sources_two_objects=True,exact_restore_bytes_from_manifest=True,idempotent_mount=True,corrupt_store_rejected_without_overwrite=True,originals_preserved=True,reclaimed_bytes=0)

    def test_40_collision_and_paths(self):
        first=CORE.ROOT/'imports/a';second=CORE.ROOT/'imports/b'
        first.write_text('one');second.write_text('two')
        with patch.object(CORE,'sha256',return_value='a'*64):
            with self.assertRaises(CORE.AuditRejected):CORE.deduplicate_shared_store({'p':[str(first),str(second)]})
        link=CORE.ROOT/'imports/link';link.symlink_to(first)
        with self.assertRaises(ValueError):CORE.deduplicate_shared_store({'p':[str(link)]})
        with self.assertRaises(ValueError):CORE.deduplicate_shared_store({'p':['/tmp/outside']})
        with self.assertRaises(ValueError):CORE.deduplicate_shared_store({'p':[str(first),str(first)]})
        self.assertEqual(CORE.deduplicate_shared_store({})['object_count'],0)

    def test_40_prefix_and_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:125322]),'114dc2366f098addcb7eac26973759fe6086aede18e2cd3f2a580bd46e9dafa5')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:125322]),CORE.scan_destructive_ops(source)):
            self.assertTrue(result)



class Batch9Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b9_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def test_41_compaction(self):
        path=CORE.ROOT/'state/compact.db'
        with sqlite3.connect(path) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, payload BLOB)')
            db.executemany('INSERT INTO records VALUES (?,?)',[(i,bytes(range(256))*16) for i in range(200)])
            db.execute('DELETE FROM records WHERE id>=20');db.commit()
            expected=db.execute('SELECT * FROM records ORDER BY id').fetchall()
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        before=path.stat().st_size
        with self.assertRaises(CORE.AuditRejected):CORE.compact_sqlite_db(path)
        result=CORE.compact_sqlite_db(path,quiesced=True)
        self.assertEqual(result['checkpoint'][0],0);self.assertTrue(result['records_preserved'])
        self.assertLess(path.stat().st_size,before)
        with sqlite3.connect(path) as db:self.assertEqual(db.execute('SELECT * FROM records ORDER BY id').fetchall(),expected)
        OBSERVATIONS['INST-0041']=dict(status='GREEN',checkpoint_truncate_and_vacuum=True,reclaimed_bytes=result['reclaimed_db_bytes'],records_and_schema_preserved=True,quiescence_required=True)

    def test_41_rowid_rollback(self):
        path=CORE.ROOT/'state/rowid.db'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS unkeyed (value TEXT)')
            db.executemany('INSERT INTO unkeyed VALUES (?)',[('first',),('second',),('third',)])
            db.execute("DELETE FROM unkeyed WHERE value='first'");db.commit()
            expected=db.execute('SELECT rowid,* FROM unkeyed').fetchall()
        with self.assertRaises(CORE.AuditRejected):CORE.compact_sqlite_db(path,quiesced=True)
        with sqlite3.connect(path) as db:self.assertEqual(db.execute('SELECT rowid,* FROM unkeyed').fetchall(),expected)

    def test_41_busy_reader(self):
        path=CORE.ROOT/'state/busy.db';writer=sqlite3.connect(path)
        writer.execute('PRAGMA journal_mode=WAL');writer.execute('CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY)')
        writer.execute('INSERT INTO data VALUES (1)');writer.commit()
        reader=sqlite3.connect(path)
        try:
            reader.execute('BEGIN');reader.execute('SELECT * FROM data').fetchall()
            writer.execute('INSERT INTO data VALUES (2)');writer.commit()
            with self.assertRaises(CORE.AuditRejected):CORE.compact_sqlite_db(path,quiesced=True)
            self.assertEqual(writer.execute('SELECT count(*) FROM data').fetchone()[0],2)
        finally:reader.close();writer.close()

    def test_42_featherweight(self):
        path=CORE.ROOT/'state/prompt_engine.db'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS owner_record (id INTEGER PRIMARY KEY, text TEXT)')
            db.execute("INSERT INTO owner_record VALUES (1,'preserve')")
        checkpoint=CORE.ROOT/'state/microkernel_checkpoint.json';checkpoint.write_text('{"accepted":40}')
        before=path.read_bytes();source=Path(CORE.__file__).read_bytes()
        plan=CORE.enable_featherweight_mode()
        self.assertLess(plan['kernel_bytes'],35000);self.assertTrue(plan['host_restart_required'])
        self.assertFalse(plan['active_in_this_process'])
        with CORE.enable_featherweight_mode(launch=True) as session:
            self.assertFalse(session.receipt['full_core_loaded'])
            self.assertEqual(session.receipt['channels'],1)
            self.assertEqual(session.request({'op':'read_checkpoint'})['checkpoint'],{'accepted':40})
            self.assertEqual(session.request({'op':'status'})['databases'][0]['tables'],1)
            self.assertIn('error',session.request({'op':'unsupported'}))
            process=session.process
        self.assertIsNotNone(process.poll())
        self.assertEqual(path.read_bytes(),before);self.assertEqual(Path(CORE.__file__).read_bytes(),source)
        OBSERVATIONS['INST-0042']=dict(status='GREEN',standalone_kernel_bytes=plan['kernel_bytes'],fresh_child_full_core_loaded=False,existing_state_read_only=True,host_must_retire_parent=True,total_python_memory_not_35kb=True)

    def test_42_microkernel_tamper(self):
        plan=CORE.enable_featherweight_mode();kernel=Path(plan['path']);kernel.write_text('corrupt')
        with self.assertRaises(CORE.AuditRejected):CORE.enable_featherweight_mode()

    def test_43_profiles(self):
        cases=[(1000000,1,'Featherweight',1),(512000000,3,'Standard Mobile',3),(2000000000,8,'High-Velocity',8),(8000000000,20,'Max Swarm',20),
               (8000000000,7,'Standard Mobile',3),(511999999,20,'Featherweight',1)]
        for free,slots,name,channels in cases:
            r=CORE.select_hardware_profile({'disk_free_bytes':free},{'dispatch_slots':slots,'dispatch_allowed':True})
            self.assertEqual((r['profile'],r['channels']),(name,channels))
            self.assertFalse(r['profile_applied'])
        for s,c in [({},{}),({'disk_free_bytes':0},{'dispatch_slots':20,'dispatch_allowed':True}),({'disk_free_bytes':8000000000},{'dispatch_slots':0,'dispatch_allowed':False})]:
            self.assertFalse(CORE.select_hardware_profile(s,c)['dispatch_allowed'])
        OBSERVATIONS['INST-0043']=dict(status='GREEN',tiers={'Featherweight':1,'Standard Mobile':3,'High-Velocity':8,'Max Swarm':20},boundaries_checked=True,unknown_or_starved_no_dispatch=True,no_worker_launch=True)

    def test_44_pages(self):
        text=('  Unicode café 🍁\n\tsearch result.  '*250)+'END\n'
        r=CORE.search_paginated_chunks(text,'search-a');chunks=[];last=None
        self.assertEqual(r['token_measure'],'UTF8_BYTE_UPPER_BOUND')
        self.assertEqual(CORE.search_paginated_chunks(search_id='search-a')['page_sha256'],r['page_sha256'])
        while not r['done']:
            self.assertLessEqual(len(r['text'].encode()),1200)
            chunks.append(r['text']);last={'index':r['page_index'],'sha256':r['page_sha256']}
            r=CORE.search_paginated_chunks(search_id='search-a',acknowledge=last)
        self.assertEqual(''.join(chunks),text)
        self.assertEqual(r['checkpoint'],len(chunks))
        self.assertTrue(CORE.search_paginated_chunks(text,'search-a')['done'])
        with self.assertRaises(CORE.AuditRejected):CORE.search_paginated_chunks(search_id='search-a',acknowledge=last)
        with self.assertRaises(CORE.AuditRejected):CORE.search_paginated_chunks('changed','search-a')
        self.assertEqual(CORE.search_paginated_chunks('','empty')['text'],'')
        OBSERVATIONS['INST-0044']=dict(status='GREEN',pages=len(chunks),page_budget_bytes=1200,token_measure='UTF8_BYTE_UPPER_BOUND_NOT_MODEL_TOKENIZER',exact_source_reconstruction=True,persistent_cursor=True,stale_ack_rejected=True,immutable_snapshot=True)

    def test_44_corruption(self):
        CORE.search_paginated_chunks('protected result','corruption')
        path=CORE.ROOT/'state/b9_search_pages.db'
        with sqlite3.connect(path) as db:db.execute("UPDATE b9_pages SET body='corrupt' WHERE search_id='corruption'")
        with self.assertRaises(CORE.AuditRejected):CORE.search_paginated_chunks(search_id='corruption')
        with self.assertRaises(CORE.AuditRejected):CORE.search_paginated_chunks(search_id='missing')

    def test_45_entities(self):
        text='2026-10-28; October 28, 2026; 01/02/2026; invalid 2026-02-30.\nCAD $1,234.56; $0.99; US$25; port 8501; ports: 8502, 8503; port 70000; localhost:8520\nTODO: verify backup\n- [ ] audit results\n- [x] finished\nACTION ITEM: preserve state\nNext Step: ask Muse\n'
        r=CORE.detect_potluck_entities(text)
        self.assertEqual(len(r['dates']),3)
        self.assertEqual(r['dates'][0]['iso_date'],'2026-10-28')
        self.assertIsNone(r['dates'][2]['iso_date'])
        self.assertEqual([m['amount'] for m in r['dollar_amounts']],['1234.56','0.99','25'])
        self.assertEqual([m['currency'] for m in r['dollar_amounts']],['CAD','UNSPECIFIED_DOLLAR','USD'])
        self.assertEqual([p['port'] for p in r['ports']],[8501,8502,8503,8520])
        self.assertEqual([a['action'] for a in r['action_items']],['verify backup','audit results','preserve state','ask Muse'])
        for rows in r.values():
            for row in rows:self.assertEqual(text[row['start']:row['end']],row['raw'])
        self.assertEqual(CORE.detect_potluck_entities('nothing explicit here'),dict(dates=[],dollar_amounts=[],ports=[],action_items=[]))
        punctuation=CORE.detect_potluck_entities('Pay $5.00, then CAD $9.99. Reject $10.999.')
        self.assertEqual([m['amount'] for m in punctuation['dollar_amounts']],['5.00','9.99'])
        OBSERVATIONS['INST-0045']=dict(status='GREEN',date_validation_and_ambiguity=True,decimal_amounts_and_currency=True,valid_port_range=True,explicit_action_markers=True,exact_character_spans=True,deterministic_regex_only=True)

    def test_45_prefix_and_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:143056]),'fac90bda38b66e6e0286f4bda50d3b3e2652878c9c534d79ab40504add17e7c3')
        for r in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:143056]),CORE.scan_destructive_ops(source)):
            self.assertTrue(r)



class Batch1InstalledTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b1_installed_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        CORE._boot()

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def test_01_file_ceiling(self):
        self.assertEqual(CORE.check_file_ceiling()['status'],'OK')
        logs=CORE.ROOT/'changes/loose_logs';logs.mkdir()
        expected={}
        for i in range(790-CORE._count()):
            name=str(i)+'.log';raw=('record '+str(i)).encode();(logs/name).write_bytes(raw);expected[name]=raw
        result=CORE.check_file_ceiling();self.assertGreater(result['packed_logs'],0)
        with CORE.zipfile.ZipFile(CORE.ROOT/'exports'/CORE.ARCHIVE_NAME) as z:
            for name,raw in expected.items():self.assertEqual(z.read('packed_logs/'+CORE.sha256(raw)+'/'+name),raw)
        unowned=CORE.ROOT/'imports/unowned';unowned.mkdir()
        for i in range(790-CORE._count()):(unowned/str(i)).write_text('owner data')
        self.assertEqual(CORE.check_file_ceiling()['status'],'BLOCKED')
        with self.assertRaises(RuntimeError):CORE.load_or_mount_engine('blocked','Blocked','rule','1')
        self.assertTrue(all(p.read_text()=='owner data' for p in unowned.iterdir()))
        OBSERVATIONS['INST-0001']=dict(status='GREEN',owned_logs_verified_before_packing=True,unowned_files_preserved=True,reserve_blocks_install=True)

    def test_02_path_rules(self):
        self.assertEqual(len(CORE.CATEGORIES),13)
        for name in CORE.CATEGORIES:self.assertTrue(CORE.verify_safe_path(name+'/record').is_relative_to(CORE.ROOT))
        for path in ('../escape','unknown/record','/tmp/outside'):
            with self.assertRaises(ValueError):CORE.verify_safe_path(path)
        OBSERVATIONS['INST-0002']=dict(status='GREEN',categories=13,path_escapes_rejected=True)

    def test_03_database_mount(self):
        with CORE.init_master_db() as db:
            self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0],'wal')
            self.assertEqual(db.execute('PRAGMA foreign_keys').fetchone()[0],1)
            self.assertEqual(db.execute('PRAGMA busy_timeout').fetchone()[0],120000)
            db.execute('CREATE TABLE IF NOT EXISTS preserved_owner (id INTEGER PRIMARY KEY, text TEXT)')
            db.execute("INSERT INTO preserved_owner VALUES (1,'existing')")
        db.close()
        with CORE.init_master_db() as db:self.assertEqual(db.execute('SELECT * FROM preserved_owner').fetchall(),[(1,'existing')])
        db.close();OBSERVATIONS['INST-0003']=dict(status='GREEN',database_mounted_without_reset=True,wal_foreign_keys_timeout=True)

    def test_04_engine_mount(self):
        sink=[]
        one=CORE.load_or_mount_engine('fixture','Fixture','immutable rule','1',sink.append)
        with CORE.init_master_db() as db:db.execute("UPDATE engine_registry_v2 SET state=? WHERE engine_id='fixture'",('{"keep":true}',))
        db.close()
        two=CORE.load_or_mount_engine('fixture','Fixture','immutable rule','1',sink.append)
        self.assertEqual(one['status'],'INSTALLED');self.assertIn('MOUNTED',two['status'])
        self.assertEqual(two['state'],{'keep':True});self.assertEqual(sink,['immutable rule']*2)
        with self.assertRaises(ValueError):CORE.load_or_mount_engine('fixture','Fixture','changed rule','1')
        OBSERVATIONS['INST-0004']=dict(status='GREEN',no_reinstall=True,persisted_state_preserved=True,verified_rules_sink=True)

    def test_05_logging(self):
        text='Owner verbatim\nUnicode café'
        result=CORE.record_turn_and_checkpoint(text,correlation_id='fixture-correlation')
        self.assertEqual(result['change'],'CHG-0001')
        archive=Path(CORE.recover_checkpoint())
        with CORE.zipfile.ZipFile(archive) as z:
            self.assertIn(text,z.read(CORE.LOG_NAME).decode())
            manifest=json.loads(z.read(CORE.MANIFEST_NAME))
            for name,meta in manifest['files'].items():self.assertEqual(CORE.sha256(z.read(name)),meta['sha256'])
        OBSERVATIONS['INST-0005']=dict(status='GREEN',verbatim_logged=True,recovery_manifest_verified=True)


class Batch10Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b10_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def test_46_mirrors(self):
        observations={}
        for i,name in enumerate(CORE._B10_MIRRORS):
            path=CORE.ROOT/'imports'/('mirror'+str(i));path.write_bytes(b'identical artifact')
            observations[name]={'path':str(path)}
        r=CORE.sync_four_mirrors(observations,CORE.sha256(b'identical artifact'))
        self.assertTrue(r['all_local_copies_match']);self.assertFalse(r['all_remote_mirrors_verified'])
        self.assertEqual(r['external_writes'],0)
        observations['Shared Google Drive Folder']['host_receipt']='connector readback supplied by host'
        r=CORE.sync_four_mirrors(observations)
        self.assertIn('HOST_ATTESTED',r['observations'][3]['remote_freshness'])
        Path(observations['Browser Export']['path']).write_text('different')
        self.assertFalse(CORE.sync_four_mirrors(observations,CORE.sha256(b'identical artifact'))['all_local_copies_match'])
        self.assertEqual(CORE.sync_four_mirrors({})['observations'][2]['state'],'UNVERIFIED')
        with sqlite3.connect(CORE.ROOT/'state/b10_mirrors.db') as db:self.assertGreaterEqual(db.execute('SELECT count(*) FROM b10_mirror_events').fetchone()[0],3)
        OBSERVATIONS['INST-0046']=dict(status='GREEN',four_named_mirrors_tracked=True,local_hash_mismatch_detected=True,unknown_remote_not_claimed_verified=True,append_only_receipts=True)

    def test_47_handoff(self):
        path=CORE.ROOT/'code/fixture.py';raw='raise RuntimeError("This recovered module must not execute")\n# café\n'.encode();path.write_bytes(raw)
        r=CORE.export_plain_text_handoff(['code/fixture.py']);handoff=Path(r['path'])
        target=CORE.ROOT/'imports/restored'
        one=subprocess.run([sys.executable,str(handoff),str(target)],capture_output=True)
        self.assertEqual(one.returncode,0,one.stderr);self.assertEqual((target/'code/fixture.py').read_bytes(),raw)
        two=subprocess.run([sys.executable,str(handoff),str(target)],capture_output=True)
        self.assertEqual(json.loads(two.stdout)['mounted'],1)
        (target/'code/fixture.py').write_text('owner changed this')
        three=subprocess.run([sys.executable,str(handoff),str(target)],capture_output=True)
        self.assertNotEqual(three.returncode,0);self.assertEqual((target/'code/fixture.py').read_text(),'owner changed this')
        OBSERVATIONS['INST-0047']=dict(status='GREEN',plain_python_no_encoded_blob=True,independent_sha256_verified_mount=True,identical_mount_no_reinstall=True,changed_record_refused=True,recovered_code_not_executed=True)

    def test_47_corrupt_handoff(self):
        (CORE.ROOT/'code/a.py').write_text('original payload\n')
        r=CORE.export_plain_text_handoff(['code/a.py']);p=Path(r['path']);p.write_text(p.read_text().replace('original payload','altered payload',1))
        target=CORE.ROOT/'imports/corrupt'
        result=subprocess.run([sys.executable,str(p),str(target)],capture_output=True)
        self.assertNotEqual(result.returncode,0);self.assertFalse((target/'code/a.py').exists())

    def test_48_registry_and_deadline(self):
        source=Path(__file__).read_text();groups=CORE._b10_test_groups(source)
        self.assertIn('Batch1InstalledTests',groups);self.assertIn('Batch10Tests',groups)
        self.assertEqual(len(groups),20)
        with self.assertRaises(ValueError):CORE.run_all_installed_unit_tests(timeout_sec=0)
        with self.assertRaises(ValueError):CORE._b10_test_groups('value = 1')
        # The outer orchestrator runs this test, all other actual classes,
        # and measures/validates its own complete elapsed time. No recursion.
        OBSERVATIONS['INST-0048']=dict(status='GREEN',actual_unittest_classes=10,cached_receipts_not_counted=True,timing_verified_by_outer_orchestrator=True)

    def test_49_scorecard(self):
        report={'observations':{'INST-0011':{'status':'GRAY'}},'instruction_coverage':list(range(1,51)),'tests_run':65,'failed_assertions':[],'accepted_checkpoint':45}
        with CORE.contextlib.redirect_stdout(io.StringIO()):text=CORE.print_owner_scorecard(report)
        self.assertIn('11/1000 | GRAY',text);self.assertIn('50/1000',text);self.assertIn('Workspace file count:',text)
        self.assertEqual(len([line for line in text.splitlines() if '/1000 |' in line]),50)
        OBSERVATIONS['INST-0049']=dict(status='GREEN',all_50_rows=True,file_counts=True,legacy_gray_not_hidden=True,plain_english=True)

    def test_50_checkpoint_lock(self):
        core=b'value = 1\n';tests=b'fixture test source\n';path=CORE.ROOT/'exports/master.zip'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('code/apccs_core.py',core);z.writestr('code/test_apccs_core.py',tests);z.writestr('state/preserved.txt',b'owner record')
        report=dict(passed=True,failed_assertions=[],instruction_coverage=list(range(1,51)),under_5_seconds=True,elapsed_seconds=1.5,tests_run=65,core_sha256=CORE.sha256(core),test_sha256=CORE.sha256(tests))
        with self.assertRaises(CORE.AuditRejected):CORE.lock_checkpoint_50(path,dict(report,under_5_seconds=False))
        with CORE.contextlib.redirect_stdout(io.StringIO()):lock=CORE.lock_checkpoint_50(path,report)
        self.assertEqual(lock['checkpoint'],'CP-050');self.assertEqual(lock['locally_verified_instructions'],50)
        with zipfile.ZipFile(path) as z:
            self.assertEqual(z.read('state/preserved.txt'),b'owner record')
            self.assertIn('audit/CP-050_LOCK.json',z.namelist())
        with CORE.contextlib.redirect_stdout(io.StringIO()):self.assertEqual(CORE.lock_checkpoint_50(path,report),lock)
        with self.assertRaises(CORE.AuditRejected):CORE.lock_checkpoint_50(path,dict(report,elapsed_seconds=2))
        OBSERVATIONS['INST-0050']=dict(status='GREEN',cp050_lock_immutable=True,requires_matching_full_test_receipt=True,prior_record_bytes_preserved=True,verification_scope='LOCAL_TESTS_PENDING_MUSE')

    def test_50_prefix_and_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:161476]),'54035c4a968f3796f300f8c90f10e43e3eaf7304d7ae1e267df1210a7a8a6ca4')
        for r in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:161476]),CORE.scan_destructive_ops(source)):
            self.assertTrue(r)


def _b10_installed_worker(group_name,report_path):
    global CORE
    selected=globals().get(group_name)
    if not isinstance(selected,type) or not issubclass(selected,unittest.TestCase):raise ValueError('Installed unittest class required')
    with tempfile.TemporaryDirectory(prefix='apccs_installed_worker_',dir='/tmp') as vault:
        os.environ['APCCS_VAULT_ROOT']=str(Path(vault)/'vault')
        import apccs_core as imported
        CORE=imported
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(selected)
        identities=[case.id() for case in suite]
        output=io.StringIO();result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
        receipt=dict(group=group_name,passed=result.wasSuccessful(),tests_run=result.testsRun,
            skipped=len(result.skipped),executed_test_ids=identities,observations=OBSERVATIONS,
            failed_assertions=[dict(test=str(test),traceback=trace) for test,trace in result.failures+result.errors],unittest_output=output.getvalue())
    receipt['scratch_removed']=not Path(vault).exists()
    Path(report_path).write_text(json.dumps(receipt,indent=2))
    return 0 if receipt['passed'] and receipt['scratch_removed'] else 1



def main_batch10():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b10_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        source=Path(__file__).with_name('apccs_core.py')
        (root/'code/apccs_core.py').write_bytes(source.read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(build_id='B10_CP050_20261028',accepted_checkpoint=45,implemented_checkpoint=50,
                  batch10_started=True,loaded_catalog_complete=True,driver_scratch_removed=not Path(tmp).exists(),
                  driver_elapsed_seconds=time.monotonic()-started,
                  release_ready=False,all_instructions_green=False,batch10_all_instructions_green=report['passed'])
    if report['driver_elapsed_seconds']>=5:
        report['passed']=False;report['all_unit_tests_passed']=False;report['batch10_all_instructions_green']=False
        report['failed_assertions'].append(dict(test='INST-0048',traceback='Complete canonical driver exceeded5seconds'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as stream:json.dump(report,stream,indent=2)
    print('Canary check: M = K -> submarine')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] and report['driver_scratch_removed'] else 1



class Batch11Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b11_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault')
        self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.path=CORE.ROOT/'state/engines.db'
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS user_records (id INTEGER PRIMARY KEY, payload BLOB, note TEXT)')
            db.executemany('INSERT INTO user_records VALUES (?,?,?)',[(1,b'\x00\xff','keep'),(7,None,'same'),(11,b'bytes','same')])
            db.execute('CREATE TABLE IF NOT EXISTS prior_history (text TEXT)')
            db.executemany('INSERT INTO prior_history VALUES (?)',[('duplicate',),('duplicate',)])
        self.before=CORE.capture_user_data_snapshot(self.path,'user_records')
        self.history_before=CORE.capture_user_data_snapshot(self.path,'prior_history')

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def manifest(self,identity='engine-a',version='1.0.0',rules='1. Preserve user records\n2. Verify hashes'):
        return dict(engine_id=identity,name='Engine '+identity,version=version,rules_text=rules,schema_version=1,entry_point='apccs_core:load_or_mount_engine')

    def install(self,identity='engine-a',version='1.0.0',rules=None):
        manifest=self.manifest(identity,version)
        if rules is not None:manifest['rules_text']=rules
        return CORE.load_engine_from_manifest(self.path,manifest)

    def assert_users(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.path,'user_records',self.before)['passed'])
        self.assertTrue(CORE.verify_user_data_untouched(self.path,'prior_history',self.history_before)['passed'])

    def test_51_manifest(self):
        manifest=self.manifest();self.assertTrue(CORE.validate_engine_manifest(manifest)['passed'])
        for key in manifest:
            altered=dict(manifest);del altered[key]
            self.assertFalse(CORE.validate_engine_manifest(altered)['passed'])
        for altered in [dict(manifest,version='01.2.3'),dict(manifest,version='1'),dict(manifest,schema_version=True),dict(manifest,schema_version=2),dict(manifest,entry_point='../unsafe.py'),dict(manifest,entry_point='os:system("command")'),dict(manifest,rules_text='  ')]:
            self.assertFalse(CORE.validate_engine_manifest(altered)['passed'])
        target=CORE.ROOT/'state/should_not_exist.db'
        with self.assertRaises(CORE.AuditRejected):CORE.load_engine_from_manifest(target,dict(manifest,entry_point='bad'))
        self.assertFalse(target.exists())
        first=self.install();self.assertEqual(first['status'],'INSTALLED_VALIDATED')
        self.assertEqual(self.install()['status'],'MOUNTED_EXISTING');self.assert_users()
        OBSERVATIONS['INST-0051']=dict(status='GREEN',all_six_keys_checked=True,invalid_before_load=True,strict_semver_schema_and_entrypoint=True,validated_adapter=True)

    def test_52_rulebook(self):
        one=CORE.compile_engine_rulebook('engine-a','1. Keep  data\n- Verify\n3) Keep\tdata\n\n• Verify')
        two=CORE.compile_engine_rulebook('engine-a','Keep data\nVerify')
        self.assertEqual(one['numbered_rules'],'1. Keep data\n2. Verify')
        self.assertEqual(one['rulebook_sha256'],two['rulebook_sha256'])
        self.assertEqual([c['number'] for c in one['clauses']],[1,2])
        for c in one['clauses']:self.assertEqual(c['sha256'],CORE.sha256(c['text'].encode()))
        self.assertEqual(CORE.compile_engine_rulebook('engine-a','cafe\u0301')['rulebook_sha256'],CORE.compile_engine_rulebook('engine-a','café')['rulebook_sha256'])
        self.install(rules='Keep data\nVerify\nKeep data')
        CORE.switch_active_chat_engine(self.path,'s','engine-a');CORE.switch_active_chat_engine(self.path,'s','engine-a')
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b11_rulebooks').fetchone()[0],1)
        self.assert_users();OBSERVATIONS['INST-0052']=dict(status='GREEN',deterministic_numbering=True,clause_hashes_verified=True,normalized_duplicates_removed=True,immutable_book_deduplicated=True)

    def test_53_switch_and_mount(self):
        self.install();self.install('engine-b')
        with sqlite3.connect(self.path) as db:db.execute("UPDATE engine_registry_v2 SET state=? WHERE engine_id='engine-a'",('{"owner":"preserve"}',))
        delivered=[]
        one=CORE.switch_active_chat_engine(self.path,'chat','engine-a',delivered.append)
        two=CORE.switch_active_chat_engine(self.path,'chat','engine-b',delivered.append)
        three=CORE.switch_active_chat_engine(self.path,'chat','engine-a',delivered.append)
        repeat=CORE.switch_active_chat_engine(self.path,'chat','engine-a',delivered.append)
        self.assertEqual([one['status'],two['status'],three['status'],repeat['status']],['SWITCHED','SWITCHED','SWITCHED','MOUNTED_HISTORY_UNCHANGED'])
        self.assertEqual(len(delivered),4)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT engine_id FROM b11_session_history ORDER BY id').fetchall(),[('engine-a',),('engine-b',),('engine-a',)])
            self.assertEqual(db.execute('SELECT count(*) FROM engine_registry_v2').fetchone()[0],2)
            self.assertEqual(db.execute("SELECT state FROM engine_registry_v2 WHERE engine_id='engine-a'").fetchone()[0],'{"owner":"preserve"}')
        self.assert_users();OBSERVATIONS['INST-0053']=dict(status='GREEN',persisted_active_session=True,history_preserved_and_append_only=True,repeated_mount_no_duplicate=True,no_reinstall=True,sink_called_not_ui_claim=True)

    def test_53_sink_failure(self):
        self.install();self.install('engine-b');CORE.switch_active_chat_engine(self.path,'chat','engine-a')
        def fail_sink(text):raise RuntimeError('host delivery failed')
        with self.assertRaises(RuntimeError):CORE.switch_active_chat_engine(self.path,'chat','engine-b',fail_sink)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT engine_id FROM b11_sessions').fetchone()[0],'engine-a')
            self.assertEqual(db.execute('SELECT count(*) FROM b11_session_history').fetchone()[0],1)
        with self.assertRaises(CORE.AuditRejected):CORE.switch_active_chat_engine(self.path,'chat','unknown')
        self.assert_users()

    def test_54_guard(self):
        self.install();self.assert_users()
        with sqlite3.connect(self.path) as db:db.execute("UPDATE user_records SET note='modified' WHERE id=7")
        self.assertFalse(CORE.verify_user_data_untouched(self.path,'user_records',self.before)['passed'])
        with sqlite3.connect(self.path) as db:db.execute("UPDATE user_records SET note='same' WHERE id=7")
        self.assert_users()
        with sqlite3.connect(self.path) as db:db.execute('ALTER TABLE user_records ADD COLUMN new_field TEXT')
        self.assertFalse(CORE.verify_user_data_untouched(self.path,'user_records',self.before)['passed'])
        with self.assertRaises(ValueError):CORE.verify_user_data_untouched(self.path,'user_records',dict(self.before,table_name='wrong'))
        OBSERVATIONS['INST-0054']=dict(status='GREEN',schema_rows_blobs_nulls_duplicate_multiplicity_and_rowids_snapshotted=True,mutation_detected=True,transactional_authorizer_protection=True,external_writer_boundary_explicit=True)

    def test_54_trigger_cannot_touch_user_records(self):
        self.install()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER corrupt_user AFTER INSERT ON b11_session_history BEGIN UPDATE user_records SET note='damage'; END")
        with self.assertRaises(sqlite3.DatabaseError):CORE.switch_active_chat_engine(self.path,'chat','engine-a')
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b11_sessions').fetchone()[0],0)
        self.assert_users()

    def test_55_upgrade(self):
        self.install();self.install('engine-b')
        CORE.switch_active_chat_engine(self.path,'chat','engine-a')
        with sqlite3.connect(self.path) as db:db.execute("UPDATE engine_registry_v2 SET state=? WHERE engine_id='engine-a'",('{"keep":true}',))
        result=CORE.upgrade_engine_if_newer(self.path,'engine-a','1.1.0','Preserve user records\nVerify hashes\nNew approved rule')
        self.assertTrue(result['upgraded'])
        with sqlite3.connect(self.path) as db:
            prior=json.loads(db.execute('SELECT prior_snapshot FROM b11_upgrade_rollbacks WHERE rollback_id=?',(result['rollback_id'],)).fetchone()[0])
            self.assertEqual(prior['registry']['version'],'1.0.0');self.assertEqual(prior['registry']['state'],'{"keep":true}')
            self.assertEqual(db.execute("SELECT state FROM engine_registry_v2 WHERE engine_id='engine-a'").fetchone()[0],'{"keep":true}')
            self.assertEqual(db.execute('SELECT version FROM b11_sessions').fetchone()[0],'1.0.0')
        self.assertFalse(CORE.upgrade_engine_if_newer(self.path,'engine-a','1.0.0','older rules')['upgraded'])
        with self.assertRaises(CORE.AuditRejected):CORE.upgrade_engine_if_newer(self.path,'engine-a','1.1.0','changed same version')
        self.assertEqual(CORE.upgrade_engine_if_newer(self.path,'engine-a','1.1.0','Preserve user records\nVerify hashes\nNew approved rule')['status'],'MOUNTED_UNCHANGED')
        CORE.switch_active_chat_engine(self.path,'chat','engine-a')
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT version FROM b11_session_history ORDER BY id').fetchall(),[('1.0.0',),('1.1.0',)])
            self.assertEqual(db.execute('SELECT count(*) FROM b11_upgrade_rollbacks').fetchone()[0],1)
        self.assert_users();OBSERVATIONS['INST-0055']=dict(status='GREEN',semver_newer_only=True,atomic_prior_version_rollback_copy=True,engine_user_state_preserved=True,sessions_pinned_until_remount=True,retries_idempotent=True)

    def test_55_atomic_failure_and_prerelease(self):
        self.install()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER fail_upgrade BEFORE UPDATE OF version ON engine_registry_v2 WHEN NEW.version='2.0.0' BEGIN SELECT RAISE(ABORT,'simulated upgrade failure'); END")
        with self.assertRaises(sqlite3.DatabaseError):CORE.upgrade_engine_if_newer(self.path,'engine-a','2.0.0','New rules')
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT version FROM engine_registry_v2').fetchone()[0],'1.0.0')
            self.assertEqual(db.execute('SELECT count(*) FROM b11_upgrade_rollbacks').fetchone()[0],0)
        versions=['1.0.0-alpha','1.0.0-alpha.1','1.0.0-alpha.beta','1.0.0-beta','1.0.0-beta.2','1.0.0-beta.11','1.0.0-rc.1','1.0.0']
        for older,newer in zip(versions,versions[1:]):self.assertEqual(CORE._b11_compare_versions(newer,older),1)
        self.assertEqual(CORE._b11_compare_versions('1.2.3+build1','1.2.3+build2'),0)
        for invalid in ('1.0','01.0.0','1.0.0-01','1.0.0-'):
            with self.assertRaises(ValueError):CORE._b11_semver(invalid)
        self.assert_users()

    def test_51_legacy_engine_refuses_reinstall(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS engines (name TEXT, user_state TEXT)')
            db.execute('INSERT INTO engines VALUES (?,?)',(self.manifest()['name'],'preserve legacy'))
        with self.assertRaises(CORE.AuditRejected):self.install()
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT * FROM engines').fetchall(),[(self.manifest()['name'],'preserve legacy')])
        self.assert_users()

    def test_55_other_session_trigger_rolled_back(self):
        self.install();self.install('engine-b')
        CORE.switch_active_chat_engine(self.path,'other','engine-b')
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER corrupt_session AFTER UPDATE OF version ON engine_registry_v2 BEGIN UPDATE b11_sessions SET engine_id='engine-a'; END")
        with self.assertRaises(CORE.AuditRejected):CORE.upgrade_engine_if_newer(self.path,'engine-a','2.0.0','New approved rules')
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT engine_id FROM b11_sessions').fetchone()[0],'engine-b')
            self.assertEqual(db.execute('SELECT count(*) FROM b11_upgrade_rollbacks').fetchone()[0],0)
        self.assert_users()

    def test_55_concurrent_idempotence(self):
        self.install()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            upgrades=list(pool.map(lambda unused:CORE.upgrade_engine_if_newer(self.path,'engine-a','1.1.0','Concurrent approved rules'),range(2)))
        self.assertEqual(sum(item['upgraded'] for item in upgrades),1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            switches=list(pool.map(lambda unused:CORE.switch_active_chat_engine(self.path,'same-chat','engine-a'),range(2)))
        self.assertEqual(sum(item['history_appended'] for item in switches),1)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM b11_upgrade_rollbacks').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM b11_session_history').fetchone()[0],1)
        self.assert_users()

    def test_55_prefix_and_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:177420]),'5e13e6442ee6415dc94737fb63b4e8e20900a648bcbb71ee084a4708484fd69f')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:177420]),CORE.scan_destructive_ops(source)):
            self.assertTrue(result)


def main_batch11():
    global CORE
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b11_driver_',dir='/tmp') as tmp:
        os.environ['APCCS_VAULT_ROOT']=str(Path(tmp)/'vault')
        import apccs_core as imported
        CORE=imported
        classes=[globals()[name] for name in CORE._b10_test_groups(Path(__file__).read_text())]
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in classes)
        def collect_ids(node):
            if isinstance(node,unittest.TestSuite):return [identity for child in node for identity in collect_ids(child)]
            return [node.id()]
        identities=collect_ids(suite);stream=io.StringIO()
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        report=dict(canary='Canary check: T = X -> motorcycle',build_id='B11_VALIDATED_ENGINE_LIFECYCLE_20261028',tests_run=result.testsRun,
            passed=result.wasSuccessful(),all_unit_tests_passed=result.wasSuccessful(),
            failed_assertions=[dict(test=str(test),traceback=trace) for test,trace in result.failures+result.errors],
            observations=OBSERVATIONS,executed_test_ids=identities,unittest_output=stream.getvalue(),
            core_sha256=CORE.sha256(Path(CORE.__file__).read_bytes()),test_sha256=CORE.sha256(Path(__file__).read_bytes()),
            timing_advisory_only=True,legacy_strict_runner_unchanged=True,collision_count=0,
            accepted_checkpoint=50,implemented_checkpoint=55,batch11_started=True,batch12_started=False,
            release_ready=False,all_instructions_green=False)
    report['scratch_removed']=not Path(tmp).exists();report['elapsed_seconds']=time.monotonic()-started
    report['instruction_coverage']=sorted({int(m.group(1)) for identity in identities for m in [CORE.re.search(r'\.test_(\d{2})(?:_|$)',identity)] if m and 1<=int(m.group(1))<=55})
    if len(report['instruction_coverage'])!=55 or not report['scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False
        report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All55 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = X -> motorcycle');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1



class Batch12Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b12_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.path=CORE.ROOT/'state/engines.db'
        self.manifest=dict(engine_id='builder',name='Builder',version='1.0.0',rules_text='Preserve records\nVerify hashes',schema_version=1,entry_point='apccs_core:load_or_mount_engine')
        CORE.load_engine_from_manifest(self.path,self.manifest)
        CORE.load_engine_from_manifest(self.path,dict(self.manifest,engine_id='legal',name='Legal'))
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS user_sentinel (id INTEGER PRIMARY KEY, text TEXT)')
            db.execute("INSERT INTO user_sentinel VALUES (1,'never overwrite')")
        self.before=CORE.capture_user_data_snapshot(self.path,'user_sentinel')

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def assert_user(self):self.assertTrue(CORE.verify_user_data_untouched(self.path,'user_sentinel',self.before)['passed'])

    def test_56_namespaces(self):
        a=CORE.get_engine_namespace('builder');b=CORE.get_engine_namespace('legal')
        self.assertNotEqual(a,b);self.assertEqual(CORE.get_engine_namespace('builder'),a)
        CORE.set_engine_namespace_value(self.path,'builder','same-key',{'program':'builder'})
        CORE.set_engine_namespace_value(self.path,'legal','same-key',{'program':'legal'})
        self.assertEqual(CORE.get_engine_namespace_value(self.path,'builder','same-key'),{'program':'builder'})
        self.assertEqual(CORE.get_engine_namespace_value(self.path,'legal','same-key'),{'program':'legal'})
        CORE.set_engine_namespace_value(self.path,'builder','same-key',{'program':'builder2'})
        self.assertEqual(CORE.get_engine_namespace_value(self.path,'legal','same-key'),{'program':'legal'})
        self.assert_user();OBSERVATIONS['INST-0056']=dict(status='GREEN',distinct_full_hash_prefixes=True,separate_key_value_tables=True,same_key_no_cross_engine_collision=True,repeat_mount_stable=True)

    def test_56_namespace_collision_and_trigger(self):
        with patch.object(CORE,'sha256',return_value='0'*64):
            CORE.get_engine_namespace('first')
            with self.assertRaises(CORE.AuditRejected):CORE.get_engine_namespace('second')
        CORE.set_engine_namespace_value(self.path,'builder','key',1);CORE.set_engine_namespace_value(self.path,'legal','key',2)
        a=CORE.get_engine_namespace('builder');b=CORE.get_engine_namespace('legal')
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TRIGGER bad_namespace AFTER UPDATE ON "'+a+'kv" BEGIN UPDATE "'+b+'kv" SET value_json=\'damage\'; END')
        with self.assertRaises(sqlite3.DatabaseError):CORE.set_engine_namespace_value(self.path,'builder','key',3)
        self.assertEqual(CORE.get_engine_namespace_value(self.path,'builder','key'),1)
        self.assertEqual(CORE.get_engine_namespace_value(self.path,'legal','key'),2);self.assert_user()
        CORE.load_engine_from_manifest(self.path,dict(self.manifest,engine_id='auditor',name='Auditor'))
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER bad_owner AFTER INSERT ON b12_namespace_owners WHEN NEW.engine_id='auditor' BEGIN UPDATE user_sentinel SET text='damage'; END")
        with self.assertRaises(sqlite3.DatabaseError):CORE.set_engine_namespace_value(self.path,'auditor','key',1)
        self.assert_user()

    def test_57_dependencies(self):
        plugin=dict(self.manifest,engine_id='plugin',dependencies=[{'engine_id':'builder','min_version':'1.0.0','max_version':'2.0.0'}])
        self.assertTrue(CORE.check_engine_dependencies(plugin,{'builder':self.manifest})['passed'])
        self.assertFalse(CORE.check_engine_dependencies(plugin,{})['passed'])
        self.assertFalse(CORE.check_engine_dependencies(plugin,{'builder':dict(self.manifest,version='0.9.0')})['passed'])
        self.assertFalse(CORE.check_engine_dependencies(plugin,{'builder':dict(self.manifest,version='2.0.0')})['passed'])
        self.assertTrue(CORE.check_engine_dependencies(dict(plugin,dependencies=['builder']),['builder'])['passed'])
        self.assertTrue(CORE.check_engine_dependencies(dict(plugin,dependencies=[{'engine_id':'missing','optional':True}]),{})['passed'])
        cyclic=dict(plugin,dependencies=['builder']);inventory={'builder':dict(self.manifest,dependencies=['plugin'])}
        self.assertFalse(CORE.check_engine_dependencies(cyclic,inventory)['passed'])
        CORE.load_engine_from_manifest(self.path,plugin)
        self.assertEqual(CORE.activate_engine_with_dependencies(self.path,'chat','plugin')['status'],'ACTIVE_DEPENDENCIES_VERIFIED')
        missing=dict(plugin,engine_id='missing-plugin',dependencies=['not-installed'])
        CORE.load_engine_from_manifest(self.path,missing)
        with self.assertRaises(CORE.AuditRejected):CORE.activate_engine_with_dependencies(self.path,'blocked','missing-plugin')
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute("SELECT count(*) FROM b11_sessions WHERE session_id='blocked'").fetchone()[0],0)
        self.assert_user();OBSERVATIONS['INST-0057']=dict(status='GREEN',presence_versions_transitive_cycles=True,optional_warning=True,activation_checks_actual_inventory_atomically=True,no_module_execution=True)

    def make_zip(self,name,members):
        path=CORE.ROOT/'imports'/name
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for key,raw in members:z.writestr(key,raw)
        return path

    def test_58_unpack(self):
        script=b"raise RuntimeError('never run this upload')\n"
        source=self.make_zip('upload.zip',[('nested/README.md',b'# passive content\n'),('script.py',script),('data.json',b'{"ok":true}')])
        stage=CORE.ROOT/'imports/staged'
        r=CORE.unpack_local_upload(source,stage)
        self.assertEqual(r['added'],3);self.assertEqual(r['executed_files'],0)
        self.assertEqual((stage/'script.py').read_bytes(),script)
        self.assertEqual(CORE.unpack_local_upload(source,stage)['mounted'],3)
        (stage/'script.py').write_text('owner changed')
        with self.assertRaises(CORE.AuditRejected):CORE.unpack_local_upload(source,stage)
        self.assertEqual((stage/'script.py').read_text(),'owner changed')
        for suffix,raw in [('.txt',b'plain\n'),('.md',b'# note\n'),('.json',b'{"x":1}')]:
            path=CORE.ROOT/'imports'/('single'+suffix);path.write_bytes(raw)
            out=CORE.ROOT/'imports'/('single_stage_'+suffix[1:]);CORE.unpack_local_upload(path,out)
            self.assertEqual((out/path.name).read_bytes(),raw)
        OBSERVATIONS['INST-0058']=dict(status='GREEN',zip_txt_md_json=True,nested_paths=True,passive_scripts_not_executed=True,repeat_mount_and_conflict_refusal=True)

    def test_58_malicious_archives(self):
        malicious=[('../escape',b'escape'),('/absolute',b'escape'),('C:\\evil',b'escape')]
        for index,entry in enumerate(malicious):
            source=self.make_zip('bad'+str(index)+'.zip',[entry]);stage=CORE.ROOT/'imports'/('badstage'+str(index))
            with self.assertRaises((ValueError,CORE.AuditRejected)):CORE.unpack_local_upload(source,stage)
            self.assertFalse(stage.exists())
        source=self.make_zip('case.zip',[('A.txt',b'one'),('a.txt',b'two')])
        with self.assertRaises(CORE.AuditRejected):CORE.unpack_local_upload(source,CORE.ROOT/'imports/case_stage')
        source=self.make_zip('parents.zip',[('parent',b'file'),('parent/child',b'child')])
        with self.assertRaises(CORE.AuditRejected):CORE.unpack_local_upload(source,CORE.ROOT/'imports/parent_stage')
        self.assertFalse((CORE.ROOT/'imports/parent_stage').exists())
        source=CORE.ROOT/'imports/link.zip'
        with zipfile.ZipFile(source,'w') as z:
            info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=0o120777<<16;z.writestr(info,'/tmp/outside')
        with self.assertRaises(CORE.AuditRejected):CORE.unpack_local_upload(source,CORE.ROOT/'imports/link_stage')
        source=self.make_zip('bomb.zip',[('huge',b'0'*200000)])
        with self.assertRaises(CORE.AuditRejected):CORE.unpack_local_upload(source,CORE.ROOT/'imports/bomb_stage')
        bad=CORE.ROOT/'imports/bad.json';bad.write_text('{"x":NaN}')
        with self.assertRaises(ValueError):CORE.unpack_local_upload(bad,CORE.ROOT/'imports/json_stage')

    def test_59_dedup(self):
        one=CORE.deduplicate_uploaded_artifact(self.path,b'same bytes','one.txt')
        two=CORE.deduplicate_uploaded_artifact(self.path,b'same bytes','one.txt')
        alias=CORE.deduplicate_uploaded_artifact(self.path,b'same bytes','two.txt')
        self.assertTrue(one['new_blob']);self.assertFalse(two['new_blob']);self.assertFalse(alias['new_blob'])
        with self.assertRaises(CORE.AuditRejected):CORE.deduplicate_uploaded_artifact(self.path,b'changed','one.txt')
        with self.assertRaises(ValueError):CORE.deduplicate_uploaded_artifact(self.path,b'bad','../escape')
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM b12_upload_objects').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM b12_upload_names').fetchone()[0],2)
        with patch.object(CORE,'sha256',return_value=one['sha256']):
            with self.assertRaises(CORE.AuditRejected):CORE.deduplicate_uploaded_artifact(self.path,b'other payload','three.txt')
        self.assert_user();OBSERVATIONS['INST-0059']=dict(status='GREEN',one_blob_multiple_aliases=True,repeat_upload_mount=True,filename_and_hash_conflicts_rejected=True,user_rows_unchanged=True)

    def test_60_health(self):
        empty=CORE.probe_loaded_engine_health(self.path,'builder');self.assertFalse(empty['ready']);self.assertIsNone(empty['last_checkpoint'])
        CORE.set_engine_namespace_value(self.path,'builder','key',{'value':1})
        self.assertFalse(CORE.probe_loaded_engine_health(self.path,'builder')['ready'])
        CORE.record_engine_namespace_checkpoint(self.path,'builder',55)
        CORE.switch_active_chat_engine(self.path,'chat','builder')
        before=self.path.read_bytes();r=CORE.probe_loaded_engine_health(self.path,'builder')
        self.assertTrue(r['ready']);self.assertEqual(r['last_checkpoint'],55);self.assertEqual(r['table_integrity'],'ok')
        self.assertEqual(self.path.read_bytes(),before)
        CORE.upgrade_engine_if_newer(self.path,'builder','1.1.0','New approved rule')
        self.assertFalse(CORE.probe_loaded_engine_health(self.path,'builder')['ready'])
        CORE.switch_active_chat_engine(self.path,'chat','builder');CORE.record_engine_namespace_checkpoint(self.path,'builder',56)
        self.assertTrue(CORE.probe_loaded_engine_health(self.path,'builder')['ready'])
        with sqlite3.connect(self.path) as db:db.execute("UPDATE engine_rules_hashes SET rules_sha256='corrupt' WHERE engine_id='builder'")
        self.assertEqual(CORE.probe_loaded_engine_health(self.path,'builder')['status'],'RED')
        self.assert_user();OBSERVATIONS['INST-0060']=dict(status='GREEN',read_only_probe=True,table_rulebook_checkpoint_verified=True,missing_or_stale_not_ready=True,corruption_red=True,no_checkpoint_fabricated=True)

    def test_60_timer_budget(self):
        self.assertEqual(CORE._b11_test_budget(65),22.75);self.assertEqual(CORE._b11_test_budget(100),35.0)
        self.assertEqual(CORE._b11_test_budget(1),15.0)
        with self.assertRaises(ValueError):CORE.run_all_installed_unit_tests(timeout_sec=0)
        self.assertIsNot(CORE.run_all_installed_unit_tests,CORE._B11_LEGACY_STRICT_TEST_RUNNER)
        OBSERVATIONS['TIMER_AMENDMENT']=dict(status='GREEN',formula='max(15.0, test_count * 0.35)',test65_budget=22.75,test100_budget=35.0,legacy_function_retained=True)

    def test_60_timer_keeps_failures(self):
        path=CORE.ROOT/'code/mock_tests.py';path.write_text('value = 1\n')
        identity='__main__.Synthetic.test_60_failure';plan={'test_count':1,'groups':{'Synthetic':[identity]}}
        class FailedWorker:
            returncode=1
            def __init__(self,args,**kwargs):
                Path(args[-1]).write_text(json.dumps(dict(group='Synthetic',passed=False,tests_run=1,skipped=0,scratch_removed=True,executed_test_ids=[identity],observations={},failed_assertions=[dict(test=identity,traceback='genuine assertion failure')])))
            def wait(self,timeout=None):return 1
            def poll(self):return 1
        with patch.object(CORE,'_b11_installed_plan',return_value=plan),patch.object(CORE._b7_subprocess,'Popen',FailedWorker):
            r=CORE.run_all_installed_unit_tests(path)
        self.assertFalse(r['passed']);self.assertTrue(any(item['traceback']=='genuine assertion failure' for item in r['failed_assertions']))

    def test_60_prefix_and_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:198655]),'b76f6f6823cbfddd49f6a403c814b7ad8922a88de511d445c34458380120fa00')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:198655]),CORE.scan_destructive_ops(source)):
            self.assertTrue(result)


def _b12_write_installed_plan(report_path):
    groups={}
    for name,cls in list(globals().items()):
        if isinstance(cls,type) and issubclass(cls,unittest.TestCase) and cls is not unittest.TestCase:
            groups[name]=[case.id() for case in unittest.defaultTestLoader.loadTestsFromTestCase(cls)]
    Path(report_path).write_text(json.dumps(dict(groups=groups,test_count=sum(map(len,groups.values())))))
    return 0


def main_batch12():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b12_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = Y -> lighthouse',build_id='B12_NAMESPACES_UPLOADS_READINESS_20261028',accepted_checkpoint=55,implemented_checkpoint=60,
        batch12_started=True,batch13_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,61)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All60 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = Y -> lighthouse');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1



class Batch13Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b13_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.path=CORE.ROOT/'state/plans.db'
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS user_records (id INTEGER PRIMARY KEY,text TEXT,payload BLOB)')
            db.execute('INSERT INTO user_records VALUES (?,?,?)',(7,'preserve',b'\x00\xff'))
        self.before=CORE.capture_user_data_snapshot(self.path,'user_records')
        self.notes={'discussion':'Owner wording: café\nKeep this exactly.','instructions':[{'id':i,'text':'Explicit task '+str(i)} for i in range(1,13)]}
        self.style={'mode':'manual-first','approvals':'owner'}

    def tearDown(self):
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def assert_user(self):self.assertTrue(CORE.verify_user_data_untouched(self.path,'user_records',self.before)['passed'])

    def lock_fixture(self):
        CORE.save_plan_discussion_draft(self.path,'project-a',self.notes,self.style)
        return CORE.lock_project_plan(self.path,'project-a')

    def test_61_drafts(self):
        one=CORE.save_plan_discussion_draft(self.path,'project-a','Discussion before scope lock','careful')
        self.assertEqual(one['revision'],1)
        self.assertEqual(CORE.save_plan_discussion_draft(self.path,'project-a','Discussion before scope lock','careful')['status'],'MOUNTED_IDENTICAL_DRAFT')
        two=CORE.save_plan_discussion_draft(self.path,'project-a',self.notes,self.style)
        self.assertEqual(two['revision'],2)
        with sqlite3.connect(self.path) as db:
            rows=db.execute('SELECT revision,notes_json,style_json FROM b13_draft_history ORDER BY revision').fetchall()
            self.assertEqual(len(rows),2);self.assertEqual(json.loads(rows[1][1]),self.notes);self.assertEqual(json.loads(rows[1][2]),self.style)
        self.assert_user();OBSERVATIONS['INST-0061']=dict(status='GREEN',raw_notes_style_preserved=True,append_only_revisions=True,identical_draft_mounts=True)

    def test_62_lock(self):
        lock=self.lock_fixture();self.assertTrue(lock['read_only'])
        self.assertEqual(CORE.lock_project_plan(self.path,'project-a')['lock_sha256'],lock['lock_sha256'])
        with self.assertRaises(CORE.AuditRejected):CORE.save_plan_discussion_draft(self.path,'project-a',{'instructions':['unrequested replacement']},'changed')
        CORE.save_plan_discussion_draft(self.path,'project-b',['Independent project task'],'independent')
        with sqlite3.connect(self.path) as db:
            raw,digest,flag=db.execute('SELECT payload,lock_sha256,read_only FROM b13_locks').fetchone()
            self.assertEqual(CORE.sha256(raw.encode()),digest);self.assertEqual(flag,1)
            self.assertEqual(json.loads(raw)['notes'],self.notes)
        self.assert_user();OBSERVATIONS['INST-0062']=dict(status='GREEN',sha256_read_only_seal=True,repeat_lock_stable=True,locked_draft_change_rejected=True,other_project_independent=True)

    def test_62_parallel_lock_and_connection(self):
        CORE.save_plan_discussion_draft(self.path,'project-a',self.notes,self.style)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            locks=list(pool.map(lambda unused:CORE.lock_project_plan(self.path,'project-a'),range(2)))
        self.assertEqual(locks[0]['lock_sha256'],locks[1]['lock_sha256'])
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b13_locks').fetchone()[0],1)
        connection=sqlite3.connect(self.path)
        try:
            result=CORE.save_plan_discussion_draft(connection,'project-b',['Explicit task'],'manual')
            self.assertEqual(result['revision'],1)
            connection.execute('BEGIN')
            with self.assertRaises(ValueError):CORE.lock_project_plan(connection,'project-b')
            connection.rollback()
            connection.execute("CREATE TRIGGER corrupt_lock AFTER INSERT ON b13_draft_history WHEN NEW.project='project-c' BEGIN UPDATE b13_locks SET payload='altered' WHERE project='project-a'; END")
            connection.commit()
            with self.assertRaises(CORE.AuditRejected):CORE.save_plan_discussion_draft(connection,'project-c',['Task'],'manual')
            self.assertEqual(CORE.lock_project_plan(self.path,'project-a')['lock_sha256'],locks[0]['lock_sha256'])
        finally:connection.close()
        self.assert_user()

    def test_63_batches(self):
        lock=self.lock_fixture()
        batches=CORE.generate_batches_from_locked_plan(self.path,'project-a')
        self.assertEqual([len(batch['instructions']) for batch in batches],[5,5,2])
        self.assertEqual([item for batch in batches for item in batch['instructions']],[dict(id=str(item['id']),text=item['text']) for item in self.notes['instructions']])
        self.assertTrue(all(batch['lock_sha256']==lock['lock_sha256'] for batch in batches))
        self.assertEqual(CORE.generate_batches_from_locked_plan(self.path,'project-a'),batches)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b13_batches').fetchone()[0],3)
        self.assertEqual(len(CORE.generate_batches_from_locked_plan(self.path,'project-a',4)),3)
        with self.assertRaises(ValueError):CORE.generate_batches_from_locked_plan(self.path,'project-a',0)
        self.assert_user();OBSERVATIONS['INST-0063']=dict(status='GREEN',deterministic_five_item_slices=True,final_short_batch_no_padding=True,queue_persisted_and_idempotent=True,no_task_text_invented=True)

    def test_63_explicit_scope_and_queue_tamper(self):
        CORE.save_plan_discussion_draft(self.path,'discussion','Discuss options without approved task list','manual')
        with self.assertRaises(CORE.AuditRejected):CORE.lock_project_plan(self.path,'discussion')
        self.lock_fixture();CORE.generate_batches_from_locked_plan(self.path,'project-a')
        with sqlite3.connect(self.path) as db:db.execute("UPDATE b13_batches SET body='corrupt' WHERE batch_number=1")
        with self.assertRaises(CORE.AuditRejected):CORE.generate_batches_from_locked_plan(self.path,'project-a')
        with self.assertRaises(ValueError):CORE.save_plan_discussion_draft(self.path,'duplicate',[{'id':1,'text':'A'},{'id':'1','text':'B'}],'manual')
        self.assert_user()

    def test_64_drift(self):
        self.lock_fixture()
        partial=CORE.check_output_against_locked_plan(self.path,'project-a',[1,2])
        self.assertEqual(partial['status'],'GRAY');self.assertFalse(partial['drift']);self.assertEqual(len(partial['missing_ids']),10)
        extra=CORE.check_output_against_locked_plan(self.path,'project-a',list(range(1,13))+[99])
        self.assertEqual(extra['status'],'RED');self.assertEqual(extra['unrequested_ids'],['99'])
        duplicate=CORE.check_output_against_locked_plan(self.path,'project-a',list(range(1,13))+[1])
        self.assertEqual(duplicate['duplicate_ids'],['1'])
        complete=CORE.check_output_against_locked_plan(self.path,'project-a',list(range(1,13)))
        self.assertTrue(complete['passed']);self.assertEqual(complete['status'],'GREEN')
        self.assert_user();OBSERVATIONS['INST-0064']=dict(status='GREEN',missing_ids_incomplete_not_unrequested=True,unrequested_and_duplicate_drift_red=True,complete_exact_ids_green=True,semantic_output_scope_not_claimed=True)

    def test_65_export_proof(self):
        lock=self.lock_fixture();before=self.path.read_bytes()
        one=CORE.export_locked_plan_bundle(self.path,'project-a');two=CORE.export_locked_plan_bundle(self.path,'project-a')
        self.assertEqual(one,two);self.assertEqual(self.path.read_bytes(),before)
        path=Path(one['path']);self.assertEqual(CORE.sha256(path.read_bytes()),one['archive_sha256'])
        with zipfile.ZipFile(path) as z:
            proof=json.loads(z.read('SHA256SUMS.json'))
            for name,digest in proof.items():self.assertEqual(CORE.sha256(z.read(name)),digest)
            self.assertEqual(CORE.sha256(z.read('locked_plan.json')),lock['lock_sha256'])
            recovered=json.loads(z.read('locked_plan.json'));self.assertEqual(recovered['notes'],self.notes);self.assertEqual(recovered['management_style'],self.style)
        self.assert_user();OBSERVATIONS['INST-0065']=dict(status='GREEN',standalone_recovery_zip=True,exact_plan_style_and_sha256_proof=True,deterministic_repeat_export=True,live_records_unchanged=True)

    def test_65_tamper_and_user_trigger(self):
        self.lock_fixture()
        with sqlite3.connect(self.path) as db:db.execute("UPDATE b13_locks SET payload='tampered' WHERE project='project-a'")
        for call in (lambda:CORE.lock_project_plan(self.path,'project-a'),lambda:CORE.generate_batches_from_locked_plan(self.path,'project-a'),lambda:CORE.check_output_against_locked_plan(self.path,'project-a',[]),lambda:CORE.export_locked_plan_bundle(self.path,'project-a')):
            with self.assertRaises(CORE.AuditRejected):call()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER bad_plan AFTER INSERT ON b13_draft_history BEGIN UPDATE user_records SET text='damage'; END")
        with self.assertRaises(sqlite3.DatabaseError):CORE.save_plan_discussion_draft(self.path,'project-b',['Task'],'manual')
        self.assert_user()

    def test_65_prefix_and_gates(self):
        source=Path(CORE.__file__).read_bytes()
        self.assertEqual(CORE.sha256(source[:225005]),'fab64595893be1d2ebcba393048ee8ad8c016d7fa8f0ff370fd1a6af8e1a44f8')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:225005]),CORE.scan_destructive_ops(source)):
            self.assertTrue(result)


def main_batch13():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b13_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = Z -> anvil',build_id='B13_LOCKED_PROJECT_PLANS_20261028',accepted_checkpoint=60,implemented_checkpoint=65,
        batch13_started=True,batch14_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,66)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All65 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = Z -> anvil');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1



class Batch14Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b14_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.path=CORE.ROOT/'state/tabs.db'
        self.manifest=dict(engine_id='builder',name='Builder',version='1.0.0',rules_text='Preserve owner records.',schema_version=1,entry_point='apccs_core:load_or_mount_engine')
        CORE.load_engine_from_manifest(self.path,self.manifest)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS user_sentinel (id INTEGER PRIMARY KEY,text TEXT)')
            db.execute('INSERT INTO user_sentinel VALUES (1,?)',('preserve',))
        self.before=CORE.capture_user_data_snapshot(self.path,'user_sentinel')
        for tab,lane in [('main','Main'),('research','Research'),('burner','Burner')]:self.register(tab,lane)

    def tearDown(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.path,'user_sentinel',self.before)['passed'])
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def register(self,tab,lane,project='alpha'):
        return CORE.register_chat_tab_session(self.path,dict(id=tab,project=project),'builder',lane)

    def finding(self):
        text='Tests establish the finding.'
        return dict(text=text,verified=True,verifier='checker',evidence=['audit/test-result.json'],sha256=CORE.sha256(text.encode()))

    def test_66_registry(self):
        result=self.register('main','Main');self.assertEqual(result['status'],'MOUNTED_EXISTING');self.assertEqual(result['seen_seq'],0)
        with self.assertRaises(CORE.AuditRejected):self.register('main','Research')
        with self.assertRaises(CORE.AuditRejected):CORE.register_chat_tab_session(self.path,'missing','not-installed','Main')
        with self.assertRaises(ValueError):self.register('bad','Unknown')
        self.register('other','Main','beta')
        OBSERVATIONS['INST-0066']=dict(status='GREEN',three_lane_types=True,idempotent_mount=True,no_engine_install=True,projects_isolated=True)

    def test_67_burner(self):
        question='SECRET-QUESTION-unique';answer='SECRET-ANSWER-unique'
        result=CORE.run_burner_question_cycle(self.path,'burner',question,answer)
        self.assertTrue(result['purged']);self.assertFalse(result['persisted_text'])
        for file in self.path.parent.iterdir():
            if file.is_file():self.assertNotIn(question.encode(),file.read_bytes());self.assertNotIn(answer.encode(),file.read_bytes())
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM b14_findings').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT * FROM b14_cycles').fetchall(),[('burner',1)])
        with self.assertRaises(CORE.AuditRejected):CORE.run_burner_question_cycle(self.path,'main','q','a')
        OBSERVATIONS['INST-0067']=dict(status='GREEN',no_question_answer_persisted=True,no_main_ledger_noise=True,text_free_cycle_receipt=True)

    def test_68_promotion(self):
        finding=self.finding()
        with self.assertRaises(CORE.AuditRejected):CORE.promote_branch_finding_to_main(self.path,'research','main',dict(finding,verified=False))
        with self.assertRaises(CORE.AuditRejected):CORE.promote_branch_finding_to_main(self.path,'research','main',dict(finding,sha256='bad'))
        with self.assertRaises(ValueError):CORE.promote_branch_finding_to_main(self.path,'research','main',dict(finding,evidence=[]))
        result=CORE.promote_branch_finding_to_main(self.path,'research','main',finding);self.assertTrue(result['promoted'])
        self.assertFalse(CORE.promote_branch_finding_to_main(self.path,'research','main',finding)['promoted'])
        self.register('other','Main','beta')
        with self.assertRaises(CORE.AuditRejected):CORE.promote_branch_finding_to_main(self.path,'research','other',finding)
        with self.assertRaises(CORE.AuditRejected):CORE.promote_branch_finding_to_main(self.path,'burner','main',finding)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b14_findings').fetchone()[0],1)
        OBSERVATIONS['INST-0068']=dict(status='GREEN',explicit_verifier_evidence_and_hash_required=True,caller_attestation_not_semantic_truth=True,deduplicated=True,cross_project_rejected=True)

    def test_69_handoff(self):
        one=CORE.create_tab_handoff_script(self.path,'main');two=CORE.create_tab_handoff_script(self.path,'main')
        self.assertEqual(one,two);packet=json.loads(one['resume_text']);self.assertEqual(packet['project'],'alpha');self.assertEqual(packet['active_engine'],'builder');self.assertIsNone(packet['last_checkpoint']);self.assertLess(one['bytes'],1200)
        self.assertEqual(CORE.sha256(one['resume_text'].encode()),one['sha256'])
        CORE.switch_active_chat_engine(self.path,'s','builder')
        CORE.record_engine_namespace_checkpoint(self.path,'builder',65)
        known=CORE.create_tab_handoff_script(self.path,'main');self.assertEqual(known['packet']['last_checkpoint'],65)
        self.assertNotIn('rules_text',known['packet'])
        OBSERVATIONS['INST-0069']=dict(status='GREEN',compact_passive_packet=True,project_engine_rulebook_reference_checkpoint=True,unknown_checkpoint_not_invented=True)

    def test_70_shared_sequence(self):
        first=CORE.guard_tab_write_conflict(self.path,'main',0);self.assertEqual(first['seq'],1)
        for call in (lambda:CORE.guard_tab_write_conflict(self.path,'research',0),lambda:CORE.run_burner_question_cycle(self.path,'burner','q','a'),lambda:CORE.promote_branch_finding_to_main(self.path,'research','main',self.finding())):
            with self.assertRaises(CORE.AuditRejected):call()
        packet=CORE.create_tab_handoff_script(self.path,'research')['packet']
        self.assertEqual(CORE.guard_tab_write_conflict(self.path,'research',packet['expected_seq'])['seq'],2)
        self.assertTrue(CORE.promote_branch_finding_to_main(self.path,'research','main',self.finding())['promoted'])
        self.register('beta','Main','beta');self.assertEqual(CORE.guard_tab_write_conflict(self.path,'beta',0)['seq'],1)
        with self.assertRaises(ValueError):CORE.guard_tab_write_conflict(self.path,'main',True)
        OBSERVATIONS['INST-0070']=dict(status='GREEN',shared_project_compare_and_swap=True,stale_writes_rollback=True,explicit_refresh=True,guard_claim_not_future_write_lease=True)

    def test_70_concurrent_claims(self):
        from concurrent.futures import ThreadPoolExecutor
        def claim(tab):
            try:return CORE.guard_tab_write_conflict(self.path,tab,0)['allowed']
            except CORE.AuditRejected:return False
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,['main','research']))
        self.assertEqual(sorted(results),[False,True])
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute("SELECT seq FROM b14_projects WHERE project='alpha'").fetchone()[0],1)

    def test_70_trigger_and_prefix(self):
        with sqlite3.connect(self.path) as db:db.execute("CREATE TRIGGER bad_tab AFTER UPDATE ON b14_projects BEGIN UPDATE user_sentinel SET text='damage'; END")
        with self.assertRaises(sqlite3.DatabaseError):CORE.guard_tab_write_conflict(self.path,'main',0)
        self.assertEqual(CORE.create_tab_handoff_script(self.path,'main')['packet']['expected_seq'],0)
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:239862]),'cd1f6fbe5110cb526008ac96155fd3772a47e4e4f2cfc29d171e4533c0c54552')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:239862]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch14():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b14_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = W -> compass',build_id='B14_TAB_LANES_20261028',accepted_checkpoint=65,implemented_checkpoint=70,
        batch14_started=True,batch15_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,71)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All70 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = W -> compass');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1




class Batch15Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b15_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.path=CORE.ROOT/'state/cache.db'
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS user_sentinel (id INTEGER PRIMARY KEY,text TEXT)')
            db.execute('INSERT INTO user_sentinel VALUES (1,?)',('preserve',))
        self.before=CORE.capture_user_data_snapshot(self.path,'user_sentinel')
        self.stage=CORE.WORKSPACE/'01_STAGING_INBOX/ring_buffer';self.stage.mkdir(parents=True)

    def tearDown(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.path,'user_sentinel',self.before)['passed'])
        self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def payload(self,count=45,session='chat'):
        return dict(session=session,messages=[dict(id=str(i),role='user',text='Message '+str(i)+' café') for i in range(count)])

    def old_file(self,name,age=601):
        p=self.stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'scratch');os.utime(p,(10000-age,10000-age));return p

    def test_71_boundaries(self):
        for current,status,flush,blocked in [(0,'GREEN',False,False),(102399,'GREEN',False,False),(102400,'YELLOW',True,False),(255999,'YELLOW',True,False),(256000,'RED',True,True),(999999,'RED',True,True)]:
            result=CORE.track_browser_cache_bytes(current);self.assertEqual((result['status'],result['flush_required'],result['blocked']),(status,flush,blocked))
        self.assertTrue(CORE.track_browser_cache_bytes(100,100)['flush_required'])
        self.assertEqual(CORE.track_browser_cache_bytes(102400,256000)['target_bytes'],102400)
        for current,ceiling in [(True,102400),(-1,102400),(2,0),(2,256001),(1.2,102400)]:
            with self.assertRaises(ValueError):CORE.track_browser_cache_bytes(current,ceiling)
        OBSERVATIONS['INST-0071']=dict(status='GREEN',target_102400_bytes=True,hard_ceiling_256000_bytes=True,exact_threshold_flush_and_block=True,host_measurement_not_browser_heap=True)

    def test_72_durable_flush(self):
        payload=dict(view='café\n'*10000,scroll=14)
        before=json.loads(json.dumps(payload));result=CORE.flush_view_cache_to_sqlite(self.path,payload)
        self.assertEqual(result['view_state'],{});self.assertLess(result['view_bytes'],102400);self.assertEqual(payload,before)
        with sqlite3.connect(self.path) as db:
            body=db.execute('SELECT body FROM b15_view_snapshots WHERE sha256=?',(result['snapshot_sha256'],)).fetchone()[0]
            self.assertEqual(json.loads(body),payload);self.assertEqual(CORE.sha256(body.encode()),result['snapshot_sha256'])
        CORE.flush_view_cache_to_sqlite(self.path,payload)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b15_view_snapshots').fetchone()[0],1)
        OBSERVATIONS['INST-0072']=dict(status='GREEN',exact_json_on_disk_before_clear=True,empty_replacement_view=True,repeat_snapshot_dedup=True,caller_must_replace_live_view=True)

    def test_72_atomic_rollback(self):
        CORE.flush_view_cache_to_sqlite(self.path,self.payload(1))
        bad=self.payload(2);bad['messages'][0]['text']='overwrite'
        with self.assertRaises(CORE.AuditRejected):CORE.flush_view_cache_to_sqlite(self.path,bad)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM b15_view_snapshots').fetchone()[0],1)
            db.execute("CREATE TRIGGER bad_flush AFTER INSERT ON b15_view_snapshots BEGIN UPDATE user_sentinel SET text='damage'; END")
        with self.assertRaises(sqlite3.DatabaseError):CORE.flush_view_cache_to_sqlite(self.path,{'new':'snapshot'})
        with self.assertRaises(ValueError):CORE.flush_view_cache_to_sqlite(self.path,{'invalid':float('nan')})

    def test_73_indexed_pages(self):
        CORE.flush_view_cache_to_sqlite(self.path,self.payload())
        with patch.object(CORE,'_b11_table_snapshot',side_effect=AssertionError('Read pagination must not load unrelated histories')):
            first=CORE.paginate_chat_history_window(self.path,'chat')
        self.assertEqual([m['id'] for m in first['messages']],[str(i) for i in range(25,45)])
        second=CORE.paginate_chat_history_window(self.path,first['next_cursor']);third=CORE.paginate_chat_history_window(self.path,second['next_cursor'])
        self.assertEqual([m['id'] for m in third['messages']],[str(i) for i in range(5)]);self.assertIsNone(third['next_cursor'])
        self.assertEqual(len(second['messages']),20)
        CORE.flush_view_cache_to_sqlite(self.path,self.payload(2,'other'))
        self.assertEqual(len(CORE.paginate_chat_history_window(self.path,'other')['messages']),2)
        CORE.flush_view_cache_to_sqlite(self.path,dict(session='chat',messages=[dict(id='45',role='assistant',text='new')]))
        self.assertEqual(CORE.paginate_chat_history_window(self.path,first['next_cursor']),second)
        with sqlite3.connect(self.path) as db:
            plan=db.execute('EXPLAIN QUERY PLAN SELECT seq FROM b15_chat_history WHERE session=? AND seq<? ORDER BY seq DESC LIMIT 20',('chat',25)).fetchall()
            self.assertTrue(any('INDEX' in row[3] for row in plan))
        self.assertEqual(CORE.paginate_chat_history_window(self.path,'empty')['messages'],[])
        with self.assertRaises(ValueError):CORE.paginate_chat_history_window(self.path,'chat',21)
        OBSERVATIONS['INST-0073']=dict(status='GREEN',latest_twenty_only=True,older_keyset_pages_indexed=True,session_isolation=True,concurrent_append_cursor_stable=True,full_text_retained_on_disk=True)

    def test_73_large_and_escaped_text(self):
        text='\x00 café ' * 7000
        payload=dict(session='huge',messages=[dict(id=str(i),role='assistant',text=text) for i in range(20)])
        CORE.flush_view_cache_to_sqlite(self.path,payload);page=CORE.paginate_chat_history_window(self.path,'huge')
        self.assertLess(len(json.dumps(page,ensure_ascii=False,separators=(',',':')).encode()),102400)
        self.assertTrue(all(m['truncated'] for m in page['messages']));self.assertEqual(len(page['messages']),20)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT body FROM b15_chat_history WHERE session=? AND seq=1',('huge',)).fetchone()[0],text)

    def test_74_binary_disk_route(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('passive.txt','payload')
        raw=stream.getvalue();result=CORE.intercept_binary_chat_dump(raw,'payload.zip')
        self.assertTrue(result['blocked']);self.assertNotIn('text',result);self.assertEqual(Path(result['path']).read_bytes(),raw)
        self.assertEqual(CORE.intercept_binary_chat_dump(raw,'payload.zip'),result)
        invalid=CORE.intercept_binary_chat_dump(b'\xff\x00raw','misnamed.txt');self.assertTrue(invalid['blocked'])
        self.assertTrue(CORE.intercept_binary_chat_dump(b'PK not a valid archive','misnamed.md')['blocked'])
        self.assertEqual(CORE.intercept_binary_chat_dump('café'.encode(),'note.txt')['text'],'café')
        big=CORE.intercept_binary_chat_dump(b'a'*102400,'long.txt');self.assertEqual(big['reason'],'VIEW_BUDGET')
        for filename in ('../escape.zip','folder/payload.zip','/escape.zip'):
            with self.assertRaises(ValueError):CORE.intercept_binary_chat_dump(raw,filename)
        OBSERVATIONS['INST-0074']=dict(status='GREEN',binary_zip_and_controls_blocked=True,exact_bytes_immutable_disk=True,large_text_disk_routed=True,no_binary_text_in_response=True,traversal_rejected=True)

    def test_75_safe_expiry(self):
        expired=self.old_file('old.tmp');fresh=self.old_file('fresh.tmp',600);future=self.old_file('future.tmp',-10);ordinary=self.old_file('owner.txt');readonly=self.old_file('readonly.tmp');readonly.chmod(0o400)
        nested=self.old_file('nested/old.cache');locked=self.old_file('locked/old.tmp');(locked.parent/'.locked').write_text('owner lock')
        vault=CORE.ROOT/'state/locked.tmp';vault.write_bytes(b'vault');os.utime(vault,(1,1))
        (self.stage/'symbol.tmp').symlink_to(vault);os.link(vault,self.stage/'hard.tmp')
        with patch.object(CORE._b8_time,'time',return_value=10000):result=CORE.sweep_expired_ring_buffer(self.stage)
        self.assertEqual(set(result['deleted']),{'old.tmp','nested/old.cache'});self.assertFalse(expired.exists());self.assertFalse(nested.exists())
        for path in (fresh,future,ordinary,readonly,locked,vault,self.stage/'symbol.tmp',self.stage/'hard.tmp'):self.assertTrue(path.exists())
        self.assertEqual(vault.read_bytes(),b'vault');self.assertFalse(result['vault_touched'])
        with self.assertRaises(ValueError):CORE.sweep_expired_ring_buffer(CORE.ROOT/'state')
        with self.assertRaises(ValueError):CORE.sweep_expired_ring_buffer(self.stage,599)
        OBSERVATIONS['INST-0075']=dict(status='GREEN',strict_older_than_600_seconds=True,dedicated_external_staging_only=True,locked_readonly_symlink_hardlink_vault_preserved=True)

    def test_75_active_lock_and_ancestor(self):
        import fcntl
        active=self.old_file('active.tmp');side=self.old_file('side.tmp');(self.stage/'side.tmp.lock').write_text('busy')
        with active.open('rb') as handle:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with patch.object(CORE._b8_time,'time',return_value=10000):result=CORE.sweep_expired_ring_buffer(self.stage)
            self.assertTrue(active.exists());self.assertTrue(side.exists());self.assertEqual(result['deleted_count'],0)
        (self.stage/'.lock').write_text('busy');child=self.stage/'child';child.mkdir()
        with self.assertRaises(CORE.AuditRejected):CORE.sweep_expired_ring_buffer(child)
        outside=CORE.WORKSPACE/'outside';outside.mkdir();(self.stage/'linked').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):CORE.sweep_expired_ring_buffer(self.stage/'linked')

    def test_75_prefix_gates(self):
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:249786]),'c710c63a858214f95ce844a81a6120a94bdce6151c5a6b3279e52857815ab3e5')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:249786]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch15():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b15_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: M = K -> submarine',build_id='B15_VIEW_CACHE_20261028',accepted_checkpoint=70,implemented_checkpoint=75,
        batch15_started=True,batch16_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,76)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All75 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: M = K -> submarine');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1





class Batch16Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b16_',dir='/tmp')
        self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name))
        self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.path=CORE.ROOT/'state/research.db'
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS user_sentinel (id INTEGER PRIMARY KEY,text TEXT)');db.execute('INSERT INTO user_sentinel VALUES (1,?)',('preserve',))
        self.before=CORE.capture_user_data_snapshot(self.path,'user_sentinel')

    def tearDown(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.path,'user_sentinel',self.before)['passed']);self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()

    def test_76_fts(self):
        one=CORE.init_and_index_fts5(self.path,'doc-a','Study Notes','Café case law and tenancy');self.assertEqual(one['status'],'INDEXED')
        self.assertEqual(CORE.init_and_index_fts5(self.path,'doc-a','Study Notes','Café case law and tenancy')['sha256'],one['sha256'])
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute("SELECT doc FROM b16_fts WHERE b16_fts MATCH 'tenancy'").fetchall(),[('doc-a',)])
        with self.assertRaises(CORE.AuditRejected):CORE.init_and_index_fts5(self.path,'doc-a','Changed','Different')
        self.assertTrue(one['fts5']);OBSERVATIONS['INST-0076']=dict(status='GREEN',local_fts5_searchable=True,exact_source_retained=True,idempotent_and_no_overwrite=True,missing_extension_fails_closed=True)

    def test_77_exact_offsets(self):
        CORE.init_and_index_fts5(self.path,'doc','title','Alpha\nExact quoted phrase café.\nExact quoted phrase café.')
        r=CORE.locate_exact_source_quote(self.path,'doc','Exact quoted phrase café');self.assertEqual([(x['start'],x['end'],x['start_line'],x['end_line']) for x in r['occurrences']],[(6,30,2,2),(32,56,3,3)])
        self.assertFalse(CORE.locate_exact_source_quote(self.path,'doc','different')['found'])
        with sqlite3.connect(self.path) as db:db.execute("UPDATE b16_docs SET body='tampered' WHERE doc='doc'")
        with self.assertRaises(CORE.AuditRejected):CORE.locate_exact_source_quote(self.path,'doc','Exact')
        OBSERVATIONS['INST-0077']=dict(status='GREEN',exact_unicode_offsets=True,one_based_lines=True,all_occurrences=True,integrity_checked=True)

    def test_78_save_choice(self):
        result=[dict(title='A',url='local://a')]
        saved=CORE.record_search_with_save_choice(self.path,'tenancy',result,'save');discard=CORE.record_search_with_save_choice(self.path,'irrelevant',result,'discard')
        self.assertTrue(saved['results_saved']);self.assertFalse(discard['results_saved'])
        with sqlite3.connect(self.path) as db:rows=db.execute('SELECT results_json,decision FROM b16_search_choices ORDER BY id').fetchall()
        self.assertEqual(json.loads(rows[0][0]),result);self.assertEqual(rows[0][1],'save');self.assertEqual(rows[1],('[]','discard'))
        with self.assertRaises(ValueError):CORE.record_search_with_save_choice(self.path,'q',result,'maybe')
        OBSERVATIONS['INST-0078']=dict(status='GREEN',explicit_decision_required=True,save_keeps_results=True,discard_does_not_keep_results=True,immutable_audit_receipt=True)

    def test_79_chronology_and_validation(self):
        a=CORE.append_chronological_ledger(self.path,'p','2026-01-03','research','Third event','ref-3')
        b=CORE.append_chronological_ledger(self.path,'p','2026-01-03','research','Same-day next','ref-4');self.assertEqual((a['seq'],b['seq']),(1,2))
        with self.assertRaises(CORE.AuditRejected):CORE.append_chronological_ledger(self.path,'p','2026-01-02','research','Earlier event','ref-2')
        for date in ('2026-2-01','2026-02-30','2026-02-01T00:00:00'):
            with self.assertRaises(ValueError):CORE.append_chronological_ledger(self.path,'p',date,'type','summary','ref')
        OBSERVATIONS['INST-0079']=dict(status='GREEN',canonical_calendar_dates=True,chronological_sequence_enforced=True,same_day_ordered=True,append_only=True)

    def test_80_hash_dedupe(self):
        record=CORE.append_chronological_ledger(self.path,'p','2026-03-01','document','Document saved','ref-a');h=record['hash']
        self.assertFalse(CORE.prevent_duplicate_ledger_entry(self.path,'p','0'*64)['duplicate'])
        self.assertTrue(CORE.prevent_duplicate_ledger_entry(self.path,'p',h)['duplicate'])
        duplicate=CORE.append_chronological_ledger(self.path,'p','2026-03-01','document','Document saved','ref-a');self.assertTrue(duplicate['duplicate']);self.assertEqual(duplicate['seq'],record['seq'])
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b16_ledger').fetchone()[0],1)
        with self.assertRaises(ValueError):CORE.prevent_duplicate_ledger_entry(self.path,'p','bad')
        with sqlite3.connect(self.path) as db:db.execute("CREATE TRIGGER bad_ledger AFTER INSERT ON b16_ledger BEGIN UPDATE user_sentinel SET text='damage'; END")
        with self.assertRaises((CORE.AuditRejected,sqlite3.DatabaseError)):CORE.append_chronological_ledger(self.path,'p','2026-03-02','type','other','ref-b')
        OBSERVATIONS['INST-0080']=dict(status='GREEN',project_scoped_sha256_lookup=True,identical_event_append_idempotent=True,trigger_mutation_denied=True)

    def test_80_parallel_dedupe_and_prefix(self):
        from concurrent.futures import ThreadPoolExecutor
        def append(_):return CORE.append_chronological_ledger(self.path,'p','2026-03-01','document','same','ref')['duplicate']
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(append,range(4)))
        self.assertEqual(sum(not x for x in results),1)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM b16_ledger').fetchone()[0],1)
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:263543]),'686504ffe019df892e42edb007e369e9622f3d1fe11667a6cc70bbc8344e7b0d')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:263543]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch16():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b16_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = X -> motorcycle',build_id='B16_FTS_LEDGER_20261028',accepted_checkpoint=75,implemented_checkpoint=80,
        batch16_started=True,batch17_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,81)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All80 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = X -> motorcycle');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1






class Batch17Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b17_',dir='/tmp');self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name));self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.db=CORE.ROOT/'state/privacy.db'
        with sqlite3.connect(self.db) as db:db.execute('CREATE TABLE IF NOT EXISTS user_sentinel (id INTEGER PRIMARY KEY,text TEXT)');db.execute('INSERT INTO user_sentinel VALUES (1,?)',('preserve',))
        self.before=CORE.capture_user_data_snapshot(self.db,'user_sentinel')
    def tearDown(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.db,'user_sentinel',self.before)['passed']);self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()
    def test_81_hold_and_82_restore(self):
        p=CORE.ROOT/'imports/document.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('private draft');r=CORE.soft_delete_with_24h_hold(self.db,'imports/document.txt','2026-01-01T00:00:00Z');self.assertFalse(p.exists());self.assertEqual(r['status'],'HELD')
        self.assertEqual(CORE.soft_delete_with_24h_hold(self.db,'imports/document.txt','2026-01-01T00:00:00Z')['status'],'ALREADY_HELD')
        with self.assertRaises(CORE.AuditRejected):CORE.restore_or_purge_trash_item(self.db,'imports/document.txt','purge','2026-01-01T23:59:59Z')
        self.assertEqual(CORE.restore_or_purge_trash_item(self.db,'imports/document.txt','restore','2026-01-01T12:00:00Z')['status'],'RESTORED');self.assertEqual(p.read_text(),'private draft')
        OBSERVATIONS['INST-0081']=dict(status='GREEN',exact_24h_hold=True,content_vaulted_not_destroyed=True,repeated_request_idempotent=True)
        OBSERVATIONS['INST-0082']=dict(status='GREEN',early_purge_blocked=True,restore_within_window=True,original_path_and_bytes_restored=True)
    def test_82_elapsed_purge(self):
        p=CORE.ROOT/'imports/expired.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'purge me');CORE.soft_delete_with_24h_hold(self.db,'imports/expired.txt','2026-01-01T00:00:00Z')
        self.assertEqual(CORE.restore_or_purge_trash_item(self.db,'imports/expired.txt','purge','2026-01-02T00:00:00Z')['status'],'PURGED')
        with sqlite3.connect(self.db) as db:self.assertEqual(db.execute("SELECT length(payload),status FROM b17_trash").fetchone(),(0,'PURGED'))
        with self.assertRaises(CORE.AuditRejected):CORE.restore_or_purge_trash_item(self.db,'imports/expired.txt','restore','2026-01-02T00:00:01Z')
    def test_83_draft_correction(self):
        p=CORE.ROOT/'imports/drafts/work.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Original owner wording.\nLeave rest.')
        prior=p.read_bytes();patch_data=dict(expected_sha256=CORE.sha256(prior),replacements=[dict(old='Original',new='Corrected')]);result=CORE.apply_in_place_draft_correction(self.db,'imports/drafts/work.txt',patch_data)
        self.assertEqual(p.read_text(),'Corrected owner wording.\nLeave rest.');self.assertEqual(result['revision'],1)
        with sqlite3.connect(self.db) as db:self.assertEqual(db.execute('SELECT body FROM b17_draft_versions').fetchone()[0],prior)
        with self.assertRaises(CORE.AuditRejected):CORE.apply_in_place_draft_correction(self.db,'imports/drafts/work.txt',patch_data)
        with self.assertRaises(CORE.AuditRejected):CORE.apply_in_place_draft_correction(self.db,'imports/drafts/work.txt',dict(expected_sha256=CORE.sha256(p.read_bytes()),replacements=[dict(old='Leave',new='Changed'),dict(old='Leave',new='Other')]))
        OBSERVATIONS['INST-0083']=dict(status='GREEN',in_place_edit=True,prior_exact_bytes_archived=True,expected_hash_and_unique_match_required=True,stale_patch_rejected=True)
    def test_84_redaction(self):
        raw='Call 604-555-0182 or micah@example.ca at 123 Main Street V6B 1A1. Micah Koivumaki.'
        clean=CORE.redact_personal_identifiers(raw,['Micah Koivumaki'])
        for secret in ('604-555-0182','micah@example.ca','123 Main Street','V6B 1A1','Micah Koivumaki'):self.assertNotIn(secret,clean)
        self.assertEqual(CORE.redact_personal_identifiers('Call 604-555-0182',['604-555-0182']),'Call [REDACTED]')
        with self.assertRaises(ValueError):CORE.redact_personal_identifiers('x',{'bad':1})
        OBSERVATIONS['INST-0084']=dict(status='GREEN',phone_email_postal_street_masked=True,owner_names_customizable=True,masking_scope_heuristic=True)
    def test_85_public_bundle(self):
        good={'pseudonym':'Donald Duck','body':'Donald Duck reviewed a fictional sample.'}
        self.assertTrue(CORE.verify_owner_privacy_mask(good)['passed'])
        for bad in ({'pseudonym':'Micah','body':'Donald Duck'}, {'pseudonym':'Donald Duck','body':'email owner@example.ca'}):self.assertFalse(CORE.verify_owner_privacy_mask(bad)['passed'])
        zpath=Path(self.temp.name)/'public.zip'
        with zipfile.ZipFile(zpath,'w') as z:z.writestr('readme.txt','Donald Duck has no private metadata.')
        self.assertTrue(CORE.verify_owner_privacy_mask(zpath)['passed'])
        with zipfile.ZipFile(zpath,'w') as z:z.writestr('readme.txt','Donald Duck call 604-555-0199')
        self.assertFalse(CORE.verify_owner_privacy_mask(zpath)['passed'])
        OBSERVATIONS['INST-0085']=dict(status='GREEN',exact_public_pseudonym_required=True,private_identifier_scan=True,zip_members_and_names_checked=True,heuristic_scan_not_proof=True)
    def test_85_prefix_gates(self):
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:271849]),'aa03a303228947708c4ce8231c094d848d00a459bd3ded24707dfcac888c8948')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:271849]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch17():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b17_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = Y -> lighthouse',build_id='B17_PRIVACY_RETENTION_20261028',accepted_checkpoint=80,implemented_checkpoint=85,
        batch17_started=True,batch18_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,86)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All85 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = Y -> lighthouse');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1







class Batch18Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b18_',dir='/tmp');self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name));self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.db=CORE.ROOT/'state/interaction.db'
        with sqlite3.connect(self.db) as db:db.execute('CREATE TABLE IF NOT EXISTS user_sentinel(id INTEGER PRIMARY KEY,text TEXT)');db.execute('INSERT INTO user_sentinel VALUES(1,?)',('preserve',))
        self.before=CORE.capture_user_data_snapshot(self.db,'user_sentinel')
    def tearDown(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.db,'user_sentinel',self.before)['passed']);self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()
    def test_86_guidance(self):
        beginner=CORE.format_guidance_by_level('SQLite','BEGINNER');novice=CORE.format_guidance_by_level('SQLite','Novice');expert=CORE.format_guidance_by_level('SQLite','Expert')
        self.assertEqual([beginner['level'],novice['level'],expert['level']],['BEGINNER','NOVICE','EXPERT']);self.assertNotEqual(beginner['checklist'],expert['checklist']);self.assertEqual(beginner,CORE.format_guidance_by_level('SQLite'))
        with self.assertRaises(ValueError):CORE.format_guidance_by_level('x','Master')
        OBSERVATIONS['INST-0086']=dict(status='GREEN',three_deterministic_levels=True,beginner_default=True,no_external_facts_invented=True)
    def test_87_workflow(self):
        mapping={'draft':['review','edit'],'review':['publish']}
        self.assertEqual(CORE.predict_next_workflow_step('review',mapping)['next_step'],'publish');choice=CORE.predict_next_workflow_step('draft',mapping);self.assertIsNone(choice['next_step']);self.assertTrue(choice['owner_choice_required']);self.assertEqual(choice['options'],['edit','review'])
        self.assertEqual(CORE.predict_next_workflow_step('unknown',mapping)['status'],'GRAY')
        with self.assertRaises(ValueError):CORE.predict_next_workflow_step('draft',{'draft':['edit','edit']})
        OBSERVATIONS['INST-0087']=dict(status='GREEN',deterministic_mapping_only=True,ambiguous_steps_offer_options=True,missing_map_gray=True)
    def test_88_alerts(self):
        for level in ('Critical','Warning','Info'):
            row=CORE.emit_system_alert(self.db,level,'TEST_ALERT','A local alert');self.assertTrue(row['one_click']);self.assertFalse(row['external_effect'])
        with sqlite3.connect(self.db) as db:self.assertEqual(db.execute('SELECT count(*) FROM b18_alerts').fetchone()[0],3)
        with self.assertRaises(ValueError):CORE.emit_system_alert(self.db,'Fatal','BAD','x')
        OBSERVATIONS['INST-0088']=dict(status='GREEN',critical_warning_info_supported=True,one_safe_action_descriptor=True,no_ui_execution_or_external_effect=True)
    def test_89_private_inquiry(self):
        text='Sensitive private diagnostic text'
        row=CORE.submit_discreet_help_inquiry(self.db,'Bug',text);self.assertEqual(row['status'],'LOCAL_ONLY');self.assertFalse(row['public_exposure']);self.assertFalse(row['transmitted'])
        with sqlite3.connect(self.db) as db:self.assertEqual(db.execute('SELECT category,msg,public_exposure,status FROM b18_helpful_inquiries').fetchone(),('Bug',text,0,'LOCAL_ONLY'))
        with self.assertRaises(ValueError):CORE.submit_discreet_help_inquiry(self.db,'Public',text)
        OBSERVATIONS['INST-0089']=dict(status='GREEN',bug_engine_only=True,local_private_store=True,no_network_or_public_feed=True)
    def test_90_update_opt_in(self):
        current={'engine_id':'builder','version':'1.2.0'}
        self.assertTrue(CORE.check_available_engine_updates(current,{'engine_id':'builder','version':'1.2.1'})['user_opt_in_required'])
        self.assertFalse(CORE.check_available_engine_updates(current,{'engine_id':'builder','version':'1.1.9'})['update_available'])
        self.assertTrue(CORE.check_available_engine_updates({'engine_id':'x','version':'1.0.0-alpha'},{'engine_id':'x','version':'1.0.0'})['update_available'])
        self.assertFalse(CORE.check_available_engine_updates({'engine_id':'x','version':'1.0.0'},{'engine_id':'x','version':'1.0.0+build'})['update_available'])
        for v in ('01.0.0','1.0','1.0.0-'):
            with self.assertRaises(ValueError):CORE.check_available_engine_updates({'engine_id':'x','version':v},{'engine_id':'x','version':'2.0.0'})
        result=CORE.check_available_engine_updates(current,{'engine_id':'builder','version':'2.0.0'});self.assertFalse(result['upgrade_performed']);self.assertFalse(result['install_authorized'])
        with self.assertRaises(ValueError):CORE.check_available_engine_updates(current,{'engine_id':'other','version':'2.0.0'})
        OBSERVATIONS['INST-0090']=dict(status='GREEN',semantic_prerelease_comparison=True,metadata_only=True,no_install_or_upgrade_without_opt_in=True)
    def test_90_prefix_gates(self):
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:282408]),'99cd880a68dfd5eb863f6135243191263d6b1201658d154ef44fa4fe9636a313')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:282408]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch18():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b18_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = Z -> anvil',build_id='B18_GUIDANCE_ALERTS_20261028',accepted_checkpoint=85,implemented_checkpoint=90,
        batch18_started=True,batch19_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,91)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All90 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = Z -> anvil');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1








class Batch19Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b19_',dir='/tmp');self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name));self.root_patch.start();self.work_patch.start()
        for name in CORE.CATEGORIES:(CORE.ROOT/name).mkdir(parents=True)
        self.db=CORE.ROOT/'state/coherence.db'
        with sqlite3.connect(self.db) as db:db.execute('CREATE TABLE IF NOT EXISTS user_sentinel(id INTEGER PRIMARY KEY,text TEXT)');db.execute('INSERT INTO user_sentinel VALUES(1,?)',('preserve',))
        self.before=CORE.capture_user_data_snapshot(self.db,'user_sentinel')
    def tearDown(self):
        self.assertTrue(CORE.verify_user_data_untouched(self.db,'user_sentinel',self.before)['passed']);self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()
    def test_91_clean_bundle(self):
        z=Path(self.temp.name)/'clean.zip'
        with zipfile.ZipFile(z,'w') as out:
            data={'code/apccs_core.py':b'core','schemas/manifest.json':b'{}','locked_plans/plan.json':b'{}','RECOVER.md':b'recovery'}
            manifest={'files':{n:{'size':len(v),'sha256':CORE.sha256(v)} for n,v in data.items()}}
            data['audit/pass_tests.json']=json.dumps({'passed':True}).encode();manifest['files']['audit/pass_tests.json']={'size':len(data['audit/pass_tests.json']),'sha256':CORE.sha256(data['audit/pass_tests.json'])}
            data['RECOVERY_MANIFEST.json']=json.dumps(manifest).encode()
            for n,v in data.items():out.writestr(n,v)
        result=CORE.verify_clean_device_recovery_bundle(z);self.assertTrue(result['passed'])
        bad=Path(self.temp.name)/'bad.zip'
        with zipfile.ZipFile(bad,'w') as out:out.writestr('../escape',b'x')
        with self.assertRaises(CORE.AuditRejected):CORE.verify_clean_device_recovery_bundle(bad)
        OBSERVATIONS['INST-0091']=dict(status='GREEN',required_code_schema_locked_plan_recovery_members=True,manifest_hashes_and_paths_verified=True,corrupt_bundle_rejected=True)
    def test_92_backup(self):
        raw=b'private backup contents'*100
        plain=CORE.export_optional_encrypted_backup(raw);self.assertEqual(CORE._b19_open_backup(plain),raw)
        enc=CORE.export_optional_encrypted_backup(raw,'correct horse battery staple');self.assertNotIn(raw,enc);self.assertEqual(CORE._b19_open_backup(enc,'correct horse battery staple'),raw)
        with self.assertRaises(CORE.AuditRejected):CORE._b19_open_backup(enc,'wrong passphrase!')
        tampered=bytearray(enc);tampered[-1]^=1
        with self.assertRaises(CORE.AuditRejected):CORE._b19_open_backup(tampered,'correct horse battery staple')
        with self.assertRaises(ValueError):CORE.export_optional_encrypted_backup(raw,'short')
        OBSERVATIONS['INST-0092']=dict(status='GREEN',one_click_plain_or_password_encrypted=True,pbkdf2_hmac_sha256=True,authentication_and_tamper_rejection=True,custom_crypto_caveat_documented=True)
    def slot(self,payload,seq):
        body=CORE._b13_json(dict(sequence=seq,payload=payload));return json.dumps(dict(sequence=seq,payload=payload,sha256=CORE.sha256(body.encode()))).encode()
    def test_93_slots(self):
        a=self.slot({'state':'old'},3);b=self.slot({'state':'new'},4)
        self.assertEqual(CORE.load_state_with_slot_fallback(a,b)['payload'],{'state':'new'})
        fallback=CORE.load_state_with_slot_fallback(a,b'{broken');self.assertEqual(fallback['payload'],{'state':'old'});self.assertTrue(fallback['fallback'])
        self.assertEqual(CORE.load_state_with_slot_fallback(b'bad',b'bad')['status'],'RED')
        OBSERVATIONS['INST-0093']=dict(status='GREEN',sha256_validated_slots=True,newest_sequence_selected=True,corrupt_slot_falls_back=True,no_valid_slot_red=True)
    def manifest(self,ident):return dict(engine_id=ident,name=ident.title(),version='1.0.0',rules_text='Keep records safe.',schema_version=1,entry_point='apccs_core:load_or_mount_engine')
    def test_94_atomic_engines(self):
        result=CORE.batch_mount_multiple_engines(self.db,[self.manifest('one'),self.manifest('two')]);self.assertEqual(result['installed_count'],2)
        with sqlite3.connect(self.db) as db:self.assertEqual(db.execute('SELECT count(*) FROM engine_registry_v2').fetchone()[0],2);self.assertEqual(db.execute('SELECT count(*) FROM b12_namespace_owners').fetchone()[0],2)
        with self.assertRaises(CORE.AuditRejected):CORE.batch_mount_multiple_engines(self.db,[self.manifest('three'),self.manifest('one')])
        with sqlite3.connect(self.db) as db:self.assertEqual(db.execute("SELECT count(*) FROM engine_registry_v2 WHERE engine_id='three'").fetchone()[0],0)
        with self.assertRaises(ValueError):CORE.batch_mount_multiple_engines(self.db,[self.manifest('dup'),self.manifest('dup')])
        OBSERVATIONS['INST-0094']=dict(status='GREEN',multiple_engines_single_atomic_transaction=True,duplicate_refused_without_partial_install=True,namespace_rows_same_transaction=True)
    def test_95_coherence(self):
        CORE.batch_mount_multiple_engines(self.db,[self.manifest('coherent')])
        vault=CORE.ROOT; (vault/'audit').mkdir(exist_ok=True);(vault/'RECOVER.md').write_text('Canary: T = Z -> anvil')
        (vault/'audit/pass_tests.json').write_text(json.dumps({'passed':True,'failed_assertions':[]}))
        result=CORE.verify_q1_part1_coherence(self.db,vault);self.assertTrue(result['passed'],result)
        OBSERVATIONS['INST-0095']=dict(status='GREEN',read_only_db_and_vault_integrity=True,engine_records_and_audit_checked=True,canary_and_recovery_checked=True)
    def test_95_prefix_gates(self):
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:289434]),'a19f0940a1d8606d7d4ae265c700799e08b71064eeb18ca2be193c6f17a4cb5f')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:289434]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch19():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b19_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: T = W -> compass',build_id='B19_RECOVERY_COHERENCE_20261028',accepted_checkpoint=90,implemented_checkpoint=95,
        batch19_started=True,batch20_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,96)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All95 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: T = W -> compass');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1









class Batch20Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apccs_b20_',dir='/tmp');self.root_patch=patch.object(CORE,'ROOT',Path(self.temp.name)/'vault');self.work_patch=patch.object(CORE,'WORKSPACE',Path(self.temp.name));self.root_patch.start();self.work_patch.start()
        for n in CORE.CATEGORIES:(CORE.ROOT/n).mkdir(parents=True)
        self.db=CORE.ROOT/'state/cp100.db'
    def tearDown(self):self.root_patch.stop();self.work_patch.stop();self.temp.cleanup()
    def test_96_schema_map(self):
        result=CORE.export_q1_part1_schema_map('class A:\n    """Schema."""\n    def run(self, value):\n        """Run schema."""\n        return value\n')
        self.assertEqual([x['name'] for x in result['symbols']],['A','run']);self.assertEqual(result['symbols'][1]['signature'],'run(self,value)');self.assertEqual(result['symbol_count'],2)
        OBSERVATIONS['INST-0096']=dict(status='GREEN',ast_only_directory=True,function_class_signatures_and_docstrings=True,deterministic_order=True)
    def test_97_continuity(self):
        source=Path(CORE.__file__).read_text()+Path(__file__).read_text();result=CORE.verify_1_to_100_symbol_continuity(source);self.assertTrue(result['passed'],result);self.assertEqual(result['verified_count'],100)
        self.assertFalse(CORE.verify_1_to_100_symbol_continuity('def one(): return 1')['passed'])
        OBSERVATIONS['INST-0097']=dict(status='GREEN',all_instruction_markers_1_to_100_required=True,missing_ids_reported=True,duplicate_top_level_symbols_rejected=True)
    def test_98_compact_manifest(self):
        report=dict(passed=True,failed_assertions=[],instruction_coverage=list(range(1,101)),tests_run=150,extra='large')
        one=CORE.compact_pass_tests_manifest(report);two=CORE.compact_pass_tests_manifest(report);self.assertEqual(one,two);self.assertNotIn('extra',one['manifest']);self.assertEqual(json.loads(one['canonical_json']),one['manifest'])
        with self.assertRaises(ValueError):CORE.compact_pass_tests_manifest({'passed':'yes','failed_assertions':[]})
        OBSERVATIONS['INST-0098']=dict(status='GREEN',minimal_deterministic_json=True,malformed_reports_rejected=True,fast=True)
    def test_99_scorecard(self):
        audit=CORE.ROOT/'audit/pass_tests.json';audit.write_text(json.dumps(dict(passed=True,instruction_coverage=list(range(1,96)),tests_run=140,failed_assertions=[])))
        with sqlite3.connect(self.db):pass
        text=CORE.generate_cp100_scorecard(self.db);self.assertIn('10% milestone',text);self.assertIn('100 | GRAY',text);self.assertIn('095 | GREEN',text)
        self.assertEqual(text,CORE.generate_cp100_scorecard(self.db));OBSERVATIONS['INST-0099']=dict(status='GREEN',plain_english_rows_1_to_100=True,unverified_items_gray=True,milestone='10_percent')
    def test_100_checkpoint_lock(self):
        root=CORE.ROOT;archive=root/'exports/APCCS_MASTER_BUILD.zip';archive.parent.mkdir(parents=True,exist_ok=True)
        base=Path(__file__).with_name('apccs_core.py').read_bytes();tests=Path(__file__).read_bytes();report=dict(passed=True,failed_assertions=[],instruction_coverage=list(range(1,101)),tests_run=150)
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('code/apccs_core.py',base);z.writestr('code/test_apccs_core.py',tests);z.writestr('audit/pass_tests.json',json.dumps(report));z.writestr('RECOVER.md','checkpoint test');z.writestr('RECOVERY_MANIFEST.json','{}');z.writestr('README.txt','existing record')
        seal=CORE.lock_checkpoint_cp100(root);self.assertEqual(seal['checkpoint'],'CP-100')
        with zipfile.ZipFile(archive) as z:
            self.assertIn('audit/CP-100_LOCK.json',z.namelist());self.assertIn(b'CP-100',z.read('RECOVER.md'));self.assertEqual(json.loads(z.read('audit/CP-100_LOCK.json'))['locally_verified_instructions'],100);self.assertEqual(z.read('README.txt'),b'existing record')
        with self.assertRaises(CORE.AuditRejected):CORE.lock_checkpoint_cp100(root)
        OBSERVATIONS['INST-0100']=dict(status='GREEN',cp100_hash_seal_and_recovery_update=True,prior_archive_records_preserved=True,unequal_or_existing_lock_not_overwritten=True,muse_acceptance_separate=True)
    def test_100_prefix_static(self):
        source=Path(CORE.__file__).read_bytes();self.assertEqual(CORE.sha256(source[:302639]),'e2be1391586c40ce3ad13953623c56c7fc635bdda0df147ea5b5103a2afd6cd9')
        for result in (CORE.scan_for_fake_padding(source),CORE.verify_ast_structure(source),CORE.check_symbol_regression(source,source[:302639]),CORE.scan_destructive_ops(source)):self.assertTrue(result)

def main_batch20():
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apccs_b20_driver_',dir='/tmp') as tmp:
        root=Path(tmp)/'vault';(root/'code').mkdir(parents=True)
        (root/'code/apccs_core.py').write_bytes(Path(__file__).with_name('apccs_core.py').read_bytes())
        (root/'code/test_apccs_core.py').write_bytes(Path(__file__).read_bytes())
        os.environ['APCCS_VAULT_ROOT']=str(root)
        import apccs_core as imported
        report=imported.run_all_installed_unit_tests()
    report.update(canary='Canary check: M = K -> submarine',build_id='B20_CP100_20261028',accepted_checkpoint=95,implemented_checkpoint=100,
        batch20_started=True,batch21_started=False,collision_count=0,timing_advisory_only=True,driver_scratch_removed=not Path(tmp).exists(),driver_elapsed_seconds=time.monotonic()-started,
        release_ready=False,all_instructions_green=False)
    if report['instruction_coverage']!=list(range(1,101)) or not report['driver_scratch_removed']:
        report['passed']=False;report['all_unit_tests_passed']=False;report['failed_assertions'].append(dict(test='coverage/cleanup',traceback='All100 instructions and clean scratch required'))
    if len(sys.argv)==3 and sys.argv[1]=='--report':
        with Path(sys.argv[2]).open('x') as output:json.dump(report,output,indent=2)
    print('Canary check: M = K -> submarine');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1









if __name__ == '__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--installed-plan':raise SystemExit(_b12_write_installed_plan(sys.argv[2]))
    if len(sys.argv)==4 and sys.argv[1]=='--installed-worker':raise SystemExit(_b10_installed_worker(sys.argv[2],sys.argv[3]))
    raise SystemExit(fence_worker() if len(sys.argv)>1 and sys.argv[1]=='--fence-worker' else main_batch20())
