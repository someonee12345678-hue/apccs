"""CP-100 verified local control panel bridge for APCCS Part 2."""

from __future__ import annotations

import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


CP100_CORE_SHA256 = "276d635f9e54d4177fd18ba0e39d360f6f6663772b1127a636a702ba89cc7603"
_IMPORT_LOCK = threading.RLock()
_CORE_CACHE = {}
_MAX_BODY_BYTES = 1_048_576


class ControlPanelError(ValueError):
    """Expected local API request or environment error."""


def _core_path(core_path=None):
    path = Path(core_path) if core_path is not None else Path(__file__).with_name("apccs_core.py")
    return path.resolve(strict=True)


def _load_verified_core(core_path=None, vault_dir=None):
    path = _core_path(core_path)
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != CP100_CORE_SHA256:
        raise ControlPanelError("Frozen CP-100 core SHA-256 mismatch")
    root = Path(vault_dir or os.environ.get("APCCS_VAULT_ROOT", "/mnt/data/apccs_central_vault")).absolute()
    key = (str(path), str(root))
    with _IMPORT_LOCK:
        cached = _CORE_CACHE.get(key)
        if cached is not None:
            return cached
        name_digest = hashlib.sha256((str(path) + "\0" + str(root)).encode()).hexdigest()[:20]
        module_name = "_apccs_cp100_" + name_digest
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ControlPanelError("Could not create CP-100 module loader")
        module = importlib.util.module_from_spec(spec)
        prior_root = os.environ.get("APCCS_VAULT_ROOT")
        os.environ["APCCS_VAULT_ROOT"] = str(root)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(module_name, None)
            raise
        finally:
            if prior_root is None:
                os.environ.pop("APCCS_VAULT_ROOT", None)
            else:
                os.environ["APCCS_VAULT_ROOT"] = prior_root
        _CORE_CACHE[key] = module
        return module


def verify_and_import_cp100_core(core_path=None, vault_dir=None):
    """Verify the exact CP-100 SHA-256 before importing its frozen APIs."""
    module = _load_verified_core(core_path, vault_dir)
    return {"passed": True, "sha256": CP100_CORE_SHA256, "module": module}


