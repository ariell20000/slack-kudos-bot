#services/services.py

from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.logger import logger
from models_db import KudosDB, User
from datetime import datetime, timezone
from models import KudosResponse, UserFullResponse, Kudos
from security import hash_password
from security import verify_password, create_access_token


def get_leaderboard(db: Session):
    leaderboard = (db.query(
        User.username,
        func.count(KudosDB.id).label("score")
    ).outerjoin(KudosDB, User.id == KudosDB.to_user_id # LEFT OUTER JOIN, TO INCLUDE USERS WITH 0 KUDOS
    ).filter(User.is_active==True).
        group_by(
        User.id, User.username
    ).order_by(
        func.count(KudosDB.id).desc()    ).
                   all())
    return [{"username": user, "score": score} for user, score in leaderboard]

def get_kudos_by_id(kudos_id: int, db: Session):
    kudos = db.get(KudosDB, kudos_id)
    if not kudos:
        raise HTTPException(status_code=404, detail="Kudos not found.")
    kudos_res= KudosResponse(
        message=kudos.message,
        from_user=kudos.from_user.username,
        time_created=kudos.time_created
    )
    return kudos_res

def delete_kudos_by_id(kudos_id: int, current_user, db: Session):
    try:
        require_admin(current_user)
    except Exception as e:
        logger.warning("User %s tried to delete Kudos %s but is not admin", current_user.username, kudos_id)
        raise HTTPException(status_code=403,detail= "Admin only")
    try:
        kudos = db.get(KudosDB, kudos_id)
        if not kudos:
            logger.warning("sender tried to delete kudos that doesnt exists")
            raise HTTPException(status_code=404, detail="Kudos not found.")
        db.delete(kudos)
        db.commit()
        logger.info("User %s deleted kudos number - %s", current_user.username, kudos_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to delete kudos number - %s by user %s", kudos_id, current_user.username)
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"status": "deleted"}

def get_kudos_by_username(username: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    kudos = user.received_kudos
    kudos_res = []
    for k in kudos:
        kudos_res.append(KudosResponse(
            message=k.message,
            from_user=k.from_user.username,
            time_created=k.time_created
        ))
    return kudos_res

def add_kudos(kudos_request: Kudos, from_user: User, db: Session):
    """
    Add a kudos from `from_user` to the target user specified in `kudos_request`.

    Validations:
    - Message must exist and be <= 200 chars.
    - Cannot send kudos to self.
    - Both users must exist and be active.
    - User cannot exceed daily kudos limit (default 5/day).
    """
    if not kudos_request.to_user:
        logger.warning("Sender %s tried to send kudos without receiver", from_user.username)
        raise HTTPException(status_code=400, detail="Missing receiver")

    if not kudos_request.message:
        logger.warning("Sender %s tried to send kudos without message", from_user.username)
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if len(kudos_request.message) > 200:
        logger.warning("Sender %s tried to send kudos with too long message", from_user.username)
        raise HTTPException(status_code=400, detail="Message too long")

    if from_user.username == kudos_request.to_user:
        logger.warning("Sender %s tried to send kudos to self", from_user.username)
        raise HTTPException(status_code=400, detail="You cannot give kudos to yourself")

    to_user = db.query(User).filter(User.username == kudos_request.to_user).first()
    if not to_user:
        logger.warning("Sender %s tried to send kudos but receiver not found", from_user.username)
        raise HTTPException(status_code=404, detail="Receiver not found")

    if not from_user.is_active:
        logger.warning("Inactive sender %s tried to send kudos", from_user.username)
        raise HTTPException(status_code=400, detail="Inactive sender")

    if not to_user.is_active:
        logger.warning("Sender %s tried to send kudos to inactive user %s", from_user.username, to_user.username)
        raise HTTPException(status_code=400, detail="Inactive receiver")

    if check_too_many_kudos_in_day(db, from_user.id):
        logger.warning("Sender %s reached daily kudos limit", from_user.username)
        raise HTTPException(status_code=400, detail="Too many kudos today")

    db_kudos = KudosDB(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        message=kudos_request.message,
        time_created=datetime.now(timezone.utc)
    )

    try:
        db.add(db_kudos)
        db.commit()
        db.refresh(db_kudos)
        logger.info("User %s sent kudos to %s", from_user.username, to_user.username)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to add kudos from %s to %s", from_user.username, to_user.username)
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"status": "received", "kudos_id": db_kudos.id}

