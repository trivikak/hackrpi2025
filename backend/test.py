import psycopg2
import os
import random
from dotenv import load_dotenv

load_dotenv()

def check_courses(sample_size=5):
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        database=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        port=os.getenv("PGPORT")
    )
    cur = conn.cursor()

    # Get total number of courses
    cur.execute("SELECT COUNT(*) FROM Courses;")
    total = cur.fetchone()[0]

    print(f"Total courses in database: {total}")

    # Pick random offsets to fetch random courses
    offsets = random.sample(range(total), min(sample_size, total))

    print(f"\nSample of {len(offsets)} courses:")

    for offset in offsets:
        cur.execute("""
            SELECT course_id, name, credits, semesters_offered
            FROM Courses
            OFFSET %s LIMIT 1;
        """, (offset,))
        course = cur.fetchone()
        print(course)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_courses()