def _json_body(body):
    if body is None or body == b"" or body == "":
        return {}
    if isinstance(body, dict):
        return body
    if isinstance(body, str):
        raw = body.encode("utf-8")
    elif isinstance(body, (bytes, bytearray, memoryview)):
        raw = bytes(body)
    else:
        raise ControlPanelError("Request body must be JSON bytes, text, or an object")
    if len(raw) > _MAX_BODY_BYTES:
        raise ControlPanelError("Request body exceeds the 1 MiB limit")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ControlPanelError("Request body must contain valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ControlPanelError("Request JSON must be an object")
    return value


def _vault_root(vault_dir):
    if not isinstance(vault_dir, (str, os.PathLike)):
        raise ControlPanelError("A local vault directory is required")
    root = Path(vault_dir).absolute()
    if root.is_symlink() or root.resolve() != root:
        raise ControlPanelError("Vault directory path cannot contain symlinks")
    return root


def _database_path(root):
    return "state/prompt_engine.db"


def _json_result(http_status, payload):
    return {"http_status": http_status, "body": payload}


def handle_control_panel_api(method, path, body, vault):
    """Route local JSON API requests through the verified CP-100 core."""
    if not isinstance(method, str) or not isinstance(path, str):
        return _json_result(400, {"error": "Method and path must be text"})
    method = method.upper()
    route = urlsplit(path).path
    if not route.startswith("/api/"):
        return _json_result(404, {"error": "Unknown API route"})
    allowed_methods = {"/api/status": {"GET"}, "/api/engines": {"GET"},
                       "/api/switch": {"POST"}, "/api/plan": {"POST"},
                       "/api/search": {"POST"}}
    if route not in allowed_methods:
        return _json_result(404, {"error": "Unknown API route"})
    if method not in allowed_methods[route]:
        return _json_result(405, {"error": "Method not allowed", "allow": sorted(allowed_methods[route])})
    try:
        root = _vault_root(vault)
        request = _json_body(body)
        loaded = verify_and_import_cp100_core(vault_dir=root)
        core = loaded["module"]
        db_path = _database_path(root)
        absolute_db = root / db_path

        if route == "/api/status":
            return _json_result(200, {
                "status": "READY", "checkpoint": "CP-100",
                "core_sha256": loaded["sha256"], "vault": str(root),
                "database_exists": absolute_db.is_file(),
                "api": ["/api/status", "/api/engines", "/api/switch", "/api/plan", "/api/search"],
            })

        if route == "/api/engines":
            engines = []
            if absolute_db.is_file():
                uri = absolute_db.resolve().as_uri() + "?mode=ro"
                with sqlite3.connect(uri, uri=True) as db:
                    exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engine_registry_v2'").fetchone()
                    if exists:
                        engines = [
                            {"engine_id": row[0], "name": row[1], "version": row[2], "state": row[3]}
                            for row in db.execute("SELECT engine_id,name,version,state FROM engine_registry_v2 ORDER BY engine_id")
                        ]
            return _json_result(200, {"engines": engines})

        if route == "/api/switch":
            session_id = request.get("session_id", "control-panel")
            engine_id = request.get("engine_id")
            if not isinstance(session_id, str) or not session_id or not isinstance(engine_id, str) or not engine_id:
                raise ControlPanelError("session_id and engine_id are required")
            switched = core.switch_active_chat_engine(db_path, session_id, engine_id)
            branch = request.get("branch", "Main")
            tab = request.get("tab", session_id)
            tab_state = core.register_chat_tab_session(db_path, tab, engine_id, branch)
            return _json_result(200, {"switch": switched, "tab": tab_state})

        if route == "/api/plan":
            project = request.get("project", "control-panel")
            action = request.get("action", "draft_and_lock")
            if not isinstance(project, str) or not project:
                raise ControlPanelError("project is required")
            if action == "draft":
                result = core.save_plan_discussion_draft(db_path, project, request.get("notes"), request.get("style", "Owner directed"))
            elif action == "lock":
                result = core.lock_project_plan(db_path, project)
            elif action == "draft_and_lock":
                core.save_plan_discussion_draft(db_path, project, request.get("notes"), request.get("style", "Owner directed"))
                result = core.lock_project_plan(db_path, project)
            else:
                raise ControlPanelError("action must be draft, lock, or draft_and_lock")
            return _json_result(200, {"plan": result})

        query = request.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > 1000:
            raise ControlPanelError("A nonempty query of at most 1,000 characters is required")
        if "body" in request:
            doc = request.get("doc", "control-panel-search")
            title = request.get("title", doc)
            if not all(isinstance(item, str) and item for item in (doc, title)) or not isinstance(request["body"], str):
                raise ControlPanelError("doc, title, and body must be text")
            core.init_and_index_fts5(db_path, doc, title, request["body"])
        results = []
        if absolute_db.is_file():
            uri = absolute_db.resolve().as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True) as db:
                table = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='b16_fts'").fetchone()
                if table:
                    try:
                        results = [
                            {"doc": row[0], "title": row[1], "snippet": row[2]}
                            for row in db.execute(
                                "SELECT doc,title,snippet(b16_fts,2,'<mark>','</mark>','…',12) "
                                "FROM b16_fts WHERE b16_fts MATCH ? ORDER BY rank LIMIT 20", (query,)
                            )
                        ]
                    except sqlite3.OperationalError as error:
                        raise ControlPanelError("Invalid or unavailable FTS5 search") from error
        decision = request.get("decision", "discard")
        if decision not in ("save", "discard"):
            raise ControlPanelError("decision must be save or discard")
        choice = core.record_search_with_save_choice(db_path, query, results, decision)
        return _json_result(200, {"query": query, "results": results, "choice": choice})
    except (ControlPanelError, ValueError, TypeError, OSError, sqlite3.Error) as error:
        return _json_result(400, {"error": str(error)})


