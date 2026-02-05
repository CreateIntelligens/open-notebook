'use client'

import { useCallback, useState, useEffect, useMemo } from 'react'
import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { NotebookHeader } from '../components/NotebookHeader'
import { SourcesColumn } from '../components/SourcesColumn'
import { NotesColumn } from '../components/NotesColumn'
import { PromptsColumn } from '../components/PromptsColumn'
import { ChatColumn } from '../components/ChatColumn'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useNotes } from '@/lib/hooks/use-notes'
import { usePrompts, useActivePrompt } from '@/lib/hooks/use-prompts'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { cn } from '@/lib/utils'
import { type LucideIcon, FileText, StickyNote, MessageSquare, MessageCircle } from 'lucide-react'

export type ContextMode = 'off' | 'insights' | 'full'

export interface ContextSelections {
  sources: Record<string, ContextMode>
  notes: Record<string, ContextMode>
}

type PanelKey = 'sources' | 'notes' | 'prompts' | 'chat'

interface PanelDefinition {
  key: PanelKey
  label: string
  icon: LucideIcon
}

const panelDefinitions: PanelDefinition[] = [
  { key: 'sources', label: 'Sources', icon: FileText },
  { key: 'notes', label: 'Notes', icon: StickyNote },
  { key: 'prompts', label: 'Prompts', icon: MessageSquare },
  { key: 'chat', label: 'Chat', icon: MessageCircle },
]

interface PanelToggleProps {
  label: string
  icon: LucideIcon
  active: boolean
  onClick: () => void
}

function PanelToggle({ label, icon: Icon, active, onClick }: PanelToggleProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'group relative flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
        active
          ? 'bg-primary text-primary-foreground shadow-sm hover:bg-primary/90'
          : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
      )}
    >
      <Icon className="h-3.5 w-3.5 transition-transform duration-200 group-hover:scale-105" />
      <span className="text-xs">{label}</span>
    </button>
  )
}

export default function NotebookPage() {
  const params = useParams()

  // Ensure the notebook ID is properly decoded from URL
  const notebookId = params?.id ? decodeURIComponent(params.id as string) : ''

  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId)
  const {
    sources,
    isLoading: sourcesLoading,
    refetch: refetchSources,
  } = useNotebookSources(notebookId)
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId)
  const { data: prompts, isLoading: promptsLoading } = usePrompts(notebookId)
  const { data: activePrompt } = useActivePrompt(notebookId)

  // Panel toggle state
  const [panelOpenState, setPanelOpenState] = useState<Record<PanelKey, boolean>>({
    sources: true,
    notes: true,
    prompts: true,
    chat: true,
  })

  const togglePanel = useCallback((panel: PanelKey) => {
    setPanelOpenState(prev => ({
      ...prev,
      [panel]: !prev[panel]
    }))
  }, [])

  // Context selection state
  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {}
  })

  // Initialize default selections when sources/notes load
  useEffect(() => {
    if (sources && sources.length > 0) {
      setContextSelections(prev => {
        const newSourceSelections = { ...prev.sources }
        sources.forEach(source => {
          // Only set default if not already set
          if (!(source.id in newSourceSelections)) {
            // Default to 'insights' if has insights, otherwise 'full'
            newSourceSelections[source.id] = source.insights_count > 0 ? 'insights' : 'full'
          }
        })
        return { ...prev, sources: newSourceSelections }
      })
    }
  }, [sources])

  useEffect(() => {
    if (notes && notes.length > 0) {
      setContextSelections(prev => {
        const newNoteSelections = { ...prev.notes }
        notes.forEach(note => {
          // Only set default if not already set
          if (!(note.id in newNoteSelections)) {
            // Notes default to 'full'
            newNoteSelections[note.id] = 'full'
          }
        })
        return { ...prev, notes: newNoteSelections }
      })
    }
  }, [notes])

  // Handler to update context selection
  const handleContextModeChange = (itemId: string, mode: ContextMode, type: 'source' | 'note') => {
    setContextSelections(prev => ({
      ...prev,
      [type === 'source' ? 'sources' : 'notes']: {
        ...(type === 'source' ? prev.sources : prev.notes),
        [itemId]: mode
      }
    }))
  }

  const gridColumnsClass = useMemo(() => {
    const openCount = panelDefinitions.reduce(
      (count, panel) => count + (panelOpenState[panel.key] ? 1 : 0),
      0
    )
    if (openCount <= 1) return 'lg:grid-cols-1'
    if (openCount === 2) return 'lg:grid-cols-2'
    if (openCount === 3) return 'lg:grid-cols-3'
    return 'lg:grid-cols-4'
  }, [panelOpenState])

  if (notebookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!notebook) {
    return (
      <AppShell>
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">Notebook Not Found</h1>
          <p className="text-muted-foreground">The requested notebook could not be found.</p>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col flex-1 min-h-0">
        <div className="flex-shrink-0 p-6 pb-0">
          <NotebookHeader notebook={notebook} />
        </div>

        <div className="flex-1 p-6 pt-6 overflow-hidden">
          <div className="flex h-full flex-col gap-6 min-h-0">
            <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card px-3 py-2">
              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <MessageCircle className="h-3.5 w-3.5" />
                顯示面板
              </div>
              <div className="flex flex-wrap gap-2">
                {panelDefinitions.map(panel => (
                  <PanelToggle
                    key={panel.key}
                    label={panel.label}
                    icon={panel.icon}
                    active={panelOpenState[panel.key]}
                    onClick={() => togglePanel(panel.key)}
                  />
                ))}
              </div>
            </div>

            <div className={cn('grid grid-cols-1 gap-6 h-full min-h-0', gridColumnsClass)}>
              {/* Sources Column */}
              {panelOpenState.sources && (
                <div className="flex flex-col h-full min-h-0 overflow-hidden">
                  <SourcesColumn
                    sources={sources}
                    isLoading={sourcesLoading}
                    notebookId={notebookId}
                    notebookName={notebook?.name}
                    onRefresh={refetchSources}
                    contextSelections={contextSelections.sources}
                    onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                  />
                </div>
              )}

              {/* Notes Column */}
              {panelOpenState.notes && (
                <div className="flex flex-col h-full min-h-0 overflow-hidden">
                  <NotesColumn
                    notes={notes}
                    isLoading={notesLoading}
                    notebookId={notebookId}
                    contextSelections={contextSelections.notes}
                    onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                  />
                </div>
              )}

              {/* Prompts Column */}
              {panelOpenState.prompts && (
                <div className="flex flex-col h-full min-h-0 overflow-hidden">
                  <PromptsColumn
                    prompts={prompts}
                    activePromptId={activePrompt?.id}
                    isLoading={promptsLoading}
                    notebookId={notebookId}
                  />
                </div>
              )}

              {/* Chat Column */}
              {panelOpenState.chat && (
                <div className="flex flex-col h-full min-h-0 overflow-hidden">
                  <ChatColumn
                    notebookId={notebookId}
                    contextSelections={contextSelections}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
