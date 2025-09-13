#!/usr/bin/env python3
import os,subprocess,urllib.request,tarfile,shutil,pathlib

node_version="22.16.0"
node_dist=f"https://nodejs.org/dist/v{node_version}/node-v{node_version}-linux-x64.tar.xz"
home=pathlib.Path.home()
local_dir=home/".local"
node_dir=local_dir/f"node-v{node_version}-linux-x64"
bin_dir=local_dir/"bin"
repo=pathlib.Path(__file__).resolve().parent

def run(cmd,cwd=None):
    subprocess.run(cmd,shell=True,check=True,cwd=cwd)

def ensure_node():
    if not (node_dir/"bin"/"node").exists():
        local_dir.mkdir(parents=True,exist_ok=True)
        archive=local_dir/f"node-v{node_version}-linux-x64.tar.xz"
        if not archive.exists():
            urllib.request.urlretrieve(node_dist,archive)
        with tarfile.open(archive,"r:xz") as f:
            f.extractall(path=local_dir)
    os.environ["PATH"]=f"{node_dir/'bin'}:"+os.environ.get("PATH","")

def ensure_pnpm():
    if not (bin_dir/"pnpm").exists():
        run(f"{node_dir/'bin'/'npm'} install pnpm@10.12.1 -g --prefix {local_dir}")
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
