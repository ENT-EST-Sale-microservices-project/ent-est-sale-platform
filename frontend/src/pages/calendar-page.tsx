import { useState, useEffect, useCallback } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/context/auth-context'
import {
  CalendarDays, ChevronLeft, ChevronRight, Clock, Loader2, Plus,
  Trash2, BookOpen, AlertTriangle, CalendarCheck2, Layers,
  MapPin, User2, Tag,
} from 'lucide-react'

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

const EVENT_TYPE_CONFIG: Record<string, { label: string; dot: string; badge: string; icon: typeof BookOpen; gradient: string }> = {
  course:   { label: 'Course',   dot: 'bg-blue-500',    badge: 'bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/30',    icon: BookOpen,        gradient: 'from-blue-500/20 to-blue-600/5' },
  exam:     { label: 'Exam',     dot: 'bg-red-500',     badge: 'bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/30',        icon: AlertTriangle,   gradient: 'from-red-500/20 to-red-600/5' },
  deadline: { label: 'Deadline', dot: 'bg-orange-500',  badge: 'bg-orange-500/15 text-orange-700 dark:text-orange-300 border-orange-500/30', icon: CalendarCheck2, gradient: 'from-orange-500/20 to-orange-600/5' },
  other:    { label: 'Other',    dot: 'bg-slate-400',   badge: 'bg-slate-500/15 text-slate-700 dark:text-slate-300 border-slate-500/30', icon: Layers,          gradient: 'from-slate-500/20 to-slate-600/5' },
}

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December']

function formatYearMonth(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function getDaysInMonth(year: number, month: number): Date[] {
  const days: Date[] = []
  const d = new Date(year, month, 1)
  while (d.getMonth() === month) { days.push(new Date(d)); d.setDate(d.getDate() + 1) }
  return days
}

function formatTime(iso: string) {
  try {
    return new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).format(new Date(iso))
  } catch { return iso }
}

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(iso))
  } catch { return iso }
}

function duration(start: string, end: string) {
  try {
    const ms = new Date(end).getTime() - new Date(start).getTime()
    const h = Math.floor(ms / 3600000)
    const m = Math.floor((ms % 3600000) / 60000)
    if (h === 0) return `${m}m`
    if (m === 0) return `${h}h`
    return `${h}h ${m}m`
  } catch { return '' }
}

