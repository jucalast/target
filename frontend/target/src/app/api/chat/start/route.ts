import { NextRequest, NextResponse } from 'next/server';

const NLP_PROCESSOR_URL = process.env.NLP_PROCESSOR_URL || 'http://localhost:8002';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${NLP_PROCESSOR_URL}/api/v1/intelligent_chat/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend error ${response.status}:`, errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Chat session started:', data);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Erro no proxy de chat start:', error);
    return NextResponse.json(
      { error: 'Erro interno do servidor', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
