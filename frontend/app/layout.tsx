'use client';

import type { Metadata } from "next";
import "./globals.css";
import { useEffect, useState } from "react";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' || 'dark';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        <title>Research Agent - AI-Powered Research Assistant</title>
        <meta name="description" content="Your intelligent research companion powered by AI. Search papers, analyze documents, and get evidence-based answers with citations." />
      </head>
      <body>
        {/* Theme Toggle Button - Fixed Position */}
        <button
          onClick={toggleTheme}
          style={{
            position: 'fixed',
            top: '24px',
            right: '24px',
            zIndex: 1000,
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            border: '1px solid var(--border-medium)',
            background: 'var(--bg-card)',
            backdropFilter: 'blur(20px)',
            color: 'var(--text-primary)',
            fontSize: '20px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s ease',
            boxShadow: 'var(--shadow-md)',
          }}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        {children}
      </body>
    </html>
  );
}
