import os
import random
import json
from aiogram import Bot
from telethon import TelegramClient
from telethon.tl.functions.messages import CreateChatRequest, EditChatAboutRequest, EditChatPhotoRequest, EditChatAdminRequest
from telethon.tl.types import InputChatUploadedPhoto
from keyboards.inline import close_ticket
from utils.helpers import get_socks5_proxy, escape_markdown_v1
from utils.logger import logger
from config.config import Config
from controllers.db_controller import DatabaseController



async def get_random_available_session(db: DatabaseController, group_limit: int = 45) -> TelegramClient:
    """
    Find a usable Telethon session from the directory that owns fewer than `group_limit` groups
    based on the database record (via created_by column). Also updates the first name if needed.
    """
    session_dir = "sessions/narvesensupportbot"
    session_files = [f for f in os.listdir(session_dir) if f.endswith(".session")]
    random.shuffle(session_files)

    for session_file in session_files:
        session_name = session_file.replace(".session", "")
        session_path = os.path.join(session_dir, session_name)
        json_path = os.path.join(session_dir, session_name + ".json")

        # Load API credentials
        try:
            with open(json_path, "r") as f:
                json_data = json.load(f)
                api_id = json_data.get("app_id")
                api_hash = json_data.get("app_hash")
                if not api_id or not api_hash:
                    logger.warning(f"Missing API credentials in {json_path}")
                    continue
        except Exception as e:
            logger.warning(f"Failed to read JSON for session {session_name}: {e}")
            continue

        # Check in DB how many groups this session has created
        try:
            group_count = await db.count_of_groups_created_by(session_name)
            if group_count >= group_limit:
                logger.info(f"Session {session_name} already created {group_count} groups. Skipping session.")
                continue
        except Exception as e:
            logger.error(f"Failed to get group count for session {session_name} from DB: {e}")
            continue
        
        proxy = get_socks5_proxy()
        if not proxy:
            logger.info(f"Failed to retrieve proxy for session {session_name}. Skipping session.")
            continue

        # Initialize and authorize Telethon client
        client = TelegramClient(session_path, api_id, api_hash, proxy)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.warning(f"Session {session_name} is not authorized. Skipping session.")
                await client.disconnect()
                continue

            logger.info(f"Using session {session_name} ({group_count} existing groups for this session)")
            return client

        except Exception as e:
            logger.error(f"Failed to initialize or connect session {session_name}: {e}")
            await client.disconnect()
            continue

    logger.error("FAILED TO RETRIEVE AVAILABLE SESSION - ALL SESSIONS HAVE GROUP LIMIT REACHED OR BANNED")
    return None

async def retrieve_session(session_name):
    session_dir = "sessions/narvesensupportbot"
    session_path = os.path.join(session_dir, session_name)
    json_path = os.path.join(session_dir, session_name + ".json")

    if not os.path.exists(json_path):
        logger.warning(f"[Cleanup] JSON file missing for {session_name}")
        return None

    with open(json_path, "r") as f:
        creds = json.load(f)
        api_id = creds.get("app_id")
        api_hash = creds.get("app_hash")

    if not api_id or not api_hash:
        logger.warning(f"[Cleanup] Incomplete credentials for {session_name}")
        return None
    
    proxy = get_socks5_proxy()
    if not proxy:
        logger.warning(f"[Cleanup] Unable to retrieve proxy for {session_name}")
        return None
    
    client = TelegramClient(session_path, api_id, api_hash, proxy)
    await client.connect()

    # Initialize and authorize Telethon client
    client = TelegramClient(session_path, api_id, api_hash, proxy)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"[Cleanup] Session {session_name} is not authorized.")
            await client.disconnect()
            return None

        logger.info(f"Using session {session_name}")
        return client

    except Exception as e:
        logger.error(f"[Cleanup] Failed to initialize or connect session {session_name}: {e}")
        if client:
            await client.disconnect()
        return None
    

