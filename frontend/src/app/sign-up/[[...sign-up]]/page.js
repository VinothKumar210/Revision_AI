import { SignUp } from "@clerk/nextjs";
import styles from "./sign-up.module.css";

export default function SignUpPage() {
  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <SignUp
          appearance={{
            elements: {
              rootBox: styles.clerkRoot,
              card: styles.clerkCard,
            },
          }}
        />
      </div>
    </div>
  );
}
