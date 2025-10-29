'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { type LucideIcon, FileText, StickyNote, MessageCircle } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { NotebookHeader } from '../components/NotebookHeader'
import { SourcesColumn } from '../components/SourcesColumn'
import { NotesColumn } from '../components/NotesColumn'
import { ChatColumn } from '../components/ChatColumn'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { useSources } from '@/lib/hooks/use-sources'
import { useNotes } from '@/lib/hooks/use-notes'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { motionTokens } from '@/lib/constants/design-tokens'
import { cn } from '@/lib/utils'

export type ContextMode = 'off' | 'insights' | 'full'

export interface ContextSelections {
  sources: Record<string, ContextMode>
  notes: Record<string, ContextMode>
}

export default function NotebookPage() {
  const params = useParams()

  // Ensure the notebook ID is properly decoded from URL
  const notebookId = decodeURIComponent(params.id as string)

  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId)
  const { data: sources, isLoading: sourcesLoading, refetch: refetchSources } = useSources(notebookId)
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId)

  // Context selection state
  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {}
  })

  const [panelOpenState, setPanelOpenState] = useState<Record<PanelKey, boolean>>({
    sources: true,
    notes: true
  })

  const standardEase = motionTokens.easing.standard.join(', ')
  const outEase = motionTokens.easing.out.join(', ')
  const panelTransition = `all ${motionTokens.duration.medium}s cubic-bezier(${standardEase})`
  const chatTransition = `all ${motionTokens.duration.medium}s cubic-bezier(${outEase})`

  const togglePanel = useCallback((panel: PanelKey) => {
    setPanelOpenState(prev => ({
      ...prev,
      [panel]: !prev[panel]
    }))
  }, [])

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

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full min-h-0">
              {panelOpenState.sources && (
                <div
                  className={cn(
                    'flex flex-col h-full min-h-0 overflow-hidden',
                    'transition-all',
                    panelOpenState.notes ? 'lg:col-span-1' : 'lg:col-span-2'
                  )}
                  style={{ transition: panelTransition }}
                >
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

              {panelOpenState.notes && (
                <div
                  className={cn(
                    'flex flex-col h-full min-h-0 overflow-hidden',
                    'transition-all',
                    panelOpenState.sources ? 'lg:col-span-1' : 'lg:col-span-2'
                  )}
                  style={{ transition: panelTransition }}
                >
                  <NotesColumn
                    notes={notes}
                    isLoading={notesLoading}
                    notebookId={notebookId}
                    contextSelections={contextSelections.notes}
                    onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                  />
                </div>
              )}

              <div
                className={cn(
                  'flex flex-col h-full min-h-0 overflow-hidden',
                  'transition-all',
                  (!panelOpenState.sources && !panelOpenState.notes) && 'lg:col-span-4',
                  (panelOpenState.sources && panelOpenState.notes) && 'lg:col-span-2',
                  (panelOpenState.sources !== panelOpenState.notes) && 'lg:col-span-2'
                )}
                style={{ transition: chatTransition }}
              >
                <ChatColumn
                  notebookId={notebookId}
                  contextSelections={contextSelections}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}

type PanelKey = 'sources' | 'notes'

interface PanelDefinition {
  key: PanelKey
  label: string
  icon: LucideIcon
}

const panelDefinitions: PanelDefinition[] = [
  { key: 'sources', label: 'Sources', icon: FileText },
  { key: 'notes', label: 'Notes', icon: StickyNote }
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
