from ue.proxy import UEProxyStructure

from .consts import CHARGE_NODE_CLS, EXPLORER_CHEST_BASE_CLS, \
    GAS_VEIN_CLS, OIL_VEIN_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from .map import MapInfo

ACTOR_LIST_TAG_FIELD_MAP = {
    'DragonNestSpawns': 'wyvernNests',
    'IceNestSpawns': 'iceWyvernNests',
    'DrakeNestSpawns': 'drakeNests',
    'DeinonychusNestSpawns': 'deinonychusNests',
    'AB_DeinonychusNestSpawns': 'deinonychusNests'
}


def unpack_defaultdict_value(obj):
    return obj[0] if obj else None


def proxy_properties_as_dict(proxy: UEProxyStructure, key_list, only_overriden=False):
    data = {}
    for key in key_list:
        if only_overriden and not proxy.has_override(key):
            continue

        value = unpack_defaultdict_value(getattr(proxy, key, None))
        if hasattr(value, 'format_for_json'):
            value = value.format_for_json()
        data[key_list[key]] = value
    return data


def get_actor_location_vector(actor):
    '''Retrieves actor's world-space location vector.'''

    if isinstance(actor, UEProxyStructure):
        scene_component = actor.RootComponent[0].value.value
    else:
        scene_component = actor.properties.get_property("RootComponent").value.value
    actor_location = scene_component.properties.get_property("RelativeLocation").values[0]

    return actor_location

def get_volume_brush_setup(volume):
    '''Retrieves the BrushComponent and BodySetup exports from a volume.'''

    if isinstance(volume, UEProxyStructure):
        brush = volume.BrushComponent[0].value.value
    else:
        brush = volume.properties.get_property('BrushComponent').value.value
    
    return (brush, brush.properties.get_property('BrushBodySetup').value.value)

def get_volume_box_count(volume) -> int:
    '''Retrieves number of boxes in a single volume.'''

    _, body = get_volume_brush_setup(volume)    
    geometry = body.properties.get_property('AggGeom')
    convex_elements = geometry.values[0].value
    return len(convex_elements.values)


def get_volume_bounds(volume, convex_index=0):
    '''Retrieves volume's world-space bounds as tuple of two vectors: min and max.'''

    brush, body = get_volume_brush_setup(volume)
    volume_location = brush.properties.get_property('RelativeLocation').values[0]
    
    geometry = body.properties.get_property('AggGeom')
    convex_elements = geometry.values[0].value
    box = convex_elements.values[convex_index].as_dict()['ElemBox'].values[0]
    return (
        dict(
            x=box.min.x + volume_location.x,
            y=box.min.y + volume_location.y,
            z=box.min.z + volume_location.z
        ),
        dict(
            x=box.max.x + volume_location.x,
            y=box.max.y + volume_location.y,
            z=box.max.z + volume_location.z
        )
    )

def convert_box_bounds_for_export(map_info: MapInfo, box_data: dict):
    # Start
    box_data['start']['lat'] = map_info.lat.from_units(box_data['start']['y'])
    box_data['start']['long'] = map_info.long.from_units(box_data['start']['x'])
    # Center
    box_data['center'] = dict(
        x=(box_data['start']['x'] + box_data['end']['x']) / 2,
        y=(box_data['start']['y'] + box_data['end']['y']) / 2,
        z=(box_data['start']['z'] + box_data['end']['z']) / 2
    )
    box_data['center']['lat'] = map_info.lat.from_units(box_data['center']['y'])
    box_data['center']['long'] = map_info.lat.from_units(box_data['center']['x'])
    # End
    box_data['end']['lat'] = map_info.lat.from_units(box_data['end']['y'])
    box_data['end']['long'] = map_info.long.from_units(box_data['end']['x'])
