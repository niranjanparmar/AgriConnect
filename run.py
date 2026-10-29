import os
from app import create_app

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
