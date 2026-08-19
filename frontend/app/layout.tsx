import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SAMVAD — Adaptive Voice-Enabled RAG",
  description:
    "Speak. Retrieve. Ground. A voice-first adaptive retrieval-augmented generation system with multilingual support, structured orchestration, and grounded responses.",
  keywords: [
    "SAMVAD",
    "RAG",
    "voice",
    "retrieval",
    "AI",
    "grounding",
    "multilingual",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
