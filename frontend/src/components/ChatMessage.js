import styles from "./ChatMessage.module.css";

export default function ChatMessage({
  message,
  onSuggestionClick,
  onConfirm,
  onEdit,
}) {
  const isUser = message.role === "user";
  const isTyping = message.role === "typing";

  if (isTyping) {
    return (
      <div className={styles.typing}>
        <span className={styles.dot}></span>
        <span className={styles.dot}></span>
        <span className={styles.dot}></span>
      </div>
    );
  }

  return (
    <div className={`${styles.bubble} ${isUser ? styles.user : styles.ai}`}>
      <div className={styles.content}>
        <p>{message.content}</p>
      </div>

      {/* Suggestion chips */}
      {message.suggested_topics && message.suggested_topics.length > 0 && (
        <div className={styles.suggestions}>
          {message.suggested_topics.map((topic, i) => (
            <button
              key={i}
              className={styles.chip}
              onClick={() => onSuggestionClick?.(topic)}
            >
              {topic}
            </button>
          ))}
        </div>
      )}

      {/* Confirm/Edit actions for save intent */}
      {message.confirmed_data && (
        <div className={styles.actions}>
          <button className={styles.confirmBtn} onClick={onConfirm}>
            ✓ Confirm & Save
          </button>
          <button className={styles.editBtn} onClick={onEdit}>
            ✎ Edit
          </button>
        </div>
      )}

      <div
        className={`${styles.timestamp} ${isUser ? styles.userTimestamp : ""}`}
      >
        {message.time || ""}
      </div>
    </div>
  );
}
