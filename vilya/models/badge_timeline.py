from vilya.libs.store import store


def get_item_count(name):
    if name == '':
        rs = store.execute("select count(1) from badge_item")
    else:
        rs = store.execute(
            "select count(1) from badge_item where item_id=%s", (name,))
    data = rs and rs[0]
    return data


def get_all_badges():
    data = store.execute("select badge_id, name, summary from badge")
    return data


def get_all_items(index, increment, name):
    start = index * increment
    if name == '':
        params = (start, increment)
        data = store.execute(
            "select badge_id, item_id, reason, date from badge_item "
            "order by date desc limit %s,%s", params)
    else:
        params = (name, start, increment)
        data = store.execute(
            "select badge_id, item_id, reason, date from badge_item "
            "where item_id=%s order by date desc limit %s,%s", params)
    return data
