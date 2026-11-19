
# -*- coding: utf-8 -*-

# ============================================================
# MEP TOOLS - ABOUT WINDOW
# Created by BALA
# Autodesk Revit 2024.3 | pyRevit 6.4
# ============================================================

from pyrevit import forms

__title__ = "About"
__author__ = "BALA"
__doc__ = "About MEP TOOLS"


XAML = """
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="About MEP TOOLS"
    Width="620"
    Height="390"
    WindowStyle="None"
    AllowsTransparency="True"
    Background="Transparent"
    ResizeMode="NoResize"
    ShowInTaskbar="False"
    WindowStartupLocation="CenterScreen">

    <Border
        Background="#FFFFFF"
        CornerRadius="16"
        Margin="12">

        <Border.Effect>
            <DropShadowEffect
                Color="#26364A"
                BlurRadius="25"
                ShadowDepth="5"
                Opacity="0.20"/>
        </Border.Effect>

        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="8"/>
                <RowDefinition Height="55"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="75"/>
            </Grid.RowDefinitions>

            <!-- TOP ACCENT -->
            <Border
                Grid.Row="0"
                Background="#176CC0"
                CornerRadius="16,16,0,0"/>

            <!-- HEADER -->
            <Grid Grid.Row="1" Margin="25,0,20,0">

                <StackPanel
                    Orientation="Horizontal"
                    VerticalAlignment="Center">

                    <TextBlock
                        Text="MEP"
                        FontSize="19"
                        FontWeight="Bold"
                        Foreground="#176CC0"/>

                    <TextBlock
                        Text=" TOOLS"
                        FontSize="19"
                        FontWeight="Bold"
                        Foreground="#20344F"/>

                </StackPanel>

                <Button
                    Content="X"
                    Width="32"
                    Height="32"
                    HorizontalAlignment="Right"
                    VerticalAlignment="Center"
                    Background="Transparent"
                    BorderThickness="0"
                    Foreground="#64748B"
                    FontSize="17"
                    Cursor="Hand"
                    Click="close_clicked"/>

            </Grid>

            <!-- MAIN CONTENT -->
            <Grid Grid.Row="2" Margin="25,12,25,15">

                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="165"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <!-- LOGO -->
                <Border
                    Grid.Column="0"
                    Width="140"
                    Height="155"
                    Background="#F0F6FD"
                    CornerRadius="14"
                    VerticalAlignment="Center">

                    <Grid>

                        <Path
                            Data="M 15,105 L 62,18 L 109,105 L 87,105 L 62,59 L 37,105 Z"
                            Fill="#176CC0"
                            Stretch="Uniform"
                            Width="95"
                            Height="95"
                            HorizontalAlignment="Center"
                            VerticalAlignment="Center"/>

                    </Grid>

                </Border>

                <!-- PRODUCT INFORMATION -->
                <StackPanel
                    Grid.Column="1"
                    VerticalAlignment="Center"
                    Margin="18,0,0,0">

                    <TextBlock
                        Text="MEP TOOLS"
                        FontSize="27"
                        FontWeight="Bold"
                        Foreground="#20344F"/>

                    <TextBlock
                        Text="Intelligent Tools for MEP Engineering"
                        FontSize="13"
                        Foreground="#176CC0"
                        Margin="0,6,0,0"/>

                    <TextBlock
                        Text="A professional collection of productivity tools for MEP design, modelling, annotation and documentation workflows in Autodesk Revit."
                        FontSize="12"
                        Foreground="#64748B"
                        TextWrapping="Wrap"
                        LineHeight="19"
                        Margin="0,15,0,12"/>

                    <Border
                        Background="#EFF6FF"
                        CornerRadius="5"
                        Padding="9"
                        HorizontalAlignment="Left">

                        <TextBlock
                            Text="AUTODESK REVIT 2024.3  |  pyRevit 6.4"
                            FontSize="10"
                            FontWeight="SemiBold"
                            Foreground="#176CC0"/>

                    </Border>

                </StackPanel>

            </Grid>

            <!-- FOOTER -->
            <Border
                Grid.Row="3"
                Background="#F8FAFC"
                CornerRadius="0,0,16,16"
                Padding="25,10">

                <Grid>

                    <StackPanel
                        VerticalAlignment="Center">

                        <TextBlock
                            Text="Created by BALA"
                            FontSize="12"
                            FontWeight="Bold"
                            Foreground="#20344F"/>

                        <TextBlock
                            Text="AI-assisted development with OpenAI"
                            FontSize="10"
                            Foreground="#8290A0"
                            Margin="0,4,0,0"/>

                    </StackPanel>

                    <Button
                        Content="CLOSE"
                        Width="95"
                        Height="35"
                        Background="#176CC0"
                        Foreground="White"
                        FontWeight="SemiBold"
                        BorderThickness="0"
                        Cursor="Hand"
                        HorizontalAlignment="Right"
                        VerticalAlignment="Center"
                        Click="close_clicked"/>

                </Grid>

            </Border>

        </Grid>

    </Border>

</Window>
"""


class AboutWindow(forms.WPFWindow):

    def __init__(self):
        forms.WPFWindow.__init__(
            self,
            XAML,
            literal_string=True
        )

    def close_clicked(self, sender, args):
        self.Close()


try:
    window = AboutWindow()
    window.show_dialog()

except Exception as error:
    forms.alert(
        "Unable to open About window:\n\n{}".format(error),
        title="MEP TOOLS"
    )
