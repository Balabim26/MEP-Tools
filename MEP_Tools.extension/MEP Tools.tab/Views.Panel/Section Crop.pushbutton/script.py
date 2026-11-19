# ============================================================
# MEP TOOLS - SECTION CROP
# UI UPDATE - KEEPING THE WORKING CROP CALCULATION
# Created by BALA
# AI-assisted development with OpenAI
# Revit 2024.3 | pyRevit 6.4
# ============================================================

__title__ = "Section\nCrop"
__author__ = "BALA"
__doc__ = (
    "Adjust Section and Elevation crop boundaries using "
    "selected bottom and top levels with independent offsets.\n\n"
    "Created by BALA\n"
    "AI-assisted development with OpenAI"
)

from pyrevit import revit, script
import math
from Autodesk.Revit.DB import (
    FilteredElementCollector, Level, ViewSection, ViewType, XYZ,
    BoundingBoxXYZ, Transaction, SubTransaction, TransactionStatus,
    IFailuresPreprocessor, FailureProcessingResult, FailureSeverity
)

import clr
clr.AddReference("System")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

from System.Drawing import Point, Size, Font, FontStyle, Color
from System.Windows.Forms import (
    Form, Label, ComboBox, ComboBoxStyle, Button,
    DialogResult, FormStartPosition, FormBorderStyle, Panel,
    TextBox, ScrollBars, BorderStyle, FlatStyle
)

doc = revit.doc
uidoc = revit.uidoc
MM_TO_FEET = 1.0 / 304.8

# ---------------- UI THEME: LEVEL ANNOTATION MATCH ----------------
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


# ============================================================
# CUSTOM MESSAGE WINDOW - NO forms.alert()
# ============================================================

def show_tool_message(title, heading, details, is_error=True):
    form = Form()
    form.Text = title
    form.Size = Size(470, 365)
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False
    form.BackColor = PALE_BLUE
    form.Font = Font("Segoe UI", 9)

    title_label = Label()
    title_label.Text = "SECTION CROP"
    title_label.Location = Point(22, 22)
    title_label.Size = Size(410, 30)
    title_label.ForeColor = DARK_BLUE
    title_label.Font = Font("Segoe UI", 16, FontStyle.Bold)
    form.Controls.Add(title_label)

    subtitle = Label()
    subtitle.Text = "MEP TOOLS  |  " + ("ERROR DETAILS" if is_error else "RESULT DETAILS")
    subtitle.Location = Point(23, 54)
    subtitle.Size = Size(410, 20)
    subtitle.ForeColor = MUTED
    subtitle.Font = Font("Segoe UI", 8)
    form.Controls.Add(subtitle)

    card = Panel()
    card.Location = Point(18, 88)
    card.Size = Size(418, 205)
    card.BackColor = WHITE
    card.BorderStyle = BorderStyle.FixedSingle
    form.Controls.Add(card)

    heading_label = Label()
    heading_label.Text = heading
    heading_label.Location = Point(17, 16)
    heading_label.Size = Size(380, 27)
    heading_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
    heading_label.ForeColor = RED if is_error else DARK_BLUE
    card.Controls.Add(heading_label)

    details_box = TextBox()
    details_box.Location = Point(16, 53)
    details_box.Size = Size(382, 133)
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
    close_button.Location = Point(326, 305)
    close_button.Size = Size(110, 34)
    close_button.BackColor = BLUE
    close_button.ForeColor = WHITE
    close_button.FlatStyle = FlatStyle.Flat
    close_button.FlatAppearance.BorderSize = 0
    close_button.DialogResult = DialogResult.OK
    form.Controls.Add(close_button)
    form.AcceptButton = close_button
    form.ShowDialog()


# ============================================================
# HELPERS
# ============================================================

def is_section_or_elevation(view):
    try:
        return (
            isinstance(view, ViewSection)
            and view.ViewType in (ViewType.Section, ViewType.Elevation)
            and not view.IsTemplate
        )
    except:
        return False


def get_project_levels():
    # Convert the .NET collector result to a Python list before sorting.
    levels = list(
        FilteredElementCollector(doc)
        .OfClass(Level)
        .ToElements()
    )
    levels.sort(key=lambda level: level.Elevation)
    return levels


# ============================================================
# SECTION CROP INPUT WINDOW
# ============================================================

