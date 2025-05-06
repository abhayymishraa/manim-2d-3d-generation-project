"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Sparkles } from "lucide-react"
import { generateManimVisualization } from "@/lib/api"

export default function GenerationForm() {
  const router = useRouter()
  const [prompt, setPrompt] = useState("")
  const [quality, setQuality] = useState("m")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!prompt.trim()) return

    setIsLoading(true)

    try {
      const response = await generateManimVisualization(prompt, quality)

      // Store job in localStorage
      const jobHistory = JSON.parse(localStorage.getItem("manimJobHistory") || "[]")
      const newJob = {
        id: response.job_id,
        prompt,
        quality,
        timestamp: new Date().toISOString(),
      }

      localStorage.setItem("manimJobHistory", JSON.stringify([newJob, ...jobHistory]))

      // Navigate to job status page
      router.push(`/job/${response.job_id}`)
    } catch (error) {
      console.error("Error generating visualization:", error)
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Textarea
          placeholder="Describe the visualization you want to create (use simple because it uses gemini model and it is not enough to generate good code without losing context). For example: 'Show a revolving ball animation', 'Explain Redis cache hit and miss', or 'Visualize how bits work in a binary system'"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="min-h-[120px] resize-none"
          required
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="w-full sm:w-1/3">
          <Select value={quality} onValueChange={setQuality}>
            <SelectTrigger>
              <SelectValue placeholder="Quality" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="l">Low</SelectItem>
              <SelectItem value="m">Medium</SelectItem>
              <SelectItem value="h">High</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button
          type="submit"
          className="w-full sm:w-2/3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
          disabled={isLoading || !prompt.trim()}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Visualization
            </>
          )}
        </Button>
      </div>
    </form>
  )
}
