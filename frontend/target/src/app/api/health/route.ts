import { NextRequest, NextResponse } from 'next/server';

const NLP_PROCESSOR_URL = process.env.NLP_PROCESSOR_URL || 'http://localhost:8002';

export async function GET() {
  try {
    // Testa a conexão com o backend
    const response = await fetch(`${NLP_PROCESSOR_URL}/api/v1/intelligent_chat/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend unhealthy! status: ${response.status}`);
    }

    const backendHealth = await response.json();
    
    return NextResponse.json({
      status: 'healthy',
      frontend: {
        status: 'running',
        timestamp: new Date().toISOString(),
        api_proxy: 'active'
      },
      backend: backendHealth,
      integration: {
        chat_api: 'connected',
        nlp_processor: 'ready',
        intelligent_chat: 'available'
      }
    });
    
  } catch (error) {
    console.error('Health check failed:', error);
    
    return NextResponse.json({
      status: 'unhealthy',
      frontend: {
        status: 'running',
        timestamp: new Date().toISOString(),
        api_proxy: 'active'
      },
      backend: {
        status: 'unreachable',
        error: error instanceof Error ? error.message : String(error)
      },
      integration: {
        chat_api: 'disconnected',
        nlp_processor: 'unavailable',
        intelligent_chat: 'offline'
      }
    }, { status: 503 });
  }
}
