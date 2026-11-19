
# ============================================================
# MEP TOOLS - AUTO SECTION BOX V6
# BALA MEP SUITE PROFESSIONAL
# Revit 2024.3 | pyRevit 6.4
#
# FEATURES:
# 1. Reuse preselected elements
# 2. Element-oriented section box
# 3. Existing / new 3D view
# 4. Remember last used view
# 5. Editable view name
# 6. Adjustable buffer in mm
# 7. Optional 3D view template
# 8. No success popup
# 9. Error popup only
# ============================================================

__title__ = "Auto\nSection Box"
__author__ = "BALA"

from pyrevit import revit, forms, script

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    View3D,
    ViewType,
    ViewFamily,
    ViewFamilyType,
    BoundingBoxXYZ,
    XYZ,
    Transform,
    LocationCurve,
    LocationPoint,
    Transaction
)

from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

import clr

clr.AddReference("System")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System import Decimal
from System.Drawing import Point, Size, Font, FontStyle

from System.Windows.Forms import (
    Form,
    Label,
    ComboBox,
    ComboBoxStyle,
    Button,
    DialogResult,
    FormStartPosition,
    FormBorderStyle,
    NumericUpDown
)


# ============================================================
# DOCUMENT
# ============================================================

doc = revit.doc
uidoc = revit.uidoc

config = script.get_config()


# ============================================================
# LAST USED VIEW
# ============================================================

def get_last_view():

    try:
        return config.last_used_3d_view
    except:
        return ""


def save_last_view(name):

    config.last_used_3d_view = name
    script.save_config()


# ============================================================
# GET EXISTING 3D VIEWS
# ============================================================

def get_3d_views():

    result = []

    collector = (
        FilteredElementCollector(doc)
        .OfClass(View3D)
        .ToElements()
    )

    for view in collector:

        if not view.IsTemplate:
            result.append(view)

    result.sort(key=lambda x: x.Name.lower())

    return result


# ============================================================
# GET 3D VIEW TEMPLATES
# ============================================================

def get_3d_templates():

    result = []

    collector = (
        FilteredElementCollector(doc)
        .OfClass(View)
        .ToElements()
    )

    for view in collector:

        if view.IsTemplate and view.ViewType == ViewType.ThreeD:
            result.append(view)

    result.sort(key=lambda x: x.Name.lower())

    return result


# ============================================================
# FIND EXISTING VIEW
# ============================================================

def find_existing_view(name, views):

    for view in views:

        if view.Name.lower() == name.lower():
            return view

    return None


# ============================================================
# CREATE UNIQUE VIEW NAME
# ============================================================

def get_unique_view_name(base_name):

    existing_names = [
        view.Name.lower()
        for view in (
            FilteredElementCollector(doc)
            .OfClass(View)
            .ToElements()
        )
    ]

    name = base_name
    number = 1

    while name.lower() in existing_names:

        name = "{} ({})".format(
            base_name,
            number
        )

        number += 1

    return name


# ============================================================
# CREATE NEW 3D VIEW
# ============================================================

def create_new_3d_view(name):

    view_types = (
        FilteredElementCollector(doc)
        .OfClass(ViewFamilyType)
        .ToElements()
    )

    three_d_type = None

    for item in view_types:

        if item.ViewFamily == ViewFamily.ThreeDimensional:
            three_d_type = item
            break

    if three_d_type is None:

        raise Exception(
            "No 3D ViewFamilyType found."
        )

    new_view = View3D.CreateIsometric(
        doc,
        three_d_type.Id
    )

    new_view.Name = get_unique_view_name(name)

    return new_view


# ============================================================
# GET SELECTED ELEMENTS
# ============================================================

