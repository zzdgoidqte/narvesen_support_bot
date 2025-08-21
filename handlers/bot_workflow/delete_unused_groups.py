import os
import json
import asyncio
from zoneinfo import ZoneInfo  # Python 3.9+
from datetime import datetime, timezone, timedelta
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import DeleteChatRequest
from utils.logger import logger
from controllers.db_controller import DatabaseController


async def delete_unused_groups(db: DatabaseController):
    """
    Runs every night at 03:00 UTC. Deletes Telegram groups that are inactive
    and removes them from the DB using their original session.
    """
    session_dir = "sessions/narvesensupportbot"
    while True:
        try:
            now = datetime.now(timezone.utc)
            target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now >= target_time:
                target_time += timedelta(days=1)

            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"[Cleanup] Sleeping until next cleanup at {target_time} UTC ({int(wait_seconds)}s)")
            await asyncio.sleep(wait_seconds)

            logger.info("[Cleanup] Starting delete_unused_groups check")
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=5)

            groups = await db.get_all_support_groups_with_creator()

            for user_id, group_id, created_by in groups:
                try:
                    if not created_by:
                        logger.warning(f"[Cleanup] No session found for user_id {user_id}")
                        continue

                    # 1. Check ticket activity
                    open_tickets = await db.get_user_open_tickets(user_id)
                    if open_tickets:
                        continue

                    latest_created_at = await db.get_user_latest_ticket_date(user_id)
                    
                    if latest_created_at:
                        # Assume naive datetime is in Helsinki time
                        latest_created_at = latest_created_at.replace(tzinfo=ZoneInfo("Europe/Helsinki"))
                        # Convert to UTC
                        latest_created_at = latest_created_at.astimezone(timezone.utc)
                    
                    if not latest_created_at or latest_created_at > cutoff_date:
                        continue

                    # 2. Load session and credentials
                    session_name = created_by.strip()
                    session_path = os.path.join(session_dir, session_name)
                    json_path = os.path.join(session_dir, session_name + ".json")

                    if not os.path.exists(json_path):
                        logger.warning(f"[Cleanup] JSON file missing for {session_name}")
                        continue

                    with open(json_path, "r") as f:
                        creds = json.load(f)
                        api_id = creds.get("app_id")
                        api_hash = creds.get("app_hash")

                    if not api_id or not api_hash:
                        logger.warning(f"[Cleanup] Incomplete credentials for {session_name}")
                        continue

                    # 3. Connect and delete group
                    client = TelegramClient(session_path, api_id, api_hash)
                    await client.connect()

                    if not await client.is_user_authorized():
                        logger.warning(f"[Cleanup] Session {session_name} not authorized")
                        await client.disconnect()
                        continue

                    try:
                        await client(DeleteChatRequest(chat_id=abs(group_id)))
                        logger.info(f"[Cleanup] Deleted Telegram group {group_id}")
                        
                        # 4. Delete from DB
                        await db.delete_support_group(user_id)
                        logger.info(f"[Cleanup] Deleted group {group_id} for user {user_id} from DB")
                    except Exception as e:
                        logger.warning(f"[Cleanup] Could not delete group {group_id}: {e}")
                        await client.disconnect()
                        continue

                    await client.disconnect()

                except Exception as inner_e:
                    logger.error(f"[Cleanup] Error with user_id {user_id}, group_id {group_id}: {inner_e}")

        except Exception as outer_e:
            logger.error(f"[Cleanup] Unexpected error in cleanup loop: {outer_e}")

        # Always wait a bit before retrying (e.g., 5 minutes if something goes wrong)
        await asyncio.sleep(300)
