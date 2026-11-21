import type { Metadata } from "next"
import { Geist_Mono, Lexend } from "next/font/google"

import { Providers } from "@/app/providers"
import "./globals.css"

const sans = Lexend({ variable: "--font-sans", subsets: ["latin"] })
const mono = Geist_Mono({ variable: "--font-mono", subsets: ["latin"] })

export const metadata: Metadata = {
  title: "altri",
  description: "Scorecard, Issues, To-Dos, Rocks and the Level 10 Meeting",
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
