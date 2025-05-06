import { Suspense } from "react"
import JobStatus from "@/components/JobStatus"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export default function JobPage({ params }: { params: { id: string } }) {
  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8">
      <Card>
        <CardHeader>
          <CardTitle>Job Status</CardTitle>
        </CardHeader>
        <CardContent>
          <Suspense fallback={<JobStatusSkeleton />}>
            <JobStatus jobId={params.id} />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  )
}

function JobStatusSkeleton() {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      <Skeleton className="h-[300px] w-full" />
    </div>
  )
}
