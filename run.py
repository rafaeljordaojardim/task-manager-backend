from app import get_app_with_config, config
from app import app
app, mongo, limiter = get_app_with_config(config.RunConfig)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')