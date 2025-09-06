import asyncio
from zoneinfo import ZoneInfo  # Python 3.9+
from datetime import datetime, timezone, timedelta
from telethon.tl.functions.messages import DeleteChatRequest
from utils.logger import logger
from utils.telegram_helpers import retrieve_session
from controllers.db_controller import DatabaseController


async def delete_unused_groups(db: DatabaseController):
    """
    Runs every night at 03:00 UTC. Deletes Telegram groups that are inactive
    and removes them from the DB using their original session.
    """
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
                    client = await retrieve_session(session_name)

                    if not client:
                        logger.warning(f"[Cleanup] Failed to load client for session {session_name}")
                        continue
                    if not client.is_connected():
                        await client.start()
                    try:
                        # 3. Delete group
                        await client(DeleteChatRequest(chat_id=abs(group_id)))
                        logger.info(f"[Cleanup] Deleted Telegram group {group_id}")
                        
                        # 4. Delete from DB
                        await db.delete_support_group(user_id)
                        await client.disconnect()
                        logger.info(f"[Cleanup] Deleted group {group_id} for user {user_id} from DB")
                    except Exception as e:
                        logger.warning(f"[Cleanup] Could not delete group {group_id}: {e}")
                        await client.disconnect()
                        continue

                except Exception as inner_e:
                    logger.error(f"[Cleanup] Error with user_id {user_id}, group_id {group_id}: {inner_e}")

        except Exception as outer_e:
            logger.error(f"[Cleanup] Unexpected error in cleanup loop: {outer_e}")

        # Always wait a bit before retrying (e.g., 5 minutes if something goes wrong)
        await asyncio.sleep(300)