def get_selected_elements():

    selected_ids = list(
        uidoc.Selection.GetElementIds()
    )

    elements = []

    # Reuse existing selection
    if selected_ids:

        for element_id in selected_ids:

            element = doc.GetElement(element_id)

            if element is not None:
                elements.append(element)

    # Ask selection only if nothing is selected
    else:

        references = uidoc.Selection.PickObjects(
            ObjectType.Element,
            "Select elements for Auto Section Box"
        )

        for reference in references:

            element = doc.GetElement(
                reference.ElementId
            )

            if element is not None:
                elements.append(element)

    return elements


# ============================================================
# GET ELEMENT ORIENTATION
# ============================================================

def get_element_direction(elements):

    for element in elements:

        try:

            location = element.Location

            # Linear / curved elements
            if isinstance(location, LocationCurve):

                curve = location.Curve

                try:

                    direction = (
                        curve.ComputeDerivatives(
                            0.5, True
                        ).BasisX
                    )

                except:

                    direction = (
                        curve.GetEndPoint(1)
                        -
                        curve.GetEndPoint(0)
                    )

                if direction.GetLength() > 0.000001:
                    return direction.Normalize()

            # Point-based family instances
            if isinstance(location, LocationPoint):

                if hasattr(element, "HandOrientation"):

                    direction = element.HandOrientation

                    if direction.GetLength() > 0.000001:
                        return direction.Normalize()

                if hasattr(element, "FacingOrientation"):

                    direction = element.FacingOrientation

                    if direction.GetLength() > 0.000001:
                        return direction.Normalize()

        except:
            continue

    # Fallback for elements without orientation
    return XYZ.BasisX


# ============================================================
# CREATE ORIENTED AXES
# ============================================================

def create_oriented_axes(direction):

    x_axis = direction.Normalize()

    reference_axis = XYZ.BasisZ

    # Avoid parallel vectors
    if abs(x_axis.DotProduct(reference_axis)) > 0.99:

        reference_axis = XYZ.BasisY

    y_axis = reference_axis.CrossProduct(
        x_axis
    ).Normalize()

    z_axis = x_axis.CrossProduct(
        y_axis
    ).Normalize()

    return x_axis, y_axis, z_axis


# ============================================================
# CALCULATE ORIENTED BOUNDING BOX
# ============================================================

def calculate_oriented_bounds(elements):

    # Orientation from first eligible selected element
    direction = get_element_direction(elements)

    x_axis, y_axis, z_axis = create_oriented_axes(
        direction
    )

    min_x = float("inf")
    min_y = float("inf")
    min_z = float("inf")

    max_x = float("-inf")
    max_y = float("-inf")
    max_z = float("-inf")

    valid_count = 0

    # Read every selected element bounding box
    for element in elements:

        bbox = element.get_BoundingBox(None)

        if bbox is None:
            continue

        bbox_transform = bbox.Transform

        # All 8 corners of the element bounding box
        for x in (bbox.Min.X, bbox.Max.X):

            for y in (bbox.Min.Y, bbox.Max.Y):

                for z in (bbox.Min.Z, bbox.Max.Z):

                    local_point = XYZ(x, y, z)

                    world_point = (
                        bbox_transform.OfPoint(local_point)
                    )

                    # Project world point into oriented axes
                    px = world_point.DotProduct(x_axis)
                    py = world_point.DotProduct(y_axis)
                    pz = world_point.DotProduct(z_axis)

                    min_x = min(min_x, px)
                    min_y = min(min_y, py)
                    min_z = min(min_z, pz)

                    max_x = max(max_x, px)
                    max_y = max(max_y, py)
                    max_z = max(max_z, pz)

        valid_count += 1

    if valid_count == 0:

        raise Exception(
            "No valid element bounding boxes found."
        )

    return (
        min_x, min_y, min_z,
        max_x, max_y, max_z,
        valid_count,
        x_axis, y_axis, z_axis
    )


# ============================================================
# SETTINGS DIALOG
# ============================================================

