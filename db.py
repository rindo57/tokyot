import pymongo, os
from datetime import datetime
import asyncio

dbclient = pymongo.MongoClient("mongodb+srv://anidl:encodes@cluster0.oobfx33.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
database = dbclient["tokyo"]

user_data = database['users']
used_tokens = database['used_tokens']
verification_tokens = database['verification_tokens']

async def add_verification_token(user_id: int, token: str):
    """Add a new verification token with expiration"""
    verification_tokens.insert_one({
        'user_id': user_id,
        'token': token,
        'created_at': datetime.now(),
        'used': False
    })
    return

async def is_valid_verification_token(user_id: int, token: str):
    """Check if a verification token is valid"""
    record = verification_tokens.find_one({
        'user_id': user_id,
        'token': token,
        'used': False,
        'created_at': {'$gt': datetime.now() - timedelta(hours=1)}  # Token expires in 1 hour
    })
    return bool(record)

async def mark_token_used(token: str):
    """Mark a verification token as used"""
    verification_tokens.update_one(
        {'token': token},
        {'$set': {'used': True}}
    )
    return

async def cleanup_expired_tokens():
    """Clean up expired verification tokens"""
    verification_tokens.delete_many({
        'created_at': {'$lt': datetime.now() - timedelta(hours=1)}
    })
    return
    
async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int, uname):
    user_data.insert_one({
        '_id': user_id, 
        'username': uname,
        'search_count': 0,
        'last_reset': datetime.now(),
        'verified': False
    })
    return

async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

async def get_user_data(user_id: int):
    return user_data.find_one({'_id': user_id})

async def update_user_search_count(user_id: int, count: int, last_reset=None):
    update_data = {
        '$set': {
            'search_count': count
        }
    }
    
    if last_reset:
        update_data['$set']['last_reset'] = last_reset
    
    user_data.update_one(
        {'_id': user_id},
        update_data,
        upsert=True
    )
    return

async def mark_user_verified(user_id: int):
    user_data.update_one(
        {'_id': user_id},
        {'$set': {'verified': True}},
        upsert=True
    )
    return

async def add_used_token(token: str, user_id: int):
    used_tokens.insert_one({
        'token': token,
        'user_id': user_id,
        'used_at': datetime.now()
    })
    return

async def is_token_used(token: str):
    return bool(used_tokens.find_one({'token': token}))
