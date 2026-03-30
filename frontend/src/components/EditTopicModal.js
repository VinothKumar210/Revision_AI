import { useState } from "react";
import styles from "./EditTopicModal.module.css";

export default function EditTopicModal({ topic, onSave, onCancel, loading }) {
  const [title, setTitle] = useState(topic.title || "");
  const [userContent, setUserContent] = useState(topic.userContent || "");

  function handleSave() {
    if (!title.trim()) return;
    onSave({ title: title.trim(), userContent: userContent.trim() });
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Edit Topic</h2>
          <button className={styles.closeBtn} onClick={onCancel} disabled={loading}>
            ✕
          </button>
        </div>

        <div className={styles.body}>
          <div className={styles.field}>
            <label className={styles.label}>Topic Title</label>
            <input
              type="text"
              className={styles.input}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={loading}
              placeholder="e.g. Photosynthesis"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Study Notes (Optional)</label>
            <textarea
              className={styles.textarea}
              value={userContent}
              onChange={(e) => setUserContent(e.target.value)}
              disabled={loading}
              placeholder="Paste your study notes or questions here to give the AI context..."
              rows={6}
            />
          </div>
        </div>

        <div className={styles.footer}>
          <button className={styles.cancelBtn} onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button 
            className={styles.saveBtn} 
            onClick={handleSave} 
            disabled={loading || !title.trim()}
          >
            {loading ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
