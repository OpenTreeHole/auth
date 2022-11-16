from fastapi import APIRouter, Depends

from auth.response import TokensResponse, MessageResponse
from auth.serializers import LoginModel
from models import User
from utils.auth import make_identifier, check_password
from utils.common import get_user, get_user_by_refresh_token
from utils.exceptions import Unauthorized
from utils.jwt_utils import create_tokens
from utils.kong import delete_jwt_credentials
from utils.orm import get_object_or_404
from shamir import ShamirEmail

router = APIRouter(tags=['token'])


@router.get('/login_required')
async def login_required(user: User = Depends(get_user)):
    return {'message': 'you are currently logged in', 'uid': user.pk}


@router.post('/login', response_model=TokensResponse)
async def login(body: LoginModel):
    # TODO: login v2
    user = await get_object_or_404(User, identifier=make_identifier(body.email))
    if not check_password(body.password, user.password):
        raise Unauthorized('password incorrect')
    shamir = await ShamirEmail.get_or_none(user_id=user.id)
    if not shamir:
        await shamir.gpg.encrypt_email(body.email, user.id)
    access_token, refresh_token = await create_tokens(user)
    return {'access': access_token, 'refresh': refresh_token, 'message': 'login successful'}


@router.get('/logout', response_model=MessageResponse)
async def logout(user: User = Depends(get_user)):
    await delete_jwt_credentials(user.id)
    return {'message': 'logout successful'}


@router.post('/refresh', response_model=TokensResponse)
async def refresh(user: User = Depends(get_user_by_refresh_token)):
    access_token, refresh_token = await create_tokens(user)
    return {'access': access_token, 'refresh': refresh_token, 'message': 'refresh successful'}
