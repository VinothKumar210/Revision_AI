"use client";

import { useState, useRef, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import Navbar from "@/components/Navbar";
import styles from "./chat.module.css";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const INITIAL_GREETING = {
  role: "ai",
  content:
    "Hey! 👋 I'm Revision AI. Tell me what topic you'd like to revise, and I'll help you set it up. You can also paste your study notes!",
  intent: "greeting",
  timestamp: new Date().toISOString(),
};

export default function ChatPage() {
  const { user } = useUser();
  const router = useRouter();
  const messagesEndRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [pendingConfirm, setPendingConfirm] = useState(null);
  const [error, setError] = useState("");

  // Load chat history on mount
  useEffect(() => {
    async function loadChatHistory() {
      try {
        const res = await fetch("/api/chat");
        if (res.ok) {
          const data = await res.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
          } else {
            setMessages([INITIAL_GREETING]);
          }
        }
      } catch (err) {
        console.error("Failed to load history", err);
        setMessages([INITIAL_GREETING]);
      } finally {
        setInitialLoading(false);
      }
    }
    loadChatHistory();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function formatTime(isoString) {
    if (!isoString) return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    return new Date(isoString).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // Build conversation history for the AI backend
  function getConversationHistory() {
    return messages
      .filter((m) => m.role !== "typing")
      .map((m) => ({
        role: m.role === "ai" ? "assistant" : "user",
        content: m.content,
      }));
  }

  async function syncMessagesToDB(newMessages) {
    try {
      await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });
    } catch (err) {
      console.error("Failed to sync messages to DB", err);
    }
  }

  async function handleClearChat() {
    if (!confirm("Are you sure you want to clear your conversation history?")) return;
    try {
      setLoading(true);
      await fetch("/api/chat", { method: "DELETE" });
      setMessages([{ ...INITIAL_GREETING, timestamp: new Date().toISOString() }]);
      setPendingConfirm(null);
    } catch (err) {
      console.error("Failed to clear chat", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(text) {
    setError("");

    // Add user message
    const userMsg = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversation_history: getConversationHistory(), // Send history *before* this msg
          clerk_id: user?.id || "",
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to get response");
      }

      const data = await res.json();
      console.log("Backend response:", data);

      const aiMsg = {
        role: "ai",
        content: data.message,
        intent: data.intent,
        timestamp: new Date().toISOString(),
      };

      // Add AI response to local state
      setMessages((prev) => {
        // Sync both new messages to the DB
        syncMessagesToDB([userMsg, aiMsg]);
        return [...prev, aiMsg];
      });

      // Special handling for UI components attached to the message
      if (data.suggested_topics || data.suggested_category) {
        // We still store them temporarily in a wrapper since our ChatMessage expects those
        aiMsg.suggested_topics = data.suggested_topics;
        aiMsg.suggested_category = data.suggested_category;
      }

      // If the AI provides confirmed_data, update our pending state
      if (data.confirmed_data) {
        setPendingConfirm(data.confirmed_data);
      }
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleSuggestionClick(topic) {
    handleSend(topic);
  }

  async function handleConfirm() {
    console.log("handleConfirm triggered. pendingConfirm:", pendingConfirm);
    
    let topicToSave = pendingConfirm;
    
    // If no AI summary yet, allow manual title entry for "Save Anytime"
    if (!topicToSave) {
      const manualTitle = window.prompt("Enter a title for this topic to save it now:");
      if (!manualTitle) {
        console.log("Manual save cancelled by user.");
        return;
      }
      
      topicToSave = {
        title: manualTitle,
        category: "General",
        user_content: messages.map(m => m.content).filter(c => c).join("\n"),
        interval_days: 1,
        preferred_time: "09:00"
      };
      console.log("Proceeding with manual save for:", manualTitle);
    }

    setLoading(true);
    setError("");

    try {
      console.log("Saving topic via /api/topics...");
      const res = await fetch("/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: topicToSave.title,
          category: topicToSave.category,
          user_content: topicToSave.user_content || null,
          enhanced_content: null,
          interval_days: topicToSave.interval_days ?? 1,
          preferred_time: topicToSave.preferred_time || "09:00",
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Server error: ${res.status}`);
      }

      const data = await res.json();
      console.log("Save successful:", data);

      setPendingConfirm(null);
      
      // Immediate redirect for better UX
      console.log("Redirecting to dashboard...");
      router.push("/dashboard");
    } catch (err) {
      console.error("Save error:", err);
      setError(err.message);
      alert(`Could not save topic: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleEdit() {
    setPendingConfirm(null);
    handleSend("I want to change some details");
  }

  if (initialLoading) {
    return (
      <div className={styles.page}>
        <Navbar />
        <div className={styles.container} style={{ justifyContent: "center", alignItems: "center" }}>
          Loading chat...
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Navbar />
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>💬 Chat with Revision AI</h1>
            <p className={styles.subtitle}>
              Tell me your topics and I&apos;ll organize your revisions
            </p>
          </div>
          <div className={styles.headerActions}>
            <button 
              className={styles.saveBtn} 
              onClick={handleConfirm} 
              disabled={loading}
              title="Save current chat as a topic anytime"
            >
              💾 Save Topic
            </button>
            <button className={styles.clearBtn} onClick={handleClearChat} disabled={loading}>
              🗑 Clear Chat
            </button>
          </div>
        </div>

        <div className={styles.messagesArea}>
          <div className={styles.messagesList}>
            {messages.map((msg, i) => (
              <ChatMessage
                key={i}
                message={{
                  ...msg,
                  time: formatTime(msg.timestamp),
                  // If we have pending confirmation data, only attach actions to the LATEST message
                  ...(pendingConfirm &&
                  msg.role === "ai" &&
                  i === messages.length - 1
                    ? { confirmed_data: pendingConfirm }
                    : {}),
                }}
                onSuggestionClick={handleSuggestionClick}
                onConfirm={handleConfirm}
                onEdit={handleEdit}
              />
            ))}

            {loading && <ChatMessage message={{ role: "typing" }} />}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {error && (
          <div className={styles.error}>
            <span>⚠️ {error}</span>
            <button className={styles.dismissBtn} onClick={() => setError("")}>
              ✕
            </button>
          </div>
        )}

        <div className={styles.inputArea}>
          <div className={styles.inputWrapper}>
            <ChatInput onSend={handleSend} disabled={loading} />
            {pendingConfirm && (
              <button 
                className={styles.floatingSaveBtn} 
                onClick={handleConfirm}
                disabled={loading}
              >
                ✅ Save & Go to Dashboard
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
