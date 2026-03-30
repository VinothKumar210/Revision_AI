import { NextResponse } from "next/server";
import { auth, currentUser } from "@clerk/nextjs/server";
import prisma from "@/lib/db";

export async function POST(request) {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const clerkUser = await currentUser();
    const email = clerkUser?.emailAddresses?.[0]?.emailAddress || "";

    const body = await request.json();
    const { name, phone } = body;

    if (!name || !name.trim()) {
      return NextResponse.json(
        { error: "Name is required." },
        { status: 400 }
      );
    }
    if (!phone || phone.length < 10) {
      return NextResponse.json(
        { error: "Valid WhatsApp number is required." },
        { status: 400 }
      );
    }

    const user = await prisma.user.upsert({
      where: { clerkId: userId },
      update: {
        name: name.trim(),
        phone: phone,
        email: email,
        isOnboarded: true,
      },
      create: {
        clerkId: userId,
        email: email,
        name: name.trim(),
        phone: phone,
        isOnboarded: true,
      },
    });

    return NextResponse.json({
      success: true,
      user: {
        id: user.id,
        name: user.name,
        phone: user.phone,
        isOnboarded: user.isOnboarded,
      },
    });
  } catch (error) {
    console.error("Onboarding error:", error);
    return NextResponse.json(
      { error: "Failed to save profile. Please try again." },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    });

    return NextResponse.json({
      isOnboarded: user?.isOnboarded || false,
      user: user
        ? {
            name: user.name,
            phone: user.phone,
          }
        : null,
    });
  } catch (error) {
    console.error("Onboarding check error:", error);
    return NextResponse.json(
      { error: "Failed to check onboarding status." },
      { status: 500 }
    );
  }
}
