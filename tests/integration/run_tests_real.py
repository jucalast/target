#!/usr/bin/env python3
"""
Script para executar testes de integração end-to-end com fluxo real.

Este script facilita a execução dos testes que validam o fluxo completo
do sistema sem mocks intermediários, testando as dependências reais
entre os módulos.

Uso:
    python run_real_flow_tests.py --all          # Todos os testes
    python run_real_flow_tests.py --main         # Teste principal
    python run_real_flow_tests.py --dependencies # Testes de dependência
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header(title):
    """Imprime cabeçalho formatado."""
    print(f"\n{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}\n")

def print_success(message):
    """Imprime mensagem de sucesso."""
    print(f"✅ {message}")

def print_error(message):
    """Imprime mensagem de erro."""
    print(f"❌ {message}")

def print_info(message):
    """Imprime mensagem informativa."""
    print(f"ℹ️  {message}")

def run_pytest(test_pattern=None, description="", extra_args=None):
    """Executa pytest com padrão específico."""
    print_header(f"EXECUTANDO: {description}")
    
    cmd = [
        "pytest", 
        "tests/integration/test_end_to_end_flow.py",
        "-v", "-s", "--tb=short"
    ]
    
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    if extra_args:
        cmd.extend(extra_args)
    
    print_info(f"Comando: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd)
        success = result.returncode == 0
        if success:
            print_success(f"{description} - SUCESSO!")
        else:
            print_error(f"{description} - FALHOU!")
        return success
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
        return False
    except Exception as e:
        print_error(f"Erro ao executar: {e}")
        return False

def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print_header("TESTES DE INTEGRAÇÃO END-TO-END REAIS")
        print("Uso:")
        print("  python run_real_flow_tests.py --all              # Todos os testes")
        print("  python run_real_flow_tests.py --main             # Teste principal")
        print("  python run_real_flow_tests.py --dependencies     # Testes de dependência")
        print("  python run_real_flow_tests.py --consistency      # Testes de consistência")
        print("  python run_real_flow_tests.py --resilience       # Testes de resiliência")
        print("  python run_real_flow_tests.py --external         # Testes com APIs externas")
        print("  python run_real_flow_tests.py --detailed         # Todos com logs detalhados")
        print()
        print("Exemplos:")
        print("  python run_real_flow_tests.py --main")
        print("  python run_real_flow_tests.py --all")
        print("  python run_real_flow_tests.py --dependencies")
        return 1
    
    test_type = sys.argv[1].lower()
    
    # Verificar se estamos no diretório correto
    if not Path("tests/integration/test_end_to_end_flow.py").exists():
        print_error("Execute este script a partir do diretório raiz do projeto!")
        return 1
    
    success = True
    
    if test_type == "--all":
        success = run_pytest(None, "TODOS OS TESTES DE INTEGRAÇÃO")
    
    elif test_type == "--main":
        success = run_pytest(
            "test_fluxo_completo_real_sem_mocks_intermediarios",
            "TESTE PRINCIPAL - FLUXO COMPLETO REAL"
        )
    
    elif test_type == "--dependencies":
        success = run_pytest(
            "test_dependencia_sequencial_dados",
            "TESTES DE DEPENDÊNCIA ENTRE MÓDULOS"
        )
    
    elif test_type == "--consistency":
        success = run_pytest(
            "test_consistencia_dados_intermediarios",
            "TESTES DE CONSISTÊNCIA DE DADOS"
        )
    
    elif test_type == "--resilience":
        success = run_pytest(
            "test_erro_propagacao_sem_falha_total",
            "TESTES DE RESILIÊNCIA A FALHAS"
        )
    
    elif test_type == "--external":
        success = run_pytest(
            "test_integração_completa_ibge_real or test_scraping_noticias_real or test_pipeline_completo_com_fontes_externas",
            "TESTES DE INTEGRAÇÃO COM APIS EXTERNAS"
        )
    
    elif test_type == "--detailed":
        success = run_pytest(
            None,
            "TODOS OS TESTES COM LOGS DETALHADOS",
            ["--log-cli-level=INFO", "-vv"]
        )
    
    else:
        print_error(f"Opção desconhecida: {test_type}")
        print_info("Use --help ou execute sem argumentos para ver as opções")
        return 1
    
    # Resumo
    print_header("RESUMO DA EXECUÇÃO")
    if success:
        print_success("🎉 Testes executados com sucesso!")
        print_info("O sistema está funcionando corretamente end-to-end")
        print_info("As dependências entre módulos estão validadas")
    else:
        print_error("😞 Alguns testes falharam!")
        print_info("Consulte os logs acima e a documentação em README_REAL_FLOW.md")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
