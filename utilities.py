def remove_duplicate_in_list(list: list, item):
    item_count = list.count(item)
    for _ in range(item_count):
        list.remove(item)


def pop_and_remove(list, item_index):
    item = list.pop(item_index)
    item_count = list.count(item)
    for _ in range(item_count):
        list.remove(item)

    return item
