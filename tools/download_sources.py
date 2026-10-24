"""Download official data with resumable ranges; BACH microscopy only (no WSI)."""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import tarfile
import threading
import time
import urllib.request
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "data/downloads"
RAW = ROOT / "data/raw"
UA = "FrameView-Academic-Dataset-Preparation/1.0"
URLS = {
    "BreakHis": "https://www.inf.ufpr.br/vri/databases/BreaKHis_v1.tar.gz",
    "CRC": "https://zenodo.org/records/1214456/files/CRC-VAL-HE-7K.zip?download=1",
    "BACH": "https://zenodo.org/records/3632035/files/ICIAR2018_BACH_Challenge.zip?download=1",
}

def request(url, start=None, end=None):
    headers = {"User-Agent": UA}
    if start is not None:
        headers["Range"] = f"bytes={start}-{end}"
    for attempt in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
                if start is not None and r.status != 206:
                    raise RuntimeError(f"Server ignored Range: {r.status}")
                data = r.read()
                if start is not None and len(data) != end-start+1:
                    raise RuntimeError("Truncated range")
                return data
        except Exception:
            if attempt == 6:
                raise
            time.sleep(min(60, 2**attempt + 1))

def size_of(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])

def download(url, dest, md5=None, workers=3, range_start=0):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = size_of(url)-range_start
    if dest.exists() and dest.stat().st_size == total:
        if not md5 or hashlib.file_digest(dest.open("rb"), "md5").hexdigest() == md5:
            return dest
    chunks = dest.parent / (dest.name + ".chunks")
    chunks.mkdir(exist_ok=True)
    step = 32 * 1024**2
    starts = list(range(0, total, step))
    done = 0
    def one(start):
        end = min(total-1, start+step-1)
        p = chunks / f"{start:012d}"
        if not p.exists() or p.stat().st_size != end-start+1:
            content = request(url, range_start+start, range_start+end)
            p.with_suffix(".tmp").write_bytes(content)
            p.with_suffix(".tmp").replace(p)
        return end-start+1
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for n in pool.map(one, starts):
            done += n
            print(f"DOWNLOAD {dest.name}: {done/1024**2:.0f}/{total/1024**2:.0f} MiB", flush=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with tmp.open("wb") as out:
        for start in starts:
            with (chunks/f"{start:012d}").open("rb") as inp:
                shutil.copyfileobj(inp, out, 8*1024**2)
    if md5:
        with tmp.open("rb") as f:
            actual = hashlib.file_digest(f, "md5").hexdigest()
        if actual != md5:
            raise RuntimeError(f"Checksum mismatch: {dest.name}: {actual}")
    tmp.replace(dest)
    # Only files created in this function's dedicated chunk directory are removed.
    for start in starts:
        (chunks/f"{start:012d}").unlink()
    chunks.rmdir()
    return dest

def safe_dest(root, name):
    parts = PurePosixPath(name.replace("\\", "/")).parts
    if any(x in {"..", ":"} or ":" in x for x in parts) or name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe archive path: {name}")
    p = root.joinpath(*parts)
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError(name)
    return p

class RemoteZip(io.RawIOBase):
    def __init__(self, url):
        self.url, self.length, self.pos = url, size_of(url), 0
        self.tail = DOWNLOADS/"BACH_microscopy_zip_tail.bin"
        self.base = 6564182477
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, n, whence=0):
        self.pos = n if whence == 0 else self.pos+n if whence == 1 else self.length+n
        return self.pos
    def read(self, n=-1):
        if self.pos >= self.length: return b""
        end = self.length-1 if n < 0 else min(self.length-1, self.pos+n-1)
        if end < self.pos: return b""
        if self.tail.exists() and self.tail.stat().st_size == self.length-self.base and self.pos>=self.base:
            with self.tail.open('rb') as f:
                f.seek(self.pos-self.base)
                data=f.read(end-self.pos+1)
        else:
            data = request(self.url, self.pos, end)
        self.pos = end+1
        return data

