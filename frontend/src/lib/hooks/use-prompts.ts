import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { promptsApi } from '@/lib/api/prompts'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useToast } from '@/lib/hooks/use-toast'
import {
  CreatePromptRequest,
  UpdatePromptRequest,
  SetActivePromptRequest
} from '@/lib/types/api'

export function usePrompts(notebookId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.prompts(notebookId),
    queryFn: () => promptsApi.list(notebookId!),
    enabled: !!notebookId,
  })
}

export function usePrompt(id?: string, options?: { enabled?: boolean }) {
  const promptId = id ?? ''
  return useQuery({
    queryKey: QUERY_KEYS.prompt(promptId),
    queryFn: () => promptsApi.get(promptId),
    enabled: !!promptId && (options?.enabled ?? true),
  })
}

export function useActivePrompt(notebookId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.activePrompt(notebookId!),
    queryFn: () => promptsApi.getActive(notebookId!),
    enabled: !!notebookId,
  })
}

export function useCreatePrompt() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: CreatePromptRequest) => promptsApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.prompts(variables.notebook_id)
      })
      toast({
        title: 'Success',
        description: 'Prompt created successfully',
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

export function useUpdatePrompt() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdatePromptRequest; notebookId?: string }) =>
      promptsApi.update(id, data),
    onSuccess: (_, variables) => {
      // Only invalidate specific queries to avoid unnecessary refetches
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.prompt(variables.id) })
      if (variables.notebookId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.prompts(variables.notebookId) })
      }
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

export function useDeletePrompt() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ id, notebookId }: { id: string; notebookId: string }) => promptsApi.delete(id),
    onSuccess: (_, { notebookId }) => {
      // Only invalidate prompts for this specific notebook
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.prompts(notebookId) })
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

export function useSetActivePrompt() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ notebookId, data }: { notebookId: string; data: SetActivePromptRequest }) =>
      promptsApi.setActive(notebookId, data),
    onSuccess: (_data, { notebookId }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.activePrompt(notebookId) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.prompts(notebookId) })
      toast({
        title: 'Success',
        description: 'Active prompt updated successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to set active prompt',
        variant: 'destructive',
      })
    },
  })
}
