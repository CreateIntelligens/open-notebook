import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transformationsApi } from '@/lib/api/transformations'
import { useToast } from '@/lib/hooks/use-toast'
import {
  CreateTransformationRequest,
  UpdateTransformationRequest,
  ExecuteTransformationRequest,
  CreatePromptPresetRequest,
  UpdatePromptPresetRequest,
} from '@/lib/types/transformations'

// Add to QUERY_KEYS in query-client.ts
export const TRANSFORMATION_QUERY_KEYS = {
  transformations: ['transformations'] as const,
  transformation: (id: string) => ['transformations', id] as const,
  promptPresets: ['transformations', 'prompt-presets'] as const,
  promptPreset: (id: string) => ['transformations', 'prompt-presets', id] as const,
}

export function useTransformations() {
  return useQuery({
    queryKey: TRANSFORMATION_QUERY_KEYS.transformations,
    queryFn: () => transformationsApi.list(),
  })
}

export function useTransformation(id?: string, options?: { enabled?: boolean }) {
  const transformationId = id ?? ''
  return useQuery({
    queryKey: TRANSFORMATION_QUERY_KEYS.transformation(transformationId),
    queryFn: () => transformationsApi.get(transformationId),
    enabled: !!transformationId && (options?.enabled ?? true),
  })
}

export function useCreateTransformation() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: CreateTransformationRequest) => transformationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.transformations })
      toast({
        title: 'Success',
        description: 'Transformation created successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create transformation',
        variant: 'destructive',
      })
    },
  })
}

export function useUpdateTransformation() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTransformationRequest }) =>
      transformationsApi.update(id, data),
    onSuccess: (_, { id, data }) => {
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.transformations })
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.transformation(id) })
      toast({
        title: 'Success',
        description: `Transformation '${data.name || 'transformation'}' saved successfully`,
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update transformation',
        variant: 'destructive',
      })
    },
  })
}

export function useDeleteTransformation() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (id: string) => transformationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.transformations })
      toast({
        title: 'Success',
        description: 'Transformation deleted successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete transformation',
        variant: 'destructive',
      })
    },
  })
}

export function useExecuteTransformation() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: ExecuteTransformationRequest) => transformationsApi.execute(data),
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to execute transformation',
        variant: 'destructive',
      })
    },
  })
}

export function usePromptPresets() {
  return useQuery({
    queryKey: TRANSFORMATION_QUERY_KEYS.promptPresets,
    queryFn: () => transformationsApi.listPromptPresets(),
  })
}

export function useCreatePromptPreset() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: CreatePromptPresetRequest) => transformationsApi.createPromptPreset(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.promptPresets })
      toast({
        title: 'Success',
        description: `Prompt '${data.name}' created successfully`,
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create prompt',
        variant: 'destructive',
      })
    },
  })
}

export function useUpdatePromptPreset() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({
      promptId,
      data,
    }: {
      promptId: string
      data: UpdatePromptPresetRequest
    }) => transformationsApi.updatePromptPreset(promptId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.promptPresets })
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.promptPreset(variables.promptId) })
      toast({
        title: 'Success',
        description: 'Prompt updated successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update prompt',
        variant: 'destructive',
      })
    },
  })
}

export function useDeletePromptPreset() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (promptId: string) => transformationsApi.deletePromptPreset(promptId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSFORMATION_QUERY_KEYS.promptPresets })
      toast({
        title: 'Success',
        description: 'Prompt deleted successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete prompt',
        variant: 'destructive',
      })
    },
  })
}
