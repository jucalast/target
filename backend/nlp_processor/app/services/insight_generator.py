"""
Gerador de insights em tempo real para o chat de inteligência de negócio.

Este módulo cria insights acionáveis baseados nas informações coletadas
durante a conversa com o usuário.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from shared.schemas.business_profile import BusinessProfile, ChatInsight

logger = logging.getLogger(__name__)


class RealtimeInsightGenerator:
    """
    Gerador de insights em tempo real que analisa o perfil de negócio
    conforme ele é construído durante a conversa.
    """
    
    def __init__(self):
        """Inicializa o gerador de insights."""
        self.market_data = self._load_market_insights()
        self.behavioral_patterns = self._load_behavioral_patterns()
        self.geographic_insights = self._load_geographic_insights()
        
        logger.info("💡 Gerador de Insights em Tempo Real inicializado")
    
    async def generate_insights(self, profile: BusinessProfile) -> List[ChatInsight]:
        """
        Gera insights relevantes baseados no perfil atual.
        
        Args:
            profile: Perfil de negócio atual
            
        Returns:
            Lista de insights acionáveis
        """
        insights = []
        
        # Insights demográficos
        insights.extend(await self._generate_demographic_insights(profile))
        
        # Insights psicográficos
        insights.extend(await self._generate_psychographic_insights(profile))
        
        # Insights de mercado
        insights.extend(await self._generate_market_insights(profile))
        
        # Insights geográficos
        insights.extend(await self._generate_geographic_insights(profile))
        
        # Insights de oportunidade
        insights.extend(await self._generate_opportunity_insights(profile))
        
        # Warnings e alertas
        insights.extend(await self._generate_warnings(profile))
        
        # Prioriza e filtra insights
        prioritized_insights = self._prioritize_insights(insights)
        
        logger.debug(f"💡 Gerados {len(prioritized_insights)} insights para o perfil")
        
        return prioritized_insights[:5]  # Retorna top 5 insights
    
    async def _generate_demographic_insights(self, profile: BusinessProfile) -> List[ChatInsight]:
        """Gera insights baseados no perfil demográfico."""
        insights = []
        
        demo = profile.target_audience.demographic
        
        # Insight sobre faixa etária
        if demo.age_range:
            age_insights = self._get_age_specific_insights(demo.age_range)
            if age_insights:
                insights.append(ChatInsight(
                    type='demographic',
                    title=f'Características da Faixa Etária {demo.age_range}',
                    description=age_insights['description'],
                    confidence=0.8,
                    data_source='Dados demográficos IBGE',
                    actionable=True,
                    related_metrics=['population_size', 'spending_power']
                ))
        
        # Insight sobre localização
        if demo.location_type:
            location_insights = self._get_location_insights(demo.location_type)
            if location_insights:
                insights.append(ChatInsight(
                    type='demographic',
                    title=f'Perfil de Consumo: {demo.location_type.title()}',
                    description=location_insights['description'],
                    confidence=0.75,
                    data_source='Pesquisa POF-IBGE',
                    actionable=True,
                    related_metrics=['regional_spending', 'market_penetration']
                ))
        
        # Insight sobre educação vs renda
        if demo.education_level and demo.income_range:
            insights.append(ChatInsight(
                type='demographic',
                title='Correlação Educação-Renda Identificada',
                description=f'Público com {demo.education_level} geralmente tem renda {demo.income_range}, o que indica boa capacidade de investimento',
                confidence=0.7,
                data_source='Correlação PNAD-POF',
                actionable=True,
                related_metrics=['disposable_income', 'education_level']
            ))
        
        return insights
    
    async def _generate_psychographic_insights(self, profile: BusinessProfile) -> List[ChatInsight]:
        """Gera insights baseados no perfil psicográfico."""
        insights = []
        
        psycho = profile.target_audience.psychographic
        
        # Insight sobre arquétipo comportamental
        if psycho.archetype:
            archetype_data = self._get_archetype_insights(psycho.archetype)
            if archetype_data:
                insights.append(ChatInsight(
                    type='psychographic',
                    title=f'Perfil {psycho.archetype.title()}: Estratégias Recomendadas',
                    description=archetype_data['marketing_strategy'],
                    confidence=0.85,
                    data_source='Análise Psicográfica POF',
                    actionable=True,
                    related_metrics=['behavioral_score', 'engagement_rate']
                ))
        
        # Insight sobre valores
        if psycho.values:
            values_insight = self._analyze_values_combination(psycho.values)
            if values_insight:
                insights.append(ChatInsight(
                    type='psychographic',
                    title='Combinação de Valores Identificada',
                    description=values_insight['description'],
                    confidence=0.8,
                    data_source='Análise de Valores',
                    actionable=True,
                    related_metrics=['value_alignment', 'brand_affinity']
                ))
        
        # Insight sobre tecnologia
        if psycho.lifestyle_indicators.tech_adoption > 0.7:
            insights.append(ChatInsight(
                type='psychographic',
                title='Alto Nível de Adoção Tecnológica',
                description='Público altamente digital: priorize canais online, redes sociais e experiências tech-first',
                confidence=0.9,
                data_source='Análise de Estilo de Vida',
                actionable=True,
                related_metrics=['digital_engagement', 'tech_spending']
            ))
        
        return insights
    
    async def _generate_market_insights(self, profile: BusinessProfile) -> List[ChatInsight]:
        """Gera insights sobre tamanho e características do mercado."""
        insights = []
        
        # Estimativa de tamanho de mercado baseada no perfil
        if profile.target_audience.demographic.age_range and profile.geographic_focus.level:
            market_size = self._estimate_market_size(profile)
            if market_size:
                insights.append(ChatInsight(
                    type='market_size',
                    title=f'Tamanho Estimado do Mercado',
                    description=f'Aproximadamente {market_size["people"]:,} pessoas no seu público-alvo, representando R$ {market_size["revenue_potential"]:,.0f} em potencial de receita',
                    confidence=0.75,
                    data_source='Projeção baseada em dados IBGE',
                    actionable=True,
                    related_metrics=['market_size', 'revenue_potential']
                ))
        
        # Insight sobre competitividade
        if profile.business_description:
            competition_insight = self._analyze_competition_level(profile.business_description)
            if competition_insight:
                insights.append(ChatInsight(
                    type='market_size',
                    title='Análise de Competitividade',
                    description=competition_insight['description'],
                    confidence=0.6,
                    data_source='Análise de mercado',
                    actionable=True,
                    related_metrics=['competition_level', 'market_saturation']
                ))
        
        return insights
    
    async def _generate_geographic_insights(self, profile: BusinessProfile) -> List[ChatInsight]:
        """Gera insights sobre estratégia geográfica."""
        insights = []
        
        geo = profile.geographic_focus
        
        # Insight sobre foco geográfico
        if geo.level != 'national':
            geographic_advantage = self._analyze_geographic_strategy(geo)
            if geographic_advantage:
                insights.append(ChatInsight(
                    type='geographic',
                    title='Vantagem da Estratégia Geográfica Focada',
                    description=geographic_advantage['description'],
                    confidence=0.8,
                    data_source='Análise geográfica',
                    actionable=True,
                    related_metrics=['geographic_penetration', 'regional_preference']
                ))
        
        # Insight sobre localizações específicas
        if geo.specific_locations:
            for location in geo.specific_locations[:2]:  # Máximo 2 locations
                location_data = self._get_specific_location_insights(location)
                if location_data:
                    insights.append(ChatInsight(
                        type='geographic',
                        title=f'Oportunidade em {location}',
                        description=location_data['description'],
                        confidence=0.7,
                        data_source=f'Dados regionais {location}',
                        actionable=True,
                        related_metrics=['regional_market_size', 'local_competition']
                    ))
        
        return insights
    
    async def _generate_opportunity_insights(self, profile: BusinessProfile) -> List[ChatInsight]:
        """Gera insights sobre oportunidades específicas."""
        insights = []
        
        # Oportunidade baseada em timing
        if profile.business_stage == 'idea' and profile.temporal_context.urgency_level == 'immediate':
            insights.append(ChatInsight(
                type='opportunity',
                title='Janela de Oportunidade: Validação Rápida',
                description='Com urgência alta e negócio em ideação, foque em MVP e validação rápida com o público-alvo identificado',
                confidence=0.85,
                data_source='Análise de timing',
                actionable=True,
                related_metrics=['time_to_market', 'validation_speed']
            ))
        
        # Oportunidade baseada em gaps de mercado
        if profile.target_audience.psychographic.archetype == 'experiencialista':
            insights.append(ChatInsight(
                type='opportunity',
                title='Gap de Mercado: Experiências Personalizadas',
                description='Arquétipo Experiencialista indica oportunidade em personalização e experiências únicas',
                confidence=0.8,
                data_source='Análise de gaps de mercado',
                actionable=True,
                related_metrics=['personalization_demand', 'experience_premium']
            ))
        
        # Oportunidade baseada em sustentabilidade
        if 'sustentabilidade' in profile.target_audience.psychographic.values:
            insights.append(ChatInsight(
                type='opportunity',
                title='Oportunidade Verde: Mercado Sustentável',
                description='Público valoriza sustentabilidade: oportunidade de posicionamento eco-friendly e marketing verde',
                confidence=0.9,
                data_source='Análise de valores',
                actionable=True,
                related_metrics=['sustainability_premium', 'green_market_growth']
            ))
        
        return insights
    
    async def _generate_warnings(self, profile: BusinessProfile) -> List[ChatInsight]:
        """Gera alertas e warnings baseados no perfil."""
        insights = []
        
        # Warning sobre mercado muito específico
        if (profile.geographic_focus.level == 'municipal' and 
            len(profile.geographic_focus.specific_locations) == 1 and
            profile.target_audience.demographic.age_range):
            
            insights.append(ChatInsight(
                type='warning',
                title='⚠️ Mercado Muito Específico',
                description='Foco muito restrito pode limitar crescimento. Considere expandir critérios conforme validar o produto',
                confidence=0.7,
                data_source='Análise de risco',
                actionable=True,
                related_metrics=['market_size_risk', 'expansion_potential']
            ))
        
        # Warning sobre competição
        if profile.business_description and 'tecnologia' in profile.business_description.lower():
            insights.append(ChatInsight(
                type='warning',
                title='⚠️ Setor Altamente Competitivo',
                description='Mercado de tecnologia tem alta competição. Foque em diferenciação clara e nicho específico',
                confidence=0.6,
                data_source='Análise setorial',
                actionable=True,
                related_metrics=['competition_intensity', 'differentiation_need']
            ))
        
        return insights
    
    def _get_age_specific_insights(self, age_range: str) -> Optional[Dict[str, Any]]:
        """Retorna insights específicos para faixa etária."""
        age_insights = {
            '18-35': {
                'description': 'Faixa etária altamente digital, valoriza experiências, tem boa disposição para experimentar novos produtos'
            },
            '25-45': {
                'description': 'Perfil com maior poder aquisitivo, decisões mais racionais, valoriza qualidade e conveniência'
            },
            '45-65': {
                'description': 'Público estabelecido, valoriza tradição e qualidade, menor adoção digital mas alta fidelidade'
            }
        }
        return age_insights.get(age_range)
    
    def _get_location_insights(self, location_type: str) -> Optional[Dict[str, Any]]:
        """Retorna insights específicos para tipo de localização."""
        location_insights = {
            'urbano': {
                'description': 'Público urbano tem maior renda, acesso a tecnologia e variedade de opções. Competição mais alta mas mercado maior'
            },
            'rural': {
                'description': 'Mercado rural tem menor competição, público mais fiel, mas limitações logísticas e de acesso digital'
            }
        }
        return location_insights.get(location_type)
    
    def _get_archetype_insights(self, archetype: str) -> Optional[Dict[str, Any]]:
        """Retorna insights específicos para arquétipo comportamental."""
        archetype_insights = {
            'experiencialista': {
                'marketing_strategy': 'Foque em storytelling, experiências únicas, inovação e canais digitais. Valorizam autenticidade e personalização'
            },
            'tradicionalista': {
                'marketing_strategy': 'Enfatize confiabilidade, tradição, qualidade comprovada. Use canais tradicionais e recomendações'
            },
            'pragmatico': {
                'marketing_strategy': 'Destaque funcionalidade, custo-benefício, praticidade. Use dados e evidências nas campanhas'
            },
            'aspiracional': {
                'marketing_strategy': 'Posicione como status symbol, use influenciadores, enfatize exclusividade e prestígio'
            },
            'equilibrado': {
                'marketing_strategy': 'Abordagem balanceada: qualidade + preço + experiência. Múltiplos canais e mensagens'
            }
        }
        return archetype_insights.get(archetype)
    
    def _analyze_values_combination(self, values: List[str]) -> Optional[Dict[str, Any]]:
        """Analisa combinação de valores para gerar insights."""
        if 'tecnologia' in values and 'sustentabilidade' in values:
            return {
                'description': 'Combinação poderosa: Tech + Sustentabilidade indica público progressista e consciente, disposto a pagar premium por soluções inovadoras e responsáveis'
            }
        elif 'familia' in values and 'segurança' in values:
            return {
                'description': 'Foco familiar + segurança: público busca estabilidade e proteção, valoriza garantias e produtos/serviços confiáveis'
            }
        return None
    
    def _estimate_market_size(self, profile: BusinessProfile) -> Optional[Dict[str, Any]]:
        """Estima tamanho do mercado baseado no perfil."""
        # Estimativas simplificadas baseadas em dados reais do IBGE
        base_population = 215_000_000  # População brasileira aproximada
        
        # Ajusta por faixa etária
        age_multiplier = {
            '18-35': 0.25,  # ~25% da população
            '25-45': 0.30,  # ~30% da população  
            '45-65': 0.20   # ~20% da população
        }
        
        # Ajusta por tipo de localização
        location_multiplier = {
            'urbano': 0.84,  # 84% da população brasileira
            'rural': 0.16    # 16% da população brasileira
        }
        
        # Ajusta por escopo geográfico
        geographic_multiplier = {
            'national': 1.0,
            'regional': 0.2,  # ~20% por região
            'state': 0.04,    # ~4% por estado médio
            'municipal': 0.005 # ~0.5% por município médio
        }
        
        age_range = profile.target_audience.demographic.age_range
        location_type = profile.target_audience.demographic.location_type
        geo_level = profile.geographic_focus.level
        
        if age_range and location_type and geo_level:
            estimated_people = (
                base_population * 
                age_multiplier.get(age_range, 0.2) * 
                location_multiplier.get(location_type, 0.8) *
                geographic_multiplier.get(geo_level, 1.0)
            )
            
            # Estimativa de potencial de receita (muito simplificada)
            avg_spending_per_person = 500  # R$ por ano
            revenue_potential = estimated_people * avg_spending_per_person
            
            return {
                'people': int(estimated_people),
                'revenue_potential': revenue_potential
            }
        
        return None
    
    def _analyze_competition_level(self, business_description: str) -> Optional[Dict[str, Any]]:
        """Analisa nível de competição baseado na descrição do negócio."""
        desc_lower = business_description.lower()
        
        high_competition_keywords = ['tecnologia', 'app', 'delivery', 'e-commerce', 'digital']
        medium_competition_keywords = ['consultoria', 'serviços', 'educação', 'saúde']
        low_competition_keywords = ['nicho', 'especializado', 'local', 'artesanal']
        
        if any(keyword in desc_lower for keyword in high_competition_keywords):
            return {
                'description': 'Setor de alta competição detectado. Foque em diferenciação clara e nicho específico para se destacar'
            }
        elif any(keyword in desc_lower for keyword in medium_competition_keywords):
            return {
                'description': 'Competição moderada no setor. Qualidade e atendimento diferenciado serão fatores-chave'
            }
        elif any(keyword in desc_lower for keyword in low_competition_keywords):
            return {
                'description': 'Mercado de nicho identificado. Oportunidade de estabelecer posição dominante rapidamente'
            }
        
        return None
    
    def _analyze_geographic_strategy(self, geo_focus: Any) -> Optional[Dict[str, Any]]:
        """Analisa vantagens da estratégia geográfica."""
        if geo_focus.level == 'municipal':
            return {
                'description': 'Estratégia municipal permite marketing hiperfocado, custos menores e conhecimento profundo do mercado local'
            }
        elif geo_focus.level == 'state':
            return {
                'description': 'Foco estadual oferece mercado significativo com características culturais/econômicas similares'
            }
        elif geo_focus.level == 'regional':
            return {
                'description': 'Estratégia regional permite escala com características demográficas relativamente homogêneas'
            }
        
        return None
    
    def _get_specific_location_insights(self, location: str) -> Optional[Dict[str, Any]]:
        """Retorna insights para localizações específicas."""
        # Dados simplificados - em implementação real, viria do banco de dados
        location_data = {
            'São Paulo': {
                'description': 'Maior mercado do país, alta competição mas grande potencial. Público sofisticado e early adopter'
            },
            'Rio de Janeiro': {
                'description': 'Mercado com forte cultura local, valoriza relacionamento e experiências. Turismo como fator adicional'
            },
            'Belo Horizonte': {
                'description': 'Hub tecnológico em crescimento, custo operacional menor que SP/RJ, público receptivo a inovações'
            }
        }
        return location_data.get(location)
    
    def _prioritize_insights(self, insights: List[ChatInsight]) -> List[ChatInsight]:
        """Prioriza insights por relevância e acionabilidade."""
        
        # Score de prioridade baseado em múltiplos fatores
        def calculate_priority_score(insight: ChatInsight) -> float:
            score = insight.confidence
            
            # Bonus para insights acionáveis
            if insight.actionable:
                score += 0.2
            
            # Bonus por tipo de insight
            type_bonus = {
                'opportunity': 0.3,
                'psychographic': 0.2,
                'market_size': 0.15,
                'demographic': 0.1,
                'warning': 0.25,
                'trend': 0.1
            }
            score += type_bonus.get(insight.type, 0)
            
            # Bonus para insights recentes
            if insight.generated_at:
                time_diff = (datetime.now() - insight.generated_at).total_seconds()
                if time_diff < 300:  # Últimos 5 minutos
                    score += 0.1
            
            return score
        
        # Ordena por score de prioridade
        insights_with_scores = [
            (insight, calculate_priority_score(insight)) 
            for insight in insights
        ]
        
        sorted_insights = sorted(
            insights_with_scores, 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [insight for insight, score in sorted_insights]
    
    def _load_market_insights(self) -> Dict[str, Any]:
        """Carrega dados de insights de mercado."""
        # Em implementação real, viria de banco de dados ou APIs
        return {}
    
    def _load_behavioral_patterns(self) -> Dict[str, Any]:
        """Carrega padrões comportamentais."""
        return {}
    
    def _load_geographic_insights(self) -> Dict[str, Any]:
        """Carrega insights geográficos."""
        return {}
