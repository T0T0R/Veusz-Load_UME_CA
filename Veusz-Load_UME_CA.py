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
# Last modification: 08-02-2023
#
# This software is a plugin for the Veusz software.


import numpy
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
    description_short = 'Load files related to an experiment of vesicles nano-impacts at an ultramicroelectrode.'
    # text to appear in dialog box
    description_full = 'Load files related to an experiment of vesicles nano-impacts at an ultramicroelectrode.'

    def __init__(self):
        """Make list of fields."""
        self.fields = [ 
            plugins.FieldFilename('filename_start', descr="First file"),
            plugins.FieldInt('nb_files', descr="Number of files", default=1, minval=1),
            plugins.FieldCombo('current_unit', descr="Unit for current", default='nA', items=('mA', 'uA', 'nA', 'pA')),
            plugins.FieldTextMulti('ref', descr="ref"),
            plugins.FieldInt('spread_size', descr="Width of current change", default=10, minval=4),
            plugins.FieldColormap('colormap', descr="Colormap of the curves", default="spectrum2"),
            plugins.FieldBool('invert_colormap', descr="Invert colormap", default=False),
            ]

    def apply(self, interface, fields):
        """Do the work of the plugin.
        interface: veusz command line interface object (exporting commands)
        fields: dict mapping field names to values
        """
        # List content: ["experiment_ca05", "experiment_ca07"]
        experiments_black = list(filter(None, fields['ref']))

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



        pluginargs = {
            'extract_cycles': False, 'extract_steps': False, 'import_all_data': True,
            'change_surface': False, 'surface': 1.0, 'surface_unit': "cm2",
            'change_mass': False, 'mass': 1.0, 'mass_unit': "mg"}
        
        # Set color on all curves except the ones selected as references.
        cvals = interface.GetColormap(
                                        fields['colormap'],
                                        invert=fields['invert_colormap'],
                                        nvals = max(1, nb_files-len(experiments_black)))

        # For some reason, the colormap generates transparent black if onlys one point is aksed.
        if nb_files-len(experiments_black) == 1 and cvals[0,0]==0 and cvals[0,1]==0 and cvals[0,2]==0 and cvals[0,3]==0:
            cvals[0,:] = [0,0,0,255] # so generate opaque black instead.
        
        # color_generator gives the next color each time next(color_generator) is called.
        color_generator = (color for color in cvals)


        interface.To('page1'); interface.To('graph1'); 

        # Import every file from (filepath_start) to (filepath_start + nb_files)
        for i in range(nb_files):
            interface.ImportFilePlugin(
                'EC-LAB CA',
                filepath_prefix + filename_root + f"{i + start_no:02d}" + "_" + filename_suffix,
                **pluginargs,
                linked = True,
                encoding = 'utf_8',
                prefix = filename_root + f"{i + start_no:02d}" + "_",
                suffix = '',
                renames = {})

            self.create_I_change_dataset(interface, filename_root + f"{i + start_no:02d}" + "_I Range", fields['spread_size'])

            # Create a new dataset with current with the convenient unit.
            current_mA_np = interface.GetData(filename_root + f"{i + start_no:02d}" + "_<I>/mA")[0]

            if fields['current_unit']=='mA':
                current_unit_np = current_mA_np
                current_unit_str = "mA"
            elif fields['current_unit']=='uA':
                current_unit_np = 1e3 * current_mA_np
                current_unit_str = "uA"
            elif fields['current_unit']=='nA':
                current_unit_np = 1e6 * current_mA_np
                current_unit_str = "nA"
            elif fields['current_unit']=='pA':
                current_unit_np = 1e9 * current_mA_np
                current_unit_str = "pA"
                
        
            interface.SetData(
                                filename_root + f"{i + start_no:02d}" + "_<I>/" + current_unit_str,
                                current_unit_np,
                                symerr=None, negerr=None, poserr=None)
 

            # If the xy plot does not already exist, create it.
            if not (filename_root + f"{i + start_no:02d}" in interface.GetChildren(where='.')):
                interface.Add('xy', name=filename_root + f"{i + start_no:02d}", autoadd=False)
            
            interface.To(filename_root + f"{i + start_no:02d}")
            interface.Set('marker', 'none')
            interface.Set('xData', filename_root + f"{i + start_no:02d}" + "_time/s")
            interface.Set('yData', filename_root + f"{i + start_no:02d}" + "_<I>/" + current_unit_str)


            if not (filename_root + f"{i + start_no:02d}" in experiments_black):                
                color = next(color_generator)
                if color[3] == 255:
                    # opaque
                    col = "#%02x%02x%02x" % (color[0], color[1], color[2])
                else:
                    # with transparency
                    col = "#%02x%02x%02x%02x" % (color[0], color[1], color[2], color[3])
            else:
                col = "#000000ff"

            interface.Set('color', col)





            interface.To('..')

            self.create_I_masked_plots(
                                        interface,
                                        filename_root + f"{i + start_no:02d}" + "_<I>/" + current_unit_str,
                                        filename_root + f"{i + start_no:02d}" + "_time/s",
                                        filename_root + f"{i + start_no:02d}" + "_I Range_change_M")


    

    def create_I_masked_plots(self, interface, dataset_I_full_str, dataset_t_full_str, dataset_I_mask_full_str,):
        """Create the multiple datasets from the splitting of the original dataset, according to 
        the mask provided.
        dataset_I_full_str is the name of the Y-dataset to split.
        dataset_t_full_str is the name of the X-dataset to split.
        dataset_I_mask_full_str is th name of mask dataset.
        Return nothing.
        """
        dataset_I_full = interface.GetData(dataset_I_full_str)[0]
        dataset_t_full = interface.GetData(dataset_t_full_str)[0]
        # The mask is longer than the dataset, so trim it at the end:
        dataset_I_mask_full = interface.GetData(dataset_I_mask_full_str)[0][:len(dataset_I_full)]

        dataset_It_full = numpy.column_stack((dataset_I_full, dataset_t_full, dataset_I_mask_full))
        datasets_It_list = []
        # [(I0,t0,m0)   [(I0,t0,m0)    [(I0,t0,m0)
        #  (I1,t1,m1)    (I1,t1,m1)],   (I1,t1,m1)
        #  (I2,t2,m2)                   (I2,t2,m2)]
        #  (I3,t3,m3)],

        

        dataset_It = []
        temp_dataset = True
        for data_slice in dataset_It_full:          #   For every value of current/time
            if data_slice[2] == 1:                  # if it is not masked
                dataset_It.append(data_slice[:2])   # add it to the temporary dataset.
                temp_dataset = True
            elif temp_dataset:                                          #   If it is masked, the temporary dataset
                if len(dataset_It) > 0:
                    datasets_It_list.append(numpy.stack(dataset_It))    # is done and added to the list of datasets.
                dataset_It = []                                         # The temporary dataset is reset.
                temp_dataset = False
        
        if len(dataset_It) > 0:                                 # If there are still values at the end that are
            datasets_It_list.append(numpy.stack(dataset_It))    # not masked, the temporary dataset is added.
        


        for no_dataset, dataset_It in enumerate(datasets_It_list):
            interface.SetData(dataset_I_full_str + "_" + str(no_dataset), dataset_It[:,0], symerr=None, negerr=None, poserr=None)
            interface.SetData(dataset_t_full_str + "_" + str(no_dataset), dataset_It[:,1], symerr=None, negerr=None, poserr=None)






    def create_I_change_dataset(self, interface, I_range_dataset_str, spread_size=10):
        """Create a dataset which can be used as a mask to hide current values
        when the current range changes.
        I_range_dataset_str is the name of the dataset containing the current ranges.
        spread_size is the number of values to be masked after a current range change.
        Return nothing.
        """

        I_range_dataset_np = interface.GetData(I_range_dataset_str)[0]

        # Converts [56,56,56,57,57,57,57,58] to [0,0,0,1,0,0,0,1]
        I_change_dataset = numpy.diff(I_range_dataset_np)

        # Convolution of punctual changes in I_range (Dirac comb) with a window function
        # (Bartlett window, triangular shape, faster to compute) to spread the changes of the current range
        # over time (tweaked by $spread_size).
        # This convolution increases the size of the dataset and the maxima are shifted of $spread_size / 2
        # from the dirac comb peaks:
        #
        # $I_change_dataset:     _____|_____|_________|______________|_
        # numpy.bartlett:        _/\_
        # convolution:           ______/\____/\________/\_____________/\_
        #
        # This shift is not an issue because this dataset is used to mask artifacts caused BY this current
        # change, and so are happening later.

        I_change_dataset_spread = numpy.convolve(I_change_dataset, numpy.bartlett(spread_size))
        
        interface.SetData(I_range_dataset_str + "_change", I_change_dataset_spread, symerr=None, negerr=None, poserr=None)

        # Creating a mask from the convoluted dataset:
        #
        # convolution:           ______/\____/\________/\_____________/\_
        # mask:                  ‾‾‾‾‾‾__‾‾‾‾__‾‾‾‾‾‾‾‾__‾‾‾‾‾‾‾‾‾‾‾‾‾__‾

        interface.SetData(I_range_dataset_str + "_change_M", numpy.logical_not(numpy.ma.make_mask(I_change_dataset_spread)), symerr=None, negerr=None, poserr=None)

    


plugins.toolspluginregistry.append(LoadUMEfilesPlugin)