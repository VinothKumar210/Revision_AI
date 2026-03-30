import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add the backend root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bson import ObjectId
from config import get_settings
from services.database import topics_collection, schedules_collection, users_collection, get_db, connect_db, disconnect_db
from services.scheduler_service import check_and_send_revisions

async def run_test():
    print("🚀 Starting End-to-End WhatsApp Test...")
    
    # Ensure database connects
    await connect_db()
    client = get_db()
    
    # 1. Update the specific user with the requested phone number
    email = "vkcricscore@gmail.com"
    # Ensure standard international Twilio format (+91 for India since 9384 is Indian)
    phone = "+919384366713" 

    user = await users_collection().find_one({"email": email})
    if not user:
        print(f"❌ Error: User with email {email} not found in the database.")
        sys.exit(1)
        
    # Force update the phone number for this test
    await users_collection().update_one(
        {"_id": user["_id"]},
        {"$set": {"phone": phone}}
    )
    user["phone"] = phone

    print(f"👤 Found User: {user.get('name', 'Student')} | Email: {email}")
    print(f"📱 Phone Updated To: {phone}")
    
    # 2. Add the test topic directly to the database
    topic_id = ObjectId()
    await topics_collection().insert_one({
        "_id": topic_id,
        "userId": str(user["_id"]),
        "title": "React Hooks Test",
        "category": "Programming",
        "userContent": "React hooks allow you to manage state. `useState` is used for setting local component state. `useEffect` is used for managing side effects like data fetching or subscriptions.",
        "revisionLevel": 0,
        "status": "ACTIVE",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    })
    
    # 3. Create a Schedule simulating "Every 1 minute"
    # We set nextRunAt to the PAST so the scheduler picks it up immediately.
    schedule_id = ObjectId()
    await schedules_collection().insert_one({
        "_id": schedule_id,
        "userId": str(user["_id"]),
        "topicId": str(topic_id),
        "intervalDays": 1,  # Conceptually 1 minute for this test
        "preferredTime": "12:00",
        "isActive": True,
        "nextRunAt": datetime.utcnow() - timedelta(minutes=1), # Due immediately!
        "lastSentAt": None,
        "createdAt": datetime.utcnow()
    })
    
    print("\n✅ Successfully created 'React Hooks Test' Topic & Schedule.")
    print("👀 Look at the Dashboard (http://localhost:3000/dashboard) to confirm it appears.")
    print("-----------------------------------------------------------------")
    print("⏳ Triggering APScheduler manually to dispatch the WhatsApp message now...")
    
    # 4. Trigger the scheduler function immediately to generate and send
    await check_and_send_revisions()
    
    print("\n📩 Check your WhatsApp on your phone! The Groq AI should have just sent the summary via Twilio.")
    print("-----------------------------------------------------------------")
    
    # 5. Simulate updating the schedule time to 5 mins
    print("🔄 Updating schedule to every '5 mins'...")
    await schedules_collection().update_one(
        {"_id": schedule_id},
        {"$set": {
            "intervalDays": 5, 
            "nextRunAt": datetime.utcnow() + timedelta(minutes=5)
        }}
    )
    print("✅ Schedule updated! Check the Dashboard again to see the updated interval.")
    print("-----------------------------------------------------------------")
    
    # 6. Delete everything cleanly
    input("🛑 Press [ENTER] when you are ready to cleanly delete the test topic and exit...")
    
    await schedules_collection().delete_one({"_id": schedule_id})
    await topics_collection().delete_one({"_id": topic_id})
    print("\n🗑️ Topics and Schedules successfully deleted. Test Complete!")

if __name__ == "__main__":
    asyncio.run(run_test())
