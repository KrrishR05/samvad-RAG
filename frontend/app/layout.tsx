import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/layout/ThemeProvider";

export const metadata: Metadata = {
  title: "SAMVAD — Evidence-Grounded Multilingual RAG Workbench",
  description:
    "Multilingual retrieval-augmented knowledge workspace with source provenance, hybrid RRF search, and pipeline telemetry.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-theme="dark"
      suppressHydrationWarning
    >
      <body className="min-h-screen antialiased selection:bg-[var(--accent-soft)] selection:text-[var(--text-primary)]">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
