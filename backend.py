"""Supersonic Client - backend: config, Modrinth / CurseForge APIs, instances, launching, agent."""
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests
import minecraft_launcher_lib as mll

try:
    from requests.adapters import HTTPAdapter, Retry
except ImportError:      # very old requests
    HTTPAdapter = Retry = None

try:
    import psutil
except ImportError:
    psutil = None

APP_DIR = Path.home() / ".supersonic"
INSTANCES_DIR = APP_DIR / "instances"
BACKUP_DIR = APP_DIR / "backups"
CACHE_DIR = APP_DIR / "cache"
MC_ROOT = APP_DIR / "minecraft"          # shared assets / libraries / versions
CONFIG_FILE = APP_DIR / "config.json"
INSTANCES_FILE = APP_DIR / "instances.json"
READY_FILE = APP_DIR / "ready.json"        # versions that are fully installed (fast launch path)
FILE_CACHE = CACHE_DIR / "files"           # content-addressed (sha1) download cache

MR_API = "https://api.modrinth.com/v2"
CF_API = "https://api.curseforge.com/v1"
UA = {"User-Agent": "greeko2030-afk/Supersonic-Client/2.6.0 (github.com/greeko2030-afk/Supersonic-Client)"}
LOADERS = ("fabric", "forge", "neoforge", "quilt")
CF_LOADER_ID = {"forge": 1, "fabric": 4, "quilt": 5, "neoforge": 6}
CF_CLASS = {"modpack": 4471, "mod": 6, "resourcepack": 12, "shader": 6552}
CONTENT_DIRS = {"mod": "mods", "resourcepack": "resourcepacks", "shader": "shaderpacks"}
NO_WINDOW = 0x08000000 if platform.system() == "Windows" else 0

