"""
Schemas para o perfil de negócio extraído através do chat inteligente.
"""
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class DemographicProfile(BaseModel):
    """Perfil demográfico do público-alvo."""
    age_range: Optional[str] = Field(None, description="Faixa etária (ex: '25-35')")
    income_range: Optional[str] = Field(None, description="Faixa de renda (ex: '3000-8000')")
    education_level: Optional[str] = Field(None, description="Nível educacional")
    location_type: Optional[str] = Field(None, description="Tipo de localização (urbano/rural)")
    family_structure: Optional[str] = Field(None, description="Estrutura familiar")
    occupation: Optional[str] = Field(None, description="Área de atuação profissional")


class LifestyleIndicators(BaseModel):
    """Indicadores de estilo de vida baseados em bens duráveis."""
    tech_adoption: float = Field(0.0, ge=0.0, le=1.0, description="Nível de adoção tecnológica")
    comfort_level: float = Field(0.0, ge=0.0, le=1.0, description="Nível de conforto")
    mobility: bool = Field(False, description="Possui mobilidade própria")
    sustainability_concern: float = Field(0.0, ge=0.0, le=1.0, description="Preocupação com sustentabilidade")


class SpendingPriority(BaseModel):
    """Prioridade de gasto específica."""
    category: str = Field(..., description="Categoria de gasto")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Score de prioridade")
    reasoning: Optional[str] = Field(None, description="Justificativa da prioridade")


class PsychographicProfile(BaseModel):
    """Perfil psicográfico do público-alvo."""
    archetype: Optional[Literal['experiencialista', 'tradicionalista', 'pragmatico', 'aspiracional', 'equilibrado']] = None
    spending_priorities: List[SpendingPriority] = Field(default_factory=list)
    lifestyle_indicators: LifestyleIndicators = Field(default_factory=LifestyleIndicators)
    values: List[str] = Field(default_factory=list, description="Valores importantes")
    sentiment_index: float = Field(0.5, ge=0.0, le=1.0, description="Índice de sentimento/otimismo")


class BehavioralProfile(BaseModel):
    """Perfil comportamental de compra."""
    purchase_channels: List[str] = Field(default_factory=list, description="Canais preferidos de compra")
    decision_factors: List[str] = Field(default_factory=list, description="Fatores de decisão de compra")
    seasonal_patterns: List[str] = Field(default_factory=list, description="Padrões sazonais")
    brand_loyalty: float = Field(0.5, ge=0.0, le=1.0, description="Nível de lealdade à marca")
    price_sensitivity: float = Field(0.5, ge=0.0, le=1.0, description="Sensibilidade a preço")


class TargetAudience(BaseModel):
    """Definição completa do público-alvo."""
    demographic: DemographicProfile = Field(default_factory=DemographicProfile)
    psychographic: PsychographicProfile = Field(default_factory=PsychographicProfile)
    behavioral: BehavioralProfile = Field(default_factory=BehavioralProfile)
    description: Optional[str] = Field(None, description="Descrição textual do público")


class GeographicFocus(BaseModel):
    """Foco geográfico do negócio."""
    level: Literal['national', 'regional', 'state', 'municipal'] = Field('national')
    specific_locations: List[str] = Field(default_factory=list)
    expansion_priority: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = Field(None, description="Justificativa do foco geográfico")


class TemporalContext(BaseModel):
    """Contexto temporal do negócio."""
    urgency_level: Literal['immediate', 'moderate', 'patient'] = Field('moderate')
    planning_horizon: Literal['6_months', '1_year', '2_3_years'] = Field('1_year')
    seasonal_relevance: bool = Field(False)
    launch_timeframe: Optional[str] = Field(None)


class ConfidenceScores(BaseModel):
    """Scores de confiança das inferências."""
    demographic_confidence: float = Field(0.0, ge=0.0, le=1.0)
    psychographic_confidence: float = Field(0.0, ge=0.0, le=1.0)
    geographic_confidence: float = Field(0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)


class BusinessProfile(BaseModel):
    """Perfil completo do negócio extraído através do chat."""
    
    # Dados básicos do negócio
    business_description: Optional[str] = Field(None, description="Descrição do negócio")
    business_stage: Optional[Literal['idea', 'mvp', 'operating', 'expanding']] = Field(None)
    revenue_model: Optional[str] = Field(None, description="Modelo de receita")
    problem_solved: Optional[str] = Field(None, description="Problema que resolve")
    value_proposition: Optional[str] = Field(None, description="Proposta de valor")
    
    # Perfil do cliente
    target_audience: TargetAudience = Field(default_factory=TargetAudience)
    
    # Contexto geográfico e temporal
    geographic_focus: GeographicFocus = Field(default_factory=GeographicFocus)
    temporal_context: TemporalContext = Field(default_factory=TemporalContext)
    
    # Meta-informações
    confidence_scores: ConfidenceScores = Field(default_factory=ConfidenceScores)
    completion_percentage: float = Field(0.0, ge=0.0, le=100.0)
    validation_status: bool = Field(False)
    
    # Controle
    session_id: Optional[str] = Field(None, description="ID da sessão de chat")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    """Mensagem do chat."""
    id: str = Field(..., description="ID único da mensagem")
    session_id: str = Field(..., description="ID da sessão")
    type: Literal['user', 'bot'] = Field(..., description="Tipo da mensagem")
    content: str = Field(..., description="Conteúdo da mensagem")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Metadados para mensagens do bot
    question_type: Optional[str] = Field(None, description="Tipo da pergunta")
    extraction_targets: List[str] = Field(default_factory=list, description="Campos que a pergunta visa extrair")
    processing_time: Optional[float] = Field(None, description="Tempo de processamento")


class ChatInsight(BaseModel):
    """Insight gerado durante o chat."""
    type: Literal['demographic', 'psychographic', 'market_size', 'opportunity', 'warning', 'trend'] = Field(...)
    title: str = Field(..., description="Título do insight")
    description: str = Field(..., description="Descrição detalhada")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança do insight")
    data_source: str = Field(..., description="Fonte dos dados")
    actionable: bool = Field(False, description="Se o insight é acionável")
    related_metrics: List[str] = Field(default_factory=list, description="Métricas relacionadas")
    generated_at: datetime = Field(default_factory=datetime.now)


class ChatResponse(BaseModel):
    """Resposta do sistema de chat.
    
    Nota: Os insights são gerados internamente, mas não são retornados ao usuário
    para manter o foco na coleta de informações do negócio.
    """
    message: ChatMessage = Field(..., description="Mensagem de resposta")
    updated_profile: BusinessProfile = Field(..., description="Perfil atualizado")
    next_question_ready: bool = Field(True, description="Se há próxima pergunta")
    completion_percentage: float = Field(..., description="Percentual de completude")


class ChatProcessRequest(BaseModel):
    """Request para processar mensagem do chat."""
    session_id: str = Field(..., description="ID da sessão")
    user_message: str = Field(..., description="Mensagem do usuário")
    current_profile: Optional[BusinessProfile] = Field(None, description="Perfil atual")


class ChatStartRequest(BaseModel):
    """Request para iniciar uma nova sessão de chat."""
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    initial_context: Optional[str] = Field(None, description="Contexto inicial do negócio")


class ChatStartResponse(BaseModel):
    """Response para início de sessão."""
    session_id: str = Field(..., description="ID da nova sessão")
    welcome_message: ChatMessage = Field(..., description="Mensagem de boas-vindas")
    initial_profile: BusinessProfile = Field(..., description="Perfil inicial vazio")
