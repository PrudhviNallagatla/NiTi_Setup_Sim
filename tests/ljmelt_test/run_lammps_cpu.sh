#!/bin/bash
set -euf -o pipefail

readonly gpu_count=${1:-$(nvidia-smi --list-gpus | wc -l)}
readonly input=${LMP_INPUT:-in.lj.txt}

mpirun -n ${gpu_count} lmp -var x 8 -var y 4 -var z 8 -in ${input}
