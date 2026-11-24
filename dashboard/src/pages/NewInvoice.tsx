import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { format } from 'date-fns'
import { api } from '@/lib/api'
import type { Contract } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { ArrowLeft } from 'lucide-react'

export default function NewInvoice() {
  const navigate = useNavigate()
  const { toast } = useToast()

  const [contractId, setContractId] = useState('')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [taxRate, setTaxRate] = useState('0')
  const [dueAt, setDueAt] = useState('')
  const [notes, setNotes] = useState('')

  const { data: contracts = [] } = useQuery<Contract[]>({
    queryKey: ['contracts'],
    queryFn: async () => (await api.get('/v1/contracts')).data,
  })

  const selectedContract = contracts.find((c) => c.id === contractId)

  const createInvoice = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/v1/invoices', {
        contract_id: contractId,
        period_start: periodStart,
        period_end: periodEnd,
        tax_rate: parseFloat(taxRate) || 0,
        due_at: dueAt || undefined,
        notes: notes || undefined,
      })
      return data
    },
    onSuccess: () => {
      toast({ title: 'Invoice created' })
      navigate('/dashboard/invoices')
    },
    onError: () => toast({ title: 'Failed to create invoice', variant: 'destructive' }),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!contractId || !periodStart || !periodEnd) {
      toast({ title: 'Please fill all required fields', variant: 'destructive' })
      return
    }
    createInvoice.mutate()
  }

  return (
    <div className="p-8 max-w-2xl">
      <Button variant="ghost" onClick={() => navigate('/dashboard/invoices')} className="-ml-2 mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Invoices
      </Button>

      <h1 className="text-2xl font-bold mb-6">New Invoice</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Invoice Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Contract *</Label>
              <Select value={contractId} onValueChange={setContractId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a contract" />
                </SelectTrigger>
                <SelectContent>
                  {contracts.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Period Start *</Label>
                <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label>Period End *</Label>
                <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} required />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tax Rate (%)</Label>
                <Input type="number" step="0.01" min="0" max="100" value={taxRate} onChange={(e) => setTaxRate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Due Date</Label>
                <Input type="date" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes…" />
            </div>
          </CardContent>
        </Card>

        {/* Summary Preview */}
        {selectedContract && periodStart && periodEnd && (
          <Card className="bg-muted/40">
            <CardHeader>
              <CardTitle className="text-base">Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Contract</span>
                <span>{selectedContract.title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Period</span>
                <span>{format(new Date(periodStart), 'MMM d')} – {format(new Date(periodEnd), 'MMM d, yyyy')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Rate</span>
                <span>${selectedContract.hourly_rate}/hr</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tax Rate</span>
                <span>{taxRate}%</span>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/dashboard/invoices')}>Cancel</Button>
          <Button type="submit" disabled={createInvoice.isPending}>
            {createInvoice.isPending ? 'Creating…' : 'Create Draft Invoice'}
          </Button>
        </div>
      </form>
    </div>
  )
}
