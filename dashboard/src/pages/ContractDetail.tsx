import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, differenceInMinutes, differenceInSeconds, parseISO } from 'date-fns'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Copy, RefreshCw, ArrowLeft, Check, X, Eye, Download } from 'lucide-react'
import { api, exportContractCSV, deleteScreenshot } from '@/lib/api'
import type { Contract, TimeWindow } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

function activityColor(level?: number) {
  if (level === undefined) return 'bg-gray-200'
  if (level <= 3) return 'bg-red-500'
  if (level <= 6) return 'bg-yellow-500'
  return 'bg-green-500'
}

function windowStatusVariant(status: TimeWindow['status']) {
  switch (status) {
    case 'submitted': return 'success'
    case 'disputed': return 'warning'
    case 'accepted_dispute': return 'muted'
    case 'rejected_dispute': return 'success'
    case 'deleted': return 'muted'
    default: return 'outline'
  }
}

function windowStatusLabel(status: TimeWindow['status']) {
  switch (status) {
    case 'accepted_dispute': return 'Dispute Accepted'
    case 'rejected_dispute': return 'Dispute Rejected'
    default: return status.charAt(0).toUpperCase() + status.slice(1)
  }
}

interface ScreenshotThumbProps {
  windowId: string
  windowEndedAt?: string
  contractId?: string
}

