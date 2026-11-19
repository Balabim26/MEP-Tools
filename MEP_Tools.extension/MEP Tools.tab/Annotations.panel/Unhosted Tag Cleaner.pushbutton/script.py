
# -*- coding: utf-8 -*-

# ============================================================
# MEP TOOLS - UNHOSTED TAG CLEANER
# Revit 2020+ | pyRevit
# Created by BALA
# ============================================================

from pyrevit import revit, forms

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    IndependentTag,
    Transaction
)

from System import TimeSpan
from System.Windows import Visibility
from System.Windows.Threading import DispatcherTimer

__title__ = "Unhosted Tag\nCleaner"
__author__ = "BALA"


# ============================================================
# MAIN WINDOW
# ============================================================

MAIN_XAML = """
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Unhosted Tag Cleaner"
    Width="420"
    Height="390"
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
                Text="UNHOSTED TAG CLEANER"
                FontSize="20"
                FontWeight="Bold"
                Foreground="#20344F"/>

            <TextBlock
                Text="Find and manage orphaned Revit tags"
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

                <!-- SEARCH SCOPE -->

                <TextBlock
                    Text="SEARCH SCOPE"
                    FontWeight="Bold"
                    Foreground="#20344F"
                    FontSize="12"
                    Margin="0,0,0,12"/>

                <RadioButton
                    x:Name="CurrentView"
                    Content="Current View"
                    GroupName="Scope"
                    IsChecked="True"
                    Margin="0,0,0,10"/>

                <RadioButton
                    x:Name="EntireProject"
                    Content="Entire Project"
                    GroupName="Scope"
                    Margin="0,0,0,15"/>

                <Separator/>

                <!-- ACTION -->

                <TextBlock
                    Text="ACTION"
                    FontWeight="Bold"
                    Foreground="#20344F"
                    FontSize="12"
                    Margin="0,15,0,12"/>

                <RadioButton
                    x:Name="CountTags"
                    Content="Count Orphaned Tags"
                    GroupName="Action"
                    IsChecked="True"
                    Margin="0,0,0,10"/>

                <RadioButton
                    x:Name="DeleteTags"
                    Content="Delete Orphaned Tags"
                    GroupName="Action"
                    Margin="0,0,0,10"/>

                <Border
                    Background="#EFF6FF"
                    CornerRadius="6"
                    Padding="10"
                    Margin="0,12,0,0">

                    <TextBlock
                        Text="Count mode reports orphaned tags. Delete mode removes only orphaned tags."
                        Foreground="#1768AE"
                        FontSize="10"
                        TextWrapping="Wrap"/>

                </Border>

            </StackPanel>

        </Border>

        <!-- FOOTER -->

        <Grid Grid.Row="2" Margin="0,12,0,0">

            <Button
                Content="CANCEL"
                Width="95"
                Height="34"
                HorizontalAlignment="Left"
                Click="cancel_clicked"/>

            <Button
                Content="RUN"
                Width="110"
                Height="34"
                HorizontalAlignment="Right"
                Background="#176CC0"
                Foreground="White"
                FontWeight="Bold"
                Click="run_clicked"/>

        </Grid>

    </Grid>

</Window>
"""


# ============================================================
# RESULT WINDOW
# ============================================================

RESULT_XAML = """
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="MEP TOOLS"
    Width="390"
    Height="205"
    WindowStartupLocation="CenterScreen"
    ResizeMode="NoResize"
    Background="#F4F7FB"
    ShowInTaskbar="False">

    <Grid Margin="16">

        <Grid.RowDefinitions>
            <RowDefinition Height="7"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="42"/>
        </Grid.RowDefinitions>

        <!-- TOP ACCENT -->

        <Border
            Grid.Row="0"
            Background="#176CC0"
            CornerRadius="4"/>

        <!-- RESULT CONTENT -->

        <Border
            Grid.Row="1"
            Background="White"
            CornerRadius="8"
            Padding="18">

            <StackPanel VerticalAlignment="Center">

                <TextBlock
                    x:Name="ResultTitle"
                    Text="ORPHAN TAG REPORT"
                    FontSize="16"
                    FontWeight="Bold"
                    Foreground="#20344F"
                    HorizontalAlignment="Center"
                    TextAlignment="Center"/>

                <TextBlock
                    x:Name="ResultMessage"
                    Text="0 Orphaned Tags Found"
                    FontSize="15"
                    FontWeight="SemiBold"
                    Foreground="#176CC0"
                    TextAlignment="Center"
                    TextWrapping="Wrap"
                    Margin="0,15,0,0"/>

            </StackPanel>

        </Border>

        <!-- CLOSE BUTTON -->

        <Button
            x:Name="CloseButton"
            Grid.Row="2"
            Content="CLOSE"
            Width="90"
            Height="30"
            HorizontalAlignment="Right"
            Background="#176CC0"
            Foreground="White"
            FontWeight="SemiBold"
            BorderThickness="0"
            Click="close_clicked"/>

    </Grid>

</Window>
"""


# ============================================================
# MAIN WINDOW CLASS
# ============================================================

