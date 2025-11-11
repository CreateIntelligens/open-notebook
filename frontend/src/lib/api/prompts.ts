import apiClient from './client'
import {
  SystemPromptResponse,
  CreatePromptRequest,
  UpdatePromptRequest,
  SetActivePromptRequest
} from '@/lib/types/api'

export const promptsApi = {
  list: async (notebookId: string) => {
    const response = await apiClient.get<SystemPromptResponse[]>(`/notebooks/${notebookId}/prompts`)
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<SystemPromptResponse>(`/prompts/${id}`)
    return response.data
  },

  create: async (data: CreatePromptRequest) => {
    const response = await apiClient.post<SystemPromptResponse>(`/notebooks/${data.notebook_id}/prompts`, data)
    return response.data
  },

  update: async (id: string, data: UpdatePromptRequest) => {
    const response = await apiClient.put<SystemPromptResponse>(`/prompts/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/prompts/${id}`)
  },

  getActive: async (notebookId: string) => {
    const response = await apiClient.get<SystemPromptResponse | null>(`/notebooks/${notebookId}/active-prompt`)
    return response.data
  },

  setActive: async (notebookId: string, data: SetActivePromptRequest) => {
    const response = await apiClient.put(`/notebooks/${notebookId}/active-prompt`, data)
    return response.data
  },
}
