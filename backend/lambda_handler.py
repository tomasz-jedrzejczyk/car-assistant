from mangum import Mangum
from main import app

# This is the entry point for AWS Lambda
# Mangum wraps FastAPI so it works with API Gateway
handler = Mangum(app, lifespan="off")