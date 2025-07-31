#!/usr/bin/env python3
"""
Script para corrigir automaticamente problemas de sintaxe e indentação em arquivos Python.
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

class PythonFileFixer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines: List[str] = []
        self.modified = False
        self.errors: List[str] = []

    def fix_issues(self) -> bool:
        """Corrige os problemas no arquivo e retorna True se houve alterações."""
        if not os.path.exists(self.file_path):
            self.errors.append(f"Arquivo não encontrado: {self.file_path}")
            return False

        try:
            # Lê o conteúdo do arquivo
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()

            # Tenta compilar para verificar erros de sintaxe
            try:
                compile(''.join(self.lines), self.file_path, 'exec')
                return False  # Sem erros de sintaxe
            except SyntaxError as e:
                original_error = str(e)
                
            # Aplica as correções
            original_lines = self.lines.copy()
            
            # Tenta corrigir os erros de sintaxe mais comuns
            self.fix_missing_blocks()
            self.fix_indentation()
            self.fix_trailing_commas()
            self.fix_unterminated_strings()
            
            # Verifica se o arquivo foi modificado
            if self.lines != original_lines:
                # Tenta compilar novamente para verificar se as correções funcionaram
                try:
                    compile(''.join(self.lines), self.file_path, 'exec')
                    self.modified = True
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        f.writelines(self.lines)
                    print(f"✅ Corrigido: {self.file_path}")
                    return True
                except SyntaxError as e:
                    self.errors.append(f"Não foi possível corrigir {self.file_path}: {e}")
                    return False
            
            return False
            
        except Exception as e:
            self.errors.append(f"Erro ao processar {self.file_path}: {e}")
            return False
    
    def fix_missing_blocks(self) -> None:
        """Corrige blocos de classe/função sem conteúdo."""
        i = 0
        while i < len(self.lines):
            line = self.lines[i].rstrip()
            
            # Verifica se é uma definição de classe ou função
            if (line.lstrip().startswith(('class ', 'def ')) and 
                line.endswith(':') and 
                not line.lstrip().startswith(('def __', 'def _'))):
                
                # Verifica se a próxima linha não está indentada ou está vazia
                if (i + 1 >= len(self.lines) or 
                    not self.lines[i+1].strip() or 
                    not self.lines[i+1].startswith(' ')):
                    
                    # Adiciona 'pass' com a indentação correta
                    indent = ' ' * (len(line) - len(line.lstrip()))
                    self.lines.insert(i+1, f"{indent}    pass\n")
                    i += 1  # Pula a linha que acabamos de adicionar
            
            i += 1
    
    def fix_indentation(self) -> None:
        """Corrige problemas de indentação."""
        # Remove linhas vazias no início do arquivo
        while self.lines and not self.lines[0].strip():
            self.lines.pop(0)
        
        # Remove linhas vazias no final do arquivo
        while self.lines and not self.lines[-1].strip():
            self.lines.pop()
        
        # Garante que haja exatamente uma linha em branco no final do arquivo
        if self.lines and not self.lines[-1].endswith('\n'):
            self.lines[-1] = self.lines[-1].rstrip() + '\n'
        self.lines.append('\n')
    
    def fix_trailing_commas(self) -> None:
        """Corrige vírgulas finais sem parênteses."""
        for i in range(len(self.lines)):
            line = self.lines[i].rstrip()
            if line.endswith(','):
                # Verifica se há um parêntese de abertura antes da vírgula
                if '(' in line and ')' not in line[line.rfind('('):]:
                    # Encontra a próxima linha não vazia
                    j = i + 1
                    while j < len(self.lines) and not self.lines[j].strip():
                        j += 1
                    
                    if j < len(self.lines):
                        # Adiciona parêntese de fechamento na próxima linha não vazia
                        indent = ' ' * (len(self.lines[j]) - len(self.lines[j].lstrip()))
                        self.lines[j] = f"{indent}){self.lines[j].lstrip()}"
    
    def fix_unterminated_strings(self) -> None:
        """Corrige strings não terminadas."""
        for i in range(len(self.lines)):
            line = self.lines[i].rstrip()
            
            # Verifica aspas triplas não fechadas
            if '"""' in line and line.count('"""') % 2 != 0:
                self.lines[i] = line + '"""\n'
            # Verifica aspas simples triplas não fechadas
            if "'''" in line and line.count("'''") % 2 != 0:
                self.lines[i] = line + "'''\n"

def find_python_files(directory: str) -> List[str]:
    """Encontra todos os arquivos Python no diretório, ignorando venv e __pycache__."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Ignora diretórios específicos
        dirs[:] = [d for d in dirs if d not in ('venv', '.venv', '__pycache__', '.git')]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Função principal."""
    if len(sys.argv) != 2:
        print("Uso: python fix_python_files.py <diretório>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Erro: '{directory}' não é um diretório válido.")
        sys.exit(1)
    
    print(f"🔍 Procurando arquivos Python em {directory}...")
    python_files = find_python_files(directory)
    
    if not python_files:
        print("Nenhum arquivo Python encontrado.")
        return
    
    print(f"🔧 Corrigindo {len(python_files)} arquivos...")
    fixed_count = 0
    
    for file_path in python_files:
        fixer = PythonFileFixer(file_path)
        if fixer.fix_issues():
            fixed_count += 1
    
    print(f"✅ Concluído! {fixed_count}/{len(python_files)} arquivos foram modificados.")

if __name__ == "__main__":
    main()
