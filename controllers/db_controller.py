# db_controller.py
import asyncpg
from aiogram import Bot
from asyncpg.exceptions import PostgresError
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple

from config.config import Config
from utils.logger import logger


class DatabaseController:
    def __init__(self, bot: Bot):
        self.pool = None
        self.config = {
            "host": Config.DB_HOST,
            "port": Config.DB_PORT,
            "user": Config.DB_USER,
            "password": Config.DB_PASS,
            "database": Config.DB_NAME,
            "min_size": Config.DB_POOL_SIZE,
            "max_size": int(Config.DB_MAX_OVERFLOW) + int(Config.DB_POOL_SIZE),
        }
        self.bot = bot
        self._validate_config()  # Validate config during initialization

    def _validate_config(self):
        """
        Validate configuration values to ensure correct types.
        """
        logger.debug("Validating database configuration...")
        if not isinstance(self.config["port"], int):
            raise ValueError(
                f"DB_PORT must be an integer, got {type(self.config['port'])}: {self.config['port']}"
            )
        if not isinstance(self.config["min_size"], int):
            raise ValueError(
                f"DB_POOL_SIZE must be an integer, got {type(self.config['min_size'])}: {self.config['min_size']}"
            )
        if not isinstance(self.config["max_size"], int):
            raise ValueError(
                f"DB_MAX_OVERFLOW + DB_POOL_SIZE must be an integer, got {type(self.config['max_size'])}: {self.config['max_size']}"
            )
        logger.debug("Database configuration validated successfully.")

    async def initialize(self):
        """
        Initialize the connection pool.
        """
        if self.pool is None:
            try:
                logger.info("Initializing database connection pool...")
                self.pool = await asyncpg.create_pool(**self.config)
                logger.info("Database connection pool initialized successfully.")
            except PostgresError as e:
                logger.error(f"Failed to initialize database connection pool: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during pool initialization: {e}")
                raise
        return self

    async def close(self):
        """
        Close the connection pool.
        """
        if self.pool:
            try:
                logger.info("Closing database connection pool...")
                await self.pool.close()
                logger.info("Database connection pool closed successfully.")
            except PostgresError as e:
                logger.error(f"Failed to close database connection pool: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during pool closure: {e}")
                raise
            finally:
                self.pool = None

    async def is_role(self, user_id: int, required_role: str) -> bool:
        """
        Checks if a user has the ROLE_ADMIN role in the multi-role system.

        Args:
            user_id: Telegram user ID to check.

        Returns:
            bool: True if the user has the ROLE_ADMIN role, False otherwise.

        Raises:
            PostgresError: If a database error occurs.
            Exception: For unexpected errors.
        """
        try:
            roles = await self.get_user_roles(user_id)
            is_role = required_role in roles
            logger.debug(
                f"Checked {required_role} status for user {user_id}: {is_role}"
            )
            return is_role
        except PostgresError as e:
            logger.error(
                f"Database error checking {required_role} status for user {user_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error checking {required_role} status for user {user_id}: {e}"
            )
            raise
    
    async def is_muted(self, user_id: int) -> bool:
        """
        Checks if a user is currently muted.
        Automatically unmutes the user if the mute has expired.

        Args:
            user_id: Telegram user ID to check.

        Returns:
            bool: True if the user is currently muted, False otherwise.

        Raises:
            PostgresError: If a database error occurs.
            Exception: For unexpected errors.
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT muted_until
                    FROM support_user_muted
                    WHERE user_id = $1
                """
                row = await conn.fetchrow(query, user_id)
                if row is None:
                    logger.debug(f"User {user_id} is not muted (no record found).")
                    return False

                muted_until = row["muted_until"]
                now = datetime.now(timezone.utc)

                if muted_until < now:
                    # Mute expired - remove the record
                    delete_query = """
                        DELETE FROM support_user_muted
                        WHERE user_id = $1
                    """
                    await conn.execute(delete_query, user_id)
                    logger.debug(f"Mute expired for user {user_id}; unmuted automatically.")
                    return False

                logger.debug(f"User {user_id} is currently muted until {muted_until}.")
                return True

        except PostgresError as e:
            logger.error(f"Database error checking mute status for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking mute status for user {user_id}: {e}")
            raise

    async def mute_user(self, user_id: int, until: datetime = None) -> None:
        """
        Mutes a user until a specified time, defaulting to 24 hours from now.

        If the user is already muted, updates the mute expiration time.

        Args:
            user_id: Telegram user ID to mute.
            until: A timezone-aware datetime indicating when the mute expires.
                   Defaults to 24 hours from now in UTC.

        Raises:
            ValueError: If 'until' is not timezone-aware.
            PostgresError: If a database error occurs.
            Exception: For unexpected errors.
        """
        if until is None:
            until = datetime.now(timezone.utc) + timedelta(days=1)

        if until.tzinfo is None or until.tzinfo.utcoffset(until) is None:
            raise ValueError("The 'until' datetime must be timezone-aware (e.g., UTC).")

        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO support_user_muted (user_id, muted_until)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id)
                    DO UPDATE SET muted_until = EXCLUDED.muted_until
                """
                await conn.execute(query, user_id, until)
                logger.debug(f"Muted user {user_id} until {until.isoformat()}.")
        except PostgresError as e:
            logger.error(f"Database error muting user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error muting user {user_id}: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int = None, username: str = None) -> dict:
        """Retrieve a user by their ID or username from the database.

        Args:
            user_id (int, optional): The ID of the user to retrieve. Defaults to None.
            username (str, optional): The username of the user to retrieve. Defaults to None.

        Returns:
            dict: A dictionary containing the user data if found, otherwise None.

        Raises:
            PostgresError: If a database error occurs during the query.
            Exception: If an unexpected error occurs during the retrieval process.
        """
        if not user_id and not username:
            logger.error("No user_id or username provided for user retrieval")
            return None

        async with self.pool.acquire() as conn:
            try:
                if username:
                    user = await conn.fetchrow(
                        "SELECT * FROM users WHERE username = $1", username
                    )
                else:
                    user = await conn.fetchrow(
                        "SELECT * FROM users WHERE user_id = $1", user_id
                    )
                return dict(user) if user else None  # Convert to dictionary

            except PostgresError as e:
                logger.error(f"Database error retrieving user by {'username' if username else 'id'} {username or user_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error retrieving user by {'username' if username else 'id'} {username or user_id}: {e}")
                raise

    async def get_user_roles(self, user_id: int) -> bool:
        """
        Retrieve all roles assigned to a user.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            list of str: A list of role names assigned to the user.

        Raises:
            PostgresError: If a database error occurs during the query.
            Exception: For any other unexpected errors.
        """
        async with self.pool.acquire() as conn:
            try:
                roles = await conn.fetch(
                    """
                    SELECT r.role_name
                    FROM roles r
                    JOIN user_roles ur ON r.role_id = ur.role_id
                    WHERE ur.user_id = $1
                    """,
                    user_id,
                )
                role_names = [row["role_name"] for row in roles]
                logger.debug(f"Retrieved roles for user {user_id}: {role_names}")
                return role_names
            except PostgresError as e:
                logger.error(f"Database error fetching roles for user {user_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching roles for user {user_id}: {e}")
                raise

    async def get_drop_by_id(self, drop_id: int) -> dict:
        """
        Asynchronously retrieves detailed information about a drop by its ID.

        This includes core drop data, associated media paths, English description,
        batch ID, and area ID, joined with the related product and batch information.

        Parameters:
            drop_id (int): The ID of the drop to retrieve.

        Returns:
            dict: A dictionary containing drop details, media paths, description,
                batch ID, and area ID. Returns None if no matching drop is found.

        Raises:
            PostgresError: If a database error occurs during retrieval.
            Exception: For any other unexpected errors.
        """

        async with self.pool.acquire() as conn:
            try:
                # Fetch the oldest ready drop with price from product_batches
                drop_query = """
                    SELECT d.*,
                        c.city as city_name, c.country_emoji,
                        pc.cycle_name,
                        u.user_id, u.first_name
                    FROM drops d
                    JOIN product_batches pb ON pb.batch_id = d.batch_id
                    JOIN products p ON p.product_id = pb.product_id
                    JOIN cities c ON d.city_id = c.city_id
                    JOIN product_cycles pc ON d.cycle_id = pc.cycle_id
                    JOIN users u ON u.user_id = d.user_id
                    WHERE d.drop_id = $1
                    ORDER BY d.created_at ASC
                    LIMIT 1
                """
                drop_row = await conn.fetchrow(drop_query, drop_id)

                if not drop_row:
                    logger.debug(f"No ready drop found for {drop_id}")
                    return None

                # Fetch media paths from drop_medias
                media_query = """
                    SELECT media_path
                    FROM drop_medias
                    WHERE drop_id = $1
                """
                media_rows = await conn.fetch(media_query, drop_id)
                media_paths = [row["media_path"] for row in media_rows]

                # Fetch English description from drop_descriptions
                desc_query = """
                    SELECT description_en as description
                    FROM drop_descriptions
                    WHERE drop_id = $1
                """
                desc_row = await conn.fetchrow(desc_query, drop_id)
                description = desc_row["description"] if desc_row else None

                # Combine all information into a single dictionary
                drop_info = dict(drop_row)
                drop_info["media_paths"] = media_paths
                drop_info["description"] = description

                logger.debug(
                    f"Fetched drop: drop_id={drop_id}, media_paths={media_paths}, "
                    f"description={description}, batch_id={drop_info.get('batch_id')}, "
                    f"area_id={drop_info.get('area_id')}"
                )
                return drop_info

            except PostgresError as e:
                logger.error(f"Database error retrieving drop by id {drop_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error retrieving drop by id {drop_id}: {e}")
                raise

    async def get_order_count_for_user(self, user_id: int):
        """Retrieve the count of orders for a user.

        Args:
            user_id (int): The ID of the user whose orders are to be counted.

        Returns:
            int: The number of orders, or 0 if none are found.

        Raises:
            PostgresError: If a database error occurs during the query.
            Exception: If an unexpected error occurs during the retrieval process.
        """
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT COUNT(*)
                    FROM orders
                    WHERE user_id = $1
                """
                # Use fetch() to get all rows instead of execute()
                orders = await conn.fetchval(query, user_id)
                # Extract user_id from each row and return as a list
                return orders or 0

            except PostgresError as e:
                logger.error(f"Failed to get orders for user: {e}")
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error getting orders for user: {e}"
                )
                raise  

    async def get_orders_for_user(self, user_id: int):
        """
        Retrieve all orders for a user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[Record]: A list of orders for the user.
        """
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT *
                    FROM orders
                    WHERE user_id = $1
                """
                orders = await conn.fetch(query, user_id)
                return [dict(order) for order in orders]

            except PostgresError as e:
                logger.error(f"Failed to get orders for user: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting orders for user: {e}")
                raise

    
    async def get_bot_settings(self):
        """Retrieve all bot settings from the bot_settings table.

        Args:
            None

        Returns:
            asyncpg.Record: The bot settings as a record, or None if not found.

        Raises:
            PostgresError: If a database error occurs during the query.
            Exception: If an unexpected error occurs during the retrieval process.
        """
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchrow("SELECT * FROM bot_settings")
                logger.debug(f"Retrieved bot_settings: {result}")
                return result

            except PostgresError as e:
                logger.error(f"Database error checking meintenance status: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error checking meintenance status: {e}")
                raise
    
    async def get_user_and_drops(
        self, client_id=None, username=None, drop_statuses=None, order_by=None
    ):
        """Retrieve user information and their drops based on user ID or username.

        Args:
            user_id (int, optional): The ID of the user to retrieve.
            username (str, optional): The username of the user to retrieve.
            drop_statuses (list, optional): List of drop statuses to filter by.
            order_by (str, optional): Column to order the results by (defaults to 'updated_at ASC').

        Returns:
            dict: A dictionary with user data and a list of their drops including city names, or None if user not found.

        Raises:
            PostgresError: If a database error occurs during the query.
            Exception: If an unexpected error occurs during the retrieval process.
        """
        async with self.pool.acquire() as conn:
            try:
                if not any([client_id, username]):
                    logger.error("No user_id or username provided")
                    return None

                # Build user query
                user_query = """
                    SELECT user_id, username, first_name, last_name, created_at, updated_at, captcha_passed
                    FROM users
                    WHERE
                """
                params = []
                if client_id:
                    user_query += "user_id = $1"
                    params.append(client_id)
                elif username:
                    user_query += "LOWER(username) = LOWER($1)"
                    params.append(username)

                logger.debug("Retrieving user data")
                user = await conn.fetchrow(user_query, *params)
                if not user:
                    logger.debug("User not found")
                    return None

                # Convert user record to dict
                user_dict = dict(user)

                # Fetch drops
                drops_query = """
                    SELECT d.drop_id, d.client_id, d.status, d.area_name, d.batch_amount, d.created_at, d.updated_at, d.lost, c.city as city_name, r.reason, p.emoji as product_emoji
                    FROM drops d
                    JOIN products p ON p.name = d.product_name
                    LEFT JOIN cities c ON d.city_id = c.city_id
                    LEFT JOIN redrop_reason r ON d.drop_id = r.drop_id
                    WHERE d.client_id = $1 AND d.status = ANY($2)
                    ORDER BY {}
                """.format(order_by or "updated_at ASC")
                logger.debug("Retrieving user drops")
                drops = await conn.fetch(
                    drops_query, user_dict["user_id"], drop_statuses
                )

                # Convert drops to list of dicts
                drops_list = [dict(drop) for drop in drops]

                return {"user": user_dict, "drops": drops_list}

            except PostgresError as e:
                logger.error(f"Failed to retrieve user and drops: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error retrieving user and drops: {e}")
                raise
    
    async def save_user_message(self, user_id: int, message_id: int, user_text: str, replied: bool = False) -> bool:
        """
        Log a support message sent by a user into the support_messages table,
        creating a support ticket if necessary.

        Args:
            user_id (int): Telegram user ID of the sender.
            message_id (int): Telegram message ID.
            user_text (str): Text content of the message.
            replied (bool, optional): Whether the message has already been replied to. Defaults to False.

        Returns:
            bool: True if message was logged successfully, False otherwise.

        Raises:
            PostgresError: If a database-related error occurs.
            Exception: For unexpected runtime errors.
        """
        async with self.pool.acquire() as conn:
            try:
                async with conn.transaction():
                    logger.debug(f"Checking for open ticket for user {user_id}")

                    # Step 1: Check for open ticket
                    select_ticket_query = """
                        SELECT ticket_id FROM support_tickets
                        WHERE user_id = $1 AND closed = FALSE
                        LIMIT 1
                    """
                    row = await conn.fetchrow(select_ticket_query, user_id)

                    if row:
                        ticket_id = row["ticket_id"]
                        logger.debug(f"Found open ticket {ticket_id} for user {user_id}")
                    else:
                        # Step 2: Create new ticket
                        insert_ticket_query = """
                            INSERT INTO support_tickets (user_id)
                            VALUES ($1)
                            RETURNING ticket_id
                        """
                        ticket_row = await conn.fetchrow(insert_ticket_query, user_id)
                        ticket_id = ticket_row["ticket_id"]
                        logger.debug(f"Created new ticket {ticket_id} for user {user_id}")

                    # Step 3: Insert support message
                    insert_message_query = """
                        INSERT INTO support_messages (ticket_id, user_id, message_id, user_text, replied)
                        VALUES ($1, $2, $3, $4, $5)
                    """
                    await conn.execute(insert_message_query, ticket_id, user_id, message_id, user_text, replied)
                    logger.debug(f"Logged message for ticket {ticket_id} from user {user_id}")

                    return True

            except PostgresError as e:
                logger.error(f"Database error while logging message from user {user_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error while logging message from user {user_id}: {e}")
                raise

    async def get_active_support_tickets(
        self,
        messages_forwarded: bool | None = None,
        user_id: int | None = None
    ) -> list[dict]:
        """
        Retrieve all unclosed support tickets with multiple messages, 
        optionally filtering by forwarding status and user.

        Args:
            messages_forwarded (bool | None, optional): 
                - If True, only return tickets forwarded to admin.
                - If False, only return tickets NOT forwarded.
                - If None, don't filter by this field.
            user_id (int | None, optional): If provided, only return tickets for this user.

        Returns:
            list[dict]: A list of tickets with multiple messages (as dictionaries).
        """
        try:
            async with self.pool.acquire() as conn:
                conditions = []
                values = []

                param_index = 1  # For dynamic $n indexing in SQL

                # Always filter for open (unclosed) tickets
                conditions.append("t.closed = FALSE")

                # Filter by messages_forwarded if explicitly set
                if messages_forwarded is not None:
                    conditions.append(f"t.messages_forwarded = ${param_index}")
                    values.append(messages_forwarded)
                    param_index += 1

                # Filter by user_id if provided
                if user_id is not None:
                    conditions.append(f"t.user_id = ${param_index}")
                    values.append(user_id)
                    param_index += 1

                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                query = f"""
                    SELECT 
                        t.*,
                        array_agg(m.*) AS messages
                    FROM support_tickets t
                    LEFT JOIN support_messages m ON t.ticket_id = m.ticket_id
                    {where_clause}
                    GROUP BY t.ticket_id
                """

                rows = await conn.fetch(query, *values)
                return [dict(row) for row in rows]

        except PostgresError as e:
            logger.error(f"Database error retrieving support tickets: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving support tickets: {e}")
            raise

        
    async def close_support_ticket(self, ticket_id: int) -> bool:
        """Mark a support ticket as closed.

        Args:
            ticket_id (int): The ID of the support ticket to close.

        Returns:
            bool: True if the ticket was successfully updated, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE support_tickets
                    SET closed = TRUE
                    WHERE ticket_id = $1
                    """,
                    ticket_id
                )

                # Check if any rows were affected
                return result.endswith("UPDATE 1")

        except PostgresError as e:
            logger.error(f"Database error while closing support ticket {ticket_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while closing support ticket {ticket_id}: {e}")
            raise
    
    async def set_messages_forwarded_for_ticket(self, ticket_id: int) -> bool:
        """Mark a support ticket as forwarded.

        Args:
            ticket_id (int): The ID of the support ticket to mark as forwarded.

        Returns:
            bool: True if the ticket was successfully updated, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE support_tickets
                    SET messages_forwarded = TRUE
                    WHERE ticket_id = $1
                    """,
                    ticket_id
                )

                # Check if any rows were affected
                return result.endswith("UPDATE 1")

        except PostgresError as e:
            logger.error(f"Database error while forwarding support ticket {ticket_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while forwarding support ticket {ticket_id}: {e}")
            raise

    async def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """
        Retrieve a support ticket by its ID, including its messages.

        Args:
            ticket_id (int): The ID of the support ticket to retrieve.

        Returns:
            Optional[Dict]: A dictionary containing the ticket data if found, None otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT st.*,
                        array_agg(sm.*) AS messages
                    FROM support_tickets st
                    JOIN support_messages sm ON sm.ticket_id = st.ticket_id
                    WHERE st.ticket_id = $1
                    GROUP BY st.ticket_id
                    """,
                    ticket_id
                )

                if row:
                    return dict(row)
                return None

        except PostgresError as e:
            logger.error(f"Database error while retrieving support ticket {ticket_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while retrieving support ticket {ticket_id}: {e}")
            raise


    async def mark_messages_as_replied(self, ticket_id: int) -> bool:
        """Mark all messages for a given ticket as replied.

        Args:
            ticket_id (int): The ID of the ticket whose messages should be marked as replied.

        Returns:
            bool: True if one or more messages were updated, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE support_messages
                    SET replied = TRUE
                    WHERE ticket_id = $1
                    """,
                    ticket_id
                )

                return result.endswith("UPDATE 0") is False

        except PostgresError as e:
            logger.error(f"Database error marking messages as replied for ticket {ticket_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error marking messages as replied for ticket {ticket_id}: {e}")
            raise

    async def set_user_group_id(self, user_id: int, group_id: int, created_by: str) -> None:
        """
        Sets or updates the group ID and creator associated with a user.

        Args:
            user_id (int): Telegram user ID.
            group_id (int): Telegram group ID (must be a negative long integer).
            created_by (str): Session name or identifier that created the group.
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO support_group_ids (user_id, group_id, created_by)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id)
                    DO UPDATE SET group_id = EXCLUDED.group_id,
                                  created_by = EXCLUDED.created_by
                """
                await conn.execute(query, user_id, group_id, created_by)
                logger.debug(f"Set group_id {group_id} and created_by '{created_by}' for user_id {user_id}")
        except Exception as e:
            logger.error(f"Failed to set group_id for user_id {user_id}: {e}")
            raise

    async def get_user_group_id(self, user_id: int) -> int | None:
        """
        Retrieves the group ID associated with a user.

        Args:
            user_id (int): Telegram user ID.

        Returns:
            int | None: The associated group ID, or None if not set.
        """
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT group_id FROM support_group_ids WHERE user_id = $1"
                row = await conn.fetchrow(query, user_id)
                if row:
                    return row["group_id"]
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve group_id for user_id {user_id}: {e}")
            raise

    async def mark_message_as_deleted(self, id: int) -> bool:
        """Mark a support message as deleted.

        Args:
            id (int): The ID of the support message to mark as deleted.

        Returns:
            bool: True if the message was successfully updated, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE support_messages
                    SET is_deleted = TRUE
                    WHERE id = $1
                    """,
                    id
                )

                # Check if exactly one row was updated
                return result.endswith("UPDATE 1")

        except PostgresError as e:
            logger.error(f"Database error while marking message {id} as deleted: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while marking message {id} as deleted: {e}")
            raise
    
    async def get_message(self, user_id: int, message_id: int) -> dict | None:
        """
        Retrieve a specific support message by user_id and message_id, including related ticket info.

        Args:
            user_id (int): The ID of the user who sent the message.
            message_id (int): The Telegram message ID.

        Returns:
            dict | None: The message and ticket info as a dictionary, or None if not found.
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT sm.*, st.*
                    FROM support_messages sm
                    JOIN support_tickets st ON sm.ticket_id = st.ticket_id
                    WHERE sm.user_id = $1 AND sm.message_id = $2
                    """,
                    user_id,
                    message_id
                )

                return dict(row) if row else None

        except PostgresError as e:
            logger.error(f"Database error while retrieving message {message_id} from user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while retrieving message {message_id} from user {user_id}: {e}")
            raise

    
    async def update_edited_message(self, user_id: int, message_id: int, new_text: str) -> bool:
        """Update the text of an unreplied support message.

        Args:
            user_id (int): The ID of the user who sent the message.
            message_id (int): The Telegram message ID.
            new_text (str): The new text to update in the message.

        Returns:
            bool: True if the message was updated successfully, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE support_messages
                    SET user_text = $1
                    WHERE user_id = $2 AND message_id = $3 AND replied = FALSE
                    """,
                    new_text,
                    user_id,
                    message_id
                )

                return result.endswith("UPDATE 1")

        except PostgresError as e:
            logger.error(f"Database error while updating message {message_id} from user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while updating message {message_id} from user {user_id}: {e}")
            raise

    async def set_lang_and_category_for_ticket(self, category_key: str, lang: str, ticket_id: int) -> bool:
        """Set the support issue category and language for a support ticket.

        Args:
            category_key (str): The classification key to assign to the ticket.
            lang (str): The detected language code (e.g., lv, eng).
            ticket_id (int): The ID of the support ticket to update.

        Returns:
            bool: True if the ticket was successfully updated, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE support_tickets
                    SET support_issue = $1,
                        lang = $2
                    WHERE ticket_id = $3
                    """,
                    category_key,
                    lang,
                    ticket_id
                )

                return result.endswith("UPDATE 1")

        except PostgresError as e:
            logger.error(f"Database error while setting category/lang for ticket {ticket_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while setting category/lang for ticket {ticket_id}: {e}")
            raise


    async def get_previous_users_category_key(self, user_id: int) -> Optional[str]:
        """
        Retrieve the support_issue of the second latest ticket for a given user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Optional[str]: The support_issue of the second latest ticket, or None if not found.
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT support_issue
                    FROM support_tickets
                    WHERE user_id = $1
                    ORDER BY created_at DESC, ticket_id DESC
                    OFFSET 1
                    LIMIT 1
                    """,
                    user_id
                )

                if row:
                    return row["support_issue"]
                return None

        except PostgresError as e:
            logger.error(f"Database error while retrieving second latest ticket for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while retrieving second latest ticket for user {user_id}: {e}")
            raise

    async def count_of_groups_created_by(self, created_by: str) -> int:
            """
            Counts the number of rows in support_group_ids where created_by matches the given value.

            Args:
                created_by (str): The value to match in the created_by column.

            Returns:
                int: The number of matching rows.
            """
            try:
                async with self.pool.acquire() as conn:
                    query = """
                        SELECT COUNT(*) FROM support_group_ids
                        WHERE created_by = $1
                    """
                    count = await conn.fetchval(query, created_by)
                    logger.debug(f"Found {count} rows where created_by = '{created_by}'")
                    return count
            except Exception as e:
                logger.error(f"Error counting rows by created_by = '{created_by}': {e}")
                raise

    async def get_user_open_tickets(self, user_id: int) -> list:
        """
        Returns a list of open support tickets for a given user.
        """
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch("""
                    SELECT * FROM support_tickets
                    WHERE user_id = $1 AND closed = false
                """, user_id)
        except Exception as e:
            logger.error(f"Error fetching open tickets for user_id {user_id}: {e}")
            return []

    async def get_user_latest_ticket_date(self, user_id: int) -> Optional[datetime]:
        """
        Returns the latest created_at datetime for a user's tickets.
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT MAX(created_at) as latest FROM support_tickets
                    WHERE user_id = $1
                """, user_id)
                return result["latest"] if result and result["latest"] else None
        except Exception as e:
            logger.error(f"Error getting latest ticket date for user_id {user_id}: {e}")
            return None

    async def delete_support_group(self, user_id: int) -> None:
        """
        Deletes the support group entry for a given user_id.
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM support_group_ids
                    WHERE user_id = $1
                """, user_id)
                logger.info(f"Deleted support group for user_id {user_id}")
        except Exception as e:
            logger.error(f"Error deleting support group for user_id {user_id}: {e}")


    async def get_all_support_groups_with_creator(self) -> List[Tuple[int, int, Optional[str]]]:
        """
        Returns a list of (user_id, group_id, created_by) from support_group_ids.
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT user_id, group_id, created_by FROM support_group_ids
                """)
                return [(row['user_id'], row['group_id'], row['created_by']) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching support groups with creator: {e}")
            return []