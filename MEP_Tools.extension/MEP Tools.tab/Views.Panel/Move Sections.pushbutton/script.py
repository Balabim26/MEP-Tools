# ============================================================
# MEP TOOLS - MOVE SECTION TO OTHER LEVEL
# Created by BALA
# AI-assisted development with OpenAI
#
# Revit 2024.3 | pyRevit 6.4
#
# FUNCTION:
# 1. Select From View (level-based plan view)
# 2. Select To View (level-based plan view)
# 3. Calculate level elevation difference
# 4. Move crop-region shape of all Section views by that Z distance
# 5. Exclude view templates and non-Section views
# 6. Custom MEP TOOLS UI and error messages
# ============================================================

__title__ = "Move Section\nTo Level"
__author__ = "BALA"
__doc__ = (
    "Move all Section view crop regions vertically using "
    "the level difference between two selected plan views.\n\n"
    "Created by BALA\n"
    "AI-assisted development with OpenAI"
)

from pyrevit import revit

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewPlan,
    ViewSection,
    ViewType,
    XYZ,
    Transform,
    CurveLoop,
    Transaction,
    SubTransaction,
    TransactionStatus,
    IFailuresPreprocessor,
    FailureProcessingResult,
    FailureSeverity
)

import clr
clr.AddReference("System")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Point, Size, Font, FontStyle, Color
from System.Windows.Forms import (
    Form,
    Label,
    ComboBox,
    ComboBoxStyle,
    Button,
    DialogResult,
    FormStartPosition,
    FormBorderStyle,
    Panel,
    TextBox,
    ScrollBars,
    BorderStyle,
    FlatStyle
)


# ============================================================
# DOCUMENT AND UI THEME
# ============================================================

doc = revit.doc
uidoc = revit.uidoc

BLUE = Color.FromArgb(35, 112, 190)
DARK_BLUE = Color.FromArgb(25, 66, 112)
LIGHT_BLUE = Color.FromArgb(241, 246, 252)
PALE_BLUE = Color.FromArgb(246, 248, 251)
TEXT_COLOR = Color.FromArgb(31, 52, 78)
MUTED = Color.FromArgb(100, 117, 139)
BORDER = Color.FromArgb(205, 214, 225)
WHITE = Color.White
RED = Color.FromArgb(190, 48, 48)
PALE_RED = Color.FromArgb(255, 243, 243)
GREEN = Color.FromArgb(35, 125, 85)
PALE_GREEN = Color.FromArgb(238, 248, 242)


# ============================================================
# CUSTOM MESSAGE WINDOW
# ============================================================

def show_tool_message(title, heading, details, is_error=True):
    form = Form()
    form.Text = title
    form.Size = Size(490, 385)
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False
    form.BackColor = PALE_BLUE
    form.Font = Font("Segoe UI", 9)

    title_label = Label()
    title_label.Text = "MOVE SECTION TO OTHER LEVEL"
    title_label.Location = Point(22, 22)
    title_label.Size = Size(440, 30)
    title_label.ForeColor = DARK_BLUE
    title_label.Font = Font("Segoe UI", 14, FontStyle.Bold)
    form.Controls.Add(title_label)

    subtitle = Label()
    subtitle.Text = "MEP TOOLS  |  MESSAGE"
    subtitle.Location = Point(23, 55)
    subtitle.Size = Size(430, 20)
    subtitle.ForeColor = MUTED
    subtitle.Font = Font("Segoe UI", 8)
    form.Controls.Add(subtitle)

    card = Panel()
    card.Location = Point(18, 91)
    card.Size = Size(438, 220)
    card.BackColor = WHITE
    card.BorderStyle = BorderStyle.FixedSingle
    form.Controls.Add(card)

    heading_label = Label()
    heading_label.Text = heading
    heading_label.Location = Point(17, 16)
    heading_label.Size = Size(400, 27)
    heading_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
    heading_label.ForeColor = RED if is_error else DARK_BLUE
    card.Controls.Add(heading_label)

    details_box = TextBox()
    details_box.Location = Point(16, 53)
    details_box.Size = Size(402, 150)
    details_box.Multiline = True
    details_box.ReadOnly = True
    details_box.ScrollBars = ScrollBars.Vertical
    details_box.BorderStyle = BorderStyle.FixedSingle
    details_box.BackColor = Color.FromArgb(250, 251, 253)
    details_box.ForeColor = TEXT_COLOR
    details_box.Font = Font("Segoe UI", 9)
    details_box.Text = str(details)
    card.Controls.Add(details_box)

    close_button = Button()
    close_button.Text = "CLOSE"
    close_button.Location = Point(346, 305)
    close_button.Size = Size(110, 32)
    close_button.BackColor = BLUE
    close_button.ForeColor = WHITE
    close_button.FlatStyle = FlatStyle.Flat
    close_button.FlatAppearance.BorderSize = 0
    close_button.DialogResult = DialogResult.OK
    form.Controls.Add(close_button)

    form.AcceptButton = close_button
    form.ShowDialog()


