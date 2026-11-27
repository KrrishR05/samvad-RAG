import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { AuthProvider } from "@/context/AuthContext";
import { KnowledgeBaseProvider } from "@/context/KnowledgeBaseContext";

export const metadata: Metadata = {
  title: "SAMVAD | संवाद",
  description:
    "Multilingual retrieval-augmented knowledge workspace with source provenance, hybrid RRF search, and pipeline telemetry.",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/samvad-icon.png",
    apple: "/samvad-icon.png",
  },
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
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("samvad_theme_v1");if(t==="light"||t==="dark"){document.documentElement.setAttribute("data-theme",t);}}catch(e){}})();`,
          }}
        />
      </head>
      <body className="min-h-screen antialiased selection:bg-[var(--accent-soft)] selection:text-[var(--text-primary)]">
        <ThemeProvider>
          <AuthProvider>
            <KnowledgeBaseProvider>{children}</KnowledgeBaseProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
