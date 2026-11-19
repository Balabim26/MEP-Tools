
# ============================================================
# BALA MEP SUITE - GRID ANNOTATION V3
# Revit 2024.3 | pyRevit 6.4
#
# FEATURES
# 1. Vertical / Horizontal / Inclined grid bubbles
# 2. Annotate All
# 3. Annotate Select Only
# 4. Automatic adjacent parallel grid dimensions
# 5. Automatic rectangular crop region alignment
# 6. Grid lines extended beyond crop boundary
# 7. Adjustable extension distance (mm)
# 8. Default extension = 300 mm
# 9. No success popup
# ============================================================

__title__ = "Grid\nAnnotation"
__author__ = "BALA"
__doc__ = (
    "Align grid bubbles and add grid dimensions in plan, "
    "elevation and section views.\n\n"
    "Created by BALA\n"
    "AI-assisted development with OpenAI"
)


from pyrevit import revit, forms

from Autodesk.Revit.DB import (
    Grid,
    ViewPlan,
    DatumEnds,
    DatumExtentType,
    Reference,
    ReferenceArray,
    FilteredElementCollector,
    Line,
    XYZ,
    Transaction
)

from Autodesk.Revit.UI.Selection import (
    ObjectType,
    ISelectionFilter
)

from Autodesk.Revit.Exceptions import OperationCanceledException

import clr

clr.AddReference("System")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System import Decimal

from System.Drawing import Point, Size, Font