# ============================================================
# FIND LEVEL-BASED PLAN VIEWS
# Only ViewPlan objects with a valid GenLevel are selectable.
# Legends, drafting views, sheets and 3D views are excluded.
# ============================================================

def get_level_plan_views():
    collected = list(
        FilteredElementCollector(doc)
        .OfClass(ViewPlan)
        .ToElements()
    )

    result = []

    for view in collected:
        try:
            if view.IsTemplate:
                continue

            level = view.GenLevel

            if level is None:
                continue

            result.append((view, level))

        except:
            continue

    result.sort(
        key=lambda item: (
            item[1].Elevation,
            item[0].Name.lower()
        )
    )

    return result


# ============================================================
# GET ALL SECTION VIEWS
# ============================================================

def get_section_views():
    collected = list(
        FilteredElementCollector(doc)
        .OfClass(View)
        .ToElements()
    )

    sections = []

    for view in collected:
        try:
            if view.IsTemplate:
                continue

            if view.ViewType == ViewType.Section:
                sections.append(view)

        except:
            continue

    sections.sort(key=lambda item: item.Name.lower())
    return sections


# ============================================================
# SAME THEME INPUT WINDOW
# ============================================================

def show_settings_dialog(plan_views):

    form = Form()
    form.Text = "Move Section to Other Level"
    form.Size = Size(550, 480)
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False
    form.BackColor = PALE_BLUE
    form.Font = Font("Segoe UI", 9)

    # Main title
    title_label = Label()
    title_label.Text = "MOVE SECTION TO OTHER LEVEL"
    title_label.Location = Point(28, 24)
    title_label.Size = Size(480, 32)
    title_label.ForeColor = DARK_BLUE
    title_label.Font = Font("Segoe UI", 15, FontStyle.Bold)
    form.Controls.Add(title_label)

    subtitle = Label()
    subtitle.Text = (
        "Select source and target plan views to shift section crops"
    )
    subtitle.Location = Point(29, 58)
    subtitle.Size = Size(480, 22)
    subtitle.ForeColor = MUTED
    subtitle.Font = Font("Segoe UI", 8)
    form.Controls.Add(subtitle)

    # Main white settings card
    card = Panel()
    card.Location = Point(20, 88)
    card.Size = Size(494, 280)
    card.BackColor = WHITE
    card.BorderStyle = BorderStyle.FixedSingle
    form.Controls.Add(card)

    def add_section_heading(text, y):
        label = Label()
        label.Text = text
        label.Location = Point(18, y)
        label.Size = Size(450, 22)
        label.ForeColor = DARK_BLUE
        label.Font = Font("Segoe UI", 9, FontStyle.Bold)
        card.Controls.Add(label)

    def add_field_label(text, y):
        label = Label()
        label.Text = text
        label.Location = Point(18, y)
        label.Size = Size(450, 20)
        label.ForeColor = TEXT_COLOR
        label.Font = Font("Segoe UI", 8)
        card.Controls.Add(label)

    def add_separator(y):
        line = Panel()
        line.Location = Point(18, y)
        line.Size = Size(455, 1)
        line.BackColor = BORDER
        card.Controls.Add(line)

    def style_combo(combo):
        combo.Font = Font("Segoe UI", 9)
        combo.BackColor = WHITE
        combo.ForeColor = TEXT_COLOR
        combo.DropDownStyle = ComboBoxStyle.DropDownList
        return combo

    # View selection section
    add_section_heading("VIEW SELECTION", 12)

    add_field_label("From View  |  Source Level", 36)
    from_combo = ComboBox()
    from_combo.Location = Point(18, 62)
    from_combo.Size = Size(455, 27)
    style_combo(from_combo)

    add_field_label("To View  |  Target Level", 101)
    to_combo = ComboBox()
    to_combo.Location = Point(18, 127)
    to_combo.Size = Size(455, 27)
    style_combo(to_combo)

    for view, level in plan_views:
        display = "{}   -   {}".format(view.Name, level.Name)
        from_combo.Items.Add(display)
        to_combo.Items.Add(display)

    # Choose active view as From View if it is an eligible plan view.
    active_index = -1
    for index, item in enumerate(plan_views):
        if item[0].Id == doc.ActiveView.Id:
            active_index = index
            break

    if active_index < 0:
        active_index = 0

    from_combo.SelectedIndex = active_index

    # Choose a different level for To View when possible.
    target_index = -1
    source_elevation = plan_views[active_index][1].Elevation

    for index, item in enumerate(plan_views):
        if abs(item[1].Elevation - source_elevation) > 0.000001:
            target_index = index
            break

    if target_index < 0:
        target_index = 1 if len(plan_views) > 1 else 0

    to_combo.SelectedIndex = target_index

    card.Controls.Add(from_combo)
    card.Controls.Add(to_combo)

    add_separator(164)

    # Calculated movement preview
    add_section_heading("LEVEL OFFSET PREVIEW", 176)

    from_level_label = Label()
    from_level_label.Text = "From Level: -"
    from_level_label.Location = Point(18, 204)
    from_level_label.Size = Size(215, 22)
    from_level_label.ForeColor = MUTED
    from_level_label.Font = Font("Segoe UI", 8)
    card.Controls.Add(from_level_label)

    to_level_label = Label()
    to_level_label.Text = "To Level: -"
    to_level_label.Location = Point(248, 204)
    to_level_label.Size = Size(225, 22)
    to_level_label.ForeColor = MUTED
    to_level_label.Font = Font("Segoe UI", 8)
    card.Controls.Add(to_level_label)

    offset_value_label = Label()
    offset_value_label.Text = "Move Distance: 0 mm"
    offset_value_label.Location = Point(18, 231)
    offset_value_label.Size = Size(455, 28)
    offset_value_label.ForeColor = BLUE
    offset_value_label.Font = Font("Segoe UI", 11, FontStyle.Bold)
    card.Controls.Add(offset_value_label)

    helper_label = Label()
    helper_label.Text = (
        "All Section view crop boundaries in this project "
        "will move by the calculated vertical distance."
    )
    helper_label.Location = Point(18, 266)
    helper_label.Size = Size(455, 26)
    helper_label.ForeColor = MUTED
    helper_label.Font = Font("Segoe UI", 8)
    card.Controls.Add(helper_label)

    validation_label = Label()
    validation_label.Text = ""
    validation_label.Location = Point(23, 373)
    validation_label.Size = Size(490, 22)
    validation_label.ForeColor = RED
    validation_label.Font = Font("Segoe UI", 8, FontStyle.Bold)
    form.Controls.Add(validation_label)

    # Update dynamic level and distance preview.
    def update_preview(sender=None, args=None):
        from_index = from_combo.SelectedIndex
        to_index = to_combo.SelectedIndex

        if from_index < 0 or to_index < 0:
            return

        from_view, from_level = plan_views[from_index]
        to_view, to_level = plan_views[to_index]

        delta_ft = to_level.Elevation - from_level.Elevation
        delta_mm = delta_ft * 304.8

        from_level_label.Text = "From Level: {}".format(
            from_level.Name
        )
        to_level_label.Text = "To Level: {}".format(
            to_level.Name
        )

        if delta_mm > 0:
            delta_text = "+{:,.0f} mm".format(delta_mm)
        elif delta_mm < 0:
            delta_text = "{:,.0f} mm".format(delta_mm)
        else:
            delta_text = "0 mm"

        offset_value_label.Text = (
            "Move Distance: {}".format(delta_text)
        )

    from_combo.SelectedIndexChanged += update_preview
    to_combo.SelectedIndexChanged += update_preview
    update_preview()

    # Buttons
    cancel_button = Button()
    cancel_button.Text = "CANCEL"
    cancel_button.Location = Point(20, 397)
    cancel_button.Size = Size(110, 32)
    cancel_button.BackColor = Color.FromArgb(226, 226, 226)
    cancel_button.ForeColor = TEXT_COLOR
    cancel_button.FlatStyle = FlatStyle.Flat
    cancel_button.FlatAppearance.BorderColor = BORDER
    form.Controls.Add(cancel_button)

    apply_button = Button()
    apply_button.Text = "APPLY"
    apply_button.Location = Point(404, 397)
    apply_button.Size = Size(110, 32)
    apply_button.BackColor = BLUE
    apply_button.ForeColor = WHITE
    apply_button.Font = Font("Segoe UI", 9, FontStyle.Bold)
    apply_button.FlatStyle = FlatStyle.Flat
    apply_button.FlatAppearance.BorderSize = 0
    form.Controls.Add(apply_button)

    form.CancelButton = cancel_button

    def on_apply(sender, args):
        validation_label.Text = ""

        if from_combo.SelectedIndex < 0:
            validation_label.Text = "Please select a From View."
            return

        if to_combo.SelectedIndex < 0:
            validation_label.Text = "Please select a To View."
            return

        from_level = plan_views[from_combo.SelectedIndex][1]
        to_level = plan_views[to_combo.SelectedIndex][1]

        delta = to_level.Elevation - from_level.Elevation

        if abs(delta) < 0.000001:
            validation_label.Text = (
                "From View and To View must be on different levels."
            )
            return

        form.DialogResult = DialogResult.OK
        form.Close()

    def on_cancel(sender, args):
        form.DialogResult = DialogResult.Cancel
        form.Close()

    apply_button.Click += on_apply
    cancel_button.Click += on_cancel

    result = form.ShowDialog()

    if result != DialogResult.OK:
        return None

    return (
        from_combo.SelectedIndex,
        to_combo.SelectedIndex
    )


