"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, RefreshCw, Trash2, Download, ArrowLeft } from "lucide-react"
import { getJobStatus, getJobCode, deleteJob } from "@/lib/api"
import CodeViewer from "@/components/CodeViewer"

interface JobStatusProps {
  jobId: string
}

interface JobData {
  job_id: string
  status: "pending" | "completed" | "failed"
  message: string
  output_path?: string
}

export default function JobStatus({ jobId }: JobStatusProps) {
  const router = useRouter()
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [code, setCode] = useState<string>("")
  const [isPolling, setIsPolling] = useState(true)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let intervalId: NodeJS.Timeout

    const fetchJobStatus = async () => {
      try {
        const data = await getJobStatus(jobId)
        setJobData(data)

        if (data.status === "completed" || data.status === "failed") {
          setIsPolling(false)

          if (data.status === "completed") {
            try {
              const codeData = await getJobCode(jobId)
              setCode(codeData?.code)
            } catch (err) {
              console.error("Error fetching code:", err)
            }
          }
        }

        setIsLoading(false)
      } catch (err) {
        setError("Failed to fetch job status")
        setIsPolling(false)
        setIsLoading(false)
      }
    }


    fetchJobStatus()

    // Set up polling if needed
    if (isPolling) {
      intervalId = setInterval(fetchJobStatus, 6000)
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [jobId, isPolling])

  const handleRefresh = async () => {
    setIsLoading(true)
    try {
      const data = await getJobStatus(jobId)
      setJobData(data)

      if (data.status === "completed") {
        try {
          const codeData = await getJobCode(jobId)
          setCode(codeData)
        } catch (err) {
          console.error("Error fetching code:", err)
        }
      }
    } catch (err) {
      setError("Failed to refresh job status")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (confirm("Are you sure you want to delete this job?")) {
      try {
        await deleteJob(jobId)

        // Remove from localStorage
        const jobHistory = JSON.parse(localStorage.getItem("manimJobHistory") || "[]")
        const updatedHistory = jobHistory.filter((job: any) => job.id !== jobId)
        localStorage.setItem("manimJobHistory", JSON.stringify(updatedHistory))

        router.push("/history")
      } catch (err) {
        setError("Failed to delete job")
      }
    }
  }

  if (isLoading && !jobData) {
    return (
      <div className="flex justify-center items-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!jobData) {
    return (
      <Alert>
        <AlertDescription>Job not found</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold mb-2">Job: {jobId.substring(0, 8)}...</h2>
          <p className="text-muted-foreground">
        Status:{" "}
        <span
          className={
            jobData.status === "completed"
          ? "text-green-500"
          : jobData.status === "failed"
            ? "text-red-500"
            : "text-yellow-500"
          }
        >
          {jobData.status.charAt(0).toUpperCase() + jobData.status.slice(1)}
        </span>
          </p>
          {jobData.message && <p className="text-sm text-muted-foreground mt-1">{jobData.message}</p>}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => router.push("/")}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        New Generation
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
        <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
        Refresh
          </Button>
          <Button variant="destructive" size="sm" onClick={handleDelete}>
        <Trash2 className="h-4 w-4 mr-2" />
        Delete
          </Button>
        </div>
      </div>

      {isPolling && (
        <div className="flex items-center justify-center py-8">
          <div className="flex flex-col items-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
            <p className="text-muted-foreground">Processing your visualization...</p>
          </div>
        </div>
      )}

      {jobData.status === "completed" && jobData.output_path && (
        <Tabs defaultValue="video">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="video">Video</TabsTrigger>
            <TabsTrigger value="code">Code</TabsTrigger>
          </TabsList>

          <TabsContent value="video" className="space-y-4">
            <div className="relative aspect-video bg-black/10 rounded-lg overflow-hidden">
              <video
                src={jobData.output_path}
                controls
                className="w-full h-full"
              />
            </div>

            <div className="flex justify-end">
              <Button asChild>
                <a
                  href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/renders/${jobData.output_path}`}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Video
                </a>
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="code">
            <CodeViewer code={code} />
          </TabsContent>
        </Tabs>
      )}

      {jobData.status === "failed" && (
        <Alert variant="destructive">
          <AlertDescription>The job failed to complete. Please try again with a different prompt.</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
