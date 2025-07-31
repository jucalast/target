# Integração com o IBGE

Este documento descreve como utilizar a integração com a API do IBGE para obtenção de dados públicos, como a PNAD Contínua e a POF (Pesquisa de Orçamentos Familiares).

## Visão Geral

O sistema utiliza a API SIDRA do IBGE para acessar dados públicos de forma programática. A implementação inclui: 

- **SIDRAClient**: Cliente de baixo nível para a API SIDRA
- **SIDRAMapper**: Mapeia conceitos de negócio para códigos SIDRA
- **SIDRAService**: Camada de serviço de alto nível para consultas comuns
- **Endpoints REST**: API para integração com o frontend

## Instalação

Certifique-se de que todas as dependências estejam instaladas:

```bash
pip install -r requirements.txt
```

## Configuração

### Variáveis de Ambiente

O sistema utiliza as seguintes variáveis de ambiente:

- `SIDRA_CACHE_DIR`: Diretório para armazenamento em cache (opcional, padrão: `.cache/sidra`)
- `SIDRA_CACHE_TTL_DAYS`: Tempo de vida do cache em dias (opcional, padrão: 7)

### Mapeamento de Conceitos

O arquivo `data/ibge/mappings/sidra_mappings.json` contém o mapeamento de conceitos para códigos SIDRA. Você pode adicionar novos conceitos seguindo o formato existente.

## Uso

### Consultando Dados por Conceito

```python
from app.services.ibge import SIDRAService

# Criar uma instância do serviço
service = SIDRAService()

# Obter dados para um conceito
df = await service.get_concept_data(
    concept="jovens_adultos",  # Conceito definido no mapeamento
    location="sp",             # Sigla do estado ou 'brasil'
    period="last"              # 'last' para o período mais recente
)
```

### Obtendo Perfil Demográfico

```python
# Obter perfil demográfico
profile = await service.get_demographic_profile(
    age_range=(18, 39),        # Faixa etária
    education_level="superior", # Nível de instrução (opcional)
    location="rj",             # Localização (opcional)
    period="last"              # Período (opcional)
)
```

## API REST

### Consulta Genérica

```http
POST /api/v1/ibge/query
Content-Type: application/json

{
  "concept": "jovens_adultos",
  "location": "sp",
  "period": "last"
}
```

### Consulta Demográfica

```http
POST /api/v1/ibge/demographic
Content-Type: application/json

{
  "age_range": [18, 39],
  "education_level": "superior_completo",
  "location": "rj",
  "period": "last"
}
```

## Testes

Para executar os testes de integração:

```bash
pytest tests/test_integration_ibge.py -v --log-cli-level=INFO
```

## Estrutura do Projeto

```
app/
  services/
    ibge/
      __init__.py         # Exporta as classes principais
      sidra_connector.py  # Implementação do cliente SIDRA
  api/
    endpoints/
      ibge.py             # Endpoints da API
  schemas/
    ibge.py              # Modelos Pydantic

data/
  ibge/
    mappings/
      sidra_mappings.json # Mapeamento de conceitos

tests/
  test_integration_ibge.py # Testes de integração
  conftest.py             # Configuração de testes
```

## Solução de Problemas

### Erro 429 (Too Many Requests)

A API do IBGE tem limites de taxa. O cliente implementa retry automático, mas é recomendado:

1. Habilitar o cache
2. Evitar consultas desnecessárias
3. Usar períodos mais longos quando possível

### Dados Desatualizados

O cache é armazenado por 7 dias por padrão. Para forçar a atualização:

1. Exclua os arquivos do diretório de cache
2. Ou desative o cache temporariamente

## Contribuição

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Envie um pull request

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
