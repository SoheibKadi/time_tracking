import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { Clock, RefreshCw, Image, AlertTriangle } from 'lucide-react'
import { publicApi } from '@/lib/api'
import type { ShareView, ShareWindow } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

function windowBadgeVariant(status: ShareWindow['status']): 'success' | 'warning' | 'muted' | 'outline' {
  switch (status) {
    case 'submitted': return 'success'
    case 'disputed': return 'warning'
    case 'accepted_dispute': return 'muted'
    case 'rejected_dispute': return 'success'
    case 'deleted': return 'muted'
    default: return 'outline'
  }
}

function windowBadgeLabel(status: ShareWindow['status']): string {
  switch (status) {
    case 'submitted': return 'Submitted'
    case 'disputed': return 'Disputed'
    case 'accepted_dispute': return 'Dispute Accepted'
    case 'rejected_dispute': return 'Dispute Rejected'
    case 'deleted': return 'Deleted'
    default: return status
  }
}

function activityBadge(level?: number) {
  if (level === undefined) return null
  if (level <= 3) return <span className="inline-flex items-center rounded px-2 py-0.5 text-xs bg-red-100 text-red-700">Low {level}/10</span>
  if (level <= 6) return <span className="inline-flex items-center rounded px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700">Mid {level}/10</span>
  return <span className="inline-flex items-center rounded px-2 py-0.5 text-xs bg-green-100 text-green-700">High {level}/10</span>
}

interface ScreenshotThumbProps {
  token: string
  screenshotId: string
  thumbnailUrl?: string
}

