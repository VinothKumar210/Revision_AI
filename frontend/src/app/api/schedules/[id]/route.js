import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// PUT: Update schedule interval or time
export async function PUT(request, context) {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await context.params;
    const body = await request.json();

    console.log(`[API Proxy] Updating schedule ${id} via FastAPI...`);
    
    const res = await fetch(`${BACKEND_URL}/schedules/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clerk_id: userId,
        interval_days: body.intervalDays,
        preferred_time: body.preferredTime,
        phone_number: body.phoneNumber,
        is_active: body.isActive
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error(`[API Proxy] FastAPI error ${res.status}: ${errText}`);
      return NextResponse.json({ error: errText }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to update schedule proxy:", error);
    return NextResponse.json(
      { error: "Failed to update schedule" },
      { status: 500 }
    );
  }
}

// DELETE: Delete a schedule
export async function DELETE(request, context) {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await context.params;

    console.log(`[API Proxy] Deleting schedule ${id} via FastAPI...`);
    
    const res = await fetch(`${BACKEND_URL}/schedules/${id}?clerk_id=${userId}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json({ error: errText }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to delete schedule proxy:", error);
    return NextResponse.json(
      { error: "Failed to delete schedule" },
      { status: 500 }
    );
  }
}
