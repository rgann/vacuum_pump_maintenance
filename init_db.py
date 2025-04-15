import os
from setup import setup_database

if __name__ == "__main__":
    print("Initializing database with sample data...")

    # Check if running on Render.com
    is_on_render = os.environ.get('RENDER') == 'true'
    if is_on_render:
        print("Running on Render.com environment")
        # Ensure the data directory exists in the project folder
        import os.path
        render_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(render_data_dir, exist_ok=True)
        print(f"Using data directory: {render_data_dir}")

    setup_database()
    print("Done!")