function ScreenshotThumb({ token, screenshotId, thumbnailUrl }: ScreenshotThumbProps) {
  const [revealed, setRevealed] = useState(false)
  const [fullSrc, setFullSrc] = useState<string | null>(null)

  const handleClick = async () => {
    if (!revealed) {
      setRevealed(true)
      return
    }
    try {
      const { data } = await publicApi.get(`/share/${token}/screenshots/${screenshotId}`)
      setFullSrc(data.url)
    } catch {
      // ignore
    }
  }

  return (
    <>
      <button
        onClick={handleClick}
        className="relative w-20 h-12 rounded overflow-hidden bg-slate-100 border group cursor-pointer"
        title={revealed ? 'View full screenshot' : 'Click to reveal'}
      >
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt="screenshot"
            className={cn('w-full h-full object-cover transition-all', !revealed && 'blur-sm')}
          />
        ) : (
          <div className={cn('w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-200 to-slate-300', !revealed && 'blur-sm')}>
            <Image className="h-5 w-5 text-slate-400" />
          </div>
        )}
        {!revealed && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <span className="text-xs text-white font-medium">Reveal</span>
          </div>
        )}
      </button>
      {fullSrc && (
        <Dialog open onOpenChange={() => setFullSrc(null)}>
          <DialogContent className="max-w-5xl p-2">
            <img src={fullSrc} alt="Screenshot full" className="w-full rounded" />
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}

interface DisputeDialogProps {
  window: ShareWindow
  token: string
  onClose: () => void
  onDisputed: () => void
}

function DisputeDialog({ window: win, token, onClose, onDisputed }: DisputeDialogProps) {
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const queryClient = useQueryClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await publicApi.patch(`/share/${token}/windows/${win.id}/dispute`, { reason: reason || undefined })
      queryClient.invalidateQueries({ queryKey: ['share', token] })
      onDisputed()
      onClose()
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dispute Time Window</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="text-sm text-muted-foreground">
            {format(parseISO(win.started_at), 'MMM d, yyyy HH:mm')} – {format(parseISO(win.ended_at), 'HH:mm')}
            {' · '}{win.duration_minutes} min
          </div>
          <div className="space-y-2">
            <Label>Reason (optional)</Label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Describe why you are disputing this time window…"
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" variant="destructive" disabled={loading}>
              {loading ? 'Submitting…' : 'Submit Dispute'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function ClientSharePage() {
  const { token } = useParams<{ token: string }>()
  const [disputingWindow, setDisputingWindow] = useState<ShareWindow | null>(null)

  const { data, isLoading, isError, dataUpdatedAt } = useQuery<ShareView>({
    queryKey: ['share', token],
    queryFn: async () => (await publicApi.get(`/share/${token}`)).data,
    enabled: !!token,
    refetchInterval: 60_000,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground">Loading…</p>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-10 w-10 text-destructive mx-auto mb-3" />
          <p className="text-lg font-medium">Share link not found</p>
          <p className="text-muted-foreground mt-1">This link may have expired or been revoked.</p>
        </div>
      </div>
    )
  }

  // Group windows by date
  const grouped = data.windows.reduce<Record<string, ShareWindow[]>>((acc, w) => {
    const day = format(parseISO(w.started_at), 'EEEE, MMMM d, yyyy')
    if (!acc[day]) acc[day] = []
    acc[day].push(w)
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-6 py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Clock className="h-5 w-5 text-primary" />
                <h1 className="text-xl font-bold">{data.contract_title}</h1>
              </div>
              <p className="text-muted-foreground">
                <span className="font-medium text-foreground">{data.billable_hours.toFixed(2)}h</span> billable at ${data.hourly_rate}/hr
              </p>
            </div>
            <div className="text-right">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-green-100 text-green-700 text-xs px-3 py-1 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                Live — refreshes automatically
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Updated {format(new Date(dataUpdatedAt), 'HH:mm:ss')}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
        {Object.keys(grouped).length === 0 && (
          <p className="text-center text-muted-foreground py-12">No time windows recorded yet.</p>
        )}
        {Object.entries(grouped).map(([day, windows]) => (
          <div key={day}>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">{day}</h2>
            <div className="space-y-2">
              {windows.map((w) => (
                <div
                  key={w.id}
                  className={cn(
                    'bg-white rounded-lg border p-4 flex items-start gap-4',
                    (w.status === 'deleted' || w.status === 'accepted_dispute') && 'opacity-50'
                  )}
                >
                  {/* Screenshot */}
                  {w.has_screenshot && w.screenshot_id && token && (
                    <ScreenshotThumb token={token} screenshotId={w.screenshot_id} thumbnailUrl={w.thumbnail_url} />
                  )}
                  {!w.has_screenshot && (
                    <div className="w-20 h-12 rounded bg-slate-100 border flex items-center justify-center shrink-0">
                      <Image className="h-5 w-5 text-slate-300" />
                    </div>
                  )}

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={cn('text-sm font-medium', (w.status === 'deleted' || w.status === 'accepted_dispute') && 'line-through')}>
                        {format(parseISO(w.started_at), 'HH:mm')} – {format(parseISO(w.ended_at), 'HH:mm')}
                      </span>
                      <span className="text-xs text-muted-foreground">{w.duration_minutes} min</span>
                      {activityBadge(w.activity_level)}
                      {w.is_manual && (
                        <span className="text-xs bg-purple-100 text-purple-700 rounded px-1.5 py-0.5">Manual</span>
                      )}
                    </div>
                    {w.manual_reason && (
                      <p className="text-xs text-muted-foreground mt-1 italic">"{w.manual_reason}"</p>
                    )}
                    {w.status === 'disputed' && w.dispute_reason && (
                      <p className="text-xs text-yellow-700 mt-1 bg-yellow-50 rounded px-2 py-1">
                        Disputed: {w.dispute_reason}
                      </p>
                    )}
                  </div>

                  {/* Right side */}
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <Badge variant={windowBadgeVariant(w.status)} className={cn('text-xs', (w.status === 'deleted' || w.status === 'accepted_dispute') && 'line-through')}>
                      {windowBadgeLabel(w.status)}
                    </Badge>
                    {w.status === 'submitted' && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs text-yellow-700 border-yellow-200 hover:bg-yellow-50"
                        onClick={() => setDisputingWindow(w)}
                      >
                        <AlertTriangle className="h-3 w-3" />
                        Dispute
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {disputingWindow && token && (
        <DisputeDialog
          window={disputingWindow}
          token={token}
          onClose={() => setDisputingWindow(null)}
          onDisputed={() => setDisputingWindow(null)}
        />
      )}
    </div>
  )
}
