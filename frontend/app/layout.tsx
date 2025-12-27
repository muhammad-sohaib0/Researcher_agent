import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Research Agent - AI-Powered Research Assistant",
  description: "Your intelligent research companion powered by AI. Search papers, analyze documents, and get evidence-based answers with citations.",
  keywords: "AI, Research, Assistant, PDF, Document Analysis, Academic Research",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
