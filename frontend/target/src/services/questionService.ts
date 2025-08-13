import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface QuestionAnalysis {
  score: number;
  is_correct: boolean;
  feedback: string;
  hints: string[];
  next_steps: string;
  conversation_id: string;
}

interface AdaptiveQuestion {
  question_id: string;
  question_text: string;
  context: string;
  difficulty: 'easy' | 'medium' | 'hard';
  hints: string[];
  explanation?: string;
}

export const analyzeResponse = async (
  questionId: string,
  response: string,
  userId: string,
  metadata: Record<string, any> = {}
): Promise<QuestionAnalysis> => {
  try {
    const result = await axios.post(`${API_BASE_URL}/question-answering/analyze-response/`, {
      question_id: questionId,
      response,
      user_id: userId,
      metadata
    });
    
    return result.data;
  } catch (error) {
    console.error('Error analyzing response:', error);
    throw error;
  }
};

export const generateAdaptiveQuestion = async (
  questionId: string,
  userId: string,
  previousAttempts: any[] = []
): Promise<AdaptiveQuestion> => {
  try {
    const result = await axios.post(`${API_BASE_URL}/question-answering/generate-adaptive-question/`, {
      question_id: questionId,
      user_id: userId,
      previous_attempts: previousAttempts
    });
    
    return result.data;
  } catch (error) {
    console.error('Error generating adaptive question:', error);
    throw error;
  }
};

export const getQuestion = async (questionId: string): Promise<any> => {
  try {
    const result = await axios.get(`${API_BASE_URL}/question-answering/questions/${questionId}`);
    return result.data;
  } catch (error) {
    console.error('Error getting question:', error);
    throw error;
  }
};

export const createQuestion = async (questionData: {
  question_text: string;
  context: string;
  expected_answer: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}): Promise<{ question_id: string }> => {
  try {
    const result = await axios.post(`${API_BASE_URL}/question-answering/questions/`, questionData);
    return result.data;
  } catch (error) {
    console.error('Error creating question:', error);
    throw error;
  }
};
