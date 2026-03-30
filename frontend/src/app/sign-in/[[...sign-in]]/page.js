import { SignIn } from "@clerk/nextjs";
import styles from "./sign-in.module.css";

export default function SignInPage() {
  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <SignIn
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
