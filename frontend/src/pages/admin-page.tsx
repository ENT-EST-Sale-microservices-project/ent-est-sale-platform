import { useState, useEffect, useCallback } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { useAuth } from '@/context/auth-context'
import { roleBadgeVariant } from '@/lib/auth'
import { MoreHorizontal, Plus, Search, ShieldAlert, UserPlus, RefreshCw, Loader2 } from 'lucide-react'

type UserProfile = {
  user_id: string
  username: string
  email?: string
  first_name?: string
  last_name?: string
  role?: string
  status: string
}

export function AdminPage() {
  const { apiFetch } = useAuth()
  const [users, setUsers] = useState<UserProfile[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)

  // Create user form state
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('student')
  const [createLoading, setCreateLoading] = useState(false)
  const [error, setError] = useState('')

  const listUsers = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<UserProfile[]>('/api/admin/users?limit=100')
      setUsers(data)
    } catch (err) {
      console.error('Failed to load users:', err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch])

  useEffect(() => {
    listUsers()
  }, [listUsers])

  async function createUser(e: React.FormEvent) {
    e.preventDefault()
    setCreateLoading(true)
    setError('')
    try {
      await apiFetch<UserProfile>('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          email,
          first_name: firstName,
          last_name: lastName,
          password,
          roles: [role],
          enabled: true,
        }),
      })
      setDialogOpen(false)
      // Reset form
      setFirstName('')
      setLastName('')
      setUsername('')
      setEmail('')
      setPassword('')
      setRole('student')
      await listUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create user failed')
    } finally {
      setCreateLoading(false)
    }
  }

  async function patchRoleAction(userId: string, newRole: string) {
    try {
      await apiFetch<UserProfile>(`/api/admin/users/${userId}/roles`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roles: [newRole] }),
      })
      await listUsers()
    } catch (err) {
      console.error('Role update failed:', err)
    }
  }

  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    (u.email && u.email.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
          <p className="text-muted-foreground">Manage platform users, roles, and access controls.</p>
        </div>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button className="gap-2 shadow-md"><UserPlus className="size-4" />Add User</Button>} />
          <DialogContent className="sm:max-w-[425px]">
            <form onSubmit={createUser}>
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>
                  Provision a new user account in Keycloak.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name</Label>
                    <Input required value={firstName} onChange={(e) => setFirstName(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name</Label>
                    <Input required value={lastName} onChange={(e) => setLastName(e.target.value)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Username</Label>
                  <Input required value={username} onChange={(e) => setUsername(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select value={role} onValueChange={(value) => setRole(value as string)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="student">Student</SelectItem>
                      <SelectItem value="teacher">Teacher</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {error && <p className="text-sm text-destructive">{error}</p>}
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createLoading} className="w-full sm:w-auto">
                  {createLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <Plus className="size-4 mr-2" />}
                  Create Account
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
        <CardHeader className="pb-3 border-b border-border/50">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
            <div className="relative max-w-sm w-full">
              <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search users..."
                className="pl-9 bg-background/50"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{users.length} total users</span>
              <Button variant="ghost" size="icon" onClick={listUsers} disabled={loading} className="size-8">
                <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow>
                <TableHead className="w-[250px] pl-6">User</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right pr-6">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    <Loader2 className="size-6 animate-spin mx-auto mb-2 text-primary" />
                    Loading users...
                  </TableCell>
                </TableRow>
              ) : filteredUsers.length > 0 ? (
                filteredUsers.map((user) => (
                  <TableRow key={user.user_id} className="group hover:bg-muted/20 transition-colors">
                    <TableCell className="pl-6">
                      <div className="font-medium text-foreground">{user.first_name} {user.last_name}</div>
                      <div className="text-xs text-muted-foreground">{user.username}</div>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">{user.email || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={roleBadgeVariant(user.role)} className="capitalize tracking-wide text-[10px]">
                        {user.role || 'none'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <span className={`size-2 rounded-full ${user.status === 'ACTIVE' || user.status === 'enabled' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                        <span className="text-xs text-muted-foreground capitalize">{user.status}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <DropdownMenu>
                        <DropdownMenuTrigger render={<Button variant="ghost" className="size-8 p-0 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"><span className="sr-only">Open menu</span><MoreHorizontal className="size-4" /></Button>} />
                        <DropdownMenuContent align="end" className="w-40">
                          <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Change Role
                          </div>
                          <DropdownMenuItem onClick={() => patchRoleAction(user.user_id, 'student')} disabled={user.role === 'student'}>
                            Student
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => patchRoleAction(user.user_id, 'teacher')} disabled={user.role === 'teacher'}>
                            Teacher
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => patchRoleAction(user.user_id, 'admin')} disabled={user.role === 'admin'}>
                            <ShieldAlert className="size-3 mr-2 text-destructive" />
                            Admin
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                    No users found matching your search.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
