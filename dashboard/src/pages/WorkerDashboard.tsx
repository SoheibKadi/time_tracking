import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Contract } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Copy, ChevronRight, Plus } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

function statusVariant(status: Contract['status']) {
  if (status === 'active') return 'success'
  if (status === 'paused') return 'warning'
  return 'muted'
}

function getShareUrl(token: string) {
  return `${window.location.origin}/share/${token}`
}

interface NewContractForm {
  title: string
  hourly_rate: string
  weekly_hour_limit: string
  screenshot_interval_min: string
  client_name: string
  client_company: string
  client_email: string
}

export default function WorkerDashboard() {
  const { toast } = useToast()
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<NewContractForm>({
    title: '',
    hourly_rate: '',
    weekly_hour_limit: '',
    screenshot_interval_min: '10',
    client_name: '',
    client_company: '',
    client_email: '',
  })

  const { data: contracts = [], refetch } = useQuery<Contract[]>({
    queryKey: ['contracts'],
    queryFn: async () => {
      const { data } = await api.get('/v1/contracts')
      return data
    },
  })

  const copyShareUrl = (token: string) => {
    navigator.clipboard.writeText(getShareUrl(token))
    toast({ title: 'Share URL copied to clipboard' })
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post('/v1/contracts', {
        title: form.title,
        hourly_rate: parseFloat(form.hourly_rate),
        weekly_hour_limit: form.weekly_hour_limit ? parseFloat(form.weekly_hour_limit) : undefined,
        screenshot_interval_min: parseInt(form.screenshot_interval_min) || 10,
        client: {
          name: form.client_name,
          company_name: form.client_company || undefined,
          billing_email: form.client_email || undefined,
        },
      })
      toast({ title: 'Contract created' })
      setShowCreate(false)
      refetch()
    } catch {
      toast({ title: 'Failed to create contract', variant: 'destructive' })
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Contracts</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          New Contract
        </Button>
      </div>

      {contracts.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          No contracts yet. Create one to get started.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {contracts.map((contract) => (
            <Card key={contract.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-tight">{contract.title}</CardTitle>
                  <Badge variant={statusVariant(contract.status)} className="shrink-0 capitalize">
                    {contract.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Rate</span>
                  <span className="font-medium">${contract.hourly_rate}/hr</span>
                </div>
                {contract.client_profile && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Client</span>
                    <span className="font-medium">{contract.client_profile.name}</span>
                  </div>
                )}
                <div className="flex gap-2 pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-xs"
                    onClick={() => copyShareUrl(contract.share_token)}
                  >
                    <Copy className="h-3 w-3" />
                    Share URL
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1 text-xs" asChild>
                    <Link to={`/dashboard/contracts/${contract.id}`}>
                      View
                      <ChevronRight className="h-3 w-3" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>New Contract</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="space-y-1">
              <Label>Title</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Hourly Rate ($)</Label>
                <Input type="number" step="0.01" value={form.hourly_rate} onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })} required />
              </div>
              <div className="space-y-1">
                <Label>Weekly Limit (hrs)</Label>
                <Input type="number" value={form.weekly_hour_limit} onChange={(e) => setForm({ ...form, weekly_hour_limit: e.target.value })} placeholder="optional" />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Screenshot Interval (min)</Label>
              <Input type="number" value={form.screenshot_interval_min} onChange={(e) => setForm({ ...form, screenshot_interval_min: e.target.value })} />
            </div>
            <div className="border-t pt-3 space-y-1">
              <p className="text-sm font-medium text-muted-foreground mb-2">Client Info</p>
              <Label>Client Name</Label>
              <Input value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Company (optional)</Label>
                <Input value={form.client_company} onChange={(e) => setForm({ ...form, client_company: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label>Billing Email</Label>
                <Input type="email" value={form.client_email} onChange={(e) => setForm({ ...form, client_email: e.target.value })} />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button type="submit" disabled={creating}>{creating ? 'Creating…' : 'Create'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
