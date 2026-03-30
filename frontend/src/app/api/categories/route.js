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

    // Get user's categories from backend
    const res = await fetch(
      `${BACKEND_URL}/topics?clerk_id=${userId}`
    );
    const data = await res.json();

    // Extract unique categories
    const categoriesMap = {};
    for (const topic of data.topics || []) {
      if (topic.category && !categoriesMap[topic.category]) {
        categoriesMap[topic.category] = {
          name: topic.category,
          id: topic.categoryId,
        };
      }
    }

    return NextResponse.json({
      categories: Object.values(categoriesMap),
    });
  } catch (error) {
    console.error("Categories fetch error:", error);
    return NextResponse.json(
      { error: "Failed to fetch categories" },
      { status: 500 }
    );
  }
}
