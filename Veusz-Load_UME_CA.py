# ##### BEGIN GPL LICENCE BLOCK #####
#  Copyright (C) 2023  Arthur Langlard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENCE BLOCK #####


# Author: Arthur Langlard, arthur.langlard@univ-nantes.fr
# Start of the project: 06-02-2023
# Last modification: 06-02-2023
#
# This software is a plugin for the Veusz software.



import veusz.plugins as plugins

class LoadUMEfilesPlugin(plugins.ToolsPlugin):
    """Load all files related to an experiment of vesicles nano-impacts at
    a ultramicroelectrode (UME).
    This comprises chronoamperometry (CA) an cyclic voltametry (CV) files."""

    # a tuple of strings building up menu to place plugin on
    menu = ('Load UME files',)
    # unique name for plugin
    name = 'Load UME files'

    # name to appear on status tool bar
    description_short = 'Load files related to an experiment of vesicles nano-impacts at a ultramicroelectrode.'
    # text to appear in dialog box
    description_full = 'Load files related to an experiment of vesicles nano-impacts at a ultramicroelectrode.'

    def __init__(self):
        """Make list of fields."""
        self.fields = [ 
            plugins.FieldFilename("filename_start", descr="First file"),
            plugins.FieldInt("nb_files", descr="Number of files", default=1, minval=1),
            ]

    def apply(self, interface, fields):
        """Do the work of the plugin.
        interface: veusz command line interface object (exporting commands)
        fields: dict mapping field names to values
        """

        nb_files = fields['nb_files']

        # String content: "C:/----/experiment_ca05_C01.mpt"
        filepath_start = fields['filename_start']
        
        # String content: "C:/----/"
        filepath_prefix = "/".join(filepath_start.split("/")[:-1]) + "/"    # Get the directory of the file.

        # String content: "experiment_ca05_C01.mpt"
        filename_suffix_start = filepath_start.split('/')[-1]               # Remove all the path (containing /) to keep the filename.

        # String content: "C:/----/experiment_ca05"
        filename_start = "_".join(filename_suffix_start.split("_")[:-1])    # Remove the "_Cxxxx.mpt" at the end.

        # String content: "C:/----/experiment_ca"
        filename_root = filename_start[:-2]                                 # Get the root name by removing the no of the experiment.
        
        # String content: "C01.mpt"
        filename_suffix = filename_suffix_start.split("_")[-1]              # Get the "Cxxxx.mpt" at the end.

        # Int content: 05
        start_no = int(filename_start[-2:])                                 # Split the name at the dash _ and remove the 2 characters "ca".

        filepaths = [filepath_prefix + filename_root + f"{i + start_no:02d}" + "_" + filename_suffix for i in range(nb_files)]


        pluginargs = {
            'extract_cycles': False, 'extract_steps': False, 'import_all_data': True,
            'change_surface': False, 'surface': 1.0, 'surface_unit': "cm2",
            'change_mass': False, 'mass': 1.0, 'mass_unit': "mg"}

        # Import every file from (filepath_start) to (filepath_start + nb_files)
        for i in range(nb_files):
            interface.ImportFilePlugin(
                'EC-LAB CA',
                filepath_prefix + filename_root + f"{i + start_no:02d}" + "_" + filename_suffix,
                **pluginargs,
                linked=True,
                encoding='utf_8',
                prefix=filepath_start + "_" + f"{i + start_no:02d}",
                suffix='',
                renames={})


plugins.toolspluginregistry.append(LoadUMEfilesPlugin)