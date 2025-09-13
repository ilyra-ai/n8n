#!/usr/bin/env python3
import os,subprocess,urllib.request,tarfile,shutil,pathlib,json

home=pathlib.Path.home()
local_dir=home/".local"
bin_dir=local_dir/"bin"
repo=pathlib.Path(__file__).resolve().parent
node_dir=None

def run(cmd,cwd=None):
    subprocess.run(cmd,shell=True,check=True,cwd=cwd)

def latest_node():
    data=json.loads(urllib.request.urlopen("https://nodejs.org/dist/index.json").read().decode())
    for e in data:
        if e.get("lts"):
            v=e["version"]
            f=f"node-{v}-linux-x64.tar.xz"
            return v,f"https://nodejs.org/dist/{v}/{f}"

def ensure_node():
    global node_dir
    v,u=latest_node()
    node_dir=local_dir/f"node-{v}-linux-x64"
    if not (node_dir/"bin"/"node").exists():
        local_dir.mkdir(parents=True,exist_ok=True)
        a=local_dir/f"node-{v}-linux-x64.tar.xz"
        if not a.exists():
            urllib.request.urlretrieve(u,a)
        with tarfile.open(a,"r:xz") as f:
            f.extractall(path=local_dir)
    os.environ["PATH"]=f"{node_dir/'bin'}:"+os.environ.get("PATH","")

def ensure_pnpm():
    if not (bin_dir/"pnpm").exists():
        run(f"{node_dir/'bin'/'npm'} install pnpm -g --prefix {local_dir}")
    os.environ["PATH"]=f"{bin_dir}:"+os.environ.get("PATH","")

def build():
    run("pnpm build:deploy",cwd=repo)

def pack():
    compiled=repo/"compiled"
    shutil.copytree(node_dir,compiled/"node",dirs_exist_ok=True)
    archive=repo/"n8n"
    if (archive.with_suffix('.zip')).exists():
        (archive.with_suffix('.zip')).unlink()
    shutil.make_archive(str(archive),"zip",root_dir=compiled)

if __name__=="__main__":
    ensure_node()
    ensure_pnpm()
    build()
    pack()
