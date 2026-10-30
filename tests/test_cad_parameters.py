from cad.api.main import PlateParameters


def test_default_plate_parameters_are_valid():
    params = PlateParameters()
    assert params.length_mm == 100
    assert params.width_mm == 60
    assert params.thickness_mm == 5


def test_custom_plate_parameters_are_valid():
    params = PlateParameters(length_mm=120, width_mm=80, thickness_mm=4,
                            hole_diameter_mm=4, hole_inset_mm=12)
    assert params.length_mm == 120
    assert params.hole_inset_mm == 12
