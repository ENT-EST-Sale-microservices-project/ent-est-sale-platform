import { useState, useEffect, useCallback, useRef } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useAuth } from '@/context/auth-context'
import { MessageSquare, Loader2, Plus, Send, Users, Wifi, WifiOff } from 'lucide-react'

type Thread = {
  thread_id: string
  title: string
  body: string
  author_id: string
  author_name: string
  module_code: string
  created_at: string
  reply_count: number
}

type Message = {
  message_id: string
  thread_id: string
  author_id: string
  author_name: string
  body: string
  created_at: string
}

type ThreadDetail = Thread & { messages: Message[] }

type WsMessage = {
  type: 'message' | 'system'
  username?: string
  text: string
  room?: string
}

const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
const WS_BASE = `${protocol}://${window.location.hostname}:8016`

export function ForumPage() {
  const { apiFetch, session } = useAuth()
  const token = session?.accessToken

  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)

  // New thread form
  const [dialogOpen, setDialogOpen] = useState(false)
  const [threadTitle, setThreadTitle] = useState('')
  const [threadBody, setThreadBody] = useState('')
  const [threadModule, setThreadModule] = useState('')
  const [threadLoading, setThreadLoading] = useState(false)
  const [threadError, setThreadError] = useState('')

  // Reply form
  const [replyText, setReplyText] = useState('')
  const [replyLoading, setReplyLoading] = useState(false)

  // WebSocket live chat
  const [wsRoom, setWsRoom] = useState('')
  const [wsInput, setWsInput] = useState('')
  const [wsMessages, setWsMessages] = useState<WsMessage[]>([])
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const chatEndRef = useRef<HTMLDivElement | null>(null)

  const loadThreads = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Thread[]>('/api/forum/threads')
      setThreads(data)
    } catch (err) {
      console.error('Failed to load threads', err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch])

  useEffect(() => {
    loadThreads()
  }, [loadThreads])

  async function loadMessages(threadId: string) {
    setMessagesLoading(true)
    try {
      const data = await apiFetch<ThreadDetail>(`/api/forum/threads/${threadId}`)
      setMessages(data.messages ?? [])
    } catch (err) {
      console.error('Failed to load messages', err)
    } finally {
      setMessagesLoading(false)
    }
  }

  function selectThread(thread: Thread) {
    setSelectedThread(thread)
    setMessages([])
    loadMessages(thread.thread_id)
    setReplyText('')
  }

  async function createThread(e: React.FormEvent) {
    e.preventDefault()
    setThreadLoading(true)
    setThreadError('')
    try {
      const t = await apiFetch<Thread>('/api/forum/threads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: threadTitle, body: threadBody, module_code: threadModule || 'general' }),
      })
      setThreads(prev => [t, ...prev])
      setDialogOpen(false)
      setThreadTitle('')
      setThreadBody('')
      setThreadModule('')
    } catch (err) {
      setThreadError(err instanceof Error ? err.message : 'Failed to create thread')
    } finally {
      setThreadLoading(false)
    }
  }

  async function postReply(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedThread || !replyText.trim()) return
    setReplyLoading(true)
    try {
      const msg = await apiFetch<Message>(`/api/forum/threads/${selectedThread.thread_id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: replyText }),
      })
      setMessages(prev => [...prev, msg])
      setThreads(prev => prev.map(t =>
        t.thread_id === selectedThread.thread_id
          ? { ...t, reply_count: (t.reply_count || 0) + 1 }
          : t
      ))
      setReplyText('')
    } catch (err) {
      console.error('Reply failed', err)
    } finally {
      setReplyLoading(false)
    }
  }

  function connectWs() {
    if (!wsRoom.trim() || !token) return
    if (wsRef.current) {
      wsRef.current.close()
    }
    setWsMessages([])
    const ws = new WebSocket(`${WS_BASE}/chat/ws?token=${token}&room=${encodeURIComponent(wsRoom)}`)
    wsRef.current = ws
    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onerror = () => setWsConnected(false)
    ws.onmessage = (e) => {
      try {
        const data: WsMessage = JSON.parse(e.data)
        setWsMessages(prev => [...prev, data])
        setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
      } catch {
        // ignore malformed
      }
    }
  }

  function sendWsMessage(e: React.FormEvent) {
    e.preventDefault()
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !wsInput.trim()) return
    wsRef.current.send(JSON.stringify({ text: wsInput }))
    setWsInput('')
  }

  useEffect(() => {
    return () => { wsRef.current?.close() }
  }, [])

  function formatDate(str: string) {
    try {
      return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(str))
    } catch { return str }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Forum</h2>
          <p className="text-muted-foreground">Discuss topics, ask questions, and share knowledge.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) { setThreadTitle(''); setThreadBody(''); setThreadModule(''); setThreadError('') } }}>
          <DialogTrigger render={<Button className="gap-2 shadow-md"><Plus className="size-4" />New Thread</Button>} />
          <DialogContent className="sm:max-w-[480px]">
            <form onSubmit={createThread}>
              <DialogHeader>
                <DialogTitle>Start a New Thread</DialogTitle>
                <DialogDescription>Post a question or topic to the forum.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label>Title</Label>
                  <Input required value={threadTitle} onChange={e => setThreadTitle(e.target.value)} placeholder="e.g. Docker networking question" />
                </div>
                <div className="space-y-2">
                  <Label>Body</Label>
                  <Textarea required value={threadBody} onChange={e => setThreadBody(e.target.value)} placeholder="Describe your question or topic..." className="resize-none h-28" />
                </div>
                <div className="space-y-2">
                  <Label>Module Code (optional)</Label>
                  <Input value={threadModule} onChange={e => setThreadModule(e.target.value)} placeholder="DEV101 or leave blank for general" />
                </div>
                {threadError && <p className="text-sm text-destructive">{threadError}</p>}
              </div>
              <DialogFooter>
                <Button type="submit" disabled={threadLoading} className="w-full sm:w-auto">
                  {threadLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <MessageSquare className="size-4 mr-2" />}
                  Post Thread
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Thread List */}
        <Card className="lg:col-span-1 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <MessageSquare className="size-4" /> Threads
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="size-6 animate-spin text-primary" />
              </div>
            ) : threads.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-center px-4">
                <MessageSquare className="size-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No threads yet. Start the conversation!</p>
              </div>
            ) : (
              <div className="divide-y divide-border/50 max-h-[500px] overflow-y-auto">
                {threads.map(thread => (
                  <button
                    key={thread.thread_id}
                    onClick={() => selectThread(thread)}
                    className={`w-full text-left p-4 transition-colors hover:bg-muted/50 ${selectedThread?.thread_id === thread.thread_id ? 'bg-primary/10 border-l-2 border-primary' : ''}`}
                  >
                    <p className="text-sm font-semibold line-clamp-1">{thread.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{thread.body}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0">{thread.module_code}</Badge>
                      <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                        <Users className="size-3" />{thread.reply_count ?? 0} replies
                      </span>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1">{formatDate(thread.created_at)}</p>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Thread Detail + Reply */}
        <Card className="lg:col-span-2 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm flex flex-col">
          <CardHeader className="pb-3 border-b border-border/50">
            {selectedThread ? (
              <>
                <CardTitle className="text-base">{selectedThread.title}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{selectedThread.body}</p>
                <div className="flex gap-2 mt-1">
                  <Badge variant="outline" className="text-[10px]">{selectedThread.module_code}</Badge>
                  <span className="text-[10px] text-muted-foreground">by {selectedThread.author_name} · {formatDate(selectedThread.created_at)}</span>
                </div>
              </>
            ) : (
              <CardTitle className="text-base text-muted-foreground">Select a thread to read</CardTitle>
            )}
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            {selectedThread ? (
              <>
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[320px]">
                  {messagesLoading ? (
                    <div className="flex justify-center py-8"><Loader2 className="size-6 animate-spin text-primary" /></div>
                  ) : messages.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">No replies yet. Be the first!</p>
                  ) : (
                    messages.map(msg => (
                      <div key={msg.message_id} className="flex gap-3">
                        <div className="shrink-0 size-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                          {msg.author_name.slice(0, 2).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline gap-2">
                            <span className="text-sm font-semibold">{msg.author_name}</span>
                            <span className="text-[10px] text-muted-foreground">{formatDate(msg.created_at)}</span>
                          </div>
                          <p className="text-sm text-muted-foreground mt-0.5 leading-relaxed">{msg.body}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                {/* Reply Form */}
                <form onSubmit={postReply} className="flex gap-2 p-4 border-t border-border/50">
                  <Input
                    value={replyText}
                    onChange={e => setReplyText(e.target.value)}
                    placeholder="Write a reply..."
                    className="flex-1"
                  />
                  <Button type="submit" disabled={replyLoading || !replyText.trim()} size="icon">
                    {replyLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  </Button>
                </form>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-center px-6">
                <MessageSquare className="size-12 text-muted-foreground mb-3" />
                <p className="text-muted-foreground text-sm">Pick a thread from the left to start reading.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Live Chat Widget */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
        <CardHeader className="pb-3 border-b border-border/50">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              {wsConnected ? <Wifi className="size-4 text-green-500" /> : <WifiOff className="size-4 text-muted-foreground" />}
              Live Module Chat
            </CardTitle>
            <Badge variant={wsConnected ? 'default' : 'secondary'} className="text-[10px]">
              {wsConnected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-3">
          {!wsConnected && (
            <div className="flex gap-2">
              <Input
                value={wsRoom}
                onChange={e => setWsRoom(e.target.value)}
                placeholder="Enter module code to join room (e.g. DEV101)"
                className="flex-1"
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); connectWs() } }}
              />
              <Button onClick={connectWs} disabled={!wsRoom.trim()} variant="outline">Join</Button>
            </div>
          )}
          {wsConnected && (
            <p className="text-xs text-muted-foreground">Room: <span className="font-mono font-medium">{wsRoom}</span></p>
          )}

          <div className="min-h-[120px] max-h-[200px] overflow-y-auto rounded-md border border-border/30 bg-muted/20 p-3 space-y-2">
            {wsMessages.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                {wsConnected ? 'Waiting for messages...' : 'Join a room to start chatting live.'}
              </p>
            ) : (
              wsMessages.map((m, i) => (
                <div key={i} className={`text-xs ${m.type === 'system' ? 'text-muted-foreground italic' : ''}`}>
                  {m.type === 'message' && m.username && (
                    <span className="font-semibold mr-1">{m.username}:</span>
                  )}
                  {m.text}
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {wsConnected && (
            <form onSubmit={sendWsMessage} className="flex gap-2">
              <Input
                value={wsInput}
                onChange={e => setWsInput(e.target.value)}
                placeholder="Type a message..."
                className="flex-1"
              />
              <Button type="submit" disabled={!wsInput.trim()} size="icon">
                <Send className="size-4" />
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
