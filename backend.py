"""Supersonic Client - backend: config, Modrinth / CurseForge APIs, instances, launching, agent."""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests
import minecraft_launcher_lib as mll

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

MR_API = "https://api.modrinth.com/v2"
CF_API = "https://api.curseforge.com/v1"
UA = {"User-Agent": "greeko-afk/Supersonic-Client/2.5.0 (github.com/greeko-afk/Supersonic-Client)"}
LOADERS = ("fabric", "forge", "neoforge", "quilt")
CF_LOADER_ID = {"forge": 1, "fabric": 4, "quilt": 5, "neoforge": 6}
NO_WINDOW = 0x08000000 if platform.system() == "Windows" else 0

DEFAULTS = {
    "username": "Raffiee_playssMC", "ram_mb": 8192, "perf_mode": "Ultra (Recommended)",
    "language": "English", "theme": "Dark (Default)", "start_with_windows": False,
    "minimize_to_tray": True, "confirm_exit": True, "preload_assets": True, "smart_memory": True,
    "optimize_launcher": True, "java_version": "Auto", "auto_java": True, "native_libs": True,
    "keep_launcher_open": True, "check_updates": True, "download_updates": True,
    "beta_updates": False, "analytics": False, "crash_reports": True, "download_limit": "Unlimited",
    "max_connections": 16, "verify_downloads": True, "delete_temp": "Always", "cloud_sync": True,
    "sync_devices": True, "curseforge_key": "", "selected_instance": "Supersonic Main", "servers": [],
    "website_url": "https://supersonic-client--greeko2030.replit.app",
    "github_url": "https://github.com/greeko-afk/Supersonic-Client",
    "discord_url": "https://discord.com",
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


def http_get(url, **kw):
    headers = dict(UA)
    headers.update(kw.pop("headers", {}))
    kw.setdefault("timeout", 15)
    return requests.get(url, headers=headers, **kw)


def download(url, dest, sha1=None):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    digest = hashlib.sha1()
    with http_get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                digest.update(chunk)
    if sha1 and digest.hexdigest().lower() != sha1.lower():
        tmp.unlink(missing_ok=True)
        raise IOError(f"Hash mismatch for {dest.name}")
    os.replace(tmp, dest)


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
        return bool(info) and (self.mods_dir / info["filename"]).exists()


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
            "icon": h.get("icon_url"),
        }

    def projects(self, slugs):
        r = http_get(f"{MR_API}/projects", params={"ids": json.dumps(slugs)})
        r.raise_for_status()
        return {p["slug"]: p for p in r.json()}

    def best_version(self, ident, mc, loader):
        loaders = [loader] + (["fabric"] if loader == "quilt" else [])
        params = {"game_versions": json.dumps([mc]), "loaders": json.dumps(loaders)}
        r = http_get(f"{MR_API}/project/{ident}/version", params=params)
        if r.status_code == 404:
            hits, _ = self.search(ident, "mod", limit=1)
            if not hits:
                return None
            r = http_get(f"{MR_API}/project/{hits[0]['slug']}/version", params=params)
        r.raise_for_status()
        versions = r.json()
        if not versions:
            return None
        return next((v for v in versions if v["version_type"] == "release"), versions[0])

    def install_mod(self, ident, inst, status=lambda s: None, _seen=None):
        """Install a mod plus its required dependencies into the instance. Returns file info or None."""
        seen = _seen if _seen is not None else set()
        if ident in seen:
            return None
        seen.add(ident)
        version = self.best_version(ident, inst.mc, inst.loader)
        if not version:
            return None
        for dep in version.get("dependencies", []):
            if dep.get("dependency_type") == "required" and dep.get("project_id"):
                self.install_mod(dep["project_id"], inst, status, seen)
        f = next((x for x in version["files"] if x.get("primary")), version["files"][0])
        status(f"Downloading {f['filename']}...")
        download(f["url"], inst.mods_dir / f["filename"], f["hashes"].get("sha1"))
        return {"filename": f["filename"], "version": version["version_number"]}

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

    def _headers(self):
        key = self.cfg.get("curseforge_key", "").strip()
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

    def search(self, query="", sort=2, version=None, loader=None, offset=0, limit=8):
        params = {"gameId": 432, "classId": 4471, "searchFilter": query, "sortField": sort,
                  "sortOrder": "desc", "index": offset, "pageSize": limit}
        if version:
            params["gameVersion"] = version
        if loader:
            params["modLoaderType"] = CF_LOADER_ID.get(loader)
        data = self.get("/mods/search", **params)
        return [self._norm(m) for m in data["data"]], data["pagination"]["totalCount"]

    @staticmethod
    def _norm(m):
        idx = (m.get("latestFilesIndexes") or [{}])[0]
        shots = m.get("screenshots") or []
        logo = (m.get("logo") or {}).get("thumbnailUrl")
        return {
            "source": "curseforge", "id": m["id"], "slug": m["slug"], "title": m["name"],
            "author": (m.get("authors") or [{}])[0].get("name", ""), "summary": m.get("summary", ""),
            "mc": idx.get("gameVersion", "?"), "file_id": idx.get("fileId"),
            "tags": [c["name"] for c in m.get("categories", [])][:3],
            "downloads": m.get("downloadCount", 0), "rating": m.get("thumbsUpCount", 0),
            "thumb": shots[0]["thumbnailUrl"] if shots else logo, "icon": logo,
        }


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


class Launcher:
    def __init__(self, cfg):
        self.cfg = cfg

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
                "-Djava.net.preferIPv4Stack=true", "-XX:+DisableExplicitGC"]
        if mode.startswith("Low"):
            return args
        if java >= 21:
            args.append("-XX:+UseZGC")
            if java < 24:                       # generational ZGC flag only exists on Java 21-23
                args.append("-XX:+ZGenerational")
        else:
            args += G1_FLAGS                    # ZGenerational would crash Java 17 (Minecraft 1.18-1.20.4)
        if mode.startswith("Ultra") and self.cfg.get("preload_assets"):
            args.append("-XX:+AlwaysPreTouch")
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
        MC_ROOT.mkdir(parents=True, exist_ok=True)
        inst.dir.mkdir(parents=True, exist_ok=True)
        cb = make_cb(status, progress)
        status(f"Checking Minecraft {inst.mc}...")
        mll.install.install_minecraft_version(inst.mc, str(MC_ROOT), callback=cb)
        status(f"Preparing {inst.loader.title()}...")
        version_id = self.install_loader(inst, cb)
        options = {
            "username": self.cfg.get("username"), "uuid": self.cfg.offline_uuid(), "token": "",
            "jvmArguments": self.jvm_args(self.java_major(version_id)),
            "launcherName": "Supersonic Client", "launcherVersion": "2.5.0",
            "gameDirectory": str(inst.dir),
        }
        if server:
            host, _, port = server.partition(":")
            options["server"] = host
            if port:
                options["port"] = port
        status("Starting game...")
        cmd = mll.command.get_minecraft_command(version_id, str(MC_ROOT), options)
        log = open(inst.dir / "launcher_output.log", "wb")
        return subprocess.Popen(cmd, cwd=str(inst.dir), stdout=log, stderr=subprocess.STDOUT,
                                creationflags=NO_WINDOW)


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