async def create_user_group(db: DatabaseController, client: TelegramClient, bot: Bot, user) -> int:
    """Create a user group and return its ID."""
    try:
        user_id = user.get("user_id")
        first_name = user.get("first_name")
        last_name = user.get("last_name")

        group_name = first_name + (" " + last_name if last_name else "")
        
        # Get bot and user entities
        bot_entity = await client.get_entity(Config.BOT_USERNAME)
        if Config.DEVELOPMENT_MODE:
            admin_entity = await client.get_entity(Config.SUPPORT_ADMIN_USERNAME)
        else:
            bot_settings = await db.get_bot_settings()
            support_username = bot_settings.get('support_username')
            admin_entity = await client.get_entity(support_username)

        if not bot_entity or not admin_entity:
            raise ValueError("Failed to retrieve bot or user entity")

        # Create a private group
        result = await client(CreateChatRequest(
            users=[bot_entity, admin_entity],
            title=group_name
        ))
        group_id = result.updates.chats[0].id
        group_id = -group_id
        group_entity = await client.get_entity(group_id)
        me = await client.get_me()
        created_by = '+' + me.phone

        await db.set_user_group_id(user_id, group_id, created_by)
        logger.info(f"Created new group '{group_name}' for user {user_id}")

        # Give support admin rights in case session gets banned
        await client(EditChatAdminRequest(
            chat_id=group_entity.id,
            user_id=admin_entity,
            is_admin=True
        ))
    
        # Set group description to user_id
        try:
            await client(EditChatAboutRequest(
                peer=group_id,  # direct int ID is okay here
                about=str(user_id)
            ))
            logger.info(f"Set group description to user_id: {user_id}")
        except Exception as e:
            logger.warning(f"Failed to set group description: {e}")

        
        # Set group profile pic using a local file
        try:
            photo_path = "data/warning.jpg"

            if os.path.exists(photo_path):
                logger.info(f"Using local photo: {photo_path}")
                uploaded_file = await client.upload_file(photo_path)
                input_photo = InputChatUploadedPhoto(uploaded_file)

                # Set the new group photo
                await client(EditChatPhotoRequest(
                    chat_id=group_entity.id,
                    photo=input_photo
                ))
            else:
                logger.error(f"Local photo not found: {photo_path}")
                
        except Exception as e:
            logger.warning(f"Failed to set group profile picture: {e}")
            
        return group_id

    except Exception as e:
        bot_settings = await db.get_bot_settings()
        raw_username = bot_settings.get('support_username', '')
        support_username = raw_username if raw_username.startswith('@') else '@' + raw_username
        await bot.send_message(
            chat_id=support_username,
            text=f"ERROR CREATING USER GROUP WITH USER {user_id}, {group_name}:\n{e}"
        )
        logger.error(f"Failed to create group for user {user_id}: {e}")
        raise

