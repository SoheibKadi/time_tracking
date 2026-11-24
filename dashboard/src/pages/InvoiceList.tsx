import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format, parseISO, isPast } from 'date-fns'
import { Plus, Download, Send, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'
import type { Invoice } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'

function invoiceStatusVariant(invoice: Invoice): 'muted' | 'info' | 'success' | 'destructive' {
  if (invoice.status === 'paid') return 'success'
  if (invoice.status === 'sent') {
    if (invoice.due_at && isPast(parseISO(invoice.due_at))) return 'destructive'
    return 'info'
  }
  return 'muted'
}

function invoiceStatusLabel(invoice: Invoice): string {
  if (invoice.status === 'sent' && invoice.due_at && isPast(parseISO(invoice.due_at))) return 'Overdue'
  return invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)
}

export default function InvoiceList() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: invoices = [] } = useQuery<Invoice[]>({
    queryKey: ['invoices'],
    queryFn: async () => (await api.get('/v1/invoices')).data,
  })

  const updateInvoice = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Invoice> }) =>
      (await api.patch(`/v1/invoices/${id}`, data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: () => toast({ title: 'Failed to update invoice', variant: 'destructive' }),
  })

  const downloadPDF = async (id: string, number: string) => {
    try {
      const response = await api.get(`/v1/invoices/${id}/pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice-${number}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast({ title: 'Failed to download PDF', variant: 'destructive' })
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Invoices</h1>
        <Button asChild>
          <Link to="/dashboard/invoices/new">
            <Plus className="h-4 w-4" /> New Invoice
          </Link>
        </Button>
      </div>

      {invoices.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">No invoices yet.</div>
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Number</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Hours</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Due</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {format(parseISO(invoice.period_start), 'MMM d')} – {format(parseISO(invoice.period_end), 'MMM d, yyyy')}
                  </TableCell>
                  <TableCell>{invoice.total_hours.toFixed(1)}h</TableCell>
                  <TableCell className="font-medium">${invoice.total.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={invoiceStatusVariant(invoice)}>
                      {invoiceStatusLabel(invoice)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {invoice.due_at ? format(parseISO(invoice.due_at), 'MMM d, yyyy') : '—'}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1 justify-end">
                      <Button size="sm" variant="ghost" onClick={() => downloadPDF(invoice.id, invoice.invoice_number)}>
                        <Download className="h-4 w-4" />
                      </Button>
                      {invoice.status === 'draft' && (
                        <Button size="sm" variant="ghost" title="Mark as Sent"
                          onClick={() => updateInvoice.mutate({ id: invoice.id, data: { status: 'sent' } })}
                          disabled={updateInvoice.isPending}>
                          <Send className="h-4 w-4" />
                        </Button>
                      )}
                      {invoice.status === 'sent' && (
                        <Button size="sm" variant="ghost" title="Mark as Paid"
                          onClick={() => updateInvoice.mutate({ id: invoice.id, data: { status: 'paid', paid_at: new Date().toISOString() } })}
                          disabled={updateInvoice.isPending}>
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
