
# -*- coding: utf-8 -*-

# ============================================================
# MEP TOOLS - LEVEL ANNOTATION
# Revit 2024.3 | pyRevit 6.4
# Created by BALA
# ============================================================

from pyrevit import revit, forms
from Autodesk.Revit.DB import (
    Level,
    FilteredElementCollector,
    DatumExtentType,
    DatumEnds,
    XYZ,
    Line,
    Transaction
)

__title__ = "Level\nAnnotation"
__author__ = "BALA"


# ============================================================
# USER INTERFACE
# ============================================================

XAML = """
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Level Annotation"
    Width="410"
    Height="440"
    WindowStartupLocation="CenterScreen"
    ResizeMode="NoResize"
    Background="#F4F7FB"
    ShowInTaskbar="False">

    <Grid Margin="18">

        <Grid.RowDefinitions>
            <RowDefinition Height="55"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="55"/>
        </Grid.RowDefinitions>

        <!-- HEADER -->

        <StackPanel Grid.Row="0">

            <TextBlock
                Text="LEVEL ANNOTATION"
                FontSize="20"
                FontWeight="Bold"
                Foreground="#20344F"/>

            <TextBlock
                Text="Level bubble and crop region settings"
                FontSize="11"
                Foreground="#64748B"
                Margin="0,5,0,0"/>

        </StackPanel>

        <!-- MAIN CONTENT -->

        <Border
            Grid.Row="1"
            Background="White"
            CornerRadius="10"
            Padding="18">

            <StackPanel>

                <TextBlock
                    Text="BUBBLE POSITION"
                    FontWeight="Bold"
                    Foreground="#20344F"
                    FontSize="12"
                    Margin="0,0,0,15"/>

                <!-- LEFT AND RIGHT IN SAME ROW -->

                <Grid Margin="0,0,0,18">

                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="*"/>
                    </Grid.ColumnDefinitions>

                    <CheckBox
                        x:Name="LeftBubble"
                        Grid.Column="0"
                        Content="Left Bubble"
                        IsChecked="False"
                        HorizontalAlignment="Left"/>

                    <CheckBox
                        x:Name="RightBubble"
                        Grid.Column="1"
                        Content="Right Bubble"
                        IsChecked="False"
                        HorizontalAlignment="Left"/>

                </Grid>

                <Separator/>

                <TextBlock
                    Text="OFFSET DISTANCE (mm)"
                    FontWeight="Bold"
                    Foreground="#20344F"
                    FontSize="12"
                    Margin="0,15,0,12"/>

                <!-- OFFSET INPUTS -->

                <Grid>

                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="15"/>
                        <ColumnDefinition Width="*"/>
                    </Grid.ColumnDefinitions>

                    <StackPanel Grid.Column="0">

                        <TextBlock
                            Text="Left Offset"
                            Foreground="#536579"
                            FontSize="11"
                            Margin="0,0,0,5"/>

                        <TextBox
                            x:Name="LeftOffset"
                            Text="0"
                            Height="32"
                            Padding="7"/>

                    </StackPanel>

                    <StackPanel Grid.Column="2">

                        <TextBlock
                            Text="Right Offset"
                            Foreground="#536579"
                            FontSize="11"
                            Margin="0,0,0,5"/>

                        <TextBox
                            x:Name="RightOffset"
                            Text="0"
                            Height="32"
                            Padding="7"/>

                    </StackPanel>

                </Grid>

                <Separator Margin="0,18,0,12"/>

                <TextBlock
                    Text="ANNOTATION MODE"
                    FontWeight="Bold"
                    Foreground="#20344F"
                    FontSize="12"
                    Margin="0,0,0,10"/>

                <RadioButton
                    x:Name="AnnotateAll"
                    Content="Annotate All Visible Levels"
                    IsChecked="True"
                    Margin="0,0,0,9"/>

                <RadioButton
                    x:Name="AnnotateSelected"
                    Content="Annotate Selected Levels"/>

                <CheckBox
                    x:Name="IncludeDimension"
                    Content="Include Dimension"
                    Margin="0,17,0,0"/>

            </StackPanel>

        </Border>

        <!-- FOOTER BUTTONS -->

        <Grid Grid.Row="2" Margin="0,12,0,0">

            <Button
                Content="CANCEL"
                Width="95"
                Height="34"
                HorizontalAlignment="Left"
                Click="cancel_clicked"/>

            <Button
                Content="APPLY"
                Width="110"
                Height="34"
                HorizontalAlignment="Right"
                Background="#176CC0"
                Foreground="White"
                FontWeight="Bold"
                Click="apply_clicked"/>

        </Grid>

    </Grid>

</Window>
"""


# ============================================================
# WINDOW CLASS
# ============================================================

class LevelAnnotationWindow(forms.WPFWindow):

    def __init__(self):

        forms.WPFWindow.__init__(
            self,
            XAML,
            literal_string=True
        )

        self.result = None

    def cancel_clicked(self, sender, args):

        self.result = None
        self.Close()

    def apply_clicked(self, sender, args):

        try:

            left_value = float(
                self.FindName("LeftOffset").Text
            )

            right_value = float(
                self.FindName("RightOffset").Text
            )

            if left_value < 0 or right_value < 0:
                forms.alert("Offset values cannot be negative.")
                return

            left = bool(
                self.FindName("LeftBubble").IsChecked
            )

            right = bool(
                self.FindName("RightBubble").IsChecked
            )

            if not left and not right:
                forms.alert(
                    "Please select Left Bubble or Right Bubble."
                )
                return

            self.result = {
                "left": left,
                "right": right,
                "left_offset": left_value,
                "right_offset": right_value,
                "all": bool(
                    self.FindName("AnnotateAll").IsChecked
                ),
                "selected": bool(
                    self.FindName("AnnotateSelected").IsChecked
                ),
                "dimension": bool(
                    self.FindName("IncludeDimension").IsChecked
                )
            }

            self.Close()

        except Exception as error:

            forms.alert(
                "Please enter valid offset values.\n\n{}".format(error)
            )


