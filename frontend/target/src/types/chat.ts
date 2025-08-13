// Types para o chat inteligente
export interface DemographicProfile {
  age_range?: string;
  income_range?: string;
  education_level?: string;
  location_type?: string;
  family_structure?: string;
  occupation?: string;
}

export interface LifestyleIndicators {
  tech_adoption: number;
  comfort_level: number;
  mobility: boolean;
  sustainability_concern: number;
}

export interface SpendingPriority {
  category: string;
  priority_score: number;
  reasoning?: string;
}

export interface PsychographicProfile {
  archetype?: 'experiencialista' | 'tradicionalista' | 'pragmatico' | 'aspiracional' | 'equilibrado';
  spending_priorities: SpendingPriority[];
  lifestyle_indicators: LifestyleIndicators;
  values: string[];
  sentiment_index: number;
}

export interface BehavioralProfile {
  purchase_channels: string[];
  decision_factors: string[];
  seasonal_patterns: string[];
  brand_loyalty: number;
  price_sensitivity: number;
}

export interface TargetAudience {
  demographic: DemographicProfile;
  psychographic: PsychographicProfile;
  behavioral: BehavioralProfile;
  description?: string;
}

export interface GeographicFocus {
  level: 'national' | 'regional' | 'state' | 'municipal';
  specific_locations: string[];
  expansion_priority: string[];
  reasoning?: string;
}

export interface TemporalContext {
  urgency_level: 'immediate' | 'moderate' | 'patient';
  planning_horizon: '6_months' | '1_year' | '2_3_years';
  seasonal_relevance: boolean;
  launch_timeframe?: string;
}

export interface ConfidenceScores {
  demographic_confidence: number;
  psychographic_confidence: number;
  geographic_confidence: number;
  overall_confidence: number;
}

export interface BusinessProfile {
  business_description?: string;
  business_stage?: 'idea' | 'mvp' | 'operating' | 'expanding';
  revenue_model?: string;
  problem_solved?: string;
  value_proposition?: string;
  target_audience: TargetAudience;
  geographic_focus: GeographicFocus;
  temporal_context: TemporalContext;
  confidence_scores: ConfidenceScores;
  completion_percentage: number;
  validation_status: boolean;
  session_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  question_type?: string;
  extraction_targets?: string[];
  processing_time?: number;
}

export interface ChatInsight {
  type: 'demographic' | 'psychographic' | 'market_size' | 'opportunity' | 'warning' | 'trend';
  title: string;
  description: string;
  confidence: number;
  data_source: string;
  actionable: boolean;
  related_metrics: string[];
  generated_at: string;
}

export interface ChatResponse {
  message: ChatMessage;
  updated_profile: BusinessProfile;
  insights: ChatInsight[];
  next_question_ready: boolean;
  completion_percentage: number;
}

export interface ChatStartRequest {
  user_name?: string;
  initial_context?: string;
}

export interface ChatStartResponse {
  session_id: string;
  welcome_message: ChatMessage;
  initial_profile: BusinessProfile;
}

export interface ChatProcessRequest {
  session_id: string;
  user_message: string;
  current_profile?: BusinessProfile;
}