def bach(catalog_only=False):
    remote = RemoteZip(URLS["BACH"])
    with zipfile.ZipFile(remote) as z:
        entries = z.infolist()
    catalog = [{"name": x.filename, "bytes": x.file_size, "compressed": x.compress_size,
                "offset": x.header_offset} for x in entries]
    (DOWNLOADS/"bach_archive_catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    selected = [x for x in entries if "/photos/" in x.filename.lower() and
                x.filename.lower().endswith((".tif", ".tiff", ".txt", ".csv"))]
    print("BACH_CATALOG", json.dumps({"entries": len(entries), "selected": len(selected),
          "selected_bytes": sum(x.file_size for x in selected), "examples": catalog[:12]}), flush=True)
    if catalog_only: return
    images = [x for x in selected if x.filename.lower().endswith((".tif", ".tiff"))]
    if len(images) != 400:
        raise RuntimeError(f"Expected 400 microscopy images, found {len(images)}; inspect catalog")
    def one(info):
        target = safe_dest(RAW/"BACH", info.filename)
        if target.exists() and target.stat().st_size == info.file_size:
            with target.open("rb") as f:
                if zlib.crc32(f.read()) & 0xffffffff == info.CRC:
                    return info.filename
        # Local header + compressed data. Filename/extra lengths are bounded by ZIP u16.
        start = info.header_offset
        remote.seek(start)
        head = remote.read(30)
        if head[:4] != b"PK\x03\x04": raise ValueError("Bad ZIP local header")
        name_len, extra_len = struct.unpack_from("<HH", head, 26)
        begin = start+30+name_len+extra_len
        remote.seek(begin)
        packed = remote.read(info.compress_size)
        content = zlib.decompress(packed, -15) if info.compress_type == zipfile.ZIP_DEFLATED else packed
        if len(content) != info.file_size or zlib.crc32(content)&0xffffffff != info.CRC:
            raise ValueError(f"ZIP CRC failed: {info.filename}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.with_suffix(target.suffix+".part").write_bytes(content)
        target.with_suffix(target.suffix+".part").replace(target)
        if not remote.tail.exists():
            time.sleep(1.1)  # stay below Zenodo's shared request limit
        return info.filename
    # Sequential HTTP: each member uses two ranges, < 120 requests/minute.
    for i, info in enumerate(selected, 1):
        one(info)
        if i%10 == 0: print(f"BACH_EXTRACT {i}/{len(selected)}", flush=True)

def breakhis():
    archive = download(URLS["BreakHis"], DOWNLOADS/"BreaKHis_v1.tar.gz")
    with tarfile.open(archive, "r:gz") as t:
        n = 0
        for entry in t:
            if not entry.isfile(): continue
            target = safe_dest(RAW/"BreakHis", entry.name)
            if target.exists() and target.stat().st_size == entry.size: continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with t.extractfile(entry) as inp, target.open("wb") as out:
                shutil.copyfileobj(inp, out)
            n += 1
        print("BREAKHIS_EXTRACTED", n, flush=True)

def crc():
    archive = download(URLS["CRC"], DOWNLOADS/"CRC-VAL-HE-7K.zip", "2fd1651b4f94ebd818ebf90ad2b6ce06", workers=2)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            target = safe_dest(RAW/"CRC-VAL-HE-7K", info.filename)
            if target.exists() and target.stat().st_size == info.file_size: continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as inp, target.open("wb") as out:
                shutil.copyfileobj(inp, out)
    print("CRC_EXTRACTED", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["bach-catalog", "bach", "bach-tail", "breakhis", "crc"])
    args = parser.parse_args()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    def bach_tail():
        catalog=json.loads((DOWNLOADS/'bach_archive_catalog.json').read_text())
        base=min(x['offset'] for x in catalog if '/Photos/' in x['name'])
        if base != 6564182477:raise ValueError('BACH archive version changed')
        download(URLS['BACH'],DOWNLOADS/'BACH_microscopy_zip_tail.bin',workers=8,range_start=base)
        bach()
    {"bach-catalog": lambda: bach(True), "bach": bach, "bach-tail":bach_tail,
     "breakhis": breakhis, "crc": crc}[args.source]()

if __name__ == "__main__": main()
