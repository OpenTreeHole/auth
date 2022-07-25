from fastapi import APIRouter

router = APIRouter(tags=['oauth2'])

# import here or the route couldn't be registered
import oauth2.resource