def show_settings_dialog(views, templates, last_view):

    form = Form()

    form.Text = "Section Box Size"
    form.Size = Size(480, 275)

    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog

    form.MaximizeBox = False
    form.MinimizeBox = False

    form.Font = Font("Arial", 9)

    # VIEW LABEL
    view_label = Label()

    view_label.Text = "View:"
    view_label.Location = Point(10, 12)
    view_label.Size = Size(55, 22)

    form.Controls.Add(view_label)

    # EDITABLE VIEW COMBO
    view_combo = ComboBox()

    view_combo.Location = Point(70, 10)
    view_combo.Size = Size(380, 25)

    view_combo.DropDownStyle = ComboBoxStyle.DropDown

    for view in views:
        view_combo.Items.Add(view.Name)

    form.Controls.Add(view_combo)

    # STATUS
    status_label = Label()

    status_label.Location = Point(65, 38)
    status_label.Size = Size(380, 22)

    form.Controls.Add(status_label)

    def update_status(sender, args):

        name = view_combo.Text.strip()

        existing = find_existing_view(
            name, views
        )

        if existing is not None:

            status_label.Text = "Existing View Will Be Used"

        elif name:

            status_label.Text = "New View Will Be Created"

        else:

            status_label.Text = ""

    view_combo.TextChanged += update_status

    # RESTORE LAST USED VIEW
    if last_view:

        existing = find_existing_view(
            last_view, views
        )

        if existing is not None:
            view_combo.Text = existing.Name

    update_status(None, None)

    # SIZE LABEL
    size_label = Label()

    size_label.Text = "Size:"
    size_label.Location = Point(10, 72)
    size_label.Size = Size(50, 24)

    form.Controls.Add(size_label)

    # SIZE OPTION
    size_combo = ComboBox()

    size_combo.Location = Point(65, 70)
    size_combo.Size = Size(190, 25)

    size_combo.DropDownStyle = ComboBoxStyle.DropDownList

    size_combo.Items.Add("Specified size")
    size_combo.Items.Add("Element extents, plus buffer")

    size_combo.SelectedIndex = 1

    form.Controls.Add(size_combo)

    # BUFFER INPUT
    buffer_input = NumericUpDown()

    buffer_input.Location = Point(260, 70)
    buffer_input.Size = Size(105, 25)

    buffer_input.Minimum = Decimal(0)
    buffer_input.Maximum = Decimal(100000)

    buffer_input.Value = Decimal(300)
    buffer_input.Increment = Decimal(50)

    form.Controls.Add(buffer_input)

    # UNIT
    unit_label = Label()

    unit_label.Text = "mm"
    unit_label.Location = Point(370, 72)
    unit_label.Size = Size(35, 22)

    form.Controls.Add(unit_label)

    # TEMPLATE LABEL
    template_label = Label()

    template_label.Text = "Assign View Template:"
    template_label.Location = Point(10, 115)
    template_label.Size = Size(160, 22)

    form.Controls.Add(template_label)

    # TEMPLATE COMBO
    template_combo = ComboBox()

    template_combo.Location = Point(10, 140)
    template_combo.Size = Size(440, 25)

    template_combo.DropDownStyle = ComboBoxStyle.DropDownList

    template_options = [None]

    template_combo.Items.Add("<None>")

    for template in templates:

        template_options.append(template)
        template_combo.Items.Add(template.Name)

    template_combo.SelectedIndex = 0

    form.Controls.Add(template_combo)

    # OK
    ok_button = Button()

    ok_button.Text = "OK"
    ok_button.Location = Point(230, 195)
    ok_button.Size = Size(85, 28)

    ok_button.DialogResult = DialogResult.OK

    form.Controls.Add(ok_button)

    # CANCEL
    cancel_button = Button()

    cancel_button.Text = "Cancel"
    cancel_button.Location = Point(325, 195)
    cancel_button.Size = Size(85, 28)

    cancel_button.DialogResult = DialogResult.Cancel

    form.Controls.Add(cancel_button)

    form.AcceptButton = ok_button
    form.CancelButton = cancel_button

    result = form.ShowDialog()

    if result != DialogResult.OK:
        return None

    view_name = view_combo.Text.strip()

    if not view_name:
        raise Exception(
            "Please select or enter a 3D View name."
        )

    selected_view = find_existing_view(
        view_name, views
    )

    selected_template = template_options[
        template_combo.SelectedIndex
    ]

    size_option = size_combo.SelectedIndex
    size_mm = float(buffer_input.Value)

    return (
        view_name,
        selected_view,
        selected_template,
        size_option,
        size_mm
    )