DEFAULTS = {
    "username": "Raffiee_playssMC", "ram_mb": 8192, "perf_mode": "Ultra (Recommended)",
    "language": "English", "theme": "Dark (Default)", "start_with_windows": False,
    "minimize_to_tray": True, "confirm_exit": True, "preload_assets": True, "smart_memory": True,
    "optimize_launcher": True, "java_version": "Auto (Recommended)", "auto_java": True, "native_libs": True,
    "keep_launcher_open": True, "check_updates": True, "download_updates": True,
    "beta_updates": False, "analytics": False, "crash_reports": True, "download_limit": "Unlimited",
    "max_connections": 16, "verify_downloads": True, "delete_temp": "Always", "cloud_sync": True,
    "sync_devices": True, "curseforge_key": "", "selected_instance": "Supersonic Main", "servers": [],
    "website_url": "https://supersonic-client--greeko2030.replit.app",
    "github_url": "https://github.com/greeko2030-afk/Supersonic-Client",
    "discord_url": "https://discord.com",
    # Supersonic Mods: mods published in a GitHub repo are installed automatically
    "auto_custom_mods": True, "mods_repo": "greeko2030-afk/mods", "mods_branch": "",
    # Translation: OpenGL -> Direct3D 12 (Windows only). Mode: Auto / OpenGL / D3D12
    "translation_mode": "Auto", "translation_folder": "Hidden Folder (Default)",
    "engine_repo": "greeko2030-afk/Supersonic-Client",
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fmt_num(n):
    n = float(n)
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if n >= div:
            s = f"{n / div:.1f}"
            return (s[:-2] if s.endswith(".0") else s) + unit
    return str(int(n))


# One shared session = keep-alive connections + automatic retries (much faster than a new connection per request)
SESSION = requests.Session()
if HTTPAdapter:
    _adapter = HTTPAdapter(pool_connections=32, pool_maxsize=64,
                           max_retries=Retry(total=3, backoff_factor=0.3, status_forcelist=(429, 500, 502, 503, 504)))
    SESSION.mount("https://", _adapter)
    SESSION.mount("http://", _adapter)


def http_get(url, **kw):
    headers = dict(UA)
    headers.update(kw.pop("headers", {}))
    kw.setdefault("timeout", 15)
    return SESSION.get(url, headers=headers, **kw)


class ManualDownload(Exception):
    """CurseForge author disabled third-party downloads for this file."""

    def __init__(self, filename, mod_id=None):
        super().__init__(f"{filename} must be downloaded manually from CurseForge")
        self.filename, self.mod_id = filename, mod_id


class Seen:
    """Thread-safe 'already handled' set, used to install shared dependencies only once."""

    def __init__(self):
        self._items, self._lock = set(), threading.Lock()

    def add(self, item):
        with self._lock:
            if item in self._items:
                return False
            self._items.add(item)
            return True


def run_parallel(jobs, workers=8, on_done=None):
    """jobs: [(key, callable)]. Runs them concurrently, returns {key: (result, error)}."""
    results = {}
    with ThreadPoolExecutor(max(1, workers)) as ex:
        futures = {ex.submit(fn): key for key, fn in jobs}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                res = (fut.result(), None)
            except Exception as e:      # noqa: BLE001 - report per job, never abort the batch
                res = (None, e)
            results[key] = res
            if on_done:
                on_done(key, *res)
    return results


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _link_or_copy(src, dst):
    try:
        os.link(src, dst)           # hard link: instant and uses no extra disk space
    except OSError:
        shutil.copyfile(src, dst)


def download(url, dest, sha1=None):
    """Download with: skip-if-present, sha1 content cache (instant re-installs), unique temp file (thread safe)."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if sha1:
        sha1 = sha1.lower()
        if dest.exists() and file_sha1(dest) == sha1:
            return "present"
        cached = FILE_CACHE / sha1
        if cached.exists():
            dest.unlink(missing_ok=True)
            _link_or_copy(cached, dest)
            return "cache"
    tmp = dest.with_name(f"{dest.name}.{uuid.uuid4().hex[:8]}.part")
    digest = hashlib.sha1()
    try:
        with http_get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 18):
                    f.write(chunk)
                    digest.update(chunk)
        if sha1 and digest.hexdigest() != sha1:
            raise IOError(f"Hash mismatch for {dest.name}")
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)
    cached = FILE_CACHE / digest.hexdigest()
    if not cached.exists():
        FILE_CACHE.mkdir(parents=True, exist_ok=True)
        try:
            _link_or_copy(dest, cached)
        except OSError:
            pass
    return "downloaded"


def clean_cache():
    """Delete cached downloads that no instance uses anymore (hard-link count 1). Returns bytes freed."""
    freed = 0
    if FILE_CACHE.exists():
        for p in FILE_CACHE.iterdir():
            try:
                st = p.stat()
                if st.st_nlink <= 1:
                    freed += st.st_size
                    p.unlink()
            except OSError:
                pass
    shutil.rmtree(CACHE_DIR / "packs", ignore_errors=True)
    return freed


def safe_join(base, rel):
    base = Path(base).resolve()
    target = (base / rel).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"Unsafe path in archive: {rel}")
    return target


def dir_size(path):
    total = 0
    for p in Path(path).rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass
    return total


def total_ram_gb():
    if psutil:
        return psutil.virtual_memory().total / 2 ** 30
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 30
    except (ValueError, OSError, AttributeError):
        return 0


def open_path(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))
    elif system == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def system_info():
    system = platform.system()
    os_name = f"{system} {platform.release()}"
    cpu, gpu = platform.processor() or "Unknown", "Unknown"
    try:
        if system == "Windows":
            build = int(platform.version().split(".")[2])
            os_name = f"Windows {'11' if build >= 22000 else '10'} {'64' if sys.maxsize > 2 ** 32 else '32'}-bit"
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_VideoController | Select-Object -First 1).Name"],
                capture_output=True, text=True, timeout=8, creationflags=NO_WINDOW)
            gpu = out.stdout.strip() or gpu
        elif system == "Darwin":
            cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                 capture_output=True, text=True, timeout=5).stdout.strip() or cpu
        else:
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass
    return {"OS": os_name, "CPU": cpu, "RAM": f"{total_ram_gb():.1f} GB",
            "GPU": gpu, "Storage": f"{shutil.disk_usage(Path.home()).total / 1e9:.0f} GB"}


# ----------------------------------------------------------------------------
# Config & instances
# ----------------------------------------------------------------------------
class Config:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.data = json.loads(json.dumps(DEFAULTS))
        if CONFIG_FILE.exists():
            try:
                self.data.update(json.loads(CONFIG_FILE.read_text("utf-8")))
            except Exception:
                pass
        if self.data.get("java_version") == "Auto":
            self.data["java_version"] = "Auto (Recommended)"
        # older versions shipped a wrong GitHub account name in the default URL
        url = str(self.data.get("github_url", ""))
        if "github.com/greeko-afk/" in url:
            self.data["github_url"] = url.replace("github.com/greeko-afk/", "github.com/greeko2030-afk/")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def save(self):
        CONFIG_FILE.write_text(json.dumps(self.data, indent=2), "utf-8")

    def reset(self):
        keep = {k: self.data.get(k) for k in ("username", "curseforge_key", "selected_instance", "servers")}
        self.data = json.loads(json.dumps(DEFAULTS))
        self.data.update(keep)
        self.save()

    def offline_uuid(self):
        raw = hashlib.md5(("OfflinePlayer:" + self.data["username"]).encode()).digest()
        return str(uuid.UUID(bytes=raw, version=3))


@dataclass
class Instance:
    name: str
    mc: str = "1.21.4"
    loader: str = "fabric"
    loader_version: str = ""
    last_played: float = 0.0
    source: str = ""
    addons: dict = field(default_factory=dict)

    @property
    def dir(self):
        return INSTANCES_DIR / re.sub(r"[^\w\- ]", "_", self.name)

    @property
    def mods_dir(self):
        return self.dir / "mods"

    def has_addon(self, name):
        info = self.addons.get(name)
        return bool(info) and (self.dir / info.get("dir", "mods") / info["filename"]).exists()


class InstanceManager:
    def __init__(self):
        self.items = []
        try:
            self.items = [Instance(**d) for d in json.loads(INSTANCES_FILE.read_text("utf-8"))]
        except Exception:
            pass
        if not self.items:
            self.create("Supersonic Main", "1.21.4", "fabric")

    def save(self):
        INSTANCES_FILE.write_text(json.dumps([asdict(i) for i in self.items], indent=2), "utf-8")

    def get(self, name):
        return next((i for i in self.items if i.name == name), None)

    def create(self, name, mc, loader, loader_version="", source=""):
        base, n = name, 2
        while self.get(name):
            name, n = f"{base} ({n})", n + 1
        inst = Instance(name, mc, loader, loader_version, source=source)
        inst.mods_dir.mkdir(parents=True, exist_ok=True)
        self.items.append(inst)
        self.save()
        return inst

    def delete(self, inst):
        shutil.rmtree(inst.dir, ignore_errors=True)
        self.items.remove(inst)
        self.save()


def backup_instance(inst):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    out = BACKUP_DIR / f"{inst.dir.name}-{time.strftime('%Y%m%d-%H%M%S')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, strict_timestamps=False) as z:
        z.writestr("instance.json", json.dumps(asdict(inst)))
        for p in inst.dir.rglob("*"):
            rel = p.relative_to(inst.dir)
            if p.is_file() and rel.parts[0] not in ("logs", "crash-reports"):
                z.write(p, "data/" + rel.as_posix())
    return out


def restore_backup(zip_path, manager):
    with zipfile.ZipFile(zip_path) as z:
        meta = json.loads(z.read("instance.json"))
        inst = manager.create(meta["name"], meta["mc"], meta["loader"],
                              meta.get("loader_version", ""), meta.get("source", ""))
        inst.addons = meta.get("addons", {})
        for m in z.namelist():
            if m.startswith("data/") and not m.endswith("/"):
                target = safe_join(inst.dir, m[5:])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(m))
    manager.save()
    return inst


# ----------------------------------------------------------------------------
# Modrinth
# ----------------------------------------------------------------------------
class Modrinth:
    _vcache = {}

    def search(self, query="", project_type="modpack", category=None, version=None,
               loader=None, sort="downloads", offset=0, limit=8):
        facets = [[f"project_type:{project_type}"]]
        if category:
            facets.append([f"categories:{category}"])
        if version:
            facets.append([f"versions:{version}"])
        if loader:
            facets.append([f"categories:{loader}"])
        r = http_get(f"{MR_API}/search", params={
            "query": query, "facets": json.dumps(facets), "index": sort, "offset": offset, "limit": limit})
        r.raise_for_status()
        data = r.json()
        return [self._norm(h) for h in data["hits"]], data["total_hits"]

    @staticmethod
    def _norm(h):
        cats = h.get("display_categories") or h.get("categories", [])
        return {
            "source": "modrinth", "id": h["project_id"], "slug": h["slug"], "title": h["title"],
            "author": h.get("author", ""), "summary": h.get("description", ""),
            "mc": (h.get("versions") or ["?"])[-1],
            "tags": [c.replace("-", " ").title() for c in cats if c not in LOADERS][:3],
            "downloads": h.get("downloads", 0), "rating": h.get("follows", 0),
            "thumb": h.get("featured_gallery") or (h.get("gallery") or [None])[0] or h.get("icon_url"),
            "icon": h.get("icon_url"), "ptype": h.get("project_type", "modpack"),
            "url": f"https://modrinth.com/{h.get('project_type', 'modpack')}/{h['slug']}",
        }

    def projects(self, slugs):
        r = http_get(f"{MR_API}/projects", params={"ids": json.dumps(slugs)})
        r.raise_for_status()
        return {p["slug"]: p for p in r.json()}

    def best_version(self, ident, mc, loader, ptype="mod"):
        key = (ident, mc, loader, ptype)
        if key in self._vcache:
            return self._vcache[key]

        def query(slug, with_version=True):
            params = {}
            if with_version:
                params["game_versions"] = json.dumps([mc])
            if ptype == "mod":
                params["loaders"] = json.dumps([loader] + (["fabric"] if loader == "quilt" else []))
            return http_get(f"{MR_API}/project/{slug}/version", params=params)

        slug = ident
        r = query(slug)
        if r.status_code == 404:
            hits, _ = self.search(ident, ptype, limit=1)
            if not hits:
                return None
            slug = hits[0]["slug"]
            r = query(slug)
        r.raise_for_status()
        versions = r.json()
        if not versions and ptype != "mod":     # resource packs / shaders usually still work on nearby versions
            r = query(slug, with_version=False)
            r.raise_for_status()
            versions = r.json()
        version = next((v for v in versions if v["version_type"] == "release"), versions[0]) if versions else None
        self._vcache[key] = version
        return version

    def install_mod(self, ident, inst, status=lambda s: None, seen=None, ptype="mod"):
        """Install a project (+ required dependencies) into the instance. Returns file info or None."""
        seen = seen if seen is not None else Seen()
        version = self.best_version(ident, inst.mc, inst.loader, ptype)
        if not version:
            return None
        if ptype == "mod":
            for dep in version.get("dependencies", []):
                pid = dep.get("project_id")
                if dep.get("dependency_type") == "required" and pid and seen.add(("mr", pid)):
                    self.install_mod(pid, inst, status, seen)
        f = next((x for x in version["files"] if x.get("primary")), version["files"][0])
        status(f"Downloading {f['filename']}...")
        download(f["url"], inst.dir / CONTENT_DIRS[ptype] / f["filename"], f["hashes"].get("sha1"))
        return {"filename": f["filename"], "version": version["version_number"],
                "source": "modrinth", "dir": CONTENT_DIRS[ptype]}

    def addon_info(self, slug, mc, loader):
        p = http_get(f"{MR_API}/project/{slug}").json()
        info = {"title": p["title"], "description": p["description"], "icon": p.get("icon_url"),
                "version": "N/A", "author": "-"}
        try:
            v = self.best_version(slug, mc, loader)
            info["version"] = v["version_number"] if v else "N/A"
        except Exception:
            pass
        try:
            members = http_get(f"{MR_API}/project/{slug}/members").json()
            info["author"] = next((m["user"]["username"] for m in members if m.get("role") == "Owner"),
                                  members[0]["user"]["username"])
        except Exception:
            pass
        return info


# ----------------------------------------------------------------------------
# CurseForge (needs a free API key from console.curseforge.com)
# ----------------------------------------------------------------------------
class CurseForge:
    def __init__(self, cfg):
        self.cfg = cfg

    def key(self):
        return (self.cfg.get("curseforge_key", "") or os.environ.get("CURSEFORGE_API_KEY", "")).strip()

    def has_key(self):
        return bool(self.key())

    def _headers(self):
        key = self.key()
        if not key:
            raise RuntimeError("CurseForge API key missing. Settings > Metadata Sources > Configure "
                               "(free key: console.curseforge.com)")
        return {"x-api-key": key, "Accept": "application/json"}

    def get(self, path, **params):
        r = http_get(CF_API + path, params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()

    def post(self, path, body):
        r = requests.post(CF_API + path, json=body, headers={**UA, **self._headers()}, timeout=30)
        r.raise_for_status()
        return r.json()

    def search(self, query="", sort=2, version=None, loader=None, offset=0, limit=8, ptype="modpack"):
        params = {"gameId": 432, "classId": CF_CLASS[ptype], "searchFilter": query, "sortField": sort,
                  "sortOrder": "desc", "index": offset, "pageSize": limit}
        if version:
            params["gameVersion"] = version
        if loader and ptype in ("mod", "modpack"):
            params["modLoaderType"] = CF_LOADER_ID.get(loader)
        data = self.get("/mods/search", **params)
        return [self._norm(m, ptype) for m in data["data"]], data["pagination"]["totalCount"]

    def best_file(self, mod_id, mc, loader, ptype="mod"):
        params = {"pageSize": 20}
        if mc:
            params["gameVersion"] = mc
        if ptype == "mod" and loader in CF_LOADER_ID:
            params["modLoaderType"] = CF_LOADER_ID[loader]
        files = self.get(f"/mods/{mod_id}/files", **params)["data"]
        if not files and ptype != "mod":
            params.pop("gameVersion", None)
            files = self.get(f"/mods/{mod_id}/files", **params)["data"]
        files = [f for f in files if f.get("isAvailable", True)]
        files.sort(key=lambda f: f.get("fileDate", ""), reverse=True)     # newest first
        files.sort(key=lambda f: f.get("releaseType", 3) != 1)            # stable: releases before beta/alpha
        return files[0] if files else None

    def install_mod(self, mod_id, inst, ptype="mod", status=lambda s: None, seen=None):
        seen = seen if seen is not None else Seen()
        f = self.best_file(mod_id, inst.mc, inst.loader, ptype)
        if not f:
            return None
        url = f.get("downloadUrl")
        if not url:
            raise ManualDownload(f["fileName"], mod_id)
        if ptype == "mod":
            for dep in f.get("dependencies", []):
                if dep.get("relationType") == 3 and seen.add(("cf", dep["modId"])):     # 3 = required dependency
                    try:
                        self.install_mod(dep["modId"], inst, "mod", status, seen)
                    except ManualDownload:
                        status("A dependency needs manual download from CurseForge")
        sha1 = next((h["value"] for h in f.get("hashes", []) if h.get("algo") == 1), None)
        status(f"Downloading {f['fileName']}...")
        download(url, inst.dir / CONTENT_DIRS[ptype] / f["fileName"], sha1)
        return {"filename": f["fileName"], "version": f.get("displayName", ""),
                "source": "curseforge", "dir": CONTENT_DIRS[ptype]}

    @staticmethod
    def _norm(m, ptype="modpack"):
        idx = (m.get("latestFilesIndexes") or [{}])[0]
        shots = m.get("screenshots") or []
        logo = (m.get("logo") or {}).get("thumbnailUrl")
        return {
            "source": "curseforge", "id": m["id"], "slug": m["slug"], "title": m["name"],
            "author": (m.get("authors") or [{}])[0].get("name", ""), "summary": m.get("summary", ""),
            "mc": idx.get("gameVersion", "?"), "file_id": idx.get("fileId"),
            "tags": [c["name"] for c in m.get("categories", [])][:3],
            "downloads": m.get("downloadCount", 0), "rating": m.get("thumbsUpCount", 0),
            "thumb": shots[0]["thumbnailUrl"] if shots else logo, "icon": logo, "ptype": ptype,
            "url": (m.get("links") or {}).get("websiteUrl") or f"https://www.curseforge.com/minecraft/search?search={m['name']}",
        }


# ----------------------------------------------------------------------------
# Store: one API over Modrinth + CurseForge
# ----------------------------------------------------------------------------
class Store:
    def __init__(self, mr, cf):
        self.mr, self.cf = mr, cf

    def search_all(self, query, ptype, mc=None, loader=None, limit=12):
        """Search both sources in parallel. Returns (merged_items, notes)."""
        mod_loader = loader if ptype == "mod" else None
        jobs = [("modrinth", lambda: self.mr.search(query, ptype, None, mc, mod_loader, "relevance", 0, limit)[0])]
        if self.cf.has_key():
            jobs.append(("curseforge", lambda: self.cf.search(query, 1, mc, mod_loader, 0, limit, ptype)[0]))
        results = run_parallel(jobs, 2)
        notes, lists = [], []
        for src in ("modrinth", "curseforge"):
            if src in results:
                items, err = results[src]
                lists.append(items or [])
                if err:
                    notes.append(f"{src.title()}: {err}")
        if not self.cf.has_key():
            notes.append("Add a CurseForge API key in Settings to include CurseForge results.")
        merged, seen = [], set()
        for i in range(max((len(x) for x in lists), default=0)):      # interleave sources
            for items in lists:
                if i < len(items) and items[i]["title"].lower() not in seen:
                    seen.add(items[i]["title"].lower())
                    merged.append(items[i])
        return merged, notes

    def install(self, item, inst, status=lambda s: None, seen=None):
        if item["source"] == "modrinth":
            return self.mr.install_mod(item["id"], inst, status, seen, item["ptype"])
        return self.cf.install_mod(item["id"], inst, item["ptype"], status, seen)

    def install_addon(self, name, slug, inst, seen=None, status=lambda s: None):
        """Catalog addon: Modrinth first, CurseForge as fallback (when a key is configured)."""
        try:
            info = self.mr.install_mod(slug, inst, status, seen)
        except requests.RequestException:
            if not self.cf.has_key():
                raise
            info = None
        if info or not self.cf.has_key():
            return info
        hits, _ = self.cf.search(name.split(" (")[0], 1, inst.mc, inst.loader, 0, 5, "mod")
        hit = next((h for h in hits if h["slug"] == slug or h["title"].lower() == name.lower()), None)
        return self.cf.install_mod(hit["id"], inst, "mod", status, seen) if hit else None


# ----------------------------------------------------------------------------
# Modpack installer (.mrpack from Modrinth, manifest.zip from CurseForge)
# ----------------------------------------------------------------------------
class PackInstaller:
    def __init__(self, cfg, instances, cf):
        self.cfg, self.instances, self.cf = cfg, instances, cf

    def install(self, pack, status, progress):
        """Returns (instance, skipped_files)."""
        status(f"Resolving {pack['title']}...")
        if pack["source"] == "modrinth":
            r = http_get(f"{MR_API}/project/{pack['id']}/version")
            r.raise_for_status()
            versions = r.json()
            if not versions:
                raise RuntimeError("No downloadable version found")
            v = next((x for x in versions if x["version_type"] == "release"), versions[0])
            f = next((x for x in v["files"] if x.get("primary")), v["files"][0])
            tmp = CACHE_DIR / "packs" / f["filename"]
            status(f"Downloading {f['filename']}...")
            download(f["url"], tmp, f["hashes"].get("sha1"))
            return self.install_mrpack(tmp, pack["title"], status, progress)
        info = self.cf.get(f"/mods/{pack['id']}/files/{pack['file_id']}")["data"]
        url = info.get("downloadUrl") or self.cf.get(
            f"/mods/{pack['id']}/files/{pack['file_id']}/download-url")["data"]
        tmp = CACHE_DIR / "packs" / info["fileName"]
        status(f"Downloading {info['fileName']}...")
        download(url, tmp)
        return self._cf_zip(tmp, pack["title"], status, progress)

    def import_file(self, path, status, progress):
        path = Path(path)
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
        if "modrinth.index.json" in names:
            return self.install_mrpack(path, path.stem, status, progress)
        if "manifest.json" in names:
            return self._cf_zip(path, path.stem, status, progress)
        raise ValueError("Unsupported file. Use a Modrinth .mrpack or a CurseForge modpack .zip")

    def install_mrpack(self, path, name, status, progress):
        with zipfile.ZipFile(path) as z:
            index = json.loads(z.read("modrinth.index.json"))
            deps = index.get("dependencies", {})
            loader, lver = "vanilla", ""
            for key, value in deps.items():
                if key != "minecraft":
                    loader, lver = key.replace("-loader", ""), value
            inst = self.instances.create(name or index.get("name", "Modpack"),
                                         deps.get("minecraft", "1.21.4"), loader, lver, source="modrinth")
            try:
                files = [f for f in index["files"] if f.get("env", {}).get("client") != "unsupported"]
                items = [(f["path"], f["downloads"][0], f.get("hashes", {}).get("sha1")) for f in files]
                self._fetch_all(items, inst.dir, status, progress)
                for prefix in ("overrides/", "client-overrides/"):
                    self._extract(z, prefix, inst.dir)
            except Exception:
                self.instances.delete(inst)
                raise
        return inst, []

    def _cf_zip(self, path, title, status, progress):
        with zipfile.ZipFile(path) as z:
            man = json.loads(z.read("manifest.json"))
            mc = man["minecraft"]["version"]
            loaders = man["minecraft"].get("modLoaders") or [{"id": "vanilla-"}]
            loader, _, lver = loaders[0]["id"].partition("-")
            inst = self.instances.create(title or man.get("name", "Modpack"), mc, loader, lver,
                                         source="curseforge")
            items, skipped = [], []
            try:
                ids = [f["fileID"] for f in man["files"]]
                status("Resolving CurseForge files...")
                for i in range(0, len(ids), 200):
                    for d in self.cf.post("/mods/files", {"fileIds": ids[i:i + 200]})["data"]:
                        if d.get("downloadUrl"):
                            sub = "mods" if d["fileName"].endswith(".jar") else "resourcepacks"
                            items.append((f"{sub}/{d['fileName']}", d["downloadUrl"], None))
                        else:
                            skipped.append(d["fileName"])
                self._fetch_all(items, inst.dir, status, progress)
                self._extract(z, man.get("overrides", "overrides") + "/", inst.dir)
            except Exception:
                self.instances.delete(inst)
                raise
        return inst, skipped

    def _fetch_all(self, items, base, status, progress):
        total, done = max(len(items), 1), 0
        verify = self.cfg.get("verify_downloads", True)

        def one(item):
            rel, url, sha = item
            download(url, safe_join(base, rel), sha if verify else None)

        with ThreadPoolExecutor(int(self.cfg.get("max_connections", 16))) as ex:
            for fut in as_completed([ex.submit(one, it) for it in items]):
                fut.result()
                done += 1
                progress(done / total)
                status(f"Downloading files {done}/{len(items)}")

    @staticmethod
    def _extract(z, prefix, dest):
        for m in z.namelist():
            if m.startswith(prefix) and not m.endswith("/"):
                target = safe_join(dest, m[len(prefix):])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(m))


# ----------------------------------------------------------------------------
# Launcher
# ----------------------------------------------------------------------------
def make_cb(status, progress):
    state = {"max": 1}
    return {
        "setStatus": lambda s: status(s),
        "setMax": lambda m: state.__setitem__("max", max(m, 1)),
        "setProgress": lambda p: progress(min(p / state["max"], 1.0)),
    }


G1_FLAGS = [
    "-XX:+UseG1GC", "-XX:+ParallelRefProcEnabled", "-XX:MaxGCPauseMillis=200",
    "-XX:+UnlockExperimentalVMOptions", "-XX:G1NewSizePercent=30", "-XX:G1MaxNewSizePercent=40",
    "-XX:G1HeapRegionSize=8M", "-XX:G1ReservePercent=20", "-XX:InitiatingHeapOccupancyPercent=15",
    "-XX:SurvivorRatio=32", "-XX:+PerfDisableSharedMem", "-XX:MaxTenuringThreshold=1",
]


# ----------------------------------------------------------------------------
# Supersonic Mods: mods published in a GitHub repository are installed automatically
# ----------------------------------------------------------------------------
try:
    import tomllib                      # Python 3.11+
except ImportError:                     # pragma: no cover
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

GH_API = "https://api.github.com"
GH_RAW = "https://raw.githubusercontent.com"
CUSTOM_MODS_DIR = CACHE_DIR / "custom_mods"           # verified jars, named by git blob sha
CUSTOM_MODS_STATE = APP_DIR / "custom_mods.json"
MC_TOKEN_RE = re.compile(r"(?:\+|mc[-_]?)(1\.\d{1,2}(?:\.\d{1,2})?)(?!\.?\d)", re.I)


def mc_parts(version):
    """'1.21.4' -> (1, 21, 4). Snapshots / unknown formats -> None."""
    text = str(version).strip()
    if re.fullmatch(r"\d+(?:\.\d+){0,3}", text):
        return tuple(int(x) for x in text.split("."))
    return None


def _cmp(a, b):
    n = max(len(a), len(b))
    a, b = tuple(a) + (0,) * (n - len(a)), tuple(b) + (0,) * (n - len(b))
    return (a > b) - (a < b)


def _term_ok(term, ver):
    """One Fabric-style version comparator: >=1.21 <1.21.1 1.21.x ~1.21.2 ^1.21 * 1.21.4"""
    term = term.strip().rstrip("-")             # '1.21-' is the pre-release marker; irrelevant for releases
    if term in ("", "*", "x", "X"):
        return True
    m = re.fullmatch(r"(>=|<=|>|<|=|~|\^)?v?(.+)", term)
    op, rest = (m.group(1) or ""), m.group(2)
    if re.search(r"(^|\.)[xX*](\.|$)", rest):    # wildcard such as 1.21.x
        prefix = []
        for part in rest.split("."):
            if part in ("x", "X", "*"):
                break
            if not part.isdigit():
                return False
            prefix.append(int(part))
        return tuple(ver[:len(prefix)]) == tuple(prefix)
    want = mc_parts(rest)
    if want is None:
        return False
    c = _cmp(ver, want)
    if op in ("", "="):
        return c == 0
    if op == ">=":
        return c >= 0
    if op == "<=":
        return c <= 0
    if op == ">":
        return c > 0
    if op == "<":
        return c < 0
    if op == "~":
        upper = (want[0], want[1] + 1) if len(want) >= 2 else (want[0] + 1,)
        return c >= 0 and _cmp(ver, upper) < 0
    if op == "^":
        return c >= 0 and _cmp(ver, (want[0] + 1,)) < 0
    return False


def _maven_ok(spec, ver):
    """Forge / NeoForge version ranges: [1.21,1.22)  [1.20.1,)  (,1.21]  1.21"""
    ranges = re.findall(r"[\[(][^\[\]()]*[\])]", spec)
    if not ranges:
        want = mc_parts(spec.strip())
        return want is not None and _cmp(ver, want) >= 0      # bare version = minimum
    for part in ranges:
        lo_inc, hi_inc, body = part[0] == "[", part[-1] == "]", part[1:-1]
        if "," not in body:
            want = mc_parts(body.strip())
            if want is not None and _cmp(ver, want) == 0:
                return True
            continue
        lo, hi = (x.strip() for x in body.split(",", 1))
        ok = True
        if lo:
            lo_v = mc_parts(lo)
            ok = lo_v is not None and (_cmp(ver, lo_v) >= 0 if lo_inc else _cmp(ver, lo_v) > 0)
        if ok and hi:
            hi_v = mc_parts(hi)
            ok = hi_v is not None and (_cmp(ver, hi_v) <= 0 if hi_inc else _cmp(ver, hi_v) < 0)
        if ok:
            return True
    return False


def mc_matches(pred, mc, style="fabric"):
    """True when Minecraft version `mc` satisfies the dependency predicate `pred` (str, list or None)."""
    ver = mc_parts(mc)
    if ver is None:
        return False
    if pred is None:
        return True                              # the mod does not restrict the Minecraft version
    if style == "maven":
        return _maven_ok(str(pred), ver)
    alternatives = pred if isinstance(pred, (list, tuple)) else [pred]
    for alt in alternatives:
        for branch in str(alt).split("||"):
            branch = re.sub(r"(>=|<=|>|<|=|~|\^)\s+", r"\1", branch.strip())
            if branch and all(_term_ok(t, ver) for t in branch.split()):
                return True
    return False


def git_blob_sha(path):
    """The sha1 GitHub reports for a file in the git tree (differs from the plain file sha1)."""
    size = Path(path).stat().st_size
    h = hashlib.sha1(f"blob {size}\0".encode())
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _natural_key(text):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", text.lower())]


def _mc_dependency(deps):
    """Extract the `minecraft` predicate from a fabric / quilt dependency block (None = unrestricted)."""
    if isinstance(deps, dict):
        return deps.get("minecraft")
    if isinstance(deps, list):                   # quilt: [{"id": "minecraft", "versions": ...}, "other"]
        for dep in deps:
            if isinstance(dep, dict) and dep.get("id") == "minecraft":
                v = dep.get("versions")
                return v if isinstance(v, (str, list)) else None
    return None


def read_jar_meta(path):
    """Reads mod metadata from a jar. Returns {id, version, env, loaders:[..], mc:{loader: predicate}} or None."""
    meta = {"id": "", "version": "", "env": "*", "loaders": [], "mc": {}}
    try:
        with zipfile.ZipFile(path) as z:
            def read(name):
                try:
                    return z.read(name)
                except KeyError:
                    return None

            raw = read("fabric.mod.json")
            if raw:
                data = json.loads(raw.decode("utf-8-sig"), strict=False)
                meta.update(id=str(data.get("id", "")), version=str(data.get("version", "")),
                            env=str(data.get("environment", "*")))
                meta["loaders"].append("fabric")
                meta["mc"]["fabric"] = _mc_dependency(data.get("depends", {}))
            raw = read("quilt.mod.json")
            if raw:
                data = json.loads(raw.decode("utf-8-sig"), strict=False).get("quilt_loader", {})
                meta["id"] = meta["id"] or str(data.get("id", ""))
                meta["version"] = meta["version"] or str(data.get("version", ""))
                meta["loaders"].append("quilt")
                meta["mc"]["quilt"] = _mc_dependency(data.get("depends", []))
            for loader, name in (("neoforge", "META-INF/neoforge.mods.toml"), ("forge", "META-INF/mods.toml")):
                raw = read(name)
                if raw and tomllib:
                    data = tomllib.loads(raw.decode("utf-8-sig"))
                    mods = data.get("mods") or [{}]
                    mid = str(mods[0].get("modId", ""))
                    meta["id"] = meta["id"] or mid
                    meta["version"] = meta["version"] or str(mods[0].get("version", ""))
                    meta["loaders"].append(loader)
                    pred = None
                    for dep in (data.get("dependencies", {}) or {}).get(mid, []):
                        if dep.get("modId") == "minecraft":
                            pred = dep.get("versionRange")
                    meta["mc"][loader] = pred
    except Exception:
        return None
    return meta if meta["loaders"] else None


def classify_repo_path(path):
    """Cheap classification from the path only (no download): Minecraft versions + loaders it names."""
    parts = path.split("/")
    name = parts[-1]
    mcs = {p for p in parts[:-1] if (mc_parts(p) or ()) and len(mc_parts(p)) >= 2}
    if not mcs:
        mcs = set(MC_TOKEN_RE.findall(name))
    loaders = {p.lower() for p in parts[:-1] if p.lower() in LOADERS}
    m = re.match(r"^(.*?)[-_+ ]v?\d", name[:-4])
    slug = re.sub(r"[_ ]", "-", (m.group(1) if m else name[:-4]).lower())
    return {"name": name, "slug": slug, "mcs": sorted(mcs), "loaders": sorted(loaders)}


class CustomMods:
    """Keeps the mods of a GitHub repo (default: greeko2030-afk/mods) installed in every matching instance.

    - one cheap API call per start (ETag => HTTP 304 costs no rate limit)
    - every jar is verified against the git blob sha before it is used
    - only files this class installed are ever updated or removed; mods the user added are never touched
    - if the user already has the same mod id installed, the user's copy wins (no duplicate-mod crash)
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.RLock()
        self._meta_lock = threading.Lock()
        self._local_cache = {}

    # -- persistent state ---------------------------------------------------------------
    def _load(self):
        try:
            return json.loads(CUSTOM_MODS_STATE.read_text("utf-8"))
        except Exception:
            return {}

    def _save(self, state):
        CUSTOM_MODS_STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CUSTOM_MODS_STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), "utf-8")
        os.replace(tmp, CUSTOM_MODS_STATE)

    @property
    def repo(self):
        return str(self.cfg.get("mods_repo") or "greeko2030-afk/mods").strip().strip("/")

    @property
    def ref(self):
        return str(self.cfg.get("mods_branch") or "").strip() or "HEAD"

    def info(self):
        st = self._load()
        return {"checked": st.get("checked", 0), "files": len(st.get("tree", [])),
                "installed": sum(len(v) for v in st.get("managed", {}).values())}

    # -- GitHub tree --------------------------------------------------------------------
    @staticmethod
    def _entry(item):
        path = item["path"]
        entry = classify_repo_path(path)
        entry.update(path=path, sha=item["sha"], size=int(item.get("size", 0)))
        return entry

    def _load_tree(self, state, network, report):
        key = f"{self.repo}@{self.ref}"
        if state.get("key") != key:                  # repo / branch changed in settings
            state.clear()
            state["key"] = key
        if network:
            headers = {"Accept": "application/vnd.github+json"}
            if state.get("etag") and state.get("tree") is not None:
                headers["If-None-Match"] = state["etag"]
            try:
                r = http_get(f"{GH_API}/repos/{self.repo}/git/trees/{self.ref}?recursive=1", headers=headers)
                if r.status_code == 304:
                    state["checked"] = time.time()
                elif r.status_code == 200:
                    data = r.json()
                    if data.get("truncated"):
                        report["errors"].append("Repository listing was truncated by GitHub (too many files)")
                    state["tree"] = [{"path": i["path"], "sha": i["sha"], "size": i.get("size", 0)}
                                     for i in data.get("tree", [])
                                     if i.get("type") == "blob" and i["path"].lower().endswith(".jar")
                                     and not i["path"].startswith(".github/")
                                     and not re.search(r"-(sources|dev|javadoc)\.jar$", i["path"], re.I)]
                    state["etag"] = r.headers.get("ETag", "")
                    state["checked"] = time.time()
                elif r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                    report["errors"].append("GitHub rate limit reached - using the saved list")
                else:
                    report["errors"].append(f"GitHub answered HTTP {r.status_code} - using the saved list")
            except (requests.RequestException, ValueError) as e:
                report["offline"] = True
                report["errors"].append(f"Could not reach GitHub ({type(e).__name__}) - using the saved list")
        if state.get("tree") is None:
            return None
        return [self._entry(i) for i in state["tree"]]

    # -- jar download / metadata ----------------------------------------------------------
    def _fetch(self, entry):
        """Returns the local path of the verified jar, downloading it first when needed."""
        dest = CUSTOM_MODS_DIR / f"{entry['sha']}.jar"
        if dest.exists() and dest.stat().st_size == entry["size"]:
            return dest
        CUSTOM_MODS_DIR.mkdir(parents=True, exist_ok=True)
        quoted = requests.utils.quote(entry["path"])
        sources = [(f"{GH_RAW}/{self.repo}/{self.ref}/{quoted}", {}),
                   (f"{GH_API}/repos/{self.repo}/git/blobs/{entry['sha']}",
                    {"Accept": "application/vnd.github.raw+json"})]      # fallback if the branch moved meanwhile
        last = None
        for url, headers in sources:
            tmp = dest.with_name(f"{dest.name}.{uuid.uuid4().hex[:8]}.part")
            try:
                digest = hashlib.sha1(f"blob {entry['size']}\0".encode())
                with http_get(url, headers=headers, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(1 << 18):
                            f.write(chunk)
                            digest.update(chunk)
                if digest.hexdigest() != entry["sha"]:
                    last = IOError(f"Checksum mismatch for {entry['name']}")
                    continue
                os.replace(tmp, dest)
                return dest
            except requests.RequestException as e:
                last = e
            finally:
                tmp.unlink(missing_ok=True)
        raise last or IOError(f"Could not download {entry['name']}")

    def _meta(self, state, entry):
        with self._meta_lock:
            cache = state.setdefault("meta", {})
            if entry["sha"] in cache:
                return cache[entry["sha"]] or None
            try:
                path = self._fetch(entry)
            except Exception:                    # noqa: BLE001 - no network: try again next time
                return None
            cache[entry["sha"]] = read_jar_meta(path) or {}      # {} = not a loadable mod, never retry
            return cache[entry["sha"]] or None

    # -- choosing the right file for an instance ------------------------------------------
    @staticmethod
    def _loader_ok(loader, meta):
        have = set(meta["loaders"])
        return loader in have or (loader == "quilt" and "fabric" in have)

    @staticmethod
    def _mc_ok(loader, meta, mc):
        pred = meta["mc"].get(loader, meta["mc"].get("fabric") if loader == "quilt" else None)
        return mc_matches(pred, mc, "maven" if loader in ("forge", "neoforge") else "fabric")

    def _pick(self, state, inst, items):
        mc = inst.mc
        series = tuple(mc_parts(mc)[:2])
        exact = [e for e in items if mc in e["mcs"]]
        plain = [e for e in items if not e["mcs"]]
        near = [e for e in items if e["mcs"] and mc not in e["mcs"]
                and any(tuple((mc_parts(t) or ())[:2]) == series for t in e["mcs"])]
        for pool, trust_name in ((exact, True), (plain, False), (near, False)):
            for e in sorted(pool, key=lambda x: _natural_key(x["name"]), reverse=True):
                if e["loaders"] and not (inst.loader in e["loaders"]
                                         or (inst.loader == "quilt" and "fabric" in e["loaders"])):
                    continue
                meta = self._meta(state, e)
                if not meta or not self._loader_ok(inst.loader, meta) or meta.get("env") == "server":
                    continue
                if trust_name or self._mc_ok(inst.loader, meta, mc):
                    return e, meta
        return None, None

    def _local_ids(self, inst, skip_names):
        """mod id -> filename for the jars the user put into the instance themselves."""
        found = {}
        if not inst.mods_dir.exists():
            return found
        for p in inst.mods_dir.glob("*.jar"):
            if p.name in skip_names:
                continue
            try:
                st = p.stat()
                key = (str(p), st.st_size, st.st_mtime_ns)
                if key not in self._local_cache:
                    self._local_cache[key] = (read_jar_meta(p) or {}).get("id", "")
                if self._local_cache[key]:
                    found[self._local_cache[key]] = p.name
            except OSError:
                continue
        return found

    # -- applying -------------------------------------------------------------------------
    def _apply(self, state, inst, tree, report):
        managed = state.setdefault("managed", {}).setdefault(inst.dir.name, {})
        if mc_parts(inst.mc) is None:
            return
        groups = {}
        for e in tree:
            groups.setdefault(e["slug"], []).append(e)
        local = self._local_ids(inst, set(managed))
        desired = {}
        for items in groups.values():
            entry, meta = self._pick(state, inst, items)
            if not entry:
                continue
            if meta["id"] in local:
                report["skipped"].append(f"{entry['name']} ({inst.name}: you already have {local[meta['id']]})")
                continue
            desired[entry["name"]] = entry
        # remove files this launcher installed earlier but that are no longer wanted (updated / removed upstream)
        for fname in [f for f in managed if f not in desired]:
            (inst.mods_dir / fname).unlink(missing_ok=True)
            managed.pop(fname, None)
            report["removed"].append(f"{fname} ({inst.name})")
        for fname, entry in desired.items():
            dest = inst.mods_dir / fname
            if managed.get(fname) == entry["sha"] and dest.exists():
                continue
            if dest.exists() and fname not in managed and git_blob_sha(dest) != entry["sha"]:
                report["skipped"].append(f"{fname} ({inst.name}: a different file with this name exists)")
                continue
            try:
                src = self._fetch(entry)
                inst.mods_dir.mkdir(parents=True, exist_ok=True)
                tmp = dest.with_name(f"{fname}.{uuid.uuid4().hex[:8]}.part")
                try:
                    _link_or_copy(src, tmp)
                    os.replace(tmp, dest)
                finally:
                    tmp.unlink(missing_ok=True)
                report["updated" if fname in managed else "installed"].append(f"{fname} ({inst.name})")
                managed[fname] = entry["sha"]
            except Exception as e:               # noqa: BLE001 - one bad file must not stop the rest
                report["errors"].append(f"{fname}: {e}")

    def sync(self, instances, network=True, progress=None, prune=False):
        """Checks the repo and installs / updates / removes mods in the given instances. Returns a report dict."""
        report = {"installed": [], "updated": [], "removed": [], "skipped": [], "errors": [],
                  "new_in_repo": [], "offline": False}
        with self.lock:
            state = self._load()
            old_paths = {t["path"] + "@" + t["sha"] for t in state.get("tree", [])}
            had_tree = bool(state.get("tree"))
            if progress:
                progress("Checking Supersonic mods repository...")
            tree = self._load_tree(state, network, report)
            if tree is None:
                report["errors"].append("No mod list available yet")
                return report
            if had_tree:
                report["new_in_repo"] = [t["name"] for t in tree if t["path"] + "@" + t["sha"] not in old_paths]
            for inst in instances:
                try:
                    if progress:
                        progress(f"Installing Supersonic mods into {inst.name}...")
                    self._apply(state, inst, tree, report)
                except Exception as e:           # noqa: BLE001
                    report["errors"].append(f"{inst.name}: {e}")
            # forget bookkeeping of instances that no longer exist
            names = {i.dir.name for i in instances}
            if prune:
                state["managed"] = {k: v for k, v in state.get("managed", {}).items() if k in names}
            self._save(state)
        return report

    def ensure(self, inst, progress=None):
        """Before launching: make sure this one instance has its mods. Uses the saved list when it is fresh."""
        state = self._load()
        fresh = time.time() - state.get("checked", 0) < 6 * 3600 and state.get("tree") is not None
        return self.sync([inst], network=not fresh, progress=progress)

    @staticmethod
    def summary(report):
        parts = []
        for key, word in (("installed", "installed"), ("updated", "updated"), ("removed", "removed")):
            if report.get(key):
                parts.append(f"{len(report[key])} {word}")
        return ", ".join(parts)



# ----------------------------------------------------------------------------
# OpenGL -> Direct3D 12 translation (Windows only, Mesa GLon12)
# ----------------------------------------------------------------------------
GH_MEDIA = "https://media.githubusercontent.com/media"
TRANSLATION_STATE = APP_DIR / "translation.json"
ENGINE_REQUIRED = ("opengl32.dll", "libgallium_wgl.dll")        # without these Mesa cannot start
ENGINE_FILES = ENGINE_REQUIRED + ("dxil.dll", "libglapi.dll", "libEGL.dll", "libGLESv1_CM.dll", "libGLESv2.dll")
TRANSLATION_MODES = ("Auto", "OpenGL", "D3D12")
TRANSLATION_FOLDERS = ("Hidden Folder (Default)", "Visible Folder")
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def _is_link(path):
    """True for symlinks AND Windows junctions (which Path.is_symlink() cannot see before Python 3.12)."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def rmtree_safe(path):
    """Delete a tree WITHOUT ever following links / junctions (shutil.rmtree could delete the real JRE)."""
    path = Path(path)
    if not os.path.lexists(path):
        return
    if _is_link(path):
        try:
            os.unlink(path)
        except OSError:
            os.rmdir(path)                      # Windows junction
        return
    if path.is_dir():
        for child in list(path.iterdir()):
            rmtree_safe(child)
        os.rmdir(path)
    else:
        try:
            path.unlink()
        except PermissionError:
            os.chmod(path, 0o666)
            path.unlink()


def _dir_link(link, target):
    """Directory link without admin rights: NTFS junction on Windows, symlink elsewhere (copy as last resort)."""
    link, target = Path(link), Path(target)
    try:
        if platform.system() == "Windows":
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                               capture_output=True, creationflags=NO_WINDOW, timeout=20)
            if r.returncode == 0:
                return
        else:
            os.symlink(target, link, target_is_directory=True)
            return
    except (OSError, subprocess.SubprocessError):
        pass
    shutil.copytree(target, link, symlinks=False)


def _pe_machine(path):
    """CPU architecture of a Windows DLL / EXE ('x64', 'arm64', 'x86') or None."""
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
        off = int.from_bytes(head[0x3C:0x40], "little")
        if head[off:off + 4] != b"PE\0\0":
            return None
        return {0x8664: "x64", 0xAA64: "arm64", 0x14C: "x86"}.get(int.from_bytes(head[off + 4:off + 6], "little"))
    except OSError:
        return None


def _host_arch():
    return {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine().lower(), "x86")


def d3d12_capable():
    """True when this Windows PC can create a Direct3D 12 device (feature level 11_0). Safe to call anywhere."""
    if platform.system() != "Windows":
        return False
    try:
        import ctypes

        class GUID(ctypes.Structure):
            _fields_ = [("a", ctypes.c_uint32), ("b", ctypes.c_uint16), ("c", ctypes.c_uint16), ("d", ctypes.c_ubyte * 8)]

        iid = GUID(0x189819F1, 0x1DB6, 0x4B57, (ctypes.c_ubyte * 8)(0xBE, 0x54, 0x18, 0x21, 0x33, 0x9B, 0x85, 0xF7))
        fn = ctypes.windll.d3d12.D3D12CreateDevice
        fn.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(GUID), ctypes.c_void_p]
        fn.restype = ctypes.c_long
        return fn(None, 0xB000, ctypes.byref(iid), None) == 0       # NULL out-pointer = capability check only
    except Exception:
        return False


class Translation:
    """Runs Minecraft through Mesa's OpenGL-on-D3D12 layer.

    Windows loads opengl32.dll from the folder of the .exe before System32, so the translation layer is put next
    to a private copy of the JVM launcher (a "shadow JRE" made of links - almost no disk space). Everything the
    translation needs and produces (engine DLLs, shadow JRE, translated shader cache) lives in ONE folder that
    is hidden by default; the real Java installation is never modified.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.last_note = ""                 # human readable reason of the last decision
        self._d3d12 = None

    # -- settings / paths ---------------------------------------------------------------
    @staticmethod
    def supported():
        return platform.system() == "Windows"

    def mode(self):
        value = str(self.cfg.get("translation_mode", "Auto"))
        return value if value in TRANSLATION_MODES else "Auto"

    @property
    def hidden(self):
        return not str(self.cfg.get("translation_folder", "")).startswith("Visible")

    @property
    def root(self):
        return APP_DIR / (".translation" if self.hidden else "translation")

    @property
    def cache_dir(self):
        return self.root / "cache"

    def _prepare_root(self):
        self.root.mkdir(parents=True, exist_ok=True)
        if platform.system() == "Windows":
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(self.root))
                if attrs != -1:
                    new = (attrs | FILE_ATTRIBUTE_HIDDEN) if self.hidden else (attrs & ~FILE_ATTRIBUTE_HIDDEN)
                    ctypes.windll.kernel32.SetFileAttributesW(str(self.root), new)
            except Exception:
                pass

    def _state(self):
        try:
            return json.loads(TRANSLATION_STATE.read_text("utf-8"))
        except Exception:
            return {}

    def _save_state(self, data):
        try:
            TRANSLATION_STATE.write_text(json.dumps(data), "utf-8")
        except OSError:
            pass

    def reset_state(self):
        """Forget an automatic OpenGL fallback (called when the user changes the mode or asks to retry)."""
        self._save_state({})

    def d3d12_available(self):
        if self._d3d12 is None:
            self._d3d12 = d3d12_capable()
        return self._d3d12

    # -- engine files ------------------------------------------------------------------
    def _engine_sources(self):
        dirs = [APP_DIR / "engine"]
        if getattr(sys, "frozen", False):
            dirs.append(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "engine")
            dirs.append(Path(sys.executable).parent / "engine")
        dirs += [Path(__file__).resolve().parent / "engine", Path.cwd() / "engine"]
        return [d for d in dirs if d.is_dir()]

    def engine_dir(self):
        return self.root / "engine"

    def engine_missing(self):
        return [n for n in ENGINE_REQUIRED if not (self.engine_dir() / n).is_file()]

    def engine_signature(self):
        parts = []
        for n in ENGINE_FILES:
            p = self.engine_dir() / n
            if p.is_file():
                st = p.stat()
                parts.append(f"{n}:{st.st_size}:{st.st_mtime_ns}")
        return hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]

    def _download_engine_file(self, repo, ref, item, dest):
        """Download one engine file from GitHub, verified (git blob sha, or sha256 when stored with Git LFS)."""
        quoted = requests.utils.quote(item["path"])
        tmp = dest.with_name(f"{dest.name}.{uuid.uuid4().hex[:8]}.part")
        try:
            if int(item.get("size", 0)) < 400:                    # tiny file: maybe a Git LFS pointer
                r = http_get(f"{GH_API}/repos/{repo}/git/blobs/{item['sha']}",
                             headers={"Accept": "application/vnd.github.raw+json"})
                r.raise_for_status()
                if r.content.startswith(b"version https://git-lfs"):
                    oid = re.search(rb"oid sha256:([0-9a-f]{64})", r.content).group(1).decode()
                    url, digest, expected = f"{GH_MEDIA}/{repo}/{ref}/{quoted}", hashlib.sha256(), oid
                else:
                    tmp.write_bytes(r.content)
                    url = None
            else:
                url = f"{GH_RAW}/{repo}/{ref}/{quoted}"
                digest = hashlib.sha1(f"blob {item['size']}\0".encode())
                expected = item["sha"]
            if url:
                with http_get(url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(1 << 18):
                            f.write(chunk)
                            digest.update(chunk)
                if digest.hexdigest() != expected:
                    raise IOError(f"Checksum mismatch for {dest.name}")
            os.replace(tmp, dest)
        finally:
            tmp.unlink(missing_ok=True)

    def ensure_engine(self, status=None):
        """Collects the engine DLLs into the translation folder (bundled copy first, then GitHub). Returns missing list."""
        eng = self.engine_dir()
        eng.mkdir(parents=True, exist_ok=True)
        for src_dir in self._engine_sources():
            for name in ENGINE_FILES:
                src, dst = src_dir / name, eng / name
                if src.is_file() and src.stat().st_size > 0 and not (dst.is_file() and dst.stat().st_size == src.stat().st_size):
                    shutil.copyfile(src, dst)
        missing = self.engine_missing()
        if not missing:
            return []
        repo = str(self.cfg.get("engine_repo") or "greeko2030-afk/Supersonic-Client")
        if status:
            status("Downloading D3D12 translation engine...")
        try:
            r = http_get(f"{GH_API}/repos/{repo}/git/trees/HEAD?recursive=1")
            r.raise_for_status()
            wanted = {n.lower() for n in ENGINE_FILES}
            items = [i for i in r.json().get("tree", [])
                     if i.get("type") == "blob" and i["path"].lower().startswith("engine/")
                     and i["path"].count("/") == 1 and i["path"].split("/")[-1].lower() in wanted
                     and not (eng / i["path"].split("/")[-1]).is_file()]
            for item in items:
                self._download_engine_file(repo, "HEAD", item, eng / item["path"].split("/")[-1])
        except Exception:                        # noqa: BLE001 - reported through the missing list below
            pass
        return self.engine_missing()

    # -- shadow JRE --------------------------------------------------------------------
    def _link_file(self, src, dst):
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)

    def _shadow_jre(self, java_exe):
        java_exe = Path(java_exe).resolve()
        home = java_exe.parent.parent
        st = java_exe.stat()
        key = hashlib.sha1(f"{home}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:10]
        dst = self.root / "jre" / key
        shadow_exe = dst / "bin" / java_exe.name
        marker = dst / ".ready"
        sig = self.engine_signature()
        if marker.is_file() and shadow_exe.exists() and marker.read_text("utf-8") == sig:
            return shadow_exe
        rmtree_safe(dst)
        (dst / "bin").mkdir(parents=True)
        for entry in home.iterdir():                          # lib, conf, legal, release ... are shared by link
            if entry.name == "bin":
                continue
            target = dst / entry.name
            _dir_link(target, entry) if entry.is_dir() else self._link_file(entry, target)
        for entry in (home / "bin").iterdir():
            target = dst / "bin" / entry.name
            _dir_link(target, entry) if entry.is_dir() else self._link_file(entry, target)
        for name in ENGINE_FILES:                             # the translation layer sits next to java(w).exe
            src = self.engine_dir() / name
            if src.is_file():
                target = dst / "bin" / name
                if os.path.lexists(target):
                    target.unlink()
                self._link_file(src, target)
        marker.write_text(sig, "utf-8")
        return shadow_exe

    # -- decision ----------------------------------------------------------------------
    def describe(self):
        """Short status for the settings page."""
        if not self.supported():
            return "Windows only - not used on this system"
        if not self.d3d12_available():
            return "No Direct3D 12 GPU found - OpenGL is used"
        missing = self.engine_missing()
        if missing and not any((d / n).is_file() for d in self._engine_sources() for n in missing):
            return "Direct3D 12 detected - engine files will be downloaded on first use"
        return "Direct3D 12 detected - ready"

    def plan(self, java_exe, status=None):
        """Returns {'mode','java','env'} to run Minecraft through D3D12, or None for plain OpenGL (reason in last_note)."""
        self.last_note = ""
        mode = self.mode()
        if not self.supported():
            self.last_note = "Translation is Windows-only"
            return None
        if mode == "OpenGL":
            self.last_note = "OpenGL selected"
            return None
        state = self._state()
        if mode == "Auto" and state.get("auto_off") and state.get("sig") == self.engine_signature():
            self.last_note = "D3D12 crashed earlier - Auto switched to OpenGL (choose D3D12 to retry)"
            return None
        if not self.d3d12_available():
            self.last_note = "No Direct3D 12 capable GPU found - using OpenGL"
            return None
        java = shutil.which(str(java_exe)) if not Path(str(java_exe)).is_absolute() else str(java_exe)
        if not java or not Path(java).is_file():
            self.last_note = "Java executable not found - using OpenGL"
            return None
        try:
            self._prepare_root()
            missing = self.ensure_engine(status)
            if missing:
                self.last_note = f"Translation engine incomplete (missing {', '.join(missing)}) - using OpenGL"
                return None
            arch = _pe_machine(self.engine_dir() / "opengl32.dll")
            if arch and arch != _host_arch():
                self.last_note = f"Engine is {arch} but this PC is {_host_arch()} - using OpenGL"
                return None
            if status:
                status("Preparing D3D12 translation...")
            shadow = self._shadow_jre(java)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:                   # noqa: BLE001 - never block the game because of the optional layer
            self.last_note = f"Translation setup failed ({e}) - using OpenGL"
            return None
        env = {
            "GALLIUM_DRIVER": "d3d12",
            "MESA_SHADER_CACHE_DIR": str(self.cache_dir),
            "MESA_GLSL_CACHE_DIR": str(self.cache_dir),
            "MESA_SHADER_CACHE_MAX_SIZE": "1G",
        }
        self.last_note = "Using OpenGL -> D3D12 translation"
        return {"mode": "D3D12", "java": str(shadow), "env": env}

    def record_launch(self, plan_used, crashed_early):
        """Called by the UI after a game run. An early crash while translating makes Auto fall back to OpenGL."""
        if not plan_used or not crashed_early:
            return False
        if self.mode() == "Auto":
            self._save_state({"auto_off": True, "sig": self.engine_signature(), "time": time.time()})
            return True
        return False

    def clear(self):
        """Deletes translated files (shader cache + shadow JRE). Engine DLLs stay. Returns bytes freed."""
        freed = 0
        for base in (APP_DIR / ".translation", APP_DIR / "translation"):
            for sub in ("cache", "jre"):
                path = base / sub
                if path.exists():
                    if sub == "cache":
                        freed += dir_size(path)
                    rmtree_safe(path)
        return freed



class Launcher:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.Lock()
        self.translation = Translation(cfg)

    # -- fast launch path: a version that was installed once is not re-verified / re-downloaded --
    @staticmethod
    def _key(inst):
        return f"{inst.mc}|{inst.loader}|{inst.loader_version}"

    @staticmethod
    def _ready():
        try:
            return json.loads(READY_FILE.read_text("utf-8"))
        except Exception:
            return {}

    def is_ready(self, inst):
        vid = self._ready().get(self._key(inst))
        if not vid:
            return None
        ok = (MC_ROOT / "versions" / vid / f"{vid}.json").exists() and \
             (MC_ROOT / "versions" / inst.mc / f"{inst.mc}.jar").exists()
        return vid if ok else None

    def invalidate(self, inst):
        ready = self._ready()
        if ready.pop(self._key(inst), None):
            READY_FILE.write_text(json.dumps(ready), "utf-8")

    def prepare(self, inst, status=lambda s: None, progress=lambda f: None):
        """Install Minecraft + loader once. Later calls return instantly. Safe to call from several threads."""
        with self.lock:
            vid = self.is_ready(inst)
            if vid:
                return vid
            MC_ROOT.mkdir(parents=True, exist_ok=True)
            cb = make_cb(status, progress)
            status(f"Checking Minecraft {inst.mc}...")
            mll.install.install_minecraft_version(inst.mc, str(MC_ROOT), callback=cb)
            status(f"Preparing {inst.loader.title()}...")
            vid = self.install_loader(inst, cb)
            ready = self._ready()
            ready[self._key(inst)] = vid
            READY_FILE.write_text(json.dumps(ready), "utf-8")
            return vid

    def java_major(self, version_id):
        try:
            data = json.loads((MC_ROOT / "versions" / version_id / f"{version_id}.json").read_text("utf-8"))
            if "javaVersion" in data:
                return int(data["javaVersion"]["majorVersion"])
            if "inheritsFrom" in data:
                return self.java_major(data["inheritsFrom"])
        except Exception:
            pass
        return 17

    def jvm_args(self, java):
        ram = int(self.cfg.get("ram_mb", 8192))
        mode = self.cfg.get("perf_mode", "")
        args = [f"-Xmx{ram}M", f"-Xms{min(ram, 2048)}M", "-Dfile.encoding=UTF-8",
                "-Djava.net.preferIPv4Stack=true", "-XX:+DisableExplicitGC", "-XX:-UsePerfData",
                "-Xshare:auto"]
        if mode.startswith("Low"):
            return args
        if java >= 21:
            args.append("-XX:+UseZGC")
            if java < 24:                       # generational ZGC flag only exists on Java 21-23
                args.append("-XX:+ZGenerational")
        else:
            args += G1_FLAGS                    # ZGenerational would crash Java 17 (Minecraft 1.18-1.20.4)
        # NOTE: no -XX:+AlwaysPreTouch - it touches the whole heap at start and adds seconds to every launch.
        if platform.system() == "Darwin":
            args.append("-XstartOnFirstThread")
        return args

    def _pick(self, prefix, mc, lver):
        installed = [v["id"] for v in mll.utils.get_installed_versions(str(MC_ROOT))]
        if lver and f"{prefix}-{lver}-{mc}" in installed:
            return f"{prefix}-{lver}-{mc}"
        matches = sorted(i for i in installed if i.startswith(prefix) and i.endswith(f"-{mc}"))
        if not matches:
            raise RuntimeError(f"{prefix} install for {mc} not found")
        return matches[-1]

    def install_loader(self, inst, cb):
        root, mc, loader, lver = str(MC_ROOT), inst.mc, inst.loader, inst.loader_version or None
        if loader == "vanilla":
            return mc
        if loader == "fabric":
            mll.fabric.install_fabric(mc, root, loader_version=lver, callback=cb)
            return self._pick("fabric-loader", mc, lver)
        if loader == "quilt":
            mll.quilt.install_quilt(mc, root, loader_version=lver, callback=cb)
            return self._pick("quilt-loader", mc, lver)
        if loader == "forge":
            fv = f"{mc}-{lver}" if lver else mll.forge.find_forge_version(mc)
            if not fv:
                raise RuntimeError(f"No Forge build found for {mc}")
            mll.forge.install_forge_version(fv, root, callback=cb)
            return mll.forge.forge_to_installed_version(fv)
        if loader == "neoforge":
            if not hasattr(mll, "mod_loader"):
                raise RuntimeError("NeoForge needs: pip install -U minecraft-launcher-lib")
            ml = mll.mod_loader.get_mod_loader("neoforge")
            ml.install(mc, root, loader_version=lver, callback=cb)
            return ml.get_installed_version(mc, lver)
        raise RuntimeError(f"Unknown loader: {loader}")

    def launch(self, inst, status, progress, server=None):
        inst.dir.mkdir(parents=True, exist_ok=True)
        version_id = self.prepare(inst, status, progress)      # instant when already installed
        options = {
            "username": self.cfg.get("username"), "uuid": self.cfg.offline_uuid(), "token": "",
            "jvmArguments": self.jvm_args(self.java_major(version_id)),
            "launcherName": "Supersonic Client", "launcherVersion": "2.6.0",
            "gameDirectory": str(inst.dir),
        }
        if server:
            host, _, port = server.partition(":")
            options["server"] = host
            if port:
                options["port"] = port
        cmd = mll.command.get_minecraft_command(version_id, str(MC_ROOT), options)
        plan = self.translation.plan(cmd[0], status)          # None = plain OpenGL
        env = None
        if plan:
            cmd[0] = plan["java"]
            env = dict(os.environ, **plan["env"])
        status("Starting game...")
        log = open(inst.dir / "launcher_output.log", "wb")
        proc = subprocess.Popen(cmd, cwd=str(inst.dir), stdout=log, stderr=subprocess.STDOUT,
                                creationflags=NO_WINDOW, env=env)
        proc.translation = plan["mode"] if plan else None     # read by the UI (crash fallback, log line)
        proc.translation_note = self.translation.last_note
        return proc


# ----------------------------------------------------------------------------
# Agent: rule-based diagnostics (real checks, no LLM)
# ----------------------------------------------------------------------------
CRASH_HINTS = [
    ("OutOfMemoryError", "Out of memory - raise the RAM allocation in Settings > Performance."),
    ("UnsupportedClassVersionError", "Wrong Java version for this Minecraft / mod version."),
    ("ModResolutionException", "A mod is missing a dependency or targets another Minecraft version."),
    ("Incompatible mod set", "Incompatible mods detected - check the mods listed in the log."),
    ("Mixin apply failed", "Two mods conflict (Mixin error) - remove the most recently added mod."),
]


class Agent:
    def __init__(self, cfg):
        self.cfg = cfg

    def respond(self, message):
        m = message.lower()
        ram = total_ram_gb()
        if any(k in m for k in ("scan", "fix", "error", "crash", "problem", "bug")):
            return "Running a full scan on your current instance...", "scan"
        if any(k in m for k in ("fps", "lag", "optim", "slow", "perform", "boost")):
            return "I'll install the essential performance addons for your current instance.", "essentials"
        if "ram" in m or "memory" in m:
            rec = int(min(8192, (ram * 1024) // 2 // 1024 * 1024)) if ram else 4096
            return f"You have {ram:.1f} GB total. Recommended allocation: {rec} MB.", None
        if "modpack" in m:
            return "Open the Modpacks tab, pick one and press Install. I can recommend one if you tell me the style you like.", None
        return "I can scan for crashes, fix broken mods, optimize FPS and tune RAM. Try: 'scan', 'boost fps' or 'how much ram'.", None

    def diagnose(self, text):
        for needle, hint in CRASH_HINTS:
            if needle in text:
                return hint
        m = re.search(r"Caused by: (.+)", text)
        return f"Cause found in log: {m.group(1)[:140]}" if m else None

    def scan(self, inst):
        results = []
        if shutil.which("java") or (MC_ROOT / "runtime").exists():
            results.append(("ok", "Java runtime available"))
        else:
            results.append(("warn", "No Java yet - it will be downloaded on first launch"))

        seen = {}
        for jar in sorted(inst.mods_dir.glob("*.jar")):
            bad, mod_id = False, None
            try:
                with zipfile.ZipFile(jar) as z:
                    bad = z.testzip() is not None
                    if not bad and "fabric.mod.json" in z.namelist():
                        mod_id = json.loads(z.read("fabric.mod.json").decode("utf-8", "ignore"),
                                            strict=False).get("id")
            except Exception:
                bad = True
            if bad:
                self._quarantine(jar, inst)
                results.append(("fix", f"Quarantined corrupt mod: {jar.name}"))
            elif mod_id in seen:
                older = min(seen[mod_id], jar, key=lambda p: p.stat().st_mtime)
                self._quarantine(older, inst)
                results.append(("fix", f"Disabled duplicate mod '{mod_id}': {older.name}"))
                if older == seen[mod_id]:
                    seen[mod_id] = jar
            elif mod_id:
                seen[mod_id] = jar

        ram = total_ram_gb()
        alloc = int(self.cfg.get("ram_mb", 8192))
        if ram and alloc > ram * 1024 * 0.75:
            new = int(ram * 1024 * 0.5) // 1024 * 1024
            self.cfg.set("ram_mb", max(new, 2048))
            results.append(("fix", f"RAM allocation {alloc} MB was too high for {ram:.0f} GB - set to {max(new, 2048)} MB"))
        else:
            results.append(("ok", f"RAM allocation OK ({alloc} MB)"))

        text = ""
        crashes = sorted((inst.dir / "crash-reports").glob("*.txt"), key=lambda p: p.stat().st_mtime) \
            if (inst.dir / "crash-reports").exists() else []
        if crashes:
            text = crashes[-1].read_text("utf-8", "ignore")
        elif (inst.dir / "launcher_output.log").exists():
            text = (inst.dir / "launcher_output.log").read_text("utf-8", "ignore")[-6000:]
        hint = self.diagnose(text) if text else None
        results.append(("warn", hint) if hint else ("ok", "No crash signatures found in latest logs"))
        return results

    @staticmethod
    def _quarantine(jar, inst):
        dest = inst.dir / "mods_disabled"
        dest.mkdir(exist_ok=True)
        shutil.move(str(jar), str(dest / jar.name))
