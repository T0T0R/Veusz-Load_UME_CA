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
# Last modification: 19-03-2023
#
# This software is a plugin for the Veusz software
# (available at https://veusz.github.io/).


import numpy
import veusz.plugins as plugins

class LoadUMEfilesPluginCA(plugins.ToolsPlugin):
    """Load all files related to an experiment of vesicles nano-impacts at
    a ultramicroelectrode (UME).
    This comprises chronoamperometry (CA) files."""

    # a tuple of strings building up menu to place plugin on
    menu = ("Load UME files", "Chronoamperometric measurements")
    # unique name for plugin
    name = "Chronoamperometric measurements"

    # name to appear on status tool bar
    description_short = "Load chronoamperometric files related to an experiment of vesicles nano-impacts at an ultramicroelectrode."
    # text to appear in dialog box
    description_full = description_short
    

    def __init__(self):
        """Make list of fields."""
        self.fields = [ 
            plugins.FieldFilename('filename_start', descr="First file"),
            plugins.FieldInt('nb_files', descr="Number of files", default=1, minval=1),
            plugins.FieldCombo('current_unit', descr="Unit for current", default='nA', items=('mA', 'uA', 'nA', 'pA')),
            plugins.FieldTextMulti('ref', descr="Experiments to remove from the colormap"),
            plugins.FieldBool('load_analysis', descr="Load steps analysis file(s)", default=False),
            plugins.FieldInt('electrode_diam_um', descr="Diameter of the electrode (um)", default=10),
            plugins.FieldInt('spread_size', descr="Width of current change", default=10, minval=4),
            plugins.FieldCombo('dataset_masked_type', descr="Dataset type for masked data", default='Expression dataset', items=('No masked data', 'Expression dataset', '1D dataset')),
            plugins.FieldColormap('colormap', descr="Colormap of the curves", default="spectrum2"),
            plugins.FieldBool('invert_colormap', descr="Invert colormap", default=False),
            ]

    def apply(self, interface, fields):
        """Do the work of the plugin.
        interface: veusz command line interface object (exporting commands)
        fields: dict mapping field names to values
        """
        # List content: ["experiment_ca05", "experiment_ca07"]
        experiments_black = list(filter(None, fields['ref']))   # Remove empty strings, for instance in ["",""]

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

        load_steps_analysis = fields['load_analysis']
        electrode_diam = fields['electrode_diam_um']



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

        if ("page1" in interface.GetChildren(where='/')):
            interface.Root.page1.Remove()

        if not ("page_CA" in interface.GetChildren(where='/')):
            interface.Root.Add('page', name="page_CA")

        # Remove old graph to update all the plotted data:
        if ("graph_CA" in interface.GetChildren(where='/page_CA')):
            interface.Root.page_CA.graph_CA.Remove()
        interface.Root.page_CA.Add('graph', name="graph_CA")


        if load_steps_analysis:
            if not ("page_CA_steps" in interface.GetChildren(where='/')):
                interface.Root.Add('page', name="page_CA_steps")
            
            if ("graph_CA_steps" in interface.GetChildren(where='/page_CA_steps')):
                interface.Root.page_CA_steps.graph_CA_steps.Remove()
            
            if not ("page_CA_steps_size" in interface.GetChildren(where='/')):
                interface.Root.Add('page', name="page_CA_steps_size")
            
            if ("graph_CA_steps_size" in interface.GetChildren(where='/page_CA_steps_size')):
                interface.Root.page_CA_steps_size.graph_CA_steps_size.Remove()
            
        else:
            if ("page_CA_steps" in interface.GetChildren(where='/')):
                interface.Root.page_CA_steps.Remove()

            if ("page_CA_steps_size" in interface.GetChildren(where='/')):
                interface.Root.page_CA_steps_size.Remove()
                


        # Import every file from (filepath_start) to (filepath_start + nb_files)
        for i in range(nb_files):
            experiment_id = filename_root + f"{i + start_no:02d}"

            interface.ImportFilePlugin(
                'EC-LAB CA',
                filepath_prefix + experiment_id + "_" + filename_suffix,
                **pluginargs,
                linked = True,
                encoding = 'utf_8',
                prefix = experiment_id + "_",
                suffix = '',
                renames = {})

            self.create_I_change_dataset(interface, experiment_id + "_I Range", fields['spread_size'])



            if load_steps_analysis:
                # Some files can be absent.
                try:
                    interface.ImportFileCSV(
                    filepath_prefix + experiment_id + "_" + filename_suffix[:-4] + "_sa.csv",
                    delimiter='\t',
                    headermode='1st',
                    linked = True,
                    encoding = 'utf_8',
                    prefix = experiment_id + "_sa",
                    renames = {})
                except:
                    pass





            # Create a new current dataset with the convenient unit.

            if fields['current_unit']=='mA':
                current_unit_str = "mA"
            elif fields['current_unit']=='uA':
                current_unit_str = "uA"
                interface.SetDataExpression(experiment_id + "_<I>/" + current_unit_str,
                                            "`" + experiment_id + "_<I>/mA" + "`*1e3",
                                            linked=True)
            elif fields['current_unit']=='nA':
                current_unit_str = "nA"
                interface.SetDataExpression(experiment_id + "_<I>/" + current_unit_str,
                                            "`" + experiment_id + "_<I>/mA" + "`*1e6",
                                            linked=True)
            elif fields['current_unit']=='pA':
                current_unit_str = "pA"
                interface.SetDataExpression(experiment_id + "_<I>/" + current_unit_str,
                                            "`" + experiment_id + "_<I>/mA" + "`*1e9",
                                            linked=True)
           
           
            # If the xy plot does not already exist, create it.
            if not (experiment_id in interface.GetChildren(where='/page_CA/graph_CA')):
                interface.Root.page_CA.graph_CA.Add('xy', name=experiment_id, autoadd=False)

            interface.Root['page_CA']['graph_CA'][experiment_id].marker.val = 'none'

            interface.Root['page_CA']['graph_CA'][experiment_id].xData.val = experiment_id + "_time/s"
            interface.Root['page_CA']['graph_CA'][experiment_id].yData.val = experiment_id + "_<I>/" + current_unit_str
            
            interface.Root.page_CA.graph_CA.x.MinorTicks.hide.val = True
            interface.Root.page_CA.graph_CA.y.MinorTicks.hide.val = True

            interface.Root.page_CA.graph_CA.x.label.val = "Time (s)"
            interface.Root.page_CA.graph_CA.y.label.val = "Current (" + current_unit_str + ")"

            
            if load_steps_analysis:
                if not ('graph_CA_steps' in interface.GetChildren(where='/page_CA_steps')):
                    interface.Root['page_CA']['graph_CA'].Clone(interface.Root['page_CA_steps'], 'graph_CA_steps')
                
                if not ('graph_CA_steps_size' in interface.GetChildren(where='/page_CA_steps_size')):
                    interface.Root['page_CA']['graph_CA'].Clone(interface.Root['page_CA_steps_size'], 'graph_CA_steps_size')

            


            # Color of the experiments excluded from the colormap
            if not (experiment_id in experiments_black):                
                color = next(color_generator)
                if color[3] == 255:
                    # opaque
                    col = "#%02x%02x%02x" % (color[0], color[1], color[2])
                else:
                    # with transparency
                    col = "#%02x%02x%02x%02x" % (color[0], color[1], color[2], color[3])
            else:
                col = "#000000ff"

            interface.Root['page_CA']['graph_CA'][experiment_id].color.val = col




            if load_steps_analysis:
                if not(i==0):   # The first curve has already been cloned when cloning the graph widget.
                    interface.Root['page_CA']['graph_CA'][experiment_id].Clone(interface.Root['page_CA_steps']['graph_CA_steps'], str(experiment_id))
                    interface.Root['page_CA']['graph_CA'][experiment_id].Clone(interface.Root['page_CA_steps_size']['graph_CA_steps_size'], str(experiment_id))
            
                peaks_time = interface.GetData(experiment_id + "_sa_Time/s")[0]
                peaks_height = interface.GetData(experiment_id + "_sa_Height/A")[0]
                peaks_indices = interface.GetData(experiment_id + "_sa_Index")[0]
                current_values = interface.GetData(experiment_id + "_<I>/" + current_unit_str)[0]
                time_values = interface.GetData(experiment_id + "_time/s")[0]
                

                # Label each step
                electrode_radius = electrode_diam/2
                for i, time_height_index in enumerate(zip(peaks_time, peaks_height, peaks_indices)):
                    interface.Root['page_CA_steps']['graph_CA_steps'].Add('label', name=str(experiment_id)+"_step_"+str(i))
                    interface.Root['page_CA_steps']['graph_CA_steps'][str(experiment_id)+"_step_"+str(i)].label.val = '{:.3f}'.format(time_height_index[1]*1e6) + " nA"
                    interface.Root['page_CA_steps']['graph_CA_steps'][str(experiment_id)+"_step_"+str(i)].positioning.val = 'axes'
                    interface.Root['page_CA_steps']['graph_CA_steps'][str(experiment_id)+"_step_"+str(i)].xPos.val = time_height_index[0]
                    interface.Root['page_CA_steps']['graph_CA_steps'][str(experiment_id)+"_step_"+str(i)].yPos.val = current_values[int(time_height_index[2])]
                    interface.Root['page_CA_steps']['graph_CA_steps'][str(experiment_id)+"_step_"+str(i)].Text.color.val = col


                    # Current in amps from nA.
                    i_before = numpy.mean(current_values[max(0,int(time_height_index[2])-5) : int(time_height_index[2])+1]) * 1e9
                    i_after = numpy.mean(current_values[int(time_height_index[2]) : min(len(current_values),int(time_height_index[2])+5) ]) * 1e9

                    # Radii in um.
                    #particle_radius = electrode_radius*numpy.sqrt(i_before**2 - i_after**2)/i_before
                    particle_radius = electrode_radius*numpy.sqrt((i_before - i_after)/i_before)
                    interface.Root['page_CA_steps_size']['graph_CA_steps_size'].Add('label', name=str(experiment_id)+"_step_"+str(i))
                    interface.Root['page_CA_steps_size']['graph_CA_steps_size'][str(experiment_id)+"_step_"+str(i)].label.val = str(int(particle_radius*2e3)) + " nm"
                    interface.Root['page_CA_steps_size']['graph_CA_steps_size'][str(experiment_id)+"_step_"+str(i)].positioning.val = 'axes'
                    interface.Root['page_CA_steps_size']['graph_CA_steps_size'][str(experiment_id)+"_step_"+str(i)].xPos.val = time_height_index[0]
                    interface.Root['page_CA_steps_size']['graph_CA_steps_size'][str(experiment_id)+"_step_"+str(i)].yPos.val = current_values[int(time_height_index[2])]
                    interface.Root['page_CA_steps_size']['graph_CA_steps_size'][str(experiment_id)+"_step_"+str(i)].Text.color.val = col

                interface.Root['page_CA_steps']['graph_CA_steps'][experiment_id].key.val = str(len(peaks_time)) + "steps / " + str(int(time_values[-1] - time_values[0])) + "s : " + "{:.2e} Hz".format(len(peaks_time)/(time_values[-1] - time_values[0]))
                interface.Root['page_CA_steps_size']['graph_CA_steps_size'][experiment_id].key.val = str(len(peaks_time)) + "steps / " + str(int(time_values[-1] - time_values[0])) + "s : " + "{:.2e} Hz".format(len(peaks_time)/(time_values[-1] - time_values[0]))



            if not fields['dataset_masked_type']=='None':
                self.create_I_masked_plots(
                                            interface,
                                            fields['dataset_masked_type'],
                                            experiment_id + "_<I>/" + current_unit_str,
                                            experiment_id + "_time/s",
                                            experiment_id + "_I Range_change_M")
            
            
        if load_steps_analysis:
            interface.Root["page_CA_steps"]['graph_CA_steps'].Add('key', name='key', autoadd=False)
            interface.Root["page_CA_steps_size"]['graph_CA_steps_size'].Add('key', name='key', autoadd=False)
        

            

            
            






    def plot_masked(self, interface, no_dataset, dataset_I_full_str, dataset_t_full_str):
        """Add a xy widget to plot a portion of a dataset.
        no_dataset is the number of the portion.
        dataset_I_full_str is the full name of the portion to plot ("experiment_ca05_<I>/mA").
        dataset_t_full_str is the full name of the portion to plot ("experiment_ca05_time/s").
        Return nothing.
        """

        # Get the name of the complete graph (with no masked data) "experiment_ca05"
        experiment_id = "_".join(dataset_I_full_str.split("_")[:-1])
        col = interface.Root['page_CA']['graph_CA'][experiment_id].color.val
        interface.Root['page_CA']['graph_CA'][experiment_id].hide.val = True
        experiment_id_no = experiment_id + "_" + str(no_dataset)

        if not (experiment_id_no in interface.GetChildren(where='/page_CA/graph_CA')):
            interface.Root.page_CA.graph_CA.Add('xy', name=experiment_id_no, autoadd=False)
    
        interface.Root['page_CA']['graph_CA'][experiment_id_no].marker.val = 'none'

        interface.Root['page_CA']['graph_CA'][experiment_id_no].xData.val = dataset_t_full_str + "_" + str(no_dataset)
        interface.Root['page_CA']['graph_CA'][experiment_id_no].yData.val = dataset_I_full_str + "_" + str(no_dataset)
            
        interface.Root['page_CA']['graph_CA'][experiment_id_no].color.val = col






    def create_I_masked_plots(self, interface, dataset_masked_type, dataset_I_full_str, dataset_t_full_str, dataset_I_mask_full_str,):
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
        dataset_I_mask_full = interface.GetData(dataset_I_mask_full_str)[0][:len(dataset_I_full)].astype(int)



        #************************** Using expression datasets for storing data *************************

        if dataset_masked_type == 'Expression dataset':
            # Get a list of the start index and end index of every reliables data:
            #
            # Index: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19
            #
            # Mask:  ‾  ‾  ‾ |_  _ |‾  ‾  ‾  ‾ |_  __|‾‾ ‾‾ ‾‾|__|‾‾ ‾‾ ‾‾ ‾‾ ‾‾
            #
            # List: [(0,3), (5,9), (11,14), (15,20)]

            list_indices = []
            start_index, end_index = -1, -1
            prev_mask_value = 0

            for index, mask_value in enumerate(dataset_I_mask_full):

                if mask_value - prev_mask_value > 0:            # If __|‾‾
                    start_index = index
                elif mask_value - prev_mask_value < 0:          # If ‾‾|__
                    end_index = index
                    list_indices.append((start_index, end_index))
                
                prev_mask_value = mask_value
            
            if end_index < start_index: # If the mask is 1 at the end, give a stop index.
                end_index = len(dataset_I_mask_full)
                list_indices.append((start_index, end_index))




            # Create corresponding expression datasets with this list of indices.
            for no_dataset, index_tuple in enumerate(list_indices):
                i_start, i_stop = index_tuple[0], index_tuple[1]
                interface.SetDataExpression(dataset_I_full_str + "_" + str(no_dataset),
                                                "`" + dataset_I_full_str + "`[" + str(i_start) + ":" + str(i_stop) + "]",
                                                linked=True)
                interface.SetDataExpression(dataset_t_full_str + "_" + str(no_dataset),
                                                "`" + dataset_t_full_str + "`[" + str(i_start) + ":" + str(i_stop) + "]",
                                                linked=True)
                
                self.plot_masked(interface, no_dataset, dataset_I_full_str, dataset_t_full_str)
                





        #************************** Using 1D datasets for storing data (raw data) *************************

        if dataset_masked_type == '1D dataset':
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
                self.plot_masked(interface, no_dataset, dataset_I_full_str, dataset_t_full_str)






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
        
        # The line below is a dataset containing the differential of the current range. 
        # Uncomment this line for debug purposes:
        #/interface.SetData(I_range_dataset_str + "_change", I_change_dataset, symerr=None, negerr=None, poserr=None)
        #interface.SetData(I_range_dataset_str + "_change_spread", I_change_dataset_spread, symerr=None, negerr=None, poserr=None)

        # Creating a mask from the convoluted dataset:
        #
        # convolution:           ______/\____/\________/\_____________/\_
        # mask:                  ‾‾‾‾‾‾__‾‾‾‾__‾‾‾‾‾‾‾‾__‾‾‾‾‾‾‾‾‾‾‾‾‾__‾

        interface.SetData(I_range_dataset_str + "_change_M",
                          numpy.logical_not(numpy.ma.make_mask(I_change_dataset_spread, shrink=False)),
                          symerr=None,
                          negerr=None,
                          poserr=None)











