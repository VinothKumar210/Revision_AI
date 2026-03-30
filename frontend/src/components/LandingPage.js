import Link from "next/link";
import styles from "./LandingPage.module.css";

export default function LandingPage() {
  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>🧠</span>
            <span className={styles.logoText}>Revision AI</span>
          </div>
          <Link href="/sign-in" className={styles.signInBtn}>
            Sign In
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroGlow}></div>
        <div className={styles.heroContent}>
          <div className={styles.badge}>✨ AI-Powered Study Revision</div>
          <h1 className={styles.heroTitle}>
            Never Forget
            <br />
            What You <span className={styles.gradient}>Study</span>
          </h1>
          <p className={styles.heroDesc}>
            Tell the AI your topics, set a schedule, and receive progressive
            revision reminders on WhatsApp. Ask doubts right in the chat.
          </p>
          <div className={styles.heroCta}>
            <Link href="/sign-up" className={styles.primaryBtn}>
              Get Started Free →
            </Link>
            <Link href="/sign-in" className={styles.secondaryBtn}>
              I have an account
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>💬</div>
            <h3 className={styles.featureTitle}>Smart Topic Setup</h3>
            <p className={styles.featureDesc}>
              Chat with AI to identify and organize your revision topics. It
              asks the right questions to understand exactly what you need.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>📲</div>
            <h3 className={styles.featureTitle}>WhatsApp Reminders</h3>
            <p className={styles.featureDesc}>
              Receive scheduled revision content via WhatsApp. Each reminder
              progressively deepens your understanding.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>📈</div>
            <h3 className={styles.featureTitle}>Progressive Learning</h3>
            <p className={styles.featureDesc}>
              4 depth levels — from basic concepts to advanced edge cases. Each
              revision builds on the previous one.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>❓</div>
            <h3 className={styles.featureTitle}>Doubt Clarification</h3>
            <p className={styles.featureDesc}>
              Have a doubt? Reply directly on WhatsApp and the AI will clarify
              with context from your revision material.
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className={styles.howItWorks}>
        <h2 className={styles.sectionTitle}>How It Works</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNum}>1</div>
            <h4>Tell the AI your topics</h4>
            <p>
              &quot;I want to revise Graphs in DSA&quot; — the AI will clarify
              and organize
            </p>
          </div>
          <div className={styles.stepDivider}></div>
          <div className={styles.step}>
            <div className={styles.stepNum}>2</div>
            <h4>Set your schedule</h4>
            <p>Choose how often and when you want to be reminded</p>
          </div>
          <div className={styles.stepDivider}></div>
          <div className={styles.step}>
            <div className={styles.stepNum}>3</div>
            <h4>Learn on WhatsApp</h4>
            <p>Get progressively deeper content + ask doubts in the chat</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>Built with Llama 3.3 · Groq · Twilio · Next.js</p>
      </footer>
    </div>
  );
}
