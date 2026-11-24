import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { blocklistApi } from '@/lib/api'
import type { BlocklistItem } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import { Trash2 } from 'lucide-react'

export default function BlocklistPage() {
  const [newPattern, setNewPattern] = useState('')
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: items = [], isLoading } = useQuery<BlocklistItem[]>({
    queryKey: ['blocklist'],
    queryFn: async () => (await blocklistApi.list()).data,
  })

  const addItem = useMutation({
    mutationFn: (pattern: string) => blocklistApi.add(pattern),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocklist'] })
      setNewPattern('')
      toast({ title: 'Pattern added' })
    },
    onError: () => toast({ title: 'Failed to add pattern', variant: 'destructive' }),
  })

  const removeItem = useMutation({
    mutationFn: (id: string) => blocklistApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocklist'] })
      toast({ title: 'Pattern removed' })
    },
    onError: () => toast({ title: 'Failed to remove pattern', variant: 'destructive' }),
  })

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPattern.trim()) return
    addItem.mutate(newPattern.trim())
  }

  return (
    <div className="p-8 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Application Blocklist</h1>
        <p className="text-muted-foreground mt-1">
          Add process or window title patterns to blur in screenshots. Matching is case-insensitive
          substring.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add Pattern</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="flex gap-2">
            <Input
              placeholder="e.g. 1Password"
              value={newPattern}
              onChange={(e) => setNewPattern(e.target.value)}
            />
            <Button type="submit" disabled={addItem.isPending || !newPattern.trim()}>
              Add
            </Button>
          </form>
          <p className="text-xs text-muted-foreground mt-2">
            Examples: 1Password, KeePass, Bitwarden, LastPass
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Current Patterns{' '}
            {!isLoading && <span className="font-normal text-muted-foreground">({items.length})</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="text-center text-muted-foreground py-8">Loading…</p>
          ) : items.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No patterns added yet.</p>
          ) : (
            <Table>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono">{item.pattern}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => removeItem.mutate(item.id)}
                        disabled={removeItem.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                        Remove
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
