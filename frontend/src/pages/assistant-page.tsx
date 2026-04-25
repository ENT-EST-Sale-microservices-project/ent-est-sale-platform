import { useState, useRef, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/context/auth-context'
import { Bot, Loader2, RefreshCw, Send, Sparkles, User } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: string[]
  model?: string
}

interface ChatResponse {
  answer: string
  sources: string[]
  model: string
  tokens_used?: number
}

export function AssistantPage() {
  const { roles, apiFetch } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modelStatus, setModelStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const primaryRole = roles[0] || 'student'

  const checkModelStatus = useCallback(async () => {
    try {
      const health = await apiFetch<{ ollama?: { ollama?: string } }>('/api/ai/health')
      setModelStatus(health?.ollama?.ollama === 'ok' ? 'ok' : 'error')
    } catch {
      setModelStatus('error')
    }
  }, [apiFetch])

  useEffect(() => {
    checkModelStatus()
    // Welcome message
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I'm your AI assistant for ENT EST Salé. How can I help you today?\n\nI can help you with:\n• Questions about courses and the platform\n• Summarizing course content\n• Generating FAQs\n• Academic guidance\n\nWhat would you like to know?`,
        timestamp: new Date(),
        model: 'llama3',
      },
    ])
  }, [checkModelStatus])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await apiFetch<ChatResponse>('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current-user',
          role: primaryRole,
          question: userMessage.content,
          context_refs: [],
        }),
      })

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        model: response.model,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get response')
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `I apologize, but I couldn't process your request right now. Please try again later.\n\nError: ${err instanceof Error ? err.message : 'Unknown error'}`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  function clearChat() {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I'm your AI assistant for ENT EST Salé. How can I help you today?\n\nI can help you with:\n• Questions about courses and the platform\n• Summarizing course content\n• Generating FAQs\n• Academic guidance\n\nWhat would you like to know?`,
        timestamp: new Date(),
        model: 'llama3',
      },
    ])
    setError(null)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="flex-shrink-0 border-b bg-muted/30 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/20">
                <Sparkles className="size-5" />
              </div>
              <div>
                <CardTitle className="text-lg">AI Assistant</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <span>Powered by Llama 3</span>
                  {modelStatus === 'loading' && (
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Loader2 className="size-3 animate-spin" /> Checking...
                    </span>
                  )}
                  {modelStatus === 'ok' && (
                    <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                      <span className="size-2 rounded-full bg-green-500" /> Online
                    </span>
                  )}
                  {modelStatus === 'error' && (
                    <span className="flex items-center gap-1 text-xs text-destructive">
                      <span className="size-2 rounded-full bg-destructive" /> Offline
                    </span>
                  )}
                </CardDescription>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={clearChat} className="gap-2">
              <RefreshCw className="size-4" />
              Clear
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div
                className={`flex size-9 shrink-0 items-center justify-center rounded-xl ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-md'
                    : 'bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/20'
                }`}
              >
                {msg.role === 'user' ? (
                  <User className="size-4" />
                ) : (
                  <Bot className="size-4" />
                )}
              </div>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                <div className="mt-2 flex items-center gap-2 text-xs opacity-60">
                  <span>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {msg.model && (
                    <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-violet-600 dark:text-violet-400">
                      {msg.model}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/20">
                <Bot className="size-4" />
              </div>
              <div className="max-w-[80%] rounded-2xl bg-muted px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="flex gap-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-destructive/10">
                <span className="text-destructive">!</span>
              </div>
              <div className="max-w-[80%] rounded-2xl bg-destructive/10 px-4 py-3">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        <div className="flex-shrink-0 border-t bg-muted/30 p-4">
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about ENT EST Salé..."
              disabled={loading}
              className="flex-1"
            />
            <Button onClick={sendMessage} disabled={loading || !input.trim()} size="icon">
              {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            </Button>
          </div>
          <p className="mt-2 text-xs text-center text-muted-foreground">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </Card>
    </div>
  )
}