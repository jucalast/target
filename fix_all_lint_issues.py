#!/usr/bin/env python3
"""
Script para corrigir automaticamente problemas de formatação em arquivos Python.
Corrige:
1. Linhas em branco com espaços em branco (W293)
2. Falta de linha em branco no final do arquivo (W292)
3. Número incorreto de linhas em branco entre funções/classes (E302)
"""

import os
import re
import sys
from pathlib import Path


def fix_whitespace_in_blank_lines(content):
    """Remove espaços em branco de linhas em branco."""
    lines = content.splitlines(True)
    fixed_lines = []

    for line in lines:
        # Se a linha contém apenas espaços em branco, substitui por uma linha vazia
        if line.strip() == '':
            fixed_lines.append('\n')
        else:
            fixed_lines.append(line)

    return ''.join(fixed_lines)


def ensure_newline_at_end(content):
    """Garante que o arquivo termine com exatamente uma nova linha."""
    # Remove múltiplas linhas em branco no final
    content = content.rstrip('\n')
    # Adiciona exatamente uma nova linha no final
    return content + '\n'


def fix_blank_lines_between_functions(content):
    """Garante que haja duas linhas em branco entre funções/classes de nível superior."""
    lines = content.splitlines(True)
    fixed_lines = []
    in_function = False

    for i, line in enumerate(lines):
        # Verifica se é o início de uma função/classe
        if re.match(r'^(def|class)\s+', line.strip()):
            # Se não for a primeira linha do arquivo e não houver duas linhas em branco antes
            if i > 0 and not (len(lines[i-1].strip()) == 0 and (i == 1 or len(lines[i-2].strip()) == 0)):
                # Adiciona linhas em branco se necessário
                if len(fixed_lines) > 0 and fixed_lines[-1].strip() != '':
                    fixed_lines.append('\n')
                if len(fixed_lines) > 1 and fixed_lines[-2].strip() != '':
                    fixed_lines.append('\n')
            in_function = True

        fixed_lines.append(line)

        # Verifica se é o final de uma função/classe
        if line.strip() == '' and i > 0 and in_function:
            in_function = False

    return ''.join(fixed_lines)


def process_file(file_path):
    """Processa um único arquivo, aplicando todas as correções."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Aplica as correções em sequência
        content = fix_whitespace_in_blank_lines(content)
        content = fix_blank_lines_between_functions(content)
        content = ensure_newline_at_end(content)

        # Escreve as alterações de volta ao arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Corrigido: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {str(e)}")
        return False


def should_skip_directory(directory_name):
    """Verifica se o diretório deve ser ignorado."""
    skip_dirs = {
        'venv', '.venv', 'env', '.env',  # Ambientes virtuais
        '.git', '.github', '.gitlab',     # Controle de versão
        '__pycache__', '.pytest_cache',   # Cache do Python
        'node_modules',                   # Dependências do Node.js
        'build', 'dist', '*.egg-info',    # Arquivos de build
        'migrations'                      # Migrações de banco de dados
    }
    return directory_name in skip_dirs or any(directory_name.startswith('.') for d in skip_dirs if d.startswith('*'))


def find_python_files(directory):
    """Encontra todos os arquivos Python no diretório especificado, ignorando diretórios específicos."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Remove diretórios que devem ser ignorados
        dirs[:] = [d for d in dirs if not should_skip_directory(d)]

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # Verifica se o caminho contém algum diretório a ser ignorado
                if not any(part.startswith('.') or part in {'venv', 'env', '__pycache__'} 
                         for part in file_path.split(os.sep)):
                    python_files.append(file_path)
    return python_files


def main():
    # Diretório raiz do projeto (pode ser personalizado)
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # Encontra todos os arquivos Python
    python_files = find_python_files(root_dir)

    if not python_files:
        print("Nenhum arquivo Python encontrado.")
        return

    print(f"🔍 Encontrados {len(python_files)} arquivos Python para verificação...")

    # Processa cada arquivo
    success_count = 0
    for file_path in python_files:
        if process_file(file_path):
            success_count += 1

    print(f"\n✅ Concluído! {success_count}/{len(python_files)} arquivos processados com sucesso.")

if __name__ == "__main__":
    main()
