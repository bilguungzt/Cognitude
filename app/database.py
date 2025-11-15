import logging
from datetime import datetime

from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

_SQLITE_FALLBACK_URL = "sqlite:///./test.db"


def _create_engine():
    db_url = settings.DATABASE_URL
    if not db_url:
        logger.warning(
            "DATABASE_URL not set. Falling back to %s for local/test usage.",
            _SQLITE_FALLBACK_URL,
        )
        return create_engine(
            _SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False},
        )

    try:
        return create_engine(str(db_url))
    except Exception as exc:
        logger.error("Failed to initialize engine for %s: %s", db_url, exc)
        logger.warning(
            "Falling back to lightweight SQLite database at %s. "
            "Set DATABASE_URL to a production-ready database for persistent storage.",
            _SQLITE_FALLBACK_URL,
        )
        return create_engine(
            _SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False},
        )


engine = _create_engine()

# Provide compatibility helpers when using SQLite for local development/testing.
if str(engine.url).startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, connection_record):
        """
        SQLite does not provide the `now()` SQL function that our models use
        for server_default timestamps. Register a compatible function so
        migrations and inserts continue to work when using the lightweight
        SQLite fallback.
        """
        try:
            dbapi_connection.create_function("now", 0, lambda: datetime.utcnow().isoformat())
        except Exception:
            # Best-effort registration; ignore if function already exists or cannot be created.
            pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_migrations() -> None:
	"""Perform lightweight schema migrations for deployments without Alembic."""
	with engine.begin() as connection:
		inspector = inspect(connection)

		if "models" in inspector.get_table_names():
			model_columns = {column["name"] for column in inspector.get_columns("models")}

			if "version" not in model_columns:
				connection.execute(
					text(
						"ALTER TABLE models ADD COLUMN version VARCHAR NOT NULL DEFAULT '1.0.0'"
					)
				)
				connection.execute(text("ALTER TABLE models ALTER COLUMN version DROP DEFAULT"))

			if "description" not in model_columns:
				connection.execute(text("ALTER TABLE models ADD COLUMN description TEXT"))

			if "created_at" not in model_columns:
				connection.execute(
					text(
						"ALTER TABLE models ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
					)
				)

			if "updated_at" not in model_columns:
				connection.execute(
					text(
						"ALTER TABLE models ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
					)
				)

				connection.execute(
					text(
						"CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$\n"
						"BEGIN\n"
						"    NEW.updated_at = NOW();\n"
						"    RETURN NEW;\n"
						"END;\n"
						"$$ LANGUAGE plpgsql;"
					)
				)

				connection.execute(text("DROP TRIGGER IF EXISTS models_set_updated_at ON models"))
				connection.execute(
					text(
						"CREATE TRIGGER models_set_updated_at BEFORE UPDATE ON models\n"
						"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
					)
				)

		if "model_features" in inspector.get_table_names():
			feature_columns = {
				column["name"] for column in inspector.get_columns("model_features")
			}

			if "order" not in feature_columns:
				connection.execute(text('ALTER TABLE model_features ADD COLUMN "order" INTEGER'))

			if "baseline_stats" not in feature_columns:
				connection.execute(text("ALTER TABLE model_features ADD COLUMN baseline_stats JSONB"))

		if "predictions" in inspector.get_table_names():
			prediction_columns = {
				column["name"] for column in inspector.get_columns("predictions")
			}

			if "status" in prediction_columns:
				connection.execute(text("ALTER TABLE predictions DROP COLUMN status"))


			if "created_at" in prediction_columns:
				connection.execute(text("ALTER TABLE predictions DROP COLUMN created_at"))

			if "updated_at" in prediction_columns:
				connection.execute(text("DROP TRIGGER IF EXISTS predictions_set_updated_at ON predictions"))
				connection.execute(text("ALTER TABLE predictions DROP COLUMN updated_at"))

			if "actual_value" not in prediction_columns:
				connection.execute(text("ALTER TABLE predictions ADD COLUMN actual_value DOUBLE PRECISION"))

			if "latency_ms" not in prediction_columns:
				connection.execute(text("ALTER TABLE predictions ADD COLUMN latency_ms DOUBLE PRECISION"))

			if "time" not in prediction_columns:
				connection.execute(
					text(
						"ALTER TABLE predictions ADD COLUMN time TIMESTAMPTZ NOT NULL DEFAULT NOW()"
					)
				)
				connection.execute(text("ALTER TABLE predictions ALTER COLUMN time DROP DEFAULT"))

			if "features" not in prediction_columns:
				connection.execute(text("ALTER TABLE predictions ADD COLUMN features JSONB"))

		# Migrate drift_alerts table
		if "drift_alerts" in inspector.get_table_names():
			alert_columns = {column["name"] for column in inspector.get_columns("drift_alerts")}
			
			if "detected_at" not in alert_columns:
				connection.execute(
					text(
						"ALTER TABLE drift_alerts ADD COLUMN detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
					)
				)
				connection.execute(text("ALTER TABLE drift_alerts ALTER COLUMN detected_at DROP DEFAULT"))
			
			if "acknowledged_at" not in alert_columns:
				connection.execute(text("ALTER TABLE drift_alerts ADD COLUMN acknowledged_at TIMESTAMPTZ"))

		# Migrate alert_channels table
		if "alert_channels" in inspector.get_table_names():
			channel_columns = {column["name"] for column in inspector.get_columns("alert_channels")}
			
			if "is_active" not in channel_columns:
				connection.execute(text("ALTER TABLE alert_channels ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
			
			if "created_at" not in channel_columns:
				connection.execute(
					text(
						"ALTER TABLE alert_channels ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
					)
				)

