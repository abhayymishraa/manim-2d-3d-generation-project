"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Clock, ArrowRight, Trash2 } from "lucide-react"
import { formatDistanceToNow } from "date-fns"

interface JobHistoryItem {
  id: string
  prompt: string
  quality: string
  timestamp: string
}

export default function HistoryPage() {
  const [jobHistory, setJobHistory] = useState<JobHistoryItem[]>([])

  useEffect(() => {
    const history = JSON.parse(localStorage.getItem("manimJobHistory") || "[]")
    setJobHistory(history)
  }, [])

  const handleClearHistory = () => {
    if (confirm("Are you sure you want to clear your entire history?")) {
      localStorage.setItem("manimJobHistory", "[]")
      setJobHistory([])
    }
  }

  const handleRemoveJob = (id: string) => {
    const updatedHistory = jobHistory.filter((job) => job.id !== id)
    localStorage.setItem("manimJobHistory", JSON.stringify(updatedHistory))
    setJobHistory(updatedHistory)
  }

  if (jobHistory.length === 0) {
    return (
      <div className="max-w-3xl mx-auto py-12 text-center">
        <h1 className="text-3xl font-bold mb-4">Generation History</h1>
        <p className="text-muted-foreground mb-8">You haven't generated any visualizations yet.</p>
        <Button asChild>
          <Link href="/">Create Your First Visualization</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Generation History</h1>
        <Button variant="destructive" onClick={handleClearHistory}>
          Clear History
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {jobHistory.map((job) => (
          <Card key={job.id} className="overflow-hidden transition-all hover:shadow-md">
            <CardHeader>
              <CardTitle className="line-clamp-1">{job.prompt}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-muted-foreground">
                <Clock className="h-4 w-4 mr-2" />
                <span>{formatDistanceToNow(new Date(job.timestamp), { addSuffix: true })}</span>
              </div>
              <div className="mt-2 text-sm">
                Quality:{" "}
                <span className="font-medium">
                  {job.quality === "l" ? "Low" : job.quality === "m" ? "Medium" : "High"}
                </span>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="ghost" size="sm" onClick={() => handleRemoveJob(job.id)}>
                <Trash2 className="h-4 w-4 mr-2" />
                Remove
              </Button>
              <Button asChild>
                <Link href={`/job/${job.id}`}>
                  View Details
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
