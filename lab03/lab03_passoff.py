#!/usr/bin/python3

# Manages file paths
import pathlib
import sys

sys.dont_write_bytecode = True # Prevent the bytecodes for the resources directory from being cached
# Add to the system path the "resources" directory relative to the script that was run
resources_path = pathlib.Path(__file__).resolve().parent.parent  / 'resources'
sys.path.append( str(resources_path) )

import test_suite_320
import repo_test

def main():
    # Check on vivado
    tester = test_suite_320.build_test_suite_320("lab03", start_date="01/27/2025")
    tester.add_Makefile_rule("sim_adder", ["sim_adder.tcl"], ["sim_adder.log"])
    tester.add_Makefile_rule("synth_adder", ["synth_adder.tcl"], ["synth_adder.log", "binary_adder_synth.dcp"])
    tester.add_Makefile_rule("implement_adder", ["implement_adder.tcl"], ["implement_adder.log", "binary_adder.bit", 
                                                                          "binary_adder.dcp", "utilization.rpt"])
    tester.run_tests()

if __name__ == "__main__":
    main()