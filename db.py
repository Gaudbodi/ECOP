import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
from werkzeug.security import generate_password_hash, check_password_hash

# MongoDB Configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "fsrp_aggregator")


_mongo_client = None
_db_instance = None

def get_db():
    """Returns a connected MongoDB database instance (singleton pattern)."""
    global _mongo_client, _db_instance
    if _db_instance is not None:
        return _db_instance
    try:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _mongo_client.admin.command('ping')
        _db_instance = _mongo_client[DB_NAME]
        logging.info("Successfully connected to MongoDB.")
        return _db_instance
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        return None

def _operator_allowed_ips():
    """Phase 2: non-Admin operators read their allowlist from
    ALLOWED_OPERATOR_IPS env var (comma-separated). Default = localhost only.
    Setting the value to ``*`` keeps the legacy "any IP" behaviour for
    backwards compatibility during rollout."""
    raw = os.environ.get("ALLOWED_OPERATOR_IPS", "127.0.0.1,::1").strip()
    if raw == "*":
        return ["*"]
    return [ip.strip() for ip in raw.split(",") if ip.strip()]


def seed_users():
    """Seeds the database with approved personnel if the collection is empty,
    or updates existing ones with the latest fields."""
    db = get_db()
    if db is None: return

    users_coll = db['users']
    operator_ips = _operator_allowed_ips()
    dummy_users = [
        {
            "staff_id": "E004",
            "email": "francisyiryel@gmail.com",
            # phone_number is intentionally None so 2FA routes through Resend
            # email — the superuser path that this account is designed to test.
            "phone_number": None,
            # notify_email is the *delivery* address for the OTP. Distinct
            # from the login identity above so the platform can keep using a
            # corporate email for sign-in while delivery hits the operator's
            # actual inbox until a verified Resend domain is in place.
            # "notify_email": os.environ.get("SUPERUSER_NOTIFY_EMAIL", "francisyiryel@gmail.com"),
            "password": generate_password_hash("password123"),
            "name": "Francis Yiryel",
            "agency": "NCA",
            "role": "Super Admin",
            "is_superuser": True,
            "allowed_ips": ["*"],
        },
        {
            "staff_id": "G001",
            "email": "generator@example.com",
            "phone_number": os.environ.get("GENERATOR_PHONE_NUMBER", "+233000000001"),
            "password": generate_password_hash("gen_pass"),
            "name": "Akwesi Mensah",
            "agency": "GMeT",
            "role": "cap generator",
            "allowed_ips": operator_ips,
        },
        {
            "staff_id": "V001",
            "email": "validator@example.com",
            "phone_number": os.environ.get("VALIDATOR_PHONE_NUMBER", "+233000000002"),
            "password": generate_password_hash("val_pass"),
            "name": "Efua Nkrumah",
            "agency": "GMeT",
            "role": "cap validator",
            "allowed_ips": operator_ips,
        },
        {
            "staff_id": "N001",
            "email": "nadmo_gen@example.com",
            "phone_number": os.environ.get("NADMO_PHONE_NUMBER", "+233000000003"),
            "password": generate_password_hash("nadmo_pass"),
            "name": "Kofi Arhin",
            "agency": "NADMO",
            "role": "cap generator",
            "allowed_ips": operator_ips,
        }
    ]

    for user in dummy_users:
        update_set = {
            "email": user["email"],
            "phone_number": user.get("phone_number"),
            "role": user["role"],
            "name": user["name"],
            "agency": user["agency"],
            "allowed_ips": user["allowed_ips"],
        }
        if user.get("notify_email"):
            update_set["notify_email"] = user["notify_email"]
        if user.get("is_superuser"):
            update_set["is_superuser"] = True
        users_coll.update_one(
            {"staff_id": user["staff_id"]},
            {
                "$set": update_set,
                "$setOnInsert": {
                    "password": user["password"]
                }
            },
            upsert=True
        )
    # Belt-and-braces: clear stale entries that may match the legacy
    # `francis@example.com` email so the new superuser email is the only
    # record pointing at staff_id E004.
    # users_coll.delete_many({"email": "francis@example.com", "staff_id": {"$ne": "E004"}})
    logging.info("Users synchronized in database (allowlist for non-Admin operators: %s).", operator_ips)


# ─── Admin user-onboarding helpers (Super Admin only at the route layer) ───

def list_users():
    """Return all user records (sans password hash) sorted by created_at desc
    if present, else by name. Used by the Admin Panel."""
    db = get_db()
    if db is None:
        return []
    try:
        users = list(db['users'].find({}, {'password': 0}))
        for u in users:
            if '_id' in u:
                u['_id'] = str(u['_id'])
        users.sort(key=lambda u: (u.get('created_at') or '0000', u.get('name') or ''), reverse=True)
        return users
    except Exception as e:
        logging.error("list_users failed: %s", e)
        return []


