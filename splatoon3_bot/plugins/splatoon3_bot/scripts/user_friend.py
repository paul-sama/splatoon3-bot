
from nonebot import logger
from datetime import datetime as dt
from ..db_sqlite import get_all_user, get_user, model_set_user_friend
from ..splat import Splatoon
from ..sp3msg import utils

logger = logger.bind(report=True)


async def task_get_user_friend():
    logger.debug(f'task_get_user_friend start')
    t = dt.utcnow()
    users = get_all_user()
    r_lst = []
    for u in users:
        if not u or not u.session_token:
            continue

        try:
            r = await get_friends(u.id)
            r_lst.extend(r)
            model_set_user_friend(r_lst)
        except Exception as e:
            logger.warning(e)

    logger.info(f'get friends: {len(r_lst)}')

    logger.debug(f'task_get_user_friend end: {(dt.utcnow() - t).seconds}')


async def get_friends(user_id):
    u = get_user(user_id=user_id)
    logger.debug(f'set_user_info: {user_id}, {u.user_id_qq or u.user_id_tg}, {u.username}')
    user_id = u.user_id_qq or u.user_id_tg or u.id
    splt = Splatoon(user_id, u.session_token)

    await splt.test_page()

    data = utils.gen_graphql_body(utils.translate_rid['FriendsList'])
    res = await splt._request(data)
    if not res:
        logger.warning(f'get_friends error: {user_id}, {u.username}')
        return

    f_list = []
    for f in res['data']['friends']['nodes']:
        if f.get('onlineState') == 'OFFLINE':
            continue

        friend_id = f['id']
        player_name = f.get('playerName') or ''
        nickname = f.get('nickname') or ''
        logger.info(f'get_friend: {u.id}, {u.nickname} -- {player_name}, {nickname}')
        user_icon = f['userIcon']['url']
        f_list.append((user_id, friend_id, player_name, nickname, user_icon))

    return f_list