def generate_try_out_control_panel_html(output_path):
    """Write a standalone control panel that uses only same-origin /api calls."""
    if not isinstance(output_path, (str, os.PathLike)):
        raise ControlPanelError("output_path must be a local path")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    html = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>APCCS Local Control Panel</title>
<style>
body{font:16px system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#17202a;background:#f5f7fa}
main{background:#fff;border:1px solid #d9e0e8;border-radius:12px;padding:1.25rem;margin:1rem 0}label{display:block;margin:.75rem 0 .25rem}
input,select,textarea,button{font:inherit;padding:.55rem;border:1px solid #aab6c3;border-radius:6px;max-width:100%}
textarea{width:98%;min-height:5rem}button{cursor:pointer;background:#164e63;color:white;margin:.5rem .25rem 0 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf2f7;padding:1rem;border-radius:8px}.row{display:flex;gap:1rem;flex-wrap:wrap}.row>section{flex:1;min-width:260px}
</style></head><body><h1>APCCS Local Control Panel</h1>
<p>This panel sends requests only to the local server that serves this page.</p><pre id="status">Checking CP-100…</pre>
<main><h2>Engine switch and chat lane</h2><label for="engine">Installed engine ID</label><select id="engine"></select>
<label for="branch">Chat tab</label><select id="branch"><option>Main</option><option>Research</option><option>Burner</option></select>
<button id="switch">Mount engine and tab</button></main>
<main><h2>Plan draft and lock</h2><label for="project">Project</label><input id="project" value="control-panel">
<label for="notes">Explicit plan items (one per line)</label><textarea id="notes">Review the local control panel</textarea>
<button id="lock">Save draft and lock plan</button></main>
<main><h2>FTS5 local search</h2><label for="doc">Document ID</label><input id="doc" value="control-panel-search">
<label for="body">Text to index (optional on later searches)</label><textarea id="body">Local APCCS search sample</textarea>
<label for="query">Search query</label><input id="query" value="local">
<button id="search">Search local index</button></main><pre id="result">Ready.</pre>
<script>
const show=(value)=>{document.getElementById('result').textContent=JSON.stringify(value,null,2)};
async function api(path,body){const options=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};const response=await fetch(path,options);const data=await response.json();if(!response.ok)throw new Error(data.error||response.statusText);return data;}
async function refresh(){try{const status=await api('/api/status');document.getElementById('status').textContent=JSON.stringify(status,null,2);const data=await api('/api/engines');const select=document.getElementById('engine');select.replaceChildren();for(const engine of data.engines){const option=document.createElement('option');option.value=engine.engine_id;option.textContent=engine.name+' ('+engine.engine_id+')';select.append(option);}if(!data.engines.length)select.innerHTML='<option value="">No installed engines</option>';show(data);}catch(error){show({error:error.message});}}
document.getElementById('switch').onclick=async()=>{try{show(await api('/api/switch',{engine_id:document.getElementById('engine').value,branch:document.getElementById('branch').value,session_id:'control-panel',tab:'control-panel'}));}catch(error){show({error:error.message});}};
document.getElementById('lock').onclick=async()=>{try{const notes=document.getElementById('notes').value.split(/\r?\n/).map((text,index)=>({id:'item-'+(index+1),text})).filter(item=>item.text.trim());show(await api('/api/plan',{action:'draft_and_lock',project:document.getElementById('project').value,notes:{instructions:notes},style:'Owner directed'}));}catch(error){show({error:error.message});}};
document.getElementById('search').onclick=async()=>{try{const body=document.getElementById('body').value;const request={query:document.getElementById('query').value,doc:document.getElementById('doc').value};if(body)request.body=body;show(await api('/api/search',request));}catch(error){show({error:error.message});}};
refresh();
</script></body></html>'''
    target.write_text(html, encoding="utf-8")
    return {"path": str(target), "bytes": target.stat().st_size, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def create_local_control_server(host="127.0.0.1", port=8501, vault_dir=None, html_path=None):
    """Create a standard-library HTTP server bound to an IPv4/IPv6 loopback host."""
    try:
        is_loopback = host.lower() == "localhost" or ipaddress.ip_address(host).is_loopback
    except (AttributeError, ValueError):
        is_loopback = False
    if not is_loopback:
        raise ControlPanelError("Control server must bind to localhost")
    root = _vault_root(vault_dir or os.environ.get("APCCS_VAULT_ROOT", Path(__file__).resolve().parents[1]))
    page = Path(html_path) if html_path is not None else Path(__file__).resolve().parents[1] / "START_OUR_OWN_SYSTEM.html"

    class Handler(BaseHTTPRequestHandler):
        server_version = "APCCSLocal/1.0"

        def _send(self, status, content_type, data):
            raw = data.encode("utf-8") if isinstance(data, str) else data
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            route = urlsplit(self.path).path
            if route in ("/", "/index.html", "/START_OUR_OWN_SYSTEM.html"):
                if page.is_file():
                    self._send(200, "text/html; charset=utf-8", page.read_text(encoding="utf-8"))
                else:
                    generated = generate_try_out_control_panel_html(page)
                    self._send(200, "text/html; charset=utf-8", page.read_text(encoding="utf-8"))
                return
            if route.startswith("/api/"):
                result = handle_control_panel_api("GET", self.path, b"", root)
                self._send(result["http_status"], "application/json; charset=utf-8", json.dumps(result["body"]))
                return
            self._send(404, "application/json; charset=utf-8", json.dumps({"error": "Not found"}))

        def do_POST(self):
            length_text = self.headers.get("Content-Length", "0")
            try:
                length = int(length_text)
            except ValueError:
                length = -1
            if length < 0 or length > _MAX_BODY_BYTES:
                self._send(413, "application/json; charset=utf-8", json.dumps({"error": "Invalid request size"}))
                return
            raw = self.rfile.read(length)
            result = handle_control_panel_api("POST", self.path, raw, root)
            self._send(result["http_status"], "application/json; charset=utf-8", json.dumps(result["body"]))

        def log_message(self, format_string, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.control_panel_html = page
    server.vault_dir = root
    return server


def handle_upload_and_dedup_api(vault_dir, db_path, filename, payload_bytes):
    """Inspect an upload, route binary bytes to disk, unpack safe types, and deduplicate."""
    root = _vault_root(vault_dir)
    if not isinstance(filename, str) or not filename or Path(filename).name != filename or len(filename) > 128:
        raise ControlPanelError("filename must be one bounded basename")
    if not isinstance(payload_bytes, bytes) or len(payload_bytes) > 64 * 1024 * 1024:
        raise ControlPanelError("payload_bytes must be bytes no larger than 64 MiB")
    core = _load_verified_core(vault_dir=root)
    intercepted = core.intercept_binary_chat_dump(payload_bytes, filename)
    suffix = Path(filename).suffix.lower()
    unpack_result = None
    source_path = None
    if suffix in (".zip", ".txt", ".md", ".json"):
        digest = hashlib.sha256(payload_bytes).hexdigest()
        if intercepted.get("blocked"):
            source_path = Path(intercepted["path"])
        else:
            relative_source = Path("imports") / "incoming_uploads" / digest / filename
            source_path = core.verify_safe_path(relative_source)
            source_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.exists():
                if not source_path.is_file() or source_path.read_bytes() != payload_bytes:
                    raise ControlPanelError("Existing upload staging record differs")
            else:
                with source_path.open("xb") as stream:
                    stream.write(payload_bytes)
        stage = Path("imports") / "unpacked_uploads" / digest
        unpack_result = core.unpack_local_upload(source_path, stage)
    dedup_result = core.deduplicate_uploaded_artifact(db_path, payload_bytes, filename)
    return {
        "upload": dedup_result,
        "unpacked": unpack_result,
        "intercept": {key: intercepted[key] for key in ("allow_chat", "blocked", "reason", "path", "sha256", "bytes", "chat_reference") if key in intercepted},
        "executed_files": 0,
    }


def handle_potluck_detect_api(text, vault_dir=None):
    """Return deterministic date, currency, port, and action spans from CP-100."""
    core = _load_verified_core(vault_dir=vault_dir)
    return core.detect_potluck_entities(text)


def handle_trash_api(db_path, vault_dir, action, item_id_or_path, current_ts):
    """Apply CP-100's 24-hour hold, restore window, or post-expiry purge."""
    root = _vault_root(vault_dir)
    core = _load_verified_core(vault_dir=root)
    if not isinstance(item_id_or_path, str) or not item_id_or_path:
        raise ControlPanelError("A vault-relative item path is required")
    if Path(item_id_or_path).is_absolute() or ".." in Path(item_id_or_path).parts:
        raise ControlPanelError("Trash item path must stay inside the vault")
    if action in ("hold", "delete"):
        return core.soft_delete_with_24h_hold(db_path, item_id_or_path, current_ts)
    if action in ("restore", "purge"):
        return core.restore_or_purge_trash_item(db_path, item_id_or_path, action, current_ts)
    raise ControlPanelError("action must be hold, restore, or purge")


def handle_privacy_redact_api(text, custom_terms=None, vault_dir=None):
    """Redact personal identifiers, then verify the masked pseudonymous bundle."""
    core = _load_verified_core(vault_dir=vault_dir)
    redacted = core.redact_personal_identifiers(text, custom_terms)
    privacy = core.verify_owner_privacy_mask({"pseudonym": "Donald Duck", "text": redacted})
    return {"redacted_text": redacted, "privacy": privacy}


_handle_control_panel_api_batch21 = handle_control_panel_api


def handle_control_panel_api(method, path, body, vault):
    """Extend the original routes with upload, potluck, trash, and redaction APIs."""
    route = urlsplit(path).path if isinstance(path, str) else ""
    new_routes = {"/api/upload", "/api/potluck", "/api/trash", "/api/redact"}
    if route not in new_routes:
        return _handle_control_panel_api_batch21(method, path, body, vault)
    if not isinstance(method, str) or method.upper() != "POST":
        return _json_result(405, {"error": "Method not allowed", "allow": ["POST"]})
    try:
        request = body if isinstance(body, dict) else _json_body(body)
        root = _vault_root(vault)
        if route == "/api/upload":
            filename = request.get("filename")
            if "payload_text" in request:
                if not isinstance(request["payload_text"], str):
                    raise ControlPanelError("payload_text must be text")
                payload = request["payload_text"].encode("utf-8")
            elif "payload_base64" in request:
                import base64
                encoded = request["payload_base64"]
                if not isinstance(encoded, str):
                    raise ControlPanelError("payload_base64 must be text")
                try:
                    payload = base64.b64decode(encoded, validate=True)
                except (ValueError, TypeError) as error:
                    raise ControlPanelError("payload_base64 is invalid") from error
            else:
                raise ControlPanelError("payload_text or payload_base64 is required")
            result = handle_upload_and_dedup_api(root, request.get("db_path", "state/prompt_engine.db"), filename, payload)
        elif route == "/api/potluck":
            result = handle_potluck_detect_api(request.get("text"), root)
        elif route == "/api/trash":
            result = handle_trash_api(request.get("db_path", "state/prompt_engine.db"), root,
                                      request.get("action"), request.get("item_id_or_path"), request.get("current_ts"))
        else:
            result = handle_privacy_redact_api(request.get("text"), request.get("custom_terms"), root)
        return _json_result(200, result)
    except (ControlPanelError, ValueError, TypeError, OSError, sqlite3.Error) as error:
        return _json_result(400, {"error": str(error)})


_generate_try_out_control_panel_html_batch21 = generate_try_out_control_panel_html


def generate_try_out_control_panel_html(output_path):
    """Extend the existing standalone panel with the four Batch 22 routes."""
    result = _generate_try_out_control_panel_html_batch21(output_path)
    target = Path(output_path)
    html = target.read_text(encoding="utf-8")
    panel = r'''<main><h2>Upload and deduplicate</h2><label for="upload-file">Choose TXT, MD, JSON, or ZIP</label><input id="upload-file" type="file" accept=".txt,.md,.json,.zip"><button id="upload-button">Inspect and store</button></main>
<main><h2>Potluck entity scan</h2><label for="potluck-text">Text to scan for dates, CAD/USD, ports, and action items</label><textarea id="potluck-text">TODO: Review invoice by 2026-10-30 for CAD $25.00. Port 8501.</textarea><button id="potluck-button">Detect entities</button></main>
<main><h2>Trash hold and restore</h2><label for="trash-path">Vault-relative file path</label><input id="trash-path" value="imports/trash-demo.txt"><select id="trash-action"><option value="hold">Hold for 24 hours</option><option value="restore">Restore</option><option value="purge">Purge after 24 hours</option></select><button id="trash-button">Apply trash action</button></main>
<main><h2>Privacy redaction</h2><label for="redact-text">Text to redact</label><textarea id="redact-text">Contact Example Person at example@example.com</textarea><label for="custom-terms">Additional names, comma separated</label><input id="custom-terms" value="Example Person"><button id="redact-button">Redact and verify</button></main>
<script>
document.getElementById('upload-button').onclick=async()=>{try{const file=document.getElementById('upload-file').files[0];if(!file)throw new Error('Choose a file first');if(file.size>600000)throw new Error('Control panel uploads are limited to 600 KB');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let start=0;start<bytes.length;start+=8192)binary+=String.fromCharCode(...bytes.subarray(start,start+8192));show(await api('/api/upload',{filename:file.name,payload_base64:btoa(binary)}));}catch(error){show({error:error.message});}};
document.getElementById('potluck-button').onclick=async()=>{try{show(await api('/api/potluck',{text:document.getElementById('potluck-text').value}));}catch(error){show({error:error.message});}};
document.getElementById('trash-button').onclick=async()=>{try{show(await api('/api/trash',{action:document.getElementById('trash-action').value,item_id_or_path:document.getElementById('trash-path').value,current_ts:new Date().toISOString()}));}catch(error){show({error:error.message});}};
document.getElementById('redact-button').onclick=async()=>{try{const terms=document.getElementById('custom-terms').value.split(',').map(value=>value.trim()).filter(Boolean);show(await api('/api/redact',{text:document.getElementById('redact-text').value,custom_terms:terms}));}catch(error){show({error:error.message});}};
</script>'''
    if "id=\"upload-button\"" not in html:
        if "</body>" not in html:
            raise ControlPanelError("Existing standalone panel has no body terminator")
        html = html.replace("</body>", panel + "</body>")
        target.write_text(html, encoding="utf-8")
    return {"path": str(target), "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


from urllib.parse import parse_qs


def _read_only_rows(database_path, table_name, query, parameters=()):
    '''Read a bounded set of rows from an existing SQLite table only.'''
    path = Path(database_path)
    if not path.is_file() or path.is_symlink():
        return []
    uri = path.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=2) as connection:
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        ).fetchone()
        if not present:
            return []
        return connection.execute(query, parameters).fetchmany(500)


def _subtab_output(value):
    '''Require deterministic JSON-safe payloads below the response ceiling.'''
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) >= 100 * 1024:
        raise ControlPanelError("Project sub-tab response exceeds 100 KiB")
    return json.loads(encoded)


def get_lanes_and_progress_subtabs(vault, db):
    '''Return Sub-Tabs 1-2 using installed scheduler and scorecard evidence.'''
    root = _vault_root(vault)
    core = _load_verified_core(vault_dir=root)
    scheduler_path = root / "state" / "b7_scheduler.db"
    task_rows = _read_only_rows(
        scheduler_path, "b7_tasks",
        "SELECT task_id,status,lease_turn FROM b7_tasks ORDER BY rowid LIMIT 500",
    )
    counts = {}
    for _task_id, status, _lease in task_rows:
        counts[status] = counts.get(status, 0) + 1
    state_rows = _read_only_rows(
        scheduler_path, "b7_scheduler_state",
        "SELECT current_turn,dispatched FROM b7_scheduler_state WHERE singleton=1 LIMIT 1",
    )
    current_turn, dispatched = state_rows[0] if state_rows else (None, None)
    queued = counts.get("QUEUED", 0)
    scorecard = {"status": "GRAY", "reason": "Installed scorecard evidence unavailable"}
    report_path = root / "audit" / "pass_tests.json"
    if report_path.is_file() and not report_path.is_symlink():
        try:
            scorecard = {"status": "GREEN", "text": core.generate_cp100_scorecard(db)}
        except (OSError, ValueError, sqlite3.Error) as error:
            scorecard = {"status": "GRAY", "reason": str(error)}
    progress = {
        "status": "GREEN" if state_rows or task_rows else "GRAY",
        "queue_status_counts": dict(sorted(counts.items())),
        "current_turn": current_turn,
        "dispatched_this_turn": dispatched,
        "queued_tasks": queued,
        "eta_turns": queued,
        "eta_basis": "one queued task per scheduler turn; estimate only",
    }
    return _subtab_output({
        "subtabs": [
            {"id": 1, "name": "Lanes", "status": "GREEN" if task_rows else "GRAY",
             "lanes": [{"task_id": row[0], "status": row[1], "lease_turn": row[2]} for row in task_rows]},
            {"id": 2, "name": "Progress and ETA", "progress": progress, "scorecard": scorecard},
        ]
    })


def get_goals_and_notepad_subtabs(db, project, notes=None):
    '''Return Sub-Tabs 3-4 from immutable plan state and deterministic entity scan.'''
    if not isinstance(project, str) or not project.strip():
        raise ControlPanelError("project is required")
    core = _load_verified_core(vault_dir=Path(db).resolve().parents[2])
    plan = {"status": "GRAY", "reason": "No locked plan available"}
    drift = {"status": "GRAY", "reason": "No locked plan available"}
    note_text = notes if isinstance(notes, str) else ""
    path = Path(db)
    if path.is_file() and not path.is_symlink():
        locked_rows = _read_only_rows(
            path, "b13_locks", "SELECT payload,lock_sha256 FROM b13_locks WHERE project=? LIMIT 1", (project,)
        )
        if locked_rows:
            payload_text, lock_sha = locked_rows[0]
            payload = json.loads(payload_text)
            plan = {"status": "GREEN", "lock_sha256": lock_sha,
                    "read_only": True, "instructions": payload.get("instructions", [])}
            if not note_text:
                note_text = "\n".join(item.get("text", "") for item in payload.get("instructions", []) if isinstance(item, dict))
            completed_ids = []
            if isinstance(notes, dict) and isinstance(notes.get("completed_ids"), list):
                completed_ids = notes["completed_ids"]
            try:
                drift = core.check_output_against_locked_plan(db, project, completed_ids)
            except (ValueError, sqlite3.Error) as error:
                drift = {"status": "GRAY", "reason": str(error)}
    entities = core.detect_potluck_entities(note_text) if note_text else {
        "dates": [], "dollar_amounts": [], "ports": [], "action_items": []
    }
    return _subtab_output({
        "subtabs": [
            {"id": 3, "name": "Goals and locked plan", "plan": plan, "drift": drift},
            {"id": 4, "name": "Notepad and potluck", "notes": note_text, "entities": entities},
        ]
    })


def get_backups_and_alerts_subtabs(vault, db):
    '''Return Sub-Tabs 5-6 from mirror, snapshot, alert, and workflow records.'''
    root = _vault_root(vault)
    core = _load_verified_core(vault_dir=root)
    mirror_path = root / "state" / "four_mirrors.json"
    if mirror_path.is_file() and not mirror_path.is_symlink():
        mirrors = core.sync_four_mirrors(json.loads(mirror_path.read_text(encoding="utf-8")))
    else:
        mirrors = core.sync_four_mirrors({})
    snapshots_root = root / "snapshots"
    snapshots = []
    if snapshots_root.is_dir() and not snapshots_root.is_symlink():
        for item in sorted(snapshots_root.iterdir(), key=lambda value: value.name)[:200]:
            if not item.is_symlink() and item.is_file():
                snapshots.append({"name": item.name, "bytes": item.stat().st_size})
    alert_rows = _read_only_rows(
        db, "b18_alerts",
        "SELECT id,severity,code,msg,created_at,acknowledged FROM b18_alerts ORDER BY id DESC LIMIT 100",
    )
    alerts = [{"id": row[0], "severity": row[1], "code": row[2], "message": row[3],
               "created_at": row[4], "acknowledged": bool(row[5])} for row in alert_rows]
    prediction = core.predict_next_workflow_step(
        "Batch 23", {"Batch 23": ["Muse audit"], "Muse audit": ["Record Checkpoint 115"]}
    )
    return _subtab_output({
        "subtabs": [
            {"id": 5, "name": "Backups and snapshots", "mirrors": mirrors, "snapshots": snapshots},
            {"id": 6, "name": "Alerts and predictions", "alerts": alerts, "prediction": prediction},
        ]
    })


_handle_control_panel_api_batch22 = handle_control_panel_api


def handle_control_panel_api(method, path, body, vault):
    '''Add a deterministic, bounded endpoint for all six Project Sub-Tabs.'''
    if isinstance(path, str) and urlsplit(path).path == "/api/subtabs":
        if not isinstance(method, str) or method.upper() not in ("GET", "POST"):
            return _json_result(405, {"error": "Method not allowed", "allow": ["GET", "POST"]})
        try:
            root = _vault_root(vault)
            request = _json_body(body) if method.upper() == "POST" else {}
            query = parse_qs(urlsplit(path).query, keep_blank_values=True)
            project = request.get("project") or (query.get("project") or ["control-panel"])[0]
            notes = request.get("notes")
            db_path = root / _database_path(root)
            sections = []
            sections.extend(get_lanes_and_progress_subtabs(root, db_path)["subtabs"])
            sections.extend(get_goals_and_notepad_subtabs(db_path, project, notes)["subtabs"])
            sections.extend(get_backups_and_alerts_subtabs(root, db_path)["subtabs"])
            return _json_result(200, _subtab_output({"project": project, "subtabs": sections}))
        except (ControlPanelError, ValueError, TypeError, OSError, sqlite3.Error, json.JSONDecodeError) as error:
            return _json_result(400, {"error": str(error)})
    return _handle_control_panel_api_batch22(method, path, body, vault)


_generate_try_out_control_panel_html_batch22 = generate_try_out_control_panel_html


def generate_try_out_control_panel_html(output_path):
    '''Add six live Project Sub-Tabs to the previously generated local panel.'''
    result = _generate_try_out_control_panel_html_batch22(output_path)
    target = Path(output_path)
    html = target.read_text(encoding="utf-8")
    panel = r'''<main><h2>Project Sub-Tabs</h2><label for="subtab-project">Project</label><input id="subtab-project" value="control-panel">
<nav id="project-subtabs" aria-label="Project Sub-Tabs">
<button type="button" data-subtab="1">1. Lanes</button><button type="button" data-subtab="2">2. Progress and ETA</button>
<button type="button" data-subtab="3">3. Goals and locked plan</button><button type="button" data-subtab="4">4. Notepad and potluck</button>
<button type="button" data-subtab="5">5. Backups and snapshots</button><button type="button" data-subtab="6">6. Alerts and predictions</button>
</nav><pre id="subtab-result">Choose a Project Sub-Tab to load live data.</pre></main>
<script>
async function loadProjectSubtab(event){const project=document.getElementById('subtab-project').value;const selected=Number(event.currentTarget.dataset.subtab);try{const data=await api('/api/subtabs?project='+encodeURIComponent(project));const tab=data.subtabs.find((item)=>item.id===selected);show({project,subtab:tab});}catch(error){show({error:error.message});}}
document.querySelectorAll('#project-subtabs [data-subtab]').forEach((button)=>button.addEventListener('click',loadProjectSubtab));
</script>'''
    if 'id="project-subtabs"' not in html:
        if "</body>" not in html:
            raise ControlPanelError("Existing standalone panel has no body terminator")
        html = html.replace("</body>", panel + "</body>")
        target.write_text(html, encoding="utf-8")
    return {"path": str(target), "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
