from models import Kudos

kudos_id_counter = 1
scores: dict[str, int] = {}
log:dict [int, Kudos] = {}
user_log:dict [str, list [Kudos]] = {}
