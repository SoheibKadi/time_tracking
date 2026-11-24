import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { adminApi } from '@/lib/api'
import type { AdminUser, AuditLog } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'

function UsersTab() {
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteName, setInviteName] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'worker' | 'admin'>('worker')
  const [tempPassword, setTempPassword] = useState<string | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: users = [], isLoading } = useQuery<AdminUser[]>({
    queryKey: ['admin-users'],
    queryFn: async () => (await adminApi.listUsers()).data,
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminApi.updateUser(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      toast({ title: 'User updated' })
    },
    onError: () => toast({ title: 'Failed to update user', variant: 'destructive' }),
  })

  const invite = useMutation({
    mutationFn: () =>
      adminApi.inviteUser({ email: inviteEmail, name: inviteName, role: inviteRole }),
    onSuccess: (res) => {
      setTempPassword(res.data.temp_password)
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: () => toast({ title: 'Failed to invite user', variant: 'destructive' }),
  })

  const handleCloseInvite = () => {
    setInviteOpen(false)
    setTempPassword(null)
    setInviteName('')
    setInviteEmail('')
    setInviteRole('worker')
  }

  return (
    <Card className="mt-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Users</CardTitle>
        <Button onClick={() => setInviteOpen(true)}>Invite User</Button>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                  Loading…
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                  No users found
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell className="capitalize">{user.role}</TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? 'success' : 'muted'}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleActive.mutate({ id: user.id, is_active: !user.is_active })}
                      disabled={toggleActive.isPending}
                    >
                      {user.is_active ? 'Deactivate' : 'Reactivate'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>

      <Dialog open={inviteOpen} onOpenChange={(open) => { if (!open) handleCloseInvite() }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite User</DialogTitle>
          </DialogHeader>
          {tempPassword ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                User invited successfully. Share this temporary password:
              </p>
              <div className="flex gap-2">
                <Input value={tempPassword} readOnly className="font-mono" />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(tempPassword)}
                >
                  Copy
                </Button>
              </div>
              <DialogFooter>
                <Button onClick={handleCloseInvite}>Close</Button>
              </DialogFooter>
            </div>
          ) : (
            <form
              onSubmit={(e) => { e.preventDefault(); invite.mutate() }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select
                  value={inviteRole}
                  onValueChange={(v) => setInviteRole(v as 'worker' | 'admin')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="worker">Worker</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleCloseInvite}>
                  Cancel
                </Button>
                <Button type="submit" disabled={invite.isPending}>
                  {invite.isPending ? 'Inviting…' : 'Invite'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}

function AuditTab() {
  const { data: logs = [], isLoading } = useQuery<AuditLog[]>({
    queryKey: ['admin-audit'],
    queryFn: async () => (await adminApi.getAuditLog()).data,
  })

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Audit Log</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Details</TableHead>
              <TableHead>IP Address</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                  Loading…
                </TableCell>
              </TableRow>
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                  No audit logs found
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                    {format(parseISO(log.created_at), 'MMM d, yyyy HH:mm:ss')}
                  </TableCell>
                  <TableCell className="text-sm font-medium">{log.action}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {log.details ?? '—'}
                  </TableCell>
                  <TableCell className="text-sm font-mono">
                    {log.ip_address ?? '—'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

export default function AdminPanel() {
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Admin Panel</h1>
      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>
        <TabsContent value="users">
          <UsersTab />
        </TabsContent>
        <TabsContent value="audit">
          <AuditTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
