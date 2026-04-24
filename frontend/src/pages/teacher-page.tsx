import { useState, useEffect, useCallback, useRef } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuth } from '@/context/auth-context'
import { BookOpen, CloudUpload, FileText, Loader2, Plus, Trash2, UploadCloud, RefreshCw } from 'lucide-react'

type Asset = {
  asset_id: string
  file_name: string
  content_type: string
  size_bytes: number
}

type Course = {
  course_id: string
  title: string
  description: string
  module_code: string
  visibility: string
  tags: string[]
  assets: Asset[]
  created_at: string
}

export function TeacherPage() {
  const { apiFetch } = useAuth()
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  
  // Create course form state
  const [title, setTitle] = useState('')
  const [moduleCode, setModuleCode] = useState('')
  const [description, setDescription] = useState('')
  const [visibility, setVisibility] = useState('public_class')
  const [tags, setTags] = useState('devops, backend')
  const [createLoading, setCreateLoading] = useState(false)
  const [error, setError] = useState('')

  // Asset upload state per course
  const [uploadingCourseId, setUploadingCourseId] = useState<string | null>(null)
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({})

  const loadCourses = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Course[]>('/api/content/courses')
      setCourses(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch])

  useEffect(() => {
    loadCourses()
  }, [loadCourses])

  async function createCourse(e: React.FormEvent) {
    e.preventDefault()
    setCreateLoading(true)
    setError('')
    try {
      const data = await apiFetch<{ course_id: string }>('/api/content/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description,
          module_code: moduleCode,
          tags: tags.split(',').map(t => t.trim()).filter(Boolean),
          visibility,
        }),
      })
      setDialogOpen(false)
      // Reset form
      setTitle('')
      setModuleCode('')
      setDescription('')
      
      // Manually add to local state since we don't have a GET endpoint
      setCourses(prev => [{
        course_id: data.course_id,
        title,
        description,
        module_code: moduleCode,
        visibility,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        assets: [],
        created_at: new Date().toISOString()
      }, ...prev])

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Course creation failed')
    } finally {
      setCreateLoading(false)
    }
  }

  async function uploadAsset(courseId: string, file: File) {
    setUploadingCourseId(courseId)
    try {
      const form = new FormData()
      form.append('file', file)
      
      const res = await apiFetch<{asset_id: string}>(`/api/content/courses/${courseId}/assets`, {
        method: 'POST',
        body: form,
      })
      
      // Update local state
      setCourses(prev => prev.map(c => {
        if (c.course_id === courseId) {
          return {
            ...c,
            assets: [...c.assets, {
              asset_id: res.asset_id,
              file_name: file.name,
              content_type: file.type,
              size_bytes: file.size
            }]
          }
        }
        return c
      }))
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploadingCourseId(null)
      if (fileInputRefs.current[courseId]) {
        fileInputRefs.current[courseId]!.value = ''
      }
    }
  }

  const [deletingCourseId, setDeletingCourseId] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState('')

  async function deleteCourse(courseId: string) {
    setDeletingCourseId(courseId)
    setDeleteError('')
    try {
      await apiFetch(`/api/content/courses/${courseId}`, { method: 'DELETE' })
      setCourses(prev => prev.filter(c => c.course_id !== courseId))
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete course')
      setTimeout(() => setDeleteError(''), 4000)
    } finally {
      setDeletingCourseId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Course Studio</h2>
          <p className="text-muted-foreground">Create courses and manage learning materials.</p>
          {deleteError && (
            <p className="text-sm text-destructive mt-1">{deleteError}</p>
          )}
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button className="gap-2 shadow-md"><Plus className="size-4" />New Course</Button>} />
          <DialogContent className="sm:max-w-[500px]">
            <form onSubmit={createCourse}>
              <DialogHeader>
                <DialogTitle>Create New Course</DialogTitle>
                <DialogDescription>
                  Define the metadata for your new course module.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2 col-span-2">
                    <Label>Course Title</Label>
                    <Input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Intro to DevOps" />
                  </div>
                  <div className="space-y-2">
                    <Label>Module Code</Label>
                    <Input required value={moduleCode} onChange={(e) => setModuleCode(e.target.value)} placeholder="DEV101" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea 
                    required 
                    value={description} 
                    onChange={(e) => setDescription(e.target.value)} 
                    placeholder="Brief overview of the course content..."
                    className="resize-none h-20"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Visibility</Label>
                    <Select value={visibility} onValueChange={(v) => setVisibility(v as string)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="public_class">Public Class</SelectItem>
                        <SelectItem value="private">Private</SelectItem>
                        <SelectItem value="archived">Archived</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Tags (comma separated)</Label>
                    <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="devops, cloud, srm" />
                  </div>
                </div>
                {error && <p className="text-sm text-destructive">{error}</p>}
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createLoading} className="w-full sm:w-auto">
                  {createLoading ? <Loader2 className="size-4 animate-spin mr-2" /> : <BookOpen className="size-4 mr-2" />}
                  Publish Course
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {courses.length === 0 ? (
        <Card className="border-dashed border-border/60 bg-transparent shadow-none">
          <CardContent className="flex flex-col items-center justify-center h-64 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-4">
              <CloudUpload className="size-6" />
            </div>
            <h3 className="text-lg font-semibold">No courses created yet</h3>
            <p className="text-sm text-muted-foreground max-w-sm mt-1 mb-4">
              Get started by creating your first course. You can then upload documents, videos, and other assets.
            </p>
            <Button onClick={() => setDialogOpen(true)} variant="outline">
              <Plus className="size-4 mr-2" /> Create First Course
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => (
            <Card key={course.course_id} className="flex flex-col border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden group">
              <CardHeader className="bg-muted/30 pb-4">
                <div className="flex justify-between items-start gap-2">
                  <div className="space-y-1 w-full overflow-hidden">
                    <div className="flex justify-between items-center w-full">
                      <span className="text-xs font-semibold tracking-wider text-primary uppercase">
                        {course.module_code}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-6 text-muted-foreground hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => deleteCourse(course.course_id)}
                        disabled={deletingCourseId === course.course_id}
                        title="Delete course"
                      >
                        {deletingCourseId === course.course_id
                          ? <Loader2 className="size-3.5 animate-spin" />
                          : <Trash2 className="size-3.5" />
                        }
                      </Button>
                    </div>
                    <CardTitle className="text-lg leading-tight truncate" title={course.title}>
                      {course.title}
                    </CardTitle>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  <Badge variant="outline" className="text-[10px] font-normal bg-background/50">
                    {course.visibility.replace('_', ' ')}
                  </Badge>
                  {course.tags.slice(0, 2).map(tag => (
                    <Badge key={tag} variant="secondary" className="text-[10px] font-normal">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardHeader>
              <CardContent className="flex-1 pt-4 space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {course.description}
                </p>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    <span>Assets ({course.assets.length})</span>
                  </div>
                  
                  {course.assets.length > 0 ? (
                    <div className="space-y-2 max-h-[120px] overflow-y-auto pr-1">
                      {course.assets.map(asset => (
                        <div key={asset.asset_id} className="flex items-center gap-2 text-sm p-2 rounded-md bg-muted/50 border border-border/50">
                          <FileText className="size-3.5 text-primary shrink-0" />
                          <span className="truncate flex-1" title={asset.file_name}>{asset.file_name}</span>
                          <span className="text-xs text-muted-foreground shrink-0">
                            {(asset.size_bytes / 1024).toFixed(0)} KB
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic bg-muted/30 p-2 rounded-md border border-border/30">
                      No assets uploaded yet.
                    </p>
                  )}
                </div>
              </CardContent>
              <CardFooter className="pt-0 border-t border-border/50 bg-muted/10 p-3">
                <div className="w-full relative">
                  <input
                    type="file"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10 disabled:cursor-not-allowed"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) uploadAsset(course.course_id, file)
                    }}
                    ref={el => { fileInputRefs.current[course.course_id] = el; }}
                    disabled={uploadingCourseId === course.course_id}
                  />
                  <Button 
                    variant="outline" 
                    className="w-full bg-background/50 hover:bg-muted"
                    disabled={uploadingCourseId === course.course_id}
                  >
                    {uploadingCourseId === course.course_id ? (
                      <Loader2 className="size-4 animate-spin mr-2" />
                    ) : (
                      <UploadCloud className="size-4 mr-2" />
                    )}
                    {uploadingCourseId === course.course_id ? 'Uploading...' : 'Upload Asset'}
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
