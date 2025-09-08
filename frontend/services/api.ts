import axios from "axios";
import { mockApiService } from "./mock";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface Message {
  role: string;
  content: string;
}

export interface ProcessDocsRequest {
  url: string;
  sections?: string[];
}

export interface ProcessDocsResponse {
  success: boolean;
  message: string;
  script: string;
  sections?: string[];
}

export interface ChatRequest {
  messages: Message[];
  doc_url: string;
}

export interface ChatResponse {
  response: string;
  audio_url: string | null;
}

export const createApiService = (useMock: boolean) => {
  if (useMock) {
    return mockApiService;
  }

  return {
    async processDocumentation(
      request: ProcessDocsRequest
    ): Promise<ProcessDocsResponse> {
      try {
        const response = await api.post("/api/docs/process", request);
        return response.data;
      } catch (error) {
        console.error("Error processing documentation:", error);
        throw error;
      }
    },

    async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
      try {
        const response = await api.post("/api/chat/send", request);
        return response.data;
      } catch (error) {
        console.error("Error sending chat message:", error);
        throw error;
      }
    },
  };
};
