import styles from "./ConfirmDialog.module.css";

export default function ConfirmDialog({ title, message, onConfirm, onCancel, loading }) {
  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button className={styles.confirmBtn} onClick={onConfirm} disabled={loading}>
            {loading ? "Please wait..." : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}