def show_settings_dialog(levels):
    form = Form()
    form.Text = "Section Crop"
    form.Size = Size(530, 555)
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False
    form.BackColor = PALE_BLUE
    form.Font = Font("Segoe UI", 9)

    # Main heading - matching Level Annotation.
    title_label = Label()
    title_label.Text = "SECTION CROP"
    title_label.Location = Point(28, 24)
    title_label.Size = Size(455, 32)
    title_label.ForeColor = DARK_BLUE
    title_label.Font = Font("Segoe UI", 16, FontStyle.Bold)
    form.Controls.Add(title_label)

    subtitle = Label()
    subtitle.Text = "View and vertical crop region settings"
    subtitle.Location = Point(29, 57)
    subtitle.Size = Size(455, 22)
    subtitle.ForeColor = MUTED
    subtitle.Font = Font("Segoe UI", 9)
    form.Controls.Add(subtitle)

    # White settings card.
    card = Panel()
    card.Location = Point(20, 91)
    card.Size = Size(474, 350)
    card.BackColor = WHITE
    card.BorderStyle = BorderStyle.FixedSingle
    form.Controls.Add(card)

    def add_section_heading(text, y):
        label = Label()
        label.Text = text
        label.Location = Point(18, y)
        label.Size = Size(430, 22)
        label.ForeColor = DARK_BLUE
        label.Font = Font("Segoe UI", 9, FontStyle.Bold)
        card.Controls.Add(label)

    def add_separator(y):
        line = Panel()
        line.Location = Point(18, y)
        line.Size = Size(435, 1)
        line.BackColor = BORDER
        card.Controls.Add(line)

    def add_field_label(parent, text, x, y, width=205):
        label = Label()
        label.Text = text
        label.Location = Point(x, y)
        label.Size = Size(width, 20)
        label.ForeColor = TEXT_COLOR
        label.Font = Font("Segoe UI", 8)
        parent.Controls.Add(label)
        return label

    def style_combo(combo):
        combo.Font = Font("Segoe UI", 9)
        combo.BackColor = WHITE
        combo.ForeColor = TEXT_COLOR
        combo.DropDownStyle = ComboBoxStyle.DropDownList
        return combo

    # VIEW SCOPE
    add_section_heading("VIEW SCOPE", 17)
    add_field_label(card, "Target Views", 18, 43, 120)

    scope_combo = ComboBox()
    scope_combo.Location = Point(18, 64)
    scope_combo.Size = Size(435, 27)
    style_combo(scope_combo)
    scope_combo.Items.Add("Current View")
    scope_combo.Items.Add("All Section / Elevation Views")
    scope_combo.SelectedIndex = (
        0 if is_section_or_elevation(doc.ActiveView) else 1
    )
    card.Controls.Add(scope_combo)

    add_separator(105)

    # LEVEL RANGE
    add_section_heading("LEVEL RANGE", 119)
    add_field_label(card, "Bottom Level", 18, 145, 205)
    add_field_label(card, "Top Level", 242, 145, 205)

    bottom_combo = ComboBox()
    bottom_combo.Location = Point(18, 166)
    bottom_combo.Size = Size(205, 27)
    style_combo(bottom_combo)

    top_combo = ComboBox()
    top_combo.Location = Point(242, 166)
    top_combo.Size = Size(211, 27)
    style_combo(top_combo)

    for level in levels:
        elevation_mm = level.Elevation * 304.8
        display = "{} ({:.0f} mm)".format(level.Name, elevation_mm)
        bottom_combo.Items.Add(display)
        top_combo.Items.Add(display)

    bottom_combo.SelectedIndex = 0
    top_combo.SelectedIndex = len(levels) - 1
    card.Controls.Add(bottom_combo)
    card.Controls.Add(top_combo)

    add_separator(207)

    # CROP OFFSETS - side-by-side like Level Annotation.
    add_section_heading("CROP OFFSETS (mm)", 220)
    add_field_label(card, "Bottom Offset", 18, 247, 205)
    add_field_label(card, "Top Offset", 242, 247, 205)

    # TextBox is used instead of NumericUpDown so the default displays
    # as a clean "0" while users can still enter decimals when needed.
    bottom_offset_input = TextBox()
    bottom_offset_input.Location = Point(18, 269)
    bottom_offset_input.Size = Size(205, 29)
    bottom_offset_input.Text = "0"
    bottom_offset_input.Font = Font("Segoe UI", 9)
    bottom_offset_input.BackColor = WHITE
    bottom_offset_input.ForeColor = TEXT_COLOR
    bottom_offset_input.BorderStyle = BorderStyle.FixedSingle
    card.Controls.Add(bottom_offset_input)

    top_offset_input = TextBox()
    top_offset_input.Location = Point(242, 269)
    top_offset_input.Size = Size(211, 29)
    top_offset_input.Text = "0"
    top_offset_input.Font = Font("Segoe UI", 9)
    top_offset_input.BackColor = WHITE
    top_offset_input.ForeColor = TEXT_COLOR
    top_offset_input.BorderStyle = BorderStyle.FixedSingle
    card.Controls.Add(top_offset_input)

    helper = Label()
    helper.Text = "Use 0 for no offset. Decimals are allowed (e.g. 125.5 mm)."
    helper.Location = Point(18, 311)
    helper.Size = Size(435, 20)
    helper.ForeColor = MUTED
    helper.Font = Font("Segoe UI", 8)
    card.Controls.Add(helper)

    # Validation text stays in this same window.
    validation_label = Label()
    validation_label.Text = ""
    validation_label.Location = Point(23, 445)
    validation_label.Size = Size(470, 22)
    validation_label.ForeColor = RED
    validation_label.Font = Font("Segoe UI", 8, FontStyle.Bold)
    form.Controls.Add(validation_label)

    # Footer buttons - same grey Cancel / blue Apply treatment.
    cancel_button = Button()
    cancel_button.Text = "CANCEL"
    cancel_button.Location = Point(20, 473)
    cancel_button.Size = Size(110, 35)
    cancel_button.BackColor = Color.FromArgb(226, 226, 226)
    cancel_button.ForeColor = TEXT_COLOR
    cancel_button.FlatStyle = FlatStyle.Flat
    cancel_button.FlatAppearance.BorderColor = BORDER
    form.Controls.Add(cancel_button)

    apply_button = Button()
    apply_button.Text = "APPLY"
    apply_button.Location = Point(384, 473)
    apply_button.Size = Size(110, 35)
    apply_button.BackColor = BLUE
    apply_button.ForeColor = WHITE
    apply_button.Font = Font("Segoe UI", 9, FontStyle.Bold)
    apply_button.FlatStyle = FlatStyle.Flat
    apply_button.FlatAppearance.BorderSize = 0
    form.Controls.Add(apply_button)

    form.CancelButton = cancel_button

    # Store validated numeric offsets for the result tuple.
    offset_values = [0.0, 0.0]

    def on_apply(sender, args):
        validation_label.Text = ""

        if bottom_combo.SelectedIndex < 0:
            validation_label.Text = "Please select a Bottom Level."
            return

        if top_combo.SelectedIndex < 0:
            validation_label.Text = "Please select a Top Level."
            return

        bottom_level = levels[bottom_combo.SelectedIndex]
        top_level = levels[top_combo.SelectedIndex]

        if bottom_level.Elevation >= top_level.Elevation:
            validation_label.Text = (
                "Bottom Level must be lower than Top Level."
            )
            return

        try:
            bottom_offset_value = float(
                bottom_offset_input.Text.strip().replace(",", ".") or "0"
            )
            top_offset_value = float(
                top_offset_input.Text.strip().replace(",", ".") or "0"
            )
        except:
            validation_label.Text = (
                "Enter valid offset values. Use 0 or a decimal such as 125.5."
            )
            return

        if (
            math.isnan(bottom_offset_value)
            or math.isinf(bottom_offset_value)
            or math.isnan(top_offset_value)
            or math.isinf(top_offset_value)
        ):
            validation_label.Text = "Enter finite numeric offset values."
            return

        if abs(bottom_offset_value) > 100000 or abs(top_offset_value) > 100000:
            validation_label.Text = "Offset values must be between -100000 and 100000 mm."
            return

        if (
            scope_combo.SelectedIndex == 0
            and not is_section_or_elevation(doc.ActiveView)
        ):
            validation_label.Text = (
                "Current View is not a Section or Elevation view. "
                "Choose All Section / Elevation Views."
            )
            return

        offset_values[0] = bottom_offset_value
        offset_values[1] = top_offset_value
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
        scope_combo.SelectedIndex,
        bottom_combo.SelectedIndex,
        top_combo.SelectedIndex,
        offset_values[0],
        offset_values[1]
    )