async def ask(db: DatabaseController, bot: Bot, user_id: int, group_id: int):
    """Handle automatic /ask for user when he writes for the first time, splitting response if over 4096 chars."""
    try:
        group_id = group_id 
        result = await db.get_user_and_drops(
            client_id=user_id,
            drop_statuses=["paid", "lost", "redrop", "angry_redrop"],
            order_by="updated_at ASC",
        )

        if not result or not result.get("user"):
            await bot.send_message(group_id, "ERROR: User not found in database.")
            return

        user = result["user"]
        drops = result.get("drops", [])
        roles = await db.get_user_roles(user["user_id"])

        # Escape user data
        escaped_username = escape_markdown_v1(user["username"] or "")
        escaped_first_name = escape_markdown_v1(user["first_name"] or "")
        escaped_last_name = escape_markdown_v1(user["last_name"] or "")

        # User info
        user_info = (
            f"👤 @{escaped_username} (`{user['user_id']}`)\n"
            f"🪪 [{escaped_first_name}](tg://user?id={user['user_id']}) {escaped_last_name}\n"
            f"🏷️ *Roles:* {", ".join(roles)}\n"
            f"🕒 *First interaction:* {user['created_at'].strftime("%Y-%m-%d %H:%M:%S")}\n"
            f"🕒 *Last interaction:* {user['updated_at'].strftime("%Y-%m-%d %H:%M:%S")}\n\n"
        )

        # Drop summary
        total_drops = len(drops)
        paid_drops = sum(1 for d in drops if d["status"] == "paid")
        lost_drops = sum(1 for d in drops if d["lost"] == True)
        normal_redrops = sum(1 for d in drops if d["status"] == "redrop")
        angry_redrops = sum(1 for d in drops if d["status"] == "angry_redrop")

        # Build summary, including only non-zero counts
        summary_lines = [f"*Summary*\n📦 Total drops: {total_drops}\n"]
        if paid_drops > 0:
            summary_lines.append(f"✔️ Paid drops: {paid_drops}")
        if lost_drops > 0:
            summary_lines.append(f"❌ Lost drops: {lost_drops}")
        if normal_redrops > 0:
            summary_lines.append(f"❤️ Normal redrops: {normal_redrops}")
        if angry_redrops > 0:
            summary_lines.append(f"🤡 Angry redrops: {angry_redrops}")

        summary = "\n".join(summary_lines)

        # drops table
        drops_table = ""
        if total_drops > 0:
            drops_table += "*Drop Summary*\n```perl\n"
            drops_table += (
                f"{'ID':<6} {'P':<2} {'Amt':<4} {'Area':<15} {'Date':<10} {'Status':<15}\n"
                f"{'-' * 6} {'-' * 2} {'-' * 4} {'-' * 15} {'-' * 10} {'-' * 10}\n"
            )
            for drop in drops:
                area = escape_markdown_v1((drop["area_name"] or ""))
                city = (escape_markdown_v1((drop["city_name"])) + ', ') if drop["city_name"] else ''
                status = "" if not drop["status"] or drop["status"] == "paid" else drop["status"].title()
                status = "🤡 Redrop" if status == "Angry_Redrop" else status
                is_lost = "" if not drop["lost"] else "(Lost)"
                formatted_date = drop["updated_at"].strftime("%Y-%m-%d")
                formatted_amount = str(round(drop['batch_amount'], 2)).rstrip('0').rstrip('.')
                drops_table += (
                    f"{drop['drop_id']:<5} {drop['product_emoji']:<2} {formatted_amount:<4} "
                    f"{(city + area)[:15]:<15} {formatted_date:<10} {status}{is_lost}\n"
                )
                    
                if drop.get("reason"):
                    drops_table += f"\tReason: {drop['reason']}\n"
            drops_table += "```\n"
        else:
            drops_table += "_No successful drops found._\n\n"

        # Full response
        full_response = user_info + drops_table + summary
        max_length = 4096

        if len(full_response) <= max_length:
            await bot.send_message(group_id, full_response, parse_mode="Markdown")
        else:
            # Try splitting: user info + summary in part 1, drops table in part 2
            part1 = user_info + summary
            part2 = drops_table
            if len(part1) < max_length and len(part2) < max_length:
                await bot.send_message(group_id, f"Part 1/2\n{part1}", parse_mode="Markdown")
                await bot.send_message(group_id, f"Part 2/2\n{part2}", parse_mode="Markdown")
            else:
                # Split drops table
                table_header = (
                    "*Drop Summary*\n```perl\n"
                    f"{'ID':<6} {'P':<7} {'Amt':<4} {'Area':<15} {'Date':<10} {'Status':<15}\n"
                    f"{'-' * 6} {'-' * 2} {'-' * 4} {'-' * 15} {'-' * 10} {'-' * 10}\n"
                )
                table_footer = "```\n"
                rows = []
                for drop in drops:
                    area = escape_markdown_v1((drop["area_name"] or ""))
                    city = (escape_markdown_v1((drop["city_name"])) + ', ') if drop["city_name"] else ''
                    status = "" if not drop["status"] or drop["status"] == "paid" else drop["status"].title()
                    status = "🤡 Redrop" if status == "Angry_Redrop" else status
                    is_lost = "" if not drop["lost"] else "(Lost)"                    
                    formatted_date = drop["updated_at"].strftime("%Y-%m-%d")
                    formatted_amount = str(round(drop['batch_amount'], 2)).rstrip('0').rstrip('.')

                    rows.append(
                        f"{drop['drop_id']:<5} {drop['product_emoji']:<6} {formatted_amount:<4} "
                        f"{(city + area)[:15]:<15} {formatted_date:<10} {status}{is_lost}\n"
                    )

                # Estimate split point
                part1_rows = []
                part2_rows = []
                current_length = len(user_info + table_header)
                for row in rows:
                    if (
                        current_length + len(row) + len(table_footer + summary)
                        < max_length
                    ):
                        part1_rows.append(row)
                        current_length += len(row)
                    else:
                        part2_rows.append(row)

                if part1_rows:
                    part1 = (
                        user_info
                        + table_header
                        + "".join(part1_rows)
                        + table_footer
                        + summary
                    )
                    await bot.send_message(group_id, f"Part 1/2\n{part1}", parse_mode="Markdown")
                if part2_rows:
                    part2 = table_header + "".join(part2_rows) + table_footer + summary
                    await bot.send_message(group_id, f"Part 2/2\n{part2}", parse_mode="Markdown")

    except Exception as e:
        await bot.send_message(group_id, "An error occurred while retrieving user data.")
        logger.error(f"Error processing /ask for {user_id}: {e}")

