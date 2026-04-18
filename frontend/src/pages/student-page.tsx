import { useState, useEffect, useCallback } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/context/auth-context'
import { BookOpen, Download, FileText, Loader2, Search, Library } from 'lucide-react'

type Course = {
  course_id: string
  title: string
  description: string
  module_code: string
  visibility: string
  assets_count: number
}

type CourseDetails = Course & {
  assets: {
    asset_id: string
    file_name: string
    content_type: string
    size_bytes: number
  }[]
}

export function StudentPage() {
  const { apiFetch } = useAuth()
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null)
  const [courseDetails, setCourseDetails] = useState<CourseDetails | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  
  const [downloadingAssetId, setDownloadingAssetId] = useState<string | null>(null)

  const loadCourses = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Course[]>('/api/access/courses')
      setCourses(data)
    } catch (err) {
      console.error('Load courses failed:', err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch])

  useEffect(() => {
    loadCourses()
  }, [loadCourses])

  const loadCourseDetails = async (courseId: string) => {
    setSelectedCourseId(courseId)
    setDetailsLoading(true)
    try {
      const data = await apiFetch<CourseDetails>(`/api/access/courses/${courseId}`)
      setCourseDetails(data)
    } catch (err) {
      console.error('Load course details failed:', err)
    } finally {
      setDetailsLoading(false)
    }
  }

  async function createDownloadLink(assetId: string) {
    if (!selectedCourseId) return
    
    setDownloadingAssetId(assetId)
    try {
      const data = await apiFetch<{ download_url: string }>(
        `/api/access/courses/${selectedCourseId}/download-links`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ asset_id: assetId }),
        },
      )
      
      // Auto trigger download
      const a = document.createElement('a')
      a.href = data.download_url
      a.target = '_blank'
      a.rel = 'noopener noreferrer'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      
    } catch (err) {
      console.error('Generate link failed:', err)
      alert('Failed to generate download link.')
    } finally {
      setDownloadingAssetId(null)
    }
  }

  const filteredCourses = courses.filter(c => 
    c.title.toLowerCase().includes(search.toLowerCase()) || 
    c.module_code.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Course Catalog</h2>
          <p className="text-muted-foreground">Browse available courses and download learning materials.</p>
        </div>
        
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search courses..."
            className="pl-9 bg-background/50 shadow-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <Loader2 className="size-8 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">Loading catalog...</p>
        </div>
      ) : courses.length === 0 ? (
        <Card className="border-dashed border-border/60 bg-transparent shadow-none">
          <CardContent className="flex flex-col items-center justify-center h-64 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-4">
              <Library className="size-6" />
            </div>
            <h3 className="text-lg font-semibold">No courses available</h3>
            <p className="text-sm text-muted-foreground max-w-sm mt-1">
              There are currently no courses published for your role. Check back later.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3 items-start">
          {/* Course List */}
          <div className="lg:col-span-2 space-y-4">
            {filteredCourses.map((course) => (
              <Card 
                key={course.course_id} 
                className={`cursor-pointer transition-all hover:shadow-md hover:border-primary/50 group ${selectedCourseId === course.course_id ? 'border-primary ring-1 ring-primary shadow-md' : 'border-border/50 bg-card/80 backdrop-blur-sm shadow-sm'}`}
                onClick={() => loadCourseDetails(course.course_id)}
              >
                <CardContent className="p-5 flex items-start gap-4">
                  <div className={`flex size-10 shrink-0 items-center justify-center rounded-lg ${selectedCourseId === course.course_id ? 'bg-primary text-primary-foreground' : 'bg-primary/10 text-primary group-hover:bg-primary/20'} transition-colors`}>
                    <BookOpen className="size-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start gap-2 mb-1">
                      <h3 className="font-semibold text-foreground truncate" title={course.title}>
                        {course.title}
                      </h3>
                      <Badge variant="outline" className="shrink-0 text-[10px] uppercase tracking-wider font-semibold">
                        {course.module_code}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                      {course.description || 'No description provided for this course.'}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground font-medium">
                      <span className="flex items-center gap-1.5">
                        <FileText className="size-3.5" />
                        {course.assets_count} Asset{course.assets_count !== 1 ? 's' : ''}
                      </span>
                      <span className="capitalize px-1.5 py-0.5 rounded bg-muted/50">
                        {course.visibility.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {filteredCourses.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                No courses match your search "{search}".
              </div>
            )}
          </div>
          
          {/* Course Details Panel */}
          <div className="lg:sticky lg:top-24">
            {selectedCourseId ? (
              <Card className="border-primary/20 bg-card shadow-lg overflow-hidden">
                {detailsLoading ? (
                  <div className="flex flex-col items-center justify-center h-48">
                    <Loader2 className="size-6 animate-spin text-primary mb-2" />
                    <p className="text-sm text-muted-foreground">Loading details...</p>
                  </div>
                ) : courseDetails ? (
                  <>
                    <CardHeader className="bg-muted/30 pb-4 border-b border-border/50">
                      <div className="flex justify-between items-center mb-2">
                        <Badge variant="default" className="text-[10px] uppercase">
                          {courseDetails.module_code}
                        </Badge>
                      </div>
                      <CardTitle className="text-xl leading-tight">
                        {courseDetails.title}
                      </CardTitle>
                      <CardDescription className="mt-2 text-sm leading-relaxed">
                        {courseDetails.description || 'No description provided.'}
                      </CardDescription>
                    </CardHeader>
                    
                    <CardContent className="p-0">
                      <div className="px-6 py-3 bg-muted/20 border-b border-border/50 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Course Materials ({courseDetails.assets.length})
                      </div>
                      
                      <div className="divide-y divide-border/50 max-h-[400px] overflow-y-auto">
                        {courseDetails.assets.length > 0 ? (
                          courseDetails.assets.map(asset => (
                            <div key={asset.asset_id} className="p-4 hover:bg-muted/30 transition-colors flex items-center justify-between gap-4">
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-foreground truncate" title={asset.file_name}>
                                  {asset.file_name}
                                </p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {(asset.size_bytes / 1024 / 1024).toFixed(2)} MB • {asset.content_type.split('/')[1] || 'File'}
                                </p>
                              </div>
                              <Button 
                                variant="secondary" 
                                size="sm" 
                                className="shrink-0 rounded-full size-8 p-0"
                                onClick={() => createDownloadLink(asset.asset_id)}
                                disabled={downloadingAssetId === asset.asset_id}
                                title="Download Asset"
                              >
                                {downloadingAssetId === asset.asset_id ? (
                                  <Loader2 className="size-4 animate-spin" />
                                ) : (
                                  <Download className="size-4" />
                                )}
                              </Button>
                            </div>
                          ))
                        ) : (
                          <div className="p-8 text-center text-sm text-muted-foreground italic">
                            No materials have been uploaded for this course yet.
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </>
                ) : (
                   <div className="flex flex-col items-center justify-center h-48 text-center text-muted-foreground">
                    <p>Failed to load course details.</p>
                  </div>
                )}
              </Card>
            ) : (
              <Card className="border-dashed border-border/60 bg-transparent shadow-none hidden lg:block">
                <CardContent className="flex flex-col items-center justify-center h-[300px] text-center text-muted-foreground">
                  <Library className="size-10 opacity-20 mb-4" />
                  <p>Select a course from the catalog<br/>to view its materials.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