# ============================================================
# MOVE ONE SECTION CROP REGION
# Preserves the original Dynamo algorithm:
# move the first crop-shape loop in global Z.
# ============================================================

def move_section_crop(section_view, offset_z):

    manager = section_view.GetCropRegionShapeManager()
    crop_shapes = manager.GetCropShape()

    if crop_shapes is None or crop_shapes.Count == 0:
        raise Exception("Crop region shape is not available.")

    # Same as original Dynamo: use the first crop boundary loop.
    curves = crop_shapes[0]

    move_transform = Transform.CreateTranslation(
        XYZ(0, 0, offset_z)
    )

    new_curves = []

    for curve in curves:
        new_curve = curve.CreateTransformed(move_transform)
        new_curves.append(new_curve)

    new_loop = CurveLoop.Create(new_curves)
    manager.SetCropShape(new_loop)


# ============================================================
# REVIT FAILURE HANDLER
# Capture transaction warnings/errors for our custom UI.
# ============================================================

class MoveSectionFailureHandler(IFailuresPreprocessor):

    def __init__(self):
        self.messages = []
        self.has_errors = False

    def PreprocessFailures(self, failures_accessor):
        try:
            failure_messages = failures_accessor.GetFailureMessages()

            for failure in failure_messages:
                description = failure.GetDescriptionText()
                severity = failure.GetSeverity()

                if description:
                    self.messages.append(description)

                if severity == FailureSeverity.Warning:
                    failures_accessor.DeleteWarning(failure)

                elif severity == FailureSeverity.Error:
                    self.has_errors = True

            if self.has_errors:
                return FailureProcessingResult.ProceedWithRollBack

            return FailureProcessingResult.Continue

        except Exception as error:
            self.messages.append(
                "Revit failure handler: {}".format(error)
            )
            self.has_errors = True
            return FailureProcessingResult.ProceedWithRollBack


