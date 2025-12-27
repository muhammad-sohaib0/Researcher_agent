"use client";

import { useRouter } from "next/navigation";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();

  const features = [
    {
      icon: "🔬",
      title: "Research Paper Search",
      description: "Search Semantic Scholar & Google Scholar. Download, analyze, and rank papers by relevance automatically.",
    },
    {
      icon: "📄",
      title: "Document Reading",
      description: "Read PDF, Word, PowerPoint, and images with AI-powered OCR. Extract text with page numbers for citations.",
    },
    {
      icon: "🎙️",
      title: "Voice Input/Output",
      description: "Convert speech to text and text to speech. Support for multiple languages including English and Urdu.",
    },
    {
      icon: "📥",
      title: "Export Results",
      description: "Download your research as formatted Word documents, PDFs, or audio files for easy sharing.",
    },
    {
      icon: "🤖",
      title: "AI-Powered Analysis",
      description: "Powered by Gemini AI. Get intelligent, evidence-based answers with proper citations.",
    },
    {
      icon: "📚",
      title: "Evidence-Based Answers",
      description: "Every answer comes with exact page numbers and source citations. No guessing, only facts.",
    },
  ];

  const audiences = [
    { icon: "🎓", title: "Students", description: "Ace your research papers and assignments" },
    { icon: "🔬", title: "Researchers", description: "Accelerate literature review and analysis" },
    { icon: "💼", title: "Professionals", description: "Make data-driven decisions with evidence" },
  ];

  return (
    <main className={styles.main}>
      {/* Background Effects */}
      <div className={styles.bgGradient}></div>
      <div className={styles.bgOrbs}>
        <div className={styles.orb1}></div>
        <div className={styles.orb2}></div>
        <div className={styles.orb3}></div>
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>🧠</span>
          <span className={styles.logoText}>Research Agent</span>
        </div>
        <button className="btn btn-primary" onClick={() => router.push("/auth")}>
          Get Started
        </button>
      </nav>

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            Your AI-Powered
            <span className="gradient-text"> Research Assistant</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Search papers, analyze documents, and get evidence-based answers with proper citations.
            Powered by advanced AI for accurate, reliable research assistance.
          </p>
          <div className={styles.heroCta}>
            <button className="btn btn-primary" onClick={() => router.push("/auth")}>
              🚀 Get Started Free
            </button>
            <button className="btn btn-secondary" onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>
              Learn More
            </button>
          </div>
        </div>
        <div className={styles.heroVisual}>
          <div className={styles.chatPreview}>
            <div className={styles.chatBubbleUser}>
              Find research papers about machine learning in healthcare
            </div>
            <div className={styles.chatBubbleAgent}>
              <div className={styles.thinkingBadge}>🔍 Searching...</div>
              I found 10 relevant papers from Semantic Scholar and Google Scholar.
              Here are the top 5 most relevant:
              <br /><br />
              1. "Deep Learning for Medical Imaging" - [Source: paper1.pdf, Page 3]
              <br />
              2. "AI in Clinical Decision Making" - [Source: paper2.pdf, Page 7]
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className={styles.features}>
        <h2 className={styles.sectionTitle}>
          Powerful <span className="gradient-text">Features</span>
        </h2>
        <p className={styles.sectionSubtitle}>
          Everything you need for efficient, evidence-based research
        </p>
        <div className={styles.featuresGrid}>
          {features.map((feature, index) => (
            <div key={index} className={`card ${styles.featureCard}`} style={{ animationDelay: `${index * 0.1}s` }}>
              <div className={styles.featureIcon}>{feature.icon}</div>
              <h3 className={styles.featureTitle}>{feature.title}</h3>
              <p className={styles.featureDesc}>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Who It's For Section */}
      <section className={styles.audience}>
        <h2 className={styles.sectionTitle}>
          Perfect For <span className="gradient-text">Everyone</span>
        </h2>
        <div className={styles.audienceGrid}>
          {audiences.map((item, index) => (
            <div key={index} className={styles.audienceCard}>
              <div className={styles.audienceIcon}>{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className={styles.cta}>
        <div className={styles.ctaContent}>
          <h2>Ready to Transform Your Research?</h2>
          <p>Start using Research Agent today and experience the power of AI-assisted research.</p>
          <button className="btn btn-primary" onClick={() => router.push("/auth")}>
            🚀 Get Started Now
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerLogo}>
            <span>🧠</span> Research Agent
          </div>
          <p>© 2024 Research Agent. Powered by AI.</p>
        </div>
      </footer>
    </main>
  );
}
