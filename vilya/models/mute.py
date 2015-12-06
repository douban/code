# coding: utf-8


from vilya.libs.rdstore import rds

# FIXME: 直接取proj了，如果以后有不基于proj的再改吧=.=
RDS_MUTE_KEY = "mute:{type}:{proj_name}:{target_id}"


def mute_rds_key(type_, proj_name, target_id):
    return RDS_MUTE_KEY.format(type=type_, proj_name=proj_name,
                               target_id=target_id)


class Mute(object):

    @staticmethod
    def mute(type_, proj_name, target_id, user_id):
        key = mute_rds_key(type_, proj_name, target_id)
        rds.sadd(key, user_id)

    @staticmethod
    def unmute(type_, proj_name, target_id, user_id):
        key = mute_rds_key(type_, proj_name, target_id)
        rds.srem(key, user_id)

    @staticmethod
    def filter(type_, proj_name, target_id, users):
        key = mute_rds_key(type_, proj_name, target_id)
        muted_users = rds.smembers(key)
        return set(users) - set(muted_users)

    @staticmethod
    def is_muted(type_, proj_name, target_id, user_id):
        key = mute_rds_key(type_, proj_name, target_id)
        return rds.sismember(key, user_id)
