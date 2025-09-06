from aiogram import Bot
from telethon import TelegramClient
from telethon.tl.functions.messages import CreateChatRequest, EditChatAboutRequest, EditChatPhotoRequest, EditChatAdminRequest
from telethon.tl.types import InputChatUploadedPhoto
from utils.logger import logger
from controllers.db_controller import DatabaseController
from config.config import Config
from utils.helpers import escape_markdown_v1, get_random_available_session
from keyboards.inline import close_ticket
import os

async def forward_ticket_to_admin(db: DatabaseController, bot: Bot, user, ticket, lang):
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