# ============================================================
# MAIN EXECUTION
# ============================================================

try:

    # STEP 1 - GET SELECTION
    elements = get_selected_elements()

    if not elements:

        raise Exception("No elements selected.")

    # STEP 2 - CALCULATE ORIENTED BOUNDS
    bounds = calculate_oriented_bounds(elements)

    (
        min_x, min_y, min_z,
        max_x, max_y, max_z,
        valid_count,
        x_axis, y_axis, z_axis
    ) = bounds

    # STEP 3 - GET VIEWS
    views = get_3d_views()

    templates = get_3d_templates()

    last_view = get_last_view()

    # STEP 4 - SETTINGS
    settings = show_settings_dialog(
        views,
        templates,
        last_view
    )

    if settings is not None:

        (
            view_name,
            selected_view,
            selected_template,
            size_option,
            size_mm
        ) = settings

        size_ft = size_mm / 304.8

        # Specified size = centered cube with exact total side length.
        # Element extents + buffer = existing calculated bounds plus padding.

        # STEP 5 - TRANSACTION
        transaction = Transaction(
            doc,
            "MEP Tools - Auto Section Box"
        )

        transaction.Start()

        try:

            # EXISTING OR NEW VIEW
            if selected_view is not None:

                target_view = doc.GetElement(
                    selected_view.Id
                )

            else:

                target_view = create_new_3d_view(
                    view_name
                )

            # OPTIONAL TEMPLATE
            if selected_template is not None:

                target_view.ViewTemplateId = (
                    selected_template.Id
                )

            # CREATE ORIENTED TRANSFORM
            box_transform = Transform.Identity

            box_transform.Origin = XYZ.Zero

            box_transform.BasisX = x_axis
            box_transform.BasisY = y_axis
            box_transform.BasisZ = z_axis

            # CREATE ORIENTED SECTION BOX
            section_box = BoundingBoxXYZ()

            section_box.Transform = box_transform

            if size_option == 0:
                # SPECIFIED SIZE: centered cube around selected elements
                center_x = (min_x + max_x) / 2.0
                center_y = (min_y + max_y) / 2.0
                center_z = (min_z + max_z) / 2.0
                half_size = size_ft / 2.0

                section_box.Min = XYZ(
                    center_x - half_size,
                    center_y - half_size,
                    center_z - half_size
                )

                section_box.Max = XYZ(
                    center_x + half_size,
                    center_y + half_size,
                    center_z + half_size
                )
            else:
                # ELEMENT EXTENTS PLUS BUFFER: existing behavior
                section_box.Min = XYZ(
                    min_x - size_ft,
                    min_y - size_ft,
                    min_z - size_ft
                )

                section_box.Max = XYZ(
                    max_x + size_ft,
                    max_y + size_ft,
                    max_z + size_ft
                )

            # APPLY SECTION BOX
            target_view.SetSectionBox(
                section_box
            )

            target_view.IsSectionBoxActive = True

            transaction.Commit()

        except:

            transaction.RollBack()
            raise

        # SAVE LAST VIEW
        save_last_view(target_view.Name)

        # OPEN TARGET VIEW
        uidoc.ActiveView = target_view

        # SUCCESS POPUP DISABLED


except OperationCanceledException:

    pass

except Exception as error:

    forms.alert(
        "AUTO SECTION BOX ERROR:\n\n{}".format(error),
        title="MEP Tools - Error"
    )
