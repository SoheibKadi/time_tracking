import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { FreelancerProfile } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'

export default function FreelancerProfilePage() {
  const { toast } = useToast()
  const [form, setForm] = useState<FreelancerProfile>({})

  const { data: profile, isLoading } = useQuery<FreelancerProfile>({
    queryKey: ['profile'],
    queryFn: async () => (await api.get('/v1/profile')).data,
  })

  useEffect(() => {
    if (profile) setForm(profile)
  }, [profile])

  const saveProfile = useMutation({
    mutationFn: async () => (await api.put('/v1/profile', form)).data,
    onSuccess: () => toast({ title: 'Profile saved' }),
    onError: () => toast({ title: 'Failed to save profile', variant: 'destructive' }),
  })

  const set = (key: keyof FreelancerProfile, value: string) =>
    setForm((f) => ({ ...f, [key]: value }))

  if (isLoading) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Loading profile…</p>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Profile</h1>
      <form onSubmit={(e) => { e.preventDefault(); saveProfile.mutate() }} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Business Info</CardTitle>
            <CardDescription>Used on invoices and billing documents</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Company Name</Label>
              <Input value={form.company_name ?? ''} onChange={(e) => set('company_name', e.target.value)} placeholder="Your company or name" />
            </div>
            <div className="space-y-2">
              <Label>Address</Label>
              <Textarea value={form.address ?? ''} onChange={(e) => set('address', e.target.value)} placeholder="Street, City, Country" rows={3} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tax & Invoice Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tax ID</Label>
                <Input value={form.tax_id ?? ''} onChange={(e) => set('tax_id', e.target.value)} placeholder="VAT / EIN / ABN…" />
              </div>
              <div className="space-y-2">
                <Label>Tax Label</Label>
                <Input value={form.tax_label ?? ''} onChange={(e) => set('tax_label', e.target.value)} placeholder="VAT / GST / Tax" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Invoice Number Prefix</Label>
              <Input value={form.invoice_prefix ?? ''} onChange={(e) => set('invoice_prefix', e.target.value)} placeholder="INV-" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Payment Instructions</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={form.payment_instructions ?? ''}
              onChange={(e) => set('payment_instructions', e.target.value)}
              placeholder="Bank transfer details, PayPal, Stripe link…"
              rows={4}
            />
          </CardContent>
        </Card>

        <Button type="submit" disabled={saveProfile.isPending}>
          {saveProfile.isPending ? 'Saving…' : 'Save Profile'}
        </Button>
      </form>
    </div>
  )
}
