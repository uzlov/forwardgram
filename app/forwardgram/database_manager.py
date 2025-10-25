"""
Database management for Forwardgram application.
Preserves all existing SQL queries and table structure.
"""

import mariadb
import logging
from typing import Dict, List, Optional, Any, Tuple
from .data_types import MessageQueue, GlobalConfig


class DatabaseManager:
    """Database operations manager with existing SQL queries preserved."""

    def __init__(self, db_config: Dict[str, Any], environment: str):
        self.db_config = db_config
        self.environment = environment
        self.table_name = f"queues_{environment}"
        self.connection: Optional[mariadb.Connection] = None

    def initialize_connection(self) -> None:
        """Initialize database connection - preserves original logic."""
        try:
            self.connection = mariadb.connect(
                user=self.db_config["user"],
                password=self.db_config["password"],
                host=self.db_config["host"],
                database=self.db_config["database"],
            )
            logging.info("Database connection initialized")
        except Exception as e:
            logging.error(f"Failed to initialize database connection: {e}")
            raise

    def close_connection(self) -> None:
        """Close database connection - preserves original logic."""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")

    def refresh_connection(self) -> None:
        """Refresh database connection - preserves original logic."""
        try:
            if self.connection:
                self.connection.ping()
            else:
                self.initialize_connection()
        except Exception as e:
            logging.error(f"Failed to refresh database connection: {e}")
            self.initialize_connection()

    def is_table_exist(self, table_name: str) -> bool:
        """Check if table exists - preserves original logic."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception as e:
            logging.error(f"Error checking table existence: {e}")
            return False

    def create_data_table(self) -> None:
        """Create data table - preserves original SQL exactly."""
        try:
            cursor = self.connection.cursor()
            # Exact same SQL as original
            command = f"""CREATE TABLE IF NOT EXISTS {self.table_name} (
                qid int(10) unsigned auto_increment,
                config_name varchar(16),
                channel_id varchar(32), 
                data longtext,
                primary key (qid)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"""

            cursor.execute(command)
            self.connection.commit()
            cursor.close()
            logging.info(f"Table {self.table_name} created or already exists")
        except Exception as e:
            logging.error(f"Error creating table: {e}")
            raise

    def load_queues(self) -> List[MessageQueue]:
        """Load all queues from database - preserves original logic."""
        try:
            cursor = self.connection.cursor()
            # Exact same SQL as original
            command = (
                f"SELECT qid, config_name, channel_id, data FROM {self.table_name}"
            )
            cursor.execute(command)

            queues = []
            for row in cursor.fetchall():
                qid, config_name, channel_id, data_json = row
                queue = MessageQueue.from_db_row(
                    qid, config_name, channel_id, data_json
                )
                queues.append(queue)

            cursor.close()
            return queues
        except Exception as e:
            logging.error(f"Error loading queues: {e}")
            return []

    def _execute_select(self, command: str, values: Tuple = ()) -> List[Tuple]:
        """Execute select query - preserves original logic."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(command, values)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Error executing select: {e}")
            return []

    def _execute_commit(self, command: str, values: Tuple) -> int:
        """Execute commit query - preserves original logic."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(command, values)
            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except Exception as e:
            logging.error(f"Error executing commit: {e}")
            return 0

    def create_queue(self, queue: MessageQueue) -> int:
        """Create new queue - preserves original SQL exactly."""
        try:
            # Exact same SQL as original
            command = f"INSERT INTO {self.table_name} (config_name, channel_id, data) VALUES (%s, %s, %s)"
            values = (queue.config_name, queue.channel_id, queue.to_db_data())
            queue_id = self._execute_commit(command, values)

            # Update the queue object with the new ID
            queue.qid = queue_id
            return queue_id
        except Exception as e:
            logging.error(f"Error creating queue: {e}")
            return 0

    def update_queue(self, queue: MessageQueue) -> None:
        """Update existing queue - preserves original SQL exactly."""
        try:
            # Exact same SQL as original
            command = f"UPDATE {self.table_name} SET data = %s WHERE qid = %s"
            values = (queue.to_db_data(), queue.qid)
            self._execute_commit(command, values)
        except Exception as e:
            logging.error(f"Error updating queue: {e}")

    def delete_queue(self, queue: MessageQueue) -> None:
        """Delete queue - preserves original SQL exactly."""
        try:
            # Exact same SQL as original
            command = f"DELETE FROM {self.table_name} WHERE qid = %s"
            values = (queue.qid,)
            self._execute_commit(command, values)
        except Exception as e:
            logging.error(f"Error deleting queue: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.initialize_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connection()