class LoadUMEfilesPluginCV(plugins.ToolsPlugin):
    """Load all files related to an experiment of vesicles nano-impacts at
    a ultramicroelectrode (UME).
    This comprises cyclic voltametry (CV) files."""

    # a tuple of strings building up menu to place plugin on
    menu = ("Load UME files", "Cyclic voltammetry measurements")
    # unique name for plugin
    name = "Cyclic voltammetry measurements"

    # name to appear on status tool bar
    description_short = "Load cyclic voltammetric files related to an experiment of vesicles nano-impacts at an ultramicroelectrode."
    # text to appear in dialog box
    description_full = description_short
    

    def __init__(self):
        """Make list of fields."""
        self.fields = [ 
            plugins.FieldFilename('filename_start', descr="First file"),
            plugins.FieldInt('nb_files', descr="Number of files", default=1, minval=1),
            plugins.FieldCombo('current_unit', descr="Unit for current", default='nA', items=('mA', 'uA', 'nA', 'pA')),
            plugins.FieldCombo('ref_potential', descr="Reference potential", default='vs pseudo-ref Pt', items=('', 'vs pseudo-ref Pt', 'vs Ag/AgCl sat.', 'vs SCE')),
            plugins.FieldTextMulti('ref', descr="Experiments to remove from the colormap"),
            plugins.FieldColormap('colormap', descr="Colormap of the curves", default="spectrum2"),
            plugins.FieldBool('invert_colormap', descr="Invert colormap", default=False),
            ]

    def apply(self, interface, fields):
        """Do the work of the plugin.
        interface: veusz command line interface object (exporting commands)
        fields: dict mapping field names to values
        """
        # List content: ["experiment_ca05", "experiment_ca07"]
        experiments_black = list(filter(None, fields['ref']))   # Remove empty strings, for instance in ["",""]

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
            'extract_cycles': False, 'import_all_data': True,
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

        if ("page1" in interface.GetChildren(where='/')):
            interface.Root.page1.Remove()

        if not ("page_CV" in interface.GetChildren(where='/')):
            interface.Root.Add('page', name="page_CV")
        
        # Remove old graph to update all the plotted data:
        if ("graph_CV" in interface.GetChildren(where='/page_CV')):
            interface.Root.page_CV.graph_CA.Remove()
        interface.Root.page_CV.Add('graph', name="graph_CV")

        # Import every file from (filepath_start) to (filepath_start + nb_files)
        for i in range(nb_files):
            experiment_id = filename_root + f"{i + start_no:02d}"

            interface.ImportFilePlugin(
                'EC-LAB CV',
                filepath_prefix + experiment_id + "_" + filename_suffix,
                **pluginargs,
                linked = True,
                encoding = 'utf_8',
                prefix = experiment_id + "_",
                suffix = '',
                renames = {})


            # Create a new current dataset with the convenient unit.

            if fields['current_unit']=='mA':
                current_unit_str = "mA"
            elif fields['current_unit']=='uA':
                current_unit_str = "uA"
                interface.SetDataExpression(experiment_id + "_<I>/" + current_unit_str,
                                            "`" + experiment_id + "_<I>/mA" + "`*1e3",
                                            linked=True)
            elif fields['current_unit']=='nA':
                current_unit_str = "nA"
                interface.SetDataExpression(experiment_id + "_<I>/" + current_unit_str,
                                            "`" + experiment_id + "_<I>/mA" + "`*1e6",
                                            linked=True)
            elif fields['current_unit']=='pA':
                current_unit_str = "pA"
                interface.SetDataExpression(experiment_id + "_<I>/" + current_unit_str,
                                            "`" + experiment_id + "_<I>/mA" + "`*1e9",
                                            linked=True)
           
           
            # If the xy plot does not already exist, create it.
            if not (experiment_id in interface.GetChildren(where='/page_CV/graph_CV')):
                interface.Root.page_CV.graph_CV.Add('xy', name=experiment_id, autoadd=False)
            
            #interface.To(experiment_id)
            #interface.Set('marker', 'none')
            interface.Root['page_CV']['graph_CV'][experiment_id].marker.val = 'none'
            #interface.Set('xData', experiment_id + "_Ewe/V")
            interface.Root['page_CV']['graph_CV'][experiment_id].xData.val = experiment_id + "_Ewe/V"

            #interface.Set('yData', experiment_id + "_<I>/" + current_unit_str)
            interface.Root['page_CV']['graph_CV'][experiment_id].yData.val = experiment_id + "_<I>/" + current_unit_str

            interface.Root.page_CV.graph_CV.x.MinorTicks.hide.val = True
            interface.Root.page_CV.graph_CV.y.MinorTicks.hide.val = True

            interface.Root.page_CV.graph_CV.x.autoRange.val = '+2%'

            interface.Root.page_CV.graph_CV.x.label.val = "E_{we} (V) " + fields['ref_potential']
            interface.Root.page_CV.graph_CV.y.label.val = "Current (" + current_unit_str + ")"
            


            # Color of the experiments excluded from the colormap
            if not (experiment_id in experiments_black):                
                color = next(color_generator)
                if color[3] == 255:
                    # opaque
                    col = "#%02x%02x%02x" % (color[0], color[1], color[2])
                else:
                    # with transparency
                    col = "#%02x%02x%02x%02x" % (color[0], color[1], color[2], color[3])
            else:
                col = "#000000ff"

            interface.Root['page_CV']['graph_CV'][experiment_id].color.val = col
            








    
    


plugins.toolspluginregistry.append(LoadUMEfilesPluginCA)
plugins.toolspluginregistry.append(LoadUMEfilesPluginCV)