async def is_message_deleted(bot: Bot, chat_id: int, message_id: int) -> bool:
    try:
        # Try to copy the message to self to see if it was deleted (only workaround i could find..)
        await bot.copy_message(
            chat_id=1234567890,  # Dummy chat ID
            from_chat_id=chat_id,
            message_id=message_id
        )
        return False  # Message exists
    except Exception as e:
        # This could be due to message not found, deleted, or other issues
        error_text = str(e).lower()
        if (
            "message to copy not found" in error_text
            or "message_id_invalid" in error_text
            or "message identifier is not valid" in error_text
        ):
            return True  # Message was deleted or doesn't exist
        elif "chat not found" in error_text:
            return False  # Error about chat_id which means message_id hasnt been deleted
        else:
            logger.error(f"Error in is_message_deleted: {e}")
            return False
        
async def forward_ticket_to_admin(db: DatabaseController, bot: Bot, user, ticket, lang): # DO NOT edit these params
    try:
        # Initialize Telethon client
        client = await get_random_available_session(db)

        # Start Telethon client if not already started
        if not client:
            logger.error("Failed to forward ticket to admin - No suitable session found (all are either unauthorized, failed, or hit group limit).")
            bot_settings = await db.get_bot_settings()
            raw_username = bot_settings.get('support_username', '')
            support_username = raw_username if raw_username.startswith('@') else '@' + raw_username
            await bot.send_message(
                chat_id=support_username,
                text=f"ERROR: Failed to forward ticket to admin - No suitable session found (all are either unauthorized, failed, or hit group limit).\n{e}"
            )
            return
        
        if not client.is_connected():
            await client.start()

        # Check if a private group exists for this user
        user_group_id = None
        user_id = user.get('user_id')
        user_group_id = await db.get_user_group_id(user_id)

        if not user_group_id:
            user_group_id = await create_user_group(db, client, bot, user)

        if user_group_id:
            await db.set_messages_forwarded_for_ticket(ticket.get('ticket_id'))
            ticket = await db.get_ticket(ticket.get('ticket_id'))
            # Call a /ask at the start of ticket
            await ask(db, bot, user_id, user_group_id)

            # Forward all user sent messages to the target group
            messages = ticket.get("messages", [])
            messages = sorted(messages, key=lambda msg: msg.get("created_at"))

            await bot.send_message(
                user_group_id,
                f"<b>Ticket topic:</b> '{ticket.get("support_issue", "Unknown")}'\n\nNOTE: You can't edit or delete the messages you send to user",
                parse_mode="HTML",
                reply_markup=close_ticket(ticket.get("ticket_id"))
            )

            for msg in messages: 
                msg_id = msg.get("message_id")
                is_deleted = msg.get("is_deleted")
                if not is_deleted:
                    try:
                        await bot.forward_message(
                            chat_id=user_group_id,
                            from_chat_id=user_id,
                            message_id=msg_id,
                        )
                    except Exception as e:
                        logger.error(f"Failed to forward message {msg_id} from user {user_id}: {e}")
                else:
                    await bot.send_message(
                        chat_id=user_group_id,
                        text=f"(DELETED MESSAGE)\n{msg.get("user_text")}"
                    )
        else:
            logger.error("Error sending messages")
        
        logger.info(
            f"Forwarded message from user {user_id} to group {user_group_id}"
        )
    except Exception as e:
        logger.error(f"Error making the group or forwarding the messages to group: {e}")
        await bot.send_message(
            chat_id=user_group_id,
            text=f"ERROR FORWARDING USER TICKET TO THIS GROUP:\n{e}"
        )
    finally:
        # Ensure Telethon client is disconnected to avoid session issues
        if client.is_connected():
            await client.disconnect()
        