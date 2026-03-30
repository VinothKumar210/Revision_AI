import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import LandingPage from "@/components/LandingPage";

export default async function Home() {
  const { userId } = await auth();

  if (userId) {
    // Check onboarding status
    try {
      const { default: prisma } = await import("@/lib/db");
      const user = await prisma.user.findUnique({
        where: { clerkId: userId },
        select: { isOnboarded: true },
      });

      if (!user || !user.isOnboarded) {
        redirect("/onboarding");
      }
      redirect("/dashboard");
    } catch {
      redirect("/onboarding");
    }
  }

  // Not logged in — show landing page
  return <LandingPage />;
}
