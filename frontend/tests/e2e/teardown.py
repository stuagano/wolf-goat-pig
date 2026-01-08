import os
import sys

# Add the backend directory to the Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
)

from app.database import engine, Base


def main():
    print("--- Starting test database teardown (Python) ---")

    # Drop all tables (synchronous engine)
    print("Dropping all tables...")
    with engine.begin() as conn:
        Base.metadata.drop_all(bind=conn)
    print("All tables dropped.")

    print("--- Test database teardown complete (Python) ---")


if __name__ == "__main__":
    main()
