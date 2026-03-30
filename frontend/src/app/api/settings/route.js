import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Check if user has an API key stored
    const res = await fetch(
      `${BACKEND_URL}/topics?clerk_id=${userId}`
    );
    // For now, just return a placeholder. The actual key check
    // will be done when we implement the settings backend route.
    return NextResponse.json({ hasApiKey: false, keyHint: "" });
  } catch {
    return NextResponse.json({ hasApiKey: false });
  }
}

export async function POST(request) {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { groq_api_key } = body;

    if (!groq_api_key) {
      return NextResponse.json(
        { error: "API key required" },
        { status: 400 }
      );
    }

    // Store the API key in the user document
    async function getPrisma() {
      const { default: prisma } = await import("@/lib/db");
      return prisma;
    }

    const prisma = await getPrisma();
    await prisma.user.update({
      where: { clerkId: userId },
      data: { groqApiKey: groq_api_key },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Settings save error:", error);
    return NextResponse.json(
      { error: "Failed to save settings" },
      { status: 500 }
    );
  }
}

export async function DELETE() {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    async function getPrisma() {
      const { default: prisma } = await import("@/lib/db");
      return prisma;
    }

    const prisma = await getPrisma();
    await prisma.user.update({
      where: { clerkId: userId },
      data: { groqApiKey: null },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Settings delete error:", error);
    return NextResponse.json(
      { error: "Failed to remove API key" },
      { status: 500 }
    );
  }
}
