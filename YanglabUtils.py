"""Layer-safe geometry utilities for YanglabPDK components."""

# '''
# Author       : Qian Zhang
# Date         : 2025-03-13 15:15:35
# LastEditors  : Qian Zhang
# LastEditTime : 2025-03-13 18:12:18
# FilePath     : \20250313_TESTc:\Users\Qian\OneDrive\GDS\WorkSpace\MY_GDS_PACKAGE_V3\YanglabPDK\YanglabUtils.py
# Description  : 

# Copyright (c) 2025 by Prof. Lan Yang Lab, All Rights Reserved. 
# '''

import gdsfactory as gf
from YanglabPDK.YanglabLayerStack import YanglabLayerMap as LAYER


def _layer_tuple(layer):
    try:
        return tuple(layer)
    except TypeError:
        return None


def _is_layer(layer, expected):
    """Compare port layers and layer specs across gdsfactory/kfactory versions."""
    layer_tuple = _layer_tuple(layer)
    expected_tuple = _layer_tuple(expected)
    if layer_tuple is not None and expected_tuple is not None:
        return layer_tuple == expected_tuple

    expected_value = getattr(expected, "value", expected)
    return layer == expected_value


def _has_layer(component, layer):
    return _layer_tuple(layer) in {_layer_tuple(item) for item in component.layers}


def _copy_info(source, target):
    info = source.info
    if hasattr(info, "model_copy"):
        target.info = info.model_copy()
    else:
        target.info = dict(info)


def _copy_ports(source, target):
    for port in source.ports:
        if _is_layer(port.layer, LAYER.PR):
            target.add_port(name=port.name, port=port, layer=LAYER.PR)
        elif _is_layer(port.layer, LAYER.NR):
            target.add_port(name=port.name, port=port, layer=LAYER.NR)
        else:
            target.add_port(name=port.name, port=port)

# When there is a overlap between positive and negative resist, use this function to seperate them
def pos_neg_seperate(comp):
    source = comp
    has_pr = _has_layer(source, LAYER.PR)
    has_nr = _has_layer(source, LAYER.NR)

    if not has_pr and not has_nr:
        return source.copy()

    positive = source.extract(layers=(LAYER.PR,)) if has_pr else None
    negative = source.extract(layers=(LAYER.NR,)) if has_nr else None

    resist_layer_tuples = {
        _layer_tuple(layer)
        for layer, present in ((LAYER.PR, has_pr), (LAYER.NR, has_nr))
        if present
    }
    rest_layers = tuple(
        layer
        for layer in source.layers
        if _layer_tuple(layer) not in resist_layer_tuples
    )
    rest = source.extract(layers=rest_layers) if rest_layers else None

    if positive is not None and negative is not None:
        positive = gf.boolean(
            A=positive,
            B=negative,
            operation="A-B",
            layer=LAYER.PR,
            layer1=LAYER.PR,
            layer2=LAYER.NR,
        )

    result = gf.Component()
    for piece in (positive, negative, rest):
        if piece is not None and piece.layers:
            result.add_ref(piece)

    _copy_ports(comp, result)
    _copy_info(comp, result)
    return result

# Used for transfer the layer from old_layer to new_layer
def remap_layers(comp, old_layer, new_layer):
    remapped = comp.extract(layers=tuple(comp.layers))
    remapped.remap_layers({old_layer: new_layer})

    result = gf.Component()
    result.add_ref(remapped)
    for port in comp.ports:
        if _is_layer(port.layer, old_layer):
            result.add_port(name=port.name, port=port, layer=new_layer)
        else:
            result.add_port(name=port.name, port=port)
    _copy_info(comp, result)
    return result

# Layer1 - Layer2, reserve substracted layer1 and layer2
def subtract_layer(comp, layer1, layer2):
    comp1 = comp.copy().extract(layers=(layer1, ))
    comp2 = comp.copy().extract(layers=(layer2, ))
    comp3 = comp.copy().remove_layers(layers=(layer1, ))
    # Boolean operation
    comp4 = gf.boolean(A=comp1, B=comp2, operation='A-B', layer=layer1)
    all_comp = gf.Component()
    all_comp.add_ref(comp4)
    all_comp.add_ref(comp3)
    all_comp.ports = comp.ports
    return all_comp


substract_layer = subtract_layer

# Copy layer1 pattern to layer2, reserve layer1
def copy_layer(comp, layer1, layer2):
    comp1 = comp.copy().extract(layers=(layer1, ))
    comp1 = remap_layers(comp1, layer1, layer2)
    all_comp = gf.Component()
    all_comp.add_ref(comp1)
    all_comp.add_ref(comp)
    all_comp.ports = comp.ports
    return all_comp

# Remove the layer from the component
def remove_layer(comp, layer):
    comp2 = comp.copy().remove_layers(layers=(layer, ))
    return comp2


def round_unit(value, unit=0.001):
    """Round a value to the nearest layout grid unit."""
    return round(value / unit) * unit

if __name__ == "__main__":
    pass