class OrphanTagWindow(forms.WPFWindow):

    def __init__(self):

        forms.WPFWindow.__init__(
            self,
            MAIN_XAML,
            literal_string=True
        )

        self.result = None

    def cancel_clicked(self, sender, args):

        self.result = None
        self.Close()

    def run_clicked(self, sender, args):

        self.result = {

            "scope": (
                "current"
                if self.FindName("CurrentView").IsChecked
                else "project"
            ),

            "action": (
                "count"
                if self.FindName("CountTags").IsChecked
                else "delete"
            )

        }

        self.Close()


# ============================================================
# RESULT WINDOW CLASS
# ============================================================

class ResultWindow(forms.WPFWindow):

    def __init__(
        self,
        title,
        message,
        auto_close=False
    ):

        forms.WPFWindow.__init__(
            self,
            RESULT_XAML,
            literal_string=True
        )

        self.timer = None

        self.FindName("ResultTitle").Text = title
        self.FindName("ResultMessage").Text = message

        if auto_close:

            self.FindName("CloseButton").Visibility = (
                Visibility.Collapsed
            )

            self.timer = DispatcherTimer()
            self.timer.Interval = TimeSpan.FromSeconds(2)
            self.timer.Tick += self.timer_tick
            self.timer.Start()

        else:

            self.FindName("CloseButton").Visibility = (
                Visibility.Visible
            )

    def timer_tick(self, sender, args):

        if self.timer:
            self.timer.Stop()

        self.Close()

    def close_clicked(self, sender, args):

        if self.timer:
            self.timer.Stop()

        self.Close()


def show_result(title, message, auto_close=False):

    result_window = ResultWindow(
        title,
        message,
        auto_close
    )

    result_window.show_dialog()


# ============================================================
# DOCUMENT
# ============================================================

doc = revit.doc
uidoc = revit.uidoc
view = doc.ActiveView


# ============================================================
# MAIN EXECUTION
# ============================================================

try:

    # --------------------------------------------------------
    # STEP 1 - SHOW MAIN WINDOW
    # --------------------------------------------------------

    window = OrphanTagWindow()
    window.show_dialog()

    settings = window.result

    if settings is None:
        raise SystemExit


    # --------------------------------------------------------
    # STEP 2 - COLLECT TAGS
    # --------------------------------------------------------

    if settings["scope"] == "current":

        tags = list(
            FilteredElementCollector(
                doc,
                view.Id
            )
            .OfClass(IndependentTag)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        scope_name = view.Name

    else:

        tags = list(
            FilteredElementCollector(doc)
            .OfClass(IndependentTag)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        scope_name = "Entire Project"


    # --------------------------------------------------------
    # STEP 3 - FIND ORPHANED TAGS
    # --------------------------------------------------------

    orphan_ids = []
    valid_count = 0
    errors = []

    for tag in tags:

        try:

            if tag.IsOrphaned:

                orphan_ids.append(tag.Id)

            else:

                valid_count += 1

        except Exception as error:

            errors.append(
                "Tag {}: {}".format(
                    tag.Id,
                    str(error)
                )
            )


    orphan_count = len(orphan_ids)


    # --------------------------------------------------------
    # STEP 4 - COUNT MODE
    # --------------------------------------------------------

    if settings["action"] == "count":

        show_result(
            "ORPHAN TAG REPORT",
            "{} Orphaned Tags Found".format(
                orphan_count
            ),
            auto_close=False
        )


    # --------------------------------------------------------
    # STEP 5 - DELETE MODE
    # --------------------------------------------------------

    else:

        if orphan_count == 0:

            show_result(
                "ORPHAN TAG REPORT",
                "No Orphaned Tags Found",
                auto_close=True
            )

        else:

            confirmation = forms.alert(

                "DELETE ORPHANED TAGS?\n\n"
                "Search Scope: {}\n"
                "Orphaned Tags Found: {}\n\n"
                "Only orphaned tags will be deleted.\n"
                "Valid tags will be kept.\n\n"
                "Do you want to continue?".format(
                    scope_name,
                    orphan_count
                ),

                title="MEP TOOLS - Confirm Deletion",
                yes=True,
                no=True
            )

            if confirmation:

                deleted_count = 0
                failed_count = 0

                transaction = Transaction(
                    doc,
                    "MEP TOOLS - Delete Orphaned Tags"
                )

                transaction.Start()

                try:

                    for element_id in orphan_ids:

                        try:

                            doc.Delete(element_id)
                            deleted_count += 1

                        except Exception:

                            failed_count += 1

                    transaction.Commit()

                except Exception:

                    transaction.RollBack()
                    raise


                # ------------------------------------------------
                # DELETE RESULT
                # ------------------------------------------------

                if failed_count == 0:

                    show_result(
                        "DELETION SUCCESSFUL",

                        "{} Orphaned Tags Deleted Successfully".format(
                            deleted_count
                        ),

                        auto_close=True
                    )

                else:

                    show_result(
                        "DELETION COMPLETED WITH WARNINGS",

                        "{} Deleted Successfully\n{} Failed".format(
                            deleted_count,
                            failed_count
                        ),

                        auto_close=False
                    )


except SystemExit:

    pass


except Exception as error:

    forms.alert(
        "UNHOSTED TAG CLEANER ERROR:\n\n{}".format(
            error
        ),
        title="MEP TOOLS - Error"
    )