export function CalendarPage() {
  const { apiFetch, hasAnyRole } = useAuth()
  const canWrite = hasAnyRole(['teacher', 'admin'])

  const [view, setView] = useState<'month' | 'agenda'>('month')
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

  useEffect(() => { loadEvents() }, [loadEvents])

  async function createEvent(e: React.FormEvent) {
    e.preventDefault()
    setCreateLoading(true)
    setFormError('')
    try {
      const ev = await apiFetch<CalendarEvent>('/api/calendar/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title, description,
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
  function goToday() { setCurrentDate(new Date()) }

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const days = getDaysInMonth(year, month)
  const firstDayOfWeek = new Date(year, month, 1).getDay()
  const paddingDays = Array(firstDayOfWeek).fill(null)
  const today = new Date()

  function eventsForDay(day: Date) {
    return events.filter(ev => {
      const d = new Date(ev.start_time)
      return d.getFullYear() === day.getFullYear() && d.getMonth() === day.getMonth() && d.getDate() === day.getDate()
    }).sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  }

  const typeCounts = events.reduce<Record<string, number>>((acc, ev) => {
    acc[ev.event_type] = (acc[ev.event_type] || 0) + 1
    return acc
  }, {})

  // Agenda: group events by date, sorted
  const agendaEvents = [...events].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  const agendaByDate: Record<string, CalendarEvent[]> = {}
  for (const ev of agendaEvents) {
    const key = new Date(ev.start_time).toDateString()
    if (!agendaByDate[key]) agendaByDate[key] = []
    agendaByDate[key].push(ev)
  }

  const todayEvents = eventsForDay(today).filter(
    ev => new Date(ev.start_time).getMonth() === today.getMonth() && new Date(ev.start_time).getFullYear() === today.getFullYear()
  )

  return (
    <div className="space-y-5">
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

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">
        {/* Main calendar area */}
        <div className="xl:col-span-3 space-y-4">
          {/* Controls row */}
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" onClick={prevMonth} className="size-9">
                <ChevronLeft className="size-4" />
              </Button>
              <h3 className="text-lg font-semibold min-w-[180px] text-center">
                {MONTH_NAMES[month]} {year}
              </h3>
              <Button variant="outline" size="icon" onClick={nextMonth} className="size-9">
                <ChevronRight className="size-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={goToday} className="text-xs px-3">
                Today
              </Button>
            </div>

            <Tabs value={view} onValueChange={(v) => setView(v as 'month' | 'agenda')}>
              <TabsList className="h-9">
                <TabsTrigger value="month" className="text-xs px-3">Month</TabsTrigger>
                <TabsTrigger value="agenda" className="text-xs px-3">Agenda</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Legend */}
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

          {/* Month View */}
          {view === 'month' && (
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
              <div className="grid grid-cols-7 border-b border-border/30">
                {DAY_NAMES.map(d => (
                  <div key={d} className="text-center text-xs font-semibold text-muted-foreground py-3 bg-muted/20">{d}</div>
                ))}
              </div>

              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="size-8 animate-spin text-primary" />
                </div>
              ) : (
                <div className="grid grid-cols-7 divide-x divide-y divide-border/20">
                  {paddingDays.map((_, i) => (
                    <div key={`pad-${i}`} className="min-h-[100px] bg-muted/5" />
                  ))}
                  {days.map(day => {
                    const isToday = day.toDateString() === today.toDateString()
                    const dayEvents = eventsForDay(day)
                    const isCurrentMonth = day.getMonth() === month
                    return (
                      <div
                        key={day.toISOString()}
                        className={`min-h-[100px] p-1.5 transition-colors hover:bg-muted/20 cursor-pointer ${
                          isToday ? 'bg-primary/5 ring-1 ring-inset ring-primary/30' : 'bg-card'
                        } ${!isCurrentMonth ? 'opacity-40' : ''}`}
                      >
                        <div className={`text-xs font-bold mb-1 w-7 h-7 flex items-center justify-center rounded-full mx-auto ${
                          isToday ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-muted'
                        }`}>
                          {day.getDate()}
                        </div>
                        <div className="space-y-0.5">
                          {dayEvents.slice(0, 3).map(ev => {
                            const cfg = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.other
                            return (
                              <button
                                key={ev.event_id}
                                onClick={() => { setSelectedEvent(ev); setDeleteError('') }}
                                className={`w-full text-left text-[10px] leading-tight px-1.5 py-0.5 rounded border truncate font-semibold ${cfg.badge} hover:opacity-80 transition-opacity`}
                              >
                                <span className={`inline-block size-1.5 rounded-full mr-1 ${cfg.dot}`} />
                                {formatTime(ev.start_time)} {ev.title}
                              </button>
                            )
                          })}
                          {dayEvents.length > 3 && (
                            <button
                              onClick={() => setSelectedEvent(dayEvents[3])}
                              className="text-[10px] text-primary font-medium pl-1 hover:underline"
                            >
                              +{dayEvents.length - 3} more
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>
          )}

          {/* Agenda View */}
          {view === 'agenda' && (
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center h-40">
                  <Loader2 className="size-8 animate-spin text-primary" />
                </div>
              ) : Object.keys(agendaByDate).length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <CalendarDays className="size-10 mb-2 opacity-30" />
                  <p className="text-sm">No events this month</p>
                </div>
              ) : (
                <div className="divide-y divide-border/30">
                  {Object.entries(agendaByDate).map(([dateStr, dayEvs]) => (
                    <div key={dateStr}>
                      <div className="px-5 py-2.5 bg-muted/30 flex items-center gap-2">
                        <span className={`text-sm font-bold ${dateStr === today.toDateString() ? 'text-primary' : 'text-foreground'}`}>
                          {dateStr === today.toDateString() ? 'Today — ' : ''}{new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date(dateStr))}
                        </span>
                        <Badge variant="outline" className="text-[10px] px-1.5">{dayEvs.length}</Badge>
                      </div>
                      {dayEvs.map(ev => {
                        const cfg = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.other
                        const Icon = cfg.icon
                        return (
                          <button
                            key={ev.event_id}
                            onClick={() => { setSelectedEvent(ev); setDeleteError('') }}
                            className="w-full text-left flex items-start gap-4 px-5 py-3.5 hover:bg-muted/30 transition-colors"
                          >
                            <div className={`mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${cfg.gradient} border border-border/30`}>
                              <Icon className={`size-4 ${cfg.badge.split(' ')[1]}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-2">
                                <p className="font-semibold text-sm truncate">{ev.title}</p>
                                <Badge className={`shrink-0 text-[10px] border ${cfg.badge}`}>{cfg.label}</Badge>
                              </div>
                              <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                <span className="flex items-center gap-1">
                                  <Clock className="size-3" />
                                  {formatTime(ev.start_time)} – {formatTime(ev.end_time)}
                                  <span className="text-[10px] opacity-60">({duration(ev.start_time, ev.end_time)})</span>
                                </span>
                                {ev.module_code && ev.module_code !== 'all' && (
                                  <span className="flex items-center gap-1">
                                    <Tag className="size-3" />
                                    {ev.module_code}
                                  </span>
                                )}
                              </div>
                              {ev.description && (
                                <p className="text-xs text-muted-foreground mt-1 truncate">{ev.description}</p>
                              )}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Right sidebar: Today's events + upcoming */}
        <div className="space-y-4">
          {/* Today's events */}
          <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
            <CardHeader className="pb-3 pt-4 px-4">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <span className="size-2 rounded-full bg-primary animate-pulse" />
                Today
                <span className="text-xs font-normal text-muted-foreground ml-auto">
                  {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(today)}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2">
              {todayEvents.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-3">No events today</p>
              ) : todayEvents.map(ev => {
                const cfg = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.other
                return (
                  <button
                    key={ev.event_id}
                    onClick={() => { setSelectedEvent(ev); setDeleteError('') }}
                    className={`w-full text-left rounded-lg p-2.5 border transition-colors hover:opacity-90 bg-gradient-to-r ${cfg.gradient} border-border/30`}
                  >
                    <div className="flex items-start gap-2">
                      <span className={`mt-0.5 size-2 rounded-full shrink-0 ${cfg.dot}`} />
                      <div className="min-w-0">
                        <p className="text-xs font-semibold truncate">{ev.title}</p>
                        <p className="text-[11px] text-muted-foreground">{formatTime(ev.start_time)}</p>
                      </div>
                    </div>
                  </button>
                )
              })}
            </CardContent>
          </Card>

          {/* Upcoming 5 events */}
          <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
            <CardHeader className="pb-3 pt-4 px-4">
              <CardTitle className="text-sm font-semibold">Upcoming</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2.5">
              {agendaEvents.filter(ev => new Date(ev.start_time) >= today).slice(0, 6).length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-3">No upcoming events</p>
              ) : agendaEvents.filter(ev => new Date(ev.start_time) >= today).slice(0, 6).map(ev => {
                const cfg = EVENT_TYPE_CONFIG[ev.event_type] || EVENT_TYPE_CONFIG.other
                return (
                  <button
                    key={ev.event_id}
                    onClick={() => { setSelectedEvent(ev); setDeleteError('') }}
                    className="w-full text-left flex items-start gap-2.5 group"
                  >
                    <span className={`mt-1.5 size-2 rounded-full shrink-0 ${cfg.dot}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold truncate group-hover:text-primary transition-colors">{ev.title}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(ev.start_time))} · {formatTime(ev.start_time)}
                      </p>
                    </div>
                  </button>
                )
              })}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Event Detail Dialog */}
      <Dialog open={!!selectedEvent} onOpenChange={(open) => { if (!open) { setSelectedEvent(null); setDeleteError('') } }}>
        <DialogContent className="sm:max-w-[460px]">
          {selectedEvent && (() => {
            const cfg = EVENT_TYPE_CONFIG[selectedEvent.event_type] || EVENT_TYPE_CONFIG.other
            const Icon = cfg.icon
            return (
              <>
                <DialogHeader>
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 flex size-10 items-center justify-center rounded-xl bg-gradient-to-br ${cfg.gradient} border border-border/30 shrink-0`}>
                      <Icon className={`size-5 ${cfg.badge.split(' ')[1]}`} />
                    </div>
                    <div className="min-w-0">
                      <DialogTitle className="leading-snug">{selectedEvent.title}</DialogTitle>
                      <DialogDescription className="flex flex-wrap items-center gap-2 mt-1.5">
                        <Badge className={`text-[10px] border ${cfg.badge}`}>{cfg.label}</Badge>
                        {selectedEvent.module_code && selectedEvent.module_code !== 'all' && (
                          <Badge variant="outline" className="text-[10px]">
                            <Tag className="size-3 mr-1" />{selectedEvent.module_code}
                          </Badge>
                        )}
                      </DialogDescription>
                    </div>
                  </div>
                </DialogHeader>

                <div className="space-y-3 py-1">
                  {selectedEvent.description && (
                    <p className="text-sm text-muted-foreground leading-relaxed">{selectedEvent.description}</p>
                  )}
                  <div className="rounded-xl border border-border/50 bg-muted/30 p-4 space-y-2.5">
                    <div className="flex items-center gap-2.5 text-sm">
                      <CalendarDays className="size-4 text-muted-foreground shrink-0" />
                      <div>
                        <p className="font-medium text-xs text-muted-foreground uppercase tracking-wide mb-0.5">Date</p>
                        <p>{formatDate(selectedEvent.start_time)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2.5 text-sm">
                      <Clock className="size-4 text-muted-foreground shrink-0" />
                      <div>
                        <p className="font-medium text-xs text-muted-foreground uppercase tracking-wide mb-0.5">Time</p>
                        <p>{formatTime(selectedEvent.start_time)} – {formatTime(selectedEvent.end_time)}
                          <span className="ml-2 text-xs text-muted-foreground">({duration(selectedEvent.start_time, selectedEvent.end_time)})</span>
                        </p>
                      </div>
                    </div>
                    {selectedEvent.target_group && selectedEvent.target_group !== 'all' && (
                      <div className="flex items-center gap-2.5 text-sm">
                        <User2 className="size-4 text-muted-foreground shrink-0" />
                        <div>
                          <p className="font-medium text-xs text-muted-foreground uppercase tracking-wide mb-0.5">Target</p>
                          <p>{selectedEvent.target_group}</p>
                        </div>
                      </div>
                    )}
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
