import pandas as pd
from datetime import timezone
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from app.core.database import SessionLocal, engine, Base
from app.db.models import Earthquake

def seed_database(csv_path: str = "emsc_catalog_egypt.csv"):
    print("1. Creating database tables if they do not exist...")
    # This ensures the 'earthquakes' table is created using your declarative Base
    Base.metadata.create_all(bind=engine)

    print(f"2. Loading {csv_path} with Pandas...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: {csv_path} not found. Ensure it is in the root directory.")
        return

    # Enforce UTC timezone awareness for the 'time' column
    df['time'] = pd.to_datetime(df['time'], utc=True, format = "mixed")

    print(f"   Loaded {len(df)} records. Preparing to insert...")

    # Convert the DataFrame to a list of dictionaries for bulk insertion
    # We rename columns to exactly match your SQLAlchemy Earthquake model attributes
    records_to_insert = []
    for _, row in df.iterrows():
        records_to_insert.append({
            "time": row['time'].to_pydatetime(),
            "magnitude": float(row['mag']),
            "latitude": float(row['lat']),
            "longitude": float(row['lon']),
            "depth": float(row['depth']),
            "place": row['place'] if pd.notna(row['place']) else 'Gulf of Suez'
        })

    print("3. Connecting to the database...")
    db: Session = SessionLocal()

    try:
        # We use SQLAlchemy's bulk insert mechanism
        # Using dialect-specific upsert (SQLite in this case) to gracefully ignore duplicates
        # based on the unique constraint we defined in models.py

        inserted_count = 0
        skipped_count = 0

        for record in records_to_insert:
            # Building the SQLite UPSERT statement: DO NOTHING if duplicate
            stmt = sqlite_upsert(Earthquake).values(record)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['time', 'latitude', 'longitude']
            )

            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted_count += 1
            else:
                skipped_count += 1

        db.commit()
        print(f"4. Seeding Complete!")
        print(f"   -> Successfully inserted: {inserted_count}")
        print(f"   -> Skipped (duplicates): {skipped_count}")

    except Exception as e:
        db.rollback()
        print(f"   Database insertion failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