function ScreenshotThumb({ windowId, windowEndedAt, contractId }: ScreenshotThumbProps) {
  const [revealed, setRevealed] = useState(false)
  const [fullSrc, setFullSrc] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [screenshotId, setScreenshotId] = useState<string | null>(null)
  const [remaining, setRemaining] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!windowEndedAt) return
    if (timerRef.current) clearInterval(timerRef.current)
    const age = differenceInSeconds(new Date(), parseISO(windowEndedAt))
    const rem = Math.max(0, 60 - age)
    if (rem <= 0) return
    setRemaining(rem)
    timerRef.current = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          if (timerRef.current) clearInterval(timerRef.current)
          return 0
        }
        return r - 1
      })
    }, 1000)
    api.get<{ id?: string; url: string }>(`/v1/screenshots/${windowId}/image`)
      .then(({ data }) => { if (data.id) setScreenshotId(data.id) })
      .catch(() => {})
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [windowId, windowEndedAt])

  const handleClick = async () => {
    if (!revealed) {
      setRevealed(true)
      return
    }
    setLoading(true)
    try {
      const { data } = await api.get<{ id?: string; url: string }>(`/v1/screenshots/${windowId}/image`)
      setFullSrc(data.url)
      if (data.id) setScreenshotId(data.id)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!screenshotId) return
    try {
      await deleteScreenshot(screenshotId)
      queryClient.invalidateQueries({ queryKey: ['windows', contractId] })
      toast({ title: 'Screenshot deleted' })
      setRemaining(0)
    } catch {
      toast({ title: 'Failed to delete screenshot', variant: 'destructive' })
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleClick}
        className={cn(
          'relative w-16 h-10 rounded overflow-hidden bg-muted border border-border group',
          loading && 'opacity-50'
        )}
        title={revealed ? 'Click to view full' : 'Click to reveal'}
      >
        <div className={cn('w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center transition-all', !revealed && 'blur-sm')}>
          <Eye className="h-4 w-4 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        {!revealed && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Eye className="h-4 w-4 text-slate-600" />
          </div>
        )}
      </button>
      {remaining > 0 && screenshotId && (
        <Button size="sm" variant="destructive" className="text-xs h-7 px-2" onClick={handleDelete}>
          Delete ({remaining}s)
        </Button>
      )}
      {fullSrc && (
        <Dialog open onOpenChange={() => setFullSrc(null)}>
          <DialogContent className="max-w-4xl">
            <img src={fullSrc} alt="Screenshot" className="w-full rounded" />
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [csvOpen, setCsvOpen] = useState(false)
  const [csvFrom, setCsvFrom] = useState('')
  const [csvTo, setCsvTo] = useState('')
  const [csvLoading, setCsvLoading] = useState(false)

  const { data: contracts } = useQuery<Contract[]>({
    queryKey: ['contracts'],
    queryFn: async () => (await api.get('/v1/contracts')).data,
  })
  const contract = contracts?.find((c) => c.id === id)

  const { data: windows = [] } = useQuery<TimeWindow[]>({
    queryKey: ['windows', id],
    queryFn: async () => (await api.get(`/v1/windows/contract/${id}`)).data,
    enabled: !!id,
  })

  const resolveDispute = useMutation({
    mutationFn: async ({ windowId, accept }: { windowId: string; accept: boolean }) => {
      const { data } = await api.patch(`/v1/windows/${windowId}/dispute/resolve`, { accept })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['windows', id] })
      toast({ title: 'Dispute resolved' })
    },
    onError: () => toast({ title: 'Failed to resolve dispute', variant: 'destructive' }),
  })

  const regenerateToken = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/contracts/${id}/regenerate-token`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      toast({ title: 'Share token regenerated' })
    },
    onError: () => toast({ title: 'Failed to regenerate token', variant: 'destructive' }),
  })

  const copyShareUrl = () => {
    if (!contract) return
    const url = `${window.location.origin}/share/${contract.share_token}`
    navigator.clipboard.writeText(url)
    toast({ title: 'Share URL copied' })
  }

  const handleCSVDownload = async () => {
    if (!csvFrom || !csvTo || !id) return
    setCsvLoading(true)
    try {
      const response = await exportContractCSV(id, csvFrom, csvTo)
      const blob = new Blob([response.data as BlobPart], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `contract-${id}-${csvFrom}-to-${csvTo}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      setCsvOpen(false)
      toast({ title: 'CSV downloaded' })
    } catch {
      toast({ title: 'Failed to export CSV', variant: 'destructive' })
    } finally {
      setCsvLoading(false)
    }
  }

  // Build chart data: activity per day
  const chartData = windows
    .filter((w) => w.activity_level !== undefined)
    .reduce<Record<string, { date: string; total: number; count: number }>>((acc, w) => {
      const day = format(parseISO(w.started_at), 'MMM d')
      if (!acc[day]) acc[day] = { date: day, total: 0, count: 0 }
      acc[day].total += w.activity_level!
      acc[day].count++
      return acc
    }, {})

  const chartPoints = Object.values(chartData).map((d) => ({
    date: d.date,
    activity: Math.round((d.total / d.count) * 10) / 10,
  }))

  const disputedWindows = windows.filter((w) => w.status === 'disputed')

  if (!contract) {
    return (
      <div className="p-8">
        <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <p className="text-muted-foreground">Loading contract…</p>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <Button variant="ghost" onClick={() => navigate('/dashboard')} className="-ml-2">
        <ArrowLeft className="h-4 w-4" /> Back to Contracts
      </Button>

      {/* Contract Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">{contract.title}</h1>
              {contract.client_profile && (
                <p className="text-muted-foreground mt-1">{contract.client_profile.name}</p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={contract.status === 'active' ? 'success' : contract.status === 'paused' ? 'warning' : 'muted'} className="capitalize text-sm px-3 py-1">
                {contract.status}
              </Badge>
              <span className="font-semibold text-lg">${contract.hourly_rate}/hr</span>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button variant="outline" size="sm" onClick={copyShareUrl}>
              <Copy className="h-4 w-4" /> Copy Share URL
            </Button>
            <Button variant="outline" size="sm" onClick={() => regenerateToken.mutate()} disabled={regenerateToken.isPending}>
              <RefreshCw className={cn('h-4 w-4', regenerateToken.isPending && 'animate-spin')} />
              Regenerate Token
            </Button>
            <Button variant="outline" size="sm" onClick={() => setCsvOpen(true)}>
              <Download className="h-4 w-4" /> Export CSV
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* CSV Export Dialog */}
      <Dialog open={csvOpen} onOpenChange={setCsvOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Export CSV</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="csv-from">From date</Label>
              <Input
                id="csv-from"
                type="date"
                value={csvFrom}
                onChange={(e) => setCsvFrom(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="csv-to">To date</Label>
              <Input
                id="csv-to"
                type="date"
                value={csvTo}
                onChange={(e) => setCsvTo(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCsvOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCSVDownload}
              disabled={csvLoading || !csvFrom || !csvTo}
            >
              {csvLoading ? 'Downloading…' : 'Download'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Activity Chart */}
      {chartPoints.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartPoints}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="activity" fill="hsl(var(--primary))" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Disputed Windows */}
      {disputedWindows.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardHeader>
            <CardTitle className="text-base text-yellow-800">Disputed Windows ({disputedWindows.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {disputedWindows.map((w) => (
              <div key={w.id} className="flex items-start justify-between gap-4 p-3 bg-white rounded-md border border-yellow-100">
                <div className="text-sm">
                  <p className="font-medium">{format(parseISO(w.started_at), 'MMM d, yyyy HH:mm')} – {format(parseISO(w.ended_at), 'HH:mm')}</p>
                  {w.dispute_reason && <p className="text-muted-foreground mt-1">Reason: {w.dispute_reason}</p>}
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="outline" className="text-green-700 border-green-200 hover:bg-green-50"
                    onClick={() => resolveDispute.mutate({ windowId: w.id, accept: true })}
                    disabled={resolveDispute.isPending}>
                    <Check className="h-4 w-4" /> Accept
                  </Button>
                  <Button size="sm" variant="outline" className="text-red-700 border-red-200 hover:bg-red-50"
                    onClick={() => resolveDispute.mutate({ windowId: w.id, accept: false })}
                    disabled={resolveDispute.isPending}>
                    <X className="h-4 w-4" /> Reject
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Time Windows Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Time Windows ({windows.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date / Time</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Activity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Screenshot</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {windows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">No time windows yet</TableCell>
                </TableRow>
              ) : (
                windows.map((w) => {
                  const dur = differenceInMinutes(parseISO(w.ended_at), parseISO(w.started_at))
                  return (
                    <TableRow key={w.id}>
                      <TableCell className="text-sm">
                        <div>{format(parseISO(w.started_at), 'MMM d, yyyy')}</div>
                        <div className="text-muted-foreground">
                          {format(parseISO(w.started_at), 'HH:mm')} – {format(parseISO(w.ended_at), 'HH:mm')}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{Math.floor(dur / 60)}h {dur % 60}m</TableCell>
                      <TableCell>
                        {w.activity_level !== undefined ? (
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={cn('h-full rounded-full', activityColor(w.activity_level))}
                                style={{ width: `${(w.activity_level / 10) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground">{w.activity_level}/10</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={windowStatusVariant(w.status)} className={cn('text-xs', w.status === 'deleted' || w.status === 'accepted_dispute' ? 'line-through' : '')}>
                          {windowStatusLabel(w.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <ScreenshotThumb windowId={w.id} windowEndedAt={w.ended_at} contractId={id} />
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
