"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/ModeToggle";
import { Home, History, Code2, Github, GithubIcon } from "lucide-react";

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-2">
          <div className="flex items-center space-x-2">
            <Code2 className="h-6 w-6 text-primary" />
            <span className="font-bold text-xl">Manim Generator</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center space-x-6">
          <Link
            href="/"
            className={`text-sm font-medium transition-colors ${
              pathname === "/"
                ? "text-primary"
                : "text-muted-foreground hover:text-primary"
            }`}
          >
            Home
          </Link>
          <Link
            href="/history"
            className={`text-sm font-medium transition-colors ${
              pathname === "/history"
                ? "text-primary"
                : "text-muted-foreground hover:text-primary"
            }`}
          >
            History
          </Link>
        </nav>

        <div className="flex items-center space-x-4">
          <div className="md:hidden flex space-x-2">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/">
                <Home className="h-5 w-5" />
              </Link>
            </Button>
            <Button variant="ghost" size="icon" asChild>
              <Link href="/history">
                <History className="h-5 w-5" />
              </Link>
            </Button>
          </div>
          <Link
            href="https://github.com/abhayymishraa/manim-2d-3d-generation-project"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-4 text-sm font-medium text-muted-foreground hover:text-primary"
          >
            <span className="flex items-center space-x-1 gap-2">
              <GithubIcon className="h-5 w-5" />
              Star on GitHub
            </span>
          </Link>
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
