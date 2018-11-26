from cove.lib.common import schema_dict_fields_generator


def add_extra_fields(data, deref_release_schema):
    all_schema_fields = set(schema_dict_fields_generator(deref_release_schema))

    if 'releases' in data:
        for release in data.get('releases', []):
            if not isinstance(release, dict):
                return
            add_extra_fields_to_obj(release, all_schema_fields, "")
    elif 'records' in data:
        for record in data.get('records', []):
            if not isinstance(record, dict):
                return
            for release in record.get('releases', []):
                add_extra_fields_to_obj(release, all_schema_fields, "")
            

def add_extra_fields_to_obj(obj, all_schema_fields, current_path):

    if not isinstance(obj, dict):
        return
    obj['__extra'] = {}

    for key, value in list(obj.items()):
        if key == '__extra':
            continue

        new_path = current_path + '/' + key
        if new_path not in all_schema_fields:
            obj['__extra'][key] = value
            continue

        if isinstance(value, list):
            for item in value:
                add_extra_fields_to_obj(item, all_schema_fields, new_path)
        elif isinstance(value, dict):
            add_extra_fields_to_obj(value, all_schema_fields, new_path)

    if not obj['__extra']:
        obj.pop('__extra')
