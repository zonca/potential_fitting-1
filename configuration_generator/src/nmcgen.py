# nmcgen.py
# 
# Normal Mode Configuration Generator
#
# Automation of the following steps of the workflow:
#	1. geometry optimization
#	2. generation of normal modes/frequency calculation
#	3. configuration generation
#
# The calculations for steps one and two are completed using a quantum chemistry code, psi4 by default. Step three is completed using Sandra's GCN code.
#
# @author Ronak

import os
import sys
import shutil

from configparser import ConfigParser

from molecule import Molecule
import qcalc

import gcn_runner
import config_loader

import output_writer

config = config_loader.load()
filenames, log_name = config_loader.process_files(config)
  
qcalc.init(config, log_name)

with open(config['files']['unoptimized_geometry'], 'r') as input_file:
    molecule = Molecule(input_file.read())

# Step 1
if 'optimize' not in config['files'] or config['files'].getboolean('optimize'):
    if config['config_generator']['code'] == 'psi4':    
        molecule, energy = qcalc.psi4optimize(molecule, config)
        
        output_writer.write_optimized_geo(molecule, energy, filenames['optimized_geometry'])
    elif config['config_generator']['code'] == 'qchem':
        energy, geometry_list = qcalc.qchemoptimize(filenames, config)
        output_writer.qchem_write_optimized_geo(geometry_list, energy, filenames['optimized_geometry'])

else:
    print("Optimized geometry already provided, skipping optimization.\n")
    
    try:
        shutil.copyfile(filenames['input_geometry'], filenames['optimized_geometry'])
    except:
        welp = "it's the same file"

# Step 2
if 'input_normal_modes' not in config['files']:
    if config['config_generator']['code'] == 'psi4':     
        normal_modes, frequencies, red_masses = qcalc.psi4frequencies(molecule, config)
        dim_null = 3 * molecule.num_atoms - len(normal_modes)
    elif config['program']['code'] == 'qchem':
        normal_modes, frequencies, red_masses, num_atoms = qcalc.qchemfrequencies(filenames, config)
        dim_null = 3 * num_atoms - len(normal_modes)
    
    output_writer.write_normal_modes(normal_modes, frequencies, red_masses, filenames['normal_modes'])
else:
    print("Normal modes already provided, skipping frequency calculation.\n")
    
    try:
        shutil.copyfile(config['files']['input_normal_modes'], filenames['normal_modes'])
    except:
        welp = "it's the same file"
    
    with open(config['files']['input_normal_modes'], 'r') as input_file:
        contents = input_file.read()
            
        dim_null = 3 * molecule.num_atoms - contents.count('normal mode')

# Step 3
gcn_runner.generate(config, dim_null, molecule.num_atoms, filenames)

