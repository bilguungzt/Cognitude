import dotenv
dotenv.load_dotenv()

# Override with .env.local for local development
dotenv.load_dotenv(dotenv_path='.env.local', override=True)

import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) # type: ignore

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
