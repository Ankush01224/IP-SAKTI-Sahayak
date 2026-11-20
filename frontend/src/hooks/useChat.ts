import { useState, useCallback } from 'react';
import { api, ChatResponse } from '../api/client';
import { ChatMessage } from '../components/MessageBubble';

export const PRESET_PROMPTS = [
  {
    title: 'Classical Formulations Patentability',
    query: 'Can an Ayurvedic classical formulation described in Charaka Samhita be patented under the Indian Patent Act?',
    tag: 'Patents Act §3(p)'
  },
  {
    title: 'NBA Approval for Herb Export',
    query: 'What permissions are required under the Biological Diversity Act for commercial utilization and export of Ashwagandha by a foreign entity?',
    tag: 'Biodiversity Act §3 & §6'
  },
  {
    title: 'ASU Manufacturing Licenses',
    query: 'What is the regulatory difference between Classical ASU drugs and Patent or Proprietary ASU medicines under Rule 158-B?',
    tag: 'Drugs & Cosmetics Act'
  },
  {
    title: 'TKDL Defensive Protection',
    query: 'How does the Traditional Knowledge Digital Library (TKDL) prevent biopiracy and invalid patents in the USPTO and EPO?',
    tag: 'TKDL & Prior Art'
  },
  {
    title: 'Ayush Standard vs Premium Mark',
    query: 'What are the heavy metal and contaminant limits required for obtaining the Ayush Premium Mark for international export?',
    tag: 'Export & Quality Limits'
  },
  {
    title: 'US FDA Botanical Drug Pathway',
    query: 'Can an Ayurvedic polyherbal formulation be approved as a prescription drug under US FDA Botanical Drug Development guidance?',
    tag: 'US FDA & CMC'
  }
];

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await api.sendChat(text.trim(), language);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.answer,
        citations: response.citations,
        confidenceScore: response.confidence_score,
        confidenceStatus: response.confidence_status,
        queryClassification: response.query_classification,
        latencyMs: response.latency_ms,
        timestamp: response.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(err.message || 'An unexpected error occurred while communicating with the Ayush legal assistant.');
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, language]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    language,
    setLanguage,
    error,
    sendMessage,
    clearChat,
  };
}
