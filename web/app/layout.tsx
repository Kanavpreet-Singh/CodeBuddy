import type { Metadata } from "next";
import { IBM_Plex_Sans, JetBrains_Mono, Space_Grotesk } from "next/font/google";

import TopBar from "@/components/TopBar";
import "./globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  weight: ["500", "600", "700"],
});

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-plex-sans",
  weight: ["400", "500", "600"],
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "CodeBuddy — describe it, watch it get built",
  description: "One prompt becomes a running app, planned, architected, and coded by an agent you can watch.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable} h-full`}
    >
      <body className="relative min-h-full">
        <div aria-hidden className="bg-grid pointer-events-none fixed inset-0 -z-20" />
        <div aria-hidden className="bg-glow pointer-events-none fixed inset-x-0 top-0 -z-10 h-[440px]" />
        <TopBar />
        {children}
      </body>
    </html>
  );
}