def create_user(*, email, name, agency, role, phone_number=None, staff_id=None, password=None,
                allowed_ips=None, created_by=None):
    """Insert a new user. Returns (user_doc, error_message). On success error
    is None; on failure user_doc is None."""
    db = get_db()
    if db is None:
        return None, "datastore_unavailable"
    email = (email or '').strip().lower()
    if not email:
        return None, "email_required"
    if not name:
        return None, "name_required"
    if not agency:
        return None, "agency_required"
    valid_roles = {"cap generator", "cap validator", "Admin"}
    # Super Admin is intentionally NOT creatable through this path — it is
    # bootstrapped via seed_users() only.
    if role not in valid_roles:
        return None, "invalid_role"

    users_coll = db['users']
    if users_coll.find_one({"email": email}):
        return None, "email_exists"
    if not staff_id:
        # Generate a stable per-agency staff id: e.g. NADMO-2 if NADMO already
        # has one user in the table. Falls back to U-<random> on collision.
        prefix = (agency or 'USR').replace(' ', '').upper()[:6]
        existing = users_coll.count_documents({"agency": agency})
        staff_id = f"{prefix}-{existing + 1:03d}"
    if users_coll.find_one({"staff_id": staff_id}):
        import secrets as _secrets
        staff_id = f"{staff_id}-{_secrets.token_hex(2).upper()}"

    doc = {
        "staff_id": staff_id,
        "email": email,
        "phone_number": phone_number,
        "name": name,
        "agency": agency,
        "role": role,
        "allowed_ips": allowed_ips or _operator_allowed_ips(),
        "password": generate_password_hash(password or "change-me"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": created_by,
    }
    try:
        result = users_coll.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        doc.pop('password', None)
        return doc, None
    except Exception as e:
        logging.error("create_user insert failed: %s", e)
        return None, "insert_failed"

def get_user_by_staff_id(staff_id):
    db = get_db()
    if db is not None:
        return db['users'].find_one({"staff_id": staff_id})
    return None

def get_user_by_email(email):
    db = get_db()
    if db is not None:
        return db['users'].find_one({"email": email})
    return None

VERIFICATION_MAX_ATTEMPTS = 5
VERIFICATION_LOCKOUT_MINUTES = 30
VERIFICATION_TTL_MINUTES = 10


def save_verification_code(email, code):
    """Saves a verification code to the database with a timestamp.
    Resets the failed-attempt counter so a fresh code starts clean."""
    db = get_db()
    if db is not None:
        try:
            codes_coll = db['verification_codes']
            codes_coll.update_one(
                {'email': email},
                {
                    '$set': {
                        'code': code,
                        'created_at': datetime.now(timezone.utc),
                        'attempts': 0,
                        'locked_until': None,
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error saving verification code: {e}")
    return False


def is_email_locked(email):
    """Returns True if the email is currently locked due to repeated bad
    verification attempts."""
    db = get_db()
    if db is None:
        return False
    try:
        record = db['verification_codes'].find_one({'email': email})
    except Exception as e:
        logging.error(f"Error checking lockout for {email}: {e}")
        return False
    if not record:
        return False
    locked_until = record.get('locked_until')
    if not locked_until:
        return False
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < locked_until


def verify_code(email, code):
    """Verifies the code for a given email. Tracks failed attempts; locks the
    email for ``VERIFICATION_LOCKOUT_MINUTES`` after
    ``VERIFICATION_MAX_ATTEMPTS`` consecutive failures. Returns True on match
    within the TTL, False otherwise (including locked or expired)."""
    db = get_db()
    if db is None:
        return False
    try:
        codes_coll = db['verification_codes']
        record = codes_coll.find_one({'email': email})
        if not record:
            return False

        # Already locked? Refuse silently (caller surfaces a generic error).
        locked_until = record.get('locked_until')
        if locked_until:
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < locked_until:
                logging.warning("verify_code denied for %s: locked until %s", email, locked_until)
                return False

        # Match + not expired → success, clear counter.
        if record.get('code') == code:
            created_at = record['created_at']
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - created_at < timedelta(minutes=VERIFICATION_TTL_MINUTES):
                codes_coll.update_one(
                    {'email': email},
                    {'$set': {'attempts': 0, 'locked_until': None}}
                )
                return True
            # Expired — don't penalise the user, but require a new code.
            return False

        # Mismatch — increment attempts, lock if at threshold.
        new_attempts = (record.get('attempts') or 0) + 1
        update = {'attempts': new_attempts}
        if new_attempts >= VERIFICATION_MAX_ATTEMPTS:
            update['locked_until'] = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_LOCKOUT_MINUTES)
            logging.warning("Email %s locked after %d failed verification attempts.", email, new_attempts)
        codes_coll.update_one({'email': email}, {'$set': update})
        return False
    except Exception as e:
        logging.error(f"Error verifying code: {e}")
    return False

def save_alert(alert_data):
    """Saves a CAP alert to the database."""
    db = get_db()
    if db is not None:
        try:
            alerts_collection = db['alerts']
            # Default workflow_stage to 1 (Pending) if not provided
            if 'workflow_stage' not in alert_data:
                alert_data['workflow_stage'] = 1
            
            result = alerts_collection.update_one(
                {'identifier': alert_data.get('identifier')},
                {'$set': alert_data},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error saving alert: {e}")
    return False

def update_alert_workflow(identifier, stage, additional_data=None):
    """Updates the workflow stage of an alert."""
    db = get_db()
    if db is not None:
        try:
            update_fields = {'workflow_stage': stage, 'updated_at': datetime.now(timezone.utc).isoformat()}
            if additional_data:
                update_fields.update(additional_data)
            
            db['alerts'].update_one(
                {'identifier': identifier},
                {'$set': update_fields}
            )
            return True
        except Exception as e:
            logging.error(f"Error updating alert workflow: {e}")
    return False

def get_alerts_by_agency(agency):
    db = get_db()
    if db is not None:
        try:
            return list(db['alerts'].find({"sender_agency": agency}).sort('sent', -1))
        except Exception as e:
            logging.error(f"Error fetching alerts by agency: {e}")
    return []

def get_all_alerts():
    db = get_db()
    if db is not None:
        try:
            return list(db['alerts'].find().sort('sent', -1))
        except Exception as e:
            logging.error(f"Error fetching alerts: {e}")
    return []

def find_alert_by_identifier(identifier):
    """Returns a single alert document by its CAP identifier, or None."""
    db = get_db()
    if db is not None:
        try:
            return db['alerts'].find_one({"identifier": identifier})
        except Exception as e:
            logging.error(f"Error fetching alert {identifier}: {e}")
    return None
