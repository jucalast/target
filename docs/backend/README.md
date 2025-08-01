# Documentação do Backend

Bem-vindo à documentação técnica do backend do Sistema de Identificação de Público-Alvo. Este documento fornece uma visão abrangente da arquitetura, componentes e fluxos de dados do sistema.

## Visão Geral

O backend é composto por quatro módulos principais que trabalham em conjunto para processar entradas de usuários, coletar e analisar dados, e gerar insights sobre públicos-alvo.

## Módulos Principais

1. [API Gateway](./api_gateway.md)
   - Ponto de entrada para todas as requisições
   - Autenticação e autorização
   - Roteamento de requisições
   - Validação de entrada

2. [ETL Pipeline](./etl_pipeline.md)
   - Coleta de dados de fontes externas (IBGE, Google Trends)
   - Transformação e normalização de dados
   - Carga em banco de dados
   - Processamento assíncrono

3. [NLP Processor](./nlp_processor.md)
   - Processamento de linguagem natural
   - Extração de características
   - Análise semântica
   - Geração de embeddings

4. [Componentes Compartilhados](./shared_components.md)
   - Modelos de banco de dados
   - Esquemas de validação
   - Utilitários comuns
   - Configurações globais

## [Integração do Sistema](./system_integration.md)

Documentação detalhada sobre como os módulos se comunicam e trabalham juntos para atender aos objetivos do projeto.

## Guias de Desenvolvimento

### Pré-requisitos

- Python 3.9+
- PostgreSQL 13+
- Docker (opcional para desenvolvimento)

### Configuração do Ambiente

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   .\venv\Scripts\activate  # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure as variáveis de ambiente (crie um arquivo `.env` baseado no `.env.example`)
5. Execute as migrações do banco de dados:
   ```bash
   alembic upgrade head
   ```

### Executando os Serviços

#### API Gateway
```bash
cd api_gateway
uvicorn app.main:app --reload
```

#### ETL Pipeline
```bash
cd etl_pipeline
python -m app.main
```

#### NLP Processor
```bash
cd nlp_processor
python -m app.main
```

## Testes

Para executar os testes:

```bash
pytest
```

## Contribuição

1. Crie um branch para sua feature (`git checkout -b feature/AmazingFeature`)
2. Faça commit das suas alterações (`git commit -m 'Add some AmazingFeature'`)
3. Faça push para o branch (`git push origin feature/AmazingFeature`)
4. Abra um Pull Request

## Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## Contato

Equipe de Desenvolvimento - [dev@example.com](mailto:dev@example.com)

Link do Projeto: [https://github.com/seu-usuario/target](https://github.com/seu-usuario/target)
