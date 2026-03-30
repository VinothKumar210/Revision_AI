import { useState } from "react";
import styles from "./EditScheduleModal.module.css";

export default function EditScheduleModal({ schedule, onSave, onCancel, loading }) {
  const [intervalDays, setIntervalDays] = useState(schedule.intervalDays ?? 0);
  const [preferredTime, setPreferredTime] = useState(schedule.preferredTime || "08:00");
  const [phoneNumber, setPhoneNumber] = useState(schedule.phoneNumber || "");

  function handleSave() {
    onSave({ 
      intervalDays: parseInt(intervalDays, 10) || 0, 
      preferredTime,
      phoneNumber
    });
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Edit Schedule</h2>
          <button className={styles.closeBtn} onClick={onCancel} disabled={loading}>
            ✕
          </button>
        </div>

        <div className={styles.body}>
          <h3 className={styles.topicTitle}>{schedule.topicTitle}</h3>
          
          <div className={styles.fieldRow}>
            <div className={styles.field}>
              <label className={styles.label}>Repeat every</label>
              <div className={styles.inputWithSuffix}>
                <input
                  type="number"
                  min="0"
                  max="30"
                  className={styles.input}
                  value={intervalDays}
                  onChange={(e) => setIntervalDays(e.target.value)}
                  disabled={loading}
                />
                <span className={styles.suffix}>days</span>
              </div>
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Preferred Time</label>
              <input
                type="time"
                className={styles.input}
                value={preferredTime}
                onChange={(e) => setPreferredTime(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Phone Number (with + country code)</label>
            <input
              type="text"
              placeholder="+1234567890"
              className={styles.input}
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              disabled={loading}
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
            disabled={loading}
          >
            {loading ? "Saving..." : (schedule.id ? "Save Changes" : "Create Schedule")}
          </button>
        </div>
      </div>
    </div>
  );
}
