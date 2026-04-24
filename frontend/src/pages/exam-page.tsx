import { useState, useEffect, useCallback, useRef } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuth } from '@/context/auth-context'
import { ClipboardList, FileUp, GraduationCap, Loader2, Plus, Star } from 'lucide-react'

type Assignment = {
  assignment_id: string
  title: string
  description: string
  due_date: string
  module_code: string
  created_by: string
  created_by_name: string
  max_grade: number
  status: string
  created_at: string
}

type Submission = {
  submission_id: string
  assignment_id: string
  student_id: string
  student_name: string
  submitted_at: string
  content_text: string
  has_file: boolean
  download_url: string | null
  grade: number | null
  feedback: string | null
  graded_at: string | null
}

export function ExamPage() {
  const { apiFetch, hasAnyRole, claims } = useAuth()
  const isTeacher = hasAnyRole(['teacher', 'admin'])
  const isStudent = hasAnyRole(['student'])
  const myUserId = claims?.sub

  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [subsLoading, setSubsLoading] = useState(false)

  // Publish assignment form (teacher)
  const [createOpen, setCreateOpen] = useState(false)
  const [aTitle, setATitle] = useState('')
  const [aDesc, setADesc] = useState('')
  const [aDue, setADue] = useState('')
  const [aModule, setAModule] = useState('')
  const [aMaxGrade, setAMaxGrade] = useState('20')
  const [aStatus, setAStatus] = useState('published')
  const [aCreateLoading, setACreateLoading] = useState(false)
  const [aCreateError, setACreateError] = useState('')

  // Student submission form
  const [submitOpen, setSubmitOpen] = useState(false)
  const [submitText, setSubmitText] = useState('')
  const [submitFile, setSubmitFile] = useState<File | null>(null)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const fileRef = useRef<HTMLInputElement | null>(null)

  // Grading form (teacher)
  const [gradeOpen, setGradeOpen] = useState(false)
  const [gradingSub, setGradingSub] = useState<Submission | null>(null)
  const [gradeValue, setGradeValue] = useState('')
  const [gradeFeedback, setGradeFeedback] = useState('')
  const [gradeLoading, setGradeLoading] = useState(false)
  const [gradeError, setGradeError] = useState('')

  const loadAssignments = useCallback(async () => {
    setLoading(true)
    try {
      const params = isStudent ? '?status=published' : ''
      const data = await apiFetch<Assignment[]>(`/api/assignments${params}`)
      setAssignments(data)
    } catch (err) {
      console.error('Failed to load assignments', err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch, isStudent])

  useEffect(() => {
    loadAssignments()
  }, [loadAssignments])

  async function loadSubmissions(assignmentId: string) {
    setSubsLoading(true)
    try {
      const data = await apiFetch<Submission[]>(`/api/assignments/${assignmentId}/submissions`)
      setSubmissions(data)
    } catch (err) {
      console.error('Failed to load submissions', err)
    } finally {
      setSubsLoading(false)
    }
  }

  function selectAssignment(a: Assignment) {
    setSelectedAssignment(a)
    setSubmissions([])
    loadSubmissions(a.assignment_id)
  }

  async function createAssignment(e: React.FormEvent) {
    e.preventDefault()
    setACreateLoading(true)
    setACreateError('')
    try {
      const a = await apiFetch<Assignment>('/api/assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: aTitle,
          description: aDesc,
          due_date: new Date(aDue).toISOString(),
          module_code: aModule,
          max_grade: parseFloat(aMaxGrade),
          status: aStatus,
        }),
      })
      setAssignments(prev => [a, ...prev])
      setCreateOpen(false)
      resetCreateForm()
    } catch (err) {
      setACreateError(err instanceof Error ? err.message : 'Failed to publish assignment')
    } finally {
      setACreateLoading(false)
    }
  }

  function resetCreateForm() {
    setATitle(''); setADesc(''); setADue(''); setAModule(''); setAMaxGrade('20'); setAStatus('published'); setACreateError('')
  }

  async function submitAssignment(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedAssignment) return
    setSubmitLoading(true)
    setSubmitError('')
    try {
      const form = new FormData()
      form.append('content_text', submitText)
      if (submitFile) form.append('file', submitFile)

      const sub = await apiFetch<Submission>(`/api/assignments/${selectedAssignment.assignment_id}/submissions`, {
        method: 'POST',
        body: form,
      })
      setSubmissions(prev => [...prev, sub])
      setSubmitOpen(false)
      setSubmitText('')
      setSubmitFile(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setSubmitLoading(false)
    }
  }

  async function gradeSubmission(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedAssignment || !gradingSub) return
    setGradeLoading(true)
    setGradeError('')
    try {
      const updated = await apiFetch<Submission>(
        `/api/assignments/${selectedAssignment.assignment_id}/submissions/${gradingSub.submission_id}/grade`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ grade: parseFloat(gradeValue), feedback: gradeFeedback }),
        }
      )
      setSubmissions(prev => prev.map(s => s.submission_id === gradingSub.submission_id ? updated : s))
      setGradeOpen(false)
      setGradingSub(null)
      setGradeValue('')
      setGradeFeedback('')
    } catch (err) {
      setGradeError(err instanceof Error ? err.message : 'Grading failed')
    } finally {
      setGradeLoading(false)
    }
  }

  function formatDate(str: string) {
    try { return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(str)) } catch { return str }
  }

  function statusBadge(status: string) {
    if (status === 'published') return <Badge className="text-[10px] bg-green-500/20 text-green-700 dark:text-green-300 border-green-500/30">published</Badge>
    return <Badge variant="secondary" className="text-[10px]">{status}</Badge>
  }

  const mySubmission = isStudent ? submissions.find(s => s.student_id === myUserId) : null

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Assignments & Exams</h2>
          <p className="text-muted-foreground">
            {isTeacher ? 'Publish assignments and grade student submissions.' : 'View assignments and submit your work.'}
          </p>
        </div>
        {isTeacher && (
          <Dialog open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) resetCreateForm() }}>
            <DialogTrigger render={<Button className="gap-2 shadow-md"><Plus className="size-4" />Publish Assignment</Button>} />
            <DialogContent className="sm:max-w-[520px]">
              <form onSubmit={createAssignment}>
                <DialogHeader>
                  <DialogTitle>Publish New Assignment</DialogTitle>
                  <DialogDescription>Students will see this once published.</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input required value={aTitle} onChange={e => setATitle(e.target.value)} placeholder="e.g. Docker Lab Report" />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea required value={aDesc} onChange={e => setADesc(e.target.value)} placeholder="Instructions, requirements, resources..." className="resize-none h-24" />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Module Code</Label>
                      <Input required value={aModule} onChange={e => setAModule(e.target.value)} placeholder="DEV101" />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Grade</Label>
                      <Input required type="number" min="1" max="100" value={aMaxGrade} onChange={e => setAMaxGrade(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select value={aStatus} onValueChange={(v) => { if (v) setAStatus(v) }}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="published">Published</SelectItem>
                          <SelectItem value="draft">Draft</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Due Date</Label>
                    <Input required type="datetime-local" value={aDue} onChange={e => setADue(e.target.value)} />
                  </div>
                  {aCreateError && <p className="text-sm text-destructive">{aCreateError}</p>}
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={aCreateLoading} className="w-full sm:w-auto">
                    {aCreateLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <ClipboardList className="size-4 mr-2" />}
                    Publish
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Assignment List */}
        <Card className="lg:col-span-1 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ClipboardList className="size-4" /> Assignments
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-32"><Loader2 className="size-6 animate-spin text-primary" /></div>
            ) : assignments.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-center px-4">
                <ClipboardList className="size-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No assignments yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-border/50 max-h-[480px] overflow-y-auto">
                {assignments.map(a => (
                  <button
                    key={a.assignment_id}
                    onClick={() => selectAssignment(a)}
                    className={`w-full text-left p-4 transition-colors hover:bg-muted/50 ${selectedAssignment?.assignment_id === a.assignment_id ? 'bg-primary/10 border-l-2 border-primary' : ''}`}
                  >
                    <p className="text-sm font-semibold line-clamp-1">{a.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0">{a.module_code}</Badge>
                      {statusBadge(a.status)}
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1">Due: {formatDate(a.due_date)}</p>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detail Panel */}
        <Card className="lg:col-span-2 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm flex flex-col">
          {selectedAssignment ? (
            <>
              <CardHeader className="border-b border-border/50">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-lg">{selectedAssignment.title}</CardTitle>
                    <CardDescription className="mt-1">{selectedAssignment.description}</CardDescription>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-2xl font-bold text-primary">{selectedAssignment.max_grade}</p>
                    <p className="text-[10px] text-muted-foreground">max pts</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Badge variant="outline" className="text-[10px]">{selectedAssignment.module_code}</Badge>
                  {statusBadge(selectedAssignment.status)}
                  <span className="text-xs text-muted-foreground">Due: {formatDate(selectedAssignment.due_date)}</span>
                </div>

                {/* Student: submit button */}
                {isStudent && !mySubmission && (
                  <Dialog open={submitOpen} onOpenChange={(open) => { setSubmitOpen(open); if (!open) { setSubmitText(''); setSubmitFile(null); setSubmitError('') } }}>
                    <DialogTrigger render={<Button size="sm" className="mt-3 gap-2 w-fit"><FileUp className="size-4" />Submit Work</Button>} />
                    <DialogContent className="sm:max-w-[460px]">
                      <form onSubmit={submitAssignment}>
                        <DialogHeader>
                          <DialogTitle>Submit Assignment</DialogTitle>
                          <DialogDescription>{selectedAssignment.title}</DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="space-y-2">
                            <Label>Your Answer</Label>
                            <Textarea required value={submitText} onChange={e => setSubmitText(e.target.value)} placeholder="Write your answer here..." className="resize-none h-32" />
                          </div>
                          <div className="space-y-2">
                            <Label>Attach File (optional, max 50 MB)</Label>
                            <input
                              type="file"
                              ref={fileRef}
                              onChange={e => setSubmitFile(e.target.files?.[0] ?? null)}
                              className="text-sm"
                            />
                          </div>
                          {submitError && <p className="text-sm text-destructive">{submitError}</p>}
                        </div>
                        <DialogFooter>
                          <Button type="submit" disabled={submitLoading} className="w-full sm:w-auto">
                            {submitLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <FileUp className="size-4 mr-2" />}
                            Submit
                          </Button>
                        </DialogFooter>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}

                {/* Student: already submitted */}
                {isStudent && mySubmission && (
                  <div className="mt-3 p-3 rounded-lg bg-muted/40 border border-border/50 text-sm">
                    <p className="font-medium text-green-600 dark:text-green-400">Submitted</p>
                    <p className="text-muted-foreground mt-1 line-clamp-2">{mySubmission.content_text}</p>
                    {mySubmission.grade !== null ? (
                      <div className="mt-2 flex items-center gap-2">
                        <Star className="size-4 text-yellow-500" />
                        <span className="font-bold">{mySubmission.grade} / {selectedAssignment.max_grade}</span>
                        {mySubmission.feedback && <span className="text-muted-foreground">— {mySubmission.feedback}</span>}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground mt-1">Awaiting grade...</p>
                    )}
                  </div>
                )}
              </CardHeader>

              {/* Teacher: submissions list */}
              {isTeacher && (
                <CardContent className="flex-1 pt-4">
                  <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <GraduationCap className="size-4" /> Submissions ({submissions.length})
                  </h3>
                  {subsLoading ? (
                    <div className="flex justify-center py-8"><Loader2 className="size-6 animate-spin text-primary" /></div>
                  ) : submissions.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">No submissions yet.</p>
                  ) : (
                    <div className="space-y-3 max-h-[300px] overflow-y-auto">
                      {submissions.map(sub => (
                        <div key={sub.submission_id} className="rounded-lg border border-border/50 p-3 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-sm font-semibold">{sub.student_name}</p>
                              <p className="text-xs text-muted-foreground">{formatDate(sub.submitted_at)}</p>
                            </div>
                            <div className="text-right">
                              {sub.grade !== null ? (
                                <div className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                                  <Star className="size-3.5" />
                                  <span className="font-bold text-sm">{sub.grade}/{selectedAssignment.max_grade}</span>
                                </div>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-7 text-xs"
                                  onClick={() => { setGradingSub(sub); setGradeOpen(true) }}
                                >
                                  Grade
                                </Button>
                              )}
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 bg-muted/30 p-2 rounded border border-border/30">
                            {sub.content_text}
                          </p>
                          {sub.has_file && sub.download_url && (
                            <a href={sub.download_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary underline">
                              Download file
                            </a>
                          )}
                          {sub.feedback && (
                            <p className="text-xs text-muted-foreground italic">Feedback: {sub.feedback}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              )}
            </>
          ) : (
            <CardContent className="flex-1 flex flex-col items-center justify-center h-64 text-center">
              <ClipboardList className="size-12 text-muted-foreground mb-3" />
              <p className="text-muted-foreground text-sm">Select an assignment to view details.</p>
            </CardContent>
          )}
        </Card>
      </div>

      {/* Grade Dialog */}
      <Dialog open={gradeOpen} onOpenChange={(open) => { setGradeOpen(open); if (!open) { setGradingSub(null); setGradeValue(''); setGradeFeedback(''); setGradeError('') } }}>
        <DialogContent className="sm:max-w-[380px]">
          <form onSubmit={gradeSubmission}>
            <DialogHeader>
              <DialogTitle>Grade Submission</DialogTitle>
              <DialogDescription>{gradingSub?.student_name} · max {selectedAssignment?.max_grade} pts</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Grade</Label>
                <Input required type="number" min="0" max={selectedAssignment?.max_grade} step="0.5" value={gradeValue} onChange={e => setGradeValue(e.target.value)} placeholder={`0 – ${selectedAssignment?.max_grade}`} />
              </div>
              <div className="space-y-2">
                <Label>Feedback</Label>
                <Textarea value={gradeFeedback} onChange={e => setGradeFeedback(e.target.value)} placeholder="Comments for the student..." className="resize-none h-20" />
              </div>
              {gradeError && <p className="text-sm text-destructive">{gradeError}</p>}
            </div>
            <DialogFooter>
              <Button type="submit" disabled={gradeLoading} className="w-full sm:w-auto">
                {gradeLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <Star className="size-4 mr-2" />}
                Submit Grade
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
