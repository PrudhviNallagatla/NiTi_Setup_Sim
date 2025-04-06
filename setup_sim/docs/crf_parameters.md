# ***Phase 1 changes to be done***

# Larger system size for better statistics
variable        nx equal 50               # Increased from 20
variable        ny equal 50               # Increased from 20
variable        nz equal 25               # Increased from 10
variable        water_pad equal 25.0      # Increased from 15.0

# Higher precision electrostatics and longer cutoffs
pair_style      hybrid/kk eam/fs/kk lj/cut/coul/long/kk 15.0 15.0  # Larger cutoff
kspace_style    pppm/kk 1.0e-5  # Higher precision for PPPM

# More detailed water distribution
variable        water_density equal 1.0  # Keep standard density
create_atoms    0 region water_region mol h2o_mol 45678 overlap 1.5  # Lower overlap threshold

# Longer equilbration runs for better statistics
run             200000    # Instead of 50000 for heating
run             300000    # Instead of 100000 for NPT
run             500000    # Instead of 200000 for final NVT

# More frequent and detailed output
thermo          500       # More frequent thermodynamic output
dump            3 all custom 5000 dump.phase1.nvt.lammpstrj id type x y z vx vy vz fx fy fz  # Added forces

# Additional analysis
compute         vacf nitinol vacf
fix             vacf_avg nitinol ave/time 5000 1 5000 c_vacf[4] file vacf.phase1.dat
compute         stress all stress/atom NULL
compute         str all reduce sum c_stress[1] c_stress[2] c_stress[3]
fix             stress_avg all ave/time 5000 1 5000 c_str[1] c_str[2] c_str[3] file stress.phase1.dat

# Maximize performance on high-performance systems
package         kokkos Newton on neigh half comm device
neighbor        2.0 bin
neigh_modify    every 1 delay 0 check yes
