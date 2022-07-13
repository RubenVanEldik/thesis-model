#!/bin/bash

# Make a new directory for this tuning run and move to it
new_directory=$(date +%s)
mkdir $new_directory
cd $new_directory

# Get the LP model
run_name="Run XXXX"
resolution="1H"
lp_model="../../output/$run_name/$resolution/model.mps"
lp_parameters="../../output/$run_name/$resolution/parameters.prm"

# Tune
grbtune Method=2 TuneBaseSettings="$lp_parameters" TuneTimeLimit=$(expr 1 * 60) "$lp_model"