from System.Windows.Forms import (
    Form,
    Label,
    GroupBox,
    CheckBox,
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
view = doc.ActiveView

FT_TO_MM = 304.8

DIMENSION_OFFSET_MM = 600.0
PARALLEL_TOLERANCE = 0.99939

# Crop alignment is always enabled
CROP_ALIGNMENT_ENABLED = True


# ============================================================
# SELECTION FILTER
# ============================================================

class GridSelectionFilter(ISelectionFilter):

    def AllowElement(self, element):
        return isinstance(element, Grid)

    def AllowReference(self, reference, point):
        return True


# ============================================================
# VIEW COORDINATES
# ============================================================

def get_screen_coordinates(point):

    return (
        point.DotProduct(view.RightDirection),
        point.DotProduct(view.UpDirection)
    )


def project_to_view(point):

    normal = view.ViewDirection.Normalize()

    distance = (
        point - view.Origin
    ).DotProduct(normal)

    return point - normal.Multiply(distance)


# ============================================================
# CROP REGION INFORMATION
# ============================================================

def get_crop_data():

    if not view.CropBoxActive:

        raise Exception(
            "Crop View is not enabled.\n\n"
            "Please enable Crop View and try again."
        )

    crop = view.CropBox

    if crop is None:
        raise Exception("Crop Box could not be read.")

    points = []

    for x in (crop.Min.X, crop.Max.X):

        for y in (crop.Min.Y, crop.Max.Y):

            for z in (crop.Min.Z, crop.Max.Z):

                point = crop.Transform.OfPoint(
                    XYZ(x, y, z)
                )

                points.append(
                    project_to_view(point)
                )

    screen_points = [
        get_screen_coordinates(p)
        for p in points
    ]

    xs = [p[0] for p in screen_points]
    ys = [p[1] for p in screen_points]

    bounds = (
        min(xs),
        min(ys),
        max(xs),
        max(ys)
    )

    return bounds, points


# ============================================================
# GET GRID CURVE
# ============================================================

def get_grid_curve(grid):

    # First try view-specific curve
    try:

        curves = grid.GetCurvesInView(
            DatumExtentType.ViewSpecific,
            view
        )

        if curves and curves.Count > 0:
            return curves[0]

    except:
        pass

    # Then try model extent curve
    try:

        curves = grid.GetCurvesInView(
            DatumExtentType.Model,
            view
        )

        if curves and curves.Count > 0:
            return curves[0]

    except:
        pass

    try:
        return grid.Curve
    except:
        return None


# ============================================================
# GET GRID TYPE
# ============================================================

def classify_grid(direction):

    dx = abs(
        direction.DotProduct(
            view.RightDirection
        )
    )

    dy = abs(
        direction.DotProduct(
            view.UpDirection
        )
    )

    tolerance = 0.0874887  # Approximately 5 degrees

    if dx <= dy * tolerance:
        return "vertical"

    if dy <= dx * tolerance:
        return "horizontal"

    return "inclined"


# ============================================================
# FIND CROP INTERSECTIONS
# ============================================================

def get_line_crop_intersections(
    p0,
    direction,
    bounds
):

    x0, y0 = get_screen_coordinates(p0)

    dx = direction.DotProduct(
        view.RightDirection
    )

    dy = direction.DotProduct(
        view.UpDirection
    )

    xmin, ymin, xmax, ymax = bounds

    intersections = []

    tolerance = 0.0001

    # Left and right crop boundaries
    if abs(dx) > 0.0000001:

        for boundary_x in (xmin, xmax):

            t = (boundary_x - x0) / dx

            y = y0 + t * dy

            if (
                ymin - tolerance
                <= y
                <= ymax + tolerance
            ):

                intersections.append(t)

    # Top and bottom crop boundaries
    if abs(dy) > 0.0000001:

        for boundary_y in (ymin, ymax):

            t = (boundary_y - y0) / dy

            x = x0 + t * dx

            if (
                xmin - tolerance
                <= x
                <= xmax + tolerance
            ):

                intersections.append(t)

    # Remove duplicate intersections
    unique = []

    for t in intersections:

        if not any(
            abs(t - old) < 0.000001
            for old in unique
        ):

            unique.append(t)

    if len(unique) < 2:
        return None

    unique.sort()

    return unique[0], unique[-1]


# ============================================================
# EXTEND GRID TO CROP + EXTENSION DISTANCE
# ============================================================

def extend_grid_to_crop(grid, bounds, extension_mm):

    if not CROP_ALIGNMENT_ENABLED:
        return None

    curve = get_grid_curve(grid)

    if not isinstance(curve, Line):
        return None

    p0 = curve.GetEndPoint(0)
    p1 = curve.GetEndPoint(1)

    vector = p1 - p0

    if vector.GetLength() < 0.000001:
        return None

    direction = vector.Normalize()

    intersections = get_line_crop_intersections(
        p0,
        direction,
        bounds
    )

    if intersections is None:
        return None

    t_min, t_max = intersections

    extension_ft = extension_mm / FT_TO_MM

    # Extend both ends outside crop boundary
    start = p0 + direction.Multiply(
        t_min - extension_ft
    )

    end = p0 + direction.Multiply(
        t_max + extension_ft
    )

    if start.DistanceTo(end) < 0.000001:
        return None

    # Set view-specific datum extents
    grid.SetDatumExtentType(
        DatumEnds.End0,
        view,
        DatumExtentType.ViewSpecific
    )

    grid.SetDatumExtentType(
        DatumEnds.End1,
        view,
        DatumExtentType.ViewSpecific
    )

    new_curve = Line.CreateBound(
        start,
        end
    )

    grid.SetCurveInView(
        DatumExtentType.ViewSpecific,
        view,
        new_curve
    )

    return start, end, direction


# ============================================================
# SET GRID BUBBLES
# ============================================================

def set_grid_bubbles(
    grid,
    endpoints,
    direction,
    settings
):

    start, end = endpoints

    x0, y0 = get_screen_coordinates(start)
    x1, y1 = get_screen_coordinates(end)

    grid_type = classify_grid(direction)

    if grid_type == "vertical":

        first_end = (
            DatumEnds.End0
            if y0 >= y1
            else DatumEnds.End1
        )

        second_end = (
            DatumEnds.End1
            if y0 >= y1
            else DatumEnds.End0
        )

        options = (
            settings["vertical_top"],
            settings["vertical_bottom"]
        )

    elif grid_type == "horizontal":

        first_end = (
            DatumEnds.End0
            if x0 <= x1
            else DatumEnds.End1
        )

        second_end = (
            DatumEnds.End1
            if x0 <= x1
            else DatumEnds.End0
        )

        options = (
            settings["horizontal_left"],
            settings["horizontal_right"]
        )

    else:

        first_end = (
            DatumEnds.End0
            if y0 >= y1
            else DatumEnds.End1
        )

        second_end = (
            DatumEnds.End1
            if y0 >= y1
            else DatumEnds.End0
        )

        options = (
            settings["inclined_top"],
            settings["inclined_bottom"]
        )

    # If neither option selected, preserve existing bubbles
    if not any(options):
        return True

    if options[0]:
        grid.ShowBubbleInView(first_end, view)
    else:
        grid.HideBubbleInView(first_end, view)

    if options[1]:
        grid.ShowBubbleInView(second_end, view)
    else:
        grid.HideBubbleInView(second_end, view)

    return True


# ============================================================
# GET ALL GRIDS IN ACTIVE VIEW
# ============================================================

def get_all_grids():

    collector = (
        FilteredElementCollector(doc, view.Id)
        .OfClass(Grid)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    return list(collector)


# ============================================================
# GET SELECTED GRIDS
# ============================================================

def get_selected_grids():

    selected_ids = list(
        uidoc.Selection.GetElementIds()
    )

    grids = []

    if selected_ids:

        for element_id in selected_ids:

            element = doc.GetElement(element_id)

            if isinstance(element, Grid):
                grids.append(element)

    if grids:
        return grids

    references = uidoc.Selection.PickObjects(
        ObjectType.Element,
        GridSelectionFilter(),
        "Select grids and click Finish."
    )

    for reference in references:

        element = doc.GetElement(
            reference.ElementId
        )

        if isinstance(element, Grid):
            grids.append(element)

    return grids


# ============================================================
# DIMENSION GRID INFORMATION
# ============================================================

def get_dimension_data(grids):

    data = []

    for grid in grids:

        try:

            curve = get_grid_curve(grid)

            if not isinstance(curve, Line):
                continue

            p0 = curve.GetEndPoint(0)
            p1 = curve.GetEndPoint(1)

            direction = (
                p1 - p0
            ).Normalize()

            # Project direction into view plane
            normal_view = view.ViewDirection.Normalize()

            direction = (
                direction
                -
                normal_view.Multiply(
                    direction.DotProduct(normal_view)
                )
            )

            if direction.GetLength() < 0.000001:
                continue

            direction = direction.Normalize()

            # Canonical direction
            right_dot = direction.DotProduct(
                view.RightDirection
            )

            up_dot = direction.DotProduct(
                view.UpDirection
            )

            if (
                right_dot < -0.000001
                or (
                    abs(right_dot) < 0.000001
                    and up_dot < 0
                )
            ):

                direction = direction.Negate()

            midpoint = (
                p0 + p1
            ).Multiply(0.5)

            data.append({

                "grid": grid,
                "direction": direction,
                "midpoint": midpoint

            })

        except:
            continue

    return data


# ============================================================
# GROUP PARALLEL GRIDS
# ============================================================

def group_parallel_grids(data):

    groups = []

    for item in data:

        added = False

        for group in groups:

            reference_direction = (
                group[0]["direction"]
            )

            dot = abs(
                reference_direction.DotProduct(
                    item["direction"]
                )
            )

            if dot >= PARALLEL_TOLERANCE:

                group.append(item)

                added = True

                break

        if not added:
            groups.append([item])

    return groups


# ============================================================
# CREATE ADJACENT GRID DIMENSIONS
# ============================================================

def create_grid_dimensions(grids, crop_points):

    # Dimensions are attempted in all supported views.
    # Revit may reject a particular grid/reference combination;
    # the caller records that as a dimension warning.

    data = get_dimension_data(grids)

    groups = group_parallel_grids(data)

    created = 0
    failed = 0

    dimension_offset = (
        DIMENSION_OFFSET_MM / FT_TO_MM
    )

    for group in groups:

        if len(group) < 2:
            continue

        try:

            direction = group[0]["direction"]

            normal = (
                view.ViewDirection.CrossProduct(
                    direction
                ).Normalize()
            )

            base = group[0]["midpoint"]

            # Position of each grid along normal
            for item in group:

                item["position"] = (
                    item["midpoint"] - base
                ).DotProduct(normal)

            group.sort(
                key=lambda item: item["position"]
            )

            # References
            references = ReferenceArray()

            for item in group:

                references.Append(
                    Reference(item["grid"])
                )

            # Find maximum crop coordinate along grid direction
            crop_positions = [

                (point - base).DotProduct(direction)

                for point in crop_points

            ]

            max_crop_position = max(
                crop_positions
            )

            # Dimension line inside crop
            line_position = (
                max_crop_position - dimension_offset
            )

            margin = 1.0

            first_position = (
                group[0]["position"] - margin
            )

            last_position = (
                group[-1]["position"] + margin
            )

            start = (
                base
                +
                direction.Multiply(line_position)
                +
                normal.Multiply(first_position)
            )

            end = (
                base
                +
                direction.Multiply(line_position)
                +
                normal.Multiply(last_position)
            )

            dimension_line = Line.CreateBound(
                start,
                end
            )

            dimension = doc.Create.NewDimension(
                view,
                dimension_line,
                references
            )

            if dimension is not None:
                created += 1
            else:
                failed += 1

        except:
            failed += 1

    return created, failed


# ============================================================
# USER DIALOG
# ============================================================

def show_dialog():

    form = Form()

    form.Text = "MEP Tools - Grid Annotation"

    form.Size = Size(440, 510)

    form.StartPosition = FormStartPosition.CenterScreen

    form.FormBorderStyle = FormBorderStyle.FixedDialog

    form.MaximizeBox = False
    form.MinimizeBox = False

    form.Font = Font("Arial", 9)

    # --------------------------------------------------------
    # GRID BUBBLE GROUP
    # --------------------------------------------------------

    main_group = GroupBox()

    main_group.Text = "Grid Bubble"

    main_group.Location = Point(15, 15)
    main_group.Size = Size(400, 275)

    form.Controls.Add(main_group)

    # VERTICAL
    label = Label()

    label.Text = "Vertical Grids"
    label.Location = Point(18, 28)
    label.Size = Size(150, 22)

    main_group.Controls.Add(label)

    vertical_top = CheckBox()

    vertical_top.Text = "Top"
    vertical_top.Location = Point(18, 55)
    vertical_top.Size = Size(120, 25)

    main_group.Controls.Add(vertical_top)

    vertical_bottom = CheckBox()

    vertical_bottom.Text = "Bottom"
    vertical_bottom.Location = Point(205, 55)
    vertical_bottom.Size = Size(140, 25)

    main_group.Controls.Add(vertical_bottom)

    # HORIZONTAL
    label = Label()

    label.Text = "Horizontal Grids"
    label.Location = Point(18, 100)
    label.Size = Size(150, 22)

    main_group.Controls.Add(label)

    horizontal_left = CheckBox()

    horizontal_left.Text = "Left"
    horizontal_left.Location = Point(18, 127)
    horizontal_left.Size = Size(120, 25)

    main_group.Controls.Add(horizontal_left)

    horizontal_right = CheckBox()

    horizontal_right.Text = "Right"
    horizontal_right.Location = Point(205, 127)
    horizontal_right.Size = Size(140, 25)

    main_group.Controls.Add(horizontal_right)

    # INCLINED
    label = Label()

    label.Text = "Inclined Grids"
    label.Location = Point(18, 172)
    label.Size = Size(150, 22)

    main_group.Controls.Add(label)

    inclined_top = CheckBox()

    inclined_top.Text = "Top"
    inclined_top.Location = Point(18, 199)
    inclined_top.Size = Size(120, 25)

    main_group.Controls.Add(inclined_top)

    inclined_bottom = CheckBox()

    inclined_bottom.Text = "Bottom"
    inclined_bottom.Location = Point(205, 199)
    inclined_bottom.Size = Size(140, 25)

    main_group.Controls.Add(inclined_bottom)

    # NOTE
    note = Label()

    note.Text = (
        "Inclined Grids: Top = Maximum Y, "
        "Bottom = Minimum Y."
    )

    note.Location = Point(18, 230)
    note.Size = Size(365, 35)

    main_group.Controls.Add(note)

    # --------------------------------------------------------
    # DIMENSION OPTION
    # --------------------------------------------------------

    dimension_check = CheckBox()

    dimension_check.Text = "Include Dimension"

    dimension_check.Location = Point(20, 300)
    dimension_check.Size = Size(250, 25)

    form.Controls.Add(dimension_check)

    # --------------------------------------------------------
    # EXTENSION DISTANCE
    # --------------------------------------------------------

    extension_label = Label()

    extension_label.Text = "Extension Distance:"

    extension_label.Location = Point(20, 345)
    extension_label.Size = Size(145, 25)

    form.Controls.Add(extension_label)

    extension_input = NumericUpDown()

    extension_input.Location = Point(165, 342)
    extension_input.Size = Size(155, 25)

    extension_input.Minimum = Decimal(0)
    extension_input.Maximum = Decimal(10000)

    extension_input.Increment = Decimal(50)
    extension_input.Value = Decimal(300)

    form.Controls.Add(extension_input)

    unit_label = Label()

    unit_label.Text = "mm"

    unit_label.Location = Point(325, 345)
    unit_label.Size = Size(40, 22)

    form.Controls.Add(unit_label)

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    all_button = Button()

    all_button.Text = "Annotate All"

    all_button.Location = Point(20, 405)
    all_button.Size = Size(180, 40)

    all_button.DialogResult = DialogResult.Yes

    form.Controls.Add(all_button)

    selected_button = Button()

    selected_button.Text = "Annotate Select Only"

    selected_button.Location = Point(210, 405)
    selected_button.Size = Size(195, 40)

    selected_button.DialogResult = DialogResult.No

    form.Controls.Add(selected_button)

    cancel_button = Button()

    cancel_button.Text = "Cancel"

    cancel_button.Location = Point(330, 455)
    cancel_button.Size = Size(75, 25)

    cancel_button.DialogResult = DialogResult.Cancel

    form.Controls.Add(cancel_button)

    form.AcceptButton = all_button
    form.CancelButton = cancel_button

    result = form.ShowDialog()

    if result not in (
        DialogResult.Yes,
        DialogResult.No
    ):
        return None

    return {

        "vertical_top": vertical_top.Checked,
        "vertical_bottom": vertical_bottom.Checked,

        "horizontal_left": horizontal_left.Checked,
        "horizontal_right": horizontal_right.Checked,

        "inclined_top": inclined_top.Checked,
        "inclined_bottom": inclined_bottom.Checked,

        "dimensions": dimension_check.Checked,

        "extension_mm": float(extension_input.Value),

        "annotate_all": (
            result == DialogResult.Yes
        )
    }


# ============================================================
# MAIN EXECUTION
# ============================================================

try:

    # STEP 1 - CHECK VIEW

    supported_view_types = (
        "FloorPlan",
        "CeilingPlan",
        "Elevation",
        "Section"
    )

    if view.ViewType.ToString() not in supported_view_types:

        raise Exception(
            "Please open a Floor Plan, Ceiling Plan, "
            "Elevation, or Section view."
        )

    # STEP 2 - READ CROP

    crop_bounds, crop_points = get_crop_data()

    # STEP 3 - SHOW DIALOG

    settings = show_dialog()

    if settings is not None:

        # STEP 4 - GET GRIDS

        if settings["annotate_all"]:

            grids = get_all_grids()

        else:

            grids = get_selected_grids()

        if not grids:

            raise Exception(
                "No grids found in the active view or selection."
            )

        # STEP 5 - TRANSACTION

        transaction = Transaction(
            doc,
            "BALA MEP SUITE - Grid Annotation V3"
        )

        transaction.Start()

        try:

            crop_aligned = 0
            bubble_updated = 0
            failed = 0

            # STEP 6 - EXTEND GRIDS AND PLACE BUBBLES

            for grid in grids:

                try:

                    result = extend_grid_to_crop(
                        grid,
                        crop_bounds,
                        settings["extension_mm"]
                    )

                    if result is None:
                        continue

                    start, end, direction = result

                    crop_aligned += 1

                    if set_grid_bubbles(
                        grid,
                        (start, end),
                        direction,
                        settings
                    ):

                        bubble_updated += 1

                except:

                    failed += 1

            # STEP 7 - DIMENSIONS

            dimension_count = 0
            dimension_failed = 0

            if settings["dimensions"]:

                (
                    dimension_count,
                    dimension_failed
                ) = create_grid_dimensions(
                    grids,
                    crop_points
                )

            # STEP 8 - COMMIT

            transaction.Commit()

        except:

            transaction.RollBack()
            raise

        # NO SUCCESS POPUP
        # WARNING POPUP ONLY IF OPERATIONS FAILED

        if failed > 0 or dimension_failed > 0:

            forms.alert(

                "GRID ANNOTATION COMPLETED WITH WARNINGS\n\n"

                "Total grids: {}\n"
                "Crop aligned: {}\n"
                "Bubble updated: {}\n"
                "Grid warnings: {}\n"
                "Dimensions created: {}\n"
                "Dimension warnings: {}".format(

                    len(grids),
                    crop_aligned,
                    bubble_updated,
                    failed,
                    dimension_count,
                    dimension_failed
                ),

                title="MEP TOOLS - Grid Annotation"
            )


except OperationCanceledException:

    pass


except Exception as error:

    forms.alert(

        "GRID ANNOTATION ERROR:\n\n{}".format(error),

        title="MEP TOOLS - Error"
    )
