#  serve oauth2 resources
from fastapi import Header, Depends

from config import config
from models import User
from oauth2 import router
from utils.exceptions import Unauthorized
from utils.orm import get_object_or_404


def get_user_id_by_oauth2(x_authenticated_userid: str = Header(default='')):
    if config.debug:  # mock
        return 1
    try:
        id = int(x_authenticated_userid)
    except:
        raise Unauthorized('oauth2 token needed')
    return id


@router.get('/oauth2/me')
async def oauth_me(
        id: int = Depends(get_user_id_by_oauth2),
        x_authenticated_scope: str = Header(default='id nickname')
):
    user = await get_object_or_404(User, id=id)
    scopes = x_authenticated_scope.strip().split(' ')
    response = {}
    if 'email' in scopes:
        # generate a fake email because user email is encrypted
        response['email'] = f'user_{user.id}@{config.domain}'
        scopes.remove('email')
    for scope in scopes:
        try:
            response[scope] = getattr(user, scope)
        except AttributeError:
            pass
    return response