# ============================================================
# MAIN
# ============================================================

def main():

    plan_views = get_level_plan_views()

    if len(plan_views) < 2:
        show_tool_message(
            "Move Section to Other Level - Input",
            "Not enough level-based plan views",
            "At least two plan views with an assigned Level are "
            "required. Legends, Drafting views, Sheets and 3D views "
            "are not valid From / To selections.",
            True
        )
        return

    settings = show_settings_dialog(plan_views)

    if settings is None:
        return

    from_index, to_index = settings

    from_view, from_level = plan_views[from_index]
    to_view, to_level = plan_views[to_index]

    offset_z = to_level.Elevation - from_level.Elevation

    if abs(offset_z) < 0.000001:
        show_tool_message(
            "Move Section to Other Level - Input",
            "No level difference",
            "The selected From View and To View are assigned to "
            "the same elevation. Select views on different levels.",
            True
        )
        return

    sections = get_section_views()

    if not sections:
        show_tool_message(
            "Move Section to Other Level - Result",
            "No Section views found",
            "This project does not contain any non-template "
            "Section views to move.",
            True
        )
        return

    transaction = Transaction(
        doc,
        "MEP Tools - Move Section to Other Level"
    )

    failure_handler = MoveSectionFailureHandler()

    transaction.Start()

    options = transaction.GetFailureHandlingOptions()
    options.SetFailuresPreprocessor(failure_handler)
    options.SetClearAfterRollback(True)
    transaction.SetFailureHandlingOptions(options)

    success_count = 0
    failures = []

    try:
        for section in sections:

            sub_transaction = SubTransaction(doc)
            sub_transaction.Start()

            try:
                move_section_crop(section, offset_z)
                sub_transaction.Commit()
                success_count += 1

            except Exception as view_error:
                try:
                    sub_transaction.RollBack()
                except:
                    pass

                failures.append(
                    "{}: {}".format(section.Name, view_error)
                )

        commit_status = transaction.Commit()

    except:
        try:
            if transaction.GetStatus() == TransactionStatus.Started:
                transaction.RollBack()
        except:
            pass
        raise

    # Revit-level transaction failure.
    if (
        commit_status == TransactionStatus.RolledBack
        or failure_handler.has_errors
    ):
        details = "\n".join(failure_handler.messages)

        if not details:
            details = (
                "Revit rolled back the operation. "
                "No section crop changes were committed."
            )

        show_tool_message(
            "Move Section to Other Level - Error",
            "Section crop movement was rolled back",
            details,
            True
        )
        return

    # Show a report only if some views failed or Revit warnings occurred.
    report = []

    if failures:
        report.append("Sections that could not be moved:")
        report.extend(failures[:15])

        if len(failures) > 15:
            report.append(
                "...and {} more failed Section views.".format(
                    len(failures) - 15
                )
            )

    if failure_handler.messages:
        report.append("")
        report.append("Revit warnings:")
        report.extend(failure_handler.messages[:10])

    if report:
        report.insert(
            0,
            "Moved: {} of {} Section views.\n"
            "From: {} ({})\n"
            "To: {} ({})\n"
            "Vertical movement: {:.3f} mm\n".format(
                success_count,
                len(sections),
                from_view.Name,
                from_level.Name,
                to_view.Name,
                to_level.Name,
                offset_z * 304.8
            )
        )

        show_tool_message(
            "Move Section to Other Level - Report",
            "Operation completed with notes",
            "\n".join(report),
            False
        )

    # No success popup if all Section views were moved successfully.


try:
    main()

except Exception as error:
    show_tool_message(
        "Move Section to Other Level - Error",
        "The tool could not complete the operation",
        str(error),
        True
    )
