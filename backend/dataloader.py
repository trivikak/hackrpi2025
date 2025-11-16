import json
import psycopg2
import os
from dotenv import load_dotenv

# Load PostgreSQL credentials
load_dotenv()

def load_courses(normalized_path="normalized_courses.json"):
    print("📘 Loading normalized course file...")
    with open(normalized_path, "r", encoding="utf-8") as f:
        courses = json.load(f)

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        database=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        port=os.getenv("PGPORT")
    )
    cur = conn.cursor()

    # Insert each course into the Courses table
    print(f"📥 Inserting {len(courses)} courses into the database...")

    for c in courses:
        # Use semesters_offered directly from JSON
        semesters = c.get("semesters_offered", [])

        # Use course_id (matches your normalized JSON)
        cur.execute(
            """
            INSERT INTO Courses (course_id, name, credits, semesters_offered, prerequisites)
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
            ON CONFLICT (course_id) DO UPDATE SET
                name = EXCLUDED.name,
                credits = EXCLUDED.credits,
                semesters_offered = EXCLUDED.semesters_offered,
                prerequisites = EXCLUDED.prerequisites;
            """,
            (
                c["course_id"],
                c["name"],
                c["credits"],
                json.dumps(semesters),
                json.dumps(c.get("prerequisites", [])),
            )
        )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Finished inserting course data!")


if __name__ == "__main__":
    load_courses()
