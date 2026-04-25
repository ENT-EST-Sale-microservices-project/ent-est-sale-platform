import { useState, useEffect, useCallback } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuth } from '@/context/auth-context'
import { CalendarDays, ChevronLeft, ChevronRight, Clock, Loader2, Plus, Trash2 } from 'lucide-react'

type CalendarEvent = {
  event_id: string
  title: string
  description: string
  event_type: string
  start_time: string
  end_time: string
  module_code: string
  target_group: string
  created_by: string
  created_at: string
}

const EVENT_TYPE_CONFIG: Record<string, { label: string; dot: string; badge: string }> = {
  course: { label: 'Course', dot: 'bg-blue-500', badge: 'bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/30' },
  exam: { label: 'Exam', dot: 'bg-red-500', badge: 'bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/30' },
  deadline: { label: 'Deadline', dot: 'bg-orange-500', badge: 'bg-orange-500/15 text-orange-700 dark:text-orange-300 border-orange-500/30' },
  other: { label: 'Other', dot: 'bg-gray-400', badge: 'bg-gray-500/15 text-gray-700 dark:text-gray-300 border-gray-500/30' },
}

function formatYearMonth(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function formatDisplayMonth(d: Date): string {
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(d)
}

function getDaysInMonth(year: number, month: number): Date[] {
  const days: Date[] = []
  const date = new Date(year, month, 1)
  while (date.getMonth() === month) {
    days.push(new Date(date))
    date.setDate(date.getDate() + 1)
  }
  return days
}

export function CalendarPage() {
  const { apiFetch, hasAnyRole } = useAuth()
  const canWrite = hasAnyRole(['teacher', 'admin'])

  const [currentDate, setCurrentDate] = useState(new Date())
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  // Form state
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [eventType, setEventType] = useState('course')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [moduleCode, setModuleCode] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [formError, setFormError] = useState('')

  const loadEvents = useCallback(async () => {
    setLoading(true)
    try {
      const month = formatYearMonth(currentDate)
      const data = await apiFetch<CalendarEvent[]>(`/api/calendar/events?month=${month}`)
      setEvents(data)
    } catch (err) {
      console.error('Failed to load calendar events', err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch, currentDate])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  async function createEvent(e: React.FormEvent) {
    e.preventDefault()
    setCreateLoading(true)
    setFormError('')
    try {
      const ev = await apiFetch<CalendarEvent>('/api/calendar/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description,
          event_type: eventType,
          start_time: new Date(startTime).toISOString(),
          end_time: new Date(endTime).toISOString(),
          module_code: moduleCode || 'all',
          target_group: moduleCode || 'all',
        }),
      })
      setEvents(prev => [...prev, ev])
      setDialogOpen(false)
      resetForm()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create event')
    } finally {
      setCreateLoading(false)
    }
  }

  async function deleteEvent(event: CalendarEvent) {
    setDeleteLoading(true)
    setDeleteError('')
    try {
      await apiFetch(`/api/calendar/events/${event.event_id}`, { method: 'DELETE' })
      setEvents(prev => prev.filter(ev => ev.event_id !== event.event_id))
      setSelectedEvent(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete event')
    } finally {
      setDeleteLoading(false)
    }
  }

  function resetForm() {
    setTitle(''); setDescription(''); setEventType('course')
    setStartTime(''); setEndTime(''); setModuleCode(''); setFormError('')
  }

  function prevMonth() { setCurrentDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1)) }
  function nextMonth() { setCurrentDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1)) }

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const days = getDaysInMonth(year, month)
  const firstDayOfWeek = new Date(year, month, 1).getDay()
  const paddingDays = Array(firstDayOfWeek).fill(null)
  const today = new Date()

  function eventsForDay(day: Date): CalendarEvent[] {
    return events.filter(ev => {
      const d = new Date(ev.start_time)
      return d.getFullYear() === day.getFullYear() &&
        d.getMonth() === day.getMonth() &&
        d.getDate() === day.getDate()
    })
  }

  // Summary counts by type
  const typeCounts = events.reduce<Record<string, number>>((acc, ev) => {
    acc[ev.event_type] = (acc[ev.event_type] || 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Academic Calendar</h2>
          <p className="text-muted-foreground">Schedule and track courses, exams, and deadlines.</p>
        </div>
        {canWrite && (
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm() }}>
            <DialogTrigger render={
              <Button className="gap-2 shadow-md">
                <Plus className="size-4" /> Add Event
              </Button>
            } />
            <DialogContent className="sm:max-w-[500px]">
              <form onSubmit={createEvent}>
                <DialogHeader>
                  <DialogTitle>New Calendar Event</DialogTitle>
                  <DialogDescription>Schedule an event for the academic calendar.</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input required value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Final Exam — DEV101" />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Details about this event..." className="resize-none h-20" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Event Type</Label>
                      <Select value={eventType} onValueChange={(v) => { if (v) setEventType(v) }}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="course">Course</SelectItem>
                          <SelectItem value="exam">Exam</SelectItem>
                          <SelectItem value="deadline">Deadline</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Module Code</Label>
                      <Input value={moduleCode} onChange={e => setModuleCode(e.target.value)} placeholder="DEV101 or leave blank" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Start</Label>
                      <Input required type="datetime-local" value={startTime} onChange={e => setStartTime(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label>End</Label>
                      <Input required type="datetime-local" value={endTime} onChange={e => setEndTime(e.target.value)} />
                    </div>
                  </div>
                  {formError && <p className="text-sm text-destructive">{formError}</p>}
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={createLoading} className="w-full sm:w-auto">
                    {createLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <CalendarDays className="size-4 mr-2" />}
                    Save Event
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Legend / Summary */}
      {events.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(EVENT_TYPE_CONFIG).map(([type, cfg]) => {
            const count = typeCounts[type] || 0
            if (!count) return null
            return (
              <div key={type} className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium border ${cfg.badge}`}>
                <span className={`size-2 rounded-full ${cfg.dot}`} />
                {cfg.label}: {count}
              </div>
            )
          })}
        </div>
      )}

      {/* Calendar Grid */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
        <CardHeader className="pb-2 border-b border-border/40">
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="icon" onClick={prevMonth} className="size-8">
              <ChevronLeft className="size-4" />
            </Button>
            <CardTitle className="text-base font-semibold">{formatDisplayMonth(currentDate)}</CardTitle>
            <Button variant="ghost" size="icon" onClick={nextMonth} className="size-8">
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {/* Day headers */}
          <div className="grid grid-cols-7 border-b border-border/30">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
              <div key={d} className="text-center text-xs font-semibold text-muted-foreground py-2.5 bg-muted/20">{d}</div>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="size-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="grid grid-cols-7 divide-x divide-y divide-border/20">
              {paddingDays.map((_, i) => (
                <div key={`pad-${i}`} className="min-h-[90px] bg-muted/10" />
              ))}
              {days.map(day => {
                const isToday = day.toDateString() === today.toDateString()
                const dayEvents = eventsForDay(day)
                return (
                  <div
                    key={day.toISOString()}
                    className={`min-h-[90px] p-1.5 transition-colors hover:bg-muted/20 ${isToday ? 'bg-primary/5' : 'bg-card'}`}
                  >
                    <p className={`text-xs font-semibold mb-1 w-6 h-6 flex items-center justify-center rounded-full mx-auto ${isToday ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground'}`}>
                      {day.getDate()}
                    </p>
                    <div className="space-y-0.5">
                      {dayEvents.slice(0, 2).map(ev => {
                        const cfg = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.other
                        return (
                          <button
                            key={ev.event_id}
                            onClick={() => { setSelectedEvent(ev); setDeleteError('') }}
                            className={`w-full text-left text-[10px] leading-tight px-1.5 py-0.5 rounded-md border truncate font-medium ${cfg.badge} hover:opacity-80 transition-opacity`}
                          >
                            {ev.title}
                          </button>
                        )
                      })}
                      {dayEvents.length > 2 && (
                        <p className="text-[10px] text-muted-foreground pl-1">+{dayEvents.length - 2} more</p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Event Detail Dialog */}
      <Dialog open={!!selectedEvent} onOpenChange={(open) => { if (!open) { setSelectedEvent(null); setDeleteError('') } }}>
        <DialogContent className="sm:max-w-[440px]">
          {selectedEvent && (() => {
            const cfg = EVENT_TYPE_CONFIG[selectedEvent.event_type] || EVENT_TYPE_CONFIG.other
            return (
              <>
                <DialogHeader>
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 size-3 rounded-full shrink-0 ${cfg.dot}`} />
                    <div>
                      <DialogTitle>{selectedEvent.title}</DialogTitle>
                      <DialogDescription className="flex flex-wrap items-center gap-2 mt-1">
                        <Badge className={`text-[10px] border ${cfg.badge}`}>{cfg.label}</Badge>
                        {selectedEvent.module_code && selectedEvent.module_code !== 'all' && (
                          <Badge variant="outline" className="text-[10px]">{selectedEvent.module_code}</Badge>
                        )}
                      </DialogDescription>
                    </div>
                  </div>
                </DialogHeader>
                <div className="space-y-3 py-1">
                  {selectedEvent.description && (
                    <p className="text-sm text-muted-foreground leading-relaxed">{selectedEvent.description}</p>
                  )}
                  <div className="rounded-lg border border-border/50 bg-muted/30 p-3 space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="size-3.5 text-muted-foreground shrink-0" />
                      <div>
                        <span className="font-medium">Start: </span>
                        <span className="text-muted-foreground">{new Date(selectedEvent.start_time).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="size-3.5 text-muted-foreground shrink-0" />
                      <div>
                        <span className="font-medium">End: </span>
                        <span className="text-muted-foreground">{new Date(selectedEvent.end_time).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  {deleteError && <p className="text-sm text-destructive">{deleteError}</p>}
                </div>
                {canWrite && (
                  <DialogFooter>
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={deleteLoading}
                      onClick={() => deleteEvent(selectedEvent)}
                      className="gap-2"
                    >
                      {deleteLoading ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
                      Delete Event
                    </Button>
                  </DialogFooter>
                )}
              </>
            )
          })()}
        </DialogContent>
      </Dialog>
    </div>
  )
}