# ============================================================
# ACTIVE VIEW VALIDATION
# ============================================================

doc = revit.doc
uidoc = revit.uidoc
view = doc.ActiveView

if view.ViewType.ToString() not in ["Elevation", "Section"]:

    forms.alert(
        "Please open an Elevation or Section view.",
        title="MEP TOOLS"
    )

    raise SystemExit


if not view.CropBoxActive:

    forms.alert(
        "Please enable Crop View before using Level Annotation.",
        title="MEP TOOLS"
    )

    raise SystemExit


# ============================================================
# SHOW WINDOW
# ============================================================

window = LevelAnnotationWindow()
window.show_dialog()

settings = window.result

if settings is None:
    raise SystemExit


# ============================================================
# COLLECT LEVELS
# ============================================================

if settings["all"]:

    levels = list(
        FilteredElementCollector(doc, view.Id)
        .OfClass(Level)
        .WhereElementIsNotElementType()
        .ToElements()
    )

else:

    selected_ids = uidoc.Selection.GetElementIds()
    levels = []

    for element_id in selected_ids:

        element = doc.GetElement(element_id)

        if isinstance(element, Level):
            levels.append(element)

    if not levels:

        forms.alert(
            "Please select one or more Levels first.",
            title="MEP TOOLS"
        )

        raise SystemExit


# ============================================================
# CROP REGION CALCULATION
# ============================================================

crop = view.CropBox
transform = crop.Transform

corners = []

for x in [crop.Min.X, crop.Max.X]:

    for y in [crop.Min.Y, crop.Max.Y]:

        for z in [crop.Min.Z, crop.Max.Z]:

            corners.append(
                transform.OfPoint(XYZ(x, y, z))
            )


right_direction = view.RightDirection

right_values = [
    point.DotProduct(right_direction)
    for point in corners
]

crop_left = min(right_values)
crop_right = max(right_values)

left_offset = settings["left_offset"] / 304.8
right_offset = settings["right_offset"] / 304.8


# ============================================================
# APPLY LEVEL ANNOTATION
# ============================================================

failed_levels = []

transaction = Transaction(
    doc,
    "MEP TOOLS - Level Annotation"
)

transaction.Start()

try:

    for level in levels:

        try:

            curves = list(
                level.GetCurvesInView(
                    DatumExtentType.ViewSpecific,
                    view
                )
            )

            if not curves:

                curves = list(
                    level.GetCurvesInView(
                        DatumExtentType.Model,
                        view
                    )
                )

            if not curves:
                failed_levels.append(level.Name)
                continue

            original_curve = curves[0]

            if not isinstance(original_curve, Line):
                failed_levels.append(level.Name)
                continue

            base_point = original_curve.GetEndPoint(0)

            base_right = base_point.DotProduct(
                right_direction
            )

            new_left = crop_left - left_offset
            new_right = crop_right + right_offset

            left_point = (
                base_point +
                right_direction.Multiply(
                    new_left - base_right
                )
            )

            right_point = (
                base_point +
                right_direction.Multiply(
                    new_right - base_right
                )
            )

            new_curve = Line.CreateBound(
                left_point,
                right_point
            )

            level.SetCurveInView(
                DatumExtentType.ViewSpecific,
                view,
                new_curve
            )

            if settings["left"]:

                level.ShowBubbleInView(
                    DatumEnds.End0,
                    view
                )

            else:

                level.HideBubbleInView(
                    DatumEnds.End0,
                    view
                )

            if settings["right"]:

                level.ShowBubbleInView(
                    DatumEnds.End1,
                    view
                )

            else:

                level.HideBubbleInView(
                    DatumEnds.End1,
                    view
                )

        except Exception:

            failed_levels.append(level.Name)

    # ========================================================
    # OPTIONAL DIMENSION
    # ========================================================

    if settings["dimension"]:

        try:

            dimension_levels = sorted(
                levels,
                key=lambda item: item.Elevation
            )

            if len(dimension_levels) >= 2:

                references = __import__(
                    "Autodesk.Revit.DB",
                    fromlist=["ReferenceArray"]
                ).ReferenceArray()

                for item in dimension_levels:

                    references.Append(
                        item.GetPlaneReference()
                    )

                dimension_x = (
                    crop_right +
                    right_offset +
                    (500.0 / 304.8)
                )

                first_level = dimension_levels[0]
                last_level = dimension_levels[-1]

                first_point = (
                    first_level.ProjectElevation *
                    view.UpDirection +
                    dimension_x * right_direction
                )

                last_point = (
                    last_level.ProjectElevation *
                    view.UpDirection +
                    dimension_x * right_direction
                )

                dimension_line = Line.CreateBound(
                    first_point,
                    last_point
                )

                doc.Create.NewDimension(
                    view,
                    dimension_line,
                    references
                )

        except Exception:

            pass

    transaction.Commit()

except Exception as error:

    transaction.RollBack()

    forms.alert(
        "Level Annotation failed:\n\n{}".format(error),
        title="MEP TOOLS"
    )

    raise


# ============================================================
# ERROR MESSAGE ONLY - NO SUCCESS POPUP
# ============================================================

if failed_levels:

    forms.alert(
        "Some Levels could not be annotated:\n\n{}".format(
            ", ".join(failed_levels)
        ),
        title="MEP TOOLS - Level Annotation"
    )
