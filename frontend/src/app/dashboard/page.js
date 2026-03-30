"use client";

import { useState, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import ConfirmDialog from "@/components/ConfirmDialog";
import EditTopicModal from "@/components/EditTopicModal";
import EditScheduleModal from "@/components/EditScheduleModal";
import styles from "./dashboard.module.css";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const LEVEL_LABELS = ["Basic", "Detailed", "In-Depth", "Advanced"];
const LEVEL_COLORS = ["#74b9ff", "#a29bfe", "#6c5ce7", "#e17055"];

export default function DashboardPage() {
  const { user } = useUser();
  const [topics, setTopics] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [topicToDelete, setTopicToDelete] = useState(null);
  const [topicToEdit, setTopicToEdit] = useState(null);
  const [scheduleToDelete, setScheduleToDelete] = useState(null);
  const [scheduleToEdit, setScheduleToEdit] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const [topicsRes, schedulesRes] = await Promise.all([
        fetch("/api/topics"),
        fetch("/api/schedules"),
      ]);
      const topicsData = await topicsRes.json();
      const schedulesData = await schedulesRes.json();
      setTopics(topicsData.topics || []);
      setSchedules(schedulesData.schedules || []);
    } catch {
      console.error("Failed to fetch dashboard data");
    } finally {
      setLoading(false);
    }
  }

  // --- Topic Handlers ---

  async function handleToggleStatus(topic) {
    const newStatus = topic.status === "ACTIVE" ? "PAUSED" : "ACTIVE";
    try {
      const res = await fetch(`/api/topics/${topic.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setTopics(topics.map(t => t.id === topic.id ? { ...t, status: newStatus } : t));
      }
    } catch (err) {
      console.error("Failed to toggle status", err);
    }
  }

  async function handleDeleteTopic() {
    if (!topicToDelete) return;
    setActionLoading(true);
    try {
      const res = await fetch(`/api/topics/${topicToDelete.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setTopics(topics.filter(t => t.id !== topicToDelete.id));
        setSchedules(schedules.filter(s => s.topicId !== topicToDelete.id));
      }
    } catch (err) {
      console.error("Failed to delete topic", err);
    } finally {
      setActionLoading(false);
      setTopicToDelete(null);
    }
  }

  async function handleSaveTopicEdit(updatedData) {
    if (!topicToEdit) return;
    setActionLoading(true);
    try {
      const res = await fetch(`/api/topics/${topicToEdit.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData),
      });
      if (res.ok) {
        const data = await res.json();
        const updatedTopic = data.topic;
        if (updatedTopic && updatedTopic.id) {
          setTopics(prev => prev.map(t => t.id === updatedTopic.id ? updatedTopic : t));
        } else {
          console.warn("Topic update succeeded but no object returned. Refreshing...");
          fetchData();
        }
      }
    } catch (err) {
      console.error("Failed to edit topic", err);
    } finally {
      setActionLoading(false);
      setTopicToEdit(null);
    }
  }

  // --- Schedule Handlers ---

  function openCreateScheduleModal(topic) {
    setScheduleToEdit({
      topicId: topic.id,
      topicTitle: topic.title,
      intervalDays: 0,
      preferredTime: "08:00",
      phoneNumber: user?.primaryPhoneNumber?.phoneNumber || ""
    });
  }

  async function handleDeleteSchedule() {
    if (!scheduleToDelete) return;
    setActionLoading(true);
    try {
      const res = await fetch(`/api/schedules/${scheduleToDelete.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setSchedules(schedules.filter(s => s.id !== scheduleToDelete.id));
      }
    } catch (err) {
      console.error("Failed to delete schedule", err);
    } finally {
      setActionLoading(false);
      setScheduleToDelete(null);
    }
  }

  async function handleSaveScheduleEdit(updatedData) {
    if (!scheduleToEdit) return;
    setActionLoading(true);
    try {
      // Determine if it's a new or existing schedule
      const isNew = !scheduleToEdit.id;
      const endpoint = isNew ? "/api/schedules" : `/api/schedules/${scheduleToEdit.id}`;
      const method = isNew ? "POST" : "PUT";

      // If new, pass topic_id
      const payload = isNew 
        ? { 
            topic_id: scheduleToEdit.topicId, 
            interval_days: updatedData.intervalDays,
            preferred_time: updatedData.preferredTime,
            phone_number: updatedData.phoneNumber
          } 
        : updatedData;

      const res = await fetch(endpoint, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        if (isNew) {
          fetchData(); // reload schedules completely
        } else {
          const data = await res.json();
          const updatedSchedule = data.schedule;
          if (updatedSchedule && updatedSchedule.id) {
            setSchedules(prev => prev.map(s => s.id === updatedSchedule.id ? updatedSchedule : s));
          } else {
            console.warn("Update succeeded but no schedule object returned. Refreshing data...");
            fetchData();
          }
        }
      } else {
        const errText = await res.text();
        alert(`Failed to save schedule: ${errText}`);
      }
    } catch (err) {
      console.error("Failed to save schedule", err);
    } finally {
      setActionLoading(false);
      setScheduleToEdit(null);
    }
  }

  const hasData = topics.length > 0;

  return (
    <div className={styles.page}>
      <Navbar />
      <div className={styles.container}>
        {/* Welcome */}
        <div className={styles.welcome}>
          <h1 className={styles.title}>
            Welcome back, {user?.firstName || "Student"} 👋
          </h1>
          <p className={styles.subtitle}>
            {hasData
              ? `You have ${topics.length} topic${topics.length !== 1 ? "s" : ""} and ${schedules.length} active schedule${schedules.length !== 1 ? "s" : ""}.`
              : "Start by adding topics to revise."}
          </p>
        </div>

        {/* Quick Actions */}
        <div className={styles.quickActions}>
          <Link href="/chat" className={styles.primaryAction}>
            <span>💬</span> Add Topics via Chat
          </Link>
          <Link href="/settings" className={styles.secondaryAction}>
            <span>⚙️</span> Settings
          </Link>
        </div>

        {/* Loading */}
        {loading && (
          <div className={styles.skeletonGrid}>
            {[1, 2, 3].map((i) => (
              <div key={i} className={styles.skeleton}></div>
            ))}
          </div>
        )}

        {/* Topics */}
        {!loading && hasData && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>📚 Your Topics</h2>
            <div className={styles.topicGrid}>
              {topics.map((topic) => {
                const level = topic.revisionLevel || 0;
                const schedule = schedules.find(
                  (s) => s.topicId === topic.id
                );
                return (
                  <div key={topic.id} className={`${styles.topicCard} ${topic.status === 'PAUSED' ? styles.topicPaused : ''}`}>
                    <div className={styles.topicHeader}>
                      <h3 className={styles.topicTitle}>{topic.title}</h3>
                      <div className={styles.topicHeaderActions}>
                         <button 
                           className={styles.iconBtn} 
                           onClick={() => setTopicToEdit(topic)}
                           title="Edit Topic"
                         >
                           ✏️
                         </button>
                         <button 
                           className={styles.iconBtn} 
                           onClick={() => setTopicToDelete(topic)}
                           title="Delete Topic"
                         >
                           🗑
                         </button>
                      </div>
                    </div>
                    <div className={styles.topicMeta}>
                      <span className={styles.category}>
                        📁 {topic.category || "General"}
                      </span>
                      <span className={styles.levelBadge} style={{ background: `${LEVEL_COLORS[level]}20`, color: LEVEL_COLORS[level] }}>
                        {LEVEL_LABELS[level]}
                      </span>
                    </div>
                    
                    {/* Integrated Schedule Info */}
                    <div className={styles.scheduleInfoInline}>
                      {schedule ? (
                        <div className={styles.activeScheduleBox}>
                          <div className={styles.scheduleDetails}>
                            <span>⏰ Every {schedule.intervalDays} day{schedule.intervalDays !== 1 ? "s" : ""} at {schedule.preferredTime}</span>
                            <span className={styles.phoneLabel}>📱 Sends to: {schedule.phoneNumber || user?.primaryPhoneNumber?.phoneNumber || "No phone set"}</span>
                            {schedule.isActive ? (
                              <span className={styles.activeDot}>● Active</span>
                            ) : (
                              <span className={styles.pausedDot}>● Paused</span>
                            )}
                          </div>
                          <div className={styles.scheduleActionsRow}>
                            <button 
                              className={styles.iconBtn} 
                              onClick={() => setScheduleToEdit(schedule)}
                              title="Edit Schedule Time"
                            >
                              🕒
                            </button>
                            <button 
                              className={styles.iconBtn} 
                              onClick={() => setScheduleToDelete(schedule)}
                              title="Remove Schedule"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className={styles.noScheduleBox}>
                          <span className={styles.scheduleDetail}>No active schedule</span>
                        </div>
                      )}
                    </div>

                    {/* Progress bar */}
                    <div className={styles.progressWrap}>
                      <div
                        className={styles.progressBar}
                        style={{
                          width: `${((level + 1) / 4) * 100}%`,
                          background: LEVEL_COLORS[level],
                          opacity: topic.status === 'PAUSED' ? 0.5 : 1
                        }}
                      ></div>
                    </div>

                    <div className={styles.topicActions}>
                      <button 
                        className={styles.statusToggleBtn}
                        onClick={() => handleToggleStatus(topic)}
                      >
                        {topic.status === "ACTIVE" ? "⏸ Pause" : "▶ Resume"}
                      </button>

                      {!schedule && topic.status === "ACTIVE" && (
                        <button
                          className={styles.scheduleBtn}
                          onClick={() => openCreateScheduleModal(topic)}
                        >
                          📅 Set Schedule
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Empty state */}
        {!loading && !hasData && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>📚</div>
            <h3>No topics yet</h3>
            <p>Chat with AI to add your first revision topic</p>
            <Link href="/chat" className={styles.emptyBtn}>
              Start Chatting →
            </Link>
          </div>
        )}
      </div>

      {/* Modals */}
      {topicToDelete && (
        <ConfirmDialog
          title="Delete Topic"
          message={`Are you sure you want to delete "${topicToDelete.title}"? This will also delete any active schedules for this topic.`}
          onConfirm={handleDeleteTopic}
          onCancel={() => setTopicToDelete(null)}
          loading={actionLoading}
        />
      )}

      {topicToEdit && (
        <EditTopicModal
          topic={topicToEdit}
          onSave={handleSaveTopicEdit}
          onCancel={() => setTopicToEdit(null)}
          loading={actionLoading}
        />
      )}

      {scheduleToDelete && (
        <ConfirmDialog
          title="Delete Schedule"
          message={`Are you sure you want to delete the schedule for "${scheduleToDelete.topicTitle}"?`}
          onConfirm={handleDeleteSchedule}
          onCancel={() => setScheduleToDelete(null)}
          loading={actionLoading}
        />
      )}

      {scheduleToEdit && (
        <EditScheduleModal
          schedule={scheduleToEdit}
          onSave={handleSaveScheduleEdit}
          onCancel={() => setScheduleToEdit(null)}
          loading={actionLoading}
        />
      )}
    </div>
  );
}
