#!/usr/bin/env python3

import os
import subprocess
import urllib.request
import tarfile  
import shutil
import pathlib
import json
import sys
import logging
import hashlib
from typing import Tuple, Optional

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações globais
home = pathlib.Path.home()
local_dir = home / ".local"
bin_dir = local_dir / "bin"
repo = pathlib.Path(__file__).resolve().parent
node_dir = None


def run_command(cmd: str, cwd: Optional[pathlib.Path] = None, capture_output: bool = False) -> Optional[str]:
    """
    Executa um comando shell com tratamento de erro melhorado
    """
    try:
        logger.info(f"Executando comando: {cmd}")
        if cwd:
            logger.info(f"Diretório: {cwd}")
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            cwd=cwd,
            capture_output=capture_output,
            text=True
        )
        
        if capture_output:
            return result.stdout.strip()
        return None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao executar comando '{cmd}': {e}")
        logger.error(f"Código de saída: {e.returncode}")
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"Erro stderr: {e.stderr}")
        raise


def download_with_progress(url: str, destination: pathlib.Path) -> None:
    """
    Download de arquivo com indicador de progresso
    """
    logger.info(f"Baixando {url} para {destination}")
    
    def progress_hook(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, (block_num * block_size * 100) // total_size)
            print(f"\rProgresso: {percent}%", end='', flush=True)
    
    try:
        urllib.request.urlretrieve(url, destination, progress_hook)
        print()  # Nova linha após o progresso
        logger.info(f"Download concluído: {destination}")
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        if destination.exists():
            destination.unlink()
        raise


def verify_file_integrity(file_path: pathlib.Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verifica a integridade do arquivo baixado
    """
    if not file_path.exists():
        return False
    
    if expected_hash:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return file_hash == expected_hash
    
    # Se não há hash esperado, apenas verifica se o arquivo não está vazio
    return file_path.stat().st_size > 0


def get_latest_node_lts() -> Tuple[str, str]:
    """
    Obtém a versão LTS mais recente do Node.js
    """
    logger.info("Buscando versão LTS mais recente do Node.js...")
    
    try:
        with urllib.request.urlopen("https://nodejs.org/dist/index.json") as response:
            data = json.loads(response.read().decode())
        
        for entry in data:
            if entry.get("lts"):
                version = entry["version"]
                filename = f"node-{version}-linux-x64.tar.xz"
                url = f"https://nodejs.org/dist/{version}/{filename}"
                logger.info(f"Versão LTS encontrada: {version}")
                return version, url
                
    except Exception as e:
        logger.error(f"Erro ao buscar versão do Node.js: {e}")
        # Fallback para uma versão conhecida
        logger.info("Usando versão fallback do Node.js")
        version = "v20.18.0"  # Versão LTS estável conhecida
        filename = f"node-{version}-linux-x64.tar.xz"
        url = f"https://nodejs.org/dist/{version}/{filename}"
        return version, url
    
    raise RuntimeError("Não foi possível determinar a versão LTS do Node.js")


def ensure_node():
    """
    Garante que o Node.js esteja instalado localmente
    """
    global node_dir
    
    logger.info("Verificando instalação do Node.js...")
    
    version, url = get_latest_node_lts()
    node_dir = local_dir / f"node-{version}-linux-x64"
    node_binary = node_dir / "bin" / "node"
    
    if node_binary.exists():
        logger.info(f"Node.js já instalado em {node_dir}")
        # Verifica se a versão está funcionando
        try:
            installed_version = run_command(f"{node_binary} --version", capture_output=True)
            logger.info(f"Versão instalada: {installed_version}")
        except:
            logger.warning("Node.js instalado mas não funcional, reinstalando...")
            shutil.rmtree(node_dir, ignore_errors=True)
    
    if not node_binary.exists():
        logger.info("Instalando Node.js...")
        local_dir.mkdir(parents=True, exist_ok=True)
        
        archive_name = f"node-{version}-linux-x64.tar.xz"
        archive_path = local_dir / archive_name
        
        # Download do arquivo se necessário
        if not archive_path.exists() or not verify_file_integrity(archive_path):
            download_with_progress(url, archive_path)
        
        # Extração
        logger.info(f"Extraindo {archive_path}...")
        try:
            with tarfile.open(archive_path, "r:xz") as tar_file:
                tar_file.extractall(path=local_dir)
            logger.info("Extração concluída")
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            # Remove arquivo corrompido
            if archive_path.exists():
                archive_path.unlink()
            raise
        
        # Verifica se a instalação foi bem-sucedida
        if not node_binary.exists():
            raise RuntimeError("Falha na instalação do Node.js")
    
    # Atualiza PATH
    node_bin_path = str(node_dir / "bin")
    current_path = os.environ.get("PATH", "")
    if node_bin_path not in current_path:
        os.environ["PATH"] = f"{node_bin_path}:{current_path}"
        logger.info(f"PATH atualizado com {node_bin_path}")


def ensure_pnpm():
    """
    Garante que o pnpm esteja instalado
    """
    logger.info("Verificando instalação do pnpm...")
    
    pnpm_binary = bin_dir / "pnpm"
    
    if pnpm_binary.exists():
        try:
            version = run_command(f"{pnpm_binary} --version", capture_output=True)
            logger.info(f"pnpm já instalado, versão: {version}")
        except:
            logger.warning("pnpm instalado mas não funcional, reinstalando...")
            pnpm_binary.unlink(missing_ok=True)
    
    if not pnpm_binary.exists():
        logger.info("Instalando pnpm...")
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        npm_binary = node_dir / "bin" / "npm"
        if not npm_binary.exists():
            raise RuntimeError("npm não encontrado. Instale o Node.js primeiro.")
        
        # Instala pnpm globalmente
        run_command(f"{npm_binary} install pnpm@latest -g --prefix {local_dir}")
        
        if not pnpm_binary.exists():
            raise RuntimeError("Falha na instalação do pnpm")
        
        logger.info("pnpm instalado com sucesso")
    
    # Atualiza PATH
    bin_path = str(bin_dir)
    current_path = os.environ.get("PATH", "")
    if bin_path not in current_path:
        os.environ["PATH"] = f"{bin_path}:{current_path}"
        logger.info(f"PATH atualizado com {bin_path}")


def check_project_structure():
    """
    Verifica se a estrutura do projeto está correta
    """
    logger.info("Verificando estrutura do projeto...")
    
    package_json = repo / "package.json"
    if not package_json.exists():
        raise RuntimeError(f"package.json não encontrado em {repo}")
    
    logger.info("Estrutura do projeto OK")


def build_project():
    """
    Executa o build do projeto
    """
    logger.info("Iniciando build do projeto...")
    
    check_project_structure()
    
    # Instala dependências se necessário
    node_modules = repo / "node_modules"
    if not node_modules.exists():
        logger.info("Instalando dependências...")
        run_command("pnpm install", cwd=repo)
    
    # Executa o build
    run_command("pnpm build:deploy", cwd=repo)
    logger.info("Build concluído")


def create_package():
    """
    Cria o pacote final
    """
    logger.info("Criando pacote final...")
    
    compiled_dir = repo / "compiled"
    
    # Remove diretório compilado anterior se existir
    if compiled_dir.exists():
        shutil.rmtree(compiled_dir)
    
    compiled_dir.mkdir(parents=True, exist_ok=True)
    
    # Copia Node.js para o pacote
    node_target = compiled_dir / "node"
    if node_dir and node_dir.exists():
        logger.info(f"Copiando Node.js de {node_dir} para {node_target}")
        shutil.copytree(node_dir, node_target, dirs_exist_ok=True)
    else:
        raise RuntimeError("Diretório do Node.js não encontrado")
    
    # Cria arquivo ZIP
    archive_name = repo / "n8n"
    zip_file = archive_name.with_suffix('.zip')
    
    if zip_file.exists():
        logger.info(f"Removendo arquivo anterior: {zip_file}")
        zip_file.unlink()
    
    logger.info(f"Criando arquivo ZIP: {zip_file}")
    shutil.make_archive(str(archive_name), "zip", root_dir=compiled_dir)
    
    if zip_file.exists():
        file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"Pacote criado com sucesso: {zip_file} ({file_size:.2f} MB)")
    else:
        raise RuntimeError("Falha na criação do pacote")


def cleanup_temp_files():
    """
    Remove arquivos temporários
    """
    logger.info("Limpando arquivos temporários...")
    
    temp_files = [
        local_dir / "node-*.tar.xz",
    ]
    
    for pattern in temp_files:
        for file_path in local_dir.glob(pattern.name):
            if file_path.is_file():
                file_path.unlink()
                logger.info(f"Removido: {file_path}")


def main():
    """
    Função principal
    """
    try:
        logger.info("=== Iniciando processo de build e empacotamento ===")
        
        # Verifica se estamos no diretório correto
        if not (repo / "package.json").exists():
            logger.error("Este script deve ser executado no diretório raiz do projeto")
            sys.exit(1)
        
        # Execução das etapas principais
        ensure_node()
        ensure_pnpm()
        build_project()
        create_package()
        
        logger.info("=== Processo concluído com sucesso ===")
        
        # Opcional: limpar arquivos temporários
        cleanup_choice = input("Deseja remover arquivos temporários? (y/N): ").lower()
        if cleanup_choice == 'y':
            cleanup_temp_files()
        
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()