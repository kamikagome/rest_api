import os

# JWT Secret Key
# In production, use a strong random value from environment variable
# For learning, we'll use a default (NEVER do this in production!)
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")

# Token expiration time in seconds (1 hour)
JWT_EXPIRATION = 3600
