'use client'

import { Controller, useForm } from 'react-hook-form'
import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogHeader } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useCreatePrompt, useUpdatePrompt, usePrompt } from '@/lib/hooks/use-prompts'
import { SystemPromptResponse } from '@/lib/types/api'

const promptSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  content: z.string().min(1, 'Content is required'),
})

type PromptFormData = z.infer<typeof promptSchema>

interface PromptEditorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
  initialPrompt?: SystemPromptResponse
}

export function PromptEditorDialog({
  open,
  onOpenChange,
  notebookId,
  initialPrompt,
}: PromptEditorDialogProps) {
  const createPrompt = useCreatePrompt()
  const updatePrompt = useUpdatePrompt()
  const isEditing = Boolean(initialPrompt)

  const promptId = initialPrompt?.id ?? ''
  const { data: fetchedPrompt, isLoading: promptLoading } = usePrompt(promptId, {
    enabled: open && !!initialPrompt?.id
  })

  const isSaving = isEditing ? updatePrompt.isPending : createPrompt.isPending

  const {
    handleSubmit,
    control,
    formState: { errors },
    reset,
  } = useForm<PromptFormData>({
    resolver: zodResolver(promptSchema),
    defaultValues: {
      name: '',
      content: '',
    },
  })

  useEffect(() => {
    if (!open) {
      reset({ name: '', content: '' })
      return
    }

    const source = fetchedPrompt ?? initialPrompt
    const name = source?.name ?? ''
    const content = source?.content ?? ''

    reset({ name, content })
  }, [open, initialPrompt, fetchedPrompt, reset])

  const onSubmit = async (data: PromptFormData) => {
    if (initialPrompt) {
      await updatePrompt.mutateAsync({
        id: promptId,
        data: {
          name: data.name,
          content: data.content,
        },
        notebookId: notebookId
      })
    } else {
      if (!notebookId) {
        console.error('Cannot create prompt without notebook_id')
        return
      }
      await createPrompt.mutateAsync({
        notebook_id: notebookId,
        name: data.name,
        content: data.content,
      })
    }
    reset()
    onOpenChange(false)
  }

  const handleDialogChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      reset()
    }
    onOpenChange(nextOpen)
  }

  const handleClose = () => {
    reset()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleDialogChange}>
      <DialogContent className="sm:max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit System Prompt' : 'Create System Prompt'}
          </DialogTitle>
          <DialogDescription>
            Define how the AI should behave when chatting in this notebook.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {isEditing && promptLoading ? (
            <div className="flex items-center justify-center py-10">
              <span className="text-sm text-muted-foreground">Loading prompt…</span>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Controller
                  control={control}
                  name="name"
                  render={({ field }) => (
                    <Input
                      id="name"
                      placeholder="e.g., Math Teacher, Code Reviewer"
                      {...field}
                    />
                  )}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="content">Content</Label>
                <Controller
                  control={control}
                  name="content"
                  render={({ field }) => (
                    <Textarea
                      id="content"
                      placeholder="You are a helpful assistant that..."
                      className="min-h-[300px] max-h-[60vh] overflow-y-auto resize-none"
                      {...field}
                    />
                  )}
                />
                {errors.content && (
                  <p className="text-sm text-destructive">{errors.content.message}</p>
                )}
              </div>
            </>
          )}

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSaving || (isEditing && promptLoading)}
            >
              {isSaving
                ? isEditing ? 'Saving...' : 'Creating...'
                : isEditing
                  ? 'Save Prompt'
                  : 'Create Prompt'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
