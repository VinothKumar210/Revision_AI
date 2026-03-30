"use client";

import { useState, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import Navbar from "@/components/Navbar";
import styles from "./settings.module.css";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function SettingsPage() {
  const { user } = useUser();
  const [apiKey, setApiKey] = useState("");
  const [savedKey, setSavedKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      if (data.hasApiKey) {
        setSavedKey("••••••••" + (data.keyHint || ""));
      }
    } catch {
      // Settings not loaded — OK
    }
  }

  async function handleSaveKey(e) {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setLoading(true);
    setMessage({ text: "", type: "" });

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ groq_api_key: apiKey.trim() }),
      });

      if (!res.ok) throw new Error("Failed to save API key");

      setSavedKey("••••••••" + apiKey.slice(-4));
      setApiKey("");
      setMessage({ text: "API key saved successfully!", type: "success" });
    } catch {
      setMessage({ text: "Failed to save API key.", type: "error" });
    } finally {
      setLoading(false);
    }
  }

  async function handleRemoveKey() {
    setLoading(true);
    try {
      await fetch("/api/settings", {
        method: "DELETE",
      });
      setSavedKey("");
      setMessage({ text: "API key removed.", type: "success" });
    } catch {
      setMessage({ text: "Failed to remove API key.", type: "error" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <Navbar />
      <div className={styles.container}>
        <h1 className={styles.title}>⚙️ Settings</h1>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Profile</h2>
          <div className={styles.card}>
            <div className={styles.profileRow}>
              <span className={styles.label}>Email</span>
              <span className={styles.value}>
                {user?.emailAddresses?.[0]?.emailAddress || "—"}
              </span>
            </div>
            <div className={styles.profileRow}>
              <span className={styles.label}>Name</span>
              <span className={styles.value}>{user?.fullName || "—"}</span>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Groq API Key</h2>
          <p className={styles.sectionDesc}>
            Use your own Groq API key for unlimited usage. Get one free at{" "}
            <a
              href="https://console.groq.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              console.groq.com
            </a>
          </p>

          <div className={styles.card}>
            {savedKey && (
              <div className={styles.savedKey}>
                <span className={styles.keyDisplay}>{savedKey}</span>
                <button
                  className={styles.removeBtn}
                  onClick={handleRemoveKey}
                  disabled={loading}
                >
                  Remove
                </button>
              </div>
            )}

            <form onSubmit={handleSaveKey} className={styles.keyForm}>
              <input
                type="password"
                placeholder="gsk_xxxxxxxxxxxxxxxx"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className={styles.input}
              />
              <button
                type="submit"
                className={styles.saveBtn}
                disabled={loading || !apiKey.trim()}
              >
                {loading ? "Saving..." : "Save Key"}
              </button>
            </form>

            {message.text && (
              <p
                className={`${styles.message} ${
                  message.type === "error" ? styles.errorMsg : styles.successMsg
                }`}
              >
                {message.text}
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