def get_status(username: str, db: Session):
    user=db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    kodus_given= db.query(KudosDB).filter(KudosDB.from_user_id == user.id).count()
    kudos_received= db.query(KudosDB).filter(KudosDB.to_user_id == user.id).count()
    return {
        "username": username,
        "kudos_given": kodus_given,
        "kudos_received": kudos_received,
        "is_active": user.is_active
    }

def register_user(user_data, db: Session):
    user = db.query(User).filter(User.username == user_data.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    try:
        hashed = hash_password(user_data.password)

        new_user = User(
            username=user_data.username,
            password_hash=hashed,
            auth_provider="local",
            role="user",
            is_active=True,
        )

        db.add(new_user)
        db.commit()

        logger.info("New user registered - %s", user_data.username)

    except IntegrityError:

        db.rollback()

        logger.warning(
            "Username already exists: %s",
            user_data.username,
        )

        raise

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to register new user %s",
            user_data.username,
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )

    return {"status": "created"}

def login_user(user_data, db: Session):
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user:
        logger.warning("Login failed for non existing user - %s", user_data.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.auth_provider != "local":
        logger.warning("Login attempt for slack user - %s", user_data.username)
        raise HTTPException(status_code=400, detail="Use Slack login")

    if not user.is_active:
        logger.warning("Login failed for non active user - %s", user_data.username)
        raise HTTPException(status_code=403, detail="User is inactive")

    if not verify_password(user_data.password, user.password_hash):
        logger.warning("Login failed for user - %s, wrong password", user_data.username)
        raise HTTPException(status_code=401, detail="Invalid details")

    token = create_access_token({"sub": user.username})

    logger.info("User %s logged in", user_data.username)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def delete_user(username: str,current_user, db: Session):
    try:
        require_admin(current_user)
    except Exception as e:
        logger.warning("User %s tried to delete user %s but is not admin", current_user.username, username)
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning("Admin %s tried to delete user %s but user not found", current_user.username, username)
            raise HTTPException(status_code=404, detail="User not found.")
        user.is_active = False
        db.commit()
        logger.info("Admin %s deleted user %s", current_user.username, username)
    except Exception:
        db.rollback()
        logger.exception("Failed to delete user %s by admin %s", username, current_user.username)
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"status": "deleted"}

def get_users_data( current_user, db: Session):
    try:
        require_admin(current_user)
    except Exception as e:
        logger.warning("User %s tried to access all users data but is not admin", current_user.username)
        raise HTTPException(status_code=403, detail="Admin only")
    users = (
        db.query(User)
        .options(
            joinedload(User.received_kudos)
            .joinedload(KudosDB.from_user)
        )
        .all()
    )
    users_data = []
    for user in users:
        kudos_res=[]
        for k in user.received_kudos:
            kudos_res.append(KudosResponse(
                message=k.message,
                from_user=k.from_user.username,
                time_created=k.time_created
            ))
        users_data.append(UserFullResponse(
            username=user.username,
            is_active=user.is_active,
            kudos_received=kudos_res
         )

    )
    logger.info("Admin %s accessed all users data", current_user.username)
    return users_data



#function that checks if the user has gave too many kudos in a day, with a default limit of 5
def check_too_many_kudos_in_day(db: Session, user_id, k=5):
    today= datetime.now(timezone.utc).date()
    kudosnum = db.query(KudosDB).filter(KudosDB.from_user_id == user_id, func.date(KudosDB.time_created)==today).count()
    return kudosnum >= k

def create_user(db, username):
    try:
        new_user = User(username=username)
        db.add(new_user)
        db.commit()
        return {"status": "created"}
    except IntegrityError:
        # Rollback the transaction to clear the failed insert
        # relevant in race conditions where two requests try to create the same user at the same time
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

def login_slack_user(db, slack_id: str, username: str):
    user = db.query(User).filter(User.slack_id == slack_id).first()
    if not user:
        user = User(
            username=username,
            slack_id=slack_id,
            auth_provider="slack",
            role="user",
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("new user created automatically by slack - %s", user.username)
    if not user.is_active:
        logger.warning("slack user %s tried to login but is not active", slack_id)
        raise HTTPException(status_code=403, detail="Inactive user")

    return user

def get_user_by_username(db, username: str):

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return user

def promote_user(username: str, current_user, db: Session):

    user = db.query(User).filter(User.username == username).first()
    require_admin(current_user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User inactive")

    user.role = "admin"
    logger.info("User %s promoted to admin", username)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to promote user")

    return {"status": "promoted"}

def require_admin(user):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")