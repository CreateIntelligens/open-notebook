import apiClient from './client'
import {
  Transformation,
  CreateTransformationRequest,
  UpdateTransformationRequest,
  ExecuteTransformationRequest,
  ExecuteTransformationResponse,
  PromptPreset,
  CreatePromptPresetRequest,
  UpdatePromptPresetRequest
} from '@/lib/types/transformations'

export const transformationsApi = {
  list: async () => {
    const response = await apiClient.get<Transformation[]>('/transformations')
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<Transformation>(`/transformations/${id}`)
    return response.data
  },

  create: async (data: CreateTransformationRequest) => {
    const response = await apiClient.post<Transformation>('/transformations', data)
    return response.data
  },

  update: async (id: string, data: UpdateTransformationRequest) => {
    const response = await apiClient.put<Transformation>(`/transformations/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/transformations/${id}`)
  },

  execute: async (data: ExecuteTransformationRequest) => {
    const response = await apiClient.post<ExecuteTransformationResponse>('/transformations/execute', data)
    return response.data
  },

  listPromptPresets: async () => {
    const response = await apiClient.get<PromptPreset[]>('/transformations/prompts')
    return response.data
  },

  createPromptPreset: async (data: CreatePromptPresetRequest) => {
    const response = await apiClient.post<PromptPreset>('/transformations/prompts', data)
    return response.data
  },

  updatePromptPreset: async (promptId: string, data: UpdatePromptPresetRequest) => {
    const response = await apiClient.put<PromptPreset>(`/transformations/prompts/${promptId}`, data)
    return response.data
  },

  deletePromptPreset: async (promptId: string) => {
    await apiClient.delete(`/transformations/prompts/${promptId}`)
  },

  getDefaultPrompt: async () => {
    const response = await apiClient.get<{ transformation_instructions: string }>('/transformations/default-prompt')
    return response.data
  },

  updateDefaultPrompt: async (data: { transformation_instructions: string }) => {
    const response = await apiClient.put<{ transformation_instructions: string }>('/transformations/default-prompt', data)
    return response.data
  }
}