# ============================================================
# CROP CALCULATION - PRESERVED
# ============================================================

def update_view_crop(
    view, bottom_elevation, top_elevation,
    bottom_offset_mm, top_offset_mm
):
    crop_box = view.CropBox
    if crop_box is None:
        raise Exception("Crop box is not available.")

    transform = crop_box.Transform
    inverse_transform = transform.Inverse

    bottom_local = inverse_transform.OfPoint(
        XYZ(0, 0, bottom_elevation)
    )
    top_local = inverse_transform.OfPoint(
        XYZ(0, 0, top_elevation)
    )

    bottom_offset_ft = bottom_offset_mm * MM_TO_FEET
    top_offset_ft = top_offset_mm * MM_TO_FEET

    new_min_y = bottom_local.Y - bottom_offset_ft
    new_max_y = top_local.Y + top_offset_ft

    if new_min_y >= new_max_y:
        raise Exception(
            "Invalid crop height. Check levels and offsets."
        )

    new_box = BoundingBoxXYZ()
    new_box.Transform = transform
    new_box.Min = XYZ(
        crop_box.Min.X, new_min_y, crop_box.Min.Z
    )
    new_box.Max = XYZ(
        crop_box.Max.X, new_max_y, crop_box.Max.Z
    )
    new_box.Enabled = crop_box.Enabled
    view.CropBox = new_box


