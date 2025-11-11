'use client'

import { useState } from 'react'
import { SystemPromptResponse } from '@/lib/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Plus, MessageSquare, MoreVertical, Trash2, Edit, CheckCircle2, Circle } from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { PromptEditorDialog } from './PromptEditorDialog'
import { useDeletePrompt, useSetActivePrompt } from '@/lib/hooks/use-prompts'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { formatDistanceToNow } from 'date-fns'

interface PromptsColumnProps {
  prompts?: SystemPromptResponse[]
  activePromptId?: string | null
  isLoading: boolean
  notebookId: string
}

export function PromptsColumn({
  prompts,
  activePromptId,
  isLoading,
  notebookId,
}: PromptsColumnProps) {
  const [dialogMode, setDialogMode] = useState<'create' | 'edit' | null>(null)
  const [editorPrompt, setEditorPrompt] = useState<SystemPromptResponse | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [promptToDelete, setPromptToDelete] = useState<string | null>(null)

  const deletePrompt = useDeletePrompt()
  const setActivePromptMutation = useSetActivePrompt()

  const handleDeleteClick = (promptId: string) => {
    setPromptToDelete(promptId)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!promptToDelete) return

    try {
      await deletePrompt.mutateAsync({ id: promptToDelete, notebookId })
      setDeleteDialogOpen(false)
      setPromptToDelete(null)
    } catch (error) {
      console.error('Failed to delete prompt:', error)
    }
  }

  const handleSetActive = async (promptId: string | null) => {
    try {
      await setActivePromptMutation.mutateAsync({
        notebookId,
        data: { prompt_id: promptId }
      })
    } catch (error) {
      console.error('Failed to set active prompt:', error)
    }
  }

  return (
    <>
      <Card className="h-full flex flex-col flex-1 overflow-hidden">
        <CardHeader className="pb-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">System Prompts</CardTitle>
            <Button
              size="sm"
              onClick={() => {
                setEditorPrompt(null)
                setDialogMode('create')
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Prompt
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto min-h-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : !prompts || prompts.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              title="No custom prompts"
              description="Create custom system prompts to control AI behavior in chat."
            />
          ) : (
            <div className="space-y-3">
              {prompts.map((prompt) => {
                const isActive = prompt.id === activePromptId
                return (
                  <div
                    key={prompt.id}
                    className={`p-3 border rounded-lg group relative transition-shadow ${
                      isActive ? 'border-primary bg-primary/5' : 'card-hover'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Checkbox for active selection */}
                      <button
                        type="button"
                        onClick={() => handleSetActive(isActive ? null : prompt.id)}
                        className="flex-shrink-0 mt-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded"
                        aria-label={isActive ? 'Unset as active prompt' : 'Set as active prompt'}
                      >
                        {isActive ? (
                          <CheckCircle2 className="h-5 w-5 text-primary" />
                        ) : (
                          <Circle className="h-5 w-5 text-muted-foreground hover:text-foreground transition-colors" />
                        )}
                      </button>

                      {/* Prompt content - clickable to edit */}
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={() => {
                          setEditorPrompt(prompt)
                          setDialogMode('edit')
                        }}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault()
                            setEditorPrompt(prompt)
                            setDialogMode('edit')
                          }
                        }}
                        className="flex-1 min-w-0 cursor-pointer"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-sm truncate">{prompt.name}</h4>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {prompt.content}
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          Updated {formatDistanceToNow(new Date(prompt.updated), { addSuffix: true })}
                        </p>
                      </div>

                      {/* Actions menu */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                            onClick={(event) => event.stopPropagation()}
                          >
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => {
                              setEditorPrompt(prompt)
                              setDialogMode('edit')
                            }}
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDeleteClick(prompt.id)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <PromptEditorDialog
        open={dialogMode !== null}
        onOpenChange={(open) => {
          if (!open) {
            setDialogMode(null)
            setEditorPrompt(null)
          }
        }}
        notebookId={notebookId}
        initialPrompt={editorPrompt ?? undefined}
      />

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDeleteConfirm}
        title="Delete Prompt"
        description="Are you sure you want to delete this prompt? This action cannot be undone."
        confirmText="Delete"
        confirmVariant="destructive"
      />
    </>
  )
}
