import GenerationForm from "@/components/GenerateForm"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  return (
    <div className="max-w-3xl mx-auto space-y-8 py-8">
      <div className="space-y-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Manim Visualization Generator</h1>
        <p className="text-xl text-muted-foreground">Create beautiful mathematical animations with natural language</p>
      </div>

      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle>Generate Animation</CardTitle>
          <CardDescription>Describe the mathematical visualization you want to create</CardDescription>
        </CardHeader>
        <CardContent>
          <GenerationForm />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>What is Manim?</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Manim is an animation engine for explanatory math videos. It's used to create precise animations
              programmatically.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>How it works</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li>Describe what you want to visualize</li>
              <li>Our AI generates Manim code</li>
              <li>The code is executed to create an animation</li>
              <li>View and download your visualization</li>
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