# ============================================================
# TARGET VIEWS
# ============================================================

def get_target_views(scope_index):
    if scope_index == 0:
        active_view = doc.ActiveView
        if not is_section_or_elevation(active_view):
            raise Exception(
                "Current View is not a Section or Elevation view."
            )
        return [active_view]

    views = list(
        FilteredElementCollector(doc)
        .OfClass(ViewSection)
        .ToElements()
    )

    result = [
        view for view in views
        if is_section_or_elevation(view)
    ]
    result.sort(key=lambda view: view.Name.lower())
    return result


# ============================================================
# REVIT FAILURE HANDLER
# Routes transaction warnings/errors to our own message window.
# ============================================================

class SectionCropFailureHandler(IFailuresPreprocessor):
    def __init__(self):
        self.messages = []
        self.has_errors = False

    def PreprocessFailures(self, failures_accessor):
        try:
            for failure in failures_accessor.GetFailureMessages():
                description = failure.GetDescriptionText()
                severity = failure.GetSeverity()

                if description:
                    self.messages.append(description)

                if severity == FailureSeverity.Warning:
                    # Warning is recorded and displayed afterwards
                    # in the MEP TOOLS message window.
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
# MAIN EXECUTION
# ============================================================

try:
    levels = get_project_levels()
    if len(levels) < 2:
        raise Exception(
            "At least two project Levels are required."
        )

    settings = show_settings_dialog(levels)
    if settings is None:
        script.exit()

    (
        scope_index, bottom_index, top_index,
        bottom_offset_mm, top_offset_mm
    ) = settings

    bottom_level = levels[bottom_index]
    top_level = levels[top_index]

    if bottom_level.Elevation >= top_level.Elevation:
        show_tool_message(
            "Section Crop - Input Check",
            "Check the selected levels",
            "Bottom Level must be lower than Top Level.",
            True
        )
        script.exit()

    bottom_elevation = bottom_level.Elevation
    top_elevation = top_level.Elevation

    target_views = get_target_views(scope_index)
    if not target_views:
        raise Exception(
            "No Section / Elevation views were found."
        )

    transaction = Transaction(doc, "MEP Tools - Section Crop")
    failure_handler = SectionCropFailureHandler()

    transaction.Start()

    options = transaction.GetFailureHandlingOptions()
    options.SetFailuresPreprocessor(failure_handler)
    options.SetClearAfterRollback(True)
    transaction.SetFailureHandlingOptions(options)

    success_count = 0
    view_failures = []

    try:
        for view in target_views:
            sub_transaction = SubTransaction(doc)
            sub_transaction.Start()

            try:
                update_view_crop(
                    view,
                    bottom_elevation,
                    top_elevation,
                    bottom_offset_mm,
                    top_offset_mm
                )
                sub_transaction.Commit()
                success_count += 1

            except Exception as view_error:
                try:
                    sub_transaction.RollBack()
                except:
                    pass
                view_failures.append(
                    "{}: {}".format(view.Name, view_error)
                )

        commit_status = transaction.Commit()

    except:
        try:
            if transaction.GetStatus() == TransactionStatus.Started:
                transaction.RollBack()
        except:
            pass
        raise

    if (
        commit_status == TransactionStatus.RolledBack
        or failure_handler.has_errors
    ):
        issue_text = "\n".join(failure_handler.messages)
        if not issue_text:
            issue_text = (
                "Revit could not complete the Section Crop operation. "
                "The transaction was rolled back."
            )

        show_tool_message(
            "Section Crop - Operation Failed",
            "The crop changes were not committed",
            issue_text,
            True
        )

    else:
        report_items = []

        if view_failures:
            report_items.append("Views that could not be updated:")
            report_items.extend(view_failures[:12])
            if len(view_failures) > 12:
                report_items.append(
                    "...and {} more view errors.".format(
                        len(view_failures) - 12
                    )
                )

        if failure_handler.messages:
            report_items.append("")
            report_items.append("Revit warnings:")
            report_items.extend(failure_handler.messages[:12])

        if report_items:
            show_tool_message(
                "Section Crop - Completed with Notes",
                "{} view(s) updated; some items need attention".format(
                    success_count
                ),
                "\n".join(report_items),
                False
            )

    # No success popup when no issues occur.

except Exception as error:
    show_tool_message(
        "Section Crop - Error",
        "Section Crop could not complete",
        str(error),
        True
    )
