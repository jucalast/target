"""
Script para buscar e armazenar em cache dados do IBGE para consultas comuns.

Este script é usado para popular o cache com dados frequentemente acessados,
melhorando o desempenho das consultas durante o desenvolvimento e produção.
"""

from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ibge.sidra_connector import SIDRAClient, SIDRAService, \

    SIDRAQueryParams

def setup_cache_directories():
"""Configura os diretórios de cache necessários."""
    cache_dir = Path("./cache/ibge")
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_types = ["pof", "pnad", "censo", "outros"]
    for cache_type in cache_types:
    (cache_dir / cache_type).mkdir(exist_ok=True)
    return cache_dir

def fetch_common_queries(service: SIDRAService, cache_dir: Path):
"""Busca e armazena em cache consultas comuns ao IBGE."""
    logger.info("Iniciando busca de consultas comuns...")

    locations = ["brasil", "são paulo", "rio de janeiro", "minas gerais"]

    age_ranges = [
    (15, 24),
    (25, 39),
    (40, 59),
    (60, 100)
]

    for location in locations:
    for age_range in age_ranges:
    cache_file =
                cache_dir / "pof" / f"pop_{location}_{age_range[0]}_{\
                age_range[1]}.json"
            if not cache_file.exists():
            try:
            logger.info(f"Buscando dados populacionais para {location}, \
                        faixa {age_range[0]}-{age_range[1]} anos")
                    data = service.get_population_by_age_range(location, \
                        age_range)
                    with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                logger.error(f"Erro ao buscar dados para {location}, \
                        {age_range}: {str(e)}")

    for location in locations:
    cache_file = cache_dir / "pof" / f"cultura_{location}.json"
        if not cache_file.exists():
        try:
        logger.info(\
                    f"Buscando dados de consumo cultural para {location}")
                data = service.get_consumer_behavior(location)
                with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
            logger.error(\
                    f"Erro ao buscar dados de cultura para {location}: {str(\
                        e)}")

    for location in locations:
    cache_file = cache_dir / "pnad" / f"renda_{location}.json"
        if not cache_file.exists():
        try:
        logger.info(\
                    f"Buscando dados de distribuição de renda para {location}")
                data = service.get_income_distribution(location)
                with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
            logger.error(\
                    f"Erro ao buscar dados de renda para {location}: {str(e)}")
    logger.info("Busca de consultas comuns concluída.")

def main():
"""Função principal do script."""
    try:

        cache_dir = setup_cache_directories()

        client = SIDRAClient(
            cache_enabled=True,
            cache_dir=cache_dir,
            cache_ttl_days=30
        )
        service = SIDRAService(client=client)

        fetch_common_queries(service, cache_dir)
        logger.info("Script de busca de dados do IBGE concluído com sucesso!")
    except Exception as e:
    logger.error(f"Erro durante a execução do script: {str(e)}", \
            exc_info=True)
        sys.exit(1)
if __name__ == "__main__":
main()
