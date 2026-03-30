import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import prisma from "@/lib/db";

// GET: Fetch the user's conversation history
export async function GET() {
  try {
    const { userId: clerkId } = await auth();
    if (!clerkId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const dbUser = await prisma.user.findUnique({ where: { clerkId } });
    if (!dbUser) {
      return NextResponse.json({ messages: [] });
    }

    const conversation = await prisma.chatConversation.findUnique({
      where: { userId: dbUser.id },
    });

    if (!conversation) {
      return NextResponse.json({ messages: [] });
    }

    // Sort by timestamp just in case
    const sortedMessages = conversation.messages.sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    return NextResponse.json({ messages: sortedMessages });
  } catch (error) {
    console.error("Failed to fetch chat history:", error);
    return NextResponse.json(
      { error: "Failed to fetch chat history" },
      { status: 500 }
    );
  }
}

// POST: Append new messages to the conversation
export async function POST(request) {
  try {
    const { userId: clerkId } = await auth();
    if (!clerkId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const dbUser = await prisma.user.findUnique({ where: { clerkId } });
    if (!dbUser) {
      return NextResponse.json({ error: "User not found in DB" }, { status: 404 });
    }
    const userId = dbUser.id;

    const { messages } = await request.json();

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: "Messages array is required" },
        { status: 400 }
      );
    }

    const conversation = await prisma.chatConversation.upsert({
      where: { userId },
      update: {
        messages: {
          push: messages.map(m => ({
            role: m.role,
            content: m.content,
            intent: m.intent || null,
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
          })),
        },
      },
      create: {
        userId,
        messages: messages.map(m => ({
          role: m.role,
          content: m.content,
          intent: m.intent || null,
          timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
        })),
      },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Failed to append chat messages:", error);
    return NextResponse.json(
      { error: "Failed to append chat messages" },
      { status: 500 }
    );
  }
}

// DELETE: Clear the user's conversation history
export async function DELETE() {
  try {
    const { userId: clerkId } = await auth();
    if (!clerkId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const dbUser = await prisma.user.findUnique({ where: { clerkId } });
    if (!dbUser) {
      return NextResponse.json({ success: true });
    }

    await prisma.chatConversation.deleteMany({
      where: { userId: dbUser.id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Failed to clear chat history:", error);
    return NextResponse.json(
      { error: "Failed to clear chat history" },
      { status: 500 }
    );
  }
}
