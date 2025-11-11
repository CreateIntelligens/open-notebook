'use client'

import { useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Loader2, Plus, Settings, Trash2 } from 'lucide-react'
import {
  usePromptPresets,
  useCreatePromptPreset,
  useUpdatePromptPreset,
  useDeletePromptPreset,
} from '@/lib/hooks/use-transformations'
import { cn } from '@/lib/utils'

const tokens = {
  panel: 'rounded-2xl border border-border/50 bg-card/80 shadow-lg shadow-primary/5 backdrop-blur',
  section: 'rounded-xl border border-border/40 bg-muted/20 px-4 py-4 backdrop-blur-sm',
  label: 'text-[11px] font-semibold uppercase tracking-wide text-muted-foreground',
}

export function DefaultPromptEditor() {
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null)
  const [promptName, setPromptName] = useState('')
  const [promptBody, setPromptBody] = useState('')

  const {
    data: promptPresets,
    isLoading,
    isRefetching,
  } = usePromptPresets()
  const createPrompt = useCreatePromptPreset()
  const updatePrompt = useUpdatePromptPreset()
  const deletePrompt = useDeletePromptPreset()

  const presets = useMemo(() => promptPresets ?? [], [promptPresets])
  const selectedPreset = useMemo(
    () => presets.find((preset) => preset.prompt_id === selectedPromptId) ?? null,
    [presets, selectedPromptId]
  )

  useEffect(() => {
    if (!presets.length) {
      setSelectedPromptId(null)
      return
    }

    const stillExists = presets.some((preset) => preset.prompt_id === selectedPromptId)
    if (!selectedPromptId || !stillExists) {
      setSelectedPromptId(presets[0]?.prompt_id ?? null)
    }
  }, [presets, selectedPromptId])

  useEffect(() => {
    if (!selectedPreset) {
      setPromptName('')
      setPromptBody('')
      return
    }

    setPromptName(selectedPreset.name)
    setPromptBody(selectedPreset.transformation_instructions || '')
  }, [selectedPreset])

  const isDirty = selectedPreset
    ? selectedPreset.name !== promptName ||
      (selectedPreset.transformation_instructions || '') !== promptBody
    : !!promptName || !!promptBody

  const isBusy = isLoading || isRefetching
  const canEditActivePrompt = !!selectedPreset && !createPrompt.isPending && !deletePrompt.isPending

  const handleSave = () => {
    if (!selectedPreset || !isDirty) return

    updatePrompt.mutate({
      promptId: selectedPreset.prompt_id,
      data: {
        name: promptName,
        transformation_instructions: promptBody,
      },
    })
  }

  const handleReset = () => {
    if (!selectedPreset) return
    setPromptName(selectedPreset.name)
    setPromptBody(selectedPreset.transformation_instructions || '')
  }

  const handleCreatePrompt = async () => {
    const fallbackName = `Prompt ${presets.length + 1}`
    try {
      const newPrompt = await createPrompt.mutateAsync({
        name: fallbackName,
        transformation_instructions: '',
      })
      setSelectedPromptId(newPrompt.prompt_id)
      setPromptName(newPrompt.name)
      setPromptBody(newPrompt.transformation_instructions || '')
    } catch {
      // errors handled by toast hook
    }
  }

  const handleDeletePrompt = async () => {
    if (!selectedPreset) return
    const activeId = selectedPreset.prompt_id

    try {
      await deletePrompt.mutateAsync(activeId)
      const nextPrompt = presets.find((preset) => preset.prompt_id !== activeId)
      setSelectedPromptId(nextPrompt?.prompt_id ?? null)
      if (!nextPrompt) {
        setPromptName('')
        setPromptBody('')
      }
    } catch {
      // toast handles errors
    }
  }

  const updatedLabel = selectedPreset?.updated
    ? new Date(selectedPreset.updated).toLocaleString()
    : 'Not saved yet'

  const renderSkeleton = (
    <CardContent className="space-y-4">
      <div className="h-12 w-full rounded-2xl bg-muted/40 animate-pulse" />
      <div className="h-24 w-full rounded-2xl bg-muted/40 animate-pulse" />
      <div className="h-48 w-full rounded-2xl bg-muted/40 animate-pulse" />
    </CardContent>
  )

  const renderEmptyState = (
    <CardContent className="space-y-6">
      <div
        className="rounded-2xl border border-dashed border-border/60 bg-muted/30 px-6 py-10 text-center backdrop-blur-sm"
        aria-live="polite"
      >
        <p className="text-lg font-semibold text-foreground">No prompt variants yet</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Create curated prompt presets and reuse them across any transformation.
        </p>
        <Button
          className="mt-6"
          onClick={handleCreatePrompt}
          disabled={createPrompt.isPending}
        >
          {createPrompt.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Create your first prompt
        </Button>
      </div>
    </CardContent>
  )

  return (
    <Card className={tokens.panel}>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Settings className="h-5 w-5" />
            </div>
            <div className="text-left">
              <CardTitle className="text-lg">Prompt presets</CardTitle>
              <CardDescription>
                Curate reusable instructions and attach them to your transformations.
              </CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>
      {isLoading && !presets.length ? (
        renderSkeleton
      ) : !presets.length ? (
        renderEmptyState
      ) : (
        <CardContent className="space-y-6">
              <div className="flex flex-col gap-4 rounded-2xl border border-border/50 bg-muted/20 p-4 backdrop-blur-sm md:flex-row md:items-center md:justify-between">
                <div className="flex-1 space-y-2">
                  <p className={tokens.label}>Active prompt preset</p>
                  <div className="flex flex-wrap items-center gap-3">
                    <Select
                      value={selectedPromptId ?? undefined}
                      onValueChange={(value) => setSelectedPromptId(value)}
                      disabled={isBusy || createPrompt.isPending || deletePrompt.isPending}
                    >
                      <SelectTrigger size="default" className="min-w-[220px]">
                        <SelectValue placeholder="Select a preset" />
                      </SelectTrigger>
                      <SelectContent>
                        {presets.map((preset) => (
                          <SelectItem key={preset.prompt_id} value={preset.prompt_id}>
                            <div className="flex flex-col text-left">
                              <span className="font-medium text-foreground">{preset.name}</span>
                              <span className="text-[11px] text-muted-foreground">{preset.prompt_id}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {isDirty && (
                      <Badge variant="outline" className="border-amber-300 bg-amber-100/60 text-amber-900">
                        Unsaved changes
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCreatePrompt}
                    disabled={createPrompt.isPending || isBusy}
                  >
                    {createPrompt.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="mr-2 h-4 w-4" />
                    )}
                    New prompt
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={!selectedPreset || deletePrompt.isPending}
                        className="text-destructive hover:text-destructive"
                      >
                        {deletePrompt.isPending ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="mr-2 h-4 w-4" />
                        )}
                        Delete
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete this prompt preset?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This action will remove <strong>{selectedPreset?.name}</strong> and any
                          transformation referencing it should be updated to avoid errors.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel disabled={deletePrompt.isPending}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={handleDeletePrompt}
                          disabled={deletePrompt.isPending}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          {deletePrompt.isPending && (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          )}
                          Delete prompt
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>

              <div className={cn(tokens.section, 'space-y-4')}>
                <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
                  <div className="space-y-2">
                    <Label htmlFor="prompt-name" className="text-sm font-medium">
                      Prompt name
                    </Label>
                    <Input
                      id="prompt-name"
                      value={promptName}
                      onChange={(event) => {
                        setPromptName(event.target.value)
                      }}
                      placeholder="e.g. Insightful Research Summary"
                      disabled={!canEditActivePrompt}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Prompt ID</Label>
                    <div className="rounded-lg border border-dashed border-border/60 bg-background/70 px-3 py-2 font-mono text-xs text-muted-foreground">
                      {selectedPreset?.prompt_id}
                    </div>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Updated {updatedLabel}
                </div>
              </div>

              <div className={cn(tokens.section, 'space-y-3')}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <Label htmlFor="prompt-body" className="text-sm font-medium">
                    Transformation instructions
                  </Label>
                  <Badge variant="outline" className="border-primary/50 text-primary">
                    Appended to every transformation that opts in
                  </Badge>
                </div>
                <Textarea
                  id="prompt-body"
                  value={promptBody}
                  onChange={(event) => {
                    setPromptBody(event.target.value)
                  }}
                  placeholder="Detail the tone, structure, and constraints you expect from the model..."
                  className="min-h-[220px] font-mono text-sm"
                  disabled={!canEditActivePrompt}
                />
                <p className="text-xs text-muted-foreground">
                  Keep prompts modular—combine them with transformation-specific instructions for maximum reuse.
                </p>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-muted-foreground">
                  Changes stay local until you save. Unsaved edits highlight in amber.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    disabled={!isDirty || !selectedPreset || updatePrompt.isPending}
                  >
                    Reset
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={!isDirty || updatePrompt.isPending || !selectedPreset || !promptName.trim()}
                  >
                    {updatePrompt.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save prompt
                  </Button>
                </div>
              </div>
            </CardContent>
        )}
      </Card>
  )
}